"""
Integration tests for Time-Series Forecasting Models Feature
Feature ID: FEATURE-CA-003-01
Tests verify that all layers work together correctly through feature_integration.py
"""

import pytest
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import asyncio
from typing import Dict, List, Any

# Import the layers (assuming these exist in the project structure)
from features.time_series_forecasting.layers.statistical_forecasting import StatisticalForecastingEngine
from features.time_series_forecasting.layers.ml_forecasting import MLForecastingEngine
from features.time_series_forecasting.layers.ensemble_orchestrator import EnsembleOrchestrator
from features.time_series_forecasting.layers.validation_backtesting import ValidationBacktesting
from features.time_series_forecasting.layers.forecast_api_integration import ForecastAPIIntegration
from features.time_series_forecasting.feature_integration import TimeSeriesForecastingFeature


class TestTimeSeriesForecastingIntegration:
    """Integration tests for Time-Series Forecasting Models"""

    @pytest.fixture
    def sample_time_series_data(self):
        """Generate sample time series data for testing"""
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        values = 100 + 10 * np.sin(np.arange(len(dates)) * 2 * np.pi / 365) + np.random.normal(0, 5, len(dates))
        return pd.DataFrame({
            'date': dates,
            'value': values,
            'feature_1': np.random.randn(len(dates)),
            'feature_2': np.random.randn(len(dates))
        })

    @pytest.fixture
    def forecasting_config(self):
        """Configuration for forecasting models"""
        return {
            'statistical': {
                'models': ['arima', 'exponential_smoothing', 'prophet'],
                'hyperparameters': {
                    'arima': {'order': (1, 1, 1)},
                    'exponential_smoothing': {'trend': 'add', 'seasonal': 'add'},
                    'prophet': {'yearly_seasonality': True}
                }
            },
            'ml': {
                'models': ['random_forest', 'xgboost', 'lstm'],
                'hyperparameters': {
                    'random_forest': {'n_estimators': 100, 'max_depth': 10},
                    'xgboost': {'n_estimators': 100, 'learning_rate': 0.1},
                    'lstm': {'units': 50, 'epochs': 10}
                }
            },
            'ensemble': {
                'method': 'weighted_average',
                'weights': {'statistical': 0.4, 'ml': 0.6}
            },
            'validation': {
                'metrics': ['mape', 'rmse', 'mae'],
                'backtesting_windows': 5,
                'test_size': 0.2
            }
        }

    @pytest.fixture
    def feature_instance(self, forecasting_config):
        """Create TimeSeriesForecastingFeature instance"""
        return TimeSeriesForecastingFeature(config=forecasting_config)

    @pytest.mark.asyncio
    async def test_end_to_end_forecasting_pipeline(self, feature_instance, sample_time_series_data):
        """
        Test complete forecasting pipeline from data input to API response
        Verifies: Data flows correctly through all layers
        """
        # Arrange
        forecast_request = {
            'data': sample_time_series_data.to_dict('records'),
            'target_column': 'value',
            'forecast_horizon': 30,
            'frequency': 'D',
            'include_confidence_intervals': True
        }

        # Mock external API calls if any
        with patch.object(ForecastAPIIntegration, 'external_api_call', return_value={'status': 'success'}):
            # Act
            result = await feature_instance.generate_forecast(forecast_request)

        # Assert
        assert result is not None
        assert 'forecast' in result
        assert 'confidence_intervals' in result
        assert 'model_performance' in result
        assert 'metadata' in result
        
        # Verify forecast structure
        forecast = result['forecast']
        assert len(forecast) == 30  # Forecast horizon
        assert all(key in forecast[0] for key in ['date', 'predicted_value'])
        
        # Verify confidence intervals
        ci = result['confidence_intervals']
        assert 'lower' in ci
        assert 'upper' in ci
        assert len(ci['lower']) == len(forecast)
        
        # Verify model performance metrics
        performance = result['model_performance']
        assert all(metric in performance for metric in ['mape', 'rmse', 'mae'])

    @pytest.mark.asyncio
    async def test_statistical_ml_ensemble_integration(self, feature_instance, sample_time_series_data):
        """
        Test integration between statistical, ML, and ensemble layers
        Verifies: Models are properly combined and weighted
        """
        # Arrange
        train_data = sample_time_series_data.iloc[:-60]
        test_data = sample_time_series_data.iloc[-60:]
        
        # Mock individual model predictions
        statistical_predictions = {
            'arima': np.random.randn(30) + 100,
            'exponential_smoothing': np.random.randn(30) + 102,
            'prophet': np.random.randn(30) + 98
        }
        
        ml_predictions = {
            'random_forest': np.random.randn(30) + 101,
            'xgboost': np.random.randn(30) + 99,
            'lstm': np.random.randn(30) + 100
        }

        with patch.object(StatisticalForecastingEngine, 'forecast', return_value=statistical_predictions):
            with patch.object(MLForecastingEngine, 'forecast', return_value=ml_predictions):
                # Act
                ensemble_result = await feature_instance.ensemble_orchestrator.combine_forecasts(
                    statistical_predictions=statistical_predictions,
                    ml_predictions=ml_predictions,
                    weights=feature_instance.config['ensemble']['weights']
                )

        # Assert
        assert ensemble_result is not None
        assert 'ensemble_forecast' in ensemble_result
        assert 'individual_forecasts' in ensemble_result
        assert 'weights_used' in ensemble_result
        
        # Verify ensemble calculation
        ensemble_forecast = ensemble_result['ensemble_forecast']
        assert len(ensemble_forecast) == 30
        assert all(isinstance(val, (int, float)) for val in ensemble_forecast)

    @pytest.mark.asyncio
    async def test_validation_backtesting_integration(self, feature_instance, sample_time_series_data):
        """
        Test validation and backtesting across different model types
        Verifies: Performance metrics are correctly calculated and compared
        """
        # Arrange
        backtesting_config = {
            'n_splits': 5,
            'test_size': 30,
            'step_size': 10
        }
        
        model_forecasts = {
            'arima': np.random.randn(150) + 100,
            'random_forest': np.random.randn(150) + 99,
            'ensemble': np.random.randn(150) + 100.5
        }
        
        actual_values = sample_time_series_data['value'].iloc[-150:].values

        # Act
        validation_results = await feature_instance.validation_backtesting.run_backtesting(
            historical_data=sample_time_series_data,
            model_forecasts=model_forecasts,
            config=backtesting_config
        )

        # Assert
        assert validation_results is not None
        assert 'model_metrics' in validation_results
        assert 'backtesting_results' in validation_results
        assert 'best_model' in validation_results
        
        # Verify metrics for each model
        model_metrics = validation_results['model_metrics']
        for model_name in ['arima', 'random_forest', 'ensemble']:
            assert model_name in model_metrics
            assert all(metric in model_metrics[model_name] for metric in ['mape', 'rmse', 'mae'])
            
        # Verify backtesting results structure
        backtesting = validation_results['backtesting_results']
        assert len(backtesting) == 5  # Number of splits
        assert all('window_start' in result and 'window_end' in result for result in backtesting)

    @pytest.mark.asyncio
    async def test_error_handling_across_layers(self, feature_instance):
        """
        Test error handling and propagation across layer boundaries
        Verifies: Errors are properly caught and handled at each layer
        """
        # Test 1: Invalid data input
        invalid_request = {
            'data': None,  # Invalid data
            'target_column': 'value',
            'forecast_horizon': 30
        }
        
        with pytest.raises(ValueError, match="Invalid data provided"):
            await feature_instance.generate_forecast(invalid_request)
        
        # Test 2: Statistical engine failure
        valid_data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=10),
            'value': [np.nan] * 10  # All NaN values
        })
        
        with patch.object(StatisticalForecastingEngine, 'forecast', side_effect=Exception("Statistical model failed")):
            result = await feature_instance.generate_forecast({
                'data': valid_data.to_dict('records'),
                'target_column': 'value',
                'forecast_horizon': 5,
                'fallback_on_error': True
            })
            
            # Should fallback to ML models only
            assert result is not None
            assert 'error_log' in result
            assert 'Statistical model failed' in result['error_log']
        
        # Test 3: Complete model failure
        with patch.object(StatisticalForecastingEngine, 'forecast', side_effect=Exception("Statistical failed")):
            with patch.object(MLForecastingEngine, 'forecast', side_effect=Exception("ML failed")):
                with pytest.raises(RuntimeError, match="All forecasting models failed"):
                    await feature_instance.generate_forecast({
                        'data': valid_data.to_dict('records'),
                        'target_column': 'value',
                        'forecast_horizon': 5,
                        'fallback_on_error': False
                    })

    @pytest.mark.asyncio
    async def test_api_integration_with_caching(self, feature_instance, sample_time_series_data):
        """
        Test API integration layer with caching and rate limiting
        Verifies: API responses are cached and rate limits are respected
        """
        # Arrange
        api_request = {
            'endpoint': '/forecast',
            'method': 'POST',
            'data': {
                'series_data': sample_time_series_data.to_dict('records'),
                'options': {
                    'use_cache': True,
                    'cache_ttl': 3600,
                    'api_key': 'test_key'
                }
            }
        }
        
        # Mock the forecast generation
        mock_forecast = {
            'forecast': [{'date': '2024-01-01', 'value': 105.2}],
            'model_used': 'ensemble',
            'cached': False
        }
        
        with patch.object(feature_instance, 'generate_forecast', return_value=mock_forecast):
            # First call - should hit the actual service
            result1 = await feature_instance.api_integration.handle_request(api_request)
            
            # Second call - should use cache
            result2 = await feature_instance.api_integration.handle_request(api_request)
        
        # Assert
        assert result1 is not None
        assert result2 is not None
        assert result1['cached'] is False
        assert result2['cached'] is True
        assert result1['forecast'] == result2['forecast']
        
        # Test rate limiting
        with patch.object(feature_instance.api_integration, 'check_rate_limit', return_value=False):
            with pytest.raises(Exception, match="Rate limit exceeded"):
                await feature_instance.api_integration.handle_request(api_request)

    @pytest.mark.asyncio
    async def test_model_selection_based_on_data_characteristics(self, feature_instance):
        """
        Test dynamic model selection based on data characteristics
        Verifies: Appropriate models are selected for different data patterns
        """
        # Test 1: Seasonal data - should prefer seasonal models
        seasonal_data = pd.DataFrame({
            'date': pd.date_range('2022-01-01', periods=730, freq='D'),
            'value': 100 + 20 * np.sin(np.arange(730) * 2 * np.pi / 365) + np.random.normal(0, 2, 730)
        })
        
        result_seasonal = await feature_instance.analyze_and_forecast(
            data=seasonal_data,
            target_column='value',
            auto_select_models=True
        )
        
        assert 'selected_models' in result_seasonal
        assert 'prophet' in result_seasonal['selected_models'] or 'exponential_smoothing' in result_seasonal['selected_models']
        assert 'data_characteristics' in result_seasonal
        assert result_seasonal['data_characteristics']['has_seasonality'] is True
        
        # Test 2: Trending data - should prefer trend-capable models
        trend_data = pd.DataFrame({
            'date': pd.date_range('2022-01-01', periods=365, freq='D'),
            'value': 100 + np.arange(365) * 0.5 + np.random.normal(0, 5, 365)
        })
        
        result_trend = await feature_instance.analyze_and_forecast(
            data=trend_data,
            target_column='value',
            auto_select_models=True
        )
        
        assert result_trend['data_characteristics']['has_trend'] is True
        assert any(model in result_trend['selected_models'] for model in ['arima', 'xgboost'])
        
        # Test 3: Short time series - should avoid complex models
        short_data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=30, freq='D'),
            'value': np.random.normal(100, 10, 30)
        })
        
        result_short = await feature_instance.analyze_and_forecast(
            data=short_data,
            target_column='value',
            auto_select_models=True
        )
        
        assert 'lstm' not in result_short['selected_models']  # LSTM needs more data
        assert len(result_short['warnings']) > 0
        assert any('short time series' in warning.lower() for warning in result_short['warnings'])


class TestTimeSeriesForecastingPerformance:
    """Performance-related integration tests"""
    
    @pytest.mark.asyncio
    async def test_concurrent_forecast_requests(self, feature_instance, sample_time_series_data):
        """
        Test handling of multiple concurrent forecast requests
        Verifies: System can handle parallel processing efficiently
        """
        # Create multiple forecast requests with different parameters
        requests = [
            {
                'data': sample_time_series_data.to_dict('records'),
                'target_column': 'value',
                'forecast_horizon': horizon,
                'request_id': f'req_{i}'
            }
            for i, horizon in enumerate([10, 20, 30, 40, 50])
        ]
        
        # Execute requests concurrently
        start_time = datetime.now()
        tasks = [feature_instance.generate_forecast(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = datetime.now()
        
        # Assert
        assert len(results) == 5
        assert all(not isinstance(r, Exception) for r in results)
        assert all('forecast' in r for r in results)
        
        # Verify different forecast horizons
        for i, (result, request) in enumerate(zip(results, requests)):
            assert len(result['forecast']) == request['forecast_horizon']
            assert result['metadata']['request_id'] == request['request_id']
        
        # Performance check (should complete within reasonable time)
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 30  # Should complete within 30 seconds

    @pytest.mark.asyncio
    async def test_large_dataset_handling(self, feature_instance):
        """
        Test system behavior with large datasets
        Verifies: Memory efficiency and processing optimization
        """
        # Generate large dataset (5 years of hourly data)
        large_data = pd.DataFrame({
            'date': pd.date_range('2019-01-01', periods=43800, freq='H'),
            'value': 100 + np.random.normal(0, 10, 43800),
            'feature_1': np.random.randn(43800),
            'feature_2': np.random.randn(43800)
        })
        
        with patch.object(feature_instance, 'optimize_for_large_data', return_value=True):
            result = await feature_instance.generate_forecast({
                'data': large_data.to_dict('records'),
                'target_column': 'value',
                'forecast_horizon': 168,  # One week hourly forecast
                'optimization': {
                    'chunk_size': 10000,
                    'parallel_processing': True,
                    'memory_limit_mb': 1024
                }
            })
        
        # Assert
        assert result is not None
        assert 'performance_stats' in result
        assert result['performance_stats']['data_points_processed'] == 43800
        assert result['performance_stats']['optimization_applied'] is True
        assert 'memory_usage_mb' in result['performance_stats']
        assert result['performance_stats']['memory_usage_mb'] < 1024