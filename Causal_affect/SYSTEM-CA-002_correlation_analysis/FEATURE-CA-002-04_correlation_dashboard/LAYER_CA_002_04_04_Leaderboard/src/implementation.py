```python
"""
Leaderboard calculation module for correlation analysis dashboard.

This module provides functionality to calculate and manage leaderboard
rankings based on correlation scores and statistical metrics.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from datetime import datetime
import logging
from dataclasses import dataclass
from scipy import stats
import warnings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CorrelationResult:
    """Data class for correlation calculation results."""
    variable1: str
    variable2: str
    correlation: float
    p_value: float
    confidence_interval: Tuple[float, float]
    sample_size: int
    timestamp: datetime


@dataclass
class LeaderboardEntry:
    """Data class for leaderboard entries."""
    rank: int
    variable_pair: Tuple[str, str]
    correlation_score: float
    p_value: float
    confidence_interval: Tuple[float, float]
    sample_size: int
    significance_level: str
    last_updated: datetime


class LeaderboardCalculator:
    """
    Calculator for generating correlation leaderboards.
    
    Handles calculation of correlation rankings with proper
    statistical methods and concurrent execution support.
    """
    
    def __init__(self, 
                 max_workers: Optional[int] = None,
                 confidence_level: float = 0.95,
                 min_sample_size: int = 30):
        """
        Initialize the leaderboard calculator.
        
        Args:
            max_workers: Maximum number of concurrent workers
            confidence_level: Confidence level for intervals (default 0.95)
            min_sample_size: Minimum sample size for valid correlations
        """
        self.max_workers = max_workers
        self.confidence_level = confidence_level
        self.min_sample_size = min_sample_size
        self._cache = {}
        
    def calculate_correlations(self, 
                             data: pd.DataFrame,
                             variables: Optional[List[str]] = None,
                             method: str = 'pearson') -> List[CorrelationResult]:
        """
        Calculate correlations between variables.
        
        Args:
            data: DataFrame containing variables
            variables: List of variables to analyze (None for all)
            method: Correlation method ('pearson', 'spearman', 'kendall')
            
        Returns:
            List of correlation results
        """
        if variables is None:
            variables = data.select_dtypes(include=[np.number]).columns.tolist()
            
        results = []
        pairs = [(v1, v2) for i, v1 in enumerate(variables) 
                 for v2 in variables[i+1:]]
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self._calculate_pair_correlation,
                    data, v1, v2, method
                ): (v1, v2)
                for v1, v2 in pairs
            }
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
                    
        return results
    
    def _calculate_pair_correlation(self,
                                  data: pd.DataFrame,
                                  var1: str,
                                  var2: str,
                                  method: str) -> Optional[CorrelationResult]:
        """Calculate correlation for a single pair of variables."""
        try:
            # Extract data and handle missing values
            x = data[var1].dropna()
            y = data[var2].dropna()
            
            # Find common indices
            common_idx = x.index.intersection(y.index)
            if len(common_idx) < self.min_sample_size:
                return None
                
            x = x.loc[common_idx]
            y = y.loc[common_idx]
            
            # Calculate correlation
            if method == 'pearson':
                corr, p_value = stats.pearsonr(x, y)
            elif method == 'spearman':
                corr, p_value = stats.spearmanr(x, y)
            elif method == 'kendall':
                corr, p_value = stats.kendalltau(x, y)
            else:
                raise ValueError(f"Unknown correlation method: {method}")
            
            # Calculate confidence interval
            ci = self._calculate_confidence_interval(
                corr, len(common_idx), method
            )
            
            return CorrelationResult(
                variable1=var1,
                variable2=var2,
                correlation=corr,
                p_value=p_value,
                confidence_interval=ci,
                sample_size=len(common_idx),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.warning(f"Error calculating correlation for {var1}-{var2}: {e}")
            return None
    
    def _calculate_confidence_interval(self,
                                     correlation: float,
                                     n: int,
                                     method: str) -> Tuple[float, float]:
        """Calculate confidence interval for correlation coefficient."""
        if method == 'pearson':
            # Fisher z-transformation
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                z = 0.5 * np.log((1 + correlation) / (1 - correlation))
                se = 1 / np.sqrt(n - 3)
                z_crit = stats.norm.ppf((1 + self.confidence_level) / 2)
                
                z_lower = z - z_crit * se
                z_upper = z + z_crit * se
                
                # Transform back
                ci_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
                ci_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)
                
        else:
            # Bootstrap for non-parametric methods
            ci_lower = correlation - 1.96 / np.sqrt(n)
            ci_upper = correlation + 1.96 / np.sqrt(n)
            
        return (max(-1, ci_lower), min(1, ci_upper))
    
    def generate_leaderboard(self,
                           correlations: List[CorrelationResult],
                           top_k: Optional[int] = None,
                           min_correlation: Optional[float] = None,
                           sort_by: str = 'absolute') -> List[LeaderboardEntry]:
        """
        Generate leaderboard from correlation results.
        
        Args:
            correlations: List of correlation results
            top_k: Number of top entries to include
            min_correlation: Minimum absolute correlation threshold
            sort_by: Sort criterion ('absolute', 'positive', 'negative')
            
        Returns:
            Sorted list of leaderboard entries
        """
        entries = []
        
        for corr in correlations:
            # Apply filters
            if min_correlation and abs(corr.correlation) < min_correlation:
                continue
                
            # Determine significance level
            sig_level = self._get_significance_level(corr.p_value)
            
            # Create entry (rank will be assigned later)
            entry = LeaderboardEntry(
                rank=0,  # Will be updated
                variable_pair=(corr.variable1, corr.variable2),
                correlation_score=corr.correlation,
                p_value=corr.p_value,
                confidence_interval=corr.confidence_interval,
                sample_size=corr.sample_size,
                significance_level=sig_level,
                last_updated=corr.timestamp
            )
            entries.append(entry)
        
        # Sort entries
        if sort_by == 'absolute':
            entries.sort(key=lambda x: abs(x.correlation_score), reverse=True)
        elif sort_by == 'positive':
            entries.sort(key=lambda x: x.correlation_score, reverse=True)
        elif sort_by == 'negative':
            entries.sort(key=lambda x: x.correlation_score)
        
        # Apply top_k filter
        if top_k:
            entries = entries[:top_k]
        
        # Assign ranks
        for i, entry in enumerate(entries):
            entry.rank = i + 1
            
        return entries
    
    def _get_significance_level(self, p_value: float) -> str:
        """Determine significance level from p-value."""
        if p_value < 0.001:
            return "***"
        elif p_value < 0.01:
            return "**"
        elif p_value < 0.05:
            return "*"
        else:
            return "ns"
    
    def calculate_leaderboard(self,
                            data: pd.DataFrame,
                            variables: Optional[List[str]] = None,
                            method: str = 'pearson',
                            top_k: Optional[int] = None,
                            min_correlation: Optional[float] = None,
                            sort_by: str = 'absolute') -> Dict[str, Any]:
        """
        Calculate complete leaderboard from data.
        
        Args:
            data: Input DataFrame
            variables: Variables to analyze
            method: Correlation method
            top_k: Number of top entries
            min_correlation: Minimum correlation threshold
            sort_by: Sort criterion
            
        Returns:
            Dictionary with leaderboard results and metadata
        """
        start_time = time.time()
        
        # Calculate correlations
        correlations = self.calculate_correlations(data, variables, method)
        
        # Generate leaderboard
        leaderboard = self.generate_leaderboard(
            correlations, top_k, min_correlation, sort_by
        )
        
        # Prepare results
        execution_time = time.time() - start_time
        
        return {
            'leaderboard': leaderboard,
            'total_correlations': len(correlations),
            'displayed_entries': len(leaderboard),
            'execution_time': execution_time,
            'method': method,
            'timestamp': datetime.now(),
            'metadata': {
                'confidence_level': self.confidence_level,
                'min_sample_size': self.min_sample_size,
                'sort_by': sort_by,
                'filters': {
                    'top_k': top_k,
                    'min_correlation': min_correlation
                }
            }
        }
    
    def format_leaderboard(self,
                         leaderboard: List[LeaderboardEntry],
                         format_type: str = 'dataframe') -> Union[pd.DataFrame, List[Dict], str]:
        """
        Format leaderboard for display.
        
        Args:
            leaderboard: List of leaderboard entries
            format_type: Output format ('dataframe', 'dict', 'html')
            
        Returns:
            Formatted leaderboard
        """
        if format_type == 'dataframe':
            data = []
            for entry in leaderboard:
                data.append({
                    'Rank': entry.rank,
                    'Variable 1': entry.variable_pair[0],
                    'Variable 2': entry.variable_pair[1],
                    'Correlation': f"{entry.correlation_score:.3f}",
                    'P-Value': f"{entry.p_value:.4f}",
                    'CI Lower': f"{entry.confidence_interval[0]:.3f}",
                    'CI Upper': f"{entry.confidence_interval[1]:.3f}",
                    'Significance': entry.significance_level,
                    'Sample Size': entry.sample_size
                })
            return pd.DataFrame(data)
            
        elif format_type == 'dict':
            return [
                {
                    'rank': entry.rank,
                    'variables': list(entry.variable_pair),
                    'correlation': entry.correlation_score,
                    'p_value': entry.p_value,
                    'confidence_interval': list(entry.confidence_interval),
                    'significance': entry.significance_level,
                    'sample_size': entry.sample_size,
                    'last_updated': entry.last_updated.isoformat()
                }
                for entry in leaderboard
            ]
            
        elif format_type == 'html':
            df = self.format_leaderboard(leaderboard, 'dataframe')
            return df.to_html(index=False, classes='leaderboard-table')
            
        else:
            raise ValueError(f"Unknown format type: {format_type}")


class FeatureOrchestrator:
    """
    Orchestrator for leaderboard feature integration.
    
    Manages leaderboard calculations and integrates with
    the broader correlation analysis system.
    """
    
    def __init__(self):
        """Initialize the feature orchestrator."""
        self.calculator = LeaderboardCalculator()
        self.cache = {}
        self.last_calculation = None
        
    def process_correlation_request(self,
                                  data: pd.DataFrame,
                                  config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a correlation leaderboard request.
        
        Args:
            data: Input data
            config: Configuration options
            
        Returns:
            Processed results with leaderboard
        """
        # Default configuration
        default_config = {
            'variables': None,
            'method': 'pearson',
            'top_k': 20,
            'min_correlation': 0.1,
            'sort_by': 'absolute',
            'format': 'dataframe'
        }
        
        if config:
            default_config.update(config)
            
        # Calculate leaderboard
        results = self.calculator.calculate_leaderboard(
            data,
            variables=default_config['variables'],
            method=default_config['method'],
            top_k=default_config['top_k'],
            min_correlation=default_config['min_correlation'],
            sort_by=default_config['sort_by']
        )
        
        # Format output
        formatted_leaderboard = self.calculator.format_leaderboard(
            results['leaderboard'],
            default_config['format']
        )
        
        # Update cache
        self.last_calculation = results
        cache_key = self._generate_cache_key(data, default_config)
        self.cache[cache_key] = results
        
        return {
            'status': 'success',
            'data': formatted_leaderboard,
            'metadata': results['metadata'],
            'execution_time': results['execution_time'],
            'timestamp': results['timestamp']
        }
    
    def _generate_cache_key(self, data: pd.DataFrame, config: Dict) -> str:
        """Generate cache key for results."""
        data_hash = hash(tuple(data.columns) + (len(data),))
        config_hash = hash(frozenset(config.items()))
        return f"{data_hash}_{config_hash}"
    
    def get_cached_results(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached results if available."""
        return self.cache.get(cache_key)
    
    def clear_cache(self):
        """Clear the results cache."""
        self.cache.clear()
        self.last_calculation = None


# Module-level instances
leaderboard_calculator = LeaderboardCalculator()
feature_orchestrator = FeatureOrchestrator()


def calculate_leaderboard(data: pd.DataFrame,
                        **kwargs) -> Dict[str, Any]:
    """
    Convenience function to calculate correlation leaderboard.
    
    Args:
        data: Input DataFrame
        **kwargs: Additional configuration options
        
    Returns:
        Leaderboard results
    """
    return feature_orchestrator.process_correlation_request(data, kwargs)
```