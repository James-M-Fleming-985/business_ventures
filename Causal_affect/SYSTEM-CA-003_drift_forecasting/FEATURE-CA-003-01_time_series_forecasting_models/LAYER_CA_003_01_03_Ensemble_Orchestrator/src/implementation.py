```python
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime
import warnings
import logging
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from prophet import Prophet
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from concurrent.futures import ThreadPoolExecutor, as_completed
import joblib
import os
import json
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseModel(ABC):
    """Base class for all forecasting models."""
    
    @abstractmethod
    def fit(self, data: pd.DataFrame):
        """Fit the model to the data."""
        pass
    
    @abstractmethod
    def predict(self, steps: int) -> np.ndarray:
        """Make predictions for the specified number of steps."""
        pass


class ARIMAModel(BaseModel):
    """ARIMA model implementation."""
    
    def __init__(self, order=(1, 1, 1)):
        self.order = order
        self.model = None
        self.fitted_model = None
        
    def fit(self, data: pd.DataFrame):
        """Fit ARIMA model to the data."""
        if 'value' not in data.columns:
            raise ValueError("Data must contain 'value' column")
        
        self.model = ARIMA(data['value'].values, order=self.order)
        self.fitted_model = self.model.fit()
        
    def predict(self, steps: int) -> np.ndarray:
        """Make predictions."""
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before prediction")
        
        forecast = self.fitted_model.forecast(steps=steps)
        return forecast


class ProphetModel(BaseModel):
    """Prophet model implementation."""
    
    def __init__(self):
        self.model = None
        
    def fit(self, data: pd.DataFrame):
        """Fit Prophet model to the data."""
        if 'ds' not in data.columns or 'y' not in data.columns:
            # Convert to Prophet format
            prophet_data = pd.DataFrame()
            if 'date' in data.columns:
                prophet_data['ds'] = pd.to_datetime(data['date'])
            else:
                prophet_data['ds'] = pd.date_range(
                    start='2020-01-01', 
                    periods=len(data), 
                    freq='D'
                )
            prophet_data['y'] = data['value'].values
            data = prophet_data
        
        self.model = Prophet(daily_seasonality=False, yearly_seasonality=True)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.model.fit(data)
        
    def predict(self, steps: int) -> np.ndarray:
        """Make predictions."""
        if self.model is None:
            raise ValueError("Model must be fitted before prediction")
        
        future = self.model.make_future_dataframe(periods=steps)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            forecast = self.model.predict(future)
        
        return forecast['yhat'].values[-steps:]


class ExponentialSmoothingModel(BaseModel):
    """Exponential Smoothing model implementation."""
    
    def __init__(self, seasonal_periods=12):
        self.seasonal_periods = seasonal_periods
        self.model = None
        
    def fit(self, data: pd.DataFrame):
        """Fit Exponential Smoothing model to the data."""
        if 'value' not in data.columns:
            raise ValueError("Data must contain 'value' column")
        
        # Handle edge cases
        if len(data) < 2:
            self.model = None
            self.last_value = data['value'].values[-1] if len(data) == 1 else 0
            return
        
        try:
            self.model = ExponentialSmoothing(
                data['value'].values,
                seasonal_periods=self.seasonal_periods if len(data) >= self.seasonal_periods * 2 else None,
                trend='add',
                seasonal='add' if len(data) >= self.seasonal_periods * 2 else None
            ).fit()
        except:
            # Fallback to simpler model
            self.model = ExponentialSmoothing(
                data['value'].values,
                trend='add'
            ).fit()
        
    def predict(self, steps: int) -> np.ndarray:
        """Make predictions."""
        if self.model is None:
            if hasattr(self, 'last_value'):
                return np.array([self.last_value] * steps)
            raise ValueError("Model must be fitted before prediction")
        
        return self.model.forecast(steps=steps)


class XGBoostModel(BaseModel):
    """XGBoost model implementation."""
    
    def __init__(self, lags=10):
        self.lags = lags
        self.model = None
        self.scaler = StandardScaler()
        self.last_values = None
        
    def _create_features(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Create lagged features for time series."""
        n = len(data)
        X = []
        y = []
        
        for i in range(self.lags, n):
            X.append(data[i-self.lags:i])
            y.append(data[i])
        
        return np.array(X), np.array(y)
    
    def fit(self, data: pd.DataFrame):
        """Fit XGBoost model to the data."""
        if 'value' not in data.columns:
            raise ValueError("Data must contain 'value' column")
        
        values = data['value'].values
        
        if len(values) < self.lags + 1:
            self.last_values = values
            self.model = None
            return
        
        X, y = self._create_features(values)
        
        if len(X) == 0:
            self.last_values = values
            self.model = None
            return
        
        X_scaled = self.scaler.fit_transform(X)
        
        self.model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.1,
            objective='reg:squarederror'
        )
        self.model.fit(X_scaled, y)
        self.last_values = values[-self.lags:]
        
    def predict(self, steps: int) -> np.ndarray:
        """Make predictions."""
        if self.model is None:
            if self.last_values is not None:
                # Simple prediction based on last value
                return np.array([self.last_values[-1]] * steps)
            raise ValueError("Model must be fitted before prediction")
        
        predictions = []
        current_input = self.last_values.copy()
        
        for _ in range(steps):
            X_pred = current_input[-self.lags:].reshape(1, -1)
            X_pred_scaled = self.scaler.transform(X_pred)
            pred = self.model.predict(X_pred_scaled)[0]
            predictions.append(pred)
            current_input = np.append(current_input, pred)
        
        return np.array(predictions)


class RandomForestModel(BaseModel):
    """Random Forest model implementation."""
    
    def __init__(self, lags=10):
        self.lags = lags
        self.model = None
        self.scaler = StandardScaler()
        self.last_values = None
        
    def _create_features(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Create lagged features for time series."""
        n = len(data)
        X = []
        y = []
        
        for i in range(self.lags, n):
            X.append(data[i-self.lags:i])
            y.append(data[i])
        
        return np.array(X), np.array(y)
    
    def fit(self, data: pd.DataFrame):
        """Fit Random Forest model to the data."""
        if 'value' not in data.columns:
            raise ValueError("Data must contain 'value' column")
        
        values = data['value'].values
        
        if len(values) < self.lags + 1:
            self.last_values = values
            self.model = None
            return
        
        X, y = self._create_features(values)
        
        if len(X) == 0:
            self.last_values = values
            self.model = None
            return
        
        X_scaled = self.scaler.fit_transform(X)
        
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        self.model.fit(X_scaled, y)
        self.last_values = values[-self.lags:]
        
    def predict(self, steps: int) -> np.ndarray:
        """Make predictions."""
        if self.model is None:
            if self.last_values is not None:
                # Simple prediction based on last value
                return np.array([self.last_values[-1]] * steps)
            raise ValueError("Model must be fitted before prediction")
        
        predictions = []
        current_input = self.last_values.copy()
        
        for _ in range(steps):
            X_pred = current_input[-self.lags:].reshape(1, -1)
            X_pred_scaled = self.scaler.transform(X_pred)
            pred = self.model.predict(X_pred_scaled)[0]
            predictions.append(pred)
            current_input = np.append(current_input, pred)
        
        return np.array(predictions)


class EnsembleOrchestrator:
    """Orchestrates multiple time series forecasting models."""
    
    def __init__(self, models: Optional[List[str]] = None):
        """
        Initialize the EnsembleOrchestrator.
        
        Args:
            models: List of model names to include in the ensemble.
                   If None, uses default set of models.
        """
        self.available_models = {
            'arima': ARIMAModel,
            'prophet': ProphetModel,
            'exponential_smoothing': ExponentialSmoothingModel,
            'xgboost': XGBoostModel,
            'random_forest': RandomForestModel
        }
        
        if models is None:
            models = list(self.available_models.keys())
        
        self.models = {}
        for model_name in models:
            if model_name in self.available_models:
                self.models[model_name] = self.available_models[model_name]()
        
        self.is_fitted = False
        self.weights = None
        self.performance_metrics = {}
        self.training_data = None
        self.validation_predictions = {}
        
    def fit(self, data: pd.DataFrame, validation_split: float = 0.2,
            parallel: bool = True) -> Dict[str, Any]:
        """
        Fit all models in the ensemble.
        
        Args:
            data: Training data with 'value' column
            validation_split: Fraction of data to use for validation
            parallel: Whether to train models in parallel
            
        Returns:
            Dictionary containing fit statistics
        """
        if 'value' not in data.columns:
            raise ValueError("Data must contain 'value' column")
        
        # Split data
        n_val = int(len(data) * validation_split)
        train_data = data.iloc[:-n_val] if n_val > 0 else data
        val_data = data.iloc[-n_val:] if n_val > 0 else None
        
        self.training_data = train_data.copy()
        
        # Fit models
        if parallel:
            with ThreadPoolExecutor(max_workers=len(self.models)) as executor:
                futures = {
                    executor.submit(self._fit_single_model, name, model, train_data): name
                    for name, model in self.models.items()
                }
                
                for future in as_completed(futures):
                    name = futures[future]
                    try:
                        future.result()
                        logger.info(f"Successfully fitted {name}")
                    except Exception as e:
                        logger.error(f"Failed to fit {name}: {str(e)}")
                        # Remove failed model
                        del self.models[name]
        else:
            for name, model in list(self.models.items()):
                try:
                    self._fit_single_model(name, model, train_data)
                    logger.info(f"Successfully fitted {name}")
                except Exception as e:
                    logger.error(f"Failed to fit {name}: {str(e)}")
                    # Remove failed model
                    del self.models[name]
        
        # Calculate weights based on validation performance
        if val_data is not None and len(val_data) > 0:
            self._calculate_weights(train_data, val_data)
        else:
            # Equal weights if no validation data
            self.weights = {name: 1.0 / len(self.models) for name in self.models}
        
        self.is_fitted = True
        
        return {
            'fitted_models': list(self.models.keys()),
            'weights': self.weights,
            'performance_metrics': self.performance_metrics
        }
    
    def _fit_single_model(self, name: str, model: BaseModel, data: pd.DataFrame):
        """Fit a single model."""
        model.fit(data)
    
    def _calculate_weights(self, train_data: pd.DataFrame, val_data: pd.DataFrame):
        """Calculate model weights based on validation performance."""
        val_steps = len(val_data)
        actual_values = val_data['value'].values
        
        errors = {}
        for name, model in self.models.items():
            try:
                # Re-fit on training data and predict validation
                model.fit(train_data)
                predictions = model.predict(val_steps)
                self.validation_predictions[name] = predictions
                
                # Calculate error (using RMSE)
                error = np.sqrt(mean_squared_error(actual_values, predictions))
                errors[name] = error
                
                # Store performance metrics
                self.performance_metrics[name] = {
                    'rmse': error,
                    'mae': mean_absolute_error(actual_values, predictions)
                }
            except Exception as e:
                logger.error(f"Failed to calculate weights for {name}: {str(e)}")
                errors[name] = float('inf')
        
        # Convert errors to weights (inverse of error)
        total_inv_error = sum(1 / (e + 1e-10) for e in errors.values() if e != float('inf'))
        
        self.weights = {}
        for name, error in errors.items():
            if error == float('inf'):
                self.weights[name] = 0.0
            else:
                self.weights[name] = (1 / (error + 1e-10)) / total_inv_error
        
        # Re-fit all models on full training data
        for name, model in self.models.items():
            try:
                model.fit(train_data)
            except:
                pass
    
    def predict(self, steps: int, method: str = 'weighted_average',
                confidence_interval: float = 0.95) -> Dict[str, Any]:
        """
        Generate ensemble predictions.
        
        Args:
            steps: Number of steps to predict
            method: Ensemble method ('weighted_average', 'median', 'best_model')
            confidence_interval: Confidence interval for predictions
            
        Returns:
            Dictionary containing predictions and metadata
        """
        if not self.is_fitted:
            raise ValueError("Orchestrator must be fitted before prediction")
        
        # Collect predictions from all models
        individual_predictions = {}
        for name, model in self.models.items():
            try:
                pred = model.predict(steps)
                individual_predictions[name] = pred
            except Exception as e:
                logger.error(f"Failed to get predictions from {name}: {str(e)}")
        
        if not individual_predictions:
            raise ValueError("No models produced valid predictions")
        
        # Combine predictions based on method
        if method == 'weighted_average':
            ensemble_pred = self._weighted_average(individual_predictions)
        elif method == 'median':
            ensemble_pred = self._median(individual_predictions)
        elif method == 'best_model':
            ensemble_pred = self._best_model(individual_predictions)
        else:
            raise ValueError(f"Unknown ensemble method: {method}")
        
        # Calculate prediction intervals
        pred_std = self._calculate_prediction_std(individual_predictions)
        z_score = 1.96 if confidence_interval == 0.95 else 2.58
        
        lower_bound = ensemble_pred - z_score * pred_std
        upper_bound = ensemble_pred + z_score * pred_std
        
        return {
            'predictions': ensemble_pred,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'individual_predictions': individual_predictions,
            'method': method,
            'confidence_interval': confidence_interval,
            'weights': self.weights
        }
    
    def _weighted_average(self, predictions: Dict[str, np.ndarray]) -> np.ndarray:
        """Calculate weighted average of predictions."""
        weighted_sum = None
        total_weight = 0
        
        for name, pred in predictions.items():
            weight = self.weights.get(name, 0)
            if weight > 0:
                if weighted_sum is None:
                    weighted_sum = weight * pred
                else:
                    weighted_sum += weight * pred
                total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else np.mean(list(predictions.values()), axis=0)
    
    def _median(self, predictions: Dict[str, np.ndarray]) -> np.ndarray:
        """Calculate median of predictions."""
        pred_array = np.array(list(predictions.values()))
        return np.median(pred_array, axis=0)
    
    def _best_model(self, predictions: Dict[str, np.ndarray]) -> np.ndarray:
        """Return predictions from the best performing model."""
        best_model = max(self.weights.items(), key=lambda x: x[1])[0]
        return predictions.get(best_model, self._weighted_average(predictions))
    
    def _calculate_prediction_std(self, predictions: Dict[str, np.ndarray]) -> np.ndarray:
        """Calculate standard deviation of predictions."""
        pred_array = np.array(list(predictions.values()))
        return np.std(pred_array, axis=0)
    
    def evaluate(self, actual_values: np.ndarray, predictions: Dict[str, Any]) -> Dict[str, float]:
        """
        Evaluate ensemble predictions against actual values.
        
        Args:
            actual_values: Actual values to compare against
            predictions: Predictions dictionary from predict method
            
        Returns:
            Dictionary of evaluation metrics
        """
        ensemble_pred = predictions['predictions']
        
        if len(actual_values) != len(ensemble_pred):
            min_len = min(len(actual_values), len(ensemble_pred))
            actual_values = actual_values[:min_len]
            ensemble_pred = ensemble_pred[:min_len]
        
        metrics = {
            'rmse': np.sqrt(mean_squared_error(actual_values, ensemble_pred)),
            'mae': mean_absolute_error(actual_values, ensemble_pred),
            'mape': np.mean(np.abs((actual_values - ensemble_pred) / (actual_values + 1e-10))) * 100
        }
        
        # Coverage for prediction intervals
        if 'lower_bound' in predictions and 'upper_bound' in predictions:
            lower = predictions['lower_bound'][:len(actual_values)]
            upper = predictions['upper_bound'][:len(actual_values)]
            coverage = np.mean((actual_values >= lower) & (actual_values <= upper))
            metrics['coverage'] = coverage
        
        return metrics
    
    def save(self, path: str):
        """
        Save the orchestrator to disk.
        
        Args:
            path: Path to save the orchestrator
        """
        os.makedirs(path, exist_ok=True)
        
        # Save metadata
        metadata = {
            'models': list(self.models.keys()),
            'weights': self.weights,
            'performance_metrics': self.performance_metrics,
            'is_fitted': self.is_fitted
        }
        
        with open(os.path.join(path, 'metadata.json'), 'w') as f:
            json.dump(metadata, f)
        
        # Save individual models
        for name, model in self.models.items():
            model_path = os.path.join(path, f'{name}.pkl')
            joblib.dump(model, model_path)
        
        # Save training data if available
        if self.training_data is not None:
            self.training_data.to_csv(os.path.join(path, 'training_data.csv'), index=False)
    
    @classmethod
    def load(cls, path: str) -> 'EnsembleOrchestrator':
        """
        Load an orchestrator from disk.
        
        Args:
            path: Path to load the orchestrator from
            
        Returns:
            Loaded EnsembleOrchestrator instance
        """
        # Load metadata
        with open(os.path.join(path, 'metadata.json'), 'r') as f:
            metadata = json.load(f)
        
        # Create orchestrator
        orchestrator = cls(models=metadata['models'])
        orchestrator.weights = metadata['weights']
        orchestrator.performance_metrics = metadata['performance_metrics']
        orchestrator.is_fitted = metadata['is_fitted']
        
        # Load individual models
        orchestrator.models = {}
        for name in metadata['models']:
            model_path = os.path.join(path, f'{name}.pkl')
            if os.path.exists(model_path):
                orchestrator.models[name] = joblib.load(model_path)
        
        # Load training data if available
        training_data_path = os.path.join(path, 'training_data.csv')
        if os.path.exists(training_data_path):
            orchestrator.training_data = pd.read_csv(training_data_path)
        
        return orchestrator
    
    def retrain(self, new_data: pd.DataFrame, incremental: bool = False) -> Dict[str, Any]:
        """
        Retrain the ensemble with new data.
        
        Args:
            new_data: New training data
            incremental: If True, combine with existing training data
            
        Returns:
            Dictionary containing retrain statistics
        """
        if incremental and self.training_data is not None:
            # Combine old and new data
            combined_data = pd.concat([self.training_data, new_data], ignore_index=True)
        else:
            combined_data = new_data
        
        # Re-fit all models
        return self.fit(combined_data)
    
    def get_model_importance(self) -> Dict[str, float]:
        """
        Get the importance/weight of each model in the ensemble.
        
        Returns:
            Dictionary mapping model names to their weights
        """
        return self.weights.copy() if self.weights else {}
    
    def remove_model(self, model_name: str):
        """
        Remove a model from the ensemble.
        
        Args:
            model_name: Name of the model to remove
        """
        if model_name in self.models:
            del self.models[model_name]
            
            # Recalculate weights
            if self.weights and model_name in self.weights:
                del self.weights[model_name]
                # Normalize remaining weights
                total_weight = sum(self.weights.values())
                if total_weight > 0:
                    self.weights = {k: v/total_weight for k, v in self.weights.items()}
    
    def add_model(self, model_name: str, model: Optional[BaseModel] = None):
        """
        Add a new model to the ensemble.
        
        Args:
            model_name: Name for the new model
            model: Model instance (if None, uses default from available_models)
        """
        if model is None and model_name in self.available_models:
            model = self.available_models[model_name]()
        
        if model is not None:
            self.models[model_name] = model
            
            # If already fitted, fit the new model
            if self.is_fitted and self.training_data is not None:
                try:
                    model.fit(self.training_data)
                    # Give it equal weight initially
                    self.weights[model_name] = 1.0 / len(self.models)
                    # Normalize all weights
                    total_weight = sum(self.weights.values())
                    self.weights = {k: v/total_weight for k, v in self.weights.items()}
                except Exception as e:
                    logger.error(f"Failed to fit new model {model_name}: {str(e)}")
                    del self.models[model_name]
```