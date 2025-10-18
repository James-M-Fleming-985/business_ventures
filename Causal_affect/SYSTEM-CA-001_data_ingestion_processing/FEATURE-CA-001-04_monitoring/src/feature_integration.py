"""
Feature Integration Module for System Monitoring & Observability
Feature ID: FEATURE-CA-001-04

This module orchestrates the Metrics Collector, Health Checker, and Alerter layers
to provide comprehensive system monitoring and observability capabilities.
"""

from pathlib import Path
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
import json
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import layer implementations
from LAYER_CA_001_04_01_Metrics_Collector.LAYER_CA_001_04_01_metrics_collector.src.implementation import (
    MetricsCollector, TimerContext
)
from LAYER_CA_001_04_02_Health_Checker.LAYER_CA_001_04_02_health_checker.src.implementation import (
    HealthMetrics, HealthChecker, SystemMonitor
)
from LAYER_CA_001_04_03_Alerter.LAYER_CA_001_04_03_alerter.src.implementation import (
    AlertSeverity, AlertStatus, Alert, AlertChannel, EmailChannel, SlackChannel, SMSChannel, AlertRule, Alerter
)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResponseStatus(Enum):
    """Status codes for feature responses"""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class FeatureConfig:
    """Configuration for System Monitoring & Observability feature"""
    # Metrics Collector configuration
    metrics_collection_interval: float = 60.0  # seconds
    metrics_retention_hours: int = 168  # 1 week
    
    # Health Checker configuration
    health_check_interval: float = 30.0  # seconds
    health_thresholds: Dict[str, float] = None
    
    # Alerter configuration
    alert_channels: List[Dict[str, Any]] = None
    alert_rules: List[Dict[str, Any]] = None
    alert_cooldown_minutes: int = 15
    
    def __post_init__(self):
        if self.health_thresholds is None:
            self.health_thresholds = {
                "cpu_usage": 80.0,
                "memory_usage": 85.0,
                "disk_usage": 90.0,
                "response_time_ms": 1000.0
            }
        
        if self.alert_channels is None:
            self.alert_channels = []
            
        if self.alert_rules is None:
            self.alert_rules = []


@dataclass
class FeatureResponse:
    """Unified response structure for feature operations"""
    status: ResponseStatus
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.errors is None:
            self.errors = []
            

class MonitoringState:
    """Represents the current monitoring state"""
    def __init__(self):
        self.is_active: bool = False
        self.last_health_check: Optional[datetime] = None
        self.last_metrics_collection: Optional[datetime] = None
        self.active_alerts: List[Alert] = []
        self.health_status: Optional[HealthMetrics] = None


class FeatureOrchestrator:
    """
    Orchestrates System Monitoring & Observability feature by coordinating
    Metrics Collector, Health Checker, and Alerter layers.
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        """
        Initialize the feature orchestrator with configuration.
        
        Args:
            config: Feature configuration object
        """
        self.config = config or FeatureConfig()
        self.state = MonitoringState()
        
        # Initialize layers
        self._initialize_layers()
        
    def _initialize_layers(self) -> None:
        """Initialize all layer instances"""
        try:
            # Initialize Metrics Collector
            logger.info("Initializing Metrics Collector layer...")
            self.metrics_collector = MetricsCollector()
            
            # Initialize Health Checker
            logger.info("Initializing Health Checker layer...")
            self.health_checker = HealthChecker()
            self.system_monitor = SystemMonitor()
            
            # Initialize Alerter
            logger.info("Initializing Alerter layer...")
            self.alerter = Alerter()
            self._setup_alert_channels()
            self._setup_alert_rules()
            
            logger.info("All layers initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize layers: {str(e)}")
            raise RuntimeError(f"Layer initialization failed: {str(e)}")
    
    def _setup_alert_channels(self) -> None:
        """Configure alert channels based on configuration"""
        for channel_config in self.config.alert_channels:
            try:
                channel_type = channel_config.get("type")
                if channel_type == "email":
                    channel = EmailChannel(
                        smtp_host=channel_config.get("smtp_host"),
                        smtp_port=channel_config.get("smtp_port"),
                        username=channel_config.get("username"),
                        password=channel_config.get("password"),
                        from_email=channel_config.get("from_email"),
                        to_emails=channel_config.get("to_emails", [])
                    )
                elif channel_type == "slack":
                    channel = SlackChannel(
                        webhook_url=channel_config.get("webhook_url"),
                        channel=channel_config.get("channel"),
                        username=channel_config.get("username")
                    )
                elif channel_type == "sms":
                    channel = SMSChannel(
                        account_sid=channel_config.get("account_sid"),
                        auth_token=channel_config.get("auth_token"),
                        from_number=channel_config.get("from_number"),
                        to_numbers=channel_config.get("to_numbers", [])
                    )
                else:
                    logger.warning(f"Unknown channel type: {channel_type}")
                    continue
                    
                self.alerter.add_channel(channel_config.get("name"), channel)
                logger.info(f"Added {channel_type} alert channel: {channel_config.get('name')}")
                
            except Exception as e:
                logger.error(f"Failed to setup alert channel: {str(e)}")
    
    def _setup_alert_rules(self) -> None:
        """Configure alert rules based on configuration"""
        for rule_config in self.config.alert_rules:
            try:
                rule = AlertRule(
                    name=rule_config.get("name"),
                    condition=rule_config.get("condition"),
                    severity=AlertSeverity[rule_config.get("severity", "WARNING")],
                    channels=rule_config.get("channels", []),
                    cooldown_minutes=rule_config.get("cooldown_minutes", self.config.alert_cooldown_minutes)
                )
                self.alerter.add_rule(rule)
                logger.info(f"Added alert rule: {rule.name}")
                
            except Exception as e:
                logger.error(f"Failed to setup alert rule: {str(e)}")
    
    def start_monitoring(self) -> FeatureResponse:
        """
        Start the monitoring system.
        
        Returns:
            FeatureResponse indicating success or failure
        """
        try:
            if self.state.is_active:
                return FeatureResponse(
                    status=ResponseStatus.WARNING,
                    message="Monitoring is already active"
                )
            
            # Start system monitor
            self.system_monitor.start()
            
            # Perform initial health check
            health_status = self._perform_health_check()
            
            # Collect initial metrics
            self._collect_metrics()
            
            self.state.is_active = True
            
            return FeatureResponse(
                status=ResponseStatus.SUCCESS,
                message="Monitoring started successfully",
                data={
                    "health_status": health_status,
                    "active_channels": list(self.alerter.channels.keys()),
                    "active_rules": len(self.alerter.rules)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to start monitoring: {str(e)}")
            return FeatureResponse(
                status=ResponseStatus.ERROR,
                message="Failed to start monitoring",
                errors=[str(e)]
            )
    
    def stop_monitoring(self) -> FeatureResponse:
        """
        Stop the monitoring system.
        
        Returns:
            FeatureResponse indicating success or failure
        """
        try:
            if not self.state.is_active:
                return FeatureResponse(
                    status=ResponseStatus.WARNING,
                    message="Monitoring is not active"
                )
            
            # Stop system monitor
            self.system_monitor.stop()
            
            # Clear active alerts
            self.state.active_alerts.clear()
            
            self.state.is_active = False
            
            return FeatureResponse(
                status=ResponseStatus.SUCCESS,
                message="Monitoring stopped successfully"
            )
            
        except Exception as e:
            logger.error(f"Failed to stop monitoring: {str(e)}")
            return FeatureResponse(
                status=ResponseStatus.ERROR,
                message="Failed to stop monitoring",
                errors=[str(e)]
            )
    
    def get_system_status(self) -> FeatureResponse:
        """
        Get comprehensive system status including metrics and health.
        
        Returns:
            FeatureResponse with system status data
        """
        try:
            if not self.state.is_active:
                return FeatureResponse(
                    status=ResponseStatus.WARNING,
                    message="Monitoring is not active"
                )
            
            # Perform health check
            health_status = self._perform_health_check()
            
            # Get current metrics
            metrics = self._get_current_metrics()
            
            # Check for threshold violations
            violations = self._check_threshold_violations(health_status)
            
            return FeatureResponse(
                status=ResponseStatus.SUCCESS,
                message="System status retrieved successfully",
                data={
                    "is_healthy": health_status.is_healthy,
                    "health_metrics": {
                        "cpu_usage": health_status.cpu_usage,
                        "memory_usage": health_status.memory_usage,
                        "disk_usage": health_status.disk_usage,
                        "active_connections": health_status.active_connections,
                        "response_time_ms": health_status.response_time_ms
                    },
                    "performance_metrics": metrics,
                    "threshold_violations": violations,
                    "active_alerts": len(self.state.active_alerts),
                    "last_check": self.state.last_health_check.isoformat() if self.state.last_health_check else None
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to get system status: {str(e)}")
            return FeatureResponse(
                status=ResponseStatus.ERROR,
                message="Failed to get system status",
                errors=[str(e)]
            )
    
    def collect_metrics(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> FeatureResponse:
        """
        Collect a custom metric.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Optional tags for the metric
            
        Returns:
            FeatureResponse indicating success or failure
        """
        try:
            self.metrics_collector.record_metric(metric_name, value, tags)
            
            return FeatureResponse(
                status=ResponseStatus.SUCCESS,
                message=f"Metric '{metric_name}' recorded successfully"
            )
            
        except Exception as e:
            logger.error(f"Failed to collect metric: {str(e)}")
            return FeatureResponse(
                status=ResponseStatus.ERROR,
                message="Failed to collect metric",
                errors=[str(e)]
            )
    
    def create_timer_context(self, operation_name: str) -> TimerContext:
        """
        Create a timer context for measuring operation duration.
        
        Args:
            operation_name: Name of the operation to measure
            
        Returns:
            TimerContext object
        """
        return self.metrics_collector.timer(operation_name)
    
    def trigger_alert(self, title: str, message: str, severity: AlertSeverity = AlertSeverity.WARNING) -> FeatureResponse:
        """
        Manually trigger an alert.
        
        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity level
            
        Returns:
            FeatureResponse indicating success or failure
        """
        try:
            alert = Alert(
                title=title,
                message=message,
                severity=severity
            )
            
            # Send alert through all channels
            sent_channels = self.alerter.send_alert(alert, list(self.alerter.channels.keys()))
            
            # Track active alert
            self.state.active_alerts.append(alert)
            
            return FeatureResponse(
                status=ResponseStatus.SUCCESS,
                message=f"Alert sent to {len(sent_channels)} channels",
                data={
                    "alert_id": alert.alert_id,
                    "sent_channels": sent_channels
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to trigger alert: {str(e)}")
            return FeatureResponse(
                status=ResponseStatus.ERROR,
                message="Failed to trigger alert",
                errors=[str(e)]
            )
    
    def get_metrics_summary(self, hours: int = 24) -> FeatureResponse:
        """
        Get metrics summary for the specified time period.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            FeatureResponse with metrics summary
        """
        try:
            summary = self.metrics_collector.get_metrics_summary(hours)
            
            return FeatureResponse(
                status=ResponseStatus.SUCCESS,
                message=f"Metrics summary for last {hours} hours",
                data={"summary": summary}
            )
            
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {str(e)}")
            return FeatureResponse(
                status=ResponseStatus.ERROR,
                message="Failed to get metrics summary",
                errors=[str(e)]
            )
    
    def _perform_health_check(self) -> HealthMetrics:
        """
        Perform a comprehensive health check.
        
        Returns:
            HealthMetrics object with current health status
        """
        health_status = self.health_checker.check_health()
        self.state.health_status = health_status
        self.state.last_health_check = datetime.now()
        
        # Check for critical conditions and trigger alerts
        self._evaluate_health_alerts(health_status)
        
        return health_status
    
    def _collect_metrics(self) -> None:
        """Collect standard system metrics"""
        try:
            # Collect health metrics
            if self.state.health_status:
                self.metrics_collector.record_metric("system.cpu.usage", self.state.health_status.cpu_usage)
                self.metrics_collector.record_metric("system.memory.usage", self.state.health_status.memory_usage)
                self.metrics_collector.record_metric("system.disk.usage", self.state.health_status.disk_usage)
                self.metrics_collector.record_metric("system.connections.active", self.state.health_status.active_connections)
                self.metrics_collector.record_metric("system.response.time_ms", self.state.health_status.response_time_ms)
            
            self.state.last_metrics_collection = datetime.now()
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {str(e)}")
    
    def _get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        try:
            return self.metrics_collector.get_all_metrics()
        except Exception as e:
            logger.error(f"Failed to get current metrics: {str(e)}")
            return {}
    
    def _check_threshold_violations(self, health_status: HealthMetrics) -> List[Dict[str, Any]]:
        """
        Check for threshold violations in health metrics.
        
        Args:
            health_status: Current health status
            
        Returns:
            List of threshold violations
        """
        violations = []
        
        thresholds = self.config.health_thresholds
        
        if health_status.cpu_usage > thresholds.get("cpu_usage", 100):
            violations.append({
                "metric": "cpu_usage",
                "value": health_status.cpu_usage,
                "threshold": thresholds["cpu_usage"]
            })
        
        if health_status.memory_usage > thresholds.get("memory_usage", 100):
            violations.append({
                "metric": "memory_usage",
                "value": health_status.memory_usage,
                "threshold": thresholds["memory_usage"]
            })
        
        if health_status.disk_usage > thresholds.get("disk_usage", 100):
            violations.append({
                "metric": "disk_usage",
                "value": health_status.disk_usage,
                "threshold": thresholds["disk_usage"]
            })
        
        if health_status.response_time_ms > thresholds.get("response_time_ms", float('inf')):
            violations.append({
                "metric": "response_time_ms",
                "value": health_status.response_time_ms,
                "threshold": thresholds["response_time_ms"]
            })
        
        return violations
    
    def _evaluate_health_alerts(self, health_status: HealthMetrics) -> None:
        """
        Evaluate health status and trigger alerts if necessary.
        
        Args:
            health_status: Current health status
        """
        try:
            violations = self._check_threshold_violations(health_status)
            
            for violation in violations:
                # Create context for alert rules
                context = {
                    "metric": violation["metric"],
                    "value": violation["value"],
                    "threshold": violation["threshold"],
                    "health_status": health_status
                }
                
                # Evaluate alert rules
                self.alerter.evaluate_rules(context)
                
        except Exception as e:
            logger.error(f"Failed to evaluate health alerts: {str(e)}")