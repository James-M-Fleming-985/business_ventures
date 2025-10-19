```python
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import logging
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CorrelationMethod(Enum):
    SPEARMAN = "spearman"
    PEARSON = "pearson"
    KENDALL = "kendall"


@dataclass
class CorrelationResult:
    """Data class for correlation analysis results."""
    coefficient: float
    p_value: float
    method: str
    n_samples: int
    confidence_interval: Optional[Tuple[float, float]] = None
    metadata: Optional[Dict[str, Any]] = None


class SpearmanCalculator:
    """
    Calculator for Spearman rank correlation coefficient.
    
    This class provides methods to calculate Spearman correlation
    with proper handling of missing data and concurrent execution support.
    """
    
    def __init__(self, confidence_level: float = 0.95, max_workers: int = 4):
        """
        Initialize the SpearmanCalculator.
        
        Args:
            confidence_level: Confidence level for interval calculation (default: 0.95)
            max_workers: Maximum number of threads for concurrent execution (default: 4)
        """
        self.confidence_level = confidence_level
        self.max_workers = max_workers
        self._validate_confidence_level()
    
    def _validate_confidence_level(self):
        """Validate confidence level is within acceptable range."""
        if not 0 < self.confidence_level < 1:
            raise ValueError("Confidence level must be between 0 and 1")
    
    def calculate(self, x: List[float], y: List[float]) -> CorrelationResult:
        """
        Calculate Spearman correlation coefficient between two variables.
        
        Args:
            x: First variable data
            y: Second variable data
            
        Returns:
            CorrelationResult containing coefficient, p-value, and metadata
            
        Raises:
            ValueError: If input data is invalid or insufficient
        """
        start_time = time.time()
        
        # Validate inputs
        x_arr, y_arr = self._validate_and_clean_data(x, y)
        
        # Calculate correlation
        coefficient, p_value = stats.spearmanr(x_arr, y_arr)
        
        # Calculate confidence interval
        n_samples = len(x_arr)
        confidence_interval = self._calculate_confidence_interval(coefficient, n_samples)
        
        # Prepare metadata
        metadata = {
            "calculation_time": time.time() - start_time,
            "original_size": len(x),
            "cleaned_size": n_samples,
            "removed_pairs": len(x) - n_samples
        }
        
        return CorrelationResult(
            coefficient=float(coefficient),
            p_value=float(p_value),
            method=CorrelationMethod.SPEARMAN.value,
            n_samples=n_samples,
            confidence_interval=confidence_interval,
            metadata=metadata
        )
    
    def _validate_and_clean_data(self, x: List[float], y: List[float]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Validate and clean input data by removing missing values.
        
        Args:
            x: First variable data
            y: Second variable data
            
        Returns:
            Tuple of cleaned numpy arrays
            
        Raises:
            ValueError: If data is invalid or insufficient
        """
        if not x or not y:
            raise ValueError("Input data cannot be empty")
        
        if len(x) != len(y):
            raise ValueError("Input arrays must have the same length")
        
        # Convert to numpy arrays and handle missing data
        x_arr = np.array(x, dtype=float)
        y_arr = np.array(y, dtype=float)
        
        # Create mask for valid data (non-NaN, non-inf)
        valid_mask = ~(np.isnan(x_arr) | np.isnan(y_arr) | 
                      np.isinf(x_arr) | np.isinf(y_arr))
        
        x_clean = x_arr[valid_mask]
        y_clean = y_arr[valid_mask]
        
        if len(x_clean) < 3:
            raise ValueError("Insufficient data points after removing missing values. Need at least 3 pairs.")
        
        return x_clean, y_clean
    
    def _calculate_confidence_interval(self, r: float, n: int) -> Tuple[float, float]:
        """
        Calculate confidence interval for Spearman correlation using Fisher's Z transformation.
        
        Args:
            r: Correlation coefficient
            n: Number of samples
            
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        # Fisher's Z transformation
        z = 0.5 * np.log((1 + r) / (1 - r))
        
        # Standard error
        se = 1.0 / np.sqrt(n - 3)
        
        # Z-score for confidence level
        z_score = stats.norm.ppf((1 + self.confidence_level) / 2)
        
        # Calculate bounds
        z_lower = z - z_score * se
        z_upper = z + z_score * se
        
        # Transform back to correlation scale
        lower = np.tanh(z_lower)
        upper = np.tanh(z_upper)
        
        return (float(lower), float(upper))
    
    def calculate_pairwise(self, data: pd.DataFrame, 
                          variables: Optional[List[str]] = None) -> Dict[Tuple[str, str], CorrelationResult]:
        """
        Calculate pairwise Spearman correlations for multiple variables.
        
        Args:
            data: DataFrame containing variables
            variables: List of column names to analyze (default: all numeric columns)
            
        Returns:
            Dictionary mapping variable pairs to correlation results
        """
        if variables is None:
            variables = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(variables) < 2:
            raise ValueError("Need at least 2 variables for pairwise correlation")
        
        results = {}
        pairs = [(variables[i], variables[j]) 
                for i in range(len(variables)) 
                for j in range(i + 1, len(variables))]
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_pair = {
                executor.submit(self._calculate_pair, data[var1].values, data[var2].values): (var1, var2)
                for var1, var2 in pairs
            }
            
            for future in as_completed(future_to_pair):
                var1, var2 = future_to_pair[future]
                try:
                    result = future.result()
                    results[(var1, var2)] = result
                except Exception as e:
                    logger.error(f"Error calculating correlation for {var1}-{var2}: {e}")
        
        return results
    
    def _calculate_pair(self, x: np.ndarray, y: np.ndarray) -> CorrelationResult:
        """Helper method for concurrent calculation of single pair."""
        return self.calculate(x.tolist(), y.tolist())
    
    def calculate_with_bootstrapping(self, x: List[float], y: List[float], 
                                   n_bootstrap: int = 1000) -> CorrelationResult:
        """
        Calculate Spearman correlation with bootstrap confidence intervals.
        
        Args:
            x: First variable data
            y: Second variable data
            n_bootstrap: Number of bootstrap iterations
            
        Returns:
            CorrelationResult with bootstrap confidence interval
        """
        x_arr, y_arr = self._validate_and_clean_data(x, y)
        
        # Original calculation
        result = self.calculate(x, y)
        
        # Bootstrap
        bootstrap_coeffs = []
        n_samples = len(x_arr)
        
        for _ in range(n_bootstrap):
            indices = np.random.choice(n_samples, size=n_samples, replace=True)
            boot_x = x_arr[indices]
            boot_y = y_arr[indices]
            boot_coeff, _ = stats.spearmanr(boot_x, boot_y)
            bootstrap_coeffs.append(boot_coeff)
        
        # Calculate bootstrap confidence interval
        alpha = 1 - self.confidence_level
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100
        
        ci_lower = np.percentile(bootstrap_coeffs, lower_percentile)
        ci_upper = np.percentile(bootstrap_coeffs, upper_percentile)
        
        result.confidence_interval = (float(ci_lower), float(ci_upper))
        result.metadata['bootstrap_iterations'] = n_bootstrap
        
        return result


class FeatureOrchestrator:
    """Orchestrator for feature calculation and integration."""
    
    def __init__(self):
        self.calculators = {
            CorrelationMethod.SPEARMAN: SpearmanCalculator()
        }
    
    def calculate_correlation(self, x: List[float], y: List[float], 
                            method: CorrelationMethod = CorrelationMethod.SPEARMAN) -> CorrelationResult:
        """
        Calculate correlation using specified method.
        
        Args:
            x: First variable data
            y: Second variable data
            method: Correlation method to use
            
        Returns:
            CorrelationResult
        """
        calculator = self.calculators.get(method)
        if not calculator:
            raise ValueError(f"Unsupported correlation method: {method}")
        
        return calculator.calculate(x, y)
    
    def integrate_with_calculator(self, calculator_type: str) -> bool:
        """
        Integrate with a specific calculator type.
        
        Args:
            calculator_type: Type of calculator to integrate
            
        Returns:
            True if integration successful
        """
        if calculator_type.lower() == "spearman":
            return isinstance(self.calculators.get(CorrelationMethod.SPEARMAN), SpearmanCalculator)
        return False


# Utility functions for compatibility
def calculate_spearman_correlation(x: List[float], y: List[float]) -> Dict[str, Any]:
    """
    Convenience function to calculate Spearman correlation.
    
    Args:
        x: First variable data
        y: Second variable data
        
    Returns:
        Dictionary with correlation results
    """
    calculator = SpearmanCalculator()
    result = calculator.calculate(x, y)
    
    return {
        'coefficient': result.coefficient,
        'p_value': result.p_value,
        'n_samples': result.n_samples,
        'confidence_interval': result.confidence_interval,
        'method': result.method,
        'metadata': result.metadata
    }
```