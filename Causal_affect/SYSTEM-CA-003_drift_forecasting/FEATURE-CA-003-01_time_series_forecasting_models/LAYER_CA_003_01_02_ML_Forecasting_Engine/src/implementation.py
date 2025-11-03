```python
"""
ML Forecasting Engine Module

This module provides machine learning-based time series forecasting functionality
with support for multiple models including Random Forest, XGBoost, and LightGBM.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False


class MLForecastingEngine:
    """
    Machine Learning Forecasting Engine for time series prediction.
    
    Supports multiple ML models including Random Forest, XGBoost, and LightGBM
    with automated feature engineering and model evaluation.
    """
    
    def __init__(self, model_type: str = 'random_forest', **kwargs):
        """
        Initialize the ML Forecasting Engine.
        
        Args:
            model_type: Type of model to use ('random_forest', 'xgboost', 'lightgbm')
            **kwargs: Additional parameters for the specific model
        """
        self.model_type = model_type.lower()
        self.model = None
        self.model_params = kwargs
        self.is_fitted = False
        self.feature_names = []
        self.target_name = None
        self.lag_features = None
        self.window_features = None
        
        # Validate model type
        valid_models = ['random_forest', 'xgboost', 'lightgbm']
        if self.model_type not in valid_models:
            raise ValueError(f"Invalid model_type. Must be one of {valid_models}")
            
        # Check dependencies
        if self.model_type == 'xgboost' and not HAS_XGBOOST:
            raise ImportError("XGBoost is not installed. Please install it first.")
        if self.model_type == 'lightgbm' and not HAS_LIGHTGBM:
            raise ImportError("LightGBM is not installed. Please install it first.")
    
    def create_features(self, data: pd.DataFrame, target_col: str, 
                       lag_features: int = 3, window_features: List[int] = None) -> pd.DataFrame:
        """
        Create time series features from the data.
        
        Args:
            data: Input DataFrame with time series data
            target_col: Name of the target column
            lag_features: Number of lag features to create
            window_features: List of window sizes for rolling statistics
            
        Returns:
            DataFrame with engineered features
        """
        if window_features is None:
            window_features = [3, 7, 14]
            
        self.lag_features = lag_features
        self.window_features = window_features
        self.target_name = target_col
        
        df = data.copy()
        
        # Create lag features
        for i in range(1, lag_features + 1):
            df[f'{target_col}_lag_{i}'] = df[target_col].shift(i)
            
        # Create rolling window features
        for window in window_features:
            df[f'{target_col}_rolling_mean_{window}'] = df[target_col].rolling(window=window).mean()
            df[f'{target_col}_rolling_std_{window}'] = df[target_col].rolling(window=window).std()
            df[f'{target_col}_rolling_min_{window}'] = df[target_col].rolling(window=window).min()
            df[f'{target_col}_rolling_max_{window}'] = df[target_col].rolling(window=window).max()
        
        # Create time-based features if index is datetime
        if isinstance(df.index, pd.DatetimeIndex):
            df['dayofweek'] = df.index.dayofweek
            df['month'] = df.index.month
            df['quarter'] = df.index.quarter
            df['dayofmonth'] = df.index.day
            df['weekofyear'] = df.index.isocalendar().week
        
        # Drop rows with NaN values created by lagging and windowing
        df = df.dropna()
        
        return df
    
    def prepare_data(self, data: pd.DataFrame, target_col: str, 
                    lag_features: int = 3, window_features: List[int] = None) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare data for training by creating features and separating target.
        
        Args:
            data: Input DataFrame
            target_col: Name of the target column
            lag_features: Number of lag features
            window_features: List of window sizes for rolling statistics
            
        Returns:
            Tuple of (features DataFrame, target Series)
        """
        # Create features
        df_features = self.create_features(data, target_col, lag_features, window_features)
        
        # Separate features and target
        y = df_features[target_col].copy()
        X = df_features.drop(columns=[target_col])
        
        self.feature_names = X.columns.tolist()
        
        return X, y
    
    def fit(self, X: pd.DataFrame, y: pd.Series):
        """
        Fit the forecasting model.
        
        Args:
            X: Features DataFrame
            y: Target Series
        """
        # Initialize model based on type
        if self.model_type == 'random_forest':
            default_params = {
                'n_estimators': 100,
                'max_depth': 10,
                'random_state': 42,
                'n_jobs': -1
            }
            default_params.update(self.model_params)
            self.model = RandomForestRegressor(**default_params)
            
        elif self.model_type == 'xgboost':
            default_params = {
                'n_estimators': 100,
                'max_depth': 6,
                'learning_rate': 0.1,
                'random_state': 42,
                'n_jobs': -1
            }
            default_params.update(self.model_params)
            self.model = xgb.XGBRegressor(**default_params)
            
        elif self.model_type == 'lightgbm':
            default_params = {
                'n_estimators': 100,
                'max_depth': -1,
                'learning_rate': 0.1,
                'random_state': 42,
                'n_jobs': -1
            }
            default_params.update(self.model_params)
            self.model = lgb.LGBMRegressor(**default_params)
        
        # Fit the model
        self.model.fit(X, y)
        self.is_fitted = True
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions using the fitted model.
        
        Args:
            X: Features DataFrame
            
        Returns:
            Array of predictions
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before making predictions")
            
        return self.model.predict(X)
    
    def forecast(self, data: pd.DataFrame, target_col: str, steps: int = 1) -> pd.DataFrame:
        """
        Generate multi-step ahead forecasts.
        
        Args:
            data: Historical data
            target_col: Target column name
            steps: Number of steps ahead to forecast
            
        Returns:
            DataFrame with forecasts
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before forecasting")
            
        # Prepare the latest data point for forecasting
        df = data.copy()
        forecasts = []
        
        for step in range(steps):
            # Create features for the current state
            df_features = self.create_features(df, target_col, self.lag_features, self.window_features)
            
            if len(df_features) == 0:
                raise ValueError("Insufficient data for creating features")
            
            # Get the latest features
            latest_features = df_features.drop(columns=[target_col]).iloc[-1:].values
            
            # Make prediction
            pred = self.model.predict(latest_features)[0]
            forecasts.append(pred)
            
            # Add prediction to the data for next iteration
            next_index = df.index[-1] + pd.Timedelta(days=1) if isinstance(df.index, pd.DatetimeIndex) else df.index[-1] + 1
            df.loc[next_index] = {target_col: pred}
        
        # Create forecast DataFrame
        if isinstance(data.index, pd.DatetimeIndex):
            forecast_index = pd.date_range(start=data.index[-1] + pd.Timedelta(days=1), periods=steps, freq='D')
        else:
            forecast_index = range(data.index[-1] + 1, data.index[-1] + steps + 1)
            
        forecast_df = pd.DataFrame({
            'forecast': forecasts
        }, index=forecast_index)
        
        return forecast_df
    
    def evaluate(self, y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model performance.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            
        Returns:
            Dictionary of evaluation metrics
        """
        metrics = {
            'mse': mean_squared_error(y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mae': mean_absolute_error(y_true, y_pred),
            'r2': r2_score(y_true, y_pred),
            'mape': np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        }
        
        return metrics
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get feature importance from the fitted model.
        
        Returns:
            DataFrame with feature names and importance scores
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before getting feature importance")
            
        if hasattr(self.model, 'feature_importances_'):
            importance_df = pd.DataFrame({
                'feature': self.feature_names,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            return importance_df
        else:
            raise AttributeError(f"Model type {self.model_type} does not support feature importance")
    
    def save_model(self, filepath: str):
        """
        Save the fitted model to disk.
        
        Args:
            filepath: Path to save the model
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before saving")
            
        import pickle
        
        model_data = {
            'model': self.model,
            'model_type': self.model_type,
            'feature_names': self.feature_names,
            'target_name': self.target_name,
            'lag_features': self.lag_features,
            'window_features': self.window_features,
            'is_fitted': self.is_fitted
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self, filepath: str):
        """
        Load a saved model from disk.
        
        Args:
            filepath: Path to the saved model
        """
        import pickle
        
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
            
        self.model = model_data['model']
        self.model_type = model_data['model_type']
        self.feature_names = model_data['feature_names']
        self.target_name = model_data['target_name']
        self.lag_features = model_data['lag_features']
        self.window_features = model_data['window_features']
        self.is_fitted = model_data['is_fitted']
    
    def cross_validate(self, data: pd.DataFrame, target_col: str, cv_splits: int = 5) -> Dict[str, List[float]]:
        """
        Perform time series cross-validation.
        
        Args:
            data: Input data
            target_col: Target column name
            cv_splits: Number of CV splits
            
        Returns:
            Dictionary with CV results
        """
        from sklearn.model_selection import TimeSeriesSplit
        
        # Prepare data
        X, y = self.prepare_data(data, target_col, self.lag_features, self.window_features)
        
        tscv = TimeSeriesSplit(n_splits=cv_splits)
        cv_results = {
            'mse': [],
            'rmse': [],
            'mae': [],
            'r2': [],
            'mape': []
        }
        
        for train_index, test_index in tscv.split(X):
            X_train, X_test = X.iloc[train_index], X.iloc[test_index]
            y_train, y_test = y.iloc[train_index], y.iloc[test_index]
            
            # Fit model
            self.fit(X_train, y_train)
            
            # Predict
            y_pred = self.predict(X_test)
            
            # Evaluate
            metrics = self.evaluate(y_test, y_pred)
            for key, value in metrics.items():
                cv_results[key].append(value)
        
        return cv_results
```