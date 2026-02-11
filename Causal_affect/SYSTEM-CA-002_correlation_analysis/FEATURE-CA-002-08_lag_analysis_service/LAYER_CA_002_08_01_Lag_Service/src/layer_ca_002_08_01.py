import numpy as np
import pandas as pd
from typing import Tuple, Optional, Union
from LAYER_CA_002_01_05_Lagged_Correlation_Analyzer.lagged_correlation_analyzer import LaggedCorrelationAnalyzer


class LagService:
    """Service class for performing lag analysis between time series."""
    
    def __init__(self):
        """Initialize the LagService."""
        self.analyzer = LaggedCorrelationAnalyzer()
    
    def calculate_lag_curve(
        self,
        series1: Union[pd.Series, np.ndarray, list],
        series2: Union[pd.Series, np.ndarray, list],
        max_lag: int = 10
    ) -> Tuple[np.ndarray, np.ndarray, int]:
        """
        Calculate lag curve showing correlations at different time lags.
        
        Parameters
        ----------
        series1 : pd.Series, np.ndarray, or list
            First time series
        series2 : pd.Series, np.ndarray, or list
            Second time series
        max_lag : int, optional
            Maximum lag to test (default: 10)
            
        Returns
        -------
        tuple
            - lag_days: Array of lag values from 0 to max_lag
            - correlations: Array of correlation values at each lag
            - optimal_lag: Lag with highest absolute correlation
            
        Raises
        ------
        ValueError
            If input series have missing data or insufficient observations
        """
        # Convert inputs to numpy arrays
        arr1 = self._to_numpy(series1)
        arr2 = self._to_numpy(series2)
        
        # Check for missing data
        if np.any(np.isnan(arr1)) or np.any(np.isnan(arr2)):
            raise ValueError("Input series contain missing data")
        
        # Check for sufficient observations
        min_required = max_lag + 2  # At least 2 observations after max lag
        if len(arr1) < min_required or len(arr2) < min_required:
            raise ValueError(f"Insufficient observations. Need at least {min_required} observations for max_lag={max_lag}")
        
        # Initialize arrays
        lag_days = np.arange(0, max_lag + 1)
        correlations = np.zeros(max_lag + 1)
        
        # Calculate correlations at each lag
        for lag in lag_days:
            if lag == 0:
                # No lag - direct correlation
                corr = np.corrcoef(arr1, arr2)[0, 1]
            else:
                # Use LaggedCorrelationAnalyzer for lagged correlations
                corr = self.analyzer.calculate_lagged_correlation(arr1, arr2, lag)
            correlations[lag] = corr
        
        # Find optimal lag (highest absolute correlation)
        abs_correlations = np.abs(correlations)
        optimal_lag = int(np.argmax(abs_correlations))
        
        return lag_days, correlations, optimal_lag
    
    def _to_numpy(self, series: Union[pd.Series, np.ndarray, list]) -> np.ndarray:
        """
        Convert input to numpy array.
        
        Parameters
        ----------
        series : pd.Series, np.ndarray, or list
            Input series
            
        Returns
        -------
        np.ndarray
            Numpy array representation
        """
        if isinstance(series, pd.Series):
            return series.values
        elif isinstance(series, list):
            return np.array(series)
        elif isinstance(series, np.ndarray):
            return series
        else:
            return np.array(series)