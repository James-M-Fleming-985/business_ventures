"""
End-to-end tests for Granger Causality API Service
Feature ID: FEATURE-CA-002-06
"""

import pytest
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import time
import json
from typing import Dict, List, Any


class TestGrangerCausalityE2E:
    """End-to-end tests for Granger Causality API Service"""
    
    BASE_URL = "http://localhost:8000/api/v1"
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authentication headers for API requests"""
        # Login to get auth token
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            json={"username": "testuser", "password": "testpass123"}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def sample_time_series_data(self):
        """Generate sample time series data for testing"""
        # Create two time series where series2 is influenced by series1
        np.random.seed(42)
        n_points = 100
        dates = pd.date_range(start='2023-01-01', periods=n_points, freq='D')
        
        # Series 1: Random walk
        series1 = np.cumsum(np.random.randn(n_points))
        
        # Series 2: Influenced by lagged values of series1 + noise
        series2 = np.zeros(n_points)
        for i in range(2, n_points):
            series2[i] = 0.7 * series1[i-1] + 0.3 * series1[i-2] + np.random.randn()
        
        return {
            "timestamps": [d.isoformat() for d in dates],
            "series1": series1.tolist(),
            "series2": series2.tolist()
        }
    
    @pytest.fixture
    def multivariate_time_series_data(self):
        """Generate multivariate time series data"""
        np.random.seed(123)
        n_points = 150
        dates = pd.date_range(start='2023-01-01', periods=n_points, freq='H')
        
        # Create complex relationships
        # X influences Y and Z
        # Y influences Z
        # Z doesn't influence others
        X = np.cumsum(np.random.randn(n_points))
        Y = np.zeros(n_points)
        Z = np.zeros(n_points)
        
        for i in range(3, n_points):
            Y[i] = 0.5 * X[i-1] + 0.2 * X[i-2] + 0.3 * Y[i-1] + np.random.randn() * 0.5
            Z[i] = 0.4 * X[i-1] + 0.3 * Y[i-1] + 0.2 * Y[i-2] + np.random.randn() * 0.5
        
        return {
            "timestamps": [d.isoformat() for d in dates],
            "series": {
                "X": X.tolist(),
                "Y": Y.tolist(),
                "Z": Z.tolist()
            }
        }

    def test_e2e_basic_granger_causality_analysis(self, auth_headers, sample_time_series_data):
        """
        Test complete workflow for basic Granger causality analysis between two time series
        
        Scenario:
        1. Upload time series data
        2. Configure analysis parameters
        3. Run Granger causality test
        4. Retrieve and verify results
        5. Download report
        """
        # Step 1: Create a new analysis project
        project_response = requests.post(
            f"{self.BASE_URL}/granger-causality/projects",
            headers=auth_headers,
            json={
                "name": "Stock Market Analysis",
                "description": "Testing causality between tech stocks and market index"
            }
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["project_id"]
        
        # Step 2: Upload time series data
        upload_response = requests.post(
            f"{self.BASE_URL}/granger-causality/projects/{project_id}/data",
            headers=auth_headers,
            json={
                "data_type": "time_series",
                "format": "json",
                "series": {
                    "tech_stock": {
                        "timestamps": sample_time_series_data["timestamps"],
                        "values": sample_time_series_data["series1"]
                    },
                    "market_index": {
                        "timestamps": sample_time_series_data["timestamps"],
                        "values": sample_time_series_data["series2"]
                    }
                }
            }
        )
        assert upload_response.status_code == 200
        data_id = upload_response.json()["data_id"]
        
        # Step 3: Configure analysis parameters
        config_response = requests.post(
            f"{self.BASE_URL}/granger-causality/projects/{project_id}/configure",
            headers=auth_headers,
            json={
                "data_id": data_id,
                "parameters": {
                    "max_lag": 5,
                    "significance_level": 0.05,
                    "test_type": "ssr_chi2test",
                    "trend": "c",  # constant term
                    "preprocess": {
                        "difference": False,
                        "standardize": True
                    }
                }
            }
        )
        assert config_response.status_code == 200
        
        # Step 4: Run Granger causality analysis
        analysis_response = requests.post(
            f"{self.BASE_URL}/granger-causality/projects/{project_id}/analyze",
            headers=auth_headers,
            json={
                "causality_tests": [
                    {
                        "cause": "tech_stock",
                        "effect": "market_index"
                    },
                    {
                        "cause": "market_index",
                        "effect": "tech_stock"
                    }
                ]
            }
        )
        assert analysis_response.status_code == 202
        job_id = analysis_response.json()["job_id"]
        
        # Step 5: Poll for job completion
        max_attempts = 30
        for _ in range(max_attempts):
            status_response = requests.get(
                f"{self.BASE_URL}/granger-causality/jobs/{job_id}/status",
                headers=auth_headers
            )
            assert status_response.status_code == 200
            status = status_response.json()["status"]
            
            if status == "completed":
                break
            elif status == "failed":
                pytest.fail(f"Analysis job failed: {status_response.json()}")
            
            time.sleep(1)
        else:
            pytest.fail("Analysis job timed out")
        
        # Step 6: Retrieve analysis results
        results_response = requests.get(
            f"{self.BASE_URL}/granger-causality/projects/{project_id}/results",
            headers=auth_headers
        )
        assert results_response.status_code == 200
        results = results_response.json()
        
        # Verify results structure and content
        assert "results" in results
        assert len(results["results"]) == 2
        
        # Check first causality test (tech_stock -> market_index)
        # Should show significant causality since we designed series2 to depend on series1
        test1 = next(r for r in results["results"] if r["cause"] == "tech_stock")
        assert test1["effect"] == "market_index"
        assert "p_value" in test1
        assert "f_statistic" in test1
        assert "is_significant" in test1
        assert test1["is_significant"] == True  # Should detect causality
        assert test1["p_value"] < 0.05
        
        # Step 7: Generate and download report
        report_response = requests.post(
            f"{self.BASE_URL}/granger-causality/projects/{project_id}/report",
            headers=auth_headers,
            json={
                "format": "pdf",
                "include_plots": True,
                "include_statistics": True
            }
        )
        assert report_response.status_code == 200
        report_url = report_response.json()["report_url"]
        
        # Download report
        download_response = requests.get(report_url, headers=auth_headers)
        assert download_response.status_code == 200
        assert download_response.headers["Content-Type"] == "application/pdf"
        assert len(download_response.content) > 1000  # Verify non-empty PDF
        
        # Cleanup
        cleanup_response = requests.delete(
            f"{self.BASE_URL}/granger-causality/projects/{project_id}",
            headers=auth_headers
        )
        assert cleanup_response.status_code == 204

    def test_e2e_multivariate_granger_causality_with_validation(self, auth_headers, multivariate_time_series_data):
        """
        Test multivariate Granger causality analysis with cross-validation
        
        Scenario:
        1. Upload multivariate time series
        2. Run stationarity tests
        3. Perform VAR model selection
        4. Execute multivariate Granger causality tests
        5. Validate results with different lag orders
        6. Export results in multiple formats
        """
        # Step 1: Create project for multivariate analysis
        project_response = requests.post(
            f"{self.BASE_URL}/granger-causality/projects",
            headers=auth_headers,
            json={
                "name": "Economic Indicators Analysis",
                "description": "Multivariate causality between economic indicators",
                "type": "multivariate"
            }
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["project_id"]
        
        # Step 2: Upload multivariate data
        upload_response = requests.post(
            f"{self.BASE_URL}/granger-causality/projects/{project_id}/data",
            headers=auth_headers,
            json={
                "data_type": "multivariate_time_series",
                "format": "json",
                "series": multivariate_time_series_data["series"],
                "timestamps": multivariate_time_series_data["timestamps"],
                "metadata": {
                    "frequency": "hourly",
                    "variables": ["X", "Y", "Z"],
                    "description": "Economic indicators time series"
                }
            }
        )
        assert upload_response.status_code == 200
        data_id = upload_response.json()["data_id"]
        
        # Step 3: Run stationarity tests
        stationarity_response = requests.post(
            f"{self.BASE_URL}/granger-causality/projects/{project_id}/stationarity-test",
            headers=auth_headers,
            json={
                "data_id": data_id,
                "tests": ["adf", "kpss", "pp"],
                "auto_difference": True
            }
        )
        assert stationarity_response.status_code == 200
        stationarity_results = stationarity_response.json()
        
        # Verify stationarity test results
        assert all(var in stationarity_results["results"] for var in ["X", "Y", "Z"])
        
        # Step 4: Perform VAR model selection
        var_selection_response = requests.post(
            f"{self.BASE_URL}/granger-causality/projects/{project_id}/var-selection",
            headers=auth_headers,
            json={
                "data_id": data_id,
                "max_lags": 10,
                "criteria": ["aic", "bic", "hqic", "fpe"],
                "apply_transformations": stationarity_results["recommended_transformations"]
            }
        )
        assert var_selection_response.status_code == 200
        var_selection = var_selection_response.json()
        optimal_lag = var_selection["optimal_lag"]
        
        # Step 5: Run multivariate Granger causality tests
        mv_causality_response = requests.post(
            f"{self.BASE_URL}/granger-causality/projects/{project_id}/multivariate-analyze",
            headers=auth_headers,
            json={
                "data_id": data_id,
                "lag_order": optimal_lag,
                "test_all_pairs": True,
                "include_instantaneous": False,
                "bootstrap": {
                    "enabled": True,
                    "iterations": 1000,
                    "confidence_level": 0.95
                }
            }
        )
        assert mv_causality_response.status_code == 202
        job_id = mv_causality_response.json()["job_id"]
        
        # Poll for completion
        completed = False
        for _ in range(60):  # Longer timeout for bootstrap
            status_response = requests.get(
                f"{self.BASE_URL}/granger-causality/jobs/{job_id}/status",
                headers=auth_headers
            )
            if status_response.json()["status"] == "completed":
                completed = True
                break
            time.sleep(2)
        
        assert completed, "Multivariate analysis job timed out"
        
        # Step 6: Retrieve comprehensive results
        results_response = requests.get(
            f"{self.BASE_URL}/granger-causality/projects/{project_id}/results/detailed",
            headers=auth_headers
        )
        assert results_response.status_code == 200
        results = results_response.json()
        
        # Verify expected causal relationships
        causality_matrix = results["causality_matrix"]
        assert causality_matrix["X"]["Y"]["is_significant"] == True  # X causes Y
        assert causality_matrix["X"]["Z"]["is_significant"] == True  # X causes Z
        assert causality_matrix["Y"]["Z"]["is_significant"] == True  # Y causes Z
        assert causality_matrix["Z"]["X"]["is_significant"] == False  # Z doesn't cause X
        assert causality_matrix["Z"]["Y"]["is_significant"] == False  # Z doesn't cause Y
        
        # Step 7: Validate with different lag orders
        validation_response = requests.post(
            f"{self.BASE_URL}/granger-causality/projects/{project_id}/validate",
            headers=auth_headers,
            json={
                "lag_range": [optimal_lag - 2, optimal_lag + 2],
                "cross_validation": {
                    "method": "rolling_window",
                    "window_size": 50,
                    "step_size": 10
                }
            }
        )
        assert validation_response.status_code == 200
        validation_results = validation_response.json()
        assert "consistency_score" in validation_results
        assert validation_results["consistency_score"] > 0.7  # Results should be consistent
        
        # Step 8: Export results in multiple formats
        formats = ["json", "csv", "excel"]
        for fmt in formats:
            export_response = requests.post(
                f"{self.BASE_URL}/granger-causality/projects/{project_id}/export",
                headers=auth_headers,
                json={
                    "format": fmt,
                    "include_raw_data": True,
                    "include_statistics": True,
                    "include_plots": fmt == "excel"
                }
            )
            assert export_response.status_code == 200
            assert "download_url" in export_response.json()

    def test_e2e_granger_causality_with_error_handling_and_recovery(self, auth_headers):
        """
        Test error handling and recovery mechanisms in the Granger causality service
        
        Scenario:
        1. Submit invalid data and verify error handling
        2. Test with insufficient data points
        3. Handle non-stationary series warnings
        4. Test job cancellation and recovery
        5. Verify data validation and preprocessing errors
        """
        # Step 1: Create project
        project_response = requests.post(
            f"{self.BASE_URL}/granger-causality/projects",
            headers=auth_headers,
            json={
                "name": "Error Handling Test Project",
                "description": "Testing error scenarios"
            }
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["project_id"]
        
        # Test 1: Invalid data format
        invalid_upload = requests.post(
            f"{self.BASE_URL}/granger-causality/projects/{project_id}/data",
            headers=auth_headers,
            json={
                "data_type": "time_series",
                "format": "invalid_format",
                "series": {"data": "malformed"}
            }
        )
        assert invalid_upload.status_code == 400
        assert "error" in invalid_upload.json()
        assert "format" in invalid_upload.json()["error"].lower()
        
        # Test 2: Insufficient data points
        short_data = {
            "timestamps": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "series": {
                "series1": [1.0, 2.0, 3.0],
                "series2": [2.0, 3.0, 4.0]
            }
        }
        
        short_upload = requests.post(
            f"{self.BASE_URL}/granger-causality/projects/{project_id}/data",
            headers=auth_headers,
            json={
                "data_type": "time_series",
                "format": "json",
                "series": short_data["series"],
                "timestamps": short_data["timestamps"]
            }
        )
        assert short_upload.status_code == 400
        assert "insufficient data" in short_upload.json()["error"].lower()
        
        # Test 3: Non-stationary series with proper handling
        # Create trending non-stationary data
        n_points = 100
        dates = pd.date_range(start='2023-01-01', periods=n_points, freq='D')
        trend = np.linspace(0, 10, n_points)
        series1 = trend + np.random.randn(n_points) * 0.5
        series2 = trend * 1.5 + np.random.randn(n_points) * 0.5
        
        nonstationary_data = {
            "timestamps": [d.isoformat() for d in dates],
            "series": {
                "trending_series1": series1.tolist(),
                "trending_series2": series2.tolist()
            }
        }
        
        upload_response = requests.post(
            f"{self.BASE_URL}/granger-causality/projects/{project_id}/data",
            headers=auth_headers,
            json={
                "data_type": "time_series",
                "format": "json",
                "series": nonstationary_data["series"],
                "timestamps": nonstationary_data["timestamps"]
            }
        )
        assert upload_response.status_code == 200
        data_id = upload_response.json()["data_id"]
        
        # Analyze without preprocessing - should warn about non-stationarity
        analysis_response = requests.post(
            f"{self.BASE_URL}/granger-causality/projects/{project_id}/analyze",
            headers=auth_headers,
            json={
                "data_id": data_id,
                "causality_tests": [
                    {
                        "cause": "trending_series1",
                        "effect": "trending_series2"
                    }
                ],
                "parameters": {
                    "max_lag": 5,
                    "check_stationarity": True,
                    "auto_transform": False
                }
            }
        )
        assert analysis_response.status_code == 202
        job_id = analysis_response.json()["job_id"]
        
        # Wait for completion
        time.sleep(2)
        results_response = requests.get(
            f"{self.BASE_URL}/granger-causality/jobs/{job_id}/result",
            headers=auth_headers
        )
        assert results_response.status_code == 200
        results = results_response.json()
        assert "warnings" in results
        assert any("non-stationary" in w.lower() for w in results["warnings"])
        
        # Test 4: Job cancellation
        # Start a long-running analysis
        long_analysis = requests.post(
            f"{self.BASE_URL}/granger-causality/projects/{project_id}/analyze",
            headers=auth_headers,
            json={
                "data_id": data_id,
                "causality_tests": [
                    {"cause": "trending_series1", "effect": "trending_series2"}
                ],
                "parameters": {
                    "max_lag": 20,
                    "bootstrap": {
                        "enabled": True,
                        "iterations": 10000
                    }
                }
            }
        )
        assert long_analysis.status_code == 202
        cancel_job_id = long_analysis.json()["job_id"]
        
        # Cancel the job
        time.sleep(1)
        cancel_response = requests.post(
            f"{self.BASE_URL}/granger-causality/jobs/{cancel_job_id}/cancel",
            headers=auth_headers
        )
        assert cancel_response.status_code == 200
        
        # Verify cancellation
        status_response = requests.get(
            f"{self.BASE_URL}/granger-causality/jobs/{cancel_job_id}/status",
            headers=auth_headers
        )
        assert status_response.json()["status"] in ["cancelled", "cancelling"]
        
        # Test 5: Missing values handling
        data_with_nulls = {
            "timestamps": [d.isoformat() for d in dates],
            "series": {
                "series_with_gaps": [1.0, 2.0, None, 4.0, None, 6.0] + [float(i) for i in range(7, n_points+1)],
                "complete_series": list(range(1, n_points+1))
            }
        }
        
        null_upload = requests.post(
            f"{self.BASE_URL}/granger-causality/projects/{project_id}/data",
            headers=auth_headers,
            json={
                "data_type": "time_series",
                "format": "json",
                "series": data_with_nulls["series"],
                "timestamps": data_with_nulls["timestamps"][:n_points],
                "missing_value_handling": "interpolate"
            }
        )
        assert null_upload.status_code == 200
        
        # Test 6: Concurrent request limit
        concurrent_requests = []
        for i in range(5):
            req = requests.post(
                f"{self.BASE_URL}/granger-causality/projects/{project_id}/analyze",
                headers=auth_headers,
                json={
                    "data_id": data_id,
                    "causality_tests": [{"cause": "trending_series1", "effect": "trending_series2"}],
                    "parameters": {"max_lag": 3}
                }
            )
            concurrent_requests.append(req)
        
        # At least one should be rate limited or queued
        status_codes = [r.status_code for r in concurrent_requests]
        assert 429 in status_codes or all(s in [202, 200] for s in status_codes)
        
        # Test 7: Recovery after service restart (simulated)
        # Save analysis state
        checkpoint_response = requests.post(
            f"{self.BASE_URL}/granger-causality/projects/{project_id}/checkpoint",
            headers=auth_headers
        )
        assert checkpoint_response.status_code == 200
        checkpoint_id = checkpoint_response.json()["checkpoint_id"]
        
        # Restore from checkpoint
        restore_response = requests.post(
            f"{self.BASE_URL}/granger-causality/projects/restore",
            headers=auth_headers,
            json={"checkpoint_id": checkpoint_id}
        )
        assert restore_response.status_code == 200
        restored_project_id = restore_response.json()["project_id"]
        assert restored_project_id
        
        # Cleanup
        for pid in [project_id, restored_project_id]:
            requests.delete(
                f"{self.BASE_URL}/granger-causality/projects/{pid}",
                headers=auth_headers
            )

    def test_e2e_real_time_streaming_granger_causality(self, auth_headers):
        """
        Test real-time streaming Granger causality analysis
        
        Scenario:
        1. Set up streaming data source
        2. Configure rolling window analysis
        3. Stream data and get real-time causality updates
        4. Handle concept drift detection
        5. Export streaming results
        """
        # Step 1: Create streaming project
        project_response = requests.post(
            f"{self.BASE_URL}/granger-causality/projects",
            headers=auth_headers,
            json={
                "name": "Real-time Market Analysis",
                "description": "Streaming causality analysis",
                "type": "streaming"
            }
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["project_id"]
        
        # Step 2: Configure streaming analysis
        stream_config = requests.post(
            f"{self.BASE_URL}/granger-causality/projects/{project_id}/streaming/configure",
            headers=auth_headers,
            json={
                "window_size": 50,
                "update_frequency": "1s",
                "lag_order": 3,
                "variables": ["price_A", "price_B", "volume"],
                "drift_detection": {
                    "enabled": True,
                    "method": "adwin",
                    "sensitivity": 0.05
                },
                "alerts": {
                    "causality_change": True,
                    "threshold": 0.1
                }
            }
        )
        assert stream_config.status_code == 200
        stream_id = stream_config.json()["stream_id"]
        
        # Step 3: Start streaming
        start_response = requests.post(
            f"{self.BASE_URL}/granger-causality/streams/{stream_id}/start",
            headers=auth_headers
        )
        assert start_response.status_code == 200
        
        # Step 4: Send streaming data
        np.random.seed(789)
        for i in range(100):
            timestamp = datetime.now().isoformat()
            
            # Simulate changing causal relationships
            if i < 50:
                # First half: A causes B
                price_a = np.sin(i * 0.1) + np.random.randn() * 0.1
                price_b = 0.8 * np.sin((i-2) * 0.1) + np.random.randn() * 0.1
                volume = abs(price_a - price_b) * 1000 + np.random.randn() * 100
            else:
                # Second half: B causes A (relationship reversal)
                price_b = np.sin(i * 0.1) + np.random.randn() * 0.1
                price_a = 0.8 * np.sin((i-2) * 0.1) + np.random.randn() * 0.1
                volume = abs(price_a - price_b) * 1500 + np.random.randn() * 100
            
            data_point = {
                "timestamp": timestamp,
                "values": {
                    "price_A": float(price_a),
                    "price_B": float(price_b),
                    "volume": float(volume)
                }
            }
            
            # Send data point
            send_response = requests.post(
                f"{self.BASE_URL}/granger-causality/streams/{stream_id}/data",
                headers=auth_headers,
                json=data_point
            )
            assert send_response.status_code in [200, 202]
            
            # Every 10 points, check for updates
            if i % 10 == 0 and i > 0:
                updates_response = requests.get(
                    f"{self.BASE_URL}/granger-causality/streams/{stream_id}/updates",
                    headers=auth_headers
                )
                assert updates_response.status_code == 200
                updates = updates_response.json()
                
                if i == 60:  # After relationship change
                    # Should detect drift and causality change
                    assert "drift_detected" in updates
                    assert "causality_changes" in updates
                    if updates["causality_changes"]:
                        changes = updates["causality_changes"]
                        assert any(c["pair"] == ["price_A", "price_B"] for c in changes)
            
            time.sleep(0.1)  # Simulate real-time delay
        
        # Step 5: Get streaming summary
        summary_response = requests.get(
            f"{self.BASE_URL}/granger-causality/streams/{stream_id}/summary",
            headers=auth_headers
        )
        assert summary_response.status_code == 200
        summary = summary_response.json()
        
        # Verify summary contains expected information
        assert "total_points_processed" in summary
        assert summary["total_points_processed"] == 100
        assert "drift_events" in summary
        assert len(summary["drift_events"]) > 0
        assert "causality_matrix_history" in summary
        
        # Step 6: Stop streaming and export results
        stop_response = requests.post(
            f"{self.BASE_URL}/granger-causality/streams/{stream_id}/stop",
            headers=auth_headers
        )
        assert stop_response.status_code == 200
        
        # Export streaming results
        export_response = requests.post(
            f"{self.BASE_URL}/granger-causality/projects/{project_id}/export-streaming",
            headers=auth_headers,
            json={
                "stream_id": stream_id,
                "format": "json",
                "include_raw_stream": False,
                "include_drift_analysis": True,
                "include_causality_evolution": True
            }
        )
        assert export_response.status_code == 200
        export_url = export_response.json()["download_url"]
        
        # Download and verify export
        download_response = requests.get(export_url, headers=auth_headers)
        assert download_response.status_code == 200
        export_data = download_response.json()
        
        # Verify export contains causality evolution
        assert "causality_evolution" in export_data
        assert len(export_data["causality_evolution"]) > 0
        
        # Cleanup
        cleanup_response = requests.delete(
            f"{self.BASE_URL}/granger-causality/projects/{project_id}",
            headers=auth_headers
        )
        assert cleanup_response.status_code == 204


if __name__ == "__main__":
    pytest.main([__file__, "-v"])