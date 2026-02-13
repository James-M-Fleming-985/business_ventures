"""
End-to-End tests for Prediction Accuracy Tracking feature
Feature ID: FEATURE-CA-002-10
"""

import pytest
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import uuid


class TestPredictionAccuracyTrackingE2E:
    """End-to-end tests for prediction accuracy tracking system"""
    
    BASE_URL = "http://localhost:8000/api/v1"
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authentication headers for API requests"""
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            json={"username": "test_user", "password": "test_password"}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def cleanup_predictions(self, auth_headers):
        """Cleanup test predictions after each test"""
        created_predictions = []
        yield created_predictions
        
        # Cleanup
        for prediction_id in created_predictions:
            requests.delete(
                f"{self.BASE_URL}/predictions/{prediction_id}",
                headers=auth_headers
            )
    
    def wait_for_processing(self, prediction_id: str, auth_headers: Dict, 
                          timeout: int = 30) -> bool:
        """Wait for prediction processing to complete"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = requests.get(
                f"{self.BASE_URL}/predictions/{prediction_id}/status",
                headers=auth_headers
            )
            if response.status_code == 200:
                status = response.json()["status"]
                if status in ["completed", "failed"]:
                    return status == "completed"
            time.sleep(1)
        return False
    
    @pytest.mark.e2e
    def test_complete_prediction_accuracy_workflow_success(self, auth_headers, cleanup_predictions):
        """
        Test complete workflow: Create predictions -> Submit actuals -> Calculate accuracy -> View reports
        
        Scenario:
        1. Submit multiple predictions for different models
        2. Wait for predictions to be processed
        3. Submit actual outcomes
        4. Verify accuracy calculations
        5. Generate and verify accuracy reports
        """
        # Step 1: Create predictions for multiple models
        models = ["model_v1", "model_v2", "model_v3"]
        predictions = []
        
        for model_id in models:
            for i in range(5):
                prediction_data = {
                    "model_id": model_id,
                    "prediction_type": "classification",
                    "input_data": {
                        "feature_1": 10.5 + i,
                        "feature_2": 20.3 - i,
                        "feature_3": i * 2.1
                    },
                    "predicted_value": "class_A" if i % 2 == 0 else "class_B",
                    "confidence": 0.85 + (i * 0.02),
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": {
                        "version": "1.0",
                        "environment": "production"
                    }
                }
                
                response = requests.post(
                    f"{self.BASE_URL}/predictions",
                    json=prediction_data,
                    headers=auth_headers
                )
                assert response.status_code == 201
                prediction = response.json()
                predictions.append(prediction)
                cleanup_predictions.append(prediction["prediction_id"])
        
        # Step 2: Wait for all predictions to be processed
        for prediction in predictions:
            assert self.wait_for_processing(
                prediction["prediction_id"], 
                auth_headers
            ), f"Prediction {prediction['prediction_id']} processing timeout"
        
        # Step 3: Submit actual outcomes
        actuals = []
        for idx, prediction in enumerate(predictions):
            # Simulate some correct and incorrect predictions
            actual_value = prediction["predicted_value"] if idx % 3 != 0 else "class_C"
            
            actual_data = {
                "prediction_id": prediction["prediction_id"],
                "actual_value": actual_value,
                "observed_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "source": "manual_verification",
                    "verified_by": "test_system"
                }
            }
            
            response = requests.post(
                f"{self.BASE_URL}/predictions/{prediction['prediction_id']}/actual",
                json=actual_data,
                headers=auth_headers
            )
            assert response.status_code == 200
            actuals.append(response.json())
        
        # Step 4: Verify accuracy calculations for each model
        for model_id in models:
            response = requests.get(
                f"{self.BASE_URL}/models/{model_id}/accuracy",
                params={
                    "start_date": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                    "end_date": datetime.utcnow().isoformat()
                },
                headers=auth_headers
            )
            assert response.status_code == 200
            
            accuracy_data = response.json()
            assert "accuracy" in accuracy_data
            assert "precision" in accuracy_data
            assert "recall" in accuracy_data
            assert "f1_score" in accuracy_data
            assert "total_predictions" in accuracy_data
            assert accuracy_data["total_predictions"] == 5
            
            # Verify accuracy is calculated correctly
            # For our test data, model should have ~66.7% accuracy (2 wrong out of 5)
            assert 0.6 <= accuracy_data["accuracy"] <= 0.7
        
        # Step 5: Generate and verify accuracy report
        response = requests.post(
            f"{self.BASE_URL}/reports/accuracy",
            json={
                "model_ids": models,
                "start_date": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "report_type": "detailed",
                "include_confusion_matrix": True
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        
        report = response.json()
        assert "report_id" in report
        assert "generated_at" in report
        assert "models" in report
        assert len(report["models"]) == 3
        
        for model_report in report["models"]:
            assert "model_id" in model_report
            assert "accuracy_metrics" in model_report
            assert "confusion_matrix" in model_report
    
    @pytest.mark.e2e
    def test_real_time_accuracy_tracking_with_drift_detection(self, auth_headers, cleanup_predictions):
        """
        Test real-time accuracy tracking with performance drift detection
        
        Scenario:
        1. Submit predictions in batches over time
        2. Submit actuals with degrading accuracy
        3. Verify drift detection triggers
        4. Check alerts are generated
        5. Verify accuracy trends
        """
        model_id = "drift_test_model"
        
        # Phase 1: Good performance (90% accuracy)
        phase1_predictions = []
        for i in range(10):
            prediction_data = {
                "model_id": model_id,
                "prediction_type": "binary",
                "input_data": {"features": [i, i*2, i*3]},
                "predicted_value": 1 if i < 5 else 0,
                "confidence": 0.9,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = requests.post(
                f"{self.BASE_URL}/predictions",
                json=prediction_data,
                headers=auth_headers
            )
            assert response.status_code == 201
            prediction = response.json()
            phase1_predictions.append(prediction)
            cleanup_predictions.append(prediction["prediction_id"])
        
        # Submit actuals for phase 1 (90% correct)
        for idx, prediction in enumerate(phase1_predictions):
            actual = prediction["predicted_value"] if idx != 5 else (1 - prediction["predicted_value"])
            response = requests.post(
                f"{self.BASE_URL}/predictions/{prediction['prediction_id']}/actual",
                json={"actual_value": actual, "observed_at": datetime.utcnow().isoformat()},
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Check baseline accuracy
        response = requests.get(
            f"{self.BASE_URL}/models/{model_id}/accuracy",
            params={"window": "1h"},
            headers=auth_headers
        )
        assert response.status_code == 200
        baseline_accuracy = response.json()["accuracy"]
        assert baseline_accuracy >= 0.85
        
        # Phase 2: Degraded performance (40% accuracy)
        time.sleep(2)  # Simulate time passing
        
        phase2_predictions = []
        for i in range(10):
            prediction_data = {
                "model_id": model_id,
                "prediction_type": "binary",
                "input_data": {"features": [i+10, i*2+10, i*3+10]},
                "predicted_value": 1 if i < 5 else 0,
                "confidence": 0.85,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = requests.post(
                f"{self.BASE_URL}/predictions",
                json=prediction_data,
                headers=auth_headers
            )
            assert response.status_code == 201
            prediction = response.json()
            phase2_predictions.append(prediction)
            cleanup_predictions.append(prediction["prediction_id"])
        
        # Submit actuals for phase 2 (40% correct - significant degradation)
        for idx, prediction in enumerate(phase2_predictions):
            # Only 4 out of 10 predictions are correct
            actual = prediction["predicted_value"] if idx < 4 else (1 - prediction["predicted_value"])
            response = requests.post(
                f"{self.BASE_URL}/predictions/{prediction['prediction_id']}/actual",
                json={"actual_value": actual, "observed_at": datetime.utcnow().isoformat()},
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Check for drift detection
        response = requests.get(
            f"{self.BASE_URL}/models/{model_id}/drift-status",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        drift_status = response.json()
        assert drift_status["drift_detected"] == True
        assert drift_status["severity"] in ["high", "critical"]
        assert "drift_score" in drift_status
        assert drift_status["drift_score"] > 0.3
        
        # Check if alerts were generated
        response = requests.get(
            f"{self.BASE_URL}/alerts",
            params={
                "model_id": model_id,
                "alert_type": "accuracy_drift",
                "start_time": (datetime.utcnow() - timedelta(minutes=5)).isoformat()
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        
        alerts = response.json()
        assert len(alerts) > 0
        assert alerts[0]["alert_type"] == "accuracy_drift"
        assert alerts[0]["severity"] in ["high", "critical"]
        
        # Verify accuracy trends
        response = requests.get(
            f"{self.BASE_URL}/models/{model_id}/accuracy-trends",
            params={
                "granularity": "5m",
                "duration": "1h"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        
        trends = response.json()
        assert "data_points" in trends
        assert len(trends["data_points"]) >= 2
        
        # Verify accuracy degradation in trends
        early_accuracy = trends["data_points"][0]["accuracy"]
        latest_accuracy = trends["data_points"][-1]["accuracy"]
        assert latest_accuracy < early_accuracy * 0.7  # At least 30% degradation
    
    @pytest.mark.e2e
    def test_multi_metric_accuracy_tracking_with_custom_thresholds(self, auth_headers, cleanup_predictions):
        """
        Test tracking multiple accuracy metrics with custom thresholds and automated actions
        
        Scenario:
        1. Configure custom accuracy thresholds for a model
        2. Submit multi-class predictions
        3. Submit actuals that trigger threshold violations
        4. Verify automated actions (model deactivation, notifications)
        5. Test threshold update and re-evaluation
        """
        model_id = "threshold_test_model"
        
        # Step 1: Configure custom accuracy thresholds
        threshold_config = {
            "model_id": model_id,
            "thresholds": {
                "accuracy": {
                    "min": 0.85,
                    "warning": 0.88,
                    "target": 0.92
                },
                "precision": {
                    "min": 0.80,
                    "warning": 0.85,
                    "target": 0.90
                },
                "recall": {
                    "min": 0.75,
                    "warning": 0.80,
                    "target": 0.85
                }
            },
            "actions": {
                "below_min": ["deactivate_model", "send_alert", "trigger_retraining"],
                "below_warning": ["send_warning", "increase_monitoring"],
                "check_interval_minutes": 5
            }
        }
        
        response = requests.post(
            f"{self.BASE_URL}/models/{model_id}/accuracy-thresholds",
            json=threshold_config,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Step 2: Submit multi-class predictions
        classes = ["class_A", "class_B", "class_C", "class_D"]
        predictions = []
        
        # Create 100 predictions distributed across classes
        for i in range(100):
            predicted_class = classes[i % 4]
            confidence = 0.7 + (i % 10) * 0.03
            
            prediction_data = {
                "model_id": model_id,
                "prediction_type": "multiclass",
                "input_data": {
                    "text": f"Sample text {i}",
                    "category": i % 5,
                    "score": i * 1.5
                },
                "predicted_value": predicted_class,
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat(),
                "probabilities": {
                    "class_A": 0.25 + (0.5 if predicted_class == "class_A" else 0),
                    "class_B": 0.25 + (0.5 if predicted_class == "class_B" else 0),
                    "class_C": 0.25 + (0.5 if predicted_class == "class_C" else 0),
                    "class_D": 0.25 + (0.5 if predicted_class == "class_D" else 0)
                }
            }
            
            response = requests.post(
                f"{self.BASE_URL}/predictions",
                json=prediction_data,
                headers=auth_headers
            )
            assert response.status_code == 201
            predictions.append(response.json())
            cleanup_predictions.append(response.json()["prediction_id"])
        
        # Step 3: Submit actuals that will trigger threshold violations
        # Create a pattern that results in ~70% accuracy (below minimum threshold)
        for idx, prediction in enumerate(predictions):
            # 70% correct predictions
            if idx < 70:
                actual = prediction["predicted_value"]
            else:
                # Make these predictions wrong, rotating through other classes
                wrong_classes = [c for c in classes if c != prediction["predicted_value"]]
                actual = wrong_classes[idx % 3]
            
            response = requests.post(
                f"{self.BASE_URL}/predictions/{prediction['prediction_id']}/actual",
                json={
                    "actual_value": actual,
                    "observed_at": datetime.utcnow().isoformat()
                },
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Wait for threshold evaluation
        time.sleep(2)
        
        # Step 4: Verify automated actions
        # Check if model was deactivated
        response = requests.get(
            f"{self.BASE_URL}/models/{model_id}/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        model_status = response.json()
        assert model_status["status"] == "deactivated"
        assert model_status["reason"] == "accuracy_threshold_violation"
        
        # Check for alerts
        response = requests.get(
            f"{self.BASE_URL}/alerts",
            params={
                "model_id": model_id,
                "alert_type": "threshold_violation",
                "limit": 10
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        alerts = response.json()
        assert len(alerts) > 0
        
        threshold_alert = alerts[0]
        assert threshold_alert["severity"] == "critical"
        assert "accuracy" in threshold_alert["violated_metrics"]
        assert threshold_alert["current_values"]["accuracy"] < 0.85
        
        # Check for retraining trigger
        response = requests.get(
            f"{self.BASE_URL}/models/{model_id}/retraining-jobs",
            headers=auth_headers
        )
        assert response.status_code == 200
        retraining_jobs = response.json()
        assert len(retraining_jobs) > 0
        assert retraining_jobs[0]["trigger_reason"] == "accuracy_threshold_violation"
        
        # Step 5: Update thresholds and re-evaluate
        # Lower thresholds to match current performance
        updated_thresholds = {
            "thresholds": {
                "accuracy": {
                    "min": 0.65,
                    "warning": 0.70,
                    "target": 0.75
                }
            }
        }
        
        response = requests.patch(
            f"{self.BASE_URL}/models/{model_id}/accuracy-thresholds",
            json=updated_thresholds,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Trigger re-evaluation
        response = requests.post(
            f"{self.BASE_URL}/models/{model_id}/evaluate-thresholds",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Check if model is reactivated
        response = requests.get(
            f"{self.BASE_URL}/models/{model_id}/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        model_status = response.json()
        assert model_status["status"] == "active"
        
        # Verify detailed accuracy metrics
        response = requests.get(
            f"{self.BASE_URL}/models/{model_id}/accuracy/detailed",
            params={"include_confusion_matrix": True},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        detailed_metrics = response.json()
        assert "overall_accuracy" in detailed_metrics
        assert "per_class_metrics" in detailed_metrics
        assert "confusion_matrix" in detailed_metrics
        assert len(detailed_metrics["per_class_metrics"]) == 4
        
        # Verify per-class metrics
        for class_name in classes:
            assert class_name in detailed_metrics["per_class_metrics"]
            class_metrics = detailed_metrics["per_class_metrics"][class_name]
            assert "precision" in class_metrics
            assert "recall" in class_metrics
            assert "f1_score" in class_metrics
            assert "support" in class_metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "e2e"])