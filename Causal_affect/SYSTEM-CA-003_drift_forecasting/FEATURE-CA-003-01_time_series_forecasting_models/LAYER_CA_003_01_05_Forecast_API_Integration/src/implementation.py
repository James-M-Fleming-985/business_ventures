```python
"""
Forecast API Integration Module

This module provides integration with various forecasting APIs and models,
including time series forecasting capabilities with drift detection.
"""

import json
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass, asdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ForecastResult:
    """Represents the result of a forecast operation."""
    forecast_values: List[float]
    confidence_intervals: Optional[Dict[str, List[float]]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    model_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert ForecastResult to dictionary."""
        result = asdict(self)
        if self.timestamp:
            result['timestamp'] = self.timestamp.isoformat()
        return result


class ForecastAPIError(Exception):
    """Custom exception for Forecast API errors."""
    pass


class ForecastAPIIntegration:
    """
    Main class for integrating with forecast APIs.
    
    Provides methods for making time series forecasts with drift detection
    and various forecasting models.
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the Forecast API Integration.
        
        Args:
            api_key: Optional API key for authentication
            base_url: Optional base URL for the API endpoint
        """
        self.api_key = api_key
        self.base_url = base_url or "https://api.forecast.example.com"
        self._models = {
            'arima': self._forecast_arima,
            'exponential_smoothing': self._forecast_exponential_smoothing,
            'prophet': self._forecast_prophet,
            'lstm': self._forecast_lstm
        }
        
    def forecast(self, 
                 data: Union[List[float], np.ndarray],
                 horizon: int,
                 model_type: str = 'arima',
                 confidence_level: float = 0.95,
                 include_drift: bool = True,
                 **kwargs) -> ForecastResult:
        """
        Generate forecast for given time series data.
        
        Args:
            data: Historical time series data
            horizon: Number of periods to forecast
            model_type: Type of forecasting model to use
            confidence_level: Confidence level for prediction intervals
            include_drift: Whether to include drift in the forecast
            **kwargs: Additional model-specific parameters
            
        Returns:
            ForecastResult object containing forecasts and metadata
            
        Raises:
            ForecastAPIError: If forecasting fails
            ValueError: If invalid parameters are provided
        """
        if not isinstance(data, (list, np.ndarray)):
            raise ValueError("Data must be a list or numpy array")
            
        if len(data) < 3:
            raise ValueError("At least 3 data points required for forecasting")
            
        if horizon < 1:
            raise ValueError("Horizon must be at least 1")
            
        if confidence_level <= 0 or confidence_level >= 1:
            raise ValueError("Confidence level must be between 0 and 1")
            
        if model_type not in self._models:
            raise ValueError(f"Unknown model type: {model_type}")
            
        try:
            # Convert to numpy array for processing
            data_array = np.array(data, dtype=float)
            
            # Check for NaN or infinite values
            if np.any(np.isnan(data_array)) or np.any(np.isinf(data_array)):
                raise ValueError("Data contains NaN or infinite values")
            
            # Detect and handle drift if requested
            if include_drift:
                drift = self._detect_drift(data_array)
            else:
                drift = 0.0
            
            # Call appropriate model
            forecast_func = self._models[model_type]
            forecast_values = forecast_func(data_array, horizon, drift, **kwargs)
            
            # Calculate confidence intervals
            confidence_intervals = self._calculate_confidence_intervals(
                forecast_values, data_array, confidence_level
            )
            
            # Prepare metadata
            metadata = {
                'model_type': model_type,
                'horizon': horizon,
                'confidence_level': confidence_level,
                'include_drift': include_drift,
                'drift_rate': drift if include_drift else None,
                'data_points': len(data),
                'forecast_generated_at': datetime.now().isoformat()
            }
            
            return ForecastResult(
                forecast_values=forecast_values.tolist(),
                confidence_intervals=confidence_intervals,
                metadata=metadata,
                timestamp=datetime.now(),
                model_type=model_type
            )
            
        except Exception as e:
            logger.error(f"Forecast failed: {str(e)}")
            raise ForecastAPIError(f"Forecast generation failed: {str(e)}")
    
    def batch_forecast(self,
                      series_list: List[List[float]],
                      horizon: int,
                      model_type: str = 'arima',
                      **kwargs) -> List[ForecastResult]:
        """
        Generate forecasts for multiple time series.
        
        Args:
            series_list: List of time series data
            horizon: Number of periods to forecast for each series
            model_type: Type of forecasting model to use
            **kwargs: Additional parameters passed to forecast method
            
        Returns:
            List of ForecastResult objects
        """
        results = []
        for i, series in enumerate(series_list):
            try:
                result = self.forecast(series, horizon, model_type, **kwargs)
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to forecast series {i}: {str(e)}")
                # Add None or empty result for failed series
                results.append(ForecastResult(
                    forecast_values=[],
                    metadata={'error': str(e), 'series_index': i}
                ))
        return results
    
    def _detect_drift(self, data: np.ndarray) -> float:
        """
        Detect drift in time series data.
        
        Args:
            data: Time series data as numpy array
            
        Returns:
            Estimated drift rate
        """
        if len(data) < 2:
            return 0.0
            
        # Simple linear trend detection
        x = np.arange(len(data))
        coefficients = np.polyfit(x, data, 1)
        return coefficients[0]
    
    def _forecast_arima(self, data: np.ndarray, horizon: int, drift: float, **kwargs) -> np.ndarray:
        """
        Generate forecast using ARIMA model.
        
        Args:
            data: Historical data
            horizon: Forecast horizon
            drift: Drift rate
            **kwargs: ARIMA-specific parameters
            
        Returns:
            Forecast values as numpy array
        """
        # Simplified ARIMA implementation
        # In production, use statsmodels or similar library
        
        # Extract parameters
        p = kwargs.get('p', 1)  # AR order
        d = kwargs.get('d', 1)  # Differencing order
        q = kwargs.get('q', 1)  # MA order
        
        # Simple forecast based on last values and trend
        last_value = data[-1]
        trend = np.mean(np.diff(data[-min(len(data), 5):]))
        
        forecast = np.zeros(horizon)
        for i in range(horizon):
            forecast[i] = last_value + (i + 1) * (trend + drift)
            
        # Add some noise for realism
        noise = np.random.normal(0, np.std(data) * 0.1, horizon)
        forecast += noise
        
        return forecast
    
    def _forecast_exponential_smoothing(self, data: np.ndarray, horizon: int, 
                                       drift: float, **kwargs) -> np.ndarray:
        """
        Generate forecast using Exponential Smoothing.
        
        Args:
            data: Historical data
            horizon: Forecast horizon
            drift: Drift rate
            **kwargs: Model-specific parameters
            
        Returns:
            Forecast values as numpy array
        """
        # Simple exponential smoothing implementation
        alpha = kwargs.get('alpha', 0.3)
        
        # Initialize
        smoothed = np.zeros(len(data))
        smoothed[0] = data[0]
        
        # Apply exponential smoothing
        for i in range(1, len(data)):
            smoothed[i] = alpha * data[i] + (1 - alpha) * smoothed[i-1]
        
        # Generate forecast
        last_smoothed = smoothed[-1]
        forecast = np.zeros(horizon)
        
        for i in range(horizon):
            forecast[i] = last_smoothed + (i + 1) * drift
            
        return forecast
    
    def _forecast_prophet(self, data: np.ndarray, horizon: int, 
                         drift: float, **kwargs) -> np.ndarray:
        """
        Generate forecast using Prophet-like model.
        
        Args:
            data: Historical data
            horizon: Forecast horizon
            drift: Drift rate
            **kwargs: Model-specific parameters
            
        Returns:
            Forecast values as numpy array
        """
        # Simplified Prophet-like implementation
        # In production, use fbprophet library
        
        # Detect seasonality (simplified)
        if len(data) >= 7:
            seasonal_period = 7
            seasonal_component = np.tile(
                data[-seasonal_period:] - np.mean(data[-seasonal_period:]), 
                (horizon // seasonal_period + 1)
            )[:horizon]
        else:
            seasonal_component = np.zeros(horizon)
        
        # Base trend
        base_trend = np.mean(data)
        trend_component = base_trend + np.arange(1, horizon + 1) * drift
        
        # Combine components
        forecast = trend_component + seasonal_component * 0.1
        
        return forecast
    
    def _forecast_lstm(self, data: np.ndarray, horizon: int, 
                      drift: float, **kwargs) -> np.ndarray:
        """
        Generate forecast using LSTM-like model.
        
        Args:
            data: Historical data
            horizon: Forecast horizon
            drift: Drift rate
            **kwargs: Model-specific parameters
            
        Returns:
            Forecast values as numpy array
        """
        # Simplified LSTM-like behavior
        # In production, use TensorFlow/PyTorch
        
        # Use recent pattern
        lookback = min(len(data), kwargs.get('lookback', 10))
        recent_pattern = data[-lookback:]
        
        # Generate forecast with pattern influence
        forecast = np.zeros(horizon)
        
        for i in range(horizon):
            # Weighted average of recent values
            weights = np.exp(-np.arange(lookback) * 0.1)
            weights = weights / np.sum(weights)
            base_value = np.sum(recent_pattern * weights[::-1])
            
            forecast[i] = base_value + (i + 1) * drift
            
        return forecast
    
    def _calculate_confidence_intervals(self, forecast: np.ndarray, 
                                       historical_data: np.ndarray,
                                       confidence_level: float) -> Dict[str, List[float]]:
        """
        Calculate confidence intervals for forecast.
        
        Args:
            forecast: Forecast values
            historical_data: Historical data for variance estimation
            confidence_level: Confidence level (e.g., 0.95)
            
        Returns:
            Dictionary with 'lower' and 'upper' bounds
        """
        # Estimate prediction error based on historical variance
        residual_std = np.std(np.diff(historical_data)) if len(historical_data) > 1 else 1.0
        
        # Calculate z-score for confidence level
        # Simplified - in production use scipy.stats
        z_score = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}.get(confidence_level, 1.96)
        
        # Increase uncertainty over forecast horizon
        horizon = len(forecast)
        uncertainty = residual_std * np.sqrt(np.arange(1, horizon + 1))
        
        lower_bound = forecast - z_score * uncertainty
        upper_bound = forecast + z_score * uncertainty
        
        return {
            'lower': lower_bound.tolist(),
            'upper': upper_bound.tolist()
        }


class DriftDetector:
    """
    Utility class for detecting drift in time series data.
    """
    
    @staticmethod
    def detect_drift(data: Union[List[float], np.ndarray], 
                    window_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Detect drift in time series data.
        
        Args:
            data: Time series data
            window_size: Window size for drift detection
            
        Returns:
            Dictionary containing drift metrics
        """
        data_array = np.array(data)
        
        if len(data_array) < 2:
            return {
                'has_drift': False,
                'drift_rate': 0.0,
                'drift_type': 'none'
            }
        
        # Linear trend
        x = np.arange(len(data_array))
        coefficients = np.polyfit(x, data_array, 1)
        drift_rate = coefficients[0]
        
        # Determine drift type
        if abs(drift_rate) < 0.01:
            drift_type = 'none'
        elif drift_rate > 0:
            drift_type = 'positive'
        else:
            drift_type = 'negative'
        
        return {
            'has_drift': drift_type != 'none',
            'drift_rate': drift_rate,
            'drift_type': drift_type,
            'trend_line_slope': drift_rate,
            'trend_line_intercept': coefficients[1]
        }


class ForecastValidator:
    """
    Utility class for validating forecast results.
    """
    
    @staticmethod
    def validate_forecast(forecast_result: ForecastResult,
                         historical_data: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Validate a forecast result.
        
        Args:
            forecast_result: ForecastResult to validate
            historical_data: Optional historical data for comparison
            
        Returns:
            Dictionary containing validation results
        """
        validation = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check forecast values
        if not forecast_result.forecast_values:
            validation['is_valid'] = False
            validation['errors'].append('No forecast values provided')
        elif any(np.isnan(val) or np.isinf(val) for val in forecast_result.forecast_values):
            validation['is_valid'] = False
            validation['errors'].append('Forecast contains NaN or infinite values')
        
        # Check confidence intervals if present
        if forecast_result.confidence_intervals:
            ci = forecast_result.confidence_intervals
            if 'lower' in ci and 'upper' in ci:
                if len(ci['lower']) != len(forecast_result.forecast_values):
                    validation['warnings'].append('Confidence interval length mismatch')
                
                # Check if intervals make sense
                for i, (lower, upper) in enumerate(zip(ci['lower'], ci['upper'])):
                    if lower > upper:
                        validation['errors'].append(f'Invalid confidence interval at index {i}')
                        validation['is_valid'] = False
        
        # Validate against historical data if provided
        if historical_data:
            hist_mean = np.mean(historical_data)
            hist_std = np.std(historical_data)
            
            forecast_mean = np.mean(forecast_result.forecast_values)
            
            # Check if forecast is reasonable (within 5 standard deviations)
            if abs(forecast_mean - hist_mean) > 5 * hist_std:
                validation['warnings'].append('Forecast mean significantly different from historical mean')
        
        return validation


# Export main classes and functions
__all__ = [
    'ForecastAPIIntegration',
    'ForecastResult',
    'ForecastAPIError',
    'DriftDetector',
    'ForecastValidator'
]
```