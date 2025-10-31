```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, Dict, Any, List, Tuple, Union
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HeatmapGenerator:
    """
    Generates correlation heatmaps for data analysis.
    
    This class provides functionality to create correlation heatmaps with various
    customization options, handles missing data, and supports concurrent execution.
    """
    
    def __init__(self, figsize: Tuple[int, int] = (10, 8), cmap: str = 'coolwarm'):
        """
        Initialize the HeatmapGenerator.
        
        Args:
            figsize: Figure size as (width, height) tuple. Default is (10, 8).
            cmap: Colormap for the heatmap. Default is 'coolwarm'.
        """
        self.figsize = figsize
        self.cmap = cmap
        self._validate_init_params()
        
    def _validate_init_params(self) -> None:
        """Validate initialization parameters."""
        if not isinstance(self.figsize, tuple) or len(self.figsize) != 2:
            raise ValueError("figsize must be a tuple of two values")
        if not all(isinstance(x, (int, float)) and x > 0 for x in self.figsize):
            raise ValueError("figsize values must be positive numbers")
        if not isinstance(self.cmap, str):
            raise ValueError("cmap must be a string")
    
    def calculate_correlation(self, 
                            data: Union[pd.DataFrame, np.ndarray], 
                            method: str = 'pearson',
                            min_periods: Optional[int] = None) -> pd.DataFrame:
        """
        Calculate correlation matrix for the given data.
        
        Args:
            data: Input data as DataFrame or numpy array
            method: Correlation method ('pearson', 'spearman', or 'kendall')
            min_periods: Minimum number of observations required per pair
            
        Returns:
            Correlation matrix as DataFrame
            
        Raises:
            ValueError: If data is invalid or method is unsupported
        """
        start_time = time.time()
        
        # Validate input
        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            raise ValueError("Data cannot be None or empty")
            
        # Convert to DataFrame if numpy array
        if isinstance(data, np.ndarray):
            if data.ndim == 1:
                data = pd.DataFrame(data.reshape(-1, 1))
            else:
                data = pd.DataFrame(data)
                
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Data must be a pandas DataFrame or numpy array")
            
        # Validate method
        valid_methods = ['pearson', 'spearman', 'kendall']
        if method not in valid_methods:
            raise ValueError(f"Method must be one of {valid_methods}")
            
        # Handle missing data
        if data.isnull().any().any():
            logger.warning("Missing data detected. Correlation will be calculated pairwise.")
            
        # Calculate correlation
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', category=RuntimeWarning)
                corr_matrix = data.corr(method=method, min_periods=min_periods)
        except Exception as e:
            raise ValueError(f"Error calculating correlation: {str(e)}")
            
        elapsed_time = time.time() - start_time
        if elapsed_time > 5.0 and len(data) >= 10000:
            logger.warning(f"Correlation calculation took {elapsed_time:.2f} seconds for {len(data)} data points")
            
        return corr_matrix
    
    def generate_heatmap(self,
                        correlation_matrix: pd.DataFrame,
                        title: Optional[str] = None,
                        annot: bool = True,
                        fmt: str = '.2f',
                        mask_upper: bool = False,
                        vmin: float = -1,
                        vmax: float = 1,
                        save_path: Optional[str] = None) -> plt.Figure:
        """
        Generate a correlation heatmap.
        
        Args:
            correlation_matrix: Correlation matrix to visualize
            title: Title for the heatmap
            annot: Whether to annotate cells with values
            fmt: Format string for annotations
            mask_upper: Whether to mask upper triangle
            vmin: Minimum value for color scale
            vmax: Maximum value for color scale
            save_path: Path to save the figure
            
        Returns:
            Matplotlib figure object
            
        Raises:
            ValueError: If correlation_matrix is invalid
        """
        if not isinstance(correlation_matrix, pd.DataFrame):
            raise ValueError("correlation_matrix must be a pandas DataFrame")
            
        if correlation_matrix.empty:
            raise ValueError("correlation_matrix cannot be empty")
            
        # Create figure
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # Create mask if requested
        mask = None
        if mask_upper:
            mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
            
        # Generate heatmap
        try:
            sns.heatmap(correlation_matrix,
                       mask=mask,
                       cmap=self.cmap,
                       annot=annot,
                       fmt=fmt,
                       vmin=vmin,
                       vmax=vmax,
                       center=0,
                       square=True,
                       linewidths=0.5,
                       cbar_kws={"shrink": 0.8},
                       ax=ax)
            
            if title:
                ax.set_title(title, fontsize=16, pad=20)
                
            # Adjust layout
            plt.tight_layout()
            
            # Save if path provided
            if save_path:
                fig.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Heatmap saved to {save_path}")
                
        except Exception as e:
            plt.close(fig)
            raise ValueError(f"Error generating heatmap: {str(e)}")
            
        return fig
    
    def process_multiple_datasets(self,
                                datasets: Dict[str, pd.DataFrame],
                                method: str = 'pearson',
                                **kwargs) -> Dict[str, plt.Figure]:
        """
        Process multiple datasets concurrently.
        
        Args:
            datasets: Dictionary of dataset names to DataFrames
            method: Correlation method to use
            **kwargs: Additional arguments for generate_heatmap
            
        Returns:
            Dictionary of dataset names to figure objects
        """
        results = {}
        
        with ThreadPoolExecutor() as executor:
            # Submit tasks
            future_to_name = {}
            for name, data in datasets.items():
                future = executor.submit(self._process_single_dataset, 
                                       data, name, method, **kwargs)
                future_to_name[future] = name
                
            # Collect results
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    results[name] = future.result()
                except Exception as e:
                    logger.error(f"Error processing dataset '{name}': {str(e)}")
                    results[name] = None
                    
        return results
    
    def _process_single_dataset(self,
                               data: pd.DataFrame,
                               name: str,
                               method: str = 'pearson',
                               **kwargs) -> plt.Figure:
        """Process a single dataset."""
        corr_matrix = self.calculate_correlation(data, method=method)
        title = kwargs.pop('title', f'Correlation Heatmap - {name}')
        return self.generate_heatmap(corr_matrix, title=title, **kwargs)
    
    def get_high_correlations(self,
                            correlation_matrix: pd.DataFrame,
                            threshold: float = 0.7,
                            exclude_diagonal: bool = True) -> List[Tuple[str, str, float]]:
        """
        Get pairs of variables with high correlation.
        
        Args:
            correlation_matrix: Correlation matrix
            threshold: Absolute correlation threshold
            exclude_diagonal: Whether to exclude diagonal elements
            
        Returns:
            List of tuples (var1, var2, correlation)
        """
        if not isinstance(correlation_matrix, pd.DataFrame):
            raise ValueError("correlation_matrix must be a pandas DataFrame")
            
        high_corr = []
        
        # Get upper triangle indices to avoid duplicates
        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                corr_value = correlation_matrix.iloc[i, j]
                if not pd.isna(corr_value) and abs(corr_value) >= threshold:
                    var1 = correlation_matrix.columns[i]
                    var2 = correlation_matrix.columns[j]
                    high_corr.append((var1, var2, corr_value))
                    
        # Sort by absolute correlation value
        high_corr.sort(key=lambda x: abs(x[2]), reverse=True)
        
        return high_corr
    
    def integrate_with_orchestrator(self, orchestrator: Any) -> None:
        """
        Integrate with feature orchestrator.
        
        Args:
            orchestrator: Feature orchestrator instance
        """
        if hasattr(orchestrator, 'register_component'):
            orchestrator.register_component('heatmap_generator', self)
            logger.info("HeatmapGenerator registered with orchestrator")
        else:
            logger.warning("Orchestrator does not support component registration")
    
    def __repr__(self) -> str:
        """String representation of HeatmapGenerator."""
        return f"HeatmapGenerator(figsize={self.figsize}, cmap='{self.cmap}')"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Heatmap Generator with {self.figsize} figure size and '{self.cmap}' colormap"
```