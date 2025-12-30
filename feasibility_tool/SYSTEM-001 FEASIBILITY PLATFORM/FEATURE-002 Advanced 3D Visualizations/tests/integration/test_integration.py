"""
Integration tests for Advanced 3D Visualizations feature
Tests the interaction between all visualization layers and components
"""

import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta
import time

# Import the feature integration module
from src.features.feature_001_002.feature_integration import (
    VisualizationIntegration,
    VisualizationMode,
    MaterialType,
    VisualizationConfig,
    PerformanceMetrics
)

# Import individual layer components for mocking
from src.features.feature_001_002.layers import (
    VisualizationFramework,
    TernaryDiagramComponent,
    FeasibilityVolumeComponent,
    ParallelCoordinatesComponent,
    ResponseSurfaceComponent,
    SensitivityAnalysisComponent,
    CorrelationMatrixComponent,
    ParetoFrontierComponent,
    RadarChartComponent,
    IntegrationLayer
)


class TestVisualizationIntegration:
    """Test suite for Advanced 3D Visualizations integration"""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for all visualization layers"""
        return {
            'framework': Mock(spec=VisualizationFramework),
            'ternary': Mock(spec=TernaryDiagramComponent),
            'feasibility': Mock(spec=FeasibilityVolumeComponent),
            'parallel': Mock(spec=ParallelCoordinatesComponent),
            'response': Mock(spec=ResponseSurfaceComponent),
            'sensitivity': Mock(spec=SensitivityAnalysisComponent),
            'correlation': Mock(spec=CorrelationMatrixComponent),
            'pareto': Mock(spec=ParetoFrontierComponent),
            'radar': Mock(spec=RadarChartComponent),
            'integration': Mock(spec=IntegrationLayer)
        }
    
    @pytest.fixture
    def visualization_integration(self, mock_components):
        """Create visualization integration instance with mocked components"""
        with patch.multiple(
            'src.features.feature_001_002.feature_integration',
            VisualizationFramework=lambda: mock_components['framework'],
            TernaryDiagramComponent=lambda: mock_components['ternary'],
            FeasibilityVolumeComponent=lambda: mock_components['feasibility'],
            ParallelCoordinatesComponent=lambda: mock_components['parallel'],
            ResponseSurfaceComponent=lambda: mock_components['response'],
            SensitivityAnalysisComponent=lambda: mock_components['sensitivity'],
            CorrelationMatrixComponent=lambda: mock_components['correlation'],
            ParetoFrontierComponent=lambda: mock_components['pareto'],
            RadarChartComponent=lambda: mock_components['radar'],
            IntegrationLayer=lambda: mock_components['integration']
        ):
            integration = VisualizationIntegration()
            integration._components = mock_components
            return integration
    
    @pytest.fixture
    def sample_configuration(self):
        """Sample configuration for testing"""
        return {
            'material_type': MaterialType.POLYMER,
            'Di': 0.5,
            'De': 0.8,
            'temperature': 25.0,
            'pressure': 1.0,
            'flow_rate': 100.0,
            'solvent_concentration': 0.2
        }
    
    @pytest.mark.asyncio
    async def test_material_dropdown_updates_all_visualizations(
        self, visualization_integration, mock_components, sample_configuration
    ):
        """
        Test: User drags material_type dropdown → all visualizations update instantly
        showing new material properties
        """
        # Setup
        initial_material = MaterialType.POLYMER
        new_material = MaterialType.CERAMIC
        
        # Configure mocks
        mock_components['integration'].get_material_properties.side_effect = [
            {'density': 1.2, 'viscosity': 0.001},  # Polymer properties
            {'density': 2.5, 'viscosity': 0.005}   # Ceramic properties
        ]
        
        # Simulate material dropdown change
        await visualization_integration.update_material_type(new_material)
        
        # Verify all components received update
        for component_name, component in mock_components.items():
            if component_name not in ['framework', 'integration']:
                component.update_material_properties.assert_called_once_with({
                    'material_type': new_material,
                    'density': 2.5,
                    'viscosity': 0.005
                })
        
        # Verify integration layer coordinated updates
        mock_components['integration'].coordinate_material_update.assert_called_once_with(
            new_material,
            {'density': 2.5, 'viscosity': 0.005}
        )
        
        # Verify framework refreshed display
        mock_components['framework'].refresh_all_components.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_di_slider_realtime_morphing(
        self, visualization_integration, mock_components, sample_configuration
    ):
        """
        Test: User adjusts Di slider continuously → triangle, feasibility volume,
        parallel coords all morph in real-time at 60 FPS
        """
        # Setup slider simulation
        di_values = np.linspace(0.3, 0.7, 10)  # Simulate smooth drag
        frame_times = []
        
        # Configure mocks for performance tracking
        mock_components['framework'].get_fps.return_value = 60
        mock_components['framework'].is_rendering.return_value = True
        
        # Simulate continuous slider adjustment
        start_time = time.time()
        for di_value in di_values:
            frame_start = time.time()
            
            # Update Di parameter
            await visualization_integration.update_parameter('Di', di_value)
            
            # Track frame time
            frame_times.append(time.time() - frame_start)
            
            # Simulate 60 FPS timing (16.67ms per frame)
            await asyncio.sleep(0.0167)
        
        total_time = time.time() - start_time
        
        # Verify smooth morphing occurred
        assert len(frame_times) == 10
        assert all(ft < 0.0167 for ft in frame_times), "All frames should render under 16.67ms"
        
        # Verify specific components updated with interpolation
        ternary_calls = mock_components['ternary'].morph_to_configuration.call_args_list
        assert len(ternary_calls) == 10
        
        feasibility_calls = mock_components['feasibility'].update_volume.call_args_list
        assert len(feasibility_calls) == 10
        
        parallel_calls = mock_components['parallel'].animate_dimension.call_args_list
        assert len(parallel_calls) == 10
        
        # Verify smooth transitions (no sudden jumps)
        for i in range(1, len(di_values)):
            prev_di = di_values[i-1]
            curr_di = di_values[i]
            assert abs(curr_di - prev_di) < 0.05, "Smooth transition between values"
    
    @pytest.mark.asyncio
    async def test_visualization_mode_switching_performance(
        self, visualization_integration, mock_components
    ):
        """
        Test: User switches from Ternary to Response Surface mode → mode selector updates,
        previous mode disposed, new mode renders < 200ms
        """
        # Setup timing
        switch_start = None
        switch_end = None
        
        # Configure mode switching behavior
        async def simulate_mode_switch():
            nonlocal switch_start, switch_end
            switch_start = time.time()
            
            # Dispose previous mode
            mock_components['ternary'].dispose.return_value = True
            
            # Initialize new mode
            mock_components['response'].initialize.return_value = True
            mock_components['response'].render.return_value = True
            
            switch_end = time.time()
        
        mock_components['framework'].switch_mode.side_effect = simulate_mode_switch
        
        # Execute mode switch
        initial_mode = VisualizationMode.TERNARY
        new_mode = VisualizationMode.RESPONSE_SURFACE
        
        await visualization_integration.switch_visualization_mode(new_mode)
        
        # Verify performance constraint
        switch_time = (switch_end - switch_start) * 1000  # Convert to ms
        assert switch_time < 200, f"Mode switch took {switch_time}ms, should be < 200ms"
        
        # Verify proper disposal and initialization sequence
        call_order = []
        for call in mock_components['framework'].mock_calls:
            call_order.append(call[0])
        
        assert 'switch_mode' in call_order
        mock_components['ternary'].dispose.assert_called_once()
        mock_components['response'].initialize.assert_called_once()
        mock_components['response'].render.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_configuration_history_management(
        self, visualization_integration, mock_components, sample_configuration
    ):
        """
        Test: User accumulates 100+ configurations → history queue maintains only last 100,
        trails show recent exploration path
        """
        # Setup history tracking
        mock_components['integration'].get_history_size.return_value = 0
        mock_components['integration'].get_trail_points.return_value = []
        
        # Generate 120 configurations
        configurations = []
        for i in range(120):
            config = sample_configuration.copy()
            config['Di'] = 0.3 + (i * 0.005)  # Vary Di parameter
            config['timestamp'] = datetime.now() + timedelta(seconds=i)
            configurations.append(config)
        
        # Add all configurations
        for config in configurations:
            await visualization_integration.add_configuration(config)
        
        # Verify history management
        history_calls = mock_components['integration'].manage_history_queue.call_args_list
        assert len(history_calls) >= 20  # Should trigger cleanup after 100
        
        # Verify only last 100 configurations kept
        final_history = mock_components['integration'].get_history.return_value
        mock_components['integration'].get_history.return_value = configurations[-100:]
        
        history = await visualization_integration.get_configuration_history()
        assert len(history) == 100
        assert history[0]['Di'] == configurations[20]['Di']  # First 20 should be dropped
        assert history[-1]['Di'] == configurations[-1]['Di']  # Most recent preserved
        
        # Verify trail visualization updated
        mock_components['ternary'].update_exploration_trail.assert_called()
        trail_data = mock_components['ternary'].update_exploration_trail.call_args[0][0]
        
        # Trail should show path through configuration space
        mock_components['parallel'].highlight_history_path.assert_called()
    
    @pytest.mark.asyncio
    async def test_sensitivity_parameter_highlighting_integration(
        self, visualization_integration, mock_components, sample_configuration
    ):
        """
        Test: User clicks sensitivity bar → corresponding parameter highlighted
        in main input panel
        """
        # Setup sensitivity data
        sensitivity_data = {
            'Di': 0.85,
            'De': 0.65,
            'temperature': 0.45,
            'pressure': 0.25,
            'flow_rate': 0.15,
            'solvent_concentration': 0.35
        }
        mock_components['sensitivity'].get_sensitivity_scores.return_value = sensitivity_data
        
        # Simulate clicking on Di sensitivity bar
        clicked_parameter = 'Di'
        click_position = {'x': 100, 'y': 50, 'bar_index': 0}
        
        # Configure highlighting behavior
        mock_components['integration'].highlight_parameter.return_value = True
        mock_components['framework'].get_input_panel.return_value = MagicMock()
        
        # Execute click event
        await visualization_integration.handle_sensitivity_click(
            clicked_parameter,
            click_position
        )
        
        # Verify parameter highlighting sequence
        mock_components['integration'].highlight_parameter.assert_called_once_with(
            clicked_parameter,
            sensitivity_data[clicked_parameter]
        )
        
        # Verify visual feedback in components
        mock_components['sensitivity'].highlight_bar.assert_called_once_with(
            clicked_parameter
        )
        
        # Verify input panel received highlight command
        input_panel = mock_components['framework'].get_input_panel.return_value
        input_panel.highlight_field.assert_called_once_with(clicked_parameter)
        
        # Verify other visualizations show parameter importance
        mock_components['parallel'].emphasize_dimension.assert_called_once_with(
            clicked_parameter,
            sensitivity_data[clicked_parameter]
        )
        
        mock_components['radar'].highlight_axis.assert_called_once_with(
            clicked_parameter
        )
    
    @pytest.mark.asyncio
    async def test_correlation_matrix_hover_interaction(
        self, visualization_integration, mock_components
    ):
        """
        Test: User hovers correlation matrix cube → tooltip shows exact
        Pearson coefficient value
        """
        # Setup correlation data
        correlation_matrix = {
            ('Di', 'De'): 0.823,
            ('Di', 'temperature'): -0.456,
            ('De', 'pressure'): 0.234,
            ('temperature', 'flow_rate'): 0.678
        }
        mock_components['correlation'].get_correlation_matrix.return_value = correlation_matrix
        
        # Simulate hover event
        hover_position = {'x': 250, 'y': 180, 'z': 50}
        hovered_pair = ('Di', 'De')
        
        # Configure hover detection
        mock_components['correlation'].get_cube_at_position.return_value = {
            'parameters': hovered_pair,
            'value': correlation_matrix[hovered_pair]
        }
        
        # Execute hover
        tooltip_data = await visualization_integration.handle_correlation_hover(
            hover_position
        )
        
        # Verify tooltip content
        assert tooltip_data['title'] == 'Correlation: Di ↔ De'
        assert tooltip_data['value'] == '0.823'
        assert tooltip_data['interpretation'] == 'Strong positive correlation'
        assert tooltip_data['position'] == hover_position
        
        # Verify visual feedback
        mock_components['correlation'].highlight_cube.assert_called_once_with(
            hovered_pair
        )
        
        # Verify related visualizations updated
        mock_components['parallel'].highlight_correlation.assert_called_once_with(
            hovered_pair[0],
            hovered_pair[1],
            correlation_matrix[hovered_pair]
        )
    
    @pytest.mark.asyncio
    async def test_reference_planes_feasibility_volume(
        self, visualization_integration, mock_components
    ):
        """
        Test: User enables reference planes in feasibility volume → transparent grids
        appear at specified score thresholds
        """
        # Setup reference plane configuration
        reference_config = {
            'enabled': True,
            'thresholds': [0.7, 0.8, 0.9],  # Score thresholds
            'colors': ['yellow', 'orange', 'green'],
            'opacity': 0.3
        }
        
        # Configure feasibility volume mock
        mock_components['feasibility'].add_reference_plane.return_value = True
        mock_components['feasibility'].get_volume_bounds.return_value = {
            'min': [0, 0, 0],
            'max': [1, 1, 1]
        }
        
        # Enable reference planes
        await visualization_integration.configure_reference_planes(reference_config)
        
        # Verify planes added for each threshold
        add_plane_calls = mock_components['feasibility'].add_reference_plane.call_args_list
        assert len(add_plane_calls) == 3
        
        for i, (threshold, color) in enumerate(zip(
            reference_config['thresholds'],
            reference_config['colors']
        )):
            call_args = add_plane_calls[i][0][0]
            assert call_args['threshold'] == threshold
            assert call_args['color'] == color
            assert call_args['opacity'] == reference_config['opacity']
            assert 'grid_spacing' in call_args
        
        # Verify integration with other components
        mock_components['integration'].sync_reference_planes.assert_called_once_with(
            reference_config
        )
        
        # Verify visual indicators in UI
        mock_components['framework'].update_reference_plane_indicators.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_across_layers(
        self, visualization_integration, mock_components
    ):
        """
        Test error handling and recovery across layer boundaries
        """
        # Simulate various error conditions
        
        # Test 1: Component initialization failure
        mock_components['response'].initialize.side_effect = Exception("GPU memory error")
        
        with pytest.raises(Exception) as exc_info:
            await visualization_integration.switch_visualization_mode(
                VisualizationMode.RESPONSE_SURFACE
            )
        
        assert "GPU memory error" in str(exc_info.value)
        
        # Verify fallback behavior
        mock_components['framework'].show_error_notification.assert_called()
        mock_components['framework'].fallback_to_mode.assert_called_with(
            VisualizationMode.TERNARY
        )
        
        # Test 2: Data update failure in one component shouldn't crash others
        mock_components['parallel'].update_data.side_effect = ValueError("Invalid dimension")
        
        # This should not raise but log error
        await visualization_integration.update_all_visualizations(sample_configuration)
        
        # Verify other components still updated
        mock_components['ternary'].update_data.assert_called()
        mock_components['feasibility'].update_data.assert_called()
        
        # Test 3: Performance degradation handling
        mock_components['framework'].get_fps.return_value = 15  # Below 30 FPS threshold
        
        await visualization_integration.check_performance()
        
        # Verify quality reduction triggered
        mock_components['framework'].reduce_quality_settings.assert_called()
        mock_components['integration'].optimize_rendering_pipeline.assert_called()
    
    @pytest.mark.asyncio
    async def test_concurrent_update_synchronization(
        self, visualization_integration, mock_components
    ):
        """
        Test that concurrent updates from multiple sources are properly synchronized
        """
        # Setup concurrent update scenario
        updates = []
        
        async def track_update(component_name, data):
            updates.append((component_name, time.time(), data))
            await asyncio.sleep(0.01)  # Simulate processing time
        
        # Configure mocks to track calls
        for name, component in mock_components.items():
            if hasattr(component, 'update_data'):
                component.update_data.side_effect = lambda d, n=name: track_update(n, d)
        
        # Trigger multiple concurrent updates
        tasks = [
            visualization_integration.update_parameter('Di', 0.6),
            visualization_integration.update_parameter('De', 0.8),
            visualization_integration.update_material_type(MaterialType.METAL),
            visualization_integration.handle_sensitivity_click('temperature', {})
        ]
        
        await asyncio.gather(*tasks)
        
        # Verify no race conditions
        assert len(updates) > 0
        
        # Check update ordering is consistent
        mock_components['integration'].acquire_update_lock.assert_called()
        mock_components['integration'].release_update_lock.assert_called()
        
        # Verify final state is consistent
        final_state = await visualization_integration.get_current_state()
        assert final_state is not None


class TestPerformanceMetrics:
    """Test performance monitoring and metrics collection"""
    
    @pytest.mark.asyncio
    async def test_fps_monitoring(self, visualization_integration, mock_components):
        """Test FPS monitoring across all components"""
        # Configure FPS values
        fps_sequence = [60, 58, 45, 30, 55, 60]
        mock_components['framework'].get_fps.side_effect = fps_sequence
        
        # Collect metrics over time
        metrics = []
        for _ in range(len(fps_sequence)):
            metric = await visualization_integration.collect_performance_metrics()
            metrics.append(metric)
            await asyncio.sleep(0.1)
        
        # Verify metrics collected
        assert len(metrics) == len(fps_sequence)
        assert metrics[2]['fps'] == 45  # Degraded performance
        assert metrics[2]['quality_reduced'] == True
        
        # Verify recovery
        assert metrics[-1]['fps'] == 60
        assert metrics[-1]['quality_restored'] == True
    
    @pytest.mark.asyncio
    async def test_memory_usage_tracking(self, visualization_integration, mock_components):
        """Test memory usage tracking across visualization layers"""
        # Configure memory usage
        mock_components['framework'].get_memory_usage.return_value = {
            'total': 1024 * 1024 * 500,  # 500 MB
            'components': {
                'ternary': 50 * 1024 * 1024,
                'feasibility': 150 * 1024 * 1024,
                'response': 200 * 1024 * 1024
            }
        }
        
        # Check memory
        memory_report = await visualization_integration.get_memory_report()
        
        assert memory_report['total_mb'] == 500
        assert memory_report['feasibility_mb'] == 150
        assert memory_report['response_mb'] == 200
        
        # Verify cleanup triggered if threshold exceeded
        mock_components['framework'].get_memory_usage.return_value = {
            'total': 1024 * 1024 * 1500  # 1.5 GB
        }
        
        await visualization_integration.check_memory_usage()
        
        mock_components['integration'].cleanup_unused_resources.assert_called()
        mock_components['framework'].garbage_collect.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])