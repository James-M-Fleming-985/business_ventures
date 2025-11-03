```python
"""
Time series forecasting models with validation and backtesting capabilities.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from datetime import datetime, timedelta
import warnings
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.stattools import adfuller
import matplotlib.pyplot as plt


class TimeSeriesValidator:
    """Validator for time series forecasting models with backtesting capabilities."""
    
    def __init__(self):
        """Initialize the TimeSeriesValidator."""
        self.validation_results = {}
        self.backtest_results = {}
        
    def validate_data(self, data: Union[pd.Series, pd.DataFrame]) -> Dict[str, any]:
        """
        Validate time series data for forecasting.
        
        Parameters
        ----------
        data : pd.Series or pd.DataFrame
            Time series data to validate
            
        Returns
        -------
        dict
            Validation results including stationarity, missing values, etc.
        """
        results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'data_info': {}
        }
        
        # Check if data is empty
        if len(data) == 0:
            results['is_valid'] = False
            results['errors'].append('Data is empty')
            return results
            
        # Check for missing values
        missing_count = data.isna().sum()
        if isinstance(data, pd.DataFrame):
            missing_count = missing_count.sum()
            
        if missing_count > 0:
            results['warnings'].append(f'Data contains {missing_count} missing values')
            
        # Check if index is datetime
        if not isinstance(data.index, pd.DatetimeIndex):
            results['warnings'].append('Index is not DatetimeIndex')
            
        # Check for duplicate indices
        if data.index.duplicated().any():
            results['is_valid'] = False
            results['errors'].append('Data contains duplicate indices')
            
        # Check stationarity
        if isinstance(data, pd.Series):
            adf_result = adfuller(data.dropna())
            results['data_info']['adf_statistic'] = adf_result[0]
            results['data_info']['adf_pvalue'] = adf_result[1]
            results['data_info']['is_stationary'] = adf_result[1] < 0.05
            
        results['data_info']['length'] = len(data)
        results['data_info']['start_date'] = data.index[0]
        results['data_info']['end_date'] = data.index[-1]
        
        return results
        
    def backtest(self, model, data: pd.Series, 
                 test_size: Union[int, float] = 0.2,
                 step_size: int = 1,
                 forecast_horizon: int = 1) -> Dict[str, any]:
        """
        Perform backtesting on a time series model.
        
        Parameters
        ----------
        model : object
            Forecasting model with fit and forecast methods
        data : pd.Series
            Time series data
        test_size : int or float
            Size of test set (number of observations or fraction)
        step_size : int
            Step size for rolling window
        forecast_horizon : int
            Number of periods to forecast
            
        Returns
        -------
        dict
            Backtesting results including metrics and predictions
        """
        # Convert test_size to integer if float
        if isinstance(test_size, float):
            test_size = int(len(data) * test_size)
            
        train_size = len(data) - test_size
        
        predictions = []
        actuals = []
        errors = []
        
        for i in range(0, test_size - forecast_horizon + 1, step_size):
            train_end = train_size + i
            test_start = train_end
            test_end = test_start + forecast_horizon
            
            train_data = data[:train_end]
            test_data = data[test_start:test_end]
            
            try:
                # Fit model
                if hasattr(model, 'fit'):
                    fitted_model = model.fit(train_data)
                else:
                    fitted_model = model(train_data)
                    
                # Make forecast
                if hasattr(fitted_model, 'forecast'):
                    pred = fitted_model.forecast(steps=forecast_horizon)
                elif hasattr(fitted_model, 'predict'):
                    pred = fitted_model.predict(start=test_start, end=test_end-1)
                else:
                    raise ValueError("Model must have forecast or predict method")
                    
                predictions.extend(pred)
                actuals.extend(test_data.values)
                
            except Exception as e:
                errors.append(str(e))
                continue
                
        # Calculate metrics
        if len(predictions) > 0 and len(actuals) > 0:
            mae = mean_absolute_error(actuals, predictions)
            mse = mean_squared_error(actuals, predictions)
            rmse = np.sqrt(mse)
            mape = np.mean(np.abs((np.array(actuals) - np.array(predictions)) / np.array(actuals))) * 100
            
            results = {
                'mae': mae,
                'mse': mse,
                'rmse': rmse,
                'mape': mape,
                'predictions': predictions,
                'actuals': actuals,
                'errors': errors,
                'n_forecasts': len(predictions)
            }
        else:
            results = {
                'mae': np.nan,
                'mse': np.nan,
                'rmse': np.nan,
                'mape': np.nan,
                'predictions': [],
                'actuals': [],
                'errors': errors,
                'n_forecasts': 0
            }
            
        self.backtest_results[model.__class__.__name__] = results
        return results
        
    def cross_validate(self, model, data: pd.Series,
                      n_splits: int = 5,
                      forecast_horizon: int = 1) -> Dict[str, any]:
        """
        Perform time series cross-validation.
        
        Parameters
        ----------
        model : object
            Forecasting model
        data : pd.Series
            Time series data
        n_splits : int
            Number of cross-validation splits
        forecast_horizon : int
            Forecast horizon
            
        Returns
        -------
        dict
            Cross-validation results
        """
        cv_scores = {
            'mae': [],
            'mse': [],
            'rmse': [],
            'mape': []
        }
        
        split_size = len(data) // (n_splits + 1)
        
        for i in range(n_splits):
            train_end = split_size * (i + 1)
            test_start = train_end
            test_end = min(test_start + forecast_horizon, len(data))
            
            if test_end > len(data):
                break
                
            train_data = data[:train_end]
            test_data = data[test_start:test_end]
            
            try:
                # Fit and predict
                if hasattr(model, 'fit'):
                    fitted = model.fit(train_data)
                    pred = fitted.forecast(steps=len(test_data))
                else:
                    fitted = model(train_data)
                    pred = fitted.forecast(steps=len(test_data))
                    
                # Calculate metrics
                mae = mean_absolute_error(test_data, pred)
                mse = mean_squared_error(test_data, pred)
                rmse = np.sqrt(mse)
                mape = np.mean(np.abs((test_data.values - pred) / test_data.values)) * 100
                
                cv_scores['mae'].append(mae)
                cv_scores['mse'].append(mse)
                cv_scores['rmse'].append(rmse)
                cv_scores['mape'].append(mape)
                
            except Exception as e:
                warnings.warn(f"Cross-validation fold {i} failed: {str(e)}")
                continue
                
        # Calculate average scores
        results = {
            'mae_mean': np.mean(cv_scores['mae']) if cv_scores['mae'] else np.nan,
            'mae_std': np.std(cv_scores['mae']) if cv_scores['mae'] else np.nan,
            'mse_mean': np.mean(cv_scores['mse']) if cv_scores['mse'] else np.nan,
            'mse_std': np.std(cv_scores['mse']) if cv_scores['mse'] else np.nan,
            'rmse_mean': np.mean(cv_scores['rmse']) if cv_scores['rmse'] else np.nan,
            'rmse_std': np.std(cv_scores['rmse']) if cv_scores['rmse'] else np.nan,
            'mape_mean': np.mean(cv_scores['mape']) if cv_scores['mape'] else np.nan,
            'mape_std': np.std(cv_scores['mape']) if cv_scores['mape'] else np.nan,
            'n_splits': len(cv_scores['mae']),
            'cv_scores': cv_scores
        }
        
        return results


class TimeSeriesForecaster:
    """Time series forecasting with multiple models."""
    
    def __init__(self):
        """Initialize the TimeSeriesForecaster."""
        self.models = {}
        self.validator = TimeSeriesValidator()
        self.forecasts = {}
        
    def add_model(self, name: str, model):
        """
        Add a forecasting model.
        
        Parameters
        ----------
        name : str
            Model name
        model : object
            Model instance
        """
        self.models[name] = model
        
    def fit_models(self, data: pd.Series):
        """
        Fit all models on the data.
        
        Parameters
        ----------
        data : pd.Series
            Training data
        """
        for name, model in self.models.items():
            try:
                if hasattr(model, 'fit'):
                    self.models[name] = model.fit(data)
                else:
                    self.models[name] = model(data)
            except Exception as e:
                warnings.warn(f"Failed to fit model {name}: {str(e)}")
                
    def forecast(self, steps: int) -> Dict[str, pd.Series]:
        """
        Generate forecasts from all models.
        
        Parameters
        ----------
        steps : int
            Number of steps to forecast
            
        Returns
        -------
        dict
            Forecasts from each model
        """
        forecasts = {}
        
        for name, model in self.models.items():
            try:
                if hasattr(model, 'forecast'):
                    forecasts[name] = model.forecast(steps=steps)
                elif hasattr(model, 'predict'):
                    forecasts[name] = model.predict(steps=steps)
                else:
                    warnings.warn(f"Model {name} has no forecast method")
            except Exception as e:
                warnings.warn(f"Failed to forecast with model {name}: {str(e)}")
                
        self.forecasts = forecasts
        return forecasts
        
    def ensemble_forecast(self, steps: int, weights: Optional[Dict[str, float]] = None) -> pd.Series:
        """
        Create ensemble forecast from multiple models.
        
        Parameters
        ----------
        steps : int
            Forecast horizon
        weights : dict, optional
            Model weights for ensemble
            
        Returns
        -------
        pd.Series
            Ensemble forecast
        """
        forecasts = self.forecast(steps)
        
        if not forecasts:
            raise ValueError("No forecasts available")
            
        if weights is None:
            weights = {name: 1.0 / len(forecasts) for name in forecasts}
            
        # Normalize weights
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}
        
        # Combine forecasts
        ensemble = None
        for name, forecast in forecasts.items():
            if name in weights:
                weighted_forecast = forecast * weights[name]
                if ensemble is None:
                    ensemble = weighted_forecast
                else:
                    ensemble += weighted_forecast
                    
        return ensemble


class DriftDetector:
    """Detect drift in time series data."""
    
    def __init__(self):
        """Initialize the DriftDetector."""
        self.drift_results = {}
        
    def detect_drift(self, data: pd.Series, window_size: int = 30,
                    threshold: float = 2.0) -> Dict[str, any]:
        """
        Detect drift in time series data.
        
        Parameters
        ----------
        data : pd.Series
            Time series data
        window_size : int
            Window size for drift detection
        threshold : float
            Threshold for drift detection
            
        Returns
        -------
        dict
            Drift detection results
        """
        rolling_mean = data.rolling(window=window_size).mean()
        rolling_std = data.rolling(window=window_size).std()
        
        # Calculate z-scores
        z_scores = np.abs((data - rolling_mean) / rolling_std)
        
        # Detect drift points
        drift_points = data.index[z_scores > threshold].tolist()
        
        results = {
            'drift_detected': len(drift_points) > 0,
            'drift_points': drift_points,
            'n_drift_points': len(drift_points),
            'z_scores': z_scores,
            'threshold': threshold,
            'window_size': window_size
        }
        
        self.drift_results = results
        return results
        
    def plot_drift(self, data: pd.Series, results: Optional[Dict] = None):
        """
        Plot drift detection results.
        
        Parameters
        ----------
        data : pd.Series
            Original time series
        results : dict, optional
            Drift detection results
        """
        if results is None:
            results = self.drift_results
            
        plt.figure(figsize=(12, 6))
        plt.plot(data.index, data.values, label='Original Data')
        
        if results.get('drift_points'):
            drift_values = data[results['drift_points']]
            plt.scatter(drift_values.index, drift_values.values,
                       color='red', s=50, label='Drift Points')
                       
        plt.legend()
        plt.title('Drift Detection Results')
        plt.xlabel('Time')
        plt.ylabel('Value')
        plt.show()


# Model wrapper classes for compatibility
class ARIMAModel:
    """ARIMA model wrapper."""
    
    def __init__(self, order=(1, 1, 1)):
        """Initialize ARIMA model."""
        self.order = order
        self.model = None
        self.fitted = None
        
    def fit(self, data):
        """Fit the model."""
        self.model = ARIMA(data, order=self.order)
        self.fitted = self.model.fit()
        return self
        
    def forecast(self, steps):
        """Generate forecast."""
        return self.fitted.forecast(steps=steps)


class SARIMAXModel:
    """SARIMAX model wrapper."""
    
    def __init__(self, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12)):
        """Initialize SARIMAX model."""
        self.order = order
        self.seasonal_order = seasonal_order
        self.model = None
        self.fitted = None
        
    def fit(self, data):
        """Fit the model."""
        self.model = SARIMAX(data, order=self.order, seasonal_order=self.seasonal_order)
        self.fitted = self.model.fit(disp=False)
        return self
        
    def forecast(self, steps):
        """Generate forecast."""
        return self.fitted.forecast(steps=steps)


class ExponentialSmoothingModel:
    """Exponential Smoothing model wrapper."""
    
    def __init__(self, trend='add', seasonal='add', seasonal_periods=12):
        """Initialize Exponential Smoothing model."""
        self.trend = trend
        self.seasonal = seasonal
        self.seasonal_periods = seasonal_periods
        self.model = None
        self.fitted = None
        
    def fit(self, data):
        """Fit the model."""
        self.model = ExponentialSmoothing(data, trend=self.trend,
                                         seasonal=self.seasonal,
                                         seasonal_periods=self.seasonal_periods)
        self.fitted = self.model.fit()
        return self
        
    def forecast(self, steps):
        """Generate forecast."""
        return self.fitted.forecast(steps=steps)
```