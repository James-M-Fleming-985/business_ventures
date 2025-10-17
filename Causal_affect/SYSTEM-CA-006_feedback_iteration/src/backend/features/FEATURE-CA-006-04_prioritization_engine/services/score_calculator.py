from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal

from ..models.schemas import (
    WorkItem,
    ScoringCriteria,
    ScoreComponent,
    CalculatedScore,
    ScoringWeight
)
from ..db.repositories import ScoringCriteriaRepository
from ...shared.exceptions import ValidationError, CalculationError


class ScoreCalculatorService:
    """Service for calculating priority scores based on multiple criteria."""
    
    def __init__(self, criteria_repo: ScoringCriteriaRepository):
        self.criteria_repo = criteria_repo
        self._weight_cache: Dict[str, ScoringWeight] = {}
    
    async def calculate_score(
        self,
        work_item: WorkItem,
        criteria: Optional[List[ScoringCriteria]] = None,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> CalculatedScore:
        """Calculate priority score for a work item."""
        if criteria is None:
            criteria = await self.criteria_repo.get_active_criteria()
        
        if not criteria:
            raise ValidationError("No scoring criteria defined")
        
        components = []
        total_weight = Decimal(0)
        weighted_sum = Decimal(0)
        
        for criterion in criteria:
            try:
                component = await self._calculate_component(
                    work_item,
                    criterion,
                    custom_weights
                )
                components.append(component)
                
                weight = Decimal(str(component.weight))
                total_weight += weight
                weighted_sum += Decimal(str(component.value)) * weight
                
            except Exception as e:
                raise CalculationError(
                    f"Failed to calculate {criterion.name}: {str(e)}"
                )
        
        if total_weight == 0:
            raise CalculationError("Total weight cannot be zero")
        
        final_score = float(weighted_sum / total_weight)
        
        return CalculatedScore(
            work_item_id=work_item.id,
            total_score=final_score,
            components=components,
            calculated_at=datetime.utcnow(),
            criteria_version=await self._get_criteria_version(criteria)
        )
    
    async def _calculate_component(
        self,
        work_item: WorkItem,
        criterion: ScoringCriteria,
        custom_weights: Optional[Dict[str, float]]
    ) -> ScoreComponent:
        """Calculate individual score component."""
        value = await self._evaluate_criterion(work_item, criterion)
        
        weight = self._get_weight(
            criterion.name,
            criterion.default_weight,
            custom_weights
        )
        
        return ScoreComponent(
            criterion_name=criterion.name,
            criterion_type=criterion.type,
            raw_value=value,
            normalized_value=self._normalize_value(
                value,
                criterion.min_value,
                criterion.max_value,
                criterion.normalization_method
            ),
            weight=weight,
            value=self._apply_weight(
                self._normalize_value(
                    value,
                    criterion.min_value,
                    criterion.max_value,
                    criterion.normalization_method
                ),
                weight
            )
        )
    
    async def _evaluate_criterion(
        self,
        work_item: WorkItem,
        criterion: ScoringCriteria
    ) -> float:
        """Evaluate criterion value for work item."""
        if criterion.type == "impact":
            return self._calculate_impact_score(work_item)
        elif criterion.type == "effort":
            return self._calculate_effort_score(work_item)
        elif criterion.type == "risk":
            return self._calculate_risk_score(work_item)
        elif criterion.type == "urgency":
            return self._calculate_urgency_score(work_item)
        elif criterion.type == "business_value":
            return self._calculate_business_value_score(work_item)
        elif criterion.type == "technical_debt":
            return self._calculate_technical_debt_score(work_item)
        elif criterion.type == "custom":
            return await self._evaluate_custom_criterion(
                work_item,
                criterion
            )
        else:
            raise ValidationError(f"Unknown criterion type: {criterion.type}")
    
    def _calculate_impact_score(self, work_item: WorkItem) -> float:
        """Calculate impact score based on affected users and systems."""
        base_score = 0.0
        
        if hasattr(work_item, 'affected_users'):
            if work_item.affected_users > 1000:
                base_score += 10.0
            elif work_item.affected_users > 100:
                base_score += 7.0
            elif work_item.affected_users > 10:
                base_score += 4.0
            else:
                base_score += 2.0
        
        if hasattr(work_item, 'critical_path'):
            if work_item.critical_path:
                base_score *= 1.5
        
        return min(base_score, 10.0)
    
    def _calculate_effort_score(self, work_item: WorkItem) -> float:
        """Calculate effort score (inverse relationship)."""
        if not hasattr(work_item, 'estimated_hours'):
            return 5.0
        
        hours = work_item.estimated_hours
        if hours <= 2:
            return 10.0
        elif hours <= 8:
            return 8.0
        elif hours <= 24:
            return 6.0
        elif hours <= 40:
            return 4.0
        else:
            return 2.0
    
    def _calculate_risk_score(self, work_item: WorkItem) -> float:
        """Calculate risk score."""
        risk_level = getattr(work_item, 'risk_level', 'medium')
        risk_map = {
            'critical': 10.0,
            'high': 8.0,
            'medium': 5.0,
            'low': 3.0,
            'none': 1.0
        }
        return risk_map.get(risk_level.lower(), 5.0)
    
    def _calculate_urgency_score(self, work_item: WorkItem) -> float:
        """Calculate urgency based on due date."""
        if not hasattr(work_item, 'due_date') or not work_item.due_date:
            return 5.0
        
        days_until = (work_item.due_date - datetime.utcnow()).days
        
        if days_until < 0:
            return 10.0  # Overdue
        elif days_until <= 1:
            return 9.0
        elif days_until <= 3:
            return 8.0
        elif days_until <= 7:
            return 6.0
        elif days_until <= 14:
            return 4.0
        else:
            return 2.0
    
    def _calculate_business_value_score(self, work_item: WorkItem) -> float:
        """Calculate business value score."""
        if hasattr(work_item, 'business_value'):
            return float(work_item.business_value)
        
        if hasattr(work_item, 'revenue_impact'):
            revenue = work_item.revenue_impact
            if revenue > 100000:
                return 10.0
            elif revenue > 50000:
                return 8.0
            elif revenue > 10000:
                return 6.0
            elif revenue > 1000:
                return 4.0
            else:
                return 2.0
        
        return 5.0
    
    def _calculate_technical_debt_score(self, work_item: WorkItem) -> float:
        """Calculate technical debt reduction score."""
        if hasattr(work_item, 'debt_reduction_hours'):
            hours = work_item.debt_reduction_hours
            if hours > 40:
                return 10.0
            elif hours > 20:
                return 8.0
            elif hours > 10:
                return 6.0
            elif hours > 5:
                return 4.0
            else:
                return 2.0
        return 3.0
    
    async def _evaluate_custom_criterion(
        self,
        work_item: WorkItem,
        criterion: ScoringCriteria
    ) -> float:
        """Evaluate custom criterion using formula or external service."""
        if criterion.formula:
            return self._evaluate_formula(
                work_item,
                criterion.formula
            )
        elif criterion.external_evaluator:
            return await self._call_external_evaluator(
                work_item,
                criterion.external_evaluator
            )
        else:
            return getattr(work_item, criterion.field_name, 5.0)
    
    def _evaluate_formula(self, work_item: WorkItem, formula: str) -> float:
        """Safely evaluate scoring formula."""
        allowed_vars = {
            key: getattr(work_item, key, 0)
            for key in dir(work_item)
            if not key.startswith('_')
        }
        
        try:
            result = eval(formula, {"__builtins__": {}}, allowed_vars)
            return float(result)
        except Exception as e:
            raise CalculationError(f"Formula evaluation failed: {e}")
    
    async def _call_external_evaluator(
        self,
        work_item: WorkItem,
        evaluator_config: Dict[str, Any]
    ) -> float:
        """Call external service for criterion evaluation."""
        # Implementation would depend on external service
        raise NotImplementedError("External evaluators not yet implemented")
    
    def _normalize_value(
        self,
        value: float,
        min_val: float,
        max_val: float,
        method: str = "linear"
    ) -> float:
        """Normalize value to 0-1 range."""
        if max_val <= min_val:
            raise CalculationError("Invalid min/max range for normalization")
        
        if method == "linear":
            normalized = (value - min_val) / (max_val - min_val)
        elif method == "logarithmic":
            import math
            log_value = math.log(value - min_val + 1)
            log_max = math.log(max_val - min_val + 1)
            normalized = log_value / log_max
        elif method == "sigmoid":
            import math
            midpoint = (max_val + min_val) / 2
            steepness = 4 / (max_val - min_val)
            normalized = 1 / (1 + math.exp(-steepness * (value - midpoint)))
        else:
            raise ValidationError(f"Unknown normalization method: {method}")
        
        return max(0.0, min(1.0, normalized))
    
    def _get_weight(
        self,
        criterion_name: str,
        default_weight: float,
        custom_weights: Optional[Dict[str, float]]
    ) -> float:
        """Get weight for criterion."""
        if custom_weights and criterion_name in custom_weights:
            return custom_weights[criterion_name]
        return default_weight
    
    def _apply_weight(self, normalized_value: float, weight: float) -> float:
        """Apply weight to normalized value."""
        return normalized_value * weight
    
    async def _get_criteria_version(self, criteria: List[ScoringCriteria]) -> str:
        """Generate version identifier for criteria set."""
        import hashlib
        criteria_str = "".join(
            f"{c.name}:{c.version}" for c in sorted(criteria, key=lambda x: x.name)
        )
        return hashlib.md5(criteria_str.encode()).hexdigest()[:8]
    
    async def recalculate_batch(
        self,
        work_items: List[WorkItem],
        criteria: Optional[List[ScoringCriteria]] = None
    ) -> List[CalculatedScore]:
        """Recalculate scores for multiple work items."""
        if criteria is None:
            criteria = await self.criteria_repo.get_active_criteria()
        
        scores = []
        for item in work_items:
            try:
                score = await self.calculate_score(item, criteria)
                scores.append(score)
            except Exception as e:
                # Log error but continue with other items
                scores.append(
                    CalculatedScore(
                        work_item_id=item.id,
                        total_score=0.0,
                        components=[],
                        calculated_at=datetime.utcnow(),
                        error=str(e)
                    )
                )
        
        return scores