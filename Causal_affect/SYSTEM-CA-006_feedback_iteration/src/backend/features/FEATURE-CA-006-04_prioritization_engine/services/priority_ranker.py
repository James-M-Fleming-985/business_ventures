from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime
from collections import defaultdict
import asyncio

from ..models.schemas import (
    WorkItem,
    CalculatedScore,
    PriorityRanking,
    RankingResult,
    RankingCriteria,
    TieBreaker,
    PriorityBracket
)
from ..db.repositories import (
    ScoreRepository,
    RankingRepository,
    WorkItemRepository
)
from .score_calculator import ScoreCalculatorService
from ...shared.exceptions import ValidationError, ProcessingError


class PriorityRankerService:
    """Service for ranking work items based on calculated scores."""
    
    def __init__(
        self,
        score_repo: ScoreRepository,
        ranking_repo: RankingRepository,
        work_item_repo: WorkItemRepository,
        score_calculator: ScoreCalculatorService
    ):
        self.score_repo = score_repo
        self.ranking_repo = ranking_repo
        self.work_item_repo = work_item_repo
        self.score_calculator = score_calculator
    
    async def rank_items(
        self,
        work_items: List[WorkItem],
        ranking_criteria: Optional[RankingCriteria] = None,
        force_recalculate: bool = False
    ) -> RankingResult:
        """Rank work items based on priority scores."""
        if not work_items:
            return RankingResult(
                rankings=[],
                total_items=0,
                ranking_timestamp=datetime.utcnow()
            )
        
        if ranking_criteria is None:
            ranking_criteria = await self._get_default_criteria()
        
        # Get or calculate scores
        scores = await self._get_scores(
            work_items,
            force_recalculate
        )
        
        # Apply ranking algorithm
        rankings = await self._apply_ranking_algorithm(
            work_items,
            scores,
            ranking_criteria
        )
        
        # Save rankings if requested
        if ranking_criteria.persist_rankings:
            await self.ranking_repo.save_rankings(rankings)
        
        return RankingResult(
            rankings=rankings,
            total_items=len(rankings),
            ranking_timestamp=datetime.utcnow(),
            criteria_used=ranking_criteria,
            score_distribution=self._calculate_score_distribution(scores)
        )
    
    async def _get_scores(
        self,
        work_items: List[WorkItem],
        force_recalculate: bool
    ) -> Dict[str, CalculatedScore]:
        """Get scores for work items, calculating if needed."""
        scores = {}
        items_to_calculate = []
        
        if not force_recalculate:
            # Try to get cached scores
            for item in work_items:
                cached_score = await self.score_repo.get_latest_score(item.id)
                if cached_score and self._is_score_valid(cached_score):
                    scores[item.id] = cached_score
                else:
                    items_to_calculate.append(item)
        else:
            items_to_calculate = work_items
        
        # Calculate missing scores
        if items_to_calculate:
            calculated = await self.score_calculator.recalculate_batch(
                items_to_calculate
            )
            for score in calculated:
                scores[score.work_item_id] = score
                await self.score_repo.save_score(score)
        
        return scores
    
    def _is_score_valid(self, score: CalculatedScore) -> bool:
        """Check if cached score is still valid."""
        age_hours = (datetime.utcnow() - score.calculated_at).total_seconds() / 3600
        return age_hours < 24 and not hasattr(score, 'error')
    
    async def _apply_ranking_algorithm(
        self,
        work_items: List[WorkItem],
        scores: Dict[str, CalculatedScore],
        criteria: RankingCriteria
    ) -> List[PriorityRanking]:
        """Apply ranking algorithm to scored items."""
        # Create item-score pairs
        scored_items = [
            (item, scores.get(item.id))
            for item in work_items
            if item.id in scores
        ]
        
        # Apply filters
        filtered_items = await self._apply_filters(
            scored_items,
            criteria
        )
        
        # Sort by score and tie breakers
        sorted_items = self._sort_items(
            filtered_items,
            criteria.tie_breakers
        )
        
        # Apply grouping if requested
        if criteria.use_priority_brackets:
            return await self._create_bracketed_rankings(
                sorted_items,
                criteria
            )
        else:
            return self._create_linear_rankings(sorted_items)
    
    async def _apply_filters(
        self,
        scored_items: List[Tuple[WorkItem, CalculatedScore]],
        criteria: RankingCriteria
    ) -> List[Tuple[WorkItem, CalculatedScore]]:
        """Apply filters to exclude certain items."""
        filtered = scored_items
        
        if criteria.min_score_threshold:
            filtered = [
                (item, score) for item, score in filtered
                if score.total_score >= criteria.min_score_threshold
            ]
        
        if criteria.exclude_statuses:
            filtered = [
                (item, score) for item, score in filtered
                if item.status not in criteria.exclude_statuses
            ]
        
        if criteria.include_types:
            filtered = [
                (item, score) for item, score in filtered
                if item.type in criteria.include_types
            ]
        
        if criteria.team_filter:
            filtered = [
                (item, score) for item, score in filtered
                if item.assigned_team in criteria.team_filter
            ]
        
        return filtered
    
    def _sort_items(
        self,
        scored_items: List[Tuple[WorkItem, CalculatedScore]],
        tie_breakers: List[TieBreaker]
    ) -> List[Tuple[WorkItem, CalculatedScore]]:
        """Sort items by score and apply tie breakers."""
        def sort_key(item_score: Tuple[WorkItem, CalculatedScore]):
            item, score = item_score
            keys = [-score.total_score]  # Negative for descending order
            
            for breaker in tie_breakers:
                value = self._get_tie_breaker_value(item, breaker)
                if breaker.descending:
                    value = -value if isinstance(value, (int, float)) else value
                keys.append(value)
            
            return tuple(keys)
        
        return sorted(scored_items, key=sort_key)
    
    def _get_tie_breaker_value(
        self,
        item: WorkItem,
        breaker: TieBreaker
    ) -> any:
        """Get value for tie breaker comparison."""
        if breaker.field == "created_date":
            return item.created_at
        elif breaker.field == "due_date":
            return item.due_date or datetime.max
        elif breaker.field == "effort":
            return getattr(item, 'estimated_hours', float('inf'))
        elif breaker.field == "id":
            return item.id
        else:
            return getattr(item, breaker.field, None)
    
    async def _create_bracketed_rankings(
        self,
        sorted_items: List[Tuple[WorkItem, CalculatedScore]],
        criteria: RankingCriteria
    ) -> List[PriorityRanking]:
        """Create rankings with priority brackets."""
        brackets = await self._determine_brackets(
            sorted_items,
            criteria
        )
        
        rankings = []
        current_rank = 1
        
        for bracket in brackets:
            for item, score in bracket.items:
                ranking = PriorityRanking(
                    work_item_id=item.id,
                    rank=current_rank,
                    score=score.total_score,
                    bracket=bracket.name,
                    bracket_priority=bracket.priority,
                    confidence_level=self._calculate_confidence(score),
                    previous_rank=await self._get_previous_rank(item.id)
                )
                rankings.append(ranking)
                current_rank += 1
        
        return rankings
    
    def _create_linear_rankings(
        self,
        sorted_items: List[Tuple[WorkItem, CalculatedScore]]
    ) -> List[PriorityRanking]:
        """Create simple linear rankings."""
        rankings = []
        
        for rank, (item, score) in enumerate(sorted_items, 1):
            ranking = PriorityRanking(
                work_item_id=item.id,
                rank=rank,
                score=score.total_score,
                confidence_level=self._calculate_confidence(score)
            )
            rankings.append(ranking)
        
        return rankings
    
    async def _determine_brackets(
        self,
        sorted_items: List[Tuple[WorkItem, CalculatedScore]],
        criteria: RankingCriteria
    ) -> List[PriorityBracket]:
        """Determine priority brackets for items."""
        if not sorted_items:
            return []
        
        brackets = []
        
        if criteria.bracket_method == "percentile":
            brackets = self._create_percentile_brackets(
                sorted_items,
                criteria.bracket_thresholds
            )
        elif criteria.bracket_method == "score_range":
            brackets = self._create_score_range_brackets(
                sorted_items,
                criteria.bracket_thresholds
            )
        elif criteria.bracket_method == "fixed_size":
            brackets = self._create_fixed_size_brackets(
                sorted_items,
                criteria.bracket_size
            )
        else:
            # Default: Create standard priority brackets
            brackets = self._create_standard_brackets(sorted_items)
        
        return brackets
    
    def _create_percentile_brackets(
        self,
        sorted_items: List[Tuple[WorkItem, CalculatedScore]],
        thresholds: List[float]
    ) -> List[PriorityBracket]:
        """Create brackets based on percentiles."""
        total_items = len(sorted_items)
        brackets = []
        
        bracket_names = ["Critical", "High", "Medium", "Low", "Backlog"]
        start_idx = 0
        
        for i, threshold in enumerate(thresholds):
            end_idx = int(total_items * threshold)
            if end_idx > start_idx:
                bracket_items = sorted_items[start_idx:end_idx]
                brackets.append(
                    PriorityBracket(
                        name=bracket_names[i] if i < len(bracket_names) else f"Priority {i+1}",
                        priority=i + 1,
                        items=bracket_items,
                        min_score=bracket_items[-1][1].total_score,
                        max_score=bracket_items[0][1].total_score
                    )
                )
                start_idx = end_idx
        
        # Add remaining items to last bracket
        if start_idx < total_items:
            remaining = sorted_items[start_idx:]
            brackets.append(
                PriorityBracket(
                    name=bracket_names[-1],
                    priority=len(brackets) + 1,
                    items=remaining,
                    min_score=remaining[-1][1].total_score if remaining else 0,
                    max_score=remaining[0][1].total_score if remaining else 0
                )
            )
        
        return brackets
    
    def _create_score_range_brackets(
        self,
        sorted_items: List[Tuple[WorkItem, CalculatedScore]],
        thresholds: List[float]
    ) -> List[PriorityBracket]:
        """Create brackets based on score ranges."""
        brackets = []
        bracket_items = defaultdict(list)
        
        for item, score in sorted_items:
            bracket_idx = 0
            for threshold in thresholds:
                if score.total_score >= threshold:
                    break
                bracket_idx += 1
            
            bracket_items[bracket_idx].append((item, score))
        
        bracket_names = ["Critical", "High", "Medium", "Low", "Backlog"]
        
        for idx, items in sorted(bracket_items.items()):
            if items:
                brackets.append(
                    PriorityBracket(
                        name=bracket_names[idx] if idx < len(bracket_names) else f"Priority {idx+1}",
                        priority=idx + 1,
                        items=items,
                        min_score=min(s.total_score for _, s in items),
                        max_score=max(s.total_score for _, s in items)
                    )
                )
        
        return brackets
    
    def _create_fixed_size_brackets(
        self,
        sorted_items: List[Tuple[WorkItem, CalculatedScore]],
        bracket_size: int
    ) -> List[PriorityBracket]:
        """Create brackets with fixed number of items."""
        brackets = []
        
        for i in range(0, len(sorted_items), bracket_size):
            bracket_items = sorted_items[i:i + bracket_size]
            brackets.append(
                PriorityBracket(
                    name=f"Bracket {len(brackets) + 1}",
                    priority=len(brackets) + 1,
                    items=bracket_items,
                    min_score=bracket_items[-1][1].total_score,
                    max_score=bracket_items[0][1].total_score
                )
            )
        
        return brackets
    
    def _create_standard_brackets(
        self,
        sorted_items: List[Tuple[WorkItem, CalculatedScore]]
    ) -> List[PriorityBracket]:
        """Create standard priority brackets."""
        # Default percentiles: top 10%, next 20%, next 30%, next 30%, bottom 10%
        return self._create_percentile_brackets(
            sorted_items,
            [0.1, 0.3, 0.6, 0.9, 1.0]
        )
    
    def _calculate_confidence(
        self,
        score: CalculatedScore
    ) -> float:
        """Calculate confidence level for score."""
        if hasattr(score, 'error') and score.error:
            return 0.0
        
        # Base confidence on component variance
        if not score.components:
            return 0.5
        
        values = [c.normalized_value for c in score.components]
        if not values:
            return 0.5
        
        avg = sum(values) / len(values)
        variance = sum((v - avg) ** 2 for v in values) / len(values)
        
        # Lower variance = higher confidence
        confidence = 1.0 - min(variance, 1.0)
        
        # Factor in score age
        age_hours = (datetime.utcnow() - score.calculated_at).total_seconds() / 3600
        age_factor = max(0.5, 1.0 - (age_hours / 168))  # Decay over a week
        
        return confidence * age_factor
    
    async def _get_previous_rank(self, work_item_id: str) -> Optional[int]:
        """Get previous ranking for comparison."""
        previous = await self.ranking_repo.get_previous_ranking(work_item_id)
        return previous.rank if previous else None
    
    async def _get_default_criteria(self) -> RankingCriteria:
        """Get default ranking criteria."""
        return RankingCriteria(
            use_priority_brackets=True,
            bracket_method="percentile",
            bracket_thresholds=[0.1, 0.3, 0.6, 0.9],
            tie_breakers=[
                TieBreaker(field="due_date", descending=False),
                TieBreaker(field="created_date", descending=False),
                TieBreaker(field="id", descending=False)
            ],
            persist_rankings=True
        )
    
    def _calculate_score_distribution(
        self,
        scores: Dict[str, CalculatedScore]
    ) -> Dict[str, float]:
        """Calculate distribution statistics for scores."""
        values = [s.total_score for s in scores.values()]
        
        if not values:
            return {}
        
        return {
            "mean": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "median": sorted(values)[len(values) // 2],
            "count": len(values)
        }
    
    async def get_ranking_history(
        self,
        work_item_id: str,
        limit: int = 10
    ) -> List[PriorityRanking]:
        """Get ranking history for a work item."""
        return await self.ranking_repo.get_ranking_history(
            work_item_id,
            limit
        )
    
    async def compare_rankings(
        self,
        current: RankingResult,
        previous: RankingResult
    ) -> Dict[str, any]:
        """Compare two ranking results."""
        comparison = {
            "total_changes": 0,
            "moved_up": [],
            "moved_down": [],
            "new_items": [],
            "removed_items": []
        }
        
        current_map = {r.work_item_id: r for r in current.rankings}
        previous_map = {r.work_item_id: r for r in previous.rankings}
        
        for item_id, current_rank in current_map.items():
            if item_id in previous_map:
                prev_rank = previous_map[item_id]
                if current_rank.rank < prev_rank.rank:
                    comparison["moved_up"].append({
                        "item_id": item_id,
                        "from_rank": prev_rank.rank,
                        "to_rank": current_rank.rank,
                        "change": prev_rank.rank - current_rank.rank
                    })
                    comparison["total_changes"] += 1
                elif current_rank.rank > prev_rank.rank:
                    comparison["moved_down"].append({
                        "item_id": item_id,
                        "from_rank": prev_rank.rank,
                        "to_rank": current_rank.rank,
                        "change": current_rank.rank - prev_rank.rank
                    })
                    comparison["total_changes"] += 1
            else:
                comparison["new_items"].append(item_id)
                comparison["total_changes"] += 1
        
        for item_id in previous_map:
            if item_id not in current_map:
                comparison["removed_items"].append(item_id)
                comparison["total_changes"] += 1
        
        return comparison