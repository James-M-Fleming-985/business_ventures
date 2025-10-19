```python
"""Transfer entropy calculator implementation for causality testing."""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from functools import lru_cache


@dataclass
class TransferEntropyResult:
    """Container for transfer entropy calculation results."""
    
    transfer_entropy: float
    normalized_transfer_entropy: float
    statistical_significance: float
    confidence_interval: Tuple[float, float]
    computation_time: float
    metadata: Dict[str, Any]


class TransferEntropyCalculator:
    """Calculator for transfer entropy between time series.
    
    Transfer entropy measures the amount of information flow from one
    time series to another, providing a measure of causality.
    
    Attributes:
        history_length: Number of past values to consider
        future_length: Number of future values to predict
        bins: Number of bins for discretization
        estimator: Entropy estimator method ('empirical', 'knn')
        n_shuffles: Number of shuffles for significance testing
    """
    
    def __init__(
        self,
        history_length: int = 1,
        future_length: int = 1,
        bins: int = 10,
        estimator: str = 'empirical',
        n_shuffles: int = 100
    ):
        """Initialize transfer entropy calculator.
        
        Args:
            history_length: Number of past values to consider
            future_length: Number of future values to predict
            bins: Number of bins for discretization
            estimator: Entropy estimator method
            n_shuffles: Number of shuffles for significance testing
        """
        self.history_length = history_length
        self.future_length = future_length
        self.bins = bins
        self.estimator = estimator
        self.n_shuffles = n_shuffles
        self._validate_parameters()
    
    def _validate_parameters(self) -> None:
        """Validate initialization parameters."""
        if self.history_length < 1:
            raise ValueError("history_length must be >= 1")
        if self.future_length < 1:
            raise ValueError("future_length must be >= 1")
        if self.bins < 2:
            raise ValueError("bins must be >= 2")
        if self.estimator not in ['empirical', 'knn']:
            raise ValueError(f"Unknown estimator: {self.estimator}")
    
    def calculate(
        self,
        source: Union[np.ndarray, pd.Series, List],
        target: Union[np.ndarray, pd.Series, List],
        lag: int = 1,
        normalize: bool = True
    ) -> TransferEntropyResult:
        """Calculate transfer entropy from source to target.
        
        Args:
            source: Source time series
            target: Target time series
            lag: Time lag between series
            normalize: Whether to normalize the result
            
        Returns:
            TransferEntropyResult containing entropy values and statistics
            
        Raises:
            ValueError: If input data is invalid
            RuntimeError: If calculation fails
        """
        start_time = time.time()
        
        # Validate and prepare data
        source_arr, target_arr = self._prepare_data(source, target)
        
        # Calculate transfer entropy
        te_value = self._calculate_transfer_entropy(
            source_arr, target_arr, lag
        )
        
        # Calculate normalized transfer entropy
        if normalize:
            normalized_te = self._normalize_transfer_entropy(
                te_value, source_arr, target_arr, lag
            )
        else:
            normalized_te = te_value
        
        # Statistical significance testing
        p_value, ci = self._significance_test(
            source_arr, target_arr, lag, te_value
        )
        
        computation_time = time.time() - start_time
        
        metadata = {
            'lag': lag,
            'history_length': self.history_length,
            'future_length': self.future_length,
            'bins': self.bins,
            'estimator': self.estimator,
            'n_samples': len(source_arr),
            'n_shuffles': self.n_shuffles
        }
        
        return TransferEntropyResult(
            transfer_entropy=te_value,
            normalized_transfer_entropy=normalized_te,
            statistical_significance=p_value,
            confidence_interval=ci,
            computation_time=computation_time,
            metadata=metadata
        )
    
    def _prepare_data(
        self,
        source: Union[np.ndarray, pd.Series, List],
        target: Union[np.ndarray, pd.Series, List]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare and validate input data."""
        # Convert to numpy arrays
        source_arr = np.asarray(source)
        target_arr = np.asarray(target)
        
        # Handle pandas Series
        if isinstance(source, pd.Series):
            source_arr = source.values
        if isinstance(target, pd.Series):
            target_arr = target.values
        
        # Validate shapes
        if source_arr.ndim != 1 or target_arr.ndim != 1:
            raise ValueError("Input must be 1-dimensional")
        
        if len(source_arr) != len(target_arr):
            raise ValueError("Source and target must have same length")
        
        if len(source_arr) < self.history_length + self.future_length + 10:
            raise ValueError("Insufficient data for transfer entropy calculation")
        
        # Handle missing data
        source_arr, target_arr = self._handle_missing_data(source_arr, target_arr)
        
        return source_arr, target_arr
    
    def _handle_missing_data(
        self,
        source: np.ndarray,
        target: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Handle missing data in time series."""
        # Check for NaN/inf values
        source_mask = np.isfinite(source)
        target_mask = np.isfinite(target)
        combined_mask = source_mask & target_mask
        
        if not np.all(combined_mask):
            warnings.warn(
                f"Removing {np.sum(~combined_mask)} samples with missing data"
            )
            source = source[combined_mask]
            target = target[combined_mask]
        
        return source, target
    
    @lru_cache(maxsize=128)
    def _calculate_transfer_entropy(
        self,
        source: np.ndarray,
        target: np.ndarray,
        lag: int
    ) -> float:
        """Calculate transfer entropy using empirical estimator."""
        # Convert arrays to tuples for caching
        if isinstance(source, np.ndarray):
            source = tuple(source)
            target = tuple(target)
            source = np.array(source)
            target = np.array(target)
        
        # Discretize data
        source_disc = self._discretize(source)
        target_disc = self._discretize(target)
        
        # Prepare embedding vectors
        n_samples = len(source) - max(self.history_length + lag, 
                                      self.history_length + self.future_length)
        
        if n_samples <= 0:
            return 0.0
        
        # Create embedding vectors
        target_future = np.zeros(n_samples)
        target_past = np.zeros((n_samples, self.history_length))
        source_past = np.zeros((n_samples, self.history_length))
        
        for i in range(n_samples):
            idx = i + self.history_length + lag
            target_future[i] = target_disc[idx]
            
            for h in range(self.history_length):
                target_past[i, h] = target_disc[idx - h - 1]
                source_past[i, h] = source_disc[idx - lag - h - 1]
        
        # Calculate conditional entropies
        h_future_given_past = self._conditional_entropy(
            target_future, target_past
        )
        
        # Combine past information
        combined_past = np.column_stack([target_past, source_past])
        h_future_given_both = self._conditional_entropy(
            target_future, combined_past
        )
        
        # Transfer entropy is the reduction in uncertainty
        te = h_future_given_past - h_future_given_both
        
        return max(0.0, te)  # Ensure non-negative
    
    def _discretize(self, data: np.ndarray) -> np.ndarray:
        """Discretize continuous data into bins."""
        # Use percentile-based bins for better distribution
        percentiles = np.linspace(0, 100, self.bins + 1)
        bin_edges = np.percentile(data, percentiles)
        bin_edges[-1] += 1e-10  # Ensure last value is included
        
        # Discretize
        discretized = np.digitize(data, bin_edges) - 1
        discretized = np.clip(discretized, 0, self.bins - 1)
        
        return discretized
    
    def _conditional_entropy(
        self,
        x: np.ndarray,
        y: np.ndarray
    ) -> float:
        """Calculate conditional entropy H(X|Y)."""
        if y.ndim == 1:
            y = y.reshape(-1, 1)
        
        # Calculate joint probability
        joint_hist = self._joint_histogram(x, y)
        joint_prob = joint_hist / joint_hist.sum()
        
        # Calculate marginal of Y
        y_marginal = joint_prob.sum(axis=0)
        
        # Calculate conditional entropy
        h_conditional = 0.0
        for i in range(joint_prob.shape[0]):
            for j in range(joint_prob.shape[1]):
                if joint_prob[i, j] > 0 and y_marginal[j] > 0:
                    h_conditional -= joint_prob[i, j] * np.log2(
                        joint_prob[i, j] / y_marginal[j]
                    )
        
        return h_conditional
    
    def _joint_histogram(
        self,
        x: np.ndarray,
        y: np.ndarray
    ) -> np.ndarray:
        """Calculate joint histogram of x and y."""
        if y.ndim == 1:
            # 2D histogram
            hist, _, _ = np.histogram2d(x, y, bins=self.bins)
            return hist
        else:
            # Multi-dimensional histogram
            # Combine y columns into single index
            y_combined = np.zeros(len(y))
            multiplier = 1
            for col in range(y.shape[1] - 1, -1, -1):
                y_combined += y[:, col] * multiplier
                multiplier *= self.bins
            
            # Create histogram with combined index
            max_y_val = multiplier
            hist = np.zeros((self.bins, max_y_val))
            
            for i in range(len(x)):
                x_bin = int(x[i])
                y_bin = int(y_combined[i])
                if 0 <= x_bin < self.bins and 0 <= y_bin < max_y_val:
                    hist[x_bin, y_bin] += 1
            
            return hist
    
    def _normalize_transfer_entropy(
        self,
        te: float,
        source: np.ndarray,
        target: np.ndarray,
        lag: int
    ) -> float:
        """Normalize transfer entropy by target entropy."""
        # Discretize target
        target_disc = self._discretize(target)
        
        # Calculate entropy of target future values
        n_samples = len(target) - self.history_length - self.future_length
        if n_samples <= 0:
            return 0.0
        
        target_future = target_disc[self.history_length:self.history_length + n_samples]
        
        # Calculate entropy
        hist, _ = np.histogram(target_future, bins=self.bins)
        prob = hist / hist.sum()
        entropy = -np.sum(prob[prob > 0] * np.log2(prob[prob > 0]))
        
        if entropy > 0:
            return te / entropy
        else:
            return 0.0
    
    def _significance_test(
        self,
        source: np.ndarray,
        target: np.ndarray,
        lag: int,
        observed_te: float
    ) -> Tuple[float, Tuple[float, float]]:
        """Test statistical significance using permutation test."""
        surrogate_te_values = []
        
        # Generate surrogate data
        for _ in range(self.n_shuffles):
            # Shuffle source to break temporal relationships
            shuffled_source = np.random.permutation(source)
            
            # Calculate transfer entropy on surrogate
            surrogate_te = self._calculate_transfer_entropy(
                shuffled_source, target, lag
            )
            surrogate_te_values.append(surrogate_te)
        
        surrogate_te_values = np.array(surrogate_te_values)
        
        # Calculate p-value
        p_value = np.mean(surrogate_te_values >= observed_te)
        
        # Calculate confidence interval
        ci_lower = np.percentile(surrogate_te_values, 2.5)
        ci_upper = np.percentile(surrogate_te_values, 97.5)
        
        return p_value, (ci_lower, ci_upper)
    
    def calculate_pairwise(
        self,
        data: pd.DataFrame,
        pairs: List[Tuple[str, str]],
        lag: int = 1,
        normalize: bool = True,
        n_jobs: int = 1
    ) -> Dict[Tuple[str, str], TransferEntropyResult]:
        """Calculate transfer entropy for multiple pairs.
        
        Args:
            data: DataFrame containing time series
            pairs: List of (source, target) column pairs
            lag: Time lag between series
            normalize: Whether to normalize results
            n_jobs: Number of parallel jobs
            
        Returns:
            Dictionary mapping pairs to results
        """
        results = {}
        
        if n_jobs == 1:
            # Sequential execution
            for source_col, target_col in pairs:
                if source_col not in data.columns or target_col not in data.columns:
                    warnings.warn(f"Skipping pair ({source_col}, {target_col}): "
                                  "columns not found")
                    continue
                
                result = self.calculate(
                    data[source_col],
                    data[target_col],
                    lag=lag,
                    normalize=normalize
                )
                results[(source_col, target_col)] = result
        else:
            # Parallel execution
            with ThreadPoolExecutor(max_workers=n_jobs) as executor:
                future_to_pair = {}
                
                for source_col, target_col in pairs:
                    if source_col not in data.columns or target_col not in data.columns:
                        continue
                    
                    future = executor.submit(
                        self.calculate,
                        data[source_col],
                        data[target_col],
                        lag,
                        normalize
                    )
                    future_to_pair[future] = (source_col, target_col)
                
                for future in as_completed(future_to_pair):
                    pair = future_to_pair[future]
                    try:
                        result = future.result()
                        results[pair] = result
                    except Exception as e:
                        warnings.warn(f"Failed to calculate TE for {pair}: {e}")
        
        return results


class FeatureOrchestrator:
    """Orchestrates transfer entropy calculations with other features."""
    
    def __init__(self):
        """Initialize feature orchestrator."""
        self.calculator = TransferEntropyCalculator()
        self._cache = {}
    
    def calculate_features(
        self,
        data: pd.DataFrame,
        feature_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate transfer entropy features based on configuration.
        
        Args:
            data: Input data DataFrame
            feature_config: Configuration for feature calculation
            
        Returns:
            Dictionary of calculated features
        """
        results = {}
        
        # Extract configuration
        pairs = feature_config.get('pairs', [])
        lag = feature_config.get('lag', 1)
        normalize = feature_config.get('normalize', True)
        n_jobs = feature_config.get('n_jobs', 1)
        
        # Update calculator parameters if provided
        if 'history_length' in feature_config:
            self.calculator.history_length = feature_config['history_length']
        if 'bins' in feature_config:
            self.calculator.bins = feature_config['bins']
        
        # Calculate transfer entropy for all pairs
        te_results = self.calculator.calculate_pairwise(
            data, pairs, lag, normalize, n_jobs
        )
        
        # Format results
        for pair, result in te_results.items():
            feature_name = f"te_{pair[0]}_to_{pair[1]}"
            results[feature_name] = {
                'value': result.transfer_entropy,
                'normalized': result.normalized_transfer_entropy,
                'p_value': result.statistical_significance,
                'significant': result.statistical_significance < 0.05,
                'metadata': result.metadata
            }
        
        return results
    
    def integrate_with_pipeline(
        self,
        pipeline: Any,
        position: str = 'after_preprocessing'
    ) -> None:
        """Integrate transfer entropy calculation into existing pipeline.
        
        Args:
            pipeline: Existing data processing pipeline
            position: Where to insert transfer entropy calculation
        """
        # This is a placeholder for pipeline integration
        # Actual implementation would depend on pipeline structure
        pass
```