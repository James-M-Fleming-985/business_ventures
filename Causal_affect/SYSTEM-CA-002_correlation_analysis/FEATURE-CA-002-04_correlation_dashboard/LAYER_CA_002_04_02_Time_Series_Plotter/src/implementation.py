```python
"""
Time Series Plotter implementation for correlation analysis dashboard.

This module provides functionality for plotting time series data with correlation
analysis capabilities, handling missing data, and supporting concurrent execution.
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Union, Any
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import seaborn as sns
from scipy import stats
import warnings
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import logging
from functools import lru_cache
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimeSeriesPlotter:
    """
    A class for plotting time series data with correlation analysis capabilities.
    
    Attributes:
        data (pd.DataFrame): The time series data to plot
        figure_size (Tuple[int, int]): Default figure size for plots
        style (str): Matplotlib style to use for plots
        _executor (ThreadPoolExecutor): Executor for concurrent operations
    """
    
    def __init__(self, data: Optional[pd.DataFrame] = None, 
                 figure_size: Tuple[int, int] = (12, 6),
                 style: str = 'seaborn'):
        """
        Initialize the TimeSeriesPlotter.
        
        Args:
            data: Initial DataFrame containing time series data
            figure_size: Tuple specifying (width, height) of plots
            style: Matplotlib style to apply to plots
        """
        self.data = data
        self.figure_size = figure_size
        self.style = style
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Apply style
        plt.style.use(style)
        
        # Suppress warnings for cleaner output
        warnings.filterwarnings('ignore', category=UserWarning)
    
    def set_data(self, data: pd.DataFrame) -> None:
        """
        Set or update the time series data.
        
        Args:
            data: DataFrame with time series data
            
        Raises:
            ValueError: If data is not a valid DataFrame
        """
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Data must be a pandas DataFrame")
        self.data = data
    
    def plot_time_series(self, columns: Optional[List[str]] = None,
                        title: str = "Time Series Plot",
                        xlabel: str = "Time",
                        ylabel: str = "Value",
                        show_grid: bool = True,
                        show_legend: bool = True) -> Figure:
        """
        Create a time series plot for specified columns.
        
        Args:
            columns: List of column names to plot. If None, plots all numeric columns
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            show_grid: Whether to show grid lines
            show_legend: Whether to show legend
            
        Returns:
            matplotlib.figure.Figure: The generated plot figure
            
        Raises:
            ValueError: If no data is set or columns are invalid
        """
        if self.data is None:
            raise ValueError("No data set. Use set_data() first.")
        
        # Determine columns to plot
        if columns is None:
            columns = self.data.select_dtypes(include=[np.number]).columns.tolist()
        
        # Validate columns exist
        invalid_cols = set(columns) - set(self.data.columns)
        if invalid_cols:
            raise ValueError(f"Columns not found in data: {invalid_cols}")
        
        # Create figure
        fig, ax = plt.subplots(figsize=self.figure_size)
        
        # Plot each column
        for col in columns:
            # Handle missing data by interpolating
            series = self.data[col].copy()
            if series.isna().any():
                series = series.interpolate(method='linear', limit_direction='both')
            
            ax.plot(self.data.index, series, label=col, alpha=0.8)
        
        # Customize plot
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        
        if show_grid:
            ax.grid(True, alpha=0.3)
        
        if show_legend and len(columns) > 0:
            ax.legend(loc='best')
        
        # Format x-axis if datetime index
        if isinstance(self.data.index, pd.DatetimeIndex):
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            fig.autofmt_xdate()
        
        plt.tight_layout()
        return fig
    
    def plot_correlation_matrix(self, columns: Optional[List[str]] = None,
                               method: str = 'pearson',
                               title: str = "Correlation Matrix",
                               cmap: str = 'coolwarm',
                               annot: bool = True) -> Figure:
        """
        Create a correlation matrix heatmap.
        
        Args:
            columns: Columns to include in correlation analysis
            method: Correlation method ('pearson', 'spearman', 'kendall')
            title: Plot title
            cmap: Colormap for the heatmap
            annot: Whether to annotate cells with correlation values
            
        Returns:
            matplotlib.figure.Figure: The correlation matrix plot
            
        Raises:
            ValueError: If invalid method or no numeric data
        """
        if self.data is None:
            raise ValueError("No data set. Use set_data() first.")
        
        # Select numeric columns
        if columns is None:
            numeric_data = self.data.select_dtypes(include=[np.number])
        else:
            numeric_data = self.data[columns].select_dtypes(include=[np.number])
        
        if numeric_data.empty:
            raise ValueError("No numeric data found for correlation analysis")
        
        # Calculate correlation matrix
        corr_matrix = numeric_data.corr(method=method)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create heatmap
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
        sns.heatmap(corr_matrix, mask=mask, cmap=cmap, center=0,
                    square=True, linewidths=0.5, cbar_kws={"shrink": .8},
                    annot=annot, fmt='.2f', ax=ax)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    def plot_rolling_correlation(self, col1: str, col2: str,
                                window: int = 30,
                                title: Optional[str] = None) -> Figure:
        """
        Plot rolling correlation between two time series.
        
        Args:
            col1: First column name
            col2: Second column name
            window: Rolling window size
            title: Plot title (auto-generated if None)
            
        Returns:
            matplotlib.figure.Figure: The rolling correlation plot
            
        Raises:
            ValueError: If columns not found or window invalid
        """
        if self.data is None:
            raise ValueError("No data set. Use set_data() first.")
        
        if col1 not in self.data.columns or col2 not in self.data.columns:
            raise ValueError(f"Columns {col1} or {col2} not found in data")
        
        if window < 2:
            raise ValueError("Window size must be at least 2")
        
        # Calculate rolling correlation
        rolling_corr = self.data[col1].rolling(window).corr(self.data[col2])
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.figure_size, height_ratios=[2, 1])
        
        # Plot time series
        ax1.plot(self.data.index, self.data[col1], label=col1, alpha=0.7)
        ax1.plot(self.data.index, self.data[col2], label=col2, alpha=0.7)
        ax1.set_ylabel('Value')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot rolling correlation
        ax2.plot(self.data.index, rolling_corr, color='green', linewidth=2)
        ax2.axhline(y=0, color='k', linestyle='--', alpha=0.5)
        ax2.set_ylabel(f'Rolling Correlation (window={window})')
        ax2.set_xlabel('Time')
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(-1.1, 1.1)
        
        # Set title
        if title is None:
            title = f"Rolling Correlation: {col1} vs {col2}"
        fig.suptitle(title, fontsize=14, fontweight='bold')
        
        # Format dates if applicable
        if isinstance(self.data.index, pd.DatetimeIndex):
            for ax in [ax1, ax2]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            fig.autofmt_xdate()
        
        plt.tight_layout()
        return fig
    
    def calculate_correlations(self, columns: Optional[List[str]] = None,
                             method: str = 'pearson',
                             handle_missing: str = 'interpolate') -> Dict[str, float]:
        """
        Calculate correlations between time series.
        
        Args:
            columns: Columns to analyze (all numeric if None)
            method: Correlation method
            handle_missing: How to handle missing data ('drop', 'interpolate', 'forward_fill')
            
        Returns:
            Dict mapping column pairs to correlation values
            
        Raises:
            ValueError: If invalid parameters
        """
        if self.data is None:
            raise ValueError("No data set. Use set_data() first.")
        
        # Select columns
        if columns is None:
            columns = self.data.select_dtypes(include=[np.number]).columns.tolist()
        
        # Handle missing data
        data_clean = self.data[columns].copy()
        
        if handle_missing == 'drop':
            data_clean = data_clean.dropna()
        elif handle_missing == 'interpolate':
            data_clean = data_clean.interpolate(method='linear', limit_direction='both')
        elif handle_missing == 'forward_fill':
            data_clean = data_clean.fillna(method='ffill')
        else:
            raise ValueError(f"Invalid handle_missing method: {handle_missing}")
        
        # Calculate correlations
        correlations = {}
        for i, col1 in enumerate(columns):
            for col2 in columns[i+1:]:
                if method == 'pearson':
                    corr, _ = stats.pearsonr(data_clean[col1], data_clean[col2])
                elif method == 'spearman':
                    corr, _ = stats.spearmanr(data_clean[col1], data_clean[col2])
                elif method == 'kendall':
                    corr, _ = stats.kendalltau(data_clean[col1], data_clean[col2])
                else:
                    raise ValueError(f"Invalid correlation method: {method}")
                
                correlations[f"{col1}_vs_{col2}"] = float(corr)
        
        return correlations
    
    async def calculate_correlations_async(self, columns: Optional[List[str]] = None,
                                         method: str = 'pearson') -> Dict[str, float]:
        """
        Asynchronously calculate correlations for better performance.
        
        Args:
            columns: Columns to analyze
            method: Correlation method
            
        Returns:
            Dict of correlation values
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.calculate_correlations, 
            columns, 
            method
        )
    
    def detect_correlation_changes(self, col1: str, col2: str,
                                 window: int = 30,
                                 threshold: float = 0.2) -> List[Dict[str, Any]]:
        """
        Detect significant changes in correlation over time.
        
        Args:
            col1: First column
            col2: Second column
            window: Rolling window size
            threshold: Minimum change to be considered significant
            
        Returns:
            List of dicts containing change points and details
        """
        if self.data is None:
            raise ValueError("No data set. Use set_data() first.")
        
        # Calculate rolling correlation
        rolling_corr = self.data[col1].rolling(window).corr(self.data[col2])
        
        # Find change points
        changes = []
        corr_diff = rolling_corr.diff()
        
        for i in range(1, len(corr_diff)):
            if abs(corr_diff.iloc[i]) > threshold:
                changes.append({
                    'index': self.data.index[i],
                    'correlation_before': rolling_corr.iloc[i-1],
                    'correlation_after': rolling_corr.iloc[i],
                    'change': corr_diff.iloc[i]
                })
        
        return changes
    
    def save_plot(self, fig: Figure, filename: str, dpi: int = 300) -> None:
        """
        Save a plot to file.
        
        Args:
            fig: Figure to save
            filename: Output filename
            dpi: Resolution in dots per inch
        """
        fig.savefig(filename, dpi=dpi, bbox_inches='tight')
        logger.info(f"Plot saved to {filename}")
    
    def get_summary_statistics(self, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Get summary statistics for time series data.
        
        Args:
            columns: Columns to summarize
            
        Returns:
            DataFrame with summary statistics
        """
        if self.data is None:
            raise ValueError("No data set. Use set_data() first.")
        
        if columns is None:
            columns = self.data.select_dtypes(include=[np.number]).columns.tolist()
        
        summary = self.data[columns].describe()
        
        # Add additional statistics
        summary.loc['skew'] = self.data[columns].skew()
        summary.loc['kurtosis'] = self.data[columns].kurtosis()
        summary.loc['missing'] = self.data[columns].isna().sum()
        
        return summary
    
    def __del__(self):
        """Clean up resources."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)


class FeatureOrchestrator:
    """
    Orchestrator for managing multiple time series plotting features.
    """
    
    def __init__(self):
        """Initialize the feature orchestrator."""
        self.plotters = {}
        self.results_cache = {}
    
    def register_plotter(self, name: str, plotter: TimeSeriesPlotter) -> None:
        """
        Register a time series plotter.
        
        Args:
            name: Unique identifier for the plotter
            plotter: TimeSeriesPlotter instance
        """
        self.plotters[name] = plotter
        logger.info(f"Registered plotter: {name}")
    
    def execute_analysis(self, plotter_name: str, 
                        analysis_type: str,
                        **kwargs) -> Any:
        """
        Execute an analysis using a registered plotter.
        
        Args:
            plotter_name: Name of the plotter to use
            analysis_type: Type of analysis to perform
            **kwargs: Additional arguments for the analysis
            
        Returns:
            Analysis results
            
        Raises:
            KeyError: If plotter not found
            ValueError: If invalid analysis type
        """
        if plotter_name not in self.plotters:
            raise KeyError(f"Plotter '{plotter_name}' not found")
        
        plotter = self.plotters[plotter_name]
        
        # Map analysis types to methods
        analysis_methods = {
            'time_series': plotter.plot_time_series,
            'correlation_matrix': plotter.plot_correlation_matrix,
            'rolling_correlation': plotter.plot_rolling_correlation,
            'calculate_correlations': plotter.calculate_correlations,
            'detect_changes': plotter.detect_correlation_changes,
            'summary_stats': plotter.get_summary_statistics
        }
        
        if analysis_type not in analysis_methods:
            raise ValueError(f"Invalid analysis type: {analysis_type}")
        
        # Execute with timing
        start_time = time.time()
        result = analysis_methods[analysis_type](**kwargs)
        execution_time = time.time() - start_time
        
        # Cache results
        cache_key = f"{plotter_name}_{analysis_type}_{str(kwargs)}"
        self.results_cache[cache_key] = {
            'result': result,
            'execution_time': execution_time,
            'timestamp': datetime.now()
        }
        
        logger.info(f"Executed {analysis_type} in {execution_time:.3f} seconds")
        
        return result
    
    def get_cached_result(self, plotter_name: str, 
                         analysis_type: str,
                         **kwargs) -> Optional[Any]:
        """
        Retrieve cached analysis results.
        
        Args:
            plotter_name: Name of the plotter
            analysis_type: Type of analysis
            **kwargs: Analysis parameters
            
        Returns:
            Cached result if available, None otherwise
        """
        cache_key = f"{plotter_name}_{analysis_type}_{str(kwargs)}"
        return self.results_cache.get(cache_key)
    
    def clear_cache(self) -> None:
        """Clear all cached results."""
        self.results_cache.clear()
        logger.info("Cache cleared")


# Utility functions for integration
def create_sample_data(n_points: int = 1000, 
                      n_series: int = 3,
                      freq: str = 'D',
                      seed: int = 42) -> pd.DataFrame:
    """
    Create sample time series data for testing.
    
    Args:
        n_points: Number of data points
        n_series: Number of time series
        freq: Frequency of time series
        seed: Random seed
        
    Returns:
        DataFrame with sample time series
    """
    np.random.seed(seed)
    
    # Create date index
    dates = pd.date_range(start='2020-01-01', periods=n_points, freq=freq)
    
    # Create correlated time series
    data = {}
    base = np.cumsum(np.random.randn(n_points))
    
    for i in range(n_series):
        noise = np.random.randn(n_points) * (i + 1)
        correlation = 0.8 - (i * 0.2)
        data[f'series_{i+1}'] = base * correlation + noise
        
        # Add some missing values
        if i > 0:
            missing_idx = np.random.choice(n_points, size=int(n_points * 0.05), replace=False)
            data[f'series_{i+1}'][missing_idx] = np.nan
    
    return pd.DataFrame(data, index=dates)


# Performance optimization decorator
def timed_execution(func):
    """Decorator to time function execution."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        if end - start > 5:
            logger.warning(f"{func.__name__} took {end-start:.2f} seconds (>5s limit)")
        return result
    return wrapper
```