"""
End-to-End tests for Statistical Correlation Calculator
Feature ID: FEATURE-CA-002-01
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import requests
from unittest.mock import Mock, patch
import time


class TestStatisticalCorrelationCalculatorE2E:
    """End-to-End tests for the Statistical Correlation Calculator feature"""

    @pytest.fixture
    def base_url(self):
        """Base URL for the API endpoints"""
        return "http://localhost:8000/api/v1"

    @pytest.fixture
    def sample_datasets(self):
        """Realistic sample datasets for testing"""
        # Financial data: stock prices
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        stock_a = [100 + i + np.random.normal(0, 2) for i in range(len(dates))]
        stock_b = [50 + i*0.5 + np.random.normal(0, 1) for i in range(len(dates))]
        
        # Temperature and ice cream sales (positive correlation)
        temperature = list(range(15, 36))
        ice_cream_sales = [temp * 10 + np.random.normal(0, 20) for temp in temperature]
        
        # Study hours and exam scores (positive correlation)
        study_hours = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        exam_scores = [55, 60, 65, 70, 75, 80, 82, 85, 88, 92]
        
        return {
            'financial': {
                'dates': dates.tolist(),
                'stock_a': stock_a,
                'stock_b': stock_b
            },
            'sales': {
                'temperature': temperature,
                'ice_cream_sales': ice_cream_sales
            },
            'education': {
                'study_hours': study_hours,
                'exam_scores': exam_scores
            }
        }

    @pytest.fixture
    def auth_headers(self):
        """Authentication headers for API requests"""
        return {
            'Authorization': 'Bearer test-token-123',
            'Content-Type': 'application/json'
        }

    def test_e2e_complete_correlation_workflow_with_visualization(self, base_url, sample_datasets, auth_headers):
        """
        Test complete end-to-end workflow: upload data -> calculate correlation -> visualize -> export results
        
        Scenario: Data scientist uploads two datasets, calculates correlation, generates visualization, and exports results
        """
        # Step 1: Upload datasets
        upload_response = requests.post(
            f"{base_url}/correlation/upload",
            headers=auth_headers,
            json={
                'name': 'Stock Price Analysis',
                'description': 'Correlation between Stock A and Stock B prices',
                'dataset_x': {
                    'name': 'Stock A',
                    'values': sample_datasets['financial']['stock_a'],
                    'timestamps': [d.isoformat() if hasattr(d, 'isoformat') else d for d in sample_datasets['financial']['dates']]
                },
                'dataset_y': {
                    'name': 'Stock B',
                    'values': sample_datasets['financial']['stock_b'],
                    'timestamps': [d.isoformat() if hasattr(d, 'isoformat') else d for d in sample_datasets['financial']['dates']]
                }
            }
        )
        
        assert upload_response.status_code == 201
        upload_data = upload_response.json()
        assert 'dataset_id' in upload_data
        assert upload_data['status'] == 'uploaded'
        dataset_id = upload_data['dataset_id']
        
        # Step 2: Calculate correlation with multiple methods
        correlation_response = requests.post(
            f"{base_url}/correlation/calculate/{dataset_id}",
            headers=auth_headers,
            json={
                'methods': ['pearson', 'spearman', 'kendall'],
                'confidence_level': 0.95,
                'handle_missing': 'pairwise',
                'outlier_detection': True
            }
        )
        
        assert correlation_response.status_code == 200
        correlation_data = correlation_response.json()
        
        # Verify correlation results
        assert 'correlation_id' in correlation_data
        assert 'results' in correlation_data
        assert 'pearson' in correlation_data['results']
        assert 'spearman' in correlation_data['results']
        assert 'kendall' in correlation_data['results']
        
        # Verify correlation values are within valid range
        for method in ['pearson', 'spearman', 'kendall']:
            corr_value = correlation_data['results'][method]['coefficient']
            assert -1 <= corr_value <= 1
            assert 'p_value' in correlation_data['results'][method]
            assert 'confidence_interval' in correlation_data['results'][method]
        
        correlation_id = correlation_data['correlation_id']
        
        # Step 3: Generate visualization
        viz_response = requests.post(
            f"{base_url}/correlation/visualize/{correlation_id}",
            headers=auth_headers,
            json={
                'plot_types': ['scatter', 'heatmap', 'regression'],
                'include_confidence_bands': True,
                'format': 'png',
                'resolution': 'high'
            }
        )
        
        assert viz_response.status_code == 200
        viz_data = viz_response.json()
        assert 'visualization_urls' in viz_data
        assert len(viz_data['visualization_urls']) == 3
        
        # Step 4: Export results
        export_response = requests.post(
            f"{base_url}/correlation/export/{correlation_id}",
            headers=auth_headers,
            json={
                'format': 'pdf',
                'include_visualizations': True,
                'include_raw_data': False,
                'include_interpretation': True
            }
        )
        
        assert export_response.status_code == 200
        export_data = export_response.json()
        assert 'export_url' in export_data
        assert export_data['format'] == 'pdf'
        assert export_data['status'] == 'completed'
        
        # Step 5: Verify audit trail
        audit_response = requests.get(
            f"{base_url}/correlation/audit/{correlation_id}",
            headers=auth_headers
        )
        
        assert audit_response.status_code == 200
        audit_data = audit_response.json()
        assert len(audit_data['events']) >= 4  # upload, calculate, visualize, export
        assert audit_data['events'][0]['action'] == 'data_uploaded'
        assert audit_data['events'][-1]['action'] == 'results_exported'

    def test_e2e_batch_correlation_analysis_with_alerts(self, base_url, sample_datasets, auth_headers):
        """
        Test batch correlation analysis with threshold alerts
        
        Scenario: User performs batch correlation analysis on multiple variable pairs and sets up alerts
        """
        # Step 1: Create batch analysis job
        batch_request = {
            'name': 'Multi-Variable Correlation Analysis',
            'datasets': [
                {
                    'pair_name': 'Temperature vs Ice Cream Sales',
                    'x_values': sample_datasets['sales']['temperature'],
                    'y_values': sample_datasets['sales']['ice_cream_sales'],
                    'expected_correlation': 'positive'
                },
                {
                    'pair_name': 'Study Hours vs Exam Scores',
                    'x_values': sample_datasets['education']['study_hours'],
                    'y_values': sample_datasets['education']['exam_scores'],
                    'expected_correlation': 'positive'
                },
                {
                    'pair_name': 'Random Uncorrelated Data',
                    'x_values': list(np.random.normal(0, 1, 50)),
                    'y_values': list(np.random.normal(0, 1, 50)),
                    'expected_correlation': 'none'
                }
            ],
            'alert_thresholds': {
                'strong_positive': 0.7,
                'strong_negative': -0.7,
                'weak_correlation': 0.3
            },
            'notification_email': 'analyst@example.com'
        }
        
        batch_response = requests.post(
            f"{base_url}/correlation/batch",
            headers=auth_headers,
            json=batch_request
        )
        
        assert batch_response.status_code == 202  # Accepted for processing
        batch_data = batch_response.json()
        assert 'job_id' in batch_data
        assert batch_data['status'] == 'processing'
        job_id = batch_data['job_id']
        
        # Step 2: Poll for job completion
        max_attempts = 10
        attempt = 0
        job_status = None
        
        while attempt < max_attempts:
            status_response = requests.get(
                f"{base_url}/correlation/batch/status/{job_id}",
                headers=auth_headers
            )
            assert status_response.status_code == 200
            job_status = status_response.json()
            
            if job_status['status'] == 'completed':
                break
                
            time.sleep(1)  # Wait before next poll
            attempt += 1
        
        assert job_status['status'] == 'completed'
        assert 'results' in job_status
        assert len(job_status['results']) == 3
        
        # Step 3: Verify correlation results and alerts
        results = job_status['results']
        
        # Temperature vs Ice Cream Sales should have strong positive correlation
        temp_ice_cream = next(r for r in results if r['pair_name'] == 'Temperature vs Ice Cream Sales')
        assert temp_ice_cream['pearson_coefficient'] > 0.7
        assert temp_ice_cream['alert_triggered'] == True
        assert temp_ice_cream['alert_type'] == 'strong_positive'
        
        # Study Hours vs Exam Scores should have positive correlation
        study_exam = next(r for r in results if r['pair_name'] == 'Study Hours vs Exam Scores')
        assert study_exam['pearson_coefficient'] > 0.5
        
        # Random data should have weak correlation
        random_data = next(r for r in results if r['pair_name'] == 'Random Uncorrelated Data')
        assert abs(random_data['pearson_coefficient']) < 0.3
        assert random_data['alert_triggered'] == True
        assert random_data['alert_type'] == 'weak_correlation'
        
        # Step 4: Generate batch report
        report_response = requests.post(
            f"{base_url}/correlation/batch/report/{job_id}",
            headers=auth_headers,
            json={
                'format': 'html',
                'include_summary': True,
                'include_recommendations': True,
                'group_by_alert_type': True
            }
        )
        
        assert report_response.status_code == 200
        report_data = report_response.json()
        assert 'report_url' in report_data
        assert 'summary' in report_data
        assert report_data['summary']['total_pairs'] == 3
        assert report_data['summary']['alerts_triggered'] >= 2
        
        # Step 5: Verify notifications were sent
        notifications_response = requests.get(
            f"{base_url}/correlation/notifications/{job_id}",
            headers=auth_headers
        )
        
        assert notifications_response.status_code == 200
        notifications_data = notifications_response.json()
        assert len(notifications_data['notifications']) > 0
        assert any(n['type'] == 'email' for n in notifications_data['notifications'])
        assert any(n['recipient'] == 'analyst@example.com' for n in notifications_data['notifications'])

    def test_e2e_time_series_correlation_with_lag_analysis(self, base_url, sample_datasets, auth_headers):
        """
        Test time series correlation with lag analysis and anomaly detection
        
        Scenario: Analyze correlation between time series data with lag, detect anomalies, and forecast
        """
        # Generate time series data with lag relationship
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        # Leading indicator
        series_a = [50 + 10 * np.sin(2 * np.pi * i / 30) + np.random.normal(0, 2) for i in range(100)]
        # Lagging indicator (5-day lag)
        series_b = [0] * 5 + [50 + 10 * np.sin(2 * np.pi * i / 30) + np.random.normal(0, 2) for i in range(95)]
        
        # Add some anomalies
        series_a[45] = 80  # Spike anomaly
        series_b[70] = 20  # Drop anomaly
        
        # Step 1: Upload time series data
        ts_upload_response = requests.post(
            f"{base_url}/correlation/timeseries/upload",
            headers=auth_headers,
            json={
                'name': 'Economic Indicators Correlation',
                'description': 'Leading vs Lagging Economic Indicators',
                'series': [
                    {
                        'name': 'Leading Indicator',
                        'values': series_a,
                        'timestamps': [d.isoformat() for d in dates],
                        'frequency': 'daily'
                    },
                    {
                        'name': 'Lagging Indicator',
                        'values': series_b,
                        'timestamps': [d.isoformat() for d in dates],
                        'frequency': 'daily'
                    }
                ],
                'metadata': {
                    'source': 'Economic Database',
                    'units': 'Index Points'
                }
            }
        )
        
        assert ts_upload_response.status_code == 201
        ts_data = ts_upload_response.json()
        series_id = ts_data['series_id']
        
        # Step 2: Perform lag correlation analysis
        lag_analysis_response = requests.post(
            f"{base_url}/correlation/timeseries/analyze/{series_id}",
            headers=auth_headers,
            json={
                'analysis_type': 'lag_correlation',
                'max_lag': 15,
                'methods': ['cross_correlation', 'dynamic_time_warping'],
                'detrend': True,
                'seasonality_adjustment': True,
                'anomaly_detection': {
                    'enabled': True,
                    'method': 'isolation_forest',
                    'contamination': 0.05
                }
            }
        )
        
        assert lag_analysis_response.status_code == 200
        lag_analysis_data = lag_analysis_response.json()
        
        # Verify lag analysis results
        assert 'optimal_lag' in lag_analysis_data
        assert 'lag_correlations' in lag_analysis_data
        assert lag_analysis_data['optimal_lag'] == 5  # Should detect 5-day lag
        assert lag_analysis_data['max_correlation'] > 0.8
        assert 'anomalies' in lag_analysis_data
        assert len(lag_analysis_data['anomalies']['series_a']) >= 1
        assert len(lag_analysis_data['anomalies']['series_b']) >= 1
        
        analysis_id = lag_analysis_data['analysis_id']
        
        # Step 3: Generate rolling correlation analysis
        rolling_response = requests.post(
            f"{base_url}/correlation/timeseries/rolling/{analysis_id}",
            headers=auth_headers,
            json={
                'window_size': 30,
                'step_size': 1,
                'min_periods': 20,
                'center': True
            }
        )
        
        assert rolling_response.status_code == 200
        rolling_data = rolling_response.json()
        assert 'rolling_correlations' in rolling_data
        assert len(rolling_data['rolling_correlations']) > 0
        assert 'stability_score' in rolling_data  # Measure of correlation stability over time
        
        # Step 4: Forecast future correlation
        forecast_response = requests.post(
            f"{base_url}/correlation/timeseries/forecast/{analysis_id}",
            headers=auth_headers,
            json={
                'forecast_periods': 30,
                'method': 'arima',
                'include_confidence_intervals': True,
                'correlation_threshold_alert': 0.5
            }
        )
        
        assert forecast_response.status_code == 200
        forecast_data = forecast_response.json()
        assert 'forecasted_correlations' in forecast_data
        assert len(forecast_data['forecasted_correlations']) == 30
        assert 'confidence_intervals' in forecast_data
        assert 'alerts' in forecast_data
        
        # Step 5: Generate comprehensive time series report
        ts_report_response = requests.post(
            f"{base_url}/correlation/timeseries/report/{analysis_id}",
            headers=auth_headers,
            json={
                'sections': [
                    'executive_summary',
                    'lag_analysis',
                    'anomaly_detection',
                    'rolling_correlation',
                    'forecast',
                    'recommendations'
                ],
                'format': 'interactive_dashboard',
                'include_raw_data': False
            }
        )
        
        assert ts_report_response.status_code == 200
        ts_report_data = ts_report_response.json()
        assert 'dashboard_url' in ts_report_data
        assert ts_report_data['format'] == 'interactive_dashboard'
        assert 'access_token' in ts_report_data  # For dashboard authentication
        
        # Step 6: Set up monitoring alerts
        monitoring_response = requests.post(
            f"{base_url}/correlation/timeseries/monitor/{series_id}",
            headers=auth_headers,
            json={
                'monitoring_config': {
                    'check_frequency': 'daily',
                    'correlation_thresholds': {
                        'min': 0.3,
                        'max': 0.9
                    },
                    'anomaly_detection': True,
                    'trend_change_detection': True
                },
                'notifications': {
                    'email': ['analyst@example.com'],
                    'webhook': 'https://example.com/correlation-alerts'
                }
            }
        )
        
        assert monitoring_response.status_code == 201
        monitoring_data = monitoring_response.json()
        assert 'monitor_id' in monitoring_data
        assert monitoring_data['status'] == 'active'
        assert monitoring_data['next_check'] is not None

    def test_e2e_correlation_failure_scenarios(self, base_url, auth_headers):
        """
        Test various failure scenarios and error handling
        
        Scenario: Test system behavior under various error conditions
        """
        # Test 1: Invalid data format
        invalid_upload_response = requests.post(
            f"{base_url}/correlation/upload",
            headers=auth_headers,
            json={
                'name': 'Invalid Dataset',
                'dataset_x': {
                    'name': 'Series X',
                    'values': [1, 2, 'invalid', 4, 5]  # Invalid data type
                },
                'dataset_y': {
                    'name': 'Series Y',
                    'values': [5, 4, 3, 2, 1]
                }
            }
        )
        
        assert invalid_upload_response.status_code == 400
        error_data = invalid_upload_response.json()
        assert 'error' in error_data
        assert 'invalid data type' in error_data['error'].lower()
        
        # Test 2: Mismatched data lengths
        mismatch_response = requests.post(
            f"{base_url}/correlation/upload",
            headers=auth_headers,
            json={
                'name': 'Mismatched Dataset',
                'dataset_x': {
                    'name': 'Series X',
                    'values': [1, 2, 3, 4, 5]
                },
                'dataset_y': {
                    'name': 'Series Y',
                    'values': [5, 4, 3]  # Different length
                }
            }
        )
        
        assert mismatch_response.status_code == 400
        assert 'length mismatch' in mismatch_response.json()['error'].lower()
        
        # Test 3: Insufficient data points
        small_data_response = requests.post(
            f"{base_url}/correlation/upload",
            headers=auth_headers,
            json={
                'name': 'Small Dataset',
                'dataset_x': {
                    'name': 'Series X',
                    'values': [1, 2]  # Too few data points
                },
                'dataset_y': {
                    'name': 'Series Y',
                    'values': [2, 1]
                }
            }
        )
        
        # Should succeed upload but fail correlation calculation
        assert small_data_response.status_code == 201
        small_dataset_id = small_data_response.json()['dataset_id']
        
        correlation_fail_response = requests.post(
            f"{base_url}/correlation/calculate/{small_dataset_id}",
            headers=auth_headers,
            json={
                'methods': ['pearson'],
                'confidence_level': 0.95
            }
        )
        
        assert correlation_fail_response.status_code == 400
        assert 'insufficient data' in correlation_fail_response.json()['error'].lower()
        
        # Test 4: Unauthorized access
        unauthorized_response = requests.post(
            f"{base_url}/correlation/upload",
            headers={'Content-Type': 'application/json'},  # No auth header
            json={
                'name': 'Unauthorized Dataset',
                'dataset_x': {'name': 'X', 'values': [1, 2, 3]},
                'dataset_y': {'name': 'Y', 'values': [3, 2, 1]}
            }
        )
        
        assert unauthorized_response.status_code == 401
        assert 'unauthorized' in unauthorized_response.json()['error'].lower()
        
        # Test 5: Rate limiting
        rate_limit_responses = []
        for i in range(15):  # Attempt many requests quickly
            response = requests.post(
                f"{base_url}/correlation/calculate/test-dataset",
                headers=auth_headers,
                json={'methods': ['pearson']}
            )
            rate_limit_responses.append(response)
        
        # At least one should be rate limited
        assert any(r.status_code == 429 for r in rate_limit_responses)
        
        # Test 6: Non-existent resource
        not_found_response = requests.get(
            f"{base_url}/correlation/results/non-existent-id",
            headers=auth_headers
        )
        
        assert not_found_response.status_code == 404
        assert 'not found' in not_found_response.json()['error'].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])