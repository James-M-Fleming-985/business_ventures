"""
Integration tests for Granger Causality API Service
Feature ID: FEATURE-CA-002-06
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
import json
from typing import Dict, List, Any

# Assuming these are the layers/modules to integrate
from feature_integration import (
    GrangerCausalityService,
    DataPreprocessor,
    TimeSeriesValidator,
    GrangerAnalyzer,
    ResultsFormatter,
    APIHandler,
    CacheManager,
    MetricsCollector
)


class TestGrangerCausalityIntegration:
    """Integration tests for Granger Causality API Service"""

    @pytest.fixture
    def sample_time_series_data(self):
        """Generate sample time series data for testing"""
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        # Create two time series where series2 is influenced by series1
        series1 = np.random.randn(100).cumsum()
        series2 = np.zeros(100)
        for i in range(2, 100):
            series2[i] = 0.7 * series1[i-1] + 0.3 * series1[i-2] + np.random.randn() * 0.5
        
        return {
            'timestamps': dates.tolist(),
            'series1': series1.tolist(),
            'series2': series2.tolist()
        }

    @pytest.fixture
    def invalid_time_series_data(self):
        """Generate invalid time series data for error testing"""
        return {
            'timestamps': pd.date_range(start='2023-01-01', periods=10, freq='D').tolist(),
            'series1': [1, 2, None, 4, 5, 6, 7, 8, 9, 10],  # Contains None
            'series2': [1, 2, 3, 4, 5]  # Mismatched length
        }

    @pytest.fixture
    def granger_service(self):
        """Initialize the Granger Causality Service with all dependencies"""
        preprocessor = DataPreprocessor()
        validator = TimeSeriesValidator()
        analyzer = GrangerAnalyzer()
        formatter = ResultsFormatter()
        cache_manager = CacheManager(ttl_seconds=300)
        metrics_collector = MetricsCollector()
        
        service = GrangerCausalityService(
            preprocessor=preprocessor,
            validator=validator,
            analyzer=analyzer,
            formatter=formatter,
            cache_manager=cache_manager,
            metrics_collector=metrics_collector
        )
        
        return service

    @pytest.fixture
    def api_handler(self, granger_service):
        """Initialize API handler with the service"""
        return APIHandler(granger_service)

    @pytest.mark.asyncio
    async def test_full_pipeline_successful_analysis(self, granger_service, sample_time_series_data):
        """
        Test 1: Verify successful end-to-end Granger causality analysis
        
        Integration scenario: Data ingestion → Validation → Preprocessing → 
                            Analysis → Formatting → Result delivery
        """
        # Arrange
        request_data = {
            'data': sample_time_series_data,
            'max_lag': 5,
            'significance_level': 0.05,
            'test_type': 'ssr_ftest'
        }
        
        # Act
        result = await granger_service.analyze(request_data)
        
        # Assert
        assert result is not None
        assert 'analysis_id' in result
        assert 'results' in result
        assert 'metadata' in result
        
        # Verify results structure
        assert 'p_value' in result['results']
        assert 'test_statistic' in result['results']
        assert 'granger_causality_detected' in result['results']
        assert 'optimal_lag' in result['results']
        
        # Verify metadata
        assert result['metadata']['status'] == 'completed'
        assert result['metadata']['series_length'] == 100
        assert result['metadata']['max_lag_tested'] == 5
        
        # Verify the causal relationship is detected (based on synthetic data)
        assert result['results']['granger_causality_detected'] is True
        assert result['results']['p_value'] < 0.05

    @pytest.mark.asyncio
    async def test_caching_integration(self, granger_service, sample_time_series_data):
        """
        Test 2: Verify caching mechanism works across layers
        
        Integration scenario: First request → Cache miss → Full analysis → Store in cache
                            Second request → Cache hit → Return cached result
        """
        # Arrange
        request_data = {
            'data': sample_time_series_data,
            'max_lag': 3,
            'significance_level': 0.05,
            'test_type': 'ssr_ftest'
        }
        
        # Act - First request
        start_time1 = datetime.now()
        result1 = await granger_service.analyze(request_data)
        execution_time1 = (datetime.now() - start_time1).total_seconds()
        
        # Act - Second request (should hit cache)
        start_time2 = datetime.now()
        result2 = await granger_service.analyze(request_data)
        execution_time2 = (datetime.now() - start_time2).total_seconds()
        
        # Assert
        assert result1 == result2  # Results should be identical
        assert execution_time2 < execution_time1 * 0.1  # Cached request should be much faster
        
        # Verify cache metrics
        cache_stats = granger_service.cache_manager.get_stats()
        assert cache_stats['hits'] >= 1
        assert cache_stats['misses'] >= 1
        assert cache_stats['hit_rate'] > 0

    @pytest.mark.asyncio
    async def test_error_handling_across_layers(self, granger_service, invalid_time_series_data):
        """
        Test 3: Verify error handling and propagation across all layers
        
        Integration scenario: Invalid data → Validation error → Error formatting → 
                            Proper error response
        """
        # Arrange
        request_data = {
            'data': invalid_time_series_data,
            'max_lag': 5,
            'significance_level': 0.05,
            'test_type': 'ssr_ftest'
        }
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await granger_service.analyze(request_data)
        
        # Verify error contains helpful information
        error_message = str(exc_info.value)
        assert any(keyword in error_message.lower() for keyword in ['length', 'mismatch', 'invalid'])
        
        # Verify metrics recorded the error
        metrics = granger_service.metrics_collector.get_metrics()
        assert metrics['total_errors'] > 0
        assert 'validation_error' in metrics['error_types']

    @pytest.mark.asyncio
    async def test_concurrent_requests_handling(self, granger_service, sample_time_series_data):
        """
        Test 4: Verify service handles concurrent requests correctly
        
        Integration scenario: Multiple concurrent requests → Proper isolation → 
                            All requests completed successfully
        """
        # Arrange
        num_concurrent_requests = 10
        requests = []
        
        for i in range(num_concurrent_requests):
            # Slightly modify data for each request to avoid cache hits
            modified_data = sample_time_series_data.copy()
            modified_data['series1'] = [x + i * 0.01 for x in modified_data['series1']]
            
            request = {
                'data': modified_data,
                'max_lag': 4,
                'significance_level': 0.05,
                'test_type': 'ssr_ftest',
                'request_id': f'concurrent_test_{i}'
            }
            requests.append(request)
        
        # Act
        tasks = [granger_service.analyze(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Assert
        assert len(results) == num_concurrent_requests
        
        # Verify all requests completed successfully
        for i, result in enumerate(results):
            assert not isinstance(result, Exception), f"Request {i} failed: {result}"
            assert result['metadata']['status'] == 'completed'
            assert 'analysis_id' in result
            
        # Verify each result is unique (no cross-contamination)
        analysis_ids = [r['analysis_id'] for r in results]
        assert len(set(analysis_ids)) == num_concurrent_requests

    @pytest.mark.asyncio
    async def test_api_to_service_integration(self, api_handler, sample_time_series_data):
        """
        Test 5: Verify API handler properly integrates with the service layer
        
        Integration scenario: HTTP request → API validation → Service processing → 
                            HTTP response formatting
        """
        # Arrange
        api_request = {
            'method': 'POST',
            'path': '/api/v1/granger-causality',
            'headers': {
                'Content-Type': 'application/json',
                'X-Request-ID': 'test-request-123'
            },
            'body': json.dumps({
                'data': sample_time_series_data,
                'config': {
                    'max_lag': 5,
                    'significance_level': 0.05,
                    'test_type': 'ssr_ftest'
                },
                'options': {
                    'include_diagnostics': True,
                    'format': 'detailed'
                }
            })
        }
        
        # Act
        response = await api_handler.handle_request(api_request)
        
        # Assert
        assert response['status_code'] == 200
        assert 'application/json' in response['headers']['Content-Type']
        
        response_body = json.loads(response['body'])
        assert response_body['success'] is True
        assert 'data' in response_body
        assert 'request_id' in response_body
        assert response_body['request_id'] == 'test-request-123'
        
        # Verify detailed format includes diagnostics
        assert 'diagnostics' in response_body['data']
        assert 'processing_time_ms' in response_body['data']['diagnostics']
        assert 'cache_hit' in response_body['data']['diagnostics']

    @pytest.mark.asyncio
    async def test_metrics_collection_integration(self, granger_service, sample_time_series_data):
        """
        Test 6: Verify metrics are properly collected across all operations
        
        Integration scenario: Multiple operations → Metrics collection → 
                            Aggregated metrics retrieval
        """
        # Arrange
        initial_metrics = granger_service.metrics_collector.get_metrics()
        
        # Act - Perform various operations
        # Successful analysis
        await granger_service.analyze({
            'data': sample_time_series_data,
            'max_lag': 3,
            'significance_level': 0.05,
            'test_type': 'ssr_ftest'
        })
        
        # Failed analysis (invalid data)
        try:
            await granger_service.analyze({
                'data': {'timestamps': [], 'series1': [], 'series2': []},
                'max_lag': 3,
                'significance_level': 0.05,
                'test_type': 'ssr_ftest'
            })
        except:
            pass  # Expected to fail
        
        # Act - Get updated metrics
        final_metrics = granger_service.metrics_collector.get_metrics()
        
        # Assert
        assert final_metrics['total_requests'] > initial_metrics['total_requests']
        assert final_metrics['successful_analyses'] >= initial_metrics['successful_analyses'] + 1
        assert final_metrics['total_errors'] >= initial_metrics['total_errors'] + 1
        
        # Verify performance metrics
        assert 'average_processing_time' in final_metrics
        assert 'p95_processing_time' in final_metrics
        assert final_metrics['average_processing_time'] > 0

    @pytest.mark.asyncio
    async def test_data_preprocessing_integration(self, granger_service):
        """
        Test 7: Verify data preprocessing handles various data quality issues
        
        Integration scenario: Raw data → Validation → Preprocessing (interpolation, 
                            outlier handling) → Clean data → Analysis
        """
        # Arrange - Create data with quality issues
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        series1_with_issues = list(range(50))
        series1_with_issues[10] = None  # Missing value
        series1_with_issues[20] = 1000   # Outlier
        
        series2_with_issues = list(range(50))
        series2_with_issues[15] = None  # Missing value
        series2_with_issues[25] = -1000  # Outlier
        
        request_data = {
            'data': {
                'timestamps': dates.tolist(),
                'series1': series1_with_issues,
                'series2': series2_with_issues
            },
            'max_lag': 3,
            'significance_level': 0.05,
            'test_type': 'ssr_ftest',
            'preprocessing_options': {
                'handle_missing': 'interpolate',
                'handle_outliers': 'clip',
                'detrend': True
            }
        }
        
        # Act
        result = await granger_service.analyze(request_data)
        
        # Assert
        assert result['metadata']['status'] == 'completed'
        assert result['metadata']['preprocessing_applied'] is True
        assert 'missing_values_handled' in result['metadata']['preprocessing_details']
        assert 'outliers_handled' in result['metadata']['preprocessing_details']
        assert result['metadata']['preprocessing_details']['missing_values_handled'] == 2
        assert result['metadata']['preprocessing_details']['outliers_handled'] == 2


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Cleanup fixture
@pytest.fixture(autouse=True)
async def cleanup(granger_service):
    """Cleanup after each test"""
    yield
    # Clear cache
    await granger_service.cache_manager.clear()
    # Reset metrics
    granger_service.metrics_collector.reset()