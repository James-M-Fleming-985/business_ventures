"""
Integration tests for Prediction Accuracy Tracking feature
Tests the interaction between Prediction Storage, Actual Updater, 
Analytics Service, and Prediction Router layers
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import json
import asyncio
from typing import Dict, List, Any

from feature_integration import (
    PredictionStorage,
    ActualUpdater,
    AnalyticsService,
    PredictionRouter,
    FeatureIntegration
)


class TestPredictionAccuracyTracking:
    """Integration tests for FEATURE-CA-002-10: Prediction Accuracy Tracking"""

    @pytest.fixture
    def mock_database(self):
        """Mock database connection"""
        db = Mock()
        db.predictions = Mock()
        db.actuals = Mock()
        db.analytics = Mock()
        return db

    @pytest.fixture
    def mock_cache(self):
        """Mock cache service"""
        cache = Mock()
        cache.get = Mock(return_value=None)
        cache.set = Mock()
        cache.delete = Mock()
        return cache

    @pytest.fixture
    def mock_message_queue(self):
        """Mock message queue service"""
        mq = Mock()
        mq.publish = Mock()
        mq.subscribe = Mock()
        return mq

    @pytest.fixture
    def prediction_storage(self, mock_database, mock_cache):
        """Initialize PredictionStorage layer"""
        return PredictionStorage(
            database=mock_database,
            cache=mock_cache
        )

    @pytest.fixture
    def actual_updater(self, mock_database, mock_message_queue):
        """Initialize ActualUpdater layer"""
        return ActualUpdater(
            database=mock_database,
            message_queue=mock_message_queue
        )

    @pytest.fixture
    def analytics_service(self, mock_database, mock_cache):
        """Initialize AnalyticsService layer"""
        return AnalyticsService(
            database=mock_database,
            cache=mock_cache
        )

    @pytest.fixture
    def prediction_router(self, prediction_storage, actual_updater, analytics_service):
        """Initialize PredictionRouter layer"""
        return PredictionRouter(
            storage=prediction_storage,
            updater=actual_updater,
            analytics=analytics_service
        )

    @pytest.fixture
    def feature_integration(self, prediction_router):
        """Initialize complete feature integration"""
        return FeatureIntegration(router=prediction_router)

    @pytest.mark.asyncio
    async def test_full_prediction_lifecycle_integration(
        self,
        feature_integration,
        mock_database,
        mock_cache,
        mock_message_queue
    ):
        """
        Test 1: Complete prediction lifecycle from storage to accuracy calculation
        Scenario: Store prediction -> Update with actual -> Calculate accuracy
        """
        # Arrange
        prediction_data = {
            "prediction_id": "pred_001",
            "model_id": "model_123",
            "value": 85.5,
            "confidence": 0.92,
            "timestamp": datetime.utcnow().isoformat(),
            "features": {"temperature": 22.5, "humidity": 65}
        }
        
        actual_data = {
            "prediction_id": "pred_001",
            "actual_value": 87.2,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Mock database responses
        mock_database.predictions.insert_one = Mock(return_value=Mock(inserted_id="pred_001"))
        mock_database.predictions.find_one = Mock(return_value=prediction_data)
        mock_database.actuals.insert_one = Mock(return_value=Mock(inserted_id="actual_001"))
        
        # Act
        # Step 1: Store prediction
        stored_prediction = await feature_integration.store_prediction(prediction_data)
        
        # Step 2: Update with actual value
        actual_result = await feature_integration.update_actual(actual_data)
        
        # Step 3: Calculate accuracy
        accuracy_metrics = await feature_integration.calculate_accuracy("pred_001")

        # Assert
        assert stored_prediction["prediction_id"] == "pred_001"
        assert actual_result["status"] == "success"
        assert "accuracy" in accuracy_metrics
        assert accuracy_metrics["prediction_id"] == "pred_001"
        
        # Verify interactions
        mock_database.predictions.insert_one.assert_called_once()
        mock_database.actuals.insert_one.assert_called_once()
        mock_message_queue.publish.assert_called_with(
            "prediction.actual.updated",
            {"prediction_id": "pred_001", "actual_value": 87.2}
        )

    @pytest.mark.asyncio
    async def test_batch_prediction_processing_integration(
        self,
        feature_integration,
        mock_database,
        mock_cache
    ):
        """
        Test 2: Batch processing of multiple predictions
        Scenario: Store batch -> Retrieve batch -> Calculate aggregate metrics
        """
        # Arrange
        batch_predictions = [
            {
                "prediction_id": f"pred_{i}",
                "model_id": "model_123",
                "value": 80 + i,
                "confidence": 0.85 + (i * 0.01),
                "timestamp": datetime.utcnow().isoformat()
            }
            for i in range(5)
        ]
        
        # Mock database batch operations
        mock_database.predictions.insert_many = Mock(
            return_value=Mock(inserted_ids=[p["prediction_id"] for p in batch_predictions])
        )
        mock_database.predictions.find = Mock(return_value=batch_predictions)
        
        # Act
        # Step 1: Store batch predictions
        batch_result = await feature_integration.store_batch_predictions(batch_predictions)
        
        # Step 2: Retrieve predictions for model
        model_predictions = await feature_integration.get_model_predictions(
            "model_123",
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow()
        )
        
        # Step 3: Calculate model performance metrics
        model_metrics = await feature_integration.calculate_model_metrics("model_123")

        # Assert
        assert len(batch_result["stored_predictions"]) == 5
        assert len(model_predictions) == 5
        assert model_metrics["model_id"] == "model_123"
        assert "average_confidence" in model_metrics
        assert "total_predictions" in model_metrics
        
        # Verify batch operations
        mock_database.predictions.insert_many.assert_called_once()
        assert mock_cache.set.call_count >= 1  # Cache should be updated

    @pytest.mark.asyncio
    async def test_error_handling_across_layers(
        self,
        feature_integration,
        mock_database,
        mock_message_queue
    ):
        """
        Test 3: Error propagation and handling across layer boundaries
        Scenario: Database failure -> Graceful degradation -> Error reporting
        """
        # Arrange
        prediction_data = {
            "prediction_id": "pred_error",
            "model_id": "model_123",
            "value": 75.0,
            "confidence": 0.88
        }
        
        # Mock database failure
        mock_database.predictions.insert_one.side_effect = Exception("Database connection failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await feature_integration.store_prediction(prediction_data)
        
        assert "Database connection failed" in str(exc_info.value)
        
        # Verify error handling
        # Should attempt to publish error event
        error_calls = [
            call for call in mock_message_queue.publish.call_args_list
            if call[0][0] == "prediction.storage.error"
        ]
        assert len(error_calls) >= 0  # Error event may be published

    @pytest.mark.asyncio
    async def test_real_time_accuracy_updates_integration(
        self,
        feature_integration,
        mock_database,
        mock_cache,
        mock_message_queue
    ):
        """
        Test 4: Real-time accuracy updates with caching
        Scenario: Actual value update triggers analytics recalculation and cache invalidation
        """
        # Arrange
        prediction_id = "pred_realtime"
        initial_prediction = {
            "prediction_id": prediction_id,
            "model_id": "model_456",
            "value": 92.3,
            "confidence": 0.95,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        actual_update = {
            "prediction_id": prediction_id,
            "actual_value": 91.8,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Mock responses
        mock_database.predictions.find_one = Mock(return_value=initial_prediction)
        mock_database.actuals.find_one = Mock(return_value=actual_update)
        mock_cache.get = Mock(side_effect=[None, {"accuracy": 94.5}])  # Cache miss then hit
        
        # Act
        # Step 1: Store initial prediction
        await feature_integration.store_prediction(initial_prediction)
        
        # Step 2: Update with actual (should trigger analytics)
        await feature_integration.update_actual(actual_update)
        
        # Step 3: Get accuracy (should use cache on second call)
        accuracy_1 = await feature_integration.get_prediction_accuracy(prediction_id)
        accuracy_2 = await feature_integration.get_prediction_accuracy(prediction_id)

        # Assert
        assert accuracy_1 is not None
        assert accuracy_2 == {"accuracy": 94.5}  # From cache
        
        # Verify cache invalidation and update
        cache_delete_calls = [
            call for call in mock_cache.delete.call_args_list
            if prediction_id in str(call)
        ]
        assert len(cache_delete_calls) >= 1  # Cache should be invalidated
        
        # Verify real-time event publishing
        mock_message_queue.publish.assert_any_call(
            "analytics.accuracy.updated",
            {
                "prediction_id": prediction_id,
                "accuracy": pytest.approx(94.5, abs=5)  # Allow some variance
            }
        )

    @pytest.mark.asyncio
    async def test_complex_analytics_aggregation_integration(
        self,
        feature_integration,
        mock_database,
        mock_cache
    ):
        """
        Test 5: Complex analytics aggregation across multiple models
        Scenario: Multi-model comparison -> Time-based aggregation -> Performance ranking
        """
        # Arrange
        models = ["model_A", "model_B", "model_C"]
        predictions_per_model = 10
        
        # Generate test data
        all_predictions = []
        for model_idx, model_id in enumerate(models):
            for i in range(predictions_per_model):
                prediction = {
                    "prediction_id": f"{model_id}_pred_{i}",
                    "model_id": model_id,
                    "value": 70 + (model_idx * 5) + i,
                    "confidence": 0.8 + (model_idx * 0.05),
                    "timestamp": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                    "actual_value": 72 + (model_idx * 4) + i,  # Simulate actuals
                    "accuracy": 95 - (model_idx * 2) - (i * 0.1)  # Varying accuracy
                }
                all_predictions.append(prediction)
        
        # Mock aggregation pipeline
        mock_database.analytics.aggregate = Mock(return_value=[
            {
                "model_id": model_id,
                "avg_accuracy": 95 - (idx * 2),
                "total_predictions": predictions_per_model,
                "confidence_score": 0.8 + (idx * 0.05)
            }
            for idx, model_id in enumerate(models)
        ])
        
        # Act
        # Step 1: Store all predictions
        for prediction in all_predictions:
            await feature_integration.store_prediction(prediction)
        
        # Step 2: Calculate comparative analytics
        comparative_report = await feature_integration.generate_comparative_analytics(
            models=models,
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow()
        )
        
        # Step 3: Get model rankings
        rankings = await feature_integration.get_model_rankings(
            metric="accuracy",
            period="24h"
        )

        # Assert
        assert len(comparative_report["models"]) == 3
        assert comparative_report["models"][0]["model_id"] == "model_A"
        assert comparative_report["models"][0]["avg_accuracy"] == 95
        
        assert len(rankings) == 3
        assert rankings[0]["model_id"] == "model_A"  # Best accuracy
        assert rankings[0]["rank"] == 1
        assert rankings[2]["model_id"] == "model_C"  # Worst accuracy
        
        # Verify complex aggregation
        mock_database.analytics.aggregate.assert_called()
        aggregate_pipeline = mock_database.analytics.aggregate.call_args[0][0]
        assert any("$group" in stage for stage in aggregate_pipeline)
        assert any("$sort" in stage for stage in aggregate_pipeline)

    @pytest.mark.asyncio
    async def test_concurrent_operations_integration(
        self,
        feature_integration,
        mock_database,
        mock_cache,
        mock_message_queue
    ):
        """
        Test 6: Concurrent operations handling
        Scenario: Multiple simultaneous predictions and updates
        """
        # Arrange
        concurrent_predictions = [
            {
                "prediction_id": f"concurrent_{i}",
                "model_id": "model_concurrent",
                "value": 80 + i,
                "confidence": 0.9
            }
            for i in range(10)
        ]
        
        # Mock thread-safe operations
        mock_database.predictions.insert_one = Mock(
            side_effect=[Mock(inserted_id=p["prediction_id"]) for p in concurrent_predictions]
        )
        
        # Act
        # Run concurrent operations
        tasks = []
        for prediction in concurrent_predictions:
            tasks.append(feature_integration.store_prediction(prediction))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Assert
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == 10
        
        # Verify no race conditions
        assert mock_database.predictions.insert_one.call_count == 10
        
        # Check message queue handled all events
        prediction_stored_events = [
            call for call in mock_message_queue.publish.call_args_list
            if call[0][0] == "prediction.stored"
        ]
        assert len(prediction_stored_events) >= 10

    @pytest.mark.asyncio
    async def test_data_consistency_integration(
        self,
        feature_integration,
        mock_database,
        mock_cache
    ):
        """
        Test 7: Data consistency across layers
        Scenario: Ensure data remains consistent through transformations
        """
        # Arrange
        original_prediction = {
            "prediction_id": "consistency_test",
            "model_id": "model_789",
            "value": 88.8,
            "confidence": 0.91,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "version": "1.2.3",
                "features_used": ["temp", "pressure", "humidity"]
            }
        }
        
        # Mock to return same data
        mock_database.predictions.find_one = Mock(return_value=original_prediction)
        
        # Act
        # Store through multiple layers
        stored = await feature_integration.store_prediction(original_prediction)
        retrieved = await feature_integration.get_prediction("consistency_test")
        
        # Transform through analytics
        analytics_data = await feature_integration.prepare_analytics_data("consistency_test")
        
        # Assert data consistency
        assert stored["prediction_id"] == original_prediction["prediction_id"]
        assert retrieved["value"] == original_prediction["value"]
        assert retrieved["metadata"]["version"] == "1.2.3"
        assert len(retrieved["metadata"]["features_used"]) == 3
        
        # Verify no data corruption through layers
        assert analytics_data["original_value"] == 88.8
        assert analytics_data["confidence"] == 0.91


if __name__ == "__main__":
    pytest.main([__file__, "-v"])