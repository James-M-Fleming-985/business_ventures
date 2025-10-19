```python
"""Lagged correlation analysis module for time series data.

This module provides functionality to calculate correlation between time series
with various lag values, handling missing data and supporting concurrent execution.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from functools import partial
import logging

logger = logging.getLogger(__name__)


@dataclass
class LaggedCorrelationResult:
    """Container for lagged correlation analysis results."""
    
    lag: int
    correlation: float
    p_value: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    n_observations: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            'lag': self.lag,
            'correlation': self.correlation,
            'p_value': self.p_value,
            'confidence_interval': self.confidence_interval,
            'n_observations': self.n_observations
        }


class LaggedCorrelationAnalyzer:
    """Analyzer for computing lagged correlations between time series."""
    
    def __init__(
        self,
        max_lag: int = 10,
        min_observations: int = 30,
        confidence_level: float = 0.95,
        method: str = 'pearson',
        handle_missing: str = 'pairwise',
        n_threads: Optional[int] = None
    ):
        """Initialize the lagged correlation analyzer.
        
        Args:
            max_lag: Maximum lag to compute
            min_observations: Minimum number of observations required
            confidence_level: Confidence level for intervals
            method: Correlation method ('pearson', 'spearman', 'kendall')
            handle_missing: How to handle missing data ('pairwise', 'complete')
            n_threads: Number of threads for parallel execution
        """
        self.max_lag = max_lag
        self.min_observations = min_observations
        self.confidence_level = confidence_level
        self.method = method
        self.handle_missing = handle_missing
        self.n_threads = n_threads
        
    def calculate_lagged_correlation(
        self,
        x: Union[np.ndarray, pd.Series, List],
        y: Union[np.ndarray, pd.Series, List],
        lags: Optional[List[int]] = None
    ) -> Dict[int, LaggedCorrelationResult]:
        """Calculate correlation between x and lagged values of y.
        
        Args:
            x: First time series
            y: Second time series  
            lags: List of lag values to compute
            
        Returns:
            Dictionary mapping lag values to correlation results
        """
        # Convert inputs to numpy arrays
        x_arr = self._to_numpy(x)
        y_arr = self._to_numpy(y)
        
        # Validate inputs
        self._validate_inputs(x_arr, y_arr)
        
        # Determine lags to compute
        if lags is None:
            lags = list(range(-self.max_lag, self.max_lag + 1))
        
        # Calculate correlations
        results = {}
        
        if self.n_threads and len(lags) > 1:
            # Parallel execution
            with ThreadPoolExecutor(max_workers=self.n_threads) as executor:
                future_to_lag = {
                    executor.submit(
                        self._compute_single_lag,
                        x_arr, y_arr, lag
                    ): lag for lag in lags
                }
                
                for future in as_completed(future_to_lag):
                    lag = future_to_lag[future]
                    try:
                        results[lag] = future.result()
                    except Exception as e:
                        logger.error(f"Error computing lag {lag}: {e}")
                        results[lag] = LaggedCorrelationResult(
                            lag=lag,
                            correlation=np.nan
                        )
        else:
            # Sequential execution
            for lag in lags:
                results[lag] = self._compute_single_lag(x_arr, y_arr, lag)
                
        return results
    
    def find_optimal_lag(
        self,
        x: Union[np.ndarray, pd.Series, List],
        y: Union[np.ndarray, pd.Series, List],
        criterion: str = 'max_correlation'
    ) -> Tuple[int, LaggedCorrelationResult]:
        """Find the lag with optimal correlation.
        
        Args:
            x: First time series
            y: Second time series
            criterion: Optimization criterion
            
        Returns:
            Tuple of (optimal_lag, result)
        """
        results = self.calculate_lagged_correlation(x, y)
        
        if criterion == 'max_correlation':
            optimal_lag = max(
                results.keys(),
                key=lambda k: abs(results[k].correlation)
                if not np.isnan(results[k].correlation) else -np.inf
            )
        elif criterion == 'min_p_value':
            optimal_lag = min(
                results.keys(),
                key=lambda k: results[k].p_value
                if results[k].p_value is not None else np.inf
            )
        else:
            raise ValueError(f"Unknown criterion: {criterion}")
            
        return optimal_lag, results[optimal_lag]
    
    def calculate_cross_correlation(
        self,
        x: Union[np.ndarray, pd.Series, List],
        y: Union[np.ndarray, pd.Series, List],
        normalize: bool = True
    ) -> np.ndarray:
        """Calculate full cross-correlation function.
        
        Args:
            x: First time series
            y: Second time series
            normalize: Whether to normalize the result
            
        Returns:
            Cross-correlation array
        """
        x_arr = self._to_numpy(x)
        y_arr = self._to_numpy(y)
        
        # Remove mean
        x_centered = x_arr - np.nanmean(x_arr)
        y_centered = y_arr - np.nanmean(y_arr)
        
        # Replace NaN with 0 for correlation calculation
        x_centered = np.nan_to_num(x_centered)
        y_centered = np.nan_to_num(y_centered)
        
        # Calculate cross-correlation
        correlation = np.correlate(x_centered, y_centered, mode='full')
        
        if normalize:
            # Normalize by standard deviations and length
            x_std = np.nanstd(x_arr)
            y_std = np.nanstd(y_arr)
            n = len(x_arr)
            
            if x_std > 0 and y_std > 0:
                correlation = correlation / (n * x_std * y_std)
            else:
                correlation = np.zeros_like(correlation)
                
        return correlation
    
    def _compute_single_lag(
        self,
        x: np.ndarray,
        y: np.ndarray,
        lag: int
    ) -> LaggedCorrelationResult:
        """Compute correlation for a single lag value."""
        # Prepare lagged data
        if lag > 0:
            # Positive lag: y is shifted forward
            x_aligned = x[:-lag] if lag < len(x) else np.array([])
            y_aligned = y[lag:] if lag < len(y) else np.array([])
        elif lag < 0:
            # Negative lag: y is shifted backward
            x_aligned = x[-lag:] if -lag < len(x) else np.array([])
            y_aligned = y[:lag] if -lag < len(y) else np.array([])
        else:
            # No lag
            x_aligned = x.copy()
            y_aligned = y.copy()
            
        # Handle missing data
        if self.handle_missing == 'pairwise':
            mask = ~(np.isnan(x_aligned) | np.isnan(y_aligned))
            x_clean = x_aligned[mask]
            y_clean = y_aligned[mask]
        elif self.handle_missing == 'complete':
            if np.any(np.isnan(x_aligned)) or np.any(np.isnan(y_aligned)):
                return LaggedCorrelationResult(
                    lag=lag,
                    correlation=np.nan,
                    n_observations=0
                )
            x_clean = x_aligned
            y_clean = y_aligned
        else:
            x_clean = x_aligned
            y_clean = y_aligned
            
        # Check minimum observations
        n_obs = len(x_clean)
        if n_obs < self.min_observations:
            return LaggedCorrelationResult(
                lag=lag,
                correlation=np.nan,
                n_observations=n_obs
            )
            
        # Calculate correlation
        try:
            if self.method == 'pearson':
                corr, p_value = self._pearson_correlation(x_clean, y_clean)
            elif self.method == 'spearman':
                corr, p_value = self._spearman_correlation(x_clean, y_clean)
            elif self.method == 'kendall':
                corr, p_value = self._kendall_correlation(x_clean, y_clean)
            else:
                raise ValueError(f"Unknown method: {self.method}")
                
            # Calculate confidence interval
            ci = self._calculate_confidence_interval(corr, n_obs)
            
            return LaggedCorrelationResult(
                lag=lag,
                correlation=corr,
                p_value=p_value,
                confidence_interval=ci,
                n_observations=n_obs
            )
            
        except Exception as e:
            logger.warning(f"Error calculating correlation for lag {lag}: {e}")
            return LaggedCorrelationResult(
                lag=lag,
                correlation=np.nan,
                n_observations=n_obs
            )
    
    def _pearson_correlation(
        self,
        x: np.ndarray,
        y: np.ndarray
    ) -> Tuple[float, float]:
        """Calculate Pearson correlation coefficient."""
        from scipy import stats
        
        if len(x) < 2:
            return np.nan, np.nan
            
        corr, p_value = stats.pearsonr(x, y)
        return corr, p_value
    
    def _spearman_correlation(
        self,
        x: np.ndarray,
        y: np.ndarray
    ) -> Tuple[float, float]:
        """Calculate Spearman correlation coefficient."""
        from scipy import stats
        
        if len(x) < 2:
            return np.nan, np.nan
            
        corr, p_value = stats.spearmanr(x, y)
        return corr, p_value
    
    def _kendall_correlation(
        self,
        x: np.ndarray,
        y: np.ndarray
    ) -> Tuple[float, float]:
        """Calculate Kendall correlation coefficient."""
        from scipy import stats
        
        if len(x) < 2:
            return np.nan, np.nan
            
        corr, p_value = stats.kendalltau(x, y)
        return corr, p_value
    
    def _calculate_confidence_interval(
        self,
        corr: float,
        n: int
    ) -> Tuple[float, float]:
        """Calculate confidence interval for correlation coefficient."""
        if np.isnan(corr) or n < 3:
            return (np.nan, np.nan)
            
        # Fisher z-transformation
        z = 0.5 * np.log((1 + corr) / (1 - corr))
        se = 1 / np.sqrt(n - 3)
        
        # Critical value
        from scipy import stats
        alpha = 1 - self.confidence_level
        z_crit = stats.norm.ppf(1 - alpha/2)
        
        # Confidence interval in z-space
        z_lower = z - z_crit * se
        z_upper = z + z_crit * se
        
        # Transform back to correlation space
        lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
        upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)
        
        return (lower, upper)
    
    def _to_numpy(self, data: Union[np.ndarray, pd.Series, List]) -> np.ndarray:
        """Convert input data to numpy array."""
        if isinstance(data, np.ndarray):
            return data.astype(float)
        elif isinstance(data, pd.Series):
            return data.to_numpy(dtype=float)
        elif isinstance(data, list):
            return np.array(data, dtype=float)
        else:
            raise TypeError(f"Unsupported data type: {type(data)}")
    
    def _validate_inputs(self, x: np.ndarray, y: np.ndarray) -> None:
        """Validate input arrays."""
        if len(x) != len(y):
            raise ValueError(f"Input arrays must have same length: {len(x)} != {len(y)}")
            
        if len(x) < self.min_observations:
            raise ValueError(
                f"Insufficient data: {len(x)} < {self.min_observations}"
            )
            
        if np.all(np.isnan(x)) or np.all(np.isnan(y)):
            raise ValueError("Input contains all NaN values")


def calculate_lagged_correlations(
    x: Union[np.ndarray, pd.Series, List],
    y: Union[np.ndarray, pd.Series, List],
    max_lag: int = 10,
    **kwargs
) -> Dict[int, LaggedCorrelationResult]:
    """Convenience function to calculate lagged correlations.
    
    Args:
        x: First time series
        y: Second time series
        max_lag: Maximum lag to compute
        **kwargs: Additional arguments for LaggedCorrelationAnalyzer
        
    Returns:
        Dictionary mapping lag values to correlation results
    """
    analyzer = LaggedCorrelationAnalyzer(max_lag=max_lag, **kwargs)
    return analyzer.calculate_lagged_correlation(x, y)
```