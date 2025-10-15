```python
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class MVP:
    """Represents a Minimum Viable Product with priority metrics."""
    id: str
    priority_score: float
    created_at: datetime = field(default_factory=datetime.now)
    score_history: List[Tuple[datetime, float]] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.score_history:
            self.score_history = [(self.created_at, self.priority_score)]
    
    def update_score(self, new_score: float, timestamp: Optional[datetime] = None):
        """Update the priority score and record in history."""
        if timestamp is None:
            timestamp = datetime.now()
        self.priority_score = new_score
        self.score_history.append((timestamp, new_score))
    
    def get_score_trend(self, days: int = 30) -> List[Tuple[datetime, float]]:
        """Get score history for the specified number of days."""
        if not self.score_history:
            return []
        
        cutoff_date = datetime.now() - timedelta(days=days)
        return [(ts, score) for ts, score in self.score_history if ts >= cutoff_date]


class RankingSystem:
    """System for ranking MVPs by priority score with percentile calculation and archiving."""
    
    def __init__(self):
        self.mvps: Dict[str, MVP] = {}
        self.archive_threshold_percentile: float = 5.0
    
    def add_mvp(self, mvp: MVP) -> None:
        """Add an MVP to the ranking system."""
        if not isinstance(mvp, MVP):
            raise ValueError("Input must be an MVP instance")
        if not mvp.id:
            raise ValueError("MVP must have an id")
        self.mvps[mvp.id] = mvp
    
    def remove_mvp(self, mvp_id: str) -> None:
        """Remove an MVP from the ranking system."""
        if mvp_id in self.mvps:
            del self.mvps[mvp_id]
    
    def rank_mvps(self) -> List[MVP]:
        """
        Rank MVPs by priority score in descending order.
        
        Returns:
            List of MVPs sorted by priority_score (highest first)
        """
        if not self.mvps:
            return []
        
        return sorted(self.mvps.values(), key=lambda x: x.priority_score, reverse=True)
    
    def calculate_percentile(self, mvp_id: str) -> float:
        """
        Calculate the percentile rank of an MVP.
        
        Args:
            mvp_id: The ID of the MVP to calculate percentile for
            
        Returns:
            Percentile rank (0-100) where higher is better
            
        Raises:
            KeyError: If MVP ID not found
        """
        if mvp_id not in self.mvps:
            raise KeyError(f"MVP with id '{mvp_id}' not found")
        
        if len(self.mvps) == 1:
            return 100.0
        
        mvp = self.mvps[mvp_id]
        scores = [m.priority_score for m in self.mvps.values()]
        
        # Calculate percentile: percentage of scores that are less than or equal to this score
        percentile = (np.sum(np.array(scores) < mvp.priority_score) / len(scores)) * 100.0
        
        return float(percentile)
    
    def get_percentile_for_score(self, score: float) -> float:
        """
        Calculate what percentile a given score would be at.
        
        Args:
            score: The score to calculate percentile for
            
        Returns:
            Percentile rank (0-100)
        """
        if not self.mvps:
            return 0.0
        
        scores = [m.priority_score for m in self.mvps.values()]
        
        if len(scores) == 1:
            if score >= scores[0]:
                return 100.0
            else:
                return 0.0
        
        percentile = (np.sum(np.array(scores) < score) / len(scores)) * 100.0
        return float(percentile)
    
    def identify_archive_candidates(self) -> List[MVP]:
        """
        Identify MVPs that are candidates for archiving.
        
        Archive candidates are MVPs in the bottom 5th percentile.
        This method aims for <5% false positive rate.
        
        Returns:
            List of MVPs that are archive candidates
        """
        if not self.mvps:
            return []
        
        if len(self.mvps) == 1:
            return []
        
        scores = [m.priority_score for m in self.mvps.values()]
        threshold_score = np.percentile(scores, self.archive_threshold_percentile)
        
        candidates = []
        for mvp in self.mvps.values():
            if mvp.priority_score <= threshold_score:
                percentile = self.calculate_percentile(mvp.id)
                if percentile <= self.archive_threshold_percentile:
                    candidates.append(mvp)
        
        return candidates
    
    def track_score_trends(self, mvp_id: str, days: int = 30) -> Dict:
        """
        Track score trends for an MVP over a specified time window.
        
        Args:
            mvp_id: The ID of the MVP to track
            days: Number of days to look back (default 30)
            
        Returns:
            Dictionary with trend information including:
            - history: List of (timestamp, score) tuples
            - trend: 'increasing', 'decreasing', 'stable', or 'insufficient_data'
            - change: Total change in score over period
            - avg_score: Average score over period
            
        Raises:
            KeyError: If MVP ID not found
        """
        if mvp_id not in self.mvps:
            raise KeyError(f"MVP with id '{mvp_id}' not found")
        
        mvp = self.mvps[mvp_id]
        history = mvp.get_score_trend(days)
        
        if len(history) < 2:
            return {
                'history': history,
                'trend': 'insufficient_data',
                'change': 0.0,
                'avg_score': history[0][1] if history else 0.0,
                'min_score': history[0][1] if history else 0.0,
                'max_score': history[0][1] if history else 0.0,
            }
        
        scores = [score for _, score in history]
        first_score = history[0][1]
        last_score = history[-1][1]
        change = last_score - first_score
        
        # Determine trend using linear regression
        if len(scores) >= 2:
            x = np.arange(len(scores))
            y = np.array(scores)
            
            # Calculate slope using least squares
            if len(x) > 1 and np.std(x) > 0:
                slope = np.polyfit(x, y, 1)[0]
                
                # Threshold for determining significant trend
                threshold = np.std(scores) * 0.1
                
                if abs(slope) < threshold:
                    trend = 'stable'
                elif slope > 0:
                    trend = 'increasing'
                else:
                    trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        return {
            'history': history,
            'trend': trend,
            'change': float(change),
            'avg_score': float(np.mean(scores)),
            'min_score': float(np.min(scores)),
            'max_score': float(np.max(scores)),
        }
    
    def get_all_trends(self, days: int = 30) -> Dict[str, Dict]:
        """
        Get score trends for all MVPs.
        
        Args:
            days: Number of days to look back (default 30)
            
        Returns:
            Dictionary mapping MVP IDs to their trend information
        """
        trends = {}
        for mvp_id in self.mvps:
            trends[mvp_id] = self.track_score_trends(mvp_id, days)
        return trends


def create_ranking_system() -> RankingSystem:
    """Factory function to create a new RankingSystem instance."""
    return RankingSystem()
```