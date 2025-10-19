```python
"""
Impulse Response Function (IRF) Calculator Module

This module provides functionality for calculating impulse response functions
to analyze the dynamic impact of shocks in time series data.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import warnings
from scipy import stats
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class IRFResult:
    """Container for IRF calculation results."""
    irf_values: np.ndarray
    periods: int
    confidence_intervals: Optional[Dict[str, np.ndarray]] = None
    standard_errors: Optional[np.ndarray] = None
    variable_names: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert IRF result to dictionary format."""
        result = {
            'irf_values': self.irf_values.tolist() if isinstance(self.irf_values, np.ndarray) else self.irf_values,
            'periods': self.periods
        }
        
        if self.confidence_intervals is not None:
            result['confidence_intervals'] = {
                k: v.tolist() if isinstance(v, np.ndarray) else v 
                for k, v in self.confidence_intervals.items()
            }
        
        if self.standard_errors is not None:
            result['standard_errors'] = self.standard_errors.tolist() if isinstance(self.standard_errors, np.ndarray) else self.standard_errors
            
        if self.variable_names is not None:
            result['variable_names'] = self.variable_names
            
        return result


class IRFCalculator:
    """
    Impulse Response Function Calculator for time series analysis.
    
    This class provides methods to calculate impulse response functions
    which measure the dynamic impact of shocks on variables over time.
    """
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        Initialize the IRF Calculator.
        
        Parameters
        ----------
        max_workers : int, optional
            Maximum number of workers for parallel processing.
            If None, uses CPU count.
        """
        self.max_workers = max_workers
        self._validate_initialized()
    
    def _validate_initialized(self):
        """Validate that the calculator is properly initialized."""
        if self.max_workers is not None and self.max_workers < 1:
            raise ValueError("max_workers must be at least 1")
    
    def calculate_irf(
        self,
        data: Union[np.ndarray, pd.DataFrame],
        periods: int = 10,
        method: str = 'ols',
        confidence_level: float = 0.95,
        handle_missing: str = 'drop',
        parallel: bool = False
    ) -> IRFResult:
        """
        Calculate impulse response function for the given data.
        
        Parameters
        ----------
        data : array-like or DataFrame
            Input time series data
        periods : int, default=10
            Number of periods to calculate IRF
        method : str, default='ols'
            Estimation method ('ols', 'var')
        confidence_level : float, default=0.95
            Confidence level for intervals
        handle_missing : str, default='drop'
            How to handle missing values ('drop', 'interpolate', 'raise')
        parallel : bool, default=False
            Whether to use parallel processing
            
        Returns
        -------
        IRFResult
            Object containing IRF values and metadata
            
        Raises
        ------
        ValueError
            If input data is invalid or parameters are incorrect
        """
        # Validate inputs
        self._validate_inputs(data, periods, method, confidence_level, handle_missing)
        
        # Convert to numpy array and handle missing data
        processed_data = self._preprocess_data(data, handle_missing)
        
        # Calculate IRF based on method
        if parallel and processed_data.shape[0] > 1000:
            irf_values = self._calculate_irf_parallel(processed_data, periods, method)
        else:
            irf_values = self._calculate_irf_sequential(processed_data, periods, method)
        
        # Calculate confidence intervals
        confidence_intervals = self._calculate_confidence_intervals(
            processed_data, irf_values, confidence_level, method
        )
        
        # Calculate standard errors
        standard_errors = self._calculate_standard_errors(processed_data, irf_values, method)
        
        # Get variable names if DataFrame
        variable_names = None
        if isinstance(data, pd.DataFrame):
            variable_names = data.columns.tolist()
        
        return IRFResult(
            irf_values=irf_values,
            periods=periods,
            confidence_intervals=confidence_intervals,
            standard_errors=standard_errors,
            variable_names=variable_names
        )
    
    def _validate_inputs(
        self,
        data: Union[np.ndarray, pd.DataFrame],
        periods: int,
        method: str,
        confidence_level: float,
        handle_missing: str
    ) -> None:
        """Validate input parameters."""
        if data is None or (isinstance(data, (np.ndarray, pd.DataFrame)) and data.size == 0):
            raise ValueError("Input data cannot be empty")
        
        if periods < 1:
            raise ValueError("Periods must be at least 1")
        
        if method not in ['ols', 'var']:
            raise ValueError(f"Unknown method: {method}")
        
        if not 0 < confidence_level < 1:
            raise ValueError("Confidence level must be between 0 and 1")
        
        if handle_missing not in ['drop', 'interpolate', 'raise']:
            raise ValueError(f"Unknown handle_missing option: {handle_missing}")
    
    def _preprocess_data(
        self,
        data: Union[np.ndarray, pd.DataFrame],
        handle_missing: str
    ) -> np.ndarray:
        """Preprocess data and handle missing values."""
        # Convert to numpy array
        if isinstance(data, pd.DataFrame):
            arr = data.values
        else:
            arr = np.asarray(data)
        
        # Ensure 2D array
        if arr.ndim == 1:
            arr = arr.reshape(-1, 1)
        
        # Handle missing values
        if np.any(np.isnan(arr)):
            if handle_missing == 'raise':
                raise ValueError("Data contains missing values")
            elif handle_missing == 'drop':
                # Remove rows with any NaN
                mask = ~np.any(np.isnan(arr), axis=1)
                arr = arr[mask]
                if arr.size == 0:
                    raise ValueError("All data removed after dropping missing values")
            elif handle_missing == 'interpolate':
                # Simple linear interpolation
                for i in range(arr.shape[1]):
                    mask = ~np.isnan(arr[:, i])
                    if np.any(mask):
                        arr[:, i] = np.interp(
                            np.arange(len(arr)),
                            np.arange(len(arr))[mask],
                            arr[:, i][mask]
                        )
        
        return arr
    
    def _calculate_irf_sequential(
        self,
        data: np.ndarray,
        periods: int,
        method: str
    ) -> np.ndarray:
        """Calculate IRF using sequential processing."""
        if method == 'ols':
            return self._calculate_ols_irf(data, periods)
        else:  # var
            return self._calculate_var_irf(data, periods)
    
    def _calculate_irf_parallel(
        self,
        data: np.ndarray,
        periods: int,
        method: str
    ) -> np.ndarray:
        """Calculate IRF using parallel processing."""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            if method == 'ols':
                future = executor.submit(self._calculate_ols_irf, data, periods)
            else:  # var
                future = executor.submit(self._calculate_var_irf, data, periods)
            return future.result()
    
    def _calculate_ols_irf(self, data: np.ndarray, periods: int) -> np.ndarray:
        """Calculate IRF using OLS method."""
        n_vars = data.shape[1]
        irf = np.zeros((periods, n_vars, n_vars))
        
        # Simple AR(1) model for each variable
        for i in range(n_vars):
            y = data[1:, i]
            X = data[:-1, :]
            
            # OLS estimation
            if X.shape[0] > 0:
                beta = np.linalg.lstsq(X, y, rcond=None)[0]
                
                # Calculate IRF
                shock = np.zeros(n_vars)
                shock[i] = 1.0
                
                response = shock.copy()
                irf[0, i, :] = response
                
                for t in range(1, periods):
                    response = beta * response[i] if n_vars == 1 else np.dot(beta, response)
                    irf[t, i, :] = response
        
        return irf
    
    def _calculate_var_irf(self, data: np.ndarray, periods: int) -> np.ndarray:
        """Calculate IRF using VAR method."""
        n_vars = data.shape[1]
        irf = np.zeros((periods, n_vars, n_vars))
        
        # Simplified VAR(1) estimation
        y = data[1:]
        X = data[:-1]
        
        if X.shape[0] > n_vars:
            # Estimate coefficient matrix
            A = np.linalg.lstsq(X, y, rcond=None)[0].T
            
            # Calculate IRF for each shock
            for i in range(n_vars):
                shock = np.zeros(n_vars)
                shock[i] = 1.0
                
                response = shock.copy()
                irf[0, i, :] = response
                
                for t in range(1, periods):
                    response = np.dot(A, response)
                    irf[t, i, :] = response
        else:
            # Not enough data for VAR, use identity
            for i in range(n_vars):
                irf[0, i, i] = 1.0
        
        return irf
    
    def _calculate_confidence_intervals(
        self,
        data: np.ndarray,
        irf: np.ndarray,
        confidence_level: float,
        method: str
    ) -> Dict[str, np.ndarray]:
        """Calculate confidence intervals for IRF."""
        # Bootstrap confidence intervals
        n_bootstrap = 100
        periods, n_vars, _ = irf.shape
        
        irf_bootstrap = np.zeros((n_bootstrap, periods, n_vars, n_vars))
        
        for b in range(n_bootstrap):
            # Resample data
            indices = np.random.choice(len(data) - 1, size=len(data) - 1, replace=True)
            data_boot = data[indices]
            
            # Recalculate IRF
            if method == 'ols':
                irf_bootstrap[b] = self._calculate_ols_irf(data_boot, periods)
            else:
                irf_bootstrap[b] = self._calculate_var_irf(data_boot, periods)
        
        # Calculate percentiles
        alpha = 1 - confidence_level
        lower = np.percentile(irf_bootstrap, 100 * alpha / 2, axis=0)
        upper = np.percentile(irf_bootstrap, 100 * (1 - alpha / 2), axis=0)
        
        return {
            'lower': lower,
            'upper': upper
        }
    
    def _calculate_standard_errors(
        self,
        data: np.ndarray,
        irf: np.ndarray,
        method: str
    ) -> np.ndarray:
        """Calculate standard errors for IRF."""
        # Bootstrap standard errors
        n_bootstrap = 100
        periods, n_vars, _ = irf.shape
        
        irf_bootstrap = np.zeros((n_bootstrap, periods, n_vars, n_vars))
        
        for b in range(n_bootstrap):
            # Resample data
            indices = np.random.choice(len(data) - 1, size=len(data) - 1, replace=True)
            data_boot = data[indices]
            
            # Recalculate IRF
            if method == 'ols':
                irf_bootstrap[b] = self._calculate_ols_irf(data_boot, periods)
            else:
                irf_bootstrap[b] = self._calculate_var_irf(data_boot, periods)
        
        # Calculate standard deviation
        return np.std(irf_bootstrap, axis=0)
    
    def batch_calculate(
        self,
        datasets: List[Union[np.ndarray, pd.DataFrame]],
        **kwargs
    ) -> List[IRFResult]:
        """
        Calculate IRF for multiple datasets in batch.
        
        Parameters
        ----------
        datasets : list of array-like
            List of datasets to process
        **kwargs : dict
            Additional parameters passed to calculate_irf
            
        Returns
        -------
        list of IRFResult
            Results for each dataset
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self.calculate_irf, data, **kwargs)
                for data in datasets
            ]
            
            for future in futures:
                try:
                    results.append(future.result())
                except Exception as e:
                    logger.error(f"Error in batch calculation: {e}")
                    results.append(None)
        
        return results
    
    def validate_results(self, result: IRFResult) -> bool:
        """
        Validate IRF calculation results.
        
        Parameters
        ----------
        result : IRFResult
            Result to validate
            
        Returns
        -------
        bool
            True if results are valid
        """
        if result is None:
            return False
        
        # Check basic properties
        if result.irf_values is None or result.periods < 1:
            return False
        
        # Check dimensions
        if result.irf_values.ndim != 3:
            return False
        
        # Check for NaN or Inf
        if np.any(np.isnan(result.irf_values)) or np.any(np.isinf(result.irf_values)):
            return False
        
        return True
```