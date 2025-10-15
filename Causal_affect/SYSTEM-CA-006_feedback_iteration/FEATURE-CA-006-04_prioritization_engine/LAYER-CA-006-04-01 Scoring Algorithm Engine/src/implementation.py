```python
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ScoreBreakdown:
    """Breakdown of score components for explainability."""
    total_score: float
    component_scores: Dict[str, float]
    normalized_scores: Dict[str, float]
    winsorized_scores: Dict[str, float]
    weights: Dict[str, float]


class ScoringAlgorithmEngine:
    """
    4-dimensional scoring algorithm engine with configurable weights,
    z-score normalization, and winsorization.
    """
    
    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        winsorize_percentile: float = 95.0
    ):
        """
        Initialize the scoring engine.
        
        Args:
            weights: Dictionary of dimension weights. Must sum to 1.0.
                    If None, equal weights are used.
            winsorize_percentile: Percentile for winsorization (default: 95.0)
        """
        self.default_dimensions = ['dimension1', 'dimension2', 'dimension3', 'dimension4']
        
        if weights is None:
            self.weights = {dim: 0.25 for dim in self.default_dimensions}
        else:
            self._validate_weights(weights)
            self.weights = weights
        
        if not 0 < winsorize_percentile <= 100:
            raise ValueError("winsorize_percentile must be between 0 and 100")
        
        self.winsorize_percentile = winsorize_percentile
        self._dimension_stats: Dict[str, Dict[str, float]] = {}
    
    def _validate_weights(self, weights: Dict[str, float]) -> None:
        """Validate that weights sum to 1.0 and are non-negative."""
        if not weights:
            raise ValueError("Weights dictionary cannot be empty")
        
        total = sum(weights.values())
        if not np.isclose(total, 1.0, rtol=1e-5):
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        
        if any(w < 0 for w in weights.values()):
            raise ValueError("All weights must be non-negative")
    
    def fit(self, data: List[Dict[str, float]]) -> None:
        """
        Fit the engine on training data to compute statistics for normalization.
        
        Args:
            data: List of dictionaries containing dimension scores
        """
        if not data:
            raise ValueError("Cannot fit on empty data")
        
        dimensions = list(self.weights.keys())
        
        # Collect values for each dimension
        dimension_values = {dim: [] for dim in dimensions}
        
        for item in data:
            for dim in dimensions:
                if dim not in item:
                    raise KeyError(f"Dimension '{dim}' not found in data item")
                dimension_values[dim].append(item[dim])
        
        # Calculate statistics for each dimension
        self._dimension_stats = {}
        for dim in dimensions:
            values = np.array(dimension_values[dim])
            
            # Calculate winsorization threshold
            threshold = np.percentile(values, self.winsorize_percentile)
            
            # Apply winsorization
            winsorized_values = np.clip(values, None, threshold)
            
            # Calculate z-score statistics on winsorized data
            mean = np.mean(winsorized_values)
            std = np.std(winsorized_values, ddof=1)
            
            # Handle zero standard deviation
            if std == 0 or np.isnan(std):
                std = 1.0
            
            self._dimension_stats[dim] = {
                'mean': mean,
                'std': std,
                'winsorize_threshold': threshold
            }
    
    def _winsorize(self, value: float, dimension: str) -> float:
        """Apply winsorization to a value."""
        if dimension not in self._dimension_stats:
            return value
        
        threshold = self._dimension_stats[dimension]['winsorize_threshold']
        return min(value, threshold)
    
    def _normalize(self, value: float, dimension: str) -> float:
        """Apply z-score normalization to a value."""
        if dimension not in self._dimension_stats:
            return value
        
        stats = self._dimension_stats[dimension]
        return (value - stats['mean']) / stats['std']
    
    def calculate_score(
        self,
        dimensions: Dict[str, float]
    ) -> ScoreBreakdown:
        """
        Calculate the weighted score with full component breakdown.
        
        Args:
            dimensions: Dictionary of dimension values
            
        Returns:
            ScoreBreakdown object with total score and component details
        """
        if not self._dimension_stats:
            raise RuntimeError("Engine must be fitted before calculating scores")
        
        # Validate dimensions
        for dim in self.weights.keys():
            if dim not in dimensions:
                raise KeyError(f"Dimension '{dim}' not found in input")
        
        component_scores = {}
        winsorized_scores = {}
        normalized_scores = {}
        
        total_score = 0.0
        
        for dim, weight in self.weights.items():
            # Original component score
            component_scores[dim] = dimensions[dim]
            
            # Apply winsorization
            winsorized = self._winsorize(dimensions[dim], dim)
            winsorized_scores[dim] = winsorized
            
            # Apply normalization
            normalized = self._normalize(winsorized, dim)
            normalized_scores[dim] = normalized
            
            # Add weighted contribution to total
            total_score += normalized * weight
        
        return ScoreBreakdown(
            total_score=total_score,
            component_scores=component_scores,
            normalized_scores=normalized_scores,
            winsorized_scores=winsorized_scores,
            weights=self.weights.copy()
        )
    
    def calculate_scores(
        self,
        data: List[Dict[str, float]]
    ) -> List[ScoreBreakdown]:
        """
        Calculate scores for multiple data points.
        
        Args:
            data: List of dictionaries containing dimension scores
            
        Returns:
            List of ScoreBreakdown objects
        """
        return [self.calculate_score(item) for item in data]
    
    def get_dimension_stats(self) -> Dict[str, Dict[str, float]]:
        """Get the computed statistics for each dimension."""
        return self._dimension_stats.copy()


def create_scoring_engine(
    weights: Optional[Dict[str, float]] = None,
    winsorize_percentile: float = 95.0
) -> ScoringAlgorithmEngine:
    """
    Factory function to create a scoring engine instance.
    
    Args:
        weights: Dictionary of dimension weights
        winsorize_percentile: Percentile for winsorization
        
    Returns:
        ScoringAlgorithmEngine instance
    """
    return ScoringAlgorithmEngine(weights=weights, winsorize_percentile=winsorize_percentile)
```