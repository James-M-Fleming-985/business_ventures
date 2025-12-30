"""
End-to-End tests for Advanced 3D Visualizations Feature
Feature ID: FEATURE-001-002
"""

import pytest
import numpy as np
import time
from unittest.mock import patch, MagicMock
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


class Test3DVisualizationE2E:
    """End-to-end tests for Advanced 3D Visualizations feature"""
    
    @pytest.fixture(scope="class")
    def browser(self):
        """Setup and teardown browser instance"""
        driver = webdriver.Chrome()
        driver.maximize_window()
        yield driver
        driver.quit()
    
    @pytest.fixture
    def sample_3d_data(self):
        """Generate realistic 3D test data"""
        # Generate sample 3D scatter plot data
        np.random.seed(42)
        n_points = 1000
        
        data = {
            'scatter_3d': {
                'x': np.random.normal(0, 1, n_points).tolist(),
                'y': np.random.normal(0, 1, n_points).tolist(),
                'z': np.random.normal(0, 1, n_points).tolist(),
                'color': np.random.choice(['red', 'blue', 'green'], n_points).tolist(),
                'size': np.random.uniform(5, 20, n_points).tolist(),
                'labels': [f'Point_{i}' for i in range(n_points)]
            },
            'surface_3d': {
                'x': np.linspace(-5, 5, 50).tolist(),
                'y': np.linspace(-5, 5, 50).tolist(),
                'z': [[np.sin(np.sqrt(i**2 + j**2)) for j in range(50)] for i in range(50)]
            },
            'mesh_3d': {
                'vertices': np.random.rand(100, 3).tolist(),
                'faces': np.random.randint(0, 100, size=(150, 3)).tolist(),
                'colors': np.random.rand(100, 3).tolist()
            }
        }
        return data
    
    @pytest.fixture
    def api_endpoint(self):
        """API endpoint for 3D visualization service"""
        return "http://localhost:8000/api/v1/visualizations"
    
    def test_e2e_create_and_interact_3d_scatter_plot(self, browser, sample_3d_data, api_endpoint):
        """
        E2E Test 1: Create and interact with 3D scatter plot
        
        Scenario:
        1. User uploads 3D scatter plot data
        2. System processes and renders the visualization
        3. User interacts with the plot (rotate, zoom, pan)
        4. User exports the visualization
        
        Acceptance Criteria:
        - Data upload completes within 5 seconds
        - 3D visualization renders correctly
        - All interaction controls work properly
        - Export functionality produces valid output
        """
        # Navigate to 3D visualization page
        browser.get(f"{api_endpoint}/3d-visualizations")
        wait = WebDriverWait(browser, 10)
        
        # Step 1: Upload 3D scatter plot data
        upload_button = wait.until(
            EC.element_to_be_clickable((By.ID, "upload-3d-data"))
        )
        upload_button.click()
        
        # Select scatter plot type
        plot_type_dropdown = browser.find_element(By.ID, "plot-type-select")
        plot_type_dropdown.click()
        scatter_option = browser.find_element(By.XPATH, "//option[@value='scatter3d']")
        scatter_option.click()
        
        # Mock file upload with sample data
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'visualization_id': 'viz_12345',
                'status': 'processing',
                'render_url': f"{api_endpoint}/render/viz_12345"
            }
            mock_post.return_value = mock_response
            
            # Simulate data input
            data_input = browser.find_element(By.ID, "data-input-field")
            browser.execute_script(
                "arguments[0].value = arguments[1]",
                data_input,
                str(sample_3d_data['scatter_3d'])
            )
            
            submit_button = browser.find_element(By.ID, "submit-data")
            submit_button.click()
        
        # Step 2: Wait for visualization to render
        start_time = time.time()
        canvas_element = wait.until(
            EC.presence_of_element_located((By.ID, "3d-canvas"))
        )
        render_time = time.time() - start_time
        
        # Verify render time is within acceptable limits
        assert render_time < 5, f"Visualization took {render_time}s to render (expected < 5s)"
        
        # Verify canvas is visible and has correct dimensions
        assert canvas_element.is_displayed()
        canvas_size = canvas_element.size
        assert canvas_size['width'] >= 800
        assert canvas_size['height'] >= 600
        
        # Step 3: Test interactions
        action = ActionChains(browser)
        
        # Test rotation
        initial_view = browser.execute_script(
            "return window.getVisualizationCamera().rotation"
        )
        
        # Drag to rotate
        action.move_to_element(canvas_element)
        action.click_and_hold()
        action.move_by_offset(100, 100)
        action.release()
        action.perform()
        
        time.sleep(0.5)  # Wait for animation
        
        rotated_view = browser.execute_script(
            "return window.getVisualizationCamera().rotation"
        )
        assert initial_view != rotated_view, "Rotation did not work"
        
        # Test zoom
        initial_zoom = browser.execute_script(
            "return window.getVisualizationCamera().zoom"
        )
        
        # Scroll to zoom
        browser.execute_script(
            "arguments[0].dispatchEvent(new WheelEvent('wheel', {deltaY: -100}));",
            canvas_element
        )
        
        time.sleep(0.5)
        
        zoomed_view = browser.execute_script(
            "return window.getVisualizationCamera().zoom"
        )
        assert zoomed_view > initial_zoom, "Zoom in did not work"
        
        # Test pan
        action.move_to_element(canvas_element)
        action.key_down('\ue008')  # Shift key
        action.click_and_hold()
        action.move_by_offset(50, 50)
        action.release()
        action.key_up('\ue008')
        action.perform()
        
        # Step 4: Export visualization
        export_button = browser.find_element(By.ID, "export-3d-viz")
        export_button.click()
        
        # Select export format
        format_dropdown = browser.find_element(By.ID, "export-format")
        format_dropdown.click()
        png_option = browser.find_element(By.XPATH, "//option[@value='png']")
        png_option.click()
        
        # Confirm export
        confirm_export = browser.find_element(By.ID, "confirm-export")
        confirm_export.click()
        
        # Wait for export to complete
        export_status = wait.until(
            EC.text_to_be_present_in_element(
                (By.ID, "export-status"),
                "Export completed successfully"
            )
        )
        assert export_status
        
        # Verify download link appears
        download_link = browser.find_element(By.ID, "download-link")
        assert download_link.is_displayed()
        assert download_link.get_attribute('href').endswith('.png')
    
    def test_e2e_3d_surface_plot_with_real_time_updates(self, browser, sample_3d_data, api_endpoint):
        """
        E2E Test 2: Create 3D surface plot with real-time data updates
        
        Scenario:
        1. User creates a 3D surface plot
        2. User enables real-time data streaming
        3. System updates visualization in real-time
        4. User modifies visualization parameters
        
        Acceptance Criteria:
        - Surface plot renders correctly
        - Real-time updates occur without lag
        - Parameter changes reflect immediately
        - No memory leaks during streaming
        """
        browser.get(f"{api_endpoint}/3d-visualizations")
        wait = WebDriverWait(browser, 10)
        
        # Create surface plot
        create_button = wait.until(
            EC.element_to_be_clickable((By.ID, "create-new-viz"))
        )
        create_button.click()
        
        # Select surface plot
        viz_type = browser.find_element(By.ID, "viz-type-surface3d")
        viz_type.click()
        
        # Load initial data
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'visualization_id': 'viz_surface_123',
                'websocket_url': 'ws://localhost:8000/ws/viz_surface_123'
            }
            mock_post.return_value = mock_response
            
            # Input surface data
            data_textarea = browser.find_element(By.ID, "surface-data-input")
            browser.execute_script(
                "arguments[0].value = arguments[1]",
                data_textarea,
                str(sample_3d_data['surface_3d'])
            )
            
            create_viz_button = browser.find_element(By.ID, "create-viz-button")
            create_viz_button.click()
        
        # Wait for surface to render
        surface_element = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "surface-3d-container"))
        )
        assert surface_element.is_displayed()
        
        # Enable real-time streaming
        streaming_toggle = browser.find_element(By.ID, "enable-streaming")
        streaming_toggle.click()
        
        # Verify streaming indicator
        streaming_indicator = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "streaming-active"))
        )
        assert "active" in streaming_indicator.get_attribute("class")
        
        # Mock WebSocket connection for real-time updates
        with patch('websocket.create_connection') as mock_ws:
            mock_connection = MagicMock()
            mock_ws.return_value = mock_connection
            
            # Simulate 5 real-time updates
            initial_memory = browser.execute_script(
                "return performance.memory.usedJSHeapSize"
            )
            
            for i in range(5):
                # Generate updated surface data
                updated_z = [[np.sin(np.sqrt(i**2 + j**2) + i*0.1) 
                             for j in range(50)] for i in range(50)]
                
                # Simulate WebSocket message
                browser.execute_script(f"""
                    window.handleRealtimeUpdate({{
                        type: 'data_update',
                        data: {{
                            z: {updated_z}
                        }}
                    }});
                """)
                
                time.sleep(0.5)  # Wait for update to render
                
                # Verify surface updated
                update_counter = browser.find_element(By.ID, "update-counter")
                assert update_counter.text == f"Updates: {i + 1}"
            
            # Check for memory leaks
            final_memory = browser.execute_script(
                "return performance.memory.usedJSHeapSize"
            )
            memory_increase = (final_memory - initial_memory) / initial_memory
            assert memory_increase < 0.2, f"Memory increased by {memory_increase*100}%"
        
        # Modify visualization parameters
        colormap_selector = browser.find_element(By.ID, "colormap-select")
        colormap_selector.click()
        viridis_option = browser.find_element(By.XPATH, "//option[@value='viridis']")
        viridis_option.click()
        
        # Add contour lines
        contour_checkbox = browser.find_element(By.ID, "show-contours")
        contour_checkbox.click()
        
        # Verify changes applied
        time.sleep(0.5)
        surface_config = browser.execute_script(
            "return window.getCurrentVisualizationConfig()"
        )
        assert surface_config['colormap'] == 'viridis'
        assert surface_config['showContours'] == True
        
        # Stop streaming
        streaming_toggle.click()
        streaming_stopped = wait.until(
            EC.text_to_be_present_in_element(
                (By.CLASS_NAME, "streaming-status"),
                "Streaming stopped"
            )
        )
        assert streaming_stopped
    
    def test_e2e_3d_mesh_visualization_error_handling(self, browser, sample_3d_data, api_endpoint):
        """
        E2E Test 3: 3D mesh visualization with error handling and recovery
        
        Scenario:
        1. User attempts to load invalid 3D mesh data
        2. System provides meaningful error messages
        3. User corrects data and successfully creates visualization
        4. User tests performance with large mesh
        
        Acceptance Criteria:
        - Invalid data triggers appropriate error messages
        - System recovers gracefully from errors
        - Large meshes load with progress indication
        - Performance metrics are displayed
        """
        browser.get(f"{api_endpoint}/3d-visualizations")
        wait = WebDriverWait(browser, 10)
        
        # Test 1: Invalid mesh data
        mesh_button = wait.until(
            EC.element_to_be_clickable((By.ID, "load-mesh-3d"))
        )
        mesh_button.click()
        
        # Submit invalid data
        invalid_data = {
            'vertices': [[1, 2]],  # Invalid: should be 3D coordinates
            'faces': [[0, 1, 2, 3]]  # Invalid: faces should have 3 indices
        }
        
        mesh_input = browser.find_element(By.ID, "mesh-data-input")
        browser.execute_script(
            "arguments[0].value = arguments[1]",
            mesh_input,
            str(invalid_data)
        )
        
        submit_mesh = browser.find_element(By.ID, "submit-mesh")
        submit_mesh.click()
        
        # Verify error message
        error_message = wait.until(
            EC.visibility_of_element_located((By.CLASS_NAME, "error-message"))
        )
        assert "Invalid mesh data" in error_message.text
        assert "vertices must have 3 coordinates" in error_message.text
        
        # Verify error details
        error_details = browser.find_element(By.ID, "error-details")
        error_details.click()
        
        detailed_error = browser.find_element(By.CLASS_NAME, "error-stack")
        assert detailed_error.is_displayed()
        
        # Test 2: Correct the data
        retry_button = browser.find_element(By.ID, "retry-button")
        retry_button.click()
        
        # Clear previous input
        mesh_input.clear()
        
        # Submit valid mesh data
        browser.execute_script(
            "arguments[0].value = arguments[1]",
            mesh_input,
            str(sample_3d_data['mesh_3d'])
        )
        
        submit_mesh.click()
        
        # Verify success
        success_message = wait.until(
            EC.visibility_of_element_located((By.CLASS_NAME, "success-message"))
        )
        assert "Mesh loaded successfully" in success_message.text
        
        # Wait for mesh to render
        mesh_canvas = wait.until(
            EC.presence_of_element_located((By.ID, "mesh-3d-canvas"))
        )
        assert mesh_canvas.is_displayed()
        
        # Test 3: Load large mesh with progress tracking
        large_mesh_button = browser.find_element(By.ID, "load-large-mesh")
        large_mesh_button.click()
        
        # Generate large mesh data
        large_mesh = {
            'vertices': np.random.rand(10000, 3).tolist(),
            'faces': np.random.randint(0, 10000, size=(15000, 3)).tolist(),
            'colors': np.random.rand(10000, 3).tolist()
        }
        
        # Start loading with progress
        with patch('requests.post') as mock_post:
            # Simulate chunked upload
            def simulate_progress():
                for i in range(0, 101, 20):
                    browser.execute_script(f"""
                        window.updateProgress({{
                            loaded: {i},
                            total: 100
                        }});
                    """)
                    time.sleep(0.2)
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'status': 'processing'}
            mock_post.return_value = mock_response
            
            # Input large mesh data
            large_mesh_input = browser.find_element(By.ID, "large-mesh-input")
            browser.execute_script(
                "arguments[0].value = arguments[1]",
                large_mesh_input,
                str(large_mesh)
            )
            
            upload_large = browser.find_element(By.ID, "upload-large-mesh")
            upload_large.click()
            
            # Verify progress bar appears
            progress_bar = wait.until(
                EC.visibility_of_element_located((By.CLASS_NAME, "progress-bar"))
            )
            assert progress_bar.is_displayed()
            
            # Simulate progress updates
            simulate_progress()
            
            # Verify completion
            completion_message = wait.until(
                EC.text_to_be_present_in_element(
                    (By.CLASS_NAME, "load-status"),
                    "Large mesh loaded successfully"
                )
            )
            assert completion_message
        
        # Test 4: Check performance metrics
        perf_button = browser.find_element(By.ID, "show-performance")
        perf_button.click()
        
        perf_panel = wait.until(
            EC.visibility_of_element_located((By.ID, "performance-panel"))
        )
        
        # Verify performance metrics
        fps_counter = browser.find_element(By.ID, "fps-counter")
        assert float(fps_counter.text.replace("FPS: ", "")) >= 30
        
        vertex_count = browser.find_element(By.ID, "vertex-count")
        assert "10,000" in vertex_count.text
        
        face_count = browser.find_element(By.ID, "face-count")
        assert "15,000" in face_count.text
        
        render_time = browser.find_element(By.ID, "render-time")
        assert float(render_time.text.replace("ms", "")) < 100
        
        # Test mesh optimization
        optimize_button = browser.find_element(By.ID, "optimize-mesh")
        optimize_button.click()
        
        # Wait for optimization
        optimization_result = wait.until(
            EC.text_to_be_present_in_element(
                (By.ID, "optimization-status"),
                "Mesh optimized"
            )
        )
        assert optimization_result
        
        # Verify improved metrics
        optimized_faces = browser.find_element(By.ID, "optimized-face-count")
        original_faces = 15000
        optimized_count = int(optimized_faces.text.replace(",", ""))
        assert optimized_count < original_faces


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])