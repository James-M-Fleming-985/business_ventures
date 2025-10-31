"""
Feature Integration for Correlation Dashboard & Visualization
Feature ID: FEATURE-CA-002-04

This module orchestrates the integration of multiple layers to provide
comprehensive correlation analysis and visualization capabilities.
"""

from pathlib import Path
import sys
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
import pandas as pd
import numpy as np
import json
from datetime import datetime
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import layer implementations
from LAYER_CA_002_04_01_Heatmap_Generator.src.implementation import HeatmapGenerator
from LAYER_CA_002_04_02_Time_Series_Plotter.src.implementation import TimeSeriesPlotter, FeatureOrchestrator as TimeSeriesOrchestrator
from LAYER_CA_002_04_03_Network_Graph.src.implementation import NetworkGraph
from LAYER_CA_002_04_04_Leaderboard.src.implementation import LeaderboardCalculator, FeatureOrchestrator as LeaderboardOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FeatureConfig:
    """Configuration for the Correlation Dashboard feature."""
    
    correlation_threshold: float = 0.5
    top_n_correlations: int = 10
    heatmap_output_format: str = 'png'
    time_series_window: int = 30
    network_min_edge_weight: float = 0.3
    enable_caching: bool = True
    output_directory: str = './output'
    

@dataclass
class FeatureResponse:
    """Unified response structure for feature operations."""
    
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class CorrelationDashboardOrchestrator:
    """
    Main orchestrator for the Correlation Dashboard & Visualization feature.
    
    Coordinates the interaction between:
    - Heatmap Generator
    - Time Series Plotter
    - Network Graph
    - Leaderboard Calculator
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        """
        Initialize the feature orchestrator.
        
        Args:
            config: Feature configuration object
        """
        self.config = config or FeatureConfig()
        self._initialize_layers()
        
    def _initialize_layers(self) -> None:
        """Initialize all layer instances with error handling."""
        try:
            # Initialize Heatmap Generator
            self.heatmap_generator = HeatmapGenerator()
            logger.info("Heatmap Generator initialized successfully")
            
            # Initialize Time Series Plotter
            self.time_series_plotter = TimeSeriesPlotter()
            self.time_series_orchestrator = TimeSeriesOrchestrator()
            self.time_series_orchestrator.register_plotter('main', self.time_series_plotter)
            logger.info("Time Series Plotter initialized successfully")
            
            # Initialize Network Graph
            self.network_graph = NetworkGraph()
            logger.info("Network Graph initialized successfully")
            
            # Initialize Leaderboard Calculator
            self.leaderboard_calculator = LeaderboardCalculator()
            self.leaderboard_orchestrator = LeaderboardOrchestrator()
            logger.info("Leaderboard Calculator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize layers: {str(e)}")
            raise RuntimeError(f"Layer initialization failed: {str(e)}")
    
    def analyze_correlations(self, data: pd.DataFrame, 
                           dataset_name: str = "default") -> FeatureResponse:
        """
        Perform comprehensive correlation analysis on the provided data.
        
        Args:
            data: Input DataFrame for analysis
            dataset_name: Name identifier for the dataset
            
        Returns:
            FeatureResponse containing analysis results
        """
        try:
            results = {}
            
            # Generate correlation matrix using Heatmap Generator
            correlation_matrix = self.heatmap_generator.calculate_correlation(data)
            results['correlation_matrix'] = correlation_matrix.to_dict()
            
            # Generate heatmap visualization
            heatmap_path = self.heatmap_generator.generate_heatmap(
                correlation_matrix, 
                f"{dataset_name}_correlation_heatmap"
            )
            results['heatmap_path'] = str(heatmap_path)
            
            # Get high correlations
            high_correlations = self.heatmap_generator.get_high_correlations(
                correlation_matrix, 
                threshold=self.config.correlation_threshold
            )
            results['high_correlations'] = high_correlations
            
            # Generate leaderboard
            leaderboard_data = self.leaderboard_calculator.calculate_correlations(data)
            leaderboard = self.leaderboard_calculator.generate_leaderboard(
                leaderboard_data, 
                top_n=self.config.top_n_correlations
            )
            results['leaderboard'] = leaderboard
            
            # Build network graph from correlation matrix
            self.network_graph.build_from_correlation_matrix(
                correlation_matrix, 
                threshold=self.config.network_min_edge_weight
            )
            
            # Get network statistics
            centrality_measures = self.network_graph.get_centrality_measures()
            results['network_centrality'] = centrality_measures
            
            # Get network clusters
            clusters = self.network_graph.get_clusters()
            results['correlation_clusters'] = clusters
            
            # Filter network by correlation threshold
            filtered_network = self.network_graph.filter_by_correlation(
                self.config.correlation_threshold
            )
            results['filtered_network'] = filtered_network.to_dict()
            
            return FeatureResponse(
                success=True,
                data=results,
                metadata={
                    'dataset_name': dataset_name,
                    'data_shape': data.shape,
                    'correlation_threshold': self.config.correlation_threshold
                }
            )
            
        except Exception as e:
            logger.error(f"Correlation analysis failed: {str(e)}")
            return FeatureResponse(
                success=False,
                error=f"Analysis failed: {str(e)}"
            )
    
    def analyze_time_series_correlations(self, data: pd.DataFrame, 
                                       time_column: str,
                                       variables: List[str]) -> FeatureResponse:
        """
        Analyze correlations over time for specified variables.
        
        Args:
            data: DataFrame with time series data
            time_column: Name of the timestamp column
            variables: List of variable names to analyze
            
        Returns:
            FeatureResponse containing time series analysis results
        """
        try:
            # Set data in time series plotter
            self.time_series_plotter.set_data(data, time_column)
            
            results = {}
            
            # Plot time series for each variable
            time_series_plots = {}
            for var in variables:
                plot_path = self.time_series_plotter.plot_time_series(
                    [var], 
                    f"time_series_{var}"
                )
                time_series_plots[var] = str(plot_path)
            results['time_series_plots'] = time_series_plots
            
            # Calculate correlations
            correlations = self.time_series_plotter.calculate_correlations(variables)
            results['correlations'] = correlations
            
            # Plot correlation matrix
            corr_matrix_plot = self.time_series_plotter.plot_correlation_matrix(
                variables, 
                "correlation_matrix"
            )
            results['correlation_matrix_plot'] = str(corr_matrix_plot)
            
            # Plot rolling correlations for variable pairs
            if len(variables) >= 2:
                rolling_corr_plots = {}
                for i in range(len(variables) - 1):
                    var1, var2 = variables[i], variables[i + 1]
                    plot_path = self.time_series_plotter.plot_rolling_correlation(
                        var1, var2, 
                        window=self.config.time_series_window,
                        output_filename=f"rolling_corr_{var1}_{var2}"
                    )
                    rolling_corr_plots[f"{var1}_{var2}"] = str(plot_path)
                results['rolling_correlation_plots'] = rolling_corr_plots
            
            # Detect correlation changes
            correlation_changes = self.time_series_plotter.detect_correlation_changes(
                variables, 
                window=self.config.time_series_window
            )
            results['correlation_changes'] = correlation_changes
            
            # Get summary statistics
            summary_stats = self.time_series_plotter.get_summary_statistics()
            results['summary_statistics'] = summary_stats
            
            return FeatureResponse(
                success=True,
                data=results,
                metadata={
                    'time_column': time_column,
                    'variables_analyzed': variables,
                    'time_window': self.config.time_series_window
                }
            )
            
        except Exception as e:
            logger.error(f"Time series correlation analysis failed: {str(e)}")
            return FeatureResponse(
                success=False,
                error=f"Time series analysis failed: {str(e)}"
            )
    
    def create_correlation_dashboard(self, datasets: Dict[str, pd.DataFrame]) -> FeatureResponse:
        """
        Create a comprehensive correlation dashboard for multiple datasets.
        
        Args:
            datasets: Dictionary mapping dataset names to DataFrames
            
        Returns:
            FeatureResponse containing dashboard components
        """
        try:
            dashboard_results = {}
            
            # Process multiple datasets with heatmap generator
            multi_dataset_results = self.heatmap_generator.process_multiple_datasets(
                datasets
            )
            dashboard_results['multi_dataset_analysis'] = multi_dataset_results
            
            # Create network visualizations for each dataset
            network_visualizations = {}
            for name, data in datasets.items():
                # Calculate correlation matrix
                corr_matrix = self.heatmap_generator.calculate_correlation(data)
                
                # Build network
                network = NetworkGraph()
                network.build_from_correlation_matrix(
                    corr_matrix, 
                    threshold=self.config.network_min_edge_weight
                )
                
                # Get network JSON representation
                network_json = network.to_json()
                network_visualizations[name] = json.loads(network_json)
                
            dashboard_results['network_visualizations'] = network_visualizations
            
            # Generate consolidated leaderboard
            all_leaderboards = {}
            for name, data in datasets.items():
                corr_data = self.leaderboard_calculator.calculate_correlations(data)
                leaderboard = self.leaderboard_calculator.generate_leaderboard(
                    corr_data, 
                    top_n=self.config.top_n_correlations
                )
                all_leaderboards[name] = leaderboard
                
            dashboard_results['leaderboards'] = all_leaderboards
            
            # Format consolidated leaderboard
            if len(datasets) == 1:
                formatted_leaderboard = self.leaderboard_calculator.format_leaderboard(
                    list(all_leaderboards.values())[0]
                )
                dashboard_results['formatted_leaderboard'] = formatted_leaderboard
            
            return FeatureResponse(
                success=True,
                data=dashboard_results,
                metadata={
                    'dataset_count': len(datasets),
                    'dataset_names': list(datasets.keys())
                }
            )
            
        except Exception as e:
            logger.error(f"Dashboard creation failed: {str(e)}")
            return FeatureResponse(
                success=False,
                error=f"Dashboard creation failed: {str(e)}"
            )
    
    def get_correlation_insights(self, data: pd.DataFrame) -> FeatureResponse:
        """
        Extract key insights from correlation analysis.
        
        Args:
            data: Input DataFrame for analysis
            
        Returns:
            FeatureResponse containing correlation insights
        """
        try:
            insights = {}
            
            # Calculate correlation matrix
            corr_matrix = self.heatmap_generator.calculate_correlation(data)
            
            # Get high correlations
            high_correlations = self.heatmap_generator.get_high_correlations(
                corr_matrix, 
                threshold=self.config.correlation_threshold
            )
            insights['high_correlations'] = high_correlations
            
            # Build network for advanced analysis
            self.network_graph.build_from_correlation_matrix(
                corr_matrix, 
                threshold=self.config.network_min_edge_weight
            )
            
            # Get centrality measures to identify key variables
            centrality = self.network_graph.get_centrality_measures()
            
            # Identify most connected variables
            if centrality:
                sorted_centrality = sorted(
                    centrality.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )
                insights['most_connected_variables'] = sorted_centrality[:5]
            
            # Get correlation clusters
            clusters = self.network_graph.get_clusters()
            insights['variable_clusters'] = clusters
            
            # Calculate basic statistics
            insights['statistics'] = {
                'mean_correlation': float(np.mean(np.abs(corr_matrix.values))),
                'max_correlation': float(np.max(np.abs(corr_matrix.values))),
                'correlation_distribution': {
                    'strong_positive': int(np.sum(corr_matrix.values > 0.7)),
                    'moderate_positive': int(np.sum((corr_matrix.values > 0.3) & (corr_matrix.values <= 0.7))),
                    'weak': int(np.sum((corr_matrix.values >= -0.3) & (corr_matrix.values <= 0.3))),
                    'moderate_negative': int(np.sum((corr_matrix.values < -0.3) & (corr_matrix.values >= -0.7))),
                    'strong_negative': int(np.sum(corr_matrix.values < -0.7))
                }
            }
            
            return FeatureResponse(
                success=True,
                data=insights,
                metadata={
                    'variables_analyzed': list(data.columns),
                    'total_correlations': len(high_correlations)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to extract correlation insights: {str(e)}")
            return FeatureResponse(
                success=False,
                error=f"Insight extraction failed: {str(e)}"
            )
    
    def clear_caches(self) -> FeatureResponse:
        """
        Clear all caches from the orchestrators.
        
        Returns:
            FeatureResponse indicating cache clearing status
        """
        try:
            # Clear time series orchestrator cache
            self.time_series_orchestrator.clear_cache()
            
            # Clear leaderboard orchestrator cache  
            self.leaderboard_orchestrator.clear_cache()
            
            logger.info("All caches cleared successfully")
            
            return FeatureResponse(
                success=True,
                data={'message': 'All caches cleared successfully'}
            )
            
        except Exception as e:
            logger.error(f"Failed to clear caches: {str(e)}")
            return FeatureResponse(
                success=False,
                error=f"Cache clearing failed: {str(e)}"
            )


def create_orchestrator(config: Optional[FeatureConfig] = None) -> CorrelationDashboardOrchestrator:
    """
    Factory function to create a configured orchestrator instance.
    
    Args:
        config: Optional feature configuration
        
    Returns:
        Configured CorrelationDashboardOrchestrator instance
    """
    return CorrelationDashboardOrchestrator(config)
