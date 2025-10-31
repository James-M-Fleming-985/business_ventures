"""
End-to-End Tests for Correlation Dashboard & Visualization Feature
Feature ID: FEATURE-CA-002-04
"""

import pytest
import time
import json
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
import requests
import numpy as np
import pandas as pd


@pytest.fixture(scope="module")
def driver():
    """Initialize WebDriver for E2E tests"""
    driver = webdriver.Chrome()  # Ensure ChromeDriver is installed
    driver.maximize_window()
    yield driver
    driver.quit()


@pytest.fixture(scope="module")
def test_data():
    """Generate realistic test data for correlation analysis"""
    np.random.seed(42)
    
    # Generate correlated time series data
    n_points = 100
    dates = pd.date_range(start='2024-01-01', periods=n_points, freq='D')
    
    # Create correlated datasets
    base = np.random.randn(n_points).cumsum()
    
    return {
        'metrics': {
            'revenue': base * 1000 + np.random.randn(n_points) * 100,
            'user_count': base * 50 + np.random.randn(n_points) * 10,
            'conversion_rate': 0.1 + (base * 0.01) + np.random.randn(n_points) * 0.005,
            'page_views': np.abs(base * 500 + np.random.randn(n_points) * 50),
            'bounce_rate': 0.5 - (base * 0.01) + np.random.randn(n_points) * 0.02
        },
        'timestamps': dates.tolist(),
        'correlation_matrix': {
            'revenue_user_count': 0.85,
            'revenue_conversion_rate': 0.72,
            'page_views_bounce_rate': -0.65
        }
    }


@pytest.fixture
def api_base_url():
    """Base URL for API endpoints"""
    return "http://localhost:8080/api/v1"


@pytest.fixture
def dashboard_url():
    """Dashboard URL"""
    return "http://localhost:3000/dashboard/correlation"


class TestCorrelationDashboardE2E:
    """End-to-End test suite for Correlation Dashboard & Visualization"""
    
    @pytest.mark.e2e
    def test_complete_correlation_analysis_workflow(self, driver, dashboard_url, api_base_url, test_data):
        """
        Test complete workflow from data selection to correlation visualization
        
        Scenario:
        1. User navigates to correlation dashboard
        2. Selects multiple metrics for analysis
        3. Configures time range and correlation parameters
        4. Generates correlation matrix and visualizations
        5. Interacts with visualizations and exports results
        
        Acceptance Criteria:
        - Dashboard loads within 3 seconds
        - At least 2 metrics can be selected for correlation
        - Correlation matrix is displayed with heat map
        - Scatter plots show relationships between metrics
        - Export functionality works for all visualizations
        """
        
        # Navigate to dashboard
        driver.get(dashboard_url)
        wait = WebDriverWait(driver, 10)
        
        # Verify dashboard loaded
        dashboard_title = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.dashboard-title"))
        )
        assert "Correlation Dashboard" in dashboard_title.text
        
        # Select metrics for correlation analysis
        metric_selector = wait.until(
            EC.element_to_be_clickable((By.ID, "metric-selector"))
        )
        metric_selector.click()
        
        # Select multiple metrics
        metrics_to_select = ['revenue', 'user_count', 'conversion_rate']
        for metric in metrics_to_select:
            metric_option = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, f"li[data-metric='{metric}']"))
            )
            metric_option.click()
        
        # Close metric selector
        driver.find_element(By.CSS_SELECTOR, "body").click()
        
        # Set time range
        time_range_selector = driver.find_element(By.ID, "time-range-selector")
        time_range_selector.click()
        last_30_days = driver.find_element(By.CSS_SELECTOR, "option[value='30d']")
        last_30_days.click()
        
        # Configure correlation settings
        correlation_method = driver.find_element(By.ID, "correlation-method")
        correlation_method.click()
        pearson_option = driver.find_element(By.CSS_SELECTOR, "option[value='pearson']")
        pearson_option.click()
        
        # Set minimum correlation threshold
        threshold_slider = driver.find_element(By.ID, "correlation-threshold")
        ActionChains(driver).drag_and_drop_by_offset(threshold_slider, 50, 0).perform()
        
        # Generate correlation analysis
        generate_button = driver.find_element(By.ID, "generate-correlation")
        generate_button.click()
        
        # Wait for analysis to complete
        loading_indicator = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".loading-spinner"))
        )
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".loading-spinner")))
        
        # Verify correlation matrix is displayed
        correlation_matrix = wait.until(
            EC.presence_of_element_located((By.ID, "correlation-matrix"))
        )
        assert correlation_matrix.is_displayed()
        
        # Verify heat map visualization
        heatmap = driver.find_element(By.CSS_SELECTOR, ".correlation-heatmap svg")
        assert heatmap.is_displayed()
        
        # Verify correlation values are shown
        correlation_cells = driver.find_elements(By.CSS_SELECTOR, ".correlation-cell")
        assert len(correlation_cells) >= 9  # 3x3 matrix
        
        # Test interactive features - hover over correlation cell
        first_cell = correlation_cells[0]
        ActionChains(driver).move_to_element(first_cell).perform()
        
        # Verify tooltip appears
        tooltip = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".correlation-tooltip"))
        )
        assert "Correlation:" in tooltip.text
        
        # Click on a correlation cell to view scatter plot
        high_correlation_cell = driver.find_element(
            By.CSS_SELECTOR, ".correlation-cell[data-correlation='high']"
        )
        high_correlation_cell.click()
        
        # Verify scatter plot modal opens
        scatter_plot_modal = wait.until(
            EC.visibility_of_element_located((By.ID, "scatter-plot-modal"))
        )
        assert scatter_plot_modal.is_displayed()
        
        # Verify scatter plot is rendered
        scatter_plot = driver.find_element(By.CSS_SELECTOR, "#scatter-plot-modal .scatter-plot svg")
        assert scatter_plot.is_displayed()
        
        # Test export functionality
        export_button = driver.find_element(By.ID, "export-correlation-data")
        export_button.click()
        
        # Select export format
        export_dropdown = wait.until(
            EC.visibility_of_element_located((By.ID, "export-format-dropdown"))
        )
        csv_option = driver.find_element(By.CSS_SELECTOR, "option[value='csv']")
        csv_option.click()
        
        # Confirm export
        confirm_export = driver.find_element(By.ID, "confirm-export")
        confirm_export.click()
        
        # Wait for download to start (checking for success message)
        success_message = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".export-success"))
        )
        assert "Export successful" in success_message.text
        
        # Close modal
        close_button = driver.find_element(By.CSS_SELECTOR, "#scatter-plot-modal .close-button")
        close_button.click()
        
        # Verify modal is closed
        wait.until(EC.invisibility_of_element_located((By.ID, "scatter-plot-modal")))
    
    @pytest.mark.e2e
    def test_real_time_correlation_updates(self, driver, dashboard_url, api_base_url, test_data):
        """
        Test real-time updates of correlation data and visualizations
        
        Scenario:
        1. User enables real-time correlation monitoring
        2. System receives new data points via WebSocket/API
        3. Correlation matrix updates automatically
        4. Visualizations reflect changes in real-time
        5. Alerts trigger for significant correlation changes
        
        Acceptance Criteria:
        - Real-time toggle is functional
        - Updates occur within 5 seconds of new data
        - Correlation changes are highlighted
        - Performance remains stable with continuous updates
        - Alert notifications appear for threshold breaches
        """
        
        # Navigate to dashboard
        driver.get(dashboard_url)
        wait = WebDriverWait(driver, 10)
        
        # Wait for dashboard to load
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.dashboard-title")))
        
        # Select metrics for real-time monitoring
        metric_selector = wait.until(
            EC.element_to_be_clickable((By.ID, "metric-selector"))
        )
        metric_selector.click()
        
        metrics = ['revenue', 'user_count', 'page_views']
        for metric in metrics:
            option = driver.find_element(By.CSS_SELECTOR, f"li[data-metric='{metric}']")
            option.click()
        
        driver.find_element(By.CSS_SELECTOR, "body").click()
        
        # Enable real-time mode
        realtime_toggle = driver.find_element(By.ID, "realtime-toggle")
        realtime_toggle.click()
        
        # Verify real-time indicator is active
        realtime_indicator = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".realtime-active"))
        )
        assert "LIVE" in realtime_indicator.text
        
        # Generate initial correlation
        generate_button = driver.find_element(By.ID, "generate-correlation")
        generate_button.click()
        
        # Wait for initial correlation matrix
        wait.until(EC.presence_of_element_located((By.ID, "correlation-matrix")))
        
        # Capture initial correlation values
        initial_correlations = {}
        correlation_cells = driver.find_elements(By.CSS_SELECTOR, ".correlation-cell")
        for cell in correlation_cells:
            metric_pair = cell.get_attribute("data-metric-pair")
            value = cell.get_attribute("data-value")
            if metric_pair and value:
                initial_correlations[metric_pair] = float(value)
        
        # Simulate new data arrival via API
        new_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "revenue": 15000,
                "user_count": 850,
                "page_views": 12000
            }
        }
        
        # Send new data point
        response = requests.post(
            f"{api_base_url}/metrics/realtime",
            json=new_data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        # Wait for real-time update (max 5 seconds)
        time.sleep(2)
        
        # Check for update indicator
        update_indicator = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".correlation-updating"))
        )
        
        # Wait for update to complete
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".correlation-updating")))
        
        # Verify correlations have been updated
        updated_cells = driver.find_elements(By.CSS_SELECTOR, ".correlation-cell")
        updated_correlations = {}
        for cell in updated_cells:
            metric_pair = cell.get_attribute("data-metric-pair")
            value = cell.get_attribute("data-value")
            if metric_pair and value:
                updated_correlations[metric_pair] = float(value)
        
        # At least one correlation should have changed
        changes_detected = False
        for pair in initial_correlations:
            if pair in updated_correlations:
                if initial_correlations[pair] != updated_correlations[pair]:
                    changes_detected = True
                    break
        
        assert changes_detected, "No correlation changes detected after real-time update"
        
        # Check for change highlighting
        highlighted_cells = driver.find_elements(By.CSS_SELECTOR, ".correlation-cell.changed")
        assert len(highlighted_cells) > 0, "Changed correlations should be highlighted"
        
        # Test alert for significant correlation change
        # Send data that will cause a significant change
        anomaly_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "revenue": 5000,  # Significant drop
                "user_count": 850,
                "page_views": 15000  # Increase
            }
        }
        
        response = requests.post(
            f"{api_base_url}/metrics/realtime",
            json=anomaly_data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        # Wait for alert notification
        alert_notification = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".correlation-alert"))
        )
        assert "Significant correlation change detected" in alert_notification.text
        
        # Verify performance - check update time
        performance_metric = driver.find_element(By.ID, "update-performance")
        update_time = float(performance_metric.get_attribute("data-last-update-time"))
        assert update_time < 5000, "Updates should complete within 5 seconds"
        
        # Disable real-time mode
        realtime_toggle.click()
        
        # Verify real-time mode is disabled
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".realtime-active")))
    
    @pytest.mark.e2e
    def test_correlation_analysis_error_handling(self, driver, dashboard_url, api_base_url):
        """
        Test error handling and edge cases in correlation analysis
        
        Scenario:
        1. User attempts correlation with insufficient data
        2. User selects incompatible metrics
        3. API failures during correlation calculation
        4. Invalid parameter configurations
        5. Recovery from errors
        
        Acceptance Criteria:
        - Clear error messages for all failure scenarios
        - Graceful degradation when data is unavailable
        - No data loss on error
        - Easy recovery path for users
        - Errors are logged appropriately
        """
        
        # Navigate to dashboard
        driver.get(dashboard_url)
        wait = WebDriverWait(driver, 10)
        
        # Wait for dashboard to load
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.dashboard-title")))
        
        # Test 1: Attempt correlation with single metric (insufficient)
        metric_selector = wait.until(
            EC.element_to_be_clickable((By.ID, "metric-selector"))
        )
        metric_selector.click()
        
        single_metric = driver.find_element(By.CSS_SELECTOR, "li[data-metric='revenue']")
        single_metric.click()
        driver.find_element(By.CSS_SELECTOR, "body").click()
        
        generate_button = driver.find_element(By.ID, "generate-correlation")
        generate_button.click()
        
        # Verify error message
        error_message = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".error-message"))
        )
        assert "Please select at least 2 metrics" in error_message.text
        
        # Clear error
        error_close = driver.find_element(By.CSS_SELECTOR, ".error-message .close")
        error_close.click()
        
        # Test 2: Select incompatible metric types
        metric_selector.click()
        
        # Add a categorical metric (simulating incompatible type)
        categorical_metric = driver.find_element(By.CSS_SELECTOR, "li[data-metric='user_category']")
        categorical_metric.click()
        driver.find_element(By.CSS_SELECTOR, "body").click()
        
        generate_button.click()
        
        # Verify incompatibility warning
        warning_message = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".warning-message"))
        )
        assert "categorical" in warning_message.text.lower()
        
        # Test 3: Simulate API failure
        # Clear previous selections
        clear_button = driver.find_element(By.ID, "clear-selections")
        clear_button.click()
        
        # Select valid metrics
        metric_selector.click()
        metrics = ['revenue', 'user_count']
        for metric in metrics:
            option = driver.find_element(By.CSS_SELECTOR, f"li[data-metric='{metric}']")
            option.click()
        driver.find_element(By.CSS_SELECTOR, "body").click()
        
        # Inject API failure simulation
        driver.execute_script("""
            window.fetch = function() {
                return Promise.reject(new Error('API Connection Failed'));
            };
        """)
        
        generate_button.click()
        
        # Verify API error handling
        api_error = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".error-notification"))
        )
        assert "Failed to calculate correlations" in api_error.text
        assert "Please try again" in api_error.text
        
        # Verify retry button appears
        retry_button = driver.find_element(By.ID, "retry-correlation")
        assert retry_button.is_displayed()
        
        # Restore fetch for next tests
        driver.execute_script("delete window.fetch;")
        
        # Test 4: Invalid time range
        time_range_start = driver.find_element(By.ID, "custom-start-date")
        time_range_end = driver.find_element(By.ID, "custom-end-date")
        
        # Set end date before start date
        driver.execute_script("arguments[0].value = '2024-12-01'", time_range_start)
        driver.execute_script("arguments[0].value = '2024-01-01'", time_range_end)
        
        generate_button.click()
        
        # Verify date validation error
        date_error = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".date-error"))
        )
        assert "End date must be after start date" in date_error.text
        
        # Test 5: Insufficient data points
        # Set valid but very narrow time range
        driver.execute_script("arguments[0].value = '2024-01-01'", time_range_start)
        driver.execute_script("arguments[0].value = '2024-01-02'", time_range_end)
        
        generate_button.click()
        
        # Verify insufficient data error
        data_error = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".data-warning"))
        )
        assert "Insufficient data points" in data_error.text
        
        # Test 6: Recovery - show that user can recover from errors
        # Clear all errors
        driver.find_element(By.ID, "clear-all-errors").click()
        
        # Set valid parameters
        driver.execute_script("arguments[0].value = '2024-01-01'", time_range_start)
        driver.execute_script("arguments[0].value = '2024-03-01'", time_range_end)
        
        # Retry correlation
        generate_button.click()
        
        # Verify successful recovery
        correlation_matrix = wait.until(
            EC.presence_of_element_located((By.ID, "correlation-matrix"))
        )
        assert correlation_matrix.is_displayed()
        
        # Verify error log link is available
        error_log_link = driver.find_element(By.ID, "view-error-log")
        assert error_log_link.is_displayed()
        
        # Click to view error log
        error_log_link.click()
        
        # Verify error log modal
        error_log_modal = wait.until(
            EC.visibility_of_element_located((By.ID, "error-log-modal"))
        )
        
        # Check that previous errors are logged
        error_entries = driver.find_elements(By.CSS_SELECTOR, ".error-log-entry")
        assert len(error_entries) >= 3  # We generated at least 3 errors
        
        # Verify error details
        first_error = error_entries[0]
        assert "timestamp" in first_error.text.lower()
        assert "error" in first_error.text.lower()


@pytest.mark.e2e
class TestCorrelationVisualizationFeatures:
    """Additional E2E tests for advanced visualization features"""
    
    def test_multi_dimensional_correlation_visualization(self, driver, dashboard_url, test_data):
        """
        Test advanced visualization features for multi-dimensional correlations
        
        Scenario:
        1. User selects 5+ metrics for correlation analysis
        2. System generates various visualization types
        3. User interacts with 3D correlation plots
        4. User customizes visualization settings
        5. User saves visualization configuration
        
        Acceptance Criteria:
        - Support for 5+ metrics simultaneously
        - Multiple visualization types available
        - 3D visualizations are interactive
        - Customization options work correctly
        - Configurations can be saved and loaded
        """
        
        driver.get(dashboard_url)
        wait = WebDriverWait(driver, 10)
        
        # Wait for dashboard
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.dashboard-title")))
        
        # Select multiple metrics (5+)
        metric_selector = wait.until(
            EC.element_to_be_clickable((By.ID, "metric-selector"))
        )
        metric_selector.click()
        
        metrics = ['revenue', 'user_count', 'conversion_rate', 'page_views', 'bounce_rate', 'session_duration']
        for metric in metrics:
            option = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, f"li[data-metric='{metric}']"))
            )
            option.click()
        
        driver.find_element(By.CSS_SELECTOR, "body").click()
        
        # Generate correlation analysis
        generate_button = driver.find_element(By.ID, "generate-correlation")
        generate_button.click()
        
        # Wait for analysis
        wait.until(EC.presence_of_element_located((By.ID, "correlation-matrix")))
        
        # Switch to different visualization types
        viz_type_selector = driver.find_element(By.ID, "visualization-type")
        viz_type_selector.click()
        
        # Test network graph visualization
        network_option = driver.find_element(By.CSS_SELECTOR, "option[value='network']")
        network_option.click()
        
        network_graph = wait.until(
            EC.presence_of_element_located((By.ID, "correlation-network"))
        )
        assert network_graph.is_displayed()
        
        # Test 3D scatter plot
        viz_type_selector.click()
        three_d_option = driver.find_element(By.CSS_SELECTOR, "option[value='3d-scatter']")
        three_d_option.click()
        
        three_d_plot = wait.until(
            EC.presence_of_element_located((By.ID, "3d-correlation-plot"))
        )
        assert three_d_plot.is_displayed()
        
        # Interact with 3D plot (rotation)
        ActionChains(driver).click_and_hold(three_d_plot).move_by_offset(100, 50).release().perform()
        
        # Customize visualization
        customize_button = driver.find_element(By.ID, "customize-visualization")
        customize_button.click()
        
        # Change color scheme
        color_scheme = wait.until(
            EC.element_to_be_clickable((By.ID, "color-scheme-selector"))
        )
        color_scheme.click()
        diverging_option = driver.find_element(By.CSS_SELECTOR, "option[value='diverging']")
        diverging_option.click()
        
        # Save configuration
        save_config_button = driver.find_element(By.ID, "save-viz-config")
        save_config_button.click()
        
        config_name_input = wait.until(
            EC.visibility_of_element_located((By.ID, "config-name"))
        )
        config_name_input.send_keys("Multi-Metric Correlation Config")
        
        save_button = driver.find_element(By.ID, "confirm-save-config")
        save_button.click()
        
        # Verify save success
        success_toast = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".success-toast"))
        )
        assert "Configuration saved" in success_toast.text


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])