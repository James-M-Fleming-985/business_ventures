"""
End-to-End tests for Regression Quantification Service
Feature ID: FEATURE-CA-002-09
"""

import pytest
import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import numpy as np
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class TestRegressionQuantificationE2E:
    """End-to-end tests for the Regression Quantification Service"""
    
    BASE_URL = "http://localhost:8080/api/v1"
    REGRESSION_SERVICE_URL = f"{BASE_URL}/regression-quantification"
    
    @classmethod
    def setup_class(cls):
        """Setup test environment"""
        cls.session = requests.Session()
        retry = Retry(
            total=3,
            read=3,
            connect=3,
            backoff_factor=0.3,
            status_forcelist=(500, 502, 504)
        )
        adapter = HTTPAdapter(max_retries=retry)
        cls.session.mount('http://', adapter)
        cls.session.mount('https://', adapter)
        
        # Test API key for authentication
        cls.headers = {
            "Authorization": "Bearer test-api-key-regression-service",
            "Content-Type": "application/json"
        }
    
    @classmethod
    def teardown_class(cls):
        """Cleanup test environment"""
        cls.session.close()
    
    def _generate_time_series_data(self, 
                                  num_points: int = 100, 
                                  trend: float = 0.5,
                                  seasonality: bool = True,
                                  noise_level: float = 0.1) -> List[Dict[str, Any]]:
        """Generate realistic time series data for testing"""
        data = []
        start_date = datetime.now() - timedelta(days=num_points)
        
        for i in range(num_points):
            timestamp = start_date + timedelta(days=i)
            
            # Base value with trend
            value = 100 + (trend * i)
            
            # Add seasonality
            if seasonality:
                value += 10 * np.sin(2 * np.pi * i / 30)  # Monthly pattern
                value += 5 * np.sin(2 * np.pi * i / 7)   # Weekly pattern
            
            # Add noise
            value += np.random.normal(0, noise_level * value)
            
            data.append({
                "timestamp": timestamp.isoformat(),
                "value": round(value, 2),
                "metric_name": "test_metric"
            })
        
        return data
    
    def _wait_for_job_completion(self, job_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for an async job to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = self.session.get(
                f"{self.REGRESSION_SERVICE_URL}/jobs/{job_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                job_status = response.json()
                
                if job_status["status"] in ["COMPLETED", "FAILED"]:
                    return job_status
                    
            time.sleep(2)
        
        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")
    
    @pytest.mark.e2e
    def test_e2e_simple_regression_quantification_workflow(self):
        """
        Test complete workflow for simple regression quantification:
        1. Submit time series data
        2. Run regression analysis
        3. Retrieve quantification results
        4. Validate regression metrics
        """
        # Step 1: Generate and submit time series data
        test_data = self._generate_time_series_data(
            num_points=90,
            trend=0.8,
            seasonality=False,
            noise_level=0.05
        )
        
        submit_request = {
            "dataset_name": "test_simple_regression",
            "data_points": test_data,
            "metadata": {
                "source": "e2e_test",
                "metric_type": "performance",
                "unit": "ms"
            }
        }
        
        response = self.session.post(
            f"{self.REGRESSION_SERVICE_URL}/datasets",
            json=submit_request,
            headers=self.headers
        )
        
        assert response.status_code == 201, f"Failed to submit dataset: {response.text}"
        dataset_response = response.json()
        dataset_id = dataset_response["dataset_id"]
        
        # Step 2: Run regression analysis
        regression_request = {
            "dataset_id": dataset_id,
            "regression_config": {
                "type": "linear",
                "confidence_level": 0.95,
                "include_diagnostics": True,
                "detect_changepoints": False
            }
        }
        
        response = self.session.post(
            f"{self.REGRESSION_SERVICE_URL}/analyze",
            json=regression_request,
            headers=self.headers
        )
        
        assert response.status_code == 202, f"Failed to start regression analysis: {response.text}"
        analysis_response = response.json()
        job_id = analysis_response["job_id"]
        
        # Step 3: Wait for analysis completion
        job_result = self._wait_for_job_completion(job_id)
        assert job_result["status"] == "COMPLETED", f"Job failed: {job_result}"
        
        # Step 4: Retrieve regression results
        response = self.session.get(
            f"{self.REGRESSION_SERVICE_URL}/results/{job_id}",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed to retrieve results: {response.text}"
        results = response.json()
        
        # Validate regression results
        assert "regression_model" in results
        assert "coefficients" in results["regression_model"]
        assert "r_squared" in results["regression_model"]
        assert "p_values" in results["regression_model"]
        
        # Validate regression quality metrics
        r_squared = results["regression_model"]["r_squared"]
        assert 0.7 <= r_squared <= 1.0, f"R-squared {r_squared} indicates poor fit"
        
        # Validate slope (should detect positive trend)
        slope = results["regression_model"]["coefficients"]["slope"]
        assert slope > 0.5, f"Expected positive slope, got {slope}"
        
        # Validate diagnostics if included
        if "diagnostics" in results:
            assert "residuals_analysis" in results["diagnostics"]
            assert "normality_test" in results["diagnostics"]
            assert "heteroscedasticity_test" in results["diagnostics"]
    
    @pytest.mark.e2e
    def test_e2e_complex_regression_with_changepoint_detection(self):
        """
        Test complex regression workflow with changepoint detection:
        1. Submit time series with structural changes
        2. Run regression with changepoint detection
        3. Validate detected changepoints
        4. Verify piecewise regression results
        """
        # Generate data with changepoint
        data_part1 = self._generate_time_series_data(
            num_points=60,
            trend=0.3,
            seasonality=True,
            noise_level=0.08
        )
        
        data_part2 = self._generate_time_series_data(
            num_points=60,
            trend=1.5,  # Steeper trend after changepoint
            seasonality=True,
            noise_level=0.08
        )
        
        # Adjust second part values and timestamps
        last_value = data_part1[-1]["value"]
        last_timestamp = datetime.fromisoformat(data_part1[-1]["timestamp"])
        
        for i, point in enumerate(data_part2):
            point["value"] = last_value + (point["value"] - data_part2[0]["value"])
            point["timestamp"] = (last_timestamp + timedelta(days=i+1)).isoformat()
        
        combined_data = data_part1 + data_part2
        
        # Step 1: Submit dataset
        submit_request = {
            "dataset_name": "test_changepoint_regression",
            "data_points": combined_data,
            "metadata": {
                "source": "e2e_test",
                "expected_changepoints": 1,
                "description": "Dataset with structural break"
            }
        }
        
        response = self.session.post(
            f"{self.REGRESSION_SERVICE_URL}/datasets",
            json=submit_request,
            headers=self.headers
        )
        
        assert response.status_code == 201
        dataset_id = response.json()["dataset_id"]
        
        # Step 2: Run regression with changepoint detection
        regression_request = {
            "dataset_id": dataset_id,
            "regression_config": {
                "type": "piecewise_linear",
                "confidence_level": 0.95,
                "include_diagnostics": True,
                "detect_changepoints": True,
                "changepoint_config": {
                "method": "PELT",  # Pruned Exact Linear Time
                    "min_segment_size": 20,
                    "penalty": "BIC",
                    "max_changepoints": 3
                }
            }
        }
        
        response = self.session.post(
            f"{self.REGRESSION_SERVICE_URL}/analyze",
            json=regression_request,
            headers=self.headers
        )
        
        assert response.status_code == 202
        job_id = response.json()["job_id"]
        
        # Step 3: Wait and retrieve results
        job_result = self._wait_for_job_completion(job_id)
        assert job_result["status"] == "COMPLETED"
        
        response = self.session.get(
            f"{self.REGRESSION_SERVICE_URL}/results/{job_id}",
            headers=self.headers
        )
        
        assert response.status_code == 200
        results = response.json()
        
        # Validate changepoint detection
        assert "changepoints" in results
        changepoints = results["changepoints"]
        assert len(changepoints) >= 1, "Expected at least one changepoint"
        
        # Validate changepoint location (should be around index 60)
        primary_changepoint = changepoints[0]
        assert 50 <= primary_changepoint["index"] <= 70, \
            f"Changepoint detected at unexpected location: {primary_changepoint['index']}"
        
        # Validate piecewise regression results
        assert "piecewise_models" in results
        assert len(results["piecewise_models"]) == len(changepoints) + 1
        
        # Verify different slopes before and after changepoint
        first_segment_slope = results["piecewise_models"][0]["coefficients"]["slope"]
        second_segment_slope = results["piecewise_models"][1]["coefficients"]["slope"]
        
        assert second_segment_slope > first_segment_slope * 2, \
            f"Expected significant slope increase after changepoint: {first_segment_slope} -> {second_segment_slope}"
        
        # Validate model comparison metrics
        assert "model_comparison" in results
        assert results["model_comparison"]["piecewise_aic"] < results["model_comparison"]["linear_aic"], \
            "Piecewise model should have better AIC than simple linear model"
    
    @pytest.mark.e2e
    def test_e2e_regression_failure_and_recovery_workflow(self):
        """
        Test regression service failure handling and recovery:
        1. Submit invalid/problematic data
        2. Verify proper error handling
        3. Submit corrected data
        4. Verify successful analysis after recovery
        """
        # Step 1: Submit dataset with insufficient data points
        insufficient_data = self._generate_time_series_data(
            num_points=5,  # Too few points for meaningful regression
            trend=0.5
        )
        
        submit_request = {
            "dataset_name": "test_insufficient_data",
            "data_points": insufficient_data,
            "metadata": {
                "source": "e2e_test_failure"
            }
        }
        
        response = self.session.post(
            f"{self.REGRESSION_SERVICE_URL}/datasets",
            json=submit_request,
            headers=self.headers
        )
        
        # Should accept dataset but fail during analysis
        assert response.status_code == 201
        dataset_id_insufficient = response.json()["dataset_id"]
        
        # Step 2: Try to run regression - should fail
        regression_request = {
            "dataset_id": dataset_id_insufficient,
            "regression_config": {
                "type": "polynomial",
                "degree": 3,  # High degree for few points
                "confidence_level": 0.95
            }
        }
        
        response = self.session.post(
            f"{self.REGRESSION_SERVICE_URL}/analyze",
            json=regression_request,
            headers=self.headers
        )
        
        if response.status_code == 202:
            # Job accepted, should fail during processing
            job_id = response.json()["job_id"]
            job_result = self._wait_for_job_completion(job_id)
            assert job_result["status"] == "FAILED"
            assert "error" in job_result
            assert "insufficient data" in job_result["error"]["message"].lower()
        else:
            # Immediate validation failure
            assert response.status_code == 400
            assert "error" in response.json()
        
        # Step 3: Submit dataset with missing values
        data_with_gaps = self._generate_time_series_data(num_points=50)
        # Introduce missing values
        for i in [10, 11, 25, 26, 27]:
            data_with_gaps[i]["value"] = None
        
        submit_request = {
            "dataset_name": "test_missing_values",
            "data_points": data_with_gaps,
            "metadata": {
                "source": "e2e_test_missing",
                "has_missing_values": True
            }
        }
        
        response = self.session.post(
            f"{self.REGRESSION_SERVICE_URL}/datasets",
            json=submit_request,
            headers=self.headers
        )
        
        assert response.status_code == 201
        dataset_id_missing = response.json()["dataset_id"]
        
        # Step 4: Run regression with missing value handling
        regression_request = {
            "dataset_id": dataset_id_missing,
            "regression_config": {
                "type": "linear",
                "confidence_level": 0.95,
                "missing_value_strategy": "interpolate",  # Handle missing values
                "include_diagnostics": True
            }
        }
        
        response = self.session.post(
            f"{self.REGRESSION_SERVICE_URL}/analyze",
            json=regression_request,
            headers=self.headers
        )
        
        assert response.status_code == 202
        job_id = response.json()["job_id"]
        
        job_result = self._wait_for_job_completion(job_id)
        assert job_result["status"] == "COMPLETED", "Should handle missing values gracefully"
        
        # Step 5: Verify recovery - submit clean data
        clean_data = self._generate_time_series_data(
            num_points=100,
            trend=0.6,
            seasonality=True,
            noise_level=0.05
        )
        
        submit_request = {
            "dataset_name": "test_recovery_clean",
            "data_points": clean_data,
            "metadata": {
                "source": "e2e_test_recovery",
                "description": "Clean dataset after failure tests"
            }
        }
        
        response = self.session.post(
            f"{self.REGRESSION_SERVICE_URL}/datasets",
            json=submit_request,
            headers=self.headers
        )
        
        assert response.status_code == 201
        dataset_id_clean = response.json()["dataset_id"]
        
        # Step 6: Run comprehensive regression analysis
        regression_request = {
            "dataset_id": dataset_id_clean,
            "regression_config": {
                "type": "auto",  # Let service choose best model
                "confidence_level": 0.95,
                "include_diagnostics": True,
                "include_forecasting": True,
                "forecast_periods": 10,
                "model_selection_criteria": "AIC"
            }
        }
        
        response = self.session.post(
            f"{self.REGRESSION_SERVICE_URL}/analyze",
            json=regression_request,
            headers=self.headers
        )
        
        assert response.status_code == 202
        job_id = response.json()["job_id"]
        
        job_result = self._wait_for_job_completion(job_id)
        assert job_result["status"] == "COMPLETED"
        
        # Verify final results
        response = self.session.get(
            f"{self.REGRESSION_SERVICE_URL}/results/{job_id}",
            headers=self.headers
        )
        
        assert response.status_code == 200
        results = response.json()
        
        # Validate comprehensive results
        assert "selected_model" in results
        assert "regression_model" in results
        assert "diagnostics" in results
        assert "forecast" in results
        assert len(results["forecast"]["predictions"]) == 10
        
        # Verify service health after recovery
        health_response = self.session.get(
            f"{self.REGRESSION_SERVICE_URL}/health",
            headers=self.headers
        )
        
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] == "healthy"
        assert health_data["service_name"] == "regression-quantification-service"
    
    @pytest.mark.e2e
    @pytest.mark.performance
    def test_e2e_regression_performance_and_scalability(self):
        """
        Test regression service performance with large datasets:
        1. Submit large time series dataset
        2. Run multiple concurrent analyses
        3. Verify performance metrics
        4. Test result caching
        """
        # Generate large dataset
        large_data = self._generate_time_series_data(
            num_points=10000,  # 10k data points
            trend=0.4,
            seasonality=True,
            noise_level=0.1
        )
        
        # Step 1: Submit large dataset
        start_time = time.time()
        
        submit_request = {
            "dataset_name": "test_large_dataset",
            "data_points": large_data,
            "metadata": {
                "source": "e2e_test_performance",
                "size": "large",
                "points": len(large_data)
            }
        }
        
        response = self.session.post(
            f"{self.REGRESSION_SERVICE_URL}/datasets",
            json=submit_request,
            headers=self.headers
        )
        
        upload_time = time.time() - start_time
        assert response.status_code == 201
        assert upload_time < 10, f"Dataset upload took too long: {upload_time}s"
        
        dataset_id = response.json()["dataset_id"]
        
        # Step 2: Run multiple analyses concurrently
        job_ids = []
        analysis_configs = [
            {"type": "linear", "name": "simple_linear"},
            {"type": "polynomial", "degree": 2, "name": "quadratic"},
            {"type": "robust", "method": "huber", "name": "robust_regression"},
            {"type": "ridge", "alpha": 0.1, "name": "ridge_regression"}
        ]
        
        start_time = time.time()
        
        for config in analysis_configs:
            regression_request = {
                "dataset_id": dataset_id,
                "regression_config": {
                    **config,
                    "confidence_level": 0.95,
                    "include_diagnostics": False  # Faster without diagnostics
                }
            }
            
            response = self.session.post(
                f"{self.REGRESSION_SERVICE_URL}/analyze",
                json=regression_request,
                headers=self.headers
            )
            
            assert response.status_code == 202
            job_ids.append({
                "id": response.json()["job_id"],
                "config": config["name"]
            })
        
        # Step 3: Wait for all jobs to complete
        completed_jobs = []
        for job_info in job_ids:
            job_result = self._wait_for_job_completion(job_info["id"], timeout=120)
            assert job_result["status"] == "COMPLETED", \
                f"Job {job_info['config']} failed: {job_result}"
            completed_jobs.append(job_info)
        
        total_analysis_time = time.time() - start_time
        assert total_analysis_time < 60, \
            f"Concurrent analyses took too long: {total_analysis_time}s"
        
        # Step 4: Test result caching
        # Retrieve same result multiple times
        job_id_to_test = job_ids[0]["id"]
        
        response_times = []
        for i in range(5):
            start_time = time.time()
            response = self.session.get(
                f"{self.REGRESSION_SERVICE_URL}/results/{job_id_to_test}",
                headers=self.headers
            )
            response_time = time.time() - start_time
            response_times.append(response_time)
            
            assert response.status_code == 200
            assert response.headers.get("X-Cache-Status") in ["HIT", "MISS"]
        
        # First request might be cache miss, subsequent should be faster
        avg_cached_time = np.mean(response_times[1:])
        assert avg_cached_time < 0.1, \
            f"Cached responses too slow: {avg_cached_time}s average"
        
        # Step 5: Verify batch operations
        batch_request = {
            "dataset_ids": [dataset_id],
            "regression_configs": [
                {
                    "type": "linear",
                    "confidence_level": 0.95,
                    "output_format": "summary"
                }
                for _ in range(10)  # 10 identical analyses
            ]
        }
        
        start_time = time.time()
        response = self.session.post(
            f"{self.REGRESSION_SERVICE_URL}/batch/analyze",
            json=batch_request,
            headers=self.headers
        )
        batch_time = time.time() - start_time
        
        if response.status_code == 200:
            # Synchronous batch processing
            batch_results = response.json()
            assert len(batch_results["results"]) == 10
            assert batch_time < 20, f"Batch processing too slow: {batch_time}s"
        else:
            # Asynchronous batch processing
            assert response.status_code == 202
            batch_job_id = response.json()["batch_job_id"]
            # Would wait for batch completion in real scenario
        
        # Performance summary
        print(f"\nPerformance Test Summary:")
        print(f"- Large dataset upload: {upload_time:.2f}s")
        print(f"- Concurrent analyses: {total_analysis_time:.2f}s")
        print(f"- Cached response time: {avg_cached_time:.3f}s")
        print(f"- Batch processing: {batch_time:.2f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])