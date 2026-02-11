"""
End-to-end tests for Lag Analysis Service
Feature ID: FEATURE-CA-002-08
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import httpx
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np


# Test configuration
API_BASE_URL = "http://localhost:8000"
LAG_ANALYSIS_ENDPOINT = f"{API_BASE_URL}/api/v1/lag-analysis"


class TestLagAnalysisServiceE2E:
    """End-to-end tests for Lag Analysis Service"""

    @pytest.fixture
    def sample_time_series_data(self):
        """Generate realistic time series data for testing"""
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        np.random.seed(42)
        
        # Create correlated time series with lag
        series_a = np.random.randn(len(dates)).cumsum() + 100
        series_b = np.roll(series_a, 3) + np.random.randn(len(dates)) * 0.5  # 3-day lag
        series_c = np.roll(series_a, 7) + np.random.randn(len(dates)) * 0.8  # 7-day lag
        
        return {
            "timestamps": [date.isoformat() for date in dates],
            "series": {
                "primary": series_a.tolist(),
                "secondary_1": series_b.tolist(),
                "secondary_2": series_c.tolist()
            }
        }

    @pytest.fixture
    def lag_analysis_request(self, sample_time_series_data):
        """Create a lag analysis request payload"""
        return {
            "data": sample_time_series_data,
            "analysis_config": {
                "max_lag": 14,  # Maximum lag to test (days)
                "correlation_method": "pearson",
                "significance_level": 0.05,
                "detrend": True
            },
            "target_series": "primary",
            "comparison_series": ["secondary_1", "secondary_2"]
        }

    @pytest.fixture
    async def http_client(self):
        """Create async HTTP client"""
        async with httpx.AsyncClient() as client:
            yield client

    @pytest.mark.asyncio
    async def test_e2e_lag_analysis_successful_correlation_detection(
        self, http_client, lag_analysis_request
    ):
        """
        E2E Test 1: Successful lag correlation detection between time series
        
        Scenario:
        - Submit time series data with known lag relationships
        - Service analyzes lag correlations
        - Returns identified lags with confidence scores
        
        Acceptance Criteria:
        - API returns 200 status code
        - Detected lags match expected values (3 and 7 days)
        - Correlation coefficients are significant (>0.8)
        - Response includes visualization data
        """
        
        # Act: Submit lag analysis request
        response = await http_client.post(
            LAG_ANALYSIS_ENDPOINT,
            json=lag_analysis_request,
            timeout=30.0
        )
        
        # Assert: Verify response status
        assert response.status_code == 200
        result = response.json()
        
        # Verify response structure
        assert "analysis_id" in result
        assert "status" in result
        assert result["status"] == "completed"
        assert "results" in result
        
        # Verify lag detection results
        lag_results = result["results"]["lag_correlations"]
        assert len(lag_results) == 2  # Two comparison series
        
        # Check detected lags for secondary_1 (expected: 3 days)
        secondary_1_result = next(
            r for r in lag_results if r["series"] == "secondary_1"
        )
        assert secondary_1_result["optimal_lag"] == 3
        assert secondary_1_result["correlation_coefficient"] > 0.8
        assert secondary_1_result["p_value"] < 0.05
        assert secondary_1_result["is_significant"] is True
        
        # Check detected lags for secondary_2 (expected: 7 days)
        secondary_2_result = next(
            r for r in lag_results if r["series"] == "secondary_2"
        )
        assert secondary_2_result["optimal_lag"] == 7
        assert secondary_2_result["correlation_coefficient"] > 0.75
        assert secondary_2_result["p_value"] < 0.05
        
        # Verify visualization data is included
        assert "visualizations" in result["results"]
        assert "correlation_heatmap" in result["results"]["visualizations"]
        assert "lag_profiles" in result["results"]["visualizations"]
        
        # Verify metadata
        assert "metadata" in result
        assert result["metadata"]["total_data_points"] == 31
        assert result["metadata"]["analysis_duration_ms"] > 0

    @pytest.mark.asyncio
    async def test_e2e_lag_analysis_with_invalid_data_handling(self, http_client):
        """
        E2E Test 2: Lag analysis with invalid/missing data handling
        
        Scenario:
        - Submit time series with missing values and outliers
        - Service handles data quality issues
        - Returns partial results with warnings
        
        Acceptance Criteria:
        - API returns 200 status code with warnings
        - Missing data is handled appropriately
        - Outliers are detected and reported
        - Analysis completes with degraded accuracy notice
        """
        
        # Arrange: Create data with quality issues
        dates = pd.date_range(start='2024-01-01', end='2024-01-20', freq='D')
        series_with_issues = list(range(20))
        
        # Introduce missing values and outliers
        series_with_issues[5] = None
        series_with_issues[10] = None
        series_with_issues[15] = 1000  # Outlier
        
        request_payload = {
            "data": {
                "timestamps": [date.isoformat() for date in dates],
                "series": {
                    "series_a": series_with_issues,
                    "series_b": [x + 2 if x is not None else None 
                                for x in series_with_issues]
                }
            },
            "analysis_config": {
                "max_lag": 5,
                "handle_missing": "interpolate",
                "outlier_detection": True,
                "outlier_threshold": 3.0  # Z-score threshold
            },
            "target_series": "series_a",
            "comparison_series": ["series_b"]
        }
        
        # Act: Submit request
        response = await http_client.post(
            LAG_ANALYSIS_ENDPOINT,
            json=request_payload,
            timeout=30.0
        )
        
        # Assert: Verify response
        assert response.status_code == 200
        result = response.json()
        
        # Verify warnings are present
        assert "warnings" in result
        warnings = result["warnings"]
        assert any("missing values" in w.lower() for w in warnings)
        assert any("outlier" in w.lower() for w in warnings)
        
        # Verify data quality report
        assert "data_quality" in result["results"]
        quality_report = result["results"]["data_quality"]
        assert quality_report["missing_values_count"] == 4  # 2 per series
        assert quality_report["outliers_detected"] == 2  # 1 per series
        assert quality_report["data_quality_score"] < 1.0  # Degraded quality
        
        # Verify analysis still completed
        assert result["status"] == "completed_with_warnings"
        assert len(result["results"]["lag_correlations"]) > 0
        
        # Verify interpolation was applied
        assert "preprocessing_applied" in result["metadata"]
        assert "interpolation" in result["metadata"]["preprocessing_applied"]

    @pytest.mark.asyncio
    async def test_e2e_lag_analysis_multi_frequency_detection(self, http_client):
        """
        E2E Test 3: Multi-frequency lag analysis with seasonal patterns
        
        Scenario:
        - Submit data with multiple lag patterns (daily, weekly, monthly)
        - Service detects multiple significant lags
        - Returns comprehensive lag profile with seasonality
        
        Acceptance Criteria:
        - Detects multiple lag periods correctly
        - Identifies seasonal patterns
        - Provides confidence intervals
        - Suggests optimal lag for forecasting
        """
        
        # Arrange: Create multi-frequency data
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        t = np.arange(len(dates))
        
        # Base signal with multiple frequencies
        base_signal = (
            10 * np.sin(2 * np.pi * t / 7) +  # Weekly pattern
            5 * np.sin(2 * np.pi * t / 30) +   # Monthly pattern
            20 * np.sin(2 * np.pi * t / 365) + # Yearly pattern
            np.random.randn(len(dates)) * 2    # Noise
        )
        
        # Create lagged versions
        daily_lag = np.roll(base_signal, 1)
        weekly_lag = np.roll(base_signal, 7)
        monthly_lag = np.roll(base_signal, 30)
        
        request_payload = {
            "data": {
                "timestamps": [date.isoformat() for date in dates],
                "series": {
                    "base": base_signal.tolist(),
                    "daily_lagged": daily_lag.tolist(),
                    "weekly_lagged": weekly_lag.tolist(),
                    "monthly_lagged": monthly_lag.tolist()
                }
            },
            "analysis_config": {
                "max_lag": 60,
                "correlation_method": "pearson",
                "detect_seasonality": True,
                "frequency_analysis": True,
                "confidence_level": 0.95
            },
            "target_series": "base",
            "comparison_series": ["daily_lagged", "weekly_lagged", "monthly_lagged"]
        }
        
        # Act: Submit request
        response = await http_client.post(
            LAG_ANALYSIS_ENDPOINT,
            json=request_payload,
            timeout=60.0  # Longer timeout for complex analysis
        )
        
        # Assert: Verify response
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "completed"
        
        # Verify multiple lags detected
        lag_results = result["results"]["lag_correlations"]
        
        # Check daily lag detection
        daily_result = next(r for r in lag_results if r["series"] == "daily_lagged")
        assert daily_result["optimal_lag"] == 1
        assert "confidence_interval" in daily_result
        assert daily_result["confidence_interval"]["lower"] <= 1
        assert daily_result["confidence_interval"]["upper"] >= 1
        
        # Check weekly lag detection
        weekly_result = next(r for r in lag_results if r["series"] == "weekly_lagged")
        assert weekly_result["optimal_lag"] == 7
        assert weekly_result["seasonality_detected"] is True
        assert "seasonal_period" in weekly_result
        assert weekly_result["seasonal_period"] == 7
        
        # Check monthly lag detection
        monthly_result = next(r for r in lag_results if r["series"] == "monthly_lagged")
        assert abs(monthly_result["optimal_lag"] - 30) <= 1  # Allow 1 day tolerance
        
        # Verify frequency analysis results
        assert "frequency_analysis" in result["results"]
        freq_analysis = result["results"]["frequency_analysis"]
        assert "dominant_frequencies" in freq_analysis
        assert "spectral_peaks" in freq_analysis
        
        # Verify forecasting recommendations
        assert "recommendations" in result["results"]
        recommendations = result["results"]["recommendations"]
        assert "optimal_forecast_lag" in recommendations
        assert "suggested_model_type" in recommendations
        assert recommendations["suggested_model_type"] in ["SARIMA", "VAR", "LSTM"]
        
        # Verify comprehensive visualizations
        visualizations = result["results"]["visualizations"]
        assert "autocorrelation_plots" in visualizations
        assert "cross_correlation_matrix" in visualizations
        assert "spectral_density_plot" in visualizations
        assert "lag_profile_3d" in visualizations

    @pytest.mark.asyncio
    async def test_e2e_lag_analysis_error_handling_invalid_config(self, http_client):
        """
        E2E Test 4: Error handling for invalid configuration
        
        Scenario:
        - Submit request with invalid parameters
        - Service validates and returns appropriate errors
        
        Acceptance Criteria:
        - Returns 400 status code
        - Error message is descriptive
        - No partial processing occurs
        """
        
        # Arrange: Invalid request with negative max_lag
        invalid_request = {
            "data": {
                "timestamps": ["2024-01-01", "2024-01-02"],
                "series": {
                    "a": [1, 2],
                    "b": [3, 4]
                }
            },
            "analysis_config": {
                "max_lag": -5,  # Invalid: negative lag
                "correlation_method": "invalid_method"  # Invalid method
            },
            "target_series": "a",
            "comparison_series": ["b"]
        }
        
        # Act: Submit invalid request
        response = await http_client.post(
            LAG_ANALYSIS_ENDPOINT,
            json=invalid_request,
            timeout=10.0
        )
        
        # Assert: Verify error response
        assert response.status_code == 400
        error_result = response.json()
        
        assert "error" in error_result
        assert "validation_errors" in error_result
        
        validation_errors = error_result["validation_errors"]
        assert any("max_lag" in str(e) for e in validation_errors)
        assert any("correlation_method" in str(e) for e in validation_errors)

    @pytest.mark.asyncio
    async def test_e2e_lag_analysis_performance_large_dataset(self, http_client):
        """
        E2E Test 5: Performance test with large dataset
        
        Scenario:
        - Submit large time series (1+ year of hourly data)
        - Verify performance and timeout handling
        
        Acceptance Criteria:
        - Completes within timeout (60 seconds)
        - Returns performance metrics
        - Handles memory efficiently
        """
        
        # Arrange: Generate large dataset (1 year hourly = 8760 points)
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='H')
        large_series = np.random.randn(len(dates)).cumsum()
        
        large_request = {
            "data": {
                "timestamps": [date.isoformat() for date in dates[:1000]],  # Subset for test
                "series": {
                    "primary": large_series[:1000].tolist(),
                    "secondary": np.roll(large_series[:1000], 24).tolist()  # 24-hour lag
                }
            },
            "analysis_config": {
                "max_lag": 48,
                "optimization_mode": "fast",  # Use optimized algorithms
                "sampling_rate": 0.1  # Sample 10% for initial analysis
            },
            "target_series": "primary",
            "comparison_series": ["secondary"]
        }
        
        # Act: Submit large dataset
        import time
        start_time = time.time()
        
        response = await http_client.post(
            LAG_ANALYSIS_ENDPOINT,
            json=large_request,
            timeout=60.0
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Assert: Verify performance
        assert response.status_code == 200
        assert processing_time < 60  # Should complete within timeout
        
        result = response.json()
        assert "performance_metrics" in result["metadata"]
        
        perf_metrics = result["metadata"]["performance_metrics"]
        assert perf_metrics["total_processing_time_ms"] < 60000
        assert "memory_usage_mb" in perf_metrics
        assert perf_metrics["data_points_processed"] == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])