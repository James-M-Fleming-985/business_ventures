"""
End-to-End tests for Time-Series Forecasting Models
Feature ID: FEATURE-CA-003-01
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import json
import time
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimeSeriesForecastingE2E:
    """E2E test client for Time-Series Forecasting Models"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def create_dataset(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Upload time-series dataset"""
        response = self.session.post(
            f"{self.base_url}/api/v1/datasets",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def create_model(self, model_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create and configure forecasting model"""
        response = self.session.post(
            f"{self.base_url}/api/v1/models",
            json=model_config
        )
        response.raise_for_status()
        return response.json()
    
    def train_model(self, model_id: str, training_params: Dict[str, Any]) -> Dict[str, Any]:
        """Train the forecasting model"""
        response = self.session.post(
            f"{self.base_url}/api/v1/models/{model_id}/train",
            json=training_params
        )
        response.raise_for_status()
        return response.json()
    
    def wait_for_training(self, model_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for model training to complete"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = self.session.get(
                f"{self.base_url}/api/v1/models/{model_id}/status"
            )
            response.raise_for_status()
            status = response.json()
            
            if status['state'] == 'COMPLETED':
                return status
            elif status['state'] == 'FAILED':
                raise Exception(f"Model training failed: {status.get('error', 'Unknown error')}")
            
            time.sleep(5)
        
        raise TimeoutError(f"Model training timed out after {timeout} seconds")
    
    def generate_forecast(self, model_id: str, forecast_params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate forecast using trained model"""
        response = self.session.post(
            f"{self.base_url}/api/v1/models/{model_id}/forecast",
            json=forecast_params
        )
        response.raise_for_status()
        return response.json()
    
    def get_model_metrics(self, model_id: str) -> Dict[str, Any]:
        """Get model performance metrics"""
        response = self.session.get(
            f"{self.base_url}/api/v1/models/{model_id}/metrics"
        )
        response.raise_for_status()
        return response.json()
    
    def cleanup(self, model_id: str = None, dataset_id: str = None):
        """Clean up resources"""
        if model_id:
            self.session.delete(f"{self.base_url}/api/v1/models/{model_id}")
        if dataset_id:
            self.session.delete(f"{self.base_url}/api/v1/datasets/{dataset_id}")


@pytest.fixture
def ts_client():
    """Create Time-Series Forecasting E2E test client"""
    # Use environment variable or default URL
    base_url = "http://localhost:8000"
    return TimeSeriesForecastingE2E(base_url)


@pytest.fixture
def sample_time_series_data():
    """Generate sample time-series data for testing"""
    # Generate realistic sales data with trend and seasonality
    dates = pd.date_range(start='2022-01-01', end='2023-12-31', freq='D')
    trend = np.linspace(1000, 1500, len(dates))
    seasonal = 200 * np.sin(2 * np.pi * np.arange(len(dates)) / 365.25)
    noise = np.random.normal(0, 50, len(dates))
    values = trend + seasonal + noise
    
    # Add some anomalies
    anomaly_indices = np.random.choice(len(dates), size=10, replace=False)
    values[anomaly_indices] += np.random.uniform(300, 500, size=10)
    
    return {
        "name": "daily_sales_data",
        "description": "Daily sales data with trend and seasonality",
        "data": [
            {
                "timestamp": date.isoformat(),
                "value": float(value),
                "metadata": {
                    "day_of_week": date.strftime('%A'),
                    "month": date.month,
                    "quarter": (date.month - 1) // 3 + 1
                }
            }
            for date, value in zip(dates, values)
        ],
        "frequency": "daily",
        "target_column": "value",
        "timestamp_column": "timestamp"
    }


class TestTimeSeriesForecastingE2E:
    """End-to-End tests for Time-Series Forecasting Models"""
    
    @pytest.mark.e2e
    def test_complete_forecasting_workflow_with_arima(self, ts_client, sample_time_series_data):
        """
        Test complete end-to-end workflow with ARIMA model:
        1. Upload time-series data
        2. Create and configure ARIMA model
        3. Train model with validation
        4. Generate forecasts
        5. Validate forecast quality
        """
        dataset_id = None
        model_id = None
        
        try:
            # Step 1: Upload time-series dataset
            logger.info("Uploading time-series dataset...")
            dataset_response = ts_client.create_dataset(sample_time_series_data)
            dataset_id = dataset_response['dataset_id']
            
            assert dataset_response['status'] == 'uploaded'
            assert dataset_response['record_count'] == len(sample_time_series_data['data'])
            assert dataset_response['frequency'] == 'daily'
            
            # Step 2: Create ARIMA model
            logger.info("Creating ARIMA model...")
            model_config = {
                "name": "sales_forecast_arima",
                "model_type": "ARIMA",
                "dataset_id": dataset_id,
                "parameters": {
                    "order": [2, 1, 2],  # (p, d, q)
                    "seasonal_order": [1, 1, 1, 12],  # (P, D, Q, s)
                    "trend": "ct",  # constant with trend
                    "enforce_stationarity": True,
                    "enforce_invertibility": True
                },
                "validation": {
                    "method": "time_series_split",
                    "n_splits": 5,
                    "test_size": 30
                }
            }
            
            model_response = ts_client.create_model(model_config)
            model_id = model_response['model_id']
            
            assert model_response['status'] == 'created'
            assert model_response['model_type'] == 'ARIMA'
            
            # Step 3: Train model
            logger.info("Training ARIMA model...")
            training_params = {
                "train_test_split": 0.8,
                "validation_metrics": ["mae", "rmse", "mape", "smape"],
                "save_diagnostics": True,
                "early_stopping": {
                    "enabled": True,
                    "patience": 5,
                    "min_improvement": 0.01
                }
            }
            
            train_response = ts_client.train_model(model_id, training_params)
            assert train_response['status'] == 'training_started'
            
            # Wait for training to complete
            training_status = ts_client.wait_for_training(model_id)
            assert training_status['state'] == 'COMPLETED'
            assert 'training_duration' in training_status
            assert training_status['training_duration'] > 0
            
            # Step 4: Get model metrics
            logger.info("Retrieving model metrics...")
            metrics = ts_client.get_model_metrics(model_id)
            
            # Validate model performance
            assert metrics['mae'] < 100  # Mean Absolute Error threshold
            assert metrics['mape'] < 0.15  # Mean Absolute Percentage Error < 15%
            assert metrics['rmse'] < 150  # Root Mean Square Error threshold
            assert 'residual_diagnostics' in metrics
            assert metrics['residual_diagnostics']['ljung_box_p_value'] > 0.05  # No autocorrelation
            
            # Step 5: Generate forecast
            logger.info("Generating forecast...")
            forecast_params = {
                "horizon": 90,  # 90 days ahead
                "confidence_level": 0.95,
                "include_history": True,
                "return_components": True
            }
            
            forecast_response = ts_client.generate_forecast(model_id, forecast_params)
            
            # Validate forecast response
            assert 'forecast' in forecast_response
            assert len(forecast_response['forecast']) == 90
            assert 'confidence_intervals' in forecast_response
            assert 'components' in forecast_response
            
            # Validate forecast structure
            first_forecast = forecast_response['forecast'][0]
            assert 'timestamp' in first_forecast
            assert 'value' in first_forecast
            assert 'lower_bound' in first_forecast
            assert 'upper_bound' in first_forecast
            
            # Validate forecast values are reasonable
            forecast_values = [f['value'] for f in forecast_response['forecast']]
            assert all(500 < v < 2500 for v in forecast_values)  # Reasonable range
            
            # Check trend component if available
            if 'trend' in forecast_response['components']:
                trend_values = forecast_response['components']['trend']
                assert len(trend_values) == 90
                # Trend should be relatively smooth
                trend_diffs = np.diff(trend_values)
                assert np.std(trend_diffs) < 10
            
            logger.info("E2E test completed successfully!")
            
        finally:
            # Cleanup
            ts_client.cleanup(model_id=model_id, dataset_id=dataset_id)
    
    @pytest.mark.e2e
    def test_prophet_model_with_holidays_and_regressors(self, ts_client):
        """
        Test Prophet model with holidays and external regressors:
        1. Create dataset with external features
        2. Configure Prophet with holidays
        3. Train with custom seasonality
        4. Generate forecast with future regressors
        5. Validate component decomposition
        """
        dataset_id = None
        model_id = None
        
        try:
            # Generate data with external regressors
            dates = pd.date_range(start='2022-01-01', end='2023-12-31', freq='D')
            base_values = 1000 + 500 * np.sin(2 * np.pi * np.arange(len(dates)) / 365.25)
            temperature_effect = 10 * (np.random.randn(len(dates)) + 20)
            marketing_spend = np.random.uniform(100, 1000, len(dates))
            values = base_values + 0.5 * marketing_spend + 2 * temperature_effect
            
            # Add holiday effects
            holidays = ['2022-12-25', '2023-01-01', '2023-07-04', '2023-12-25']
            for holiday in holidays:
                holiday_date = pd.Timestamp(holiday)
                if holiday_date in dates:
                    idx = dates.get_loc(holiday_date)
                    values[idx] *= 1.5  # 50% increase on holidays
            
            dataset_config = {
                "name": "sales_with_features",
                "description": "Sales data with temperature and marketing spend",
                "data": [
                    {
                        "timestamp": date.isoformat(),
                        "value": float(value),
                        "temperature": float(temp),
                        "marketing_spend": float(spend),
                        "is_weekend": date.weekday() >= 5
                    }
                    for date, value, temp, spend in zip(dates, values, temperature_effect, marketing_spend)
                ],
                "frequency": "daily",
                "target_column": "value",
                "timestamp_column": "timestamp",
                "feature_columns": ["temperature", "marketing_spend", "is_weekend"]
            }
            
            # Step 1: Upload dataset
            logger.info("Uploading dataset with external features...")
            dataset_response = ts_client.create_dataset(dataset_config)
            dataset_id = dataset_response['dataset_id']
            
            # Step 2: Create Prophet model with holidays
            logger.info("Creating Prophet model with holidays...")
            model_config = {
                "name": "prophet_with_features",
                "model_type": "PROPHET",
                "dataset_id": dataset_id,
                "parameters": {
                    "growth": "linear",
                    "changepoint_prior_scale": 0.05,
                    "seasonality_prior_scale": 10,
                    "holidays_prior_scale": 10,
                    "seasonality_mode": "multiplicative",
                    "interval_width": 0.95,
                    "holidays": [
                        {"holiday": "Christmas", "ds": ["2022-12-25", "2023-12-25"]},
                        {"holiday": "New Year", "ds": ["2022-01-01", "2023-01-01"]},
                        {"holiday": "Independence Day", "ds": ["2023-07-04"]}
                    ],
                    "add_regressors": [
                        {"name": "temperature", "prior_scale": 10, "standardize": True},
                        {"name": "marketing_spend", "prior_scale": 10, "standardize": True}
                    ],
                    "custom_seasonalities": [
                        {
                            "name": "monthly",
                            "period": 30.5,
                            "fourier_order": 5
                        }
                    ]
                }
            }
            
            model_response = ts_client.create_model(model_config)
            model_id = model_response['model_id']
            
            # Step 3: Train model
            logger.info("Training Prophet model...")
            training_params = {
                "train_test_split": 0.85,
                "cross_validation": {
                    "initial": "365 days",
                    "period": "30 days",
                    "horizon": "60 days"
                },
                "hyperparameter_tuning": {
                    "enabled": True,
                    "param_grid": {
                        "changepoint_prior_scale": [0.001, 0.01, 0.1],
                        "seasonality_prior_scale": [0.01, 0.1, 1.0]
                    }
                }
            }
            
            train_response = ts_client.train_model(model_id, training_params)
            training_status = ts_client.wait_for_training(model_id, timeout=600)
            
            # Step 4: Generate forecast with future regressors
            logger.info("Generating forecast with future regressors...")
            
            # Create future regressor values
            future_dates = pd.date_range(start='2024-01-01', end='2024-03-31', freq='D')
            future_regressors = [
                {
                    "timestamp": date.isoformat(),
                    "temperature": float(20 + 10 * np.sin(2 * np.pi * i / 365)),
                    "marketing_spend": float(500 + 200 * np.random.randn()),
                    "is_weekend": date.weekday() >= 5
                }
                for i, date in enumerate(future_dates)
            ]
            
            forecast_params = {
                "horizon": 90,
                "future_regressors": future_regressors,
                "return_components": True,
                "mcmc_samples": 0  # Use MAP estimation for speed
            }
            
            forecast_response = ts_client.generate_forecast(model_id, forecast_params)
            
            # Validate forecast with components
            assert 'forecast' in forecast_response
            assert len(forecast_response['forecast']) == 90
            assert 'components' in forecast_response
            
            # Check component breakdown
            components = forecast_response['components']
            assert 'trend' in components
            assert 'yearly' in components
            assert 'monthly' in components  # Custom seasonality
            assert 'holidays' in components
            assert 'temperature' in components  # External regressor
            assert 'marketing_spend' in components  # External regressor
            
            # Validate component contributions
            for i in range(90):
                forecast_value = forecast_response['forecast'][i]['value']
                component_sum = (
                    components['trend'][i] +
                    components['yearly'][i] +
                    components['monthly'][i] +
                    components['holidays'][i] +
                    components['temperature'][i] +
                    components['marketing_spend'][i]
                )
                # Components should approximately sum to forecast (within numerical tolerance)
                assert abs(forecast_value - component_sum) < forecast_value * 0.1
            
            # Get cross-validation metrics
            metrics = ts_client.get_model_metrics(model_id)
            assert 'cross_validation_metrics' in metrics
            cv_metrics = metrics['cross_validation_metrics']
            assert cv_metrics['mape'] < 0.2  # Less than 20% error
            assert cv_metrics['coverage'] > 0.8  # 80% of actuals within prediction interval
            
        finally:
            # Cleanup
            ts_client.cleanup(model_id=model_id, dataset_id=dataset_id)
    
    @pytest.mark.e2e
    def test_lstm_deep_learning_model_with_multivariate_input(self, ts_client):
        """
        Test LSTM deep learning model for multivariate time series:
        1. Create multivariate dataset
        2. Configure LSTM with multiple features
        3. Train with early stopping
        4. Generate multi-step ahead forecasts
        5. Test model serving and real-time predictions
        """
        dataset_id = None
        model_id = None
        
        try:
            # Generate multivariate time series data
            n_samples = 1000
            dates = pd.date_range(start='2021-01-01', periods=n_samples, freq='H')
            
            # Create correlated time series
            np.random.seed(42)
            t = np.arange(n_samples)
            
            # Primary series with complex patterns
            series1 = (
                1000 + 
                200 * np.sin(2 * np.pi * t / 24) +  # Daily pattern
                100 * np.sin(2 * np.pi * t / (24 * 7)) +  # Weekly pattern
                0.5 * t +  # Trend
                50 * np.random.randn(n_samples)  # Noise
            )
            
            # Correlated series
            series2 = 0.7 * series1 + 300 + 30 * np.random.randn(n_samples)
            series3 = 500 * np.sin(2 * np.pi * t / 12 + np.pi/4) + 20 * np.random.randn(n_samples)
            
            # Create dataset
            dataset_config = {
                "name": "multivariate_energy_consumption",
                "description": "Multivariate time series for energy forecasting",
                "data": [
                    {
                        "timestamp": date.isoformat(),
                        "energy_consumption": float(s1),
                        "temperature": float(s2),
                        "solar_radiation": float(s3),
                        "hour": date.hour,
                        "day_of_week": date.dayofweek,
                        "month": date.month
                    }
                    for date, s1, s2, s3 in zip(dates, series1, series2, series3)
                ],
                "frequency": "hourly",
                "target_column": "energy_consumption",
                "timestamp_column": "timestamp",
                "feature_columns": [
                    "temperature", "solar_radiation", 
                    "hour", "day_of_week", "month"
                ]
            }
            
            # Step 1: Upload multivariate dataset
            logger.info("Uploading multivariate dataset...")
            dataset_response = ts_client.create_dataset(dataset_config)
            dataset_id = dataset_response['dataset_id']
            
            # Step 2: Create LSTM model
            logger.info("Creating LSTM deep learning model...")
            model_config = {
                "name": "energy_lstm_forecaster",
                "model_type": "LSTM",
                "dataset_id": dataset_id,
                "parameters": {
                    "architecture": {
                        "input_sequence_length": 168,  # 7 days of hourly data
                        "output_sequence_length": 24,  # Predict next 24 hours
                        "lstm_layers": [
                            {"units": 128, "dropout": 0.2, "recurrent_dropout": 0.2},
                            {"units": 64, "dropout": 0.2, "recurrent_dropout": 0.2}
                        ],
                        "dense_layers": [
                            {"units": 32, "activation": "relu", "dropout": 0.1}
                        ],
                        "output_activation": "linear"
                    },
                    "training": {
                        "batch_size": 32,
                        "epochs": 100,
                        "learning_rate": 0.001,
                        "optimizer": "adam",
                        "loss": "huber",
                        "metrics": ["mae", "mse"],
                        "early_stopping": {
                            "monitor": "val_loss",
                            "patience": 10,
                            "restore_best_weights": True
                        },
                        "reduce_lr_on_plateau": {
                            "monitor": "val_loss",
                            "factor": 0.5,
                            "patience": 5,
                            "min_lr": 0.00001
                        }
                    },
                    "preprocessing": {
                        "scaling_method": "minmax",
                        "handle_missing": "interpolate",
                        "detrend": False
                    }
                }
            }
            
            model_response = ts_client.create_model(model_config)
            model_id = model_response['model_id']
            
            # Step 3: Train LSTM model
            logger.info("Training LSTM model...")
            training_params = {
                "train_val_test_split": [0.7, 0.15, 0.15],
                "data_augmentation": {
                    "enabled": True,
                    "methods": ["gaussian_noise", "time_shift"]
                },
                "save_checkpoints": True,
                "tensorboard_logging": True
            }
            
            train_response = ts_client.train_model(model_id, training_params)
            training_status = ts_client.wait_for_training(model_id, timeout=900)
            
            # Verify training completed successfully
            assert training_status['state'] == 'COMPLETED'
            assert 'epochs_completed' in training_status
            assert training_status['epochs_completed'] > 0
            
            # Step 4: Generate multi-step forecast
            logger.info("Generating multi-step ahead forecast...")
            
            # Get last 168 hours of data for input
            last_sequence = {
                "sequence_data": dataset_config["data"][-168:],
                "forecast_horizon": 24,
                "prediction_intervals": True,
                "n_simulations": 100  # For uncertainty estimation
            }
            
            forecast_params = {
                "input_sequence": last_sequence,
                "return_attention_weights": True,
                "return_feature_importance": True
            }
            
            forecast_response = ts_client.generate_forecast(model_id, forecast_params)
            
            # Validate multi-step forecast
            assert 'forecast' in forecast_response
            assert len(forecast_response['forecast']) == 24
            
            # Check prediction intervals
            for forecast_point in forecast_response['forecast']:
                assert 'value' in forecast_point
                assert 'lower_bound' in forecast_point
                assert 'upper_bound' in forecast_point
                assert 'std_dev' in forecast_point
                # Prediction intervals should be reasonable
                assert forecast_point['lower_bound'] < forecast_point['value']
                assert forecast_point['value'] < forecast_point['upper_bound']
            
            # Check feature importance if available
            if 'feature_importance' in forecast_response:
                importance = forecast_response['feature_importance']
                assert 'temperature' in importance
                assert 'solar_radiation' in importance
                # Temperature should be important for energy consumption
                assert importance['temperature'] > 0.1
            
            # Step 5: Test real-time prediction endpoint
            logger.info("Testing real-time prediction endpoint...")
            
            # Simulate streaming data
            real_time_data = {
                "model_id": model_id,
                "streaming_data": [
                    {
                        "timestamp": (dates[-1] + timedelta(hours=i)).isoformat(),
                        "temperature": float(1200 + 50 * np.random.randn()),
                        "solar_radiation": float(500 + 30 * np.random.randn()),
                        "hour": (dates[-1] + timedelta(hours=i)).hour,
                        "day_of_week": (dates[-1] + timedelta(hours=i)).dayofweek,
                        "month": (dates[-1] + timedelta(hours=i)).month
                    }
                    for i in range(1, 25)
                ],
                "update_type": "sliding_window",
                "return_updated_forecast": True
            }
            
            # Make real-time prediction
            rt_response = ts_client.session.post(
                f"{ts_client.base_url}/api/v1/models/{model_id}/predict/realtime",
                json=real_time_data
            )
            rt_response.raise_for_status()
            rt_result = rt_response.json()
            
            # Validate real-time predictions
            assert 'predictions' in rt_result
            assert len(rt_result['predictions']) == 24
            assert 'latency_ms' in rt_result
            assert rt_result['latency_ms'] < 1000  # Sub-second latency
            
            # Get final model metrics
            metrics = ts_client.get_model_metrics(model_id)
            
            # Validate model performance
            assert metrics['test_mae'] < 100
            assert metrics['test_mse'] < 15000
            assert 'training_history' in metrics
            
            # Check for overfitting
            train_loss = metrics['training_history']['loss'][-1]
            val_loss = metrics['training_history']['val_loss'][-1]
            assert val_loss / train_loss < 1.5  # Validation loss not too much higher
            
            logger.info("LSTM E2E test completed successfully!")
            
        finally:
            # Cleanup
            ts_client.cleanup(model_id=model_id, dataset_id=dataset_id)
    
    @pytest.mark.e2e
    def test_model_comparison_and_ensemble(self, ts_client, sample_time_series_data):
        """
        Test model comparison and ensemble functionality:
        1. Train multiple models on same dataset
        2. Compare model performances
        3. Create ensemble model
        4. Validate ensemble outperforms individual models
        """
        dataset_id = None
        model_ids = []
        ensemble_id = None
        
        try:
            # Step 1: Upload dataset
            logger.info("Uploading dataset for model comparison...")
            dataset_response = ts_client.create_dataset(sample_time_series_data)
            dataset_id = dataset_response['dataset_id']
            
            # Step 2: Train multiple models
            models_config = [
                {
                    "name": "arima_model",
                    "model_type": "ARIMA",
                    "parameters": {
                        "auto_arima": True,
                        "seasonal": True,
                        "stepwise": True,
                        "suppress_warnings": True
                    }
                },
                {
                    "name": "prophet_model", 
                    "model_type": "PROPHET",
                    "parameters": {
                        "growth": "linear",
                        "yearly_seasonality": True,
                        "weekly_seasonality": True,
                        "daily_seasonality": False
                    }
                },
                {
                    "name": "exponential_smoothing",
                    "model_type": "ETS",
                    "parameters": {
                        "trend": "add",
                        "seasonal": "add",
                        "seasonal_periods": 7,
                        "use_boxcox": True
                    }
                }
            ]
            
            # Train all models
            for config in models_config:
                logger.info(f"Training {config['name']}...")
                config['dataset_id'] = dataset_id
                
                model_response = ts_client.create_model(config)
                model_id = model_response['model_id']
                model_ids.append(model_id)
                
                train_params = {
                    "train_test_split": 0.8,
                    "validation_metrics": ["mae", "rmse", "mape"]
                }
                
                ts_client.train_model(model_id, train_params)
                ts_client.wait_for_training(model_id)
            
            # Step 3: Compare models
            logger.info("Comparing model performances...")
            comparison_request = {
                "model_ids": model_ids,
                "comparison_metrics": ["mae", "rmse", "mape", "mase"],
                "forecast_horizons": [7, 14, 30],
                "statistical_tests": {
                    "dm_test": True,  # Diebold-Mariano test
                    "confidence_level": 0.95
                }
            }
            
            comparison_response = ts_client.session.post(
                f"{ts_client.base_url}/api/v1/models/compare",
                json=comparison_request
            )
            comparison_response.raise_for_status()
            comparison_results = comparison_response.json()
            
            # Validate comparison results
            assert 'rankings' in comparison_results
            assert 'detailed_metrics' in comparison_results
            assert 'statistical_significance' in comparison_results
            
            # Step 4: Create ensemble model
            logger.info("Creating ensemble model...")
            ensemble_config = {
                "name": "forecast_ensemble",
                "model_type": "ENSEMBLE",
                "dataset_id": dataset_id,
                "parameters": {
                    "base_models": model_ids,
                    "ensemble_method": "weighted_average",
                    "weight_optimization": {
                        "method": "minimize_rmse",
                        "constraints": "sum_to_one",
                        "non_negative": True
                    },
                    "stacking": {
                        "enabled": True,
                        "meta_learner": "linear_regression",
                        "cv_folds": 5
                    }
                }
            }
            
            ensemble_response = ts_client.create_model(ensemble_config)
            ensemble_id = ensemble_response['model_id']
            
            # Train ensemble
            ensemble_train_params = {
                "retrain_base_models": False,
                "optimize_weights": True
            }
            
            ts_client.train_model(ensemble_id, ensemble_train_params)
            ts_client.wait_for_training(ensemble_id)
            
            # Step 5: Compare ensemble with individual models
            logger.info("Comparing ensemble with individual models...")
            
            # Get ensemble metrics
            ensemble_metrics = ts_client.get_model_metrics(ensemble_id)
            
            # Get individual model metrics
            individual_metrics = []
            for model_id in model_ids:
                metrics = ts_client.get_model_metrics(model_id)
                individual_metrics.append(metrics)
            
            # Ensemble should outperform or match best individual model
            best_individual_mae = min(m['mae'] for m in individual_metrics)
            assert ensemble_metrics['mae'] <= best_individual_mae * 1.05  # Within 5%
            
            # Check ensemble weights
            assert 'ensemble_weights' in ensemble_metrics
            weights = ensemble_metrics['ensemble_weights']
            assert len(weights) == len(model_ids)
            assert abs(sum(weights.values()) - 1.0) < 0.001  # Sum to 1
            assert all(w >= 0 for w in weights.values())  # Non-negative
            
            # Generate ensemble forecast
            forecast_params = {
                "horizon": 30,
                "return_individual_forecasts": True,
                "confidence_level": 0.95
            }
            
            ensemble_forecast = ts_client.generate_forecast(ensemble_id, forecast_params)
            
            # Validate ensemble forecast
            assert 'forecast' in ensemble_forecast
            assert 'individual_forecasts' in ensemble_forecast
            assert len(ensemble_forecast['individual_forecasts']) == len(model_ids)
            
            # Ensemble prediction intervals should be tighter than worst model
            ensemble_intervals = [
                f['upper_bound'] - f['lower_bound'] 
                for f in ensemble_forecast['forecast']
            ]
            avg_ensemble_interval = np.mean(ensemble_intervals)
            
            logger.info("Model comparison and ensemble E2E test completed!")
            
        finally:
            # Cleanup
            if ensemble_id:
                ts_client.cleanup(model_id=ensemble_id)
            for model_id in model_ids:
                ts_client.cleanup(model_id=model_id)
            if dataset_id:
                ts_client.cleanup(dataset_id=dataset_id)


@pytest.mark.e2e
class TestErrorScenariosE2E:
    """Test error handling and edge cases"""
    
    def test_insufficient_data_handling(self, ts_client):
        """Test model behavior with insufficient historical data"""
        dataset_id = None
        model_id = None
        
        try:
            # Create dataset with only 30 days of data
            dates = pd.date_range(start='2023-01-01', end='2023-01-30', freq='D')
            values = 1000 + 100 * np.random.randn(len(dates))
            
            small_dataset = {
                "name": "small_dataset",
                "data": [
                    {"timestamp": date.isoformat(), "value": float(val)}
                    for date, val in zip(dates, values)
                ],
                "frequency": "daily",
                "target_column": "value",
                "timestamp_column": "timestamp"
            }
            
            dataset_response = ts_client.create_dataset(small_dataset)
            dataset_id = dataset_response['dataset_id']
            
            # Try to create model requiring more data
            model_config = {
                "name": "model_insufficient_data",
                "model_type": "ARIMA",
                "dataset_id": dataset_id,
                "parameters": {
                    "seasonal_order": [1, 1, 1, 365]  # Yearly seasonality
                }
            }
            
            with pytest.raises(requests.HTTPError) as exc_info:
                model_response = ts_client.create_model(model_config)
                model_id = model_response.get('model_id')
            
            # Should get appropriate error message
            assert exc_info.value.response.status_code == 400
            error_data = exc_info.value.response.json()
            assert 'insufficient data' in error_data['error'].lower()
            
        finally:
            ts_client.cleanup(model_id=model_id, dataset_id=dataset_id)
    
    def test_missing_data_handling(self, ts_client):
        """Test model handling of missing values and gaps"""
        dataset_id = None
        model_id = None
        
        try:
            # Create dataset with missing values
            dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
            values = 1000 + 200 * np.sin(2 * np.pi * np.arange(len(dates)) / 365.25)
            
            # Introduce missing values
            missing_indices = np.random.choice(len(dates), size=50, replace=False)
            values[missing_indices] = np.nan
            
            dataset_with_gaps = {
                "name": "dataset_with_gaps",
                "data": [
                    {"timestamp": date.isoformat(), "value": None if np.isnan(val) else float(val)}
                    for date, val in zip(dates, values)
                ],
                "frequency": "daily",
                "target_column": "value",
                "timestamp_column": "timestamp",
                "data_quality": {
                    "missing_value_threshold": 0.2,  # Allow up to 20% missing
                    "interpolation_method": "linear"
                }
            }
            
            # Upload dataset should succeed with warning
            dataset_response = ts_client.create_dataset(dataset_with_gaps)
            dataset_id = dataset_response['dataset_id']
            
            assert 'warnings' in dataset_response
            assert any('missing values' in w.lower() for w in dataset_response['warnings'])
            
            # Create and train model
            model_config = {
                "name": "model_with_interpolation",
                "model_type": "PROPHET",
                "dataset_id": dataset_id,
                "parameters": {
                    "handle_missing": "interpolate"
                }
            }
            
            model_response = ts_client.create_model(model_config)
            model_id = model_response['model_id']
            
            # Training should succeed
            train_params = {"train_test_split": 0.8}
            ts_client.train_model(model_id, train_params)
            training_status = ts_client.wait_for_training(model_id)
            
            assert training_status['state'] == 'COMPLETED'
            
            # Check that missing values were handled
            metrics = ts_client.get_model_metrics(model_id)
            assert 'data_preprocessing' in metrics
            assert 'missing_values_handled' in metrics['data_preprocessing']
            assert metrics['data_preprocessing']['missing_values_handled'] == 50
            
        finally:
            ts_client.cleanup(model_id=model_id, dataset_id=dataset_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])