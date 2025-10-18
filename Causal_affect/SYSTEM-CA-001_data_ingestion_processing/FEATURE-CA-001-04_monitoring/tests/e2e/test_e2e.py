"""
End-to-end tests for System Monitoring & Observability feature
Feature ID: FEATURE-CA-001-04
"""

import pytest
import time
import json
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import requests
from dataclasses import dataclass
from typing import List, Dict, Any
import logging


# Test data structures
@dataclass
class MetricData:
    """Represents a metric data point"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str]
    unit: str = "count"


@dataclass
class LogEntry:
    """Represents a log entry"""
    level: str
    message: str
    timestamp: datetime
    service: str
    trace_id: str = None
    context: Dict[str, Any] = None


@dataclass
class Alert:
    """Represents an alert"""
    id: str
    name: str
    severity: str
    condition: str
    threshold: float
    status: str = "active"


# Mock monitoring system components
class MockMonitoringSystem:
    """Mock monitoring system for testing"""
    
    def __init__(self):
        self.metrics_store = []
        self.logs_store = []
        self.alerts_store = []
        self.dashboards = {}
        self.alert_rules = []
        self.notification_channels = []
        
    def ingest_metrics(self, metrics: List[MetricData]) -> bool:
        """Ingest metrics into the system"""
        for metric in metrics:
            self.metrics_store.append({
                "name": metric.name,
                "value": metric.value,
                "timestamp": metric.timestamp.isoformat(),
                "labels": metric.labels,
                "unit": metric.unit
            })
        return True
    
    def ingest_logs(self, logs: List[LogEntry]) -> bool:
        """Ingest logs into the system"""
        for log in logs:
            self.logs_store.append({
                "level": log.level,
                "message": log.message,
                "timestamp": log.timestamp.isoformat(),
                "service": log.service,
                "trace_id": log.trace_id,
                "context": log.context or {}
            })
        return True
    
    def query_metrics(self, query: str, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Query metrics based on criteria"""
        results = []
        for metric in self.metrics_store:
            metric_time = datetime.fromisoformat(metric["timestamp"])
            if start_time <= metric_time <= end_time:
                if query in metric["name"]:
                    results.append(metric)
        return results
    
    def query_logs(self, filters: Dict[str, Any]) -> List[Dict]:
        """Query logs based on filters"""
        results = []
        for log in self.logs_store:
            match = True
            if "service" in filters and log["service"] != filters["service"]:
                match = False
            if "level" in filters and log["level"] != filters["level"]:
                match = False
            if "trace_id" in filters and log["trace_id"] != filters["trace_id"]:
                match = False
            if match:
                results.append(log)
        return results
    
    def create_alert_rule(self, alert: Alert) -> str:
        """Create an alert rule"""
        self.alert_rules.append(alert)
        return alert.id
    
    def evaluate_alerts(self) -> List[Dict]:
        """Evaluate alert rules and generate alerts"""
        triggered_alerts = []
        
        # Check each alert rule
        for rule in self.alert_rules:
            # Simple threshold-based alerting
            recent_metrics = self.query_metrics(
                rule.condition,
                datetime.now() - timedelta(minutes=5),
                datetime.now()
            )
            
            if recent_metrics:
                latest_value = recent_metrics[-1]["value"]
                if latest_value > rule.threshold:
                    triggered_alerts.append({
                        "alert_id": rule.id,
                        "name": rule.name,
                        "severity": rule.severity,
                        "value": latest_value,
                        "threshold": rule.threshold,
                        "timestamp": datetime.now().isoformat()
                    })
                    self.alerts_store.append(triggered_alerts[-1])
        
        return triggered_alerts
    
    def create_dashboard(self, name: str, config: Dict) -> str:
        """Create a monitoring dashboard"""
        dashboard_id = f"dash-{len(self.dashboards) + 1}"
        self.dashboards[dashboard_id] = {
            "id": dashboard_id,
            "name": name,
            "config": config,
            "created_at": datetime.now().isoformat()
        }
        return dashboard_id
    
    def get_system_health(self) -> Dict:
        """Get overall system health status"""
        # Calculate health based on recent metrics and alerts
        recent_alerts = [a for a in self.alerts_store 
                        if datetime.fromisoformat(a["timestamp"]) > datetime.now() - timedelta(hours=1)]
        
        critical_alerts = len([a for a in recent_alerts if a["severity"] == "critical"])
        warning_alerts = len([a for a in recent_alerts if a["severity"] == "warning"])
        
        if critical_alerts > 0:
            health_status = "unhealthy"
        elif warning_alerts > 2:
            health_status = "degraded"
        else:
            health_status = "healthy"
        
        return {
            "status": health_status,
            "critical_alerts": critical_alerts,
            "warning_alerts": warning_alerts,
            "last_check": datetime.now().isoformat()
        }


# Fixtures
@pytest.fixture
def monitoring_system():
    """Create a mock monitoring system"""
    return MockMonitoringSystem()


@pytest.fixture
def sample_metrics():
    """Generate sample metrics data"""
    base_time = datetime.now()
    metrics = []
    
    # CPU metrics
    for i in range(10):
        metrics.append(MetricData(
            name="system.cpu.usage",
            value=30 + (i * 5) + (10 if i > 5 else 0),  # Simulate increasing CPU
            timestamp=base_time + timedelta(minutes=i),
            labels={"host": "server-1", "core": "total"},
            unit="percent"
        ))
    
    # Memory metrics
    for i in range(10):
        metrics.append(MetricData(
            name="system.memory.usage",
            value=60 + (i * 2),  # Gradual memory increase
            timestamp=base_time + timedelta(minutes=i),
            labels={"host": "server-1", "type": "used"},
            unit="percent"
        ))
    
    # Request rate metrics
    for i in range(10):
        metrics.append(MetricData(
            name="application.request.rate",
            value=1000 + (i * 100) + (500 if i > 7 else 0),  # Spike at the end
            timestamp=base_time + timedelta(minutes=i),
            labels={"service": "api-gateway", "endpoint": "/api/v1/users"},
            unit="requests/min"
        ))
    
    return metrics


@pytest.fixture
def sample_logs():
    """Generate sample log data"""
    base_time = datetime.now()
    logs = []
    trace_id = "trace-123-456"
    
    # Normal operation logs
    for i in range(5):
        logs.append(LogEntry(
            level="INFO",
            message=f"Request processed successfully",
            timestamp=base_time + timedelta(seconds=i*10),
            service="api-gateway",
            trace_id=trace_id,
            context={"user_id": "user-123", "duration_ms": 150 + i*10}
        ))
    
    # Warning logs
    logs.append(LogEntry(
        level="WARNING",
        message="High memory usage detected",
        timestamp=base_time + timedelta(minutes=5),
        service="api-gateway",
        context={"memory_percent": 78}
    ))
    
    # Error logs
    logs.append(LogEntry(
        level="ERROR",
        message="Database connection timeout",
        timestamp=base_time + timedelta(minutes=7),
        service="user-service",
        trace_id="trace-789-012",
        context={"error_code": "DB_TIMEOUT", "retry_count": 3}
    ))
    
    return logs


@pytest.fixture
def alert_rules():
    """Sample alert rules"""
    return [
        Alert(
            id="alert-1",
            name="High CPU Usage",
            severity="warning",
            condition="system.cpu.usage",
            threshold=70
        ),
        Alert(
            id="alert-2",
            name="Critical Memory Usage",
            severity="critical",
            condition="system.memory.usage",
            threshold=80
        ),
        Alert(
            id="alert-3",
            name="High Request Rate",
            severity="warning",
            condition="application.request.rate",
            threshold=1500
        )
    ]


# End-to-End Tests
class TestSystemMonitoringE2E:
    """End-to-end tests for System Monitoring & Observability"""
    
    @pytest.mark.asyncio
    async def test_e2e_complete_monitoring_workflow(self, monitoring_system, sample_metrics, sample_logs, alert_rules):
        """
        Test complete monitoring workflow from data ingestion to alerting
        
        Scenario:
        1. Ingest metrics and logs from multiple services
        2. Set up alert rules for various conditions
        3. Query and analyze the data
        4. Trigger alerts based on thresholds
        5. Create dashboard with visualizations
        6. Verify system health status
        """
        
        # Step 1: Ingest monitoring data
        print("\n=== Step 1: Ingesting monitoring data ===")
        
        # Ingest metrics
        metrics_ingested = monitoring_system.ingest_metrics(sample_metrics)
        assert metrics_ingested is True
        assert len(monitoring_system.metrics_store) == 30  # 10 CPU + 10 Memory + 10 Request rate
        
        # Ingest logs
        logs_ingested = monitoring_system.ingest_logs(sample_logs)
        assert logs_ingested is True
        assert len(monitoring_system.logs_store) == 7
        
        print(f"✓ Ingested {len(monitoring_system.metrics_store)} metrics")
        print(f"✓ Ingested {len(monitoring_system.logs_store)} logs")
        
        # Step 2: Set up alert rules
        print("\n=== Step 2: Setting up alert rules ===")
        
        for rule in alert_rules:
            rule_id = monitoring_system.create_alert_rule(rule)
            assert rule_id == rule.id
            print(f"✓ Created alert rule: {rule.name} (threshold: {rule.threshold})")
        
        assert len(monitoring_system.alert_rules) == 3
        
        # Step 3: Query and analyze data
        print("\n=== Step 3: Querying and analyzing data ===")
        
        # Query CPU metrics
        cpu_metrics = monitoring_system.query_metrics(
            "system.cpu.usage",
            datetime.now() - timedelta(hours=1),
            datetime.now()
        )
        assert len(cpu_metrics) == 10
        
        # Verify CPU trend (should be increasing)
        cpu_values = [m["value"] for m in cpu_metrics]
        assert cpu_values[-1] > cpu_values[0]  # CPU increased over time
        print(f"✓ CPU usage trend: {cpu_values[0]}% → {cpu_values[-1]}%")
        
        # Query error logs
        error_logs = monitoring_system.query_logs({"level": "ERROR"})
        assert len(error_logs) == 1
        assert error_logs[0]["message"] == "Database connection timeout"
        print(f"✓ Found {len(error_logs)} error logs")
        
        # Query logs by trace ID
        trace_logs = monitoring_system.query_logs({"trace_id": "trace-123-456"})
        assert len(trace_logs) == 5
        print(f"✓ Found {len(trace_logs)} logs for trace ID")
        
        # Step 4: Evaluate alerts
        print("\n=== Step 4: Evaluating alerts ===")
        
        triggered_alerts = monitoring_system.evaluate_alerts()
        assert len(triggered_alerts) >= 2  # At least CPU and Request rate should trigger
        
        # Verify alert details
        for alert in triggered_alerts:
            print(f"✗ Alert triggered: {alert['name']} - "
                  f"Value: {alert['value']:.2f} > Threshold: {alert['threshold']}")
            assert alert['value'] > alert['threshold']
        
        # Step 5: Create dashboard
        print("\n=== Step 5: Creating dashboard ===")
        
        dashboard_config = {
            "title": "System Overview Dashboard",
            "panels": [
                {
                    "type": "graph",
                    "title": "CPU Usage",
                    "query": "system.cpu.usage",
                    "timeRange": "1h"
                },
                {
                    "type": "graph",
                    "title": "Memory Usage",
                    "query": "system.memory.usage",
                    "timeRange": "1h"
                },
                {
                    "type": "stat",
                    "title": "Request Rate",
                    "query": "application.request.rate",
                    "aggregation": "latest"
                },
                {
                    "type": "logs",
                    "title": "Error Logs",
                    "filter": {"level": "ERROR"},
                    "limit": 50
                }
            ],
            "refresh": "30s"
        }
        
        dashboard_id = monitoring_system.create_dashboard(
            "System Overview",
            dashboard_config
        )
        assert dashboard_id in monitoring_system.dashboards
        dashboard = monitoring_system.dashboards[dashboard_id]
        assert len(dashboard["config"]["panels"]) == 4
        print(f"✓ Created dashboard: {dashboard['name']} (ID: {dashboard_id})")
        
        # Step 6: Check system health
        print("\n=== Step 6: Checking system health ===")
        
        health_status = monitoring_system.get_system_health()
        assert health_status["status"] in ["healthy", "degraded", "unhealthy"]
        assert health_status["critical_alerts"] >= 0
        assert health_status["warning_alerts"] >= 0
        
        print(f"✓ System health: {health_status['status']}")
        print(f"  - Critical alerts: {health_status['critical_alerts']}")
        print(f"  - Warning alerts: {health_status['warning_alerts']}")
        
        # Verify overall workflow completion
        print("\n=== Workflow Summary ===")
        print(f"✓ Total metrics collected: {len(monitoring_system.metrics_store)}")
        print(f"✓ Total logs collected: {len(monitoring_system.logs_store)}")
        print(f"✓ Active alert rules: {len(monitoring_system.alert_rules)}")
        print(f