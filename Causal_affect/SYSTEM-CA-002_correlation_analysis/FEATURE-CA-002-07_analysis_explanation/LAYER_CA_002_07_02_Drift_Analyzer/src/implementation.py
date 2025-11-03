```python
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from typing import Dict, List, Tuple, Optional, Any, Union
import warnings
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DriftResult:
    """Container for drift detection results."""
    drift_score: float
    drift_detected: bool
    drift_type: str
    details: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class DriftAnalyzer:
    """Analyzes data drift between reference and current datasets."""
    
    def __init__(self, method: str = 'ks', threshold: float = 0.05):
        """
        Initialize DriftAnalyzer.
        
        Args:
            method: Method for drift detection ('ks', 'chi2', 'psi', 'wasserstein')
            threshold: Threshold for drift detection
        """
        self.method = method.lower()
        self.threshold = threshold
        self.reference_data = None
        self.current_data = None
        self.drift_history = []
        
    def fit(self, reference_data: Union[pd.DataFrame, np.ndarray]) -> 'DriftAnalyzer':
        """
        Fit the analyzer with reference data.
        
        Args:
            reference_data: Reference dataset
            
        Returns:
            Self
        """
        if isinstance(reference_data, pd.DataFrame):
            self.reference_data = reference_data.copy()
        else:
            self.reference_data = pd.DataFrame(reference_data)
        return self
        
    def detect_drift(self, current_data: Union[pd.DataFrame, np.ndarray]) -> DriftResult:
        """
        Detect drift between reference and current data.
        
        Args:
            current_data: Current dataset to compare against reference
            
        Returns:
            DriftResult object containing drift detection results
        """
        if self.reference_data is None:
            raise ValueError("Reference data not set. Call fit() first.")
            
        if isinstance(current_data, pd.DataFrame):
            self.current_data = current_data.copy()
        else:
            self.current_data = pd.DataFrame(current_data)
            
        # Ensure column alignment
        if isinstance(self.reference_data, pd.DataFrame) and isinstance(self.current_data, pd.DataFrame):
            common_cols = list(set(self.reference_data.columns) & set(self.current_data.columns))
            if not common_cols:
                common_cols = list(range(min(self.reference_data.shape[1], self.current_data.shape[1])))
            self.reference_data = self.reference_data[common_cols]
            self.current_data = self.current_data[common_cols]
        
        if self.method == 'ks':
            result = self._ks_test()
        elif self.method == 'chi2':
            result = self._chi2_test()
        elif self.method == 'psi':
            result = self._psi_test()
        elif self.method == 'wasserstein':
            result = self._wasserstein_test()
        else:
            raise ValueError(f"Unknown method: {self.method}")
            
        self.drift_history.append(result)
        return result
        
    def _ks_test(self) -> DriftResult:
        """Perform Kolmogorov-Smirnov test for drift detection."""
        from scipy import stats
        
        drift_scores = []
        p_values = []
        
        for col in self.reference_data.columns:
            ref_col = self.reference_data[col].dropna()
            curr_col = self.current_data[col].dropna()
            
            if len(ref_col) == 0 or len(curr_col) == 0:
                continue
                
            if pd.api.types.is_numeric_dtype(ref_col):
                statistic, p_value = stats.ks_2samp(ref_col, curr_col)
                drift_scores.append(statistic)
                p_values.append(p_value)
                
        if drift_scores:
            drift_score = np.mean(drift_scores)
            avg_p_value = np.mean(p_values)
            drift_detected = avg_p_value < self.threshold
        else:
            drift_score = 0.0
            drift_detected = False
            avg_p_value = 1.0
            
        return DriftResult(
            drift_score=drift_score,
            drift_detected=drift_detected,
            drift_type='distribution',
            details={
                'p_value': avg_p_value,
                'column_scores': drift_scores,
                'method': 'ks'
            }
        )
        
    def _chi2_test(self) -> DriftResult:
        """Perform Chi-square test for drift detection."""
        from scipy import stats
        
        drift_scores = []
        p_values = []
        
        for col in self.reference_data.columns:
            ref_col = self.reference_data[col].dropna()
            curr_col = self.current_data[col].dropna()
            
            if len(ref_col) == 0 or len(curr_col) == 0:
                continue
                
            # For categorical or discretized numerical data
            try:
                # Create frequency tables
                all_values = pd.concat([ref_col, curr_col]).unique()
                ref_freq = ref_col.value_counts().reindex(all_values, fill_value=0)
                curr_freq = curr_col.value_counts().reindex(all_values, fill_value=0)
                
                # Chi-square test
                chi2, p_value = stats.chisquare(curr_freq, ref_freq * (curr_freq.sum() / ref_freq.sum()))
                drift_scores.append(chi2)
                p_values.append(p_value)
            except:
                continue
                
        if drift_scores:
            drift_score = np.mean(drift_scores)
            avg_p_value = np.mean(p_values)
            drift_detected = avg_p_value < self.threshold
        else:
            drift_score = 0.0
            drift_detected = False
            avg_p_value = 1.0
            
        return DriftResult(
            drift_score=drift_score,
            drift_detected=drift_detected,
            drift_type='distribution',
            details={
                'p_value': avg_p_value,
                'column_scores': drift_scores,
                'method': 'chi2'
            }
        )
        
    def _psi_test(self) -> DriftResult:
        """Calculate Population Stability Index for drift detection."""
        drift_scores = []
        
        for col in self.reference_data.columns:
            ref_col = self.reference_data[col].dropna()
            curr_col = self.current_data[col].dropna()
            
            if len(ref_col) == 0 or len(curr_col) == 0:
                continue
                
            try:
                # Bin numerical data
                if pd.api.types.is_numeric_dtype(ref_col):
                    n_bins = min(10, int(np.sqrt(len(ref_col))))
                    _, bins = np.histogram(ref_col, bins=n_bins)
                    ref_hist, _ = np.histogram(ref_col, bins=bins)
                    curr_hist, _ = np.histogram(curr_col, bins=bins)
                    
                    # Normalize
                    ref_hist = ref_hist / ref_hist.sum()
                    curr_hist = curr_hist / curr_hist.sum()
                    
                    # Calculate PSI
                    psi = 0
                    for i in range(len(ref_hist)):
                        if ref_hist[i] > 0 and curr_hist[i] > 0:
                            psi += (curr_hist[i] - ref_hist[i]) * np.log(curr_hist[i] / ref_hist[i])
                            
                    drift_scores.append(psi)
            except:
                continue
                
        if drift_scores:
            drift_score = np.mean(drift_scores)
            # PSI thresholds: < 0.1 (no drift), 0.1-0.2 (moderate), > 0.2 (significant)
            drift_detected = drift_score > 0.2
        else:
            drift_score = 0.0
            drift_detected = False
            
        return DriftResult(
            drift_score=drift_score,
            drift_detected=drift_detected,
            drift_type='distribution',
            details={
                'column_scores': drift_scores,
                'method': 'psi'
            }
        )
        
    def _wasserstein_test(self) -> DriftResult:
        """Calculate Wasserstein distance for drift detection."""
        from scipy.stats import wasserstein_distance
        
        drift_scores = []
        
        for col in self.reference_data.columns:
            ref_col = self.reference_data[col].dropna()
            curr_col = self.current_data[col].dropna()
            
            if len(ref_col) == 0 or len(curr_col) == 0:
                continue
                
            if pd.api.types.is_numeric_dtype(ref_col):
                try:
                    distance = wasserstein_distance(ref_col, curr_col)
                    drift_scores.append(distance)
                except:
                    continue
                    
        if drift_scores:
            drift_score = np.mean(drift_scores)
            # Normalize by standard deviation for threshold comparison
            ref_std = self.reference_data.std().mean()
            normalized_score = drift_score / (ref_std + 1e-8)
            drift_detected = normalized_score > self.threshold
        else:
            drift_score = 0.0
            drift_detected = False
            
        return DriftResult(
            drift_score=drift_score,
            drift_detected=drift_detected,
            drift_type='distribution',
            details={
                'column_scores': drift_scores,
                'method': 'wasserstein'
            }
        )
        
    def get_drift_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive drift report.
        
        Returns:
            Dictionary containing drift analysis results
        """
        if not self.drift_history:
            return {
                'status': 'No drift detection performed',
                'history': []
            }
            
        latest_result = self.drift_history[-1]
        
        return {
            'current_drift_score': latest_result.drift_score,
            'drift_detected': latest_result.drift_detected,
            'drift_type': latest_result.drift_type,
            'method': self.method,
            'threshold': self.threshold,
            'timestamp': latest_result.timestamp.isoformat(),
            'details': latest_result.details,
            'history_length': len(self.drift_history),
            'drift_trend': self._calculate_drift_trend()
        }
        
    def _calculate_drift_trend(self) -> str:
        """Calculate trend in drift scores."""
        if len(self.drift_history) < 2:
            return 'insufficient_data'
            
        scores = [result.drift_score for result in self.drift_history[-5:]]
        
        if len(scores) >= 2:
            # Simple linear trend
            x = np.arange(len(scores))
            slope = np.polyfit(x, scores, 1)[0]
            
            if slope > 0.01:
                return 'increasing'
            elif slope < -0.01:
                return 'decreasing'
            else:
                return 'stable'
        
        return 'unknown'


class ConceptDriftDetector:
    """Detects concept drift in model predictions."""
    
    def __init__(self, window_size: int = 100, threshold: float = 0.05):
        """
        Initialize ConceptDriftDetector.
        
        Args:
            window_size: Size of sliding window for drift detection
            threshold: Threshold for drift detection
        """
        self.window_size = window_size
        self.threshold = threshold
        self.error_rates = []
        self.predictions = []
        self.actuals = []
        
    def update(self, y_true: np.ndarray, y_pred: np.ndarray) -> bool:
        """
        Update detector with new predictions and check for drift.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            
        Returns:
            True if drift detected, False otherwise
        """
        # Store predictions
        self.predictions.extend(y_pred.flatten().tolist())
        self.actuals.extend(y_true.flatten().tolist())
        
        # Calculate error rate for current batch
        error_rate = np.mean(y_true != y_pred)
        self.error_rates.append(error_rate)
        
        # Check for drift if we have enough data
        if len(self.error_rates) >= 2 * self.window_size:
            # Compare recent window with previous window
            recent_errors = self.error_rates[-self.window_size:]
            previous_errors = self.error_rates[-2*self.window_size:-self.window_size]
            
            # Statistical test for difference in error rates
            from scipy import stats
            _, p_value = stats.ttest_ind(recent_errors, previous_errors)
            
            return p_value < self.threshold
            
        return False
        
    def get_drift_info(self) -> Dict[str, Any]:
        """
        Get information about detected drift.
        
        Returns:
            Dictionary containing drift information
        """
        if len(self.error_rates) < self.window_size:
            return {
                'drift_detected': False,
                'current_error_rate': self.error_rates[-1] if self.error_rates else 0.0,
                'window_error_rate': np.mean(self.error_rates) if self.error_rates else 0.0,
                'samples_processed': len(self.predictions)
            }
            
        recent_errors = self.error_rates[-self.window_size:]
        
        return {
            'drift_detected': self.update(np.array([0]), np.array([0])),  # Dummy check
            'current_error_rate': self.error_rates[-1],
            'window_error_rate': np.mean(recent_errors),
            'error_trend': 'increasing' if np.mean(recent_errors) > np.mean(self.error_rates[:-self.window_size]) else 'stable',
            'samples_processed': len(self.predictions)
        }


class DataDriftVisualizer:
    """Visualizes data drift patterns."""
    
    def __init__(self):
        """Initialize DataDriftVisualizer."""
        self.drift_scores = []
        self.timestamps = []
        
    def add_drift_result(self, result: DriftResult):
        """
        Add drift result for visualization.
        
        Args:
            result: DriftResult object
        """
        self.drift_scores.append(result.drift_score)
        self.timestamps.append(result.timestamp)
        
    def plot_drift_timeline(self) -> Dict[str, Any]:
        """
        Create drift timeline visualization data.
        
        Returns:
            Dictionary containing plot data
        """
        if not self.drift_scores:
            return {
                'x': [],
                'y': [],
                'title': 'Drift Timeline',
                'xlabel': 'Time',
                'ylabel': 'Drift Score'
            }
            
        return {
            'x': [ts.isoformat() for ts in self.timestamps],
            'y': self.drift_scores,
            'title': 'Drift Timeline',
            'xlabel': 'Time',
            'ylabel': 'Drift Score',
            'type': 'line'
        }
        
    def plot_feature_drift(self, reference_data: pd.DataFrame, current_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Create feature-wise drift visualization data.
        
        Args:
            reference_data: Reference dataset
            current_data: Current dataset
            
        Returns:
            List of plot data for each feature
        """
        plots = []
        
        common_cols = list(set(reference_data.columns) & set(current_data.columns))
        
        for col in common_cols:
            if pd.api.types.is_numeric_dtype(reference_data[col]):
                plot_data = {
                    'feature': col,
                    'reference': {
                        'data': reference_data[col].dropna().tolist(),
                        'type': 'histogram',
                        'label': 'Reference'
                    },
                    'current': {
                        'data': current_data[col].dropna().tolist(),
                        'type': 'histogram',
                        'label': 'Current'
                    },
                    'title': f'Distribution Comparison: {col}'
                }
                plots.append(plot_data)
                
        return plots
```