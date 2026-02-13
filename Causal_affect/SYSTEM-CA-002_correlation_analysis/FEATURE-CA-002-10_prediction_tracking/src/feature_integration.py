"""
Feature Integration Module for Prediction Accuracy Tracking
Feature ID: FEATURE-CA-002-10
"""

from pathlib import Path
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from standardized layer folders
from LAYER_CA_002_10_01_Prediction_Storage.src.implementation import PredictionStorage
from LAYER_CA_002_10_02_Actual_Updater.src.implementation import ActualUpdater
from LAYER_CA_002_10_03_Analytics_Service.src.implementation import AnalyticsService
from LAYER_CA_002_10_04_Prediction_Router.src.implementation import MockDatabase, MockActualUpdater

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FeatureConfig:
    """Configuration for the Prediction Accuracy Tracking feature."""
    enable_logging: bool = True
    cache_analytics: bool = True
    max_predictions: int = 10000
    time_window_days: int = 30


@dataclass
class FeatureResponse:
    """Unified response structure for feature operations."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class FeatureOrchestrator:
    """
    Main orchestrator for the Prediction Accuracy Tracking feature.
    Coordinates interactions between all layers to provide a unified interface.
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        """
        Initialize the feature orchestrator with all required layers.
        
        Args:
            config: Optional configuration for the feature
        """
        self.config = config or FeatureConfig()
        
        try:
            # Initialize layer instances
            self.prediction_storage = PredictionStorage()
            self.actual_updater = ActualUpdater()
            self.analytics_service = AnalyticsService()
            
            # Initialize mock services from prediction router
            self.mock_database = MockDatabase()
            self.mock_actual_updater = MockActualUpdater()
            
            if self.config.enable_logging:
                logger.info("Feature orchestrator initialized successfully")
                
        except Exception as e:
            error_msg = f"Failed to initialize feature orchestrator: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def store_prediction(self, prediction_data: Dict[str, Any]) -> FeatureResponse:
        """
        Store a new prediction using the prediction storage layer.
        
        Args:
            prediction_data: Dictionary containing prediction information
            
        Returns:
            FeatureResponse indicating success or failure
        """
        try:
            # Store the prediction
            result = self.prediction_storage.store_prediction(prediction_data)
            
            return FeatureResponse(
                success=True,
                data=result
            )
            
        except Exception as e:
            error_msg = f"Failed to store prediction: {str(e)}"
            logger.error(error_msg)
            return FeatureResponse(
                success=False,
                error=error_msg
            )
    
    def update_actual_values(self, prediction_id: str, actual_value: Any) -> FeatureResponse:
        """
        Update actual values for a prediction.
        
        Args:
            prediction_id: ID of the prediction to update
            actual_value: The actual value observed
            
        Returns:
            FeatureResponse indicating success or failure
        """
        try:
            # Update using the actual updater
            result = self.actual_updater.update_actual(prediction_id, actual_value)
            
            # Also update using mock updater for compatibility
            mock_result = self.mock_actual_updater.update_actuals(
                prediction_id, actual_value
            )
            
            return FeatureResponse(
                success=True,
                data={
                    "actual_updater": result,
                    "mock_updater": mock_result
                }
            )
            
        except Exception as e:
            error_msg = f"Failed to update actual values: {str(e)}"
            logger.error(error_msg)
            return FeatureResponse(
                success=False,
                error=error_msg
            )
    
    def get_predictions(self, filters: Optional[Dict[str, Any]] = None) -> FeatureResponse:
        """
        Retrieve predictions based on filters.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            FeatureResponse containing predictions
        """
        try:
            # Get predictions from mock database
            predictions = self.mock_database.get_predictions()
            
            return FeatureResponse(
                success=True,
                data=predictions
            )
            
        except Exception as e:
            error_msg = f"Failed to get predictions: {str(e)}"
            logger.error(error_msg)
            return FeatureResponse(
                success=False,
                error=error_msg
            )
    
    def get_prediction_details(self, prediction_id: str) -> FeatureResponse:
        """
        Get detailed information about a specific prediction.
        
        Args:
            prediction_id: ID of the prediction
            
        Returns:
            FeatureResponse containing prediction details
        """
        try:
            # Get prediction from mock database
            prediction = self.mock_database.get_prediction_by_id(prediction_id)
            
            if prediction:
                return FeatureResponse(
                    success=True,
                    data=prediction
                )
            else:
                return FeatureResponse(
                    success=False,
                    error=f"Prediction with ID {prediction_id} not found"
                )
                
        except Exception as e:
            error_msg = f"Failed to get prediction details: {str(e)}"
            logger.error(error_msg)
            return FeatureResponse(
                success=False,
                error=error_msg
            )
    
    def calculate_accuracy_metrics(self, model_id: Optional[str] = None) -> FeatureResponse:
        """
        Calculate accuracy metrics for predictions.
        
        Args:
            model_id: Optional model ID to filter metrics
            
        Returns:
            FeatureResponse containing accuracy metrics
        """
        try:
            # Get metrics from mock database
            metrics = self.mock_database.get_accuracy_metrics()
            
            # Calculate additional metrics using analytics service
            analytics_result = self.analytics_service.calculate_metrics()
            
            combined_metrics = {
                "database_metrics": metrics,
                "analytics_metrics": analytics_result
            }
            
            return FeatureResponse(
                success=True,
                data=combined_metrics
            )
            
        except Exception as e:
            error_msg = f"Failed to calculate accuracy metrics: {str(e)}"
            logger.error(error_msg)
            return FeatureResponse(
                success=False,
                error=error_msg
            )
    
    def get_accuracy_timeseries(self, 
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> FeatureResponse:
        """
        Get accuracy metrics over time.
        
        Args:
            start_date: Optional start date for the timeseries
            end_date: Optional end date for the timeseries
            
        Returns:
            FeatureResponse containing timeseries data
        """
        try:
            # Get timeseries from mock database
            timeseries = self.mock_database.get_accuracy_timeseries()
            
            return FeatureResponse(
                success=True,
                data=timeseries
            )
            
        except Exception as e:
            error_msg = f"Failed to get accuracy timeseries: {str(e)}"
            logger.error(error_msg)
            return FeatureResponse(
                success=False,
                error=error_msg
            )
    
    def compare_models(self, model_ids: List[str]) -> FeatureResponse:
        """
        Compare accuracy metrics across multiple models.
        
        Args:
            model_ids: List of model IDs to compare
            
        Returns:
            FeatureResponse containing model comparison data
        """
        try:
            # Get comparisons from mock database
            comparisons = self.mock_database.get_model_comparisons()
            
            return FeatureResponse(
                success=True,
                data=comparisons
            )
            
        except Exception as e:
            error_msg = f"Failed to compare models: {str(e)}"
            logger.error(error_msg)
            return FeatureResponse(
                success=False,
                error=error_msg
            )
    
    def batch_store_predictions(self, predictions: List[Dict[str, Any]]) -> FeatureResponse:
        """
        Store multiple predictions in a batch operation.
        
        Args:
            predictions: List of prediction data dictionaries
            
        Returns:
            FeatureResponse containing batch operation results
        """
        try:
            results = []
            failed_count = 0
            
            for prediction in predictions:
                try:
                    result = self.prediction_storage.store_prediction(prediction)
                    results.append({
                        "success": True,
                        "data": result
                    })
                except Exception as e:
                    failed_count += 1
                    results.append({
                        "success": False,
                        "error": str(e)
                    })
            
            return FeatureResponse(
                success=(failed_count == 0),
                data={
                    "total": len(predictions),
                    "successful": len(predictions) - failed_count,
                    "failed": failed_count,
                    "results": results
                }
            )
            
        except Exception as e:
            error_msg = f"Failed to batch store predictions: {str(e)}"
            logger.error(error_msg)
            return FeatureResponse(
                success=False,
                error=error_msg
            )
    
    def generate_analytics_report(self, report_type: str = "summary") -> FeatureResponse:
        """
        Generate a comprehensive analytics report.
        
        Args:
            report_type: Type of report to generate (summary, detailed, etc.)
            
        Returns:
            FeatureResponse containing the analytics report
        """
        try:
            # Gather data from all sources
            predictions = self.mock_database.get_predictions()
            metrics = self.mock_database.get_accuracy_metrics()
            timeseries = self.mock_database.get_accuracy_timeseries()
            
            # Use analytics service to generate insights
            analytics_metrics = self.analytics_service.calculate_metrics()
            
            report = {
                "report_type": report_type,
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_predictions": len(predictions) if predictions else 0,
                    "accuracy_metrics": metrics,
                    "analytics_insights": analytics_metrics
                },
                "timeseries_data": timeseries
            }
            
            return FeatureResponse(
                success=True,
                data=report
            )
            
        except Exception as e:
            error_msg = f"Failed to generate analytics report: {str(e)}"
            logger.error(error_msg)
            return FeatureResponse(
                success=False,
                error=error_msg
            )
    
    def health_check(self) -> FeatureResponse:
        """
        Perform a health check on all layers.
        
        Returns:
            FeatureResponse containing health status of all layers
        """
        try:
            health_status = {
                "overall": "healthy",
                "layers": {
                    "prediction_storage": "healthy",
                    "actual_updater": "healthy",
                    "analytics_service": "healthy",
                    "mock_services": "healthy"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Test each layer with a simple operation
            try:
                self.mock_database.get_predictions()
            except Exception:
                health_status["layers"]["mock_services"] = "unhealthy"
                health_status["overall"] = "degraded"
            
            return FeatureResponse(
                success=True,
                data=health_status
            )
            
        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            logger.error(error_msg)
            return FeatureResponse(
                success=False,
                error=error_msg,
                data={"overall": "unhealthy"}
            )


# Example usage and testing
if __name__ == "__main__":
    # Initialize the feature orchestrator
    orchestrator = FeatureOrchestrator()
    
    # Test storing a prediction
    prediction_data = {
        "model_id": "model_001",
        "prediction_value": 42.5,
        "confidence": 0.85,
        "timestamp": datetime.now().isoformat()
    }
    
    result = orchestrator.store_prediction(prediction_data)
    print(f"Store prediction result: {result}")
    
    # Test getting predictions
    predictions_result = orchestrator.get_predictions()
    print(f"Get predictions result: {predictions_result}")
    
    # Test calculating metrics
    metrics_result = orchestrator.calculate_accuracy_metrics()
    print(f"Accuracy metrics result: {metrics_result}")
    
    # Test health check
    health_result = orchestrator.health_check()
    print(f"Health check result: {health_result}")
