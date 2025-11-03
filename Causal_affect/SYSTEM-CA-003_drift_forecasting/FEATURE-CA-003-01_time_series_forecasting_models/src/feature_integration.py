"""
Feature Integration Module for Time-Series Forecasting Models
FEATURE ID: FEATURE-CA-003-01

This module orchestrates the integration of multiple forecasting layers to provide
comprehensive time-series forecasting capabilities.
"""

from pathlib import Path
import sys
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from layer implementations
from LAYER_CA_003_01_01_Statistical_Forecasting_Engine.src.implementation import (
    StatisticalForecastingEngine, TimeSeriesForecaster as StatisticalTimeSeriesForecaster
)
from LAYER_CA_003_01_02_ML_Forecasting_Engine.src.implementation import MLForecastingEngine
from LAYER_CA_003_01_03_Ensemble_Orchestrator.src.implementation import (
    EnsembleOrchestrator, ARIMAModel, ProphetModel, ExponentialSmoothingModel,
    XGBoostModel, RandomForestModel
)
from LAYER_CA_003_01_04_Validation__Backtesting.src.implementation import (
    TimeSeriesValidator, TimeSeriesForecaster as ValidationTimeSeriesForecaster,
    DriftDetector
)
from LAYER_CA_003_01_05_Forecast_API_Integration.src.implementation import (
    ForecastAPIIntegration, ForecastResult, ForecastValidator
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FeatureConfig:
    """Configuration for the Time-Series Forecasting Feature."""
    
    # Statistical forecasting config
    statistical_models: List[str] = field(default_factory=lambda: ['arima', 'exponential_smoothing'])
    
    # ML forecasting config
    ml_models: List[str] = field(default_factory=lambda: ['xgboost', 'random_forest'])
    
    # Ensemble config
    ensemble_method: str = 'weighted_average'
    ensemble_weights: Optional[Dict[str, float]] = None
    
    # Validation config
    validation_split: float = 0.2
    backtest_periods: int = 5
    
    # Forecast config
    forecast_horizon: int = 30
    confidence_level: float = 0.95
    
    # API config
    api_timeout: int = 60
    max_retries: int = 3


@dataclass
class FeatureResponse:
    """Unified response structure for feature operations."""
    
    success: bool
    operation: str
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class FeatureOrchestrator:
    """
    Main orchestrator for Time-Series Forecasting Models feature.
    
    This class coordinates the interaction between multiple forecasting layers
    to provide comprehensive time-series analysis and prediction capabilities.
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        """
        Initialize the feature orchestrator.
        
        Args:
            config: Feature configuration. Uses defaults if not provided.
        """
        self.config = config or FeatureConfig()
        self._initialized = False
        
        # Layer instances
        self.statistical_engine = None
        self.statistical_forecaster = None
        self.ml_engine = None
        self.ensemble_orchestrator = None
        self.validator = None
        self.validation_forecaster = None
        self.drift_detector = None
        self.api_integration = None
        self.forecast_validator = None
        
        # Initialize layers
        self._initialize_layers()
    
    def _initialize_layers(self) -> None:
        """Initialize all layer instances with error handling."""
        try:
            # Statistical Forecasting Engine
            self.statistical_engine = StatisticalForecastingEngine()
            self.statistical_forecaster = StatisticalTimeSeriesForecaster()
            
            # ML Forecasting Engine
            self.ml_engine = MLForecastingEngine()
            
            # Ensemble Orchestrator
            self.ensemble_orchestrator = EnsembleOrchestrator()
            
            # Validation & Backtesting
            self.validator = TimeSeriesValidator()
            self.validation_forecaster = ValidationTimeSeriesForecaster()
            self.drift_detector = DriftDetector()
            
            # Forecast API Integration
            self.api_integration = ForecastAPIIntegration()
            self.forecast_validator = ForecastValidator()
            
            self._initialized = True
            logger.info("All layers initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing layers: {str(e)}")
            self._initialized = False
            raise
    
    def train_models(self, data: pd.DataFrame, target_column: str) -> FeatureResponse:
        """
        Train all configured forecasting models.
        
        Args:
            data: Time-series data with datetime index
            target_column: Name of the target column to forecast
            
        Returns:
            FeatureResponse with training results
        """
        if not self._initialized:
            return FeatureResponse(
                success=False,
                operation="train_models",
                error="Feature orchestrator not properly initialized"
            )
        
        try:
            results = {}
            
            # Statistical models training
            logger.info("Training statistical models...")
            
            # Load data into statistical forecaster
            self.statistical_forecaster.load_data(data, target_column)
            
            # Fit statistical engine
            self.statistical_engine.fit(data[target_column])
            
            # ML models training
            logger.info("Training ML models...")
            
            # Prepare data for ML
            ml_data = self.ml_engine.prepare_data(data, target_column)
            features = self.ml_engine.create_features(ml_data)
            
            # Fit ML engine
            self.ml_engine.fit(features, ml_data[target_column])
            
            # Ensemble models training
            logger.info("Training ensemble models...")
            
            # Add models to ensemble
            if 'arima' in self.config.statistical_models:
                self.ensemble_orchestrator.add_model('arima', ARIMAModel())
            if 'prophet' in self.config.statistical_models:
                self.ensemble_orchestrator.add_model('prophet', ProphetModel())
            if 'exponential_smoothing' in self.config.statistical_models:
                self.ensemble_orchestrator.add_model('exp_smoothing', ExponentialSmoothingModel())
            if 'xgboost' in self.config.ml_models:
                self.ensemble_orchestrator.add_model('xgboost', XGBoostModel())
            if 'random_forest' in self.config.ml_models:
                self.ensemble_orchestrator.add_model('random_forest', RandomForestModel())
            
            # Fit ensemble
            self.ensemble_orchestrator.fit(data, target_column)
            
            # Add models to validation forecaster
            for model_type in self.config.statistical_models:
                if model_type == 'arima':
                    from LAYER_CA_003_01_04_Validation__Backtesting.src.implementation import ARIMAModel as ValidationARIMA
                    self.validation_forecaster.add_model(ValidationARIMA())
                elif model_type == 'exponential_smoothing':
                    from LAYER_CA_003_01_04_Validation__Backtesting.src.implementation import ExponentialSmoothingModel as ValidationExpSmoothing
                    self.validation_forecaster.add_model(ValidationExpSmoothing())
            
            # Fit validation models
            self.validation_forecaster.fit_models(data, target_column)
            
            results['models_trained'] = len(self.config.statistical_models) + len(self.config.ml_models)
            results['training_complete'] = True
            
            return FeatureResponse(
                success=True,
                operation="train_models",
                data=results,
                metadata={
                    'statistical_models': self.config.statistical_models,
                    'ml_models': self.config.ml_models,
                    'ensemble_method': self.config.ensemble_method
                }
            )
            
        except Exception as e:
            logger.error(f"Error training models: {str(e)}")
            return FeatureResponse(
                success=False,
                operation="train_models",
                error=str(e)
            )
    
    def generate_forecast(self, horizon: Optional[int] = None) -> FeatureResponse:
        """
        Generate forecasts using all trained models.
        
        Args:
            horizon: Forecast horizon. Uses config default if not provided.
            
        Returns:
            FeatureResponse with forecast results
        """
        if not self._initialized:
            return FeatureResponse(
                success=False,
                operation="generate_forecast",
                error="Feature orchestrator not properly initialized"
            )
        
        try:
            horizon = horizon or self.config.forecast_horizon
            forecasts = {}
            
            # Statistical forecasts
            logger.info("Generating statistical forecasts...")
            stat_forecast = self.statistical_engine.predict(steps=horizon)
            forecasts['statistical'] = stat_forecast
            
            # ML forecasts
            logger.info("Generating ML forecasts...")
            ml_forecast = self.ml_engine.forecast(horizon=horizon)
            forecasts['ml'] = ml_forecast
            
            # Ensemble forecast
            logger.info("Generating ensemble forecast...")
            ensemble_forecast = self.ensemble_orchestrator.predict(
                horizon=horizon,
                weights=self.config.ensemble_weights
            )
            forecasts['ensemble'] = ensemble_forecast
            
            # Validation forecaster forecast
            validation_forecast = self.validation_forecaster.forecast(steps=horizon)
            forecasts['validation'] = validation_forecast
            
            # API integration forecast
            api_forecast_result = self.api_integration.forecast(
                data=forecasts['ensemble'],
                horizon=horizon
            )
            
            return FeatureResponse(
                success=True,
                operation="generate_forecast",
                data=forecasts,
                metadata={
                    'horizon': horizon,
                    'confidence_level': self.config.confidence_level,
                    'forecast_timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating forecast: {str(e)}")
            return FeatureResponse(
                success=False,
                operation="generate_forecast",
                error=str(e)
            )
    
    def validate_forecast(self, data: pd.DataFrame, target_column: str) -> FeatureResponse:
        """
        Validate forecasts using backtesting and cross-validation.
        
        Args:
            data: Historical data for validation
            target_column: Target column name
            
        Returns:
            FeatureResponse with validation results
        """
        if not self._initialized:
            return FeatureResponse(
                success=False,
                operation="validate_forecast",
                error="Feature orchestrator not properly initialized"
            )
        
        try:
            validation_results = {}
            
            # Validate data quality
            logger.info("Validating data quality...")
            data_validation = self.validator.validate_data(data)
            validation_results['data_quality'] = data_validation
            
            # Backtesting
            logger.info("Performing backtesting...")
            backtest_results = self.validator.backtest(
                data=data,
                target_col=target_column,
                periods=self.config.backtest_periods
            )
            validation_results['backtest'] = backtest_results
            
            # Cross-validation for ML models
            logger.info("Performing cross-validation...")
            cv_results = self.ml_engine.cross_validate(
                n_splits=self.config.backtest_periods
            )
            validation_results['cross_validation'] = cv_results
            
            # Drift detection
            logger.info("Checking for drift...")
            drift_results = self.drift_detector.detect_drift(
                historical_data=data[target_column],
                recent_data=data[target_column].tail(30)
            )
            validation_results['drift_detection'] = drift_results
            
            # Ensemble evaluation
            ensemble_eval = self.ensemble_orchestrator.evaluate(
                test_data=data.tail(int(len(data) * self.config.validation_split))
            )
            validation_results['ensemble_performance'] = ensemble_eval
            
            # Forecast validation
            forecast_validation = self.forecast_validator.validate_forecast(
                forecast_data=validation_results['backtest'],
                actual_data=data[target_column]
            )
            validation_results['forecast_validation'] = forecast_validation
            
            return FeatureResponse(
                success=True,
                operation="validate_forecast",
                data=validation_results,
                metadata={
                    'validation_split': self.config.validation_split,
                    'backtest_periods': self.config.backtest_periods
                }
            )
            
        except Exception as e:
            logger.error(f"Error validating forecast: {str(e)}")
            return FeatureResponse(
                success=False,
                operation="validate_forecast",
                error=str(e)
            )
    
    def batch_forecast(self, datasets: List[pd.DataFrame], target_columns: List[str]) -> FeatureResponse:
        """
        Generate forecasts for multiple time series.
        
        Args:
            datasets: List of dataframes containing time series
            target_columns: List of target column names
            
        Returns:
            FeatureResponse with batch forecast results
        """
        if not self._initialized:
            return FeatureResponse(
                success=False,
                operation="batch_forecast",
                error="Feature orchestrator not properly initialized"
            )
        
        try:
            batch_results = []
            
            # Prepare batch data
            batch_data = []
            for i, (df, target) in enumerate(zip(datasets, target_columns)):
                batch_data.append({
                    'id': f'series_{i}',
                    'data': df,
                    'target': target
                })
            
            # Generate batch forecasts
            logger.info(f"Generating forecasts for {len(batch_data)} series...")
            batch_forecast_results = self.api_integration.batch_forecast(
                batch_data=batch_data,
                horizon=self.config.forecast_horizon
            )
            
            return FeatureResponse(
                success=True,
                operation="batch_forecast",
                data=batch_forecast_results,
                metadata={
                    'num_series': len(datasets),
                    'horizon': self.config.forecast_horizon
                }
            )
            
        except Exception as e:
            logger.error(f"Error in batch forecast: {str(e)}")
            return FeatureResponse(
                success=False,
                operation="batch_forecast",
                error=str(e)
            )
    
    def get_model_diagnostics(self) -> FeatureResponse:
        """
        Get comprehensive diagnostics from all models.
        
        Returns:
            FeatureResponse with model diagnostics
        """
        if not self._initialized:
            return FeatureResponse(
                success=False,
                operation="get_model_diagnostics",
                error="Feature orchestrator not properly initialized"
            )
        
        try:
            diagnostics = {}
            
            # Statistical model summary
            stat_summary = self.statistical_engine.get_model_summary()
            diagnostics['statistical_models'] = stat_summary
            
            # ML feature importance
            feature_importance = self.ml_engine.get_feature_importance()
            diagnostics['ml_feature_importance'] = feature_importance
            
            # Ensemble model importance
            model_importance = self.ensemble_orchestrator.get_model_importance()
            diagnostics['ensemble_weights'] = model_importance
            
            # Model comparison
            comparison = self.statistical_forecaster.compare_models()
            diagnostics['model_comparison'] = comparison
            
            return FeatureResponse(
                success=True,
                operation="get_model_diagnostics",
                data=diagnostics,
                metadata={
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting model diagnostics: {str(e)}")
            return FeatureResponse(
                success=False,
                operation="get_model_diagnostics",
                error=str(e)
            )
    
    def save_models(self, path: str) -> FeatureResponse:
        """
        Save all trained models to disk.
        
        Args:
            path: Directory path to save models
            
        Returns:
            FeatureResponse with save status
        """
        if not self._initialized:
            return FeatureResponse(
                success=False,
                operation="save_models",
                error="Feature orchestrator not properly initialized"
            )
        
        try:
            save_path = Path(path)
            save_path.mkdir(parents=True, exist_ok=True)
            
            # Save ML model
            ml_path = save_path / "ml_model.pkl"
            self.ml_engine.save_model(str(ml_path))
            
            # Save ensemble
            ensemble_path = save_path / "ensemble_model.pkl"
            self.ensemble_orchestrator.save(str(ensemble_path))
            
            return FeatureResponse(
                success=True,
                operation="save_models",
                data={'saved_path': str(save_path)},
                metadata={
                    'models_saved': ['ml_model', 'ensemble_model']
                }
            )
            
        except Exception as e:
            logger.error(f"Error saving models: {str(e)}")
            return FeatureResponse(
                success=False,
                operation="save_models",
                error=str(e)
            )
    
    def load_models(self, path: str) -> FeatureResponse:
        """
        Load previously saved models.
        
        Args:
            path: Directory path containing saved models
            
        Returns:
            FeatureResponse with load status
        """
        if not self._initialized:
            return FeatureResponse(
                success=False,
                operation="load_models",
                error="Feature orchestrator not properly initialized"
            )
        
        try:
            load_path = Path(path)
            
            # Load ML model
            ml_path = load_path / "ml_model.pkl"
            if ml_path.exists():
                self.ml_engine.load_model(str(ml_path))
            
            # Load ensemble
            ensemble_path = load_path / "ensemble_model.pkl"
            if ensemble_path.exists():
                self.ensemble_orchestrator.load(str(ensemble_path))
            
            return FeatureResponse(
                success=True,
                operation="load_models",
                data={'loaded_from': str(load_path)},
                metadata={
                    'models_loaded': ['ml_model', 'ensemble_model']
                }
            )
            
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            return FeatureResponse(
                success=False,
                operation="load_models",
                error=str(e)
            )
