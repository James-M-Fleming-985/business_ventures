```python
"""
Granger causality test implementation for time series analysis.

This module provides functionality to test Granger causality between time series,
determining if one series helps predict another.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any
from statsmodels.tsa.stattools import grangercausalitytests
from statsmodels.tools.sm_exceptions import InfeasibleTestError
import warnings
from concurrent.futures import ThreadPoolExecutor, Future
import time
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class GrangerTestResult:
    """Container for Granger causality test results."""
    
    test_statistic: float
    p_value: float
    lags: int
    reject_null: bool
    confidence_level: float = 0.05
    direction: Optional[str] = None
    aic: Optional[float] = None
    bic: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            'test_statistic': self.test_statistic,
            'p_value': self.p_value,
            'lags': self.lags,
            'reject_null': self.reject_null,
            'confidence_level': self.confidence_level,
            'direction': self.direction,
            'aic': self.aic,
            'bic': self.bic
        }


class GrangerCausalityTest:
    """
    Implements Granger causality testing for time series analysis.
    
    The Granger causality test determines whether one time series is useful
    in forecasting another. If a time series X "Granger-causes" Y, then past
    values of X contain information that helps predict Y above and beyond the
    information contained in past values of Y alone.
    
    Attributes:
        max_lag (int): Maximum number of lags to test
        confidence_level (float): Significance level for hypothesis testing
        handle_missing (str): Method for handling missing data ('drop', 'interpolate')
    """
    
    def __init__(self, 
                 max_lag: int = 4,
                 confidence_level: float = 0.05,
                 handle_missing: str = 'drop'):
        """
        Initialize Granger causality test.
        
        Args:
            max_lag: Maximum number of lags to test (default: 4)
            confidence_level: Significance level (default: 0.05)
            handle_missing: How to handle missing data (default: 'drop')
        """
        if max_lag < 1:
            raise ValueError("max_lag must be at least 1")
        if not 0 < confidence_level < 1:
            raise ValueError("confidence_level must be between 0 and 1")
        if handle_missing not in ['drop', 'interpolate']:
            raise ValueError("handle_missing must be 'drop' or 'interpolate'")
            
        self.max_lag = max_lag
        self.confidence_level = confidence_level
        self.handle_missing = handle_missing
        self._cache = {}
        
    def test(self, 
             x: Union[np.ndarray, pd.Series, List[float]], 
             y: Union[np.ndarray, pd.Series, List[float]],
             lag: Optional[int] = None) -> GrangerTestResult:
        """
        Perform Granger causality test.
        
        Tests the null hypothesis that x does not Granger-cause y.
        
        Args:
            x: First time series (potential cause)
            y: Second time series (potential effect)
            lag: Number of lags to use (if None, uses optimal lag)
            
        Returns:
            GrangerTestResult containing test results
            
        Raises:
            ValueError: If input data is invalid
            RuntimeError: If test calculation fails
        """
        # Convert inputs to numpy arrays
        x_arr = self._to_array(x)
        y_arr = self._to_array(y)
        
        # Validate inputs
        if len(x_arr) != len(y_arr):
            raise ValueError("Input series must have the same length")
        if len(x_arr) < self.max_lag + 1:
            raise ValueError(f"Series too short for max_lag={self.max_lag}")
            
        # Handle missing data
        x_clean, y_clean = self._handle_missing_data(x_arr, y_arr)
        
        # Determine optimal lag if not specified
        if lag is None:
            lag = self._select_optimal_lag(x_clean, y_clean)
        else:
            if lag > self.max_lag or lag < 1:
                raise ValueError(f"lag must be between 1 and {self.max_lag}")
                
        # Perform Granger causality test
        try:
            result = self._perform_test(x_clean, y_clean, lag)
        except Exception as e:
            raise RuntimeError(f"Granger test failed: {str(e)}")
            
        return result
        
    def test_bidirectional(self,
                          x: Union[np.ndarray, pd.Series, List[float]],
                          y: Union[np.ndarray, pd.Series, List[float]]) -> Dict[str, GrangerTestResult]:
        """
        Test Granger causality in both directions.
        
        Args:
            x: First time series
            y: Second time series
            
        Returns:
            Dictionary with 'x_causes_y' and 'y_causes_x' results
        """
        results = {}
        
        # Test x -> y
        result_xy = self.test(x, y)
        result_xy.direction = 'x_causes_y'
        results['x_causes_y'] = result_xy
        
        # Test y -> x
        result_yx = self.test(y, x)
        result_yx.direction = 'y_causes_x'
        results['y_causes_x'] = result_yx
        
        return results
        
    def test_multiple(self,
                     data: Dict[str, Union[np.ndarray, pd.Series, List[float]]],
                     pairs: Optional[List[Tuple[str, str]]] = None) -> Dict[Tuple[str, str], GrangerTestResult]:
        """
        Test Granger causality for multiple variable pairs.
        
        Args:
            data: Dictionary mapping variable names to time series
            pairs: List of (cause, effect) tuples to test (if None, tests all pairs)
            
        Returns:
            Dictionary mapping (cause, effect) tuples to test results
        """
        if pairs is None:
            # Test all possible pairs
            variables = list(data.keys())
            pairs = [(v1, v2) for v1 in variables for v2 in variables if v1 != v2]
            
        results = {}
        for cause, effect in pairs:
            if cause not in data or effect not in data:
                raise ValueError(f"Variable not found in data: {cause} or {effect}")
                
            result = self.test(data[cause], data[effect])
            result.direction = f"{cause}_causes_{effect}"
            results[(cause, effect)] = result
            
        return results
        
    def test_concurrent(self,
                       data: Dict[str, Union[np.ndarray, pd.Series, List[float]]],
                       pairs: Optional[List[Tuple[str, str]]] = None,
                       max_workers: int = 4) -> Dict[Tuple[str, str], Future]:
        """
        Test multiple pairs concurrently using thread pool.
        
        Args:
            data: Dictionary mapping variable names to time series
            pairs: List of (cause, effect) tuples to test
            max_workers: Maximum number of concurrent workers
            
        Returns:
            Dictionary mapping pairs to Future objects containing results
        """
        if pairs is None:
            variables = list(data.keys())
            pairs = [(v1, v2) for v1 in variables for v2 in variables if v1 != v2]
            
        futures = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for cause, effect in pairs:
                if cause not in data or effect not in data:
                    continue
                    
                future = executor.submit(self.test, data[cause], data[effect])
                futures[(cause, effect)] = future
                
        # Wait for all futures to complete and get results
        results = {}
        for pair, future in futures.items():
            try:
                result = future.result(timeout=5.0)
                result.direction = f"{pair[0]}_causes_{pair[1]}"
                results[pair] = result
            except Exception as e:
                # Log error but continue with other tests
                warnings.warn(f"Test failed for pair {pair}: {str(e)}")
                
        return results
        
    def _to_array(self, data: Union[np.ndarray, pd.Series, List[float]]) -> np.ndarray:
        """Convert input data to numpy array."""
        if isinstance(data, pd.Series):
            return data.values
        elif isinstance(data, list):
            return np.array(data)
        elif isinstance(data, np.ndarray):
            return data
        else:
            raise TypeError(f"Unsupported data type: {type(data)}")
            
    def _handle_missing_data(self, x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Handle missing values in the data."""
        # Create mask for non-missing values
        mask = ~(np.isnan(x) | np.isnan(y))
        
        if self.handle_missing == 'drop':
            return x[mask], y[mask]
        elif self.handle_missing == 'interpolate':
            # Simple linear interpolation
            x_clean = np.copy(x)
            y_clean = np.copy(y)
            
            if np.any(np.isnan(x_clean)):
                nans = np.isnan(x_clean)
                x_clean[nans] = np.interp(np.flatnonzero(nans), 
                                         np.flatnonzero(~nans), 
                                         x_clean[~nans])
                                         
            if np.any(np.isnan(y_clean)):
                nans = np.isnan(y_clean)
                y_clean[nans] = np.interp(np.flatnonzero(nans), 
                                         np.flatnonzero(~nans), 
                                         y_clean[~nans])
                                         
            return x_clean, y_clean
            
    @lru_cache(maxsize=128)
    def _select_optimal_lag(self, x_tuple: tuple, y_tuple: tuple) -> int:
        """Select optimal lag using information criteria."""
        x = np.array(x_tuple)
        y = np.array(y_tuple)
        
        # Combine series for testing
        data = np.column_stack((y, x))
        
        best_aic = float('inf')
        best_lag = 1
        
        for lag in range(1, min(self.max_lag + 1, len(x) // 3)):
            try:
                # Suppress warnings for this operation
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    test_result = grangercausalitytests(data, maxlag=[lag], verbose=False)
                    
                # Extract AIC from the VAR model
                if lag in test_result and 'params_ftest' in test_result[lag][0]:
                    # Use F-test p-value as proxy for model quality
                    p_value = test_result[lag][0]['params_ftest'][1]
                    # Prefer lower p-values (stronger evidence) with penalty for lag
                    aic_proxy = p_value * (1 + 0.1 * lag)
                    
                    if aic_proxy < best_aic:
                        best_aic = aic_proxy
                        best_lag = lag
                        
            except:
                continue
                
        return best_lag
        
    def _perform_test(self, x: np.ndarray, y: np.ndarray, lag: int) -> GrangerTestResult:
        """Perform the actual Granger causality test."""
        # Combine series for testing
        data = np.column_stack((y, x))
        
        # Cache key for results
        cache_key = (tuple(x), tuple(y), lag)
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        try:
            # Suppress verbose output
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                test_results = grangercausalitytests(data, maxlag=[lag], verbose=False)
                
        except Exception as e:
            raise RuntimeError(f"Failed to compute Granger test: {str(e)}")
            
        # Extract test results for the specified lag
        if lag not in test_results:
            raise RuntimeError(f"No results for lag {lag}")
            
        lag_results = test_results[lag][0]
        
        # Extract F-test results (most commonly used)
        if 'ssr_ftest' in lag_results:
            test_stat = lag_results['ssr_ftest'][0]
            p_value = lag_results['ssr_ftest'][1]
        elif 'params_ftest' in lag_results:
            test_stat = lag_results['params_ftest'][0]
            p_value = lag_results['params_ftest'][1]
        else:
            raise RuntimeError("No F-test results found")
            
        # Determine if null hypothesis is rejected
        reject_null = p_value < self.confidence_level
        
        # Create result object
        result = GrangerTestResult(
            test_statistic=float(test_stat),
            p_value=float(p_value),
            lags=lag,
            reject_null=reject_null,
            confidence_level=self.confidence_level
        )
        
        # Cache result
        self._cache[cache_key] = result
        
        return result
        

def granger_causality_test(x: Union[np.ndarray, pd.Series, List[float]],
                          y: Union[np.ndarray, pd.Series, List[float]],
                          max_lag: int = 4,
                          confidence_level: float = 0.05) -> GrangerTestResult:
    """
    Convenience function to perform Granger causality test.
    
    Args:
        x: First time series (potential cause)
        y: Second time series (potential effect)
        max_lag: Maximum lag to consider
        confidence_level: Significance level for test
        
    Returns:
        GrangerTestResult with test results
    """
    tester = GrangerCausalityTest(max_lag=max_lag, confidence_level=confidence_level)
    return tester.test(x, y)
```