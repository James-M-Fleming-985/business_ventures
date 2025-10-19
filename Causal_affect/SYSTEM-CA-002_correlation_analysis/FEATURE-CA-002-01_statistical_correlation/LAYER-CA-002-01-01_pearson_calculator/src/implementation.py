```python
"""Pearson correlation calculator implementation."""

import numpy as np
import pandas as pd
from typing import Union, Dict, Any, Optional, Tuple
from scipy import stats
import warnings
import logging
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)


class PearsonCalculator:
    """Calculate Pearson correlation coefficients with statistical significance.
    
    This class provides methods to compute Pearson correlation coefficients
    between variables, handling missing data and providing statistical
    significance testing.
    """
    
    def __init__(self):
        """Initialize the Pearson calculator."""
        self._executor = ThreadPoolExecutor(max_workers=4)
        
    def calculate(self, x: Union[np.ndarray, pd.Series, list], 
                  y: Union[np.ndarray, pd.Series, list],
                  handle_missing: str = 'pairwise') -> Dict[str, Any]:
        """Calculate Pearson correlation coefficient between two variables.
        
        Args:
            x: First variable data
            y: Second variable data
            handle_missing: How to handle missing values ('pairwise', 'complete', 'drop')
                - 'pairwise': Use available pairs of observations
                - 'complete': Use only complete cases
                - 'drop': Drop any row with missing values
        
        Returns:
            Dict containing:
                - coefficient: Pearson correlation coefficient
                - p_value: Two-tailed p-value for testing non-correlation
                - n_observations: Number of valid observations used
                - confidence_interval: 95% confidence interval (tuple)
                
        Raises:
            ValueError: If input arrays have different lengths or insufficient data
            TypeError: If input types are invalid
        """
        # Validate inputs
        x_arr, y_arr = self._validate_and_convert_inputs(x, y)
        
        # Handle missing data
        x_clean, y_clean = self._handle_missing_data(x_arr, y_arr, handle_missing)
        
        # Check minimum requirements
        if len(x_clean) < 2:
            raise ValueError("Insufficient data for correlation calculation (need at least 2 observations)")
            
        # Calculate correlation
        start_time = time.time()
        
        # Use scipy for correlation and p-value
        correlation, p_value = stats.pearsonr(x_clean, y_clean)
        
        # Calculate confidence interval
        ci_lower, ci_upper = self._calculate_confidence_interval(correlation, len(x_clean))
        
        # Check performance requirement
        elapsed = time.time() - start_time
        if elapsed > 5.0 and len(x_clean) <= 10000:
            logger.warning(f"Calculation took {elapsed:.2f}s for {len(x_clean)} points")
        
        return {
            'coefficient': float(correlation),
            'p_value': float(p_value),
            'n_observations': len(x_clean),
            'confidence_interval': (float(ci_lower), float(ci_upper))
        }
    
    def calculate_matrix(self, data: Union[np.ndarray, pd.DataFrame],
                        handle_missing: str = 'pairwise') -> pd.DataFrame:
        """Calculate correlation matrix for multiple variables.
        
        Args:
            data: Data matrix with variables as columns
            handle_missing: How to handle missing values
            
        Returns:
            Correlation matrix as pandas DataFrame
            
        Raises:
            ValueError: If data has insufficient observations
            TypeError: If data type is invalid
        """
        # Convert to DataFrame if needed
        if isinstance(data, np.ndarray):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise TypeError("Data must be numpy array or pandas DataFrame")
            
        # Handle missing data based on strategy
        if handle_missing == 'complete':
            df = df.dropna()
        elif handle_missing == 'drop':
            df = df.dropna()
            
        if len(df) < 2:
            raise ValueError("Insufficient data for correlation calculation")
            
        # Calculate correlation matrix
        if handle_missing == 'pairwise':
            corr_matrix = df.corr(method='pearson')
        else:
            corr_matrix = df.corr(method='pearson')
            
        return corr_matrix
    
    def calculate_partial(self, x: Union[np.ndarray, pd.Series],
                         y: Union[np.ndarray, pd.Series],
                         z: Union[np.ndarray, pd.Series, pd.DataFrame],
                         handle_missing: str = 'pairwise') -> Dict[str, Any]:
        """Calculate partial correlation controlling for other variables.
        
        Args:
            x: First variable
            y: Second variable
            z: Control variable(s)
            handle_missing: How to handle missing values
            
        Returns:
            Dict with partial correlation results
        """
        # Convert inputs
        x_arr = self._to_array(x)
        y_arr = self._to_array(y)
        
        if isinstance(z, (pd.DataFrame, np.ndarray)) and z.ndim == 2:
            z_arr = z
        else:
            z_arr = self._to_array(z).reshape(-1, 1)
            
        # Combine all data
        if isinstance(z_arr, pd.DataFrame):
            all_data = pd.DataFrame({
                'x': x_arr,
                'y': y_arr
            })
            all_data = pd.concat([all_data, z_arr], axis=1)
        else:
            all_data = np.column_stack([x_arr, y_arr, z_arr])
            
        # Handle missing data
        if handle_missing in ['complete', 'drop']:
            if isinstance(all_data, pd.DataFrame):
                all_data = all_data.dropna()
                x_clean = all_data['x'].values
                y_clean = all_data['y'].values
                z_clean = all_data.iloc[:, 2:].values
            else:
                mask = ~np.any(np.isnan(all_data), axis=1)
                all_data = all_data[mask]
                x_clean = all_data[:, 0]
                y_clean = all_data[:, 1]
                z_clean = all_data[:, 2:]
        else:
            if isinstance(all_data, pd.DataFrame):
                x_clean = all_data['x'].values
                y_clean = all_data['y'].values
                z_clean = all_data.iloc[:, 2:].values
            else:
                x_clean = all_data[:, 0]
                y_clean = all_data[:, 1]
                z_clean = all_data[:, 2:]
                
        # Calculate residuals
        x_resid = self._calculate_residuals(x_clean, z_clean)
        y_resid = self._calculate_residuals(y_clean, z_clean)
        
        # Calculate partial correlation
        result = self.calculate(x_resid, y_resid, handle_missing='complete')
        result['control_variables'] = z_clean.shape[1] if z_clean.ndim > 1 else 1
        
        return result
    
    def _validate_and_convert_inputs(self, x: Any, y: Any) -> Tuple[np.ndarray, np.ndarray]:
        """Validate and convert inputs to numpy arrays."""
        x_arr = self._to_array(x)
        y_arr = self._to_array(y)
        
        if len(x_arr) != len(y_arr):
            raise ValueError(f"Input arrays must have same length: {len(x_arr)} != {len(y_arr)}")
            
        return x_arr, y_arr
    
    def _to_array(self, data: Any) -> np.ndarray:
        """Convert various input types to numpy array."""
        if isinstance(data, np.ndarray):
            return data.astype(float)
        elif isinstance(data, pd.Series):
            return data.values.astype(float)
        elif isinstance(data, list):
            return np.array(data, dtype=float)
        else:
            raise TypeError(f"Unsupported data type: {type(data)}")
    
    def _handle_missing_data(self, x: np.ndarray, y: np.ndarray, 
                           method: str) -> Tuple[np.ndarray, np.ndarray]:
        """Handle missing data according to specified method."""
        if method in ['pairwise', 'complete', 'drop']:
            # Create mask for valid observations
            mask = ~(np.isnan(x) | np.isnan(y))
            return x[mask], y[mask]
        else:
            raise ValueError(f"Unknown missing data method: {method}")
    
    def _calculate_confidence_interval(self, r: float, n: int, 
                                     alpha: float = 0.05) -> Tuple[float, float]:
        """Calculate confidence interval for correlation coefficient using Fisher's z-transform."""
        # Fisher's z-transformation
        z = 0.5 * np.log((1 + r) / (1 - r))
        
        # Standard error
        se = 1 / np.sqrt(n - 3)
        
        # Critical value
        z_crit = stats.norm.ppf(1 - alpha/2)
        
        # Confidence interval in z-space
        z_lower = z - z_crit * se
        z_upper = z + z_crit * se
        
        # Transform back to r-space
        r_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
        r_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)
        
        return r_lower, r_upper
    
    def _calculate_residuals(self, y: np.ndarray, x: np.ndarray) -> np.ndarray:
        """Calculate residuals from linear regression."""
        # Remove any rows with NaN
        mask = ~(np.isnan(y) | np.any(np.isnan(x), axis=1 if x.ndim > 1 else 0))
        y_clean = y[mask]
        x_clean = x[mask] if x.ndim == 1 else x[mask, :]
        
        # Add intercept
        if x_clean.ndim == 1:
            x_clean = x_clean.reshape(-1, 1)
        x_with_intercept = np.column_stack([np.ones(len(x_clean)), x_clean])
        
        # Calculate coefficients using least squares
        coeffs = np.linalg.lstsq(x_with_intercept, y_clean, rcond=None)[0]
        
        # Calculate predictions and residuals
        predictions = x_with_intercept @ coeffs
        residuals_clean = y_clean - predictions
        
        # Return residuals with NaN for removed observations
        residuals = np.full_like(y, np.nan)
        residuals[mask] = residuals_clean
        
        return residuals[mask]
    
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self._executor.shutdown(wait=True)
        
    def integrate_with_orchestrator(self, orchestrator: Any) -> None:
        """Integrate calculator with feature orchestrator.
        
        Args:
            orchestrator: Feature orchestrator instance
        """
        # Register this calculator with the orchestrator
        if hasattr(orchestrator, 'register_calculator'):
            orchestrator.register_calculator('pearson', self)
        
    def calculate_concurrent(self, pairs: list) -> list:
        """Calculate correlations for multiple variable pairs concurrently.
        
        Args:
            pairs: List of (x, y) tuples
            
        Returns:
            List of correlation results
        """
        futures = []
        for x, y in pairs:
            future = self._executor.submit(self.calculate, x, y)
            futures.append(future)
            
        results = []
        for future in futures:
            results.append(future.result())
            
        return results
```