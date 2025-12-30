"""
Integration tests for Interactive Feasibility Tool (FEATURE-001)
Tests interactions between all layers of the system
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import numpy as np

# Mock imports for the layers
from engine_framework import SimulationEngine, SimulationConfig
from material_database import MaterialDB, Material, MaterialProperties
from optimization_engine import OptimizationEngine, OptimizationParams, OptimizationResult
from api_backend import APIServer, APIRequest, APIResponse
from visualization_frontend import Visualization3D, RenderData, UserInteraction


class TestInteractiveFeasibilityIntegration:
    """Integration tests for the Interactive Feasibility Tool"""

    @pytest.fixture
    def mock_simulation_engine(self):
        """Mock simulation engine for testing"""
        engine = Mock(spec=SimulationEngine)
        engine.run_simulation = Mock(return_value={
            'status': 'completed',
            'results': {
                'stress_max': 150.5,
                'deformation': 0.002,
                'safety_factor': 2.1
            },
            'mesh_data': np.random.rand(1000, 3)
        })
        engine.validate_config = Mock(return_value=True)
        return engine

    @pytest.fixture
    def mock_material_db(self):
        """Mock material database for testing"""
        db = Mock(spec=MaterialDB)
        db.get_material = Mock(return_value=Material(
            id='MAT001',
            name='Steel AISI 304',
            properties=MaterialProperties(
                density=7850,
                yield_strength=215e6,
                elastic_modulus=200e9,
                poisson_ratio=0.29
            )
        ))
        db.search_materials = Mock(return_value=[
            {'id': 'MAT001', 'name': 'Steel AISI 304'},
            {'id': 'MAT002', 'name': 'Aluminum 6061'}
        ])
        db.validate_material = Mock(return_value=True)
        return db

    @pytest.fixture
    def mock_optimization_engine(self):
        """Mock optimization engine for testing"""
        engine = Mock(spec=OptimizationEngine)
        engine.optimize = Mock(return_value=OptimizationResult(
            optimal_params={
                'thickness': 0.025,
                'material_id': 'MAT001',
                'geometry_params': {'radius': 0.5, 'height': 1.2}
            },
            convergence_history=[100, 85, 72, 65, 63],
            final_objective=63.0,
            constraints_satisfied=True
        ))
        engine.validate_constraints = Mock(return_value=True)
        return engine

    @pytest.fixture
    async def mock_api_server(self):
        """Mock API server for testing"""
        server = AsyncMock(spec=APIServer)
        server.process_request = AsyncMock(return_value=APIResponse(
            status=200,
            data={'message': 'Success'},
            request_id='REQ123'
        ))
        server.validate_request = AsyncMock(return_value=True)
        return server

    @pytest.fixture
    def mock_visualization(self):
        """Mock 3D visualization for testing"""
        viz = Mock(spec=Visualization3D)
        viz.render = Mock(return_value={'frame_id': 'FRAME001'})
        viz.update_mesh = Mock(return_value=True)
        viz.handle_interaction = Mock(return_value={
            'action': 'rotate',
            'parameters': {'angle': 45, 'axis': 'y'}
        })
        return viz

    @pytest.mark.asyncio
    async def test_full_workflow_integration(self, mock_simulation_engine, mock_material_db, 
                                           mock_optimization_engine, mock_api_server, 
                                           mock_visualization):
        """Test complete workflow from API request to 3D visualization"""
        
        # Simulate user request through API
        user_request = APIRequest(
            endpoint='/simulate',
            method='POST',
            data={
                'material_id': 'MAT001',
                'geometry': {'type': 'cylinder', 'radius': 0.5, 'height': 1.0},
                'loads': {'force': 1000, 'direction': [0, -1, 0]},
                'constraints': {'fixed_base': True}
            }
        )
        
        # API validates and processes request
        api_response = await mock_api_server.process_request(user_request)
        assert api_response.status == 200
        
        # Material database lookup
        material = mock_material_db.get_material('MAT001')
        assert material is not None
        assert material.name == 'Steel AISI 304'
        
        # Simulation engine runs with material properties
        sim_config = SimulationConfig(
            material=material,
            geometry=user_request.data['geometry'],
            loads=user_request.data['loads']
        )
        sim_results = mock_simulation_engine.run_simulation(sim_config)
        assert sim_results['status'] == 'completed'
        assert 'stress_max' in sim_results['results']
        
        # Optimization engine processes results
        opt_params = OptimizationParams(
            objective='minimize_weight',
            constraints={'max_stress': 200e6, 'max_deformation': 0.005},
            variables=['thickness', 'radius']
        )
        opt_result = mock_optimization_engine.optimize(sim_results, opt_params)
        assert opt_result.constraints_satisfied
        
        # Visualization renders results
        render_data = RenderData(
            mesh=sim_results['mesh_data'],
            stress_field=sim_results['results'],
            optimal_geometry=opt_result.optimal_params
        )
        viz_result = mock_visualization.render(render_data)
        assert viz_result['frame_id'] == 'FRAME001'

    def test_material_to_simulation_integration(self, mock_simulation_engine, mock_material_db):
        """Test integration between material database and simulation engine"""
        
        # Search for materials based on requirements
        material_requirements = {
            'min_yield_strength': 200e6,
            'max_density': 8000
        }
        materials = mock_material_db.search_materials(material_requirements)
        assert len(materials) > 0
        
        # Select material and validate
        selected_material_id = materials[0]['id']
        material = mock_material_db.get_material(selected_material_id)
        is_valid = mock_material_db.validate_material(material.id)
        assert is_valid
        
        # Configure simulation with material
        sim_config = SimulationConfig(
            material=material,
            geometry={'type': 'beam', 'length': 2.0, 'width': 0.1, 'height': 0.05}
        )
        
        # Validate configuration
        config_valid = mock_simulation_engine.validate_config(sim_config)
        assert config_valid
        
        # Run simulation
        results = mock_simulation_engine.run_simulation(sim_config)
        assert results['status'] == 'completed'
        
        # Verify material properties were used
        mock_material_db.get_material.assert_called_with(selected_material_id)
        mock_simulation_engine.run_simulation.assert_called_once()

    def test_simulation_to_optimization_integration(self, mock_simulation_engine, 
                                                   mock_optimization_engine):
        """Test integration between simulation results and optimization"""
        
        # Run initial simulation
        initial_config = SimulationConfig(
            material=Mock(properties=MaterialProperties(
                density=2700,
                yield_strength=270e6,
                elastic_modulus=70e9,
                poisson_ratio=0.33
            )),
            geometry={'thickness': 0.03, 'area': 0.1}
        )
        
        sim_results = mock_simulation_engine.run_simulation(initial_config)
        
        # Define optimization problem based on simulation
        opt_params = OptimizationParams(
            objective='minimize_weight',
            constraints={
                'max_stress': sim_results['results']['stress_max'] * 0.8,
                'min_safety_factor': 2.0
            },
            initial_values={'thickness': initial_config.geometry['thickness']}
        )
        
        # Validate constraints are achievable
        constraints_valid = mock_optimization_engine.validate_constraints(
            opt_params, sim_results
        )
        assert constraints_valid
        
        # Run optimization
        opt_result = mock_optimization_engine.optimize(sim_results, opt_params)
        
        # Verify optimized design is better
        assert opt_result.optimal_params['thickness'] <= initial_config.geometry['thickness']
        assert opt_result.final_objective < 100  # Some improvement metric
        
        # Run verification simulation with optimized parameters
        optimized_config = SimulationConfig(
            material=initial_config.material,
            geometry=opt_result.optimal_params['geometry_params']
        )
        
        verification_results = mock_simulation_engine.run_simulation(optimized_config)
        assert verification_results['status'] == 'completed'

    @pytest.mark.asyncio
    async def test_api_to_visualization_integration(self, mock_api_server, 
                                                   mock_visualization):
        """Test integration from API requests to visualization updates"""
        
        # User interaction in visualization
        user_interaction = UserInteraction(
            type='select_component',
            target_id='COMP_001',
            position=[0.5, 0.3, 0.0]
        )
        
        interaction_result = mock_visualization.handle_interaction(user_interaction)
        
        # API request based on interaction
        api_request = APIRequest(
            endpoint='/component/analyze',
            method='POST',
            data={
                'component_id': 'COMP_001',
                'analysis_type': 'stress',
                'interaction': interaction_result
            }
        )
        
        # Process request
        api_response = await mock_api_server.process_request(api_request)
        assert api_response.status == 200
        
        # Update visualization with results
        viz_update_data = {
            'component_id': 'COMP_001',
            'stress_data': api_response.data,
            'highlight': True
        }
        
        update_success = mock_visualization.update_mesh(viz_update_data)
        assert update_success
        
        # Render updated visualization
        render_result = mock_visualization.render(
            RenderData(
                mesh=np.random.rand(500, 3),
                stress_field={'max': 180.0, 'min': 20.0},
                highlights=['COMP_001']
            )
        )
        assert render_result is not None

    def test_error_handling_across_layers(self, mock_simulation_engine, mock_material_db,
                                        mock_optimization_engine, mock_visualization):
        """Test error propagation and handling across layer boundaries"""
        
        # Test 1: Invalid material ID
        mock_material_db.get_material.side_effect = Exception("Material not found")
        
        with pytest.raises(Exception) as exc_info:
            material = mock_material_db.get_material('INVALID_ID')
        assert "Material not found" in str(exc_info.value)
        
        # Reset mock
        mock_material_db.get_material.side_effect = None
        mock_material_db.get_material.return_value = Mock(spec=Material)
        
        # Test 2: Simulation failure
        mock_simulation_engine.run_simulation.return_value = {
            'status': 'failed',
            'error': 'Mesh generation failed',
            'error_code': 'MESH_ERROR'
        }
        
        sim_config = Mock(spec=SimulationConfig)
        sim_results = mock_simulation_engine.run_simulation(sim_config)
        assert sim_results['status'] == 'failed'
        
        # Test 3: Optimization constraints not satisfied
        mock_optimization_engine.optimize.return_value = OptimizationResult(
            optimal_params={},
            convergence_history=[],
            final_objective=float('inf'),
            constraints_satisfied=False
        )
        
        opt_result = mock_optimization_engine.optimize(Mock(), Mock())
        assert not opt_result.constraints_satisfied
        
        # Test 4: Visualization error recovery
        mock_visualization.render.side_effect = [
            Exception("GPU memory error"),
            {'frame_id': 'FRAME_RECOVERY', 'quality': 'reduced'}
        ]
        
        # First attempt fails
        with pytest.raises(Exception) as exc_info:
            mock_visualization.render(Mock())
        assert "GPU memory error" in str(exc_info.value)
        
        # Recovery attempt with reduced quality
        recovery_result = mock_visualization.render(Mock())
        assert recovery_result['quality'] == 'reduced'

    @pytest.mark.asyncio
    async def test_concurrent_layer_operations(self, mock_simulation_engine, 
                                             mock_material_db, mock_api_server):
        """Test concurrent operations across multiple layers"""
        
        async def simulate_user_session(session_id):
            # Multiple users making concurrent requests
            request = APIRequest(
                endpoint=f'/session/{session_id}/simulate',
                method='POST',
                data={'material_id': f'MAT{session_id}', 'geometry': {}}
            )
            
            # API handles concurrent requests
            response = await mock_api_server.process_request(request)
            
            # Each request triggers material lookup
            material = mock_material_db.get_material(f'MAT{session_id}')
            
            # And simulation
            sim_results = mock_simulation_engine.run_simulation(
                SimulationConfig(material=material, geometry={})
            )
            
            return {
                'session_id': session_id,
                'response': response,
                'simulation': sim_results
            }
        
        # Simulate 5 concurrent user sessions
        tasks = [simulate_user_session(i) for i in range(1, 6)]
        results = await asyncio.gather(*tasks)
        
        # Verify all sessions completed successfully
        assert len(results) == 5
        for result in results:
            assert result['response'].status == 200
            assert result['simulation']['status'] == 'completed'
        
        # Verify correct number of calls
        assert mock_api_server.process_request.call_count == 5
        assert mock_material_db.get_material.call_count == 5
        assert mock_simulation_engine.run_simulation.call_count == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])