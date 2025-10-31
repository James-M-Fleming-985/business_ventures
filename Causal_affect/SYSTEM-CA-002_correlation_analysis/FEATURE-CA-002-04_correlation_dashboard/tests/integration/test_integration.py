"""
Integration tests for Correlation Dashboard & Visualization feature
Tests the interaction between multiple layers to ensure proper integration
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import json
from typing import Dict, List, Any

# Assuming these are the main classes from each layer
from src.correlation_dashboard.heatmap_generator import HeatmapGenerator
from src.correlation_dashboard.time_series_plotter import TimeSeriesPlotter
from src.correlation_dashboard.network_graph import NetworkGraph
from src.correlation_dashboard.leaderboard import Leaderboard
from src.correlation_dashboard.feature_integration import CorrelationDashboard


@pytest.fixture
def sample_correlation_data():
    """Generate sample correlation data for testing"""
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
    
    # Create correlation matrix
    n_symbols = len(symbols)
    correlation_matrix = pd.DataFrame(
        np.random.rand(n_symbols, n_symbols) * 0.8 + 0.2,
        index=symbols,
        columns=symbols
    )
    # Make it symmetric with diagonal = 1
    correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2
    np.fill_diagonal(correlation_matrix.values, 1.0)
    
    # Create time series data
    time_series_data = {}
    for symbol in symbols:
        time_series_data[symbol] = pd.Series(
            np.cumsum(np.random.randn(len(dates))) + 100,
            index=dates
        )
    
    return {
        'correlation_matrix': correlation_matrix,
        'time_series': time_series_data,
        'symbols': symbols,
        'dates': dates
    }


@pytest.fixture
def mock_dashboard_components():
    """Create mocked dashboard components"""
    heatmap_gen = Mock(spec=HeatmapGenerator)
    time_series = Mock(spec=TimeSeriesPlotter)
    network_graph = Mock(spec=NetworkGraph)
    leaderboard = Mock(spec=Leaderboard)
    
    return {
        'heatmap': heatmap_gen,
        'time_series': time_series,
        'network': network_graph,
        'leaderboard': leaderboard
    }


@pytest.fixture
def correlation_dashboard(mock_dashboard_components):
    """Create a CorrelationDashboard instance with mocked components"""
    dashboard = CorrelationDashboard()
    dashboard.heatmap_generator = mock_dashboard_components['heatmap']
    dashboard.time_series_plotter = mock_dashboard_components['time_series']
    dashboard.network_graph = mock_dashboard_components['network']
    dashboard.leaderboard = mock_dashboard_components['leaderboard']
    return dashboard


class TestCorrelationDashboardIntegration:
    
    def test_full_dashboard_update_flow(self, correlation_dashboard, sample_correlation_data):
        """
        Test the complete dashboard update flow from data input to visualization generation
        
        Integration Scenario: Full dashboard refresh with all components
        """
        # Setup mock returns
        correlation_dashboard.heatmap_generator.generate.return_value = {
            'plot_data': 'heatmap_plot',
            'status': 'success'
        }
        correlation_dashboard.time_series_plotter.plot.return_value = {
            'plot_data': 'time_series_plot',
            'status': 'success'
        }
        correlation_dashboard.network_graph.create.return_value = {
            'graph_data': 'network_plot',
            'status': 'success'
        }
        correlation_dashboard.leaderboard.generate.return_value = {
            'rankings': [('AAPL', 0.85), ('GOOGL', 0.82)],
            'status': 'success'
        }
        
        # Execute dashboard update
        result = correlation_dashboard.update_dashboard(
            correlation_matrix=sample_correlation_data['correlation_matrix'],
            time_series_data=sample_correlation_data['time_series'],
            update_all=True
        )
        
        # Verify all components were called
        correlation_dashboard.heatmap_generator.generate.assert_called_once()
        correlation_dashboard.time_series_plotter.plot.assert_called_once()
        correlation_dashboard.network_graph.create.assert_called_once()
        correlation_dashboard.leaderboard.generate.assert_called_once()
        
        # Verify result structure
        assert result['status'] == 'success'
        assert 'heatmap' in result['visualizations']
        assert 'time_series' in result['visualizations']
        assert 'network' in result['visualizations']
        assert 'leaderboard' in result['visualizations']
    
    
    def test_selective_component_update(self, correlation_dashboard, sample_correlation_data):
        """
        Test updating only specific dashboard components
        
        Integration Scenario: User selects specific visualizations to update
        """
        # Setup to update only heatmap and leaderboard
        correlation_dashboard.heatmap_generator.generate.return_value = {
            'plot_data': 'updated_heatmap',
            'status': 'success'
        }
        correlation_dashboard.leaderboard.generate.return_value = {
            'rankings': [('MSFT', 0.88)],
            'status': 'success'
        }
        
        # Execute selective update
        result = correlation_dashboard.update_dashboard(
            correlation_matrix=sample_correlation_data['correlation_matrix'],
            components=['heatmap', 'leaderboard']
        )
        
        # Verify only selected components were called
        correlation_dashboard.heatmap_generator.generate.assert_called_once()
        correlation_dashboard.leaderboard.generate.assert_called_once()
        correlation_dashboard.time_series_plotter.plot.assert_not_called()
        correlation_dashboard.network_graph.create.assert_not_called()
        
        # Verify result contains only updated components
        assert 'heatmap' in result['visualizations']
        assert 'leaderboard' in result['visualizations']
        assert 'time_series' not in result['visualizations']
        assert 'network' not in result['visualizations']
    
    
    def test_error_propagation_and_handling(self, correlation_dashboard, sample_correlation_data):
        """
        Test error handling when one component fails
        
        Integration Scenario: Network graph generation fails, other components should continue
        """
        # Setup mixed success/failure scenarios
        correlation_dashboard.heatmap_generator.generate.return_value = {
            'plot_data': 'heatmap_success',
            'status': 'success'
        }
        correlation_dashboard.network_graph.create.side_effect = Exception("Network graph generation failed")
        correlation_dashboard.time_series_plotter.plot.return_value = {
            'plot_data': 'time_series_success',
            'status': 'success'
        }
        correlation_dashboard.leaderboard.generate.return_value = {
            'rankings': [],
            'status': 'success'
        }
        
        # Execute dashboard update
        result = correlation_dashboard.update_dashboard(
            correlation_matrix=sample_correlation_data['correlation_matrix'],
            time_series_data=sample_correlation_data['time_series'],
            update_all=True,
            fail_on_error=False
        )
        
        # Verify partial success handling
        assert result['status'] == 'partial_success'
        assert 'heatmap' in result['visualizations']
        assert 'time_series' in result['visualizations']
        assert 'leaderboard' in result['visualizations']
        assert 'errors' in result
        assert any('network' in str(error) for error in result['errors'])
    
    
    def test_data_filtering_integration(self, correlation_dashboard, sample_correlation_data):
        """
        Test data filtering across multiple components
        
        Integration Scenario: Apply threshold filter that affects all visualizations
        """
        # Create filtered correlation matrix (only strong correlations > 0.7)
        filtered_matrix = sample_correlation_data['correlation_matrix'].copy()
        filtered_matrix[filtered_matrix < 0.7] = 0
        
        # Setup mock returns with filtered data expectations
        correlation_dashboard.heatmap_generator.generate.return_value = {
            'plot_data': 'filtered_heatmap',
            'filtered_pairs': 8,
            'status': 'success'
        }
        correlation_dashboard.network_graph.create.return_value = {
            'graph_data': 'filtered_network',
            'edge_count': 8,
            'status': 'success'
        }
        correlation_dashboard.leaderboard.generate.return_value = {
            'rankings': [('AAPL', 0.92), ('GOOGL', 0.88)],
            'filtered_count': 3,
            'status': 'success'
        }
        
        # Apply filter and update
        result = correlation_dashboard.apply_correlation_filter(
            correlation_matrix=sample_correlation_data['correlation_matrix'],
            threshold=0.7,
            update_visualizations=True
        )
        
        # Verify filter was applied to all components
        assert result['filter_applied'] == True
        assert result['threshold'] == 0.7
        
        # Verify components received filtered data
        heatmap_call_args = correlation_dashboard.heatmap_generator.generate.call_args
        network_call_args = correlation_dashboard.network_graph.create.call_args
        
        # Check that filtered matrix was passed
        assert heatmap_call_args is not None
        assert network_call_args is not None
    
    
    def test_real_time_update_integration(self, correlation_dashboard, sample_correlation_data):
        """
        Test real-time update mechanism across components
        
        Integration Scenario: Streaming updates that refresh specific visualizations
        """
        # Simulate streaming correlation updates
        update_queue = []
        for i in range(5):
            new_correlation = sample_correlation_data['correlation_matrix'].copy()
            # Simulate correlation changes
            new_correlation.iloc[0, 1] = 0.5 + (i * 0.05)
            update_queue.append({
                'timestamp': datetime.now() + timedelta(seconds=i),
                'data': new_correlation
            })
        
        # Setup mock responses for streaming updates
        correlation_dashboard.heatmap_generator.update_cell.return_value = {'status': 'success'}
        correlation_dashboard.network_graph.update_edge.return_value = {'status': 'success'}
        correlation_dashboard.leaderboard.update_ranking.return_value = {'status': 'success'}
        
        # Process streaming updates
        results = []
        for update in update_queue:
            result = correlation_dashboard.process_streaming_update(
                correlation_update=update['data'],
                timestamp=update['timestamp'],
                update_mode='incremental'
            )
            results.append(result)
        
        # Verify incremental updates were processed
        assert len(results) == 5
        assert all(r['status'] == 'success' for r in results)
        
        # Verify update methods were called
        assert correlation_dashboard.heatmap_generator.update_cell.call_count >= 5
        assert correlation_dashboard.network_graph.update_edge.call_count >= 5
        assert correlation_dashboard.leaderboard.update_ranking.call_count >= 5
    
    
    def test_export_integration(self, correlation_dashboard, sample_correlation_data):
        """
        Test exporting dashboard state across all components
        
        Integration Scenario: Export complete dashboard for reporting
        """
        # Setup component export returns
        correlation_dashboard.heatmap_generator.export.return_value = {
            'type': 'heatmap',
            'data': sample_correlation_data['correlation_matrix'].to_dict(),
            'format': 'json'
        }
        correlation_dashboard.time_series_plotter.export.return_value = {
            'type': 'time_series',
            'data': {'series': 'mock_data'},
            'format': 'json'
        }
        correlation_dashboard.network_graph.export.return_value = {
            'type': 'network',
            'nodes': 5,
            'edges': 10,
            'format': 'graphml'
        }
        correlation_dashboard.leaderboard.export.return_value = {
            'type': 'leaderboard',
            'rankings': [('AAPL', 0.85)],
            'format': 'csv'
        }
        
        # Execute full dashboard export
        export_result = correlation_dashboard.export_dashboard(
            formats=['json', 'csv', 'png'],
            include_metadata=True
        )
        
        # Verify all components were exported
        assert 'heatmap' in export_result['exports']
        assert 'time_series' in export_result['exports']
        assert 'network' in export_result['exports']
        assert 'leaderboard' in export_result['exports']
        
        # Verify metadata inclusion
        assert 'metadata' in export_result
        assert 'export_timestamp' in export_result['metadata']
        assert 'component_count' in export_result['metadata']
        
        # Verify export methods were called with correct formats
        correlation_dashboard.heatmap_generator.export.assert_called_once()
        correlation_dashboard.time_series_plotter.export.assert_called_once()
        correlation_dashboard.network_graph.export.assert_called_once()
        correlation_dashboard.leaderboard.export.assert_called_once()


class TestCorrelationDashboardPerformance:
    """Performance-related integration tests"""
    
    @pytest.mark.performance
    def test_large_dataset_handling(self, correlation_dashboard):
        """
        Test dashboard performance with large correlation matrices
        
        Integration Scenario: Handle 100+ symbols correlation matrix
        """
        # Generate large dataset
        n_symbols = 100
        symbols = [f'SYM{i:03d}' for i in range(n_symbols)]
        large_matrix = pd.DataFrame(
            np.random.rand(n_symbols, n_symbols),
            index=symbols,
            columns=symbols
        )
        
        # Setup mock returns
        correlation_dashboard.heatmap_generator.generate.return_value = {
            'status': 'success',
            'processing_time': 0.5
        }
        correlation_dashboard.network_graph.create.return_value = {
            'status': 'success',
            'processing_time': 1.2
        }
        
        # Execute with performance monitoring
        import time
        start_time = time.time()
        
        result = correlation_dashboard.update_dashboard(
            correlation_matrix=large_matrix,
            performance_mode=True,
            chunk_size=50
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify performance optimizations were applied
        assert result['status'] == 'success'
        assert 'performance_metrics' in result
        assert processing_time < 5.0  # Should complete within 5 seconds


if __name__ == "__main__":
    pytest.main([__file__, "-v"])