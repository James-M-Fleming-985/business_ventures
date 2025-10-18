"""
Integration tests for System Monitoring & Observability Feature
Feature ID: FEATURE-CA-001-04
Tests the integration between Metrics_Collector, Health_Checker, and Alerter layers
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, List, Any
import json
import redis
import smtplib
from email.mime.text import MIMEText
import requests

# Import the layers (assuming they exist in the project structure)
from src.features.system_monitoring.metrics_collector import MetricsCollector
from src.features.system_monitoring.health_checker import HealthChecker
from src.features.system_monitoring.alerter import Alerter


class TestSystemMonitoringIntegration:
    """Integration tests for System Monitoring & Observability feature"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client for metrics storage"""
        with patch('redis.Redis') as mock:
            redis_instance = Mock()
            mock.return_value = redis_instance
            redis_instance.get.return_value = None
            redis_instance.set.return_value = True
            redis_instance.exists.return_value = False
            yield redis_instance

    @pytest.fixture
    def mock_smtp(self):
        """Mock SMTP server for email alerts"""
        with patch('smtplib.SMTP') as mock:
            smtp_instance = Mock()
            mock.return_value = smtp_instance
            smtp_instance.send_message.return_value = None
            yield smtp_instance

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client for webhook alerts"""
        with patch('requests.post') as mock:
            mock.return_value.status_code = 200
            mock.return_value.json.return_value = {"status": "success"}
            yield mock

    @pytest.fixture
    def metrics_collector(self, mock_redis):
        """Initialize MetricsCollector with mocked dependencies"""
        return MetricsCollector(
            redis_client=mock_redis,
            collection_interval=1,  # 1 second for testing
            retention_period=3600  # 1 hour
        )

    @pytest.fixture
    def health_checker(self, metrics_collector):
        """Initialize HealthChecker with MetricsCollector"""
        return HealthChecker(
            metrics_collector=metrics_collector,
            thresholds={
                "cpu_usage": 80.0,
                "memory_usage": 90.0,
                "disk_usage": 85.0,
                "response_time": 1000,  # ms
                "error_rate": 5.0  # percentage
            }
        )

    @pytest.fixture
    def alerter(self, mock_smtp, mock_http_client):
        """Initialize Alerter with mocked dependencies"""
        return Alerter(
            smtp_config={
                "host": "smtp.example.com",
                "port": 587,
                "username": "alerts@example.com",
                "password": "test_password"
            },
            webhook_urls=["https://webhook.example.com/alerts"],
            alert_cooldown=300  # 5 minutes
        )

    @pytest.fixture
    def sample_metrics(self):
        """Sample metrics for testing"""
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": 75.5,
            "memory_usage": 82.3,
            "disk_usage": 60.0,
            "response_time": 250,
            "error_rate": 2.5,
            "active_connections": 150,
            "requests_per_second": 1000
        }

    @pytest.mark.asyncio
    async def test_metrics_collection_to_health_check_flow(
        self, metrics_collector, health_checker, sample_metrics
    ):
        """Test 1: Metrics collection triggers health check and returns status"""
        # Arrange
        metrics_collector.collect_system_metrics = AsyncMock(return_value=sample_metrics)
        
        # Act
        # Collect metrics
        collected_metrics = await metrics_collector.collect_system_metrics()
        assert collected_metrics == sample_metrics
        
        # Store metrics
        stored = await metrics_collector.store_metrics(collected_metrics)
        assert stored is True
        
        # Perform health check using collected metrics
        health_status = await health_checker.check_health(collected_metrics)
        
        # Assert
        assert health_status["status"] == "healthy"
        assert health_status["metrics_checked"] == len(sample_metrics)
        assert all(check["status"] == "ok" for check in health_status["checks"])
        assert health_status["timestamp"] is not None

    @pytest.mark.asyncio
    async def test_unhealthy_metrics_trigger_alerts(
        self, metrics_collector, health_checker, alerter, mock_smtp, mock_http_client
    ):
        """Test 2: Unhealthy metrics trigger appropriate alerts"""
        # Arrange
        unhealthy_metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": 95.0,  # Above threshold
            "memory_usage": 92.0,  # Above threshold
            "disk_usage": 70.0,
            "response_time": 1500,  # Above threshold
            "error_rate": 1.0
        }
        
        metrics_collector.collect_system_metrics = AsyncMock(return_value=unhealthy_metrics)
        
        # Act
        # Collect and store metrics
        collected_metrics = await metrics_collector.collect_system_metrics()
        await metrics_collector.store_metrics(collected_metrics)
        
        # Check health
        health_status = await health_checker.check_health(collected_metrics)
        
        # Send alerts for unhealthy status
        if health_status["status"] != "healthy":
            alert_result = await alerter.send_alert(
                alert_type="health_check_failure",
                severity="high",
                details=health_status
            )
        
        # Assert
        assert health_status["status"] == "unhealthy"
        assert len([c for c in health_status["checks"] if c["status"] == "critical"]) >= 3
        
        # Verify email alert was sent
        mock_smtp.send_message.assert_called_once()
        
        # Verify webhook was called
        mock_http_client.assert_called_once()
        assert alert_result["email_sent"] is True
        assert alert_result["webhook_sent"] is True

    @pytest.mark.asyncio
    async def test_metric_trend_analysis_integration(
        self, metrics_collector, health_checker, alerter, mock_redis
    ):
        """Test 3: Integration of metric trend analysis across layers"""
        # Arrange
        # Simulate historical metrics
        historical_metrics = []
        base_time = datetime.now() - timedelta(minutes=30)
        
        for i in range(10):
            metrics = {
                "timestamp": (base_time + timedelta(minutes=i*3)).isoformat(),
                "cpu_usage": 50.0 + (i * 5),  # Increasing trend
                "memory_usage": 60.0,
                "disk_usage": 70.0,
                "response_time": 200 + (i * 50),  # Increasing trend
                "error_rate": 1.0
            }
            historical_metrics.append(metrics)
        
        # Mock Redis to return historical data
        mock_redis.zrangebyscore.return_value = [
            json.dumps(m).encode() for m in historical_metrics
        ]
        
        # Act
        # Analyze trends
        trends = await metrics_collector.analyze_trends(
            metric_name="cpu_usage",
            time_window=timedelta(minutes=30)
        )
        
        # Check if trends indicate potential issues
        health_prediction = await health_checker.predict_health_issues(trends)
        
        # Send predictive alert if needed
        if health_prediction["risk_level"] == "high":
            alert_result = await alerter.send_alert(
                alert_type="predictive_alert",
                severity="medium",
                details={
                    "prediction": health_prediction,
                    "trends": trends
                }
            )
        
        # Assert
        assert trends["trend_direction"] == "increasing"
        assert trends["average_change_rate"] > 0
        assert health_prediction["risk_level"] in ["medium", "high"]
        assert "predicted_breach_time" in health_prediction

    @pytest.mark.asyncio
    async def test_alert_deduplication_and_cooldown(
        self, alerter, health_checker, mock_smtp, mock_http_client
    ):
        """Test 4: Alert deduplication prevents spam during sustained issues"""
        # Arrange
        critical_health_status = {
            "status": "critical",
            "timestamp": datetime.now().isoformat(),
            "checks": [
                {"metric": "cpu_usage", "status": "critical", "value": 95.0}
            ]
        }
        
        # Act
        # Send first alert
        first_alert = await alerter.send_alert(
            alert_type="critical_health",
            severity="critical",
            details=critical_health_status
        )
        
        # Try to send duplicate alerts
        duplicate_alerts = []
        for _ in range(3):
            result = await alerter.send_alert(
                alert_type="critical_health",
                severity="critical",
                details=critical_health_status
            )
            duplicate_alerts.append(result)
            await asyncio.sleep(0.1)  # Small delay
        
        # Assert
        assert first_alert["email_sent"] is True
        assert first_alert["webhook_sent"] is True
        
        # Verify deduplication worked
        for dup in duplicate_alerts:
            assert dup["email_sent"] is False
            assert dup["deduplicated"] is True
            assert "cooldown_remaining" in dup
        
        # Verify only one email and webhook were sent
        assert mock_smtp.send_message.call_count == 1
        assert mock_http_client.call_count == 1

    @pytest.mark.asyncio
    async def test_complete_monitoring_pipeline_with_recovery(
        self, metrics_collector, health_checker, alerter, 
        mock_redis, mock_smtp, mock_http_client
    ):
        """Test 5: Complete monitoring pipeline including issue detection and recovery"""
        # Arrange
        issue_detected = False
        recovery_detected = False
        
        # Simulate metrics that go from healthy -> unhealthy -> healthy
        metric_sequence = [
            # Healthy state
            {"cpu_usage": 60.0, "memory_usage": 70.0, "error_rate": 1.0},
            {"cpu_usage": 65.0, "memory_usage": 72.0, "error_rate": 1.5},
            # Degrading
            {"cpu_usage": 85.0, "memory_usage": 88.0, "error_rate": 4.0},
            # Critical
            {"cpu_usage": 92.0, "memory_usage": 94.0, "error_rate": 7.0},
            # Recovery begins
            {"cpu_usage": 80.0, "memory_usage": 85.0, "error_rate": 3.0},
            # Fully recovered
            {"cpu_usage": 55.0, "memory_usage": 65.0, "error_rate": 0.5},
        ]
        
        alerts_sent = []
        
        # Act
        for i, metric_values in enumerate(metric_sequence):
            # Create full metrics
            metrics = {
                "timestamp": datetime.now().isoformat(),
                **metric_values,
                "disk_usage": 50.0,
                "response_time": 200,
                "active_connections": 100
            }
            
            # Collect and store
            await metrics_collector.store_metrics(metrics)
            
            # Check health
            health_status = await health_checker.check_health(metrics)
            
            # Handle state transitions
            if health_status["status"] != "healthy" and not issue_detected:
                issue_detected = True
                alert = await alerter.send_alert(
                    alert_type="health_degradation",
                    severity="high",
                    details=health_status
                )
                alerts_sent.append(("degradation", alert))
                
            elif health_status["status"] == "healthy" and issue_detected and not recovery_detected:
                recovery_detected = True
                alert = await alerter.send_alert(
                    alert_type="health_recovery",
                    severity="info",
                    details={
                        "status": "recovered",
                        "recovery_time": datetime.now().isoformat(),
                        "current_metrics": health_status
                    }
                )
                alerts_sent.append(("recovery", alert))
            
            await asyncio.sleep(0.1)  # Simulate time passing
        
        # Assert
        assert issue_detected is True
        assert recovery_detected is True
        assert len(alerts_sent) >= 2
        
        # Verify degradation alert
        degradation_alerts = [a for t, a in alerts_sent if t == "degradation"]
        assert len(degradation_alerts) > 0
        assert degradation_alerts[0]["email_sent"] is True
        
        # Verify recovery alert
        recovery_alerts = [a for t, a in alerts_sent if t == "recovery"]
        assert len(recovery_alerts) == 1
        assert recovery_alerts[0]["email_sent"] is True

    @pytest.mark.asyncio
    async def test_error_handling_across_layers(
        self, metrics_collector, health_checker, alerter,
        mock_redis, mock_smtp
    ):
        """Test 6: Error handling and resilience across layer boundaries"""
        # Arrange
        # Simulate Redis failure
        mock_redis.set.side_effect = redis.ConnectionError("Redis connection failed")
        mock_redis.get.side_effect = redis.ConnectionError("Redis connection failed")
        
        # Simulate SMTP failure
        mock_smtp.send_message.side_effect = smtplib.SMTPException("SMTP server error")
        
        # Act & Assert
        # Metrics collection should handle Redis errors gracefully
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": 90.0,
            "memory_usage": 85.0
        }
        
        # Storage should fail but not crash
        store_result = await metrics_collector.store_metrics(metrics)
        assert store_result is False
        
        # Health check should still work with provided metrics
        health_status = await health_checker.check_health(metrics)
        assert health_status["status"] == "unhealthy"
        
        # Alert sending should handle SMTP errors
        alert_result = await alerter.send_alert(
            alert_type="critical",
            severity="high",
            details=health_status
        )
        
        assert alert_result["email_sent"] is False
        assert "error" in alert_result
        assert "SMTP" in alert_result["error"]
        
        # Webhook might still work (if implemented with fallback)
        # This demonstrates resilience - one channel fails but others continue

    @pytest.mark.asyncio
    async def test_metric_aggregation_and_reporting(
        self, metrics_collector, health_checker, mock_redis
    ):
        """Test 7: Metric aggregation for reporting across time windows"""
        # Arrange
        # Generate metrics for different time periods
        now = datetime.now()
        metrics_data = []
        
        for hours_ago in range(24):
            for minute in range(0, 60, 15):
                timestamp = now