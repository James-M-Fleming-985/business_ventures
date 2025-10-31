```python
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class DeviceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class DeviceMetrics:
    device_id: str
    timestamp: datetime
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    temperature: float = 0.0
    response_time: float = 0.0
    error_count: int = 0
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthCheckResult:
    device_id: str
    status: DeviceStatus
    timestamp: datetime
    metrics: DeviceMetrics
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    alert_id: str
    device_id: str
    severity: AlertSeverity
    message: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class DeviceHealthMonitor:
    """Monitors health status of hardware devices."""
    
    def __init__(self):
        self._devices: Dict[str, Dict[str, Any]] = {}
        self._health_checks: Dict[str, HealthCheckResult] = {}
        self._alerts: Dict[str, Alert] = {}
        self._alert_handlers: List[Callable] = []
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._health_check_intervals: Dict[str, float] = {}
        self._alert_counter = 0
        self._running = False
        self._thresholds: Dict[str, Dict[str, float]] = {}
        self._device_check_functions: Dict[str, Callable] = {}
        
    async def initialize(self) -> None:
        """Initialize the health monitor service."""
        self._running = True
        logger.info("DeviceHealthMonitor initialized")
        
    async def shutdown(self) -> None:
        """Shutdown the health monitor service."""
        self._running = False
        
        # Cancel all monitoring tasks
        for task in self._monitoring_tasks.values():
            task.cancel()
            
        # Wait for tasks to complete
        if self._monitoring_tasks:
            await asyncio.gather(*self._monitoring_tasks.values(), return_exceptions=True)
            
        self._monitoring_tasks.clear()
        logger.info("DeviceHealthMonitor shutdown complete")
        
    def register_device(self, device_id: str, device_info: Dict[str, Any]) -> None:
        """Register a device for health monitoring."""
        self._devices[device_id] = device_info
        self._health_check_intervals[device_id] = device_info.get('check_interval', 30.0)
        
        # Set default thresholds
        self._thresholds[device_id] = {
            'cpu_usage': device_info.get('cpu_threshold', 80.0),
            'memory_usage': device_info.get('memory_threshold', 85.0),
            'temperature': device_info.get('temperature_threshold', 70.0),
            'response_time': device_info.get('response_time_threshold', 1000.0),
            'error_count': device_info.get('error_count_threshold', 10)
        }
        
        logger.info(f"Device {device_id} registered for health monitoring")
        
    def unregister_device(self, device_id: str) -> None:
        """Unregister a device from health monitoring."""
        if device_id in self._devices:
            del self._devices[device_id]
            
        if device_id in self._health_checks:
            del self._health_checks[device_id]
            
        if device_id in self._monitoring_tasks:
            self._monitoring_tasks[device_id].cancel()
            del self._monitoring_tasks[device_id]
            
        if device_id in self._health_check_intervals:
            del self._health_check_intervals[device_id]
            
        if device_id in self._thresholds:
            del self._thresholds[device_id]
            
        logger.info(f"Device {device_id} unregistered from health monitoring")
        
    async def start_monitoring(self, device_id: str) -> None:
        """Start monitoring a specific device."""
        if device_id not in self._devices:
            raise ValueError(f"Device {device_id} not registered")
            
        if device_id in self._monitoring_tasks:
            logger.warning(f"Monitoring already started for device {device_id}")
            return
            
        task = asyncio.create_task(self._monitor_device(device_id))
        self._monitoring_tasks[device_id] = task
        logger.info(f"Started monitoring device {device_id}")
        
    async def stop_monitoring(self, device_id: str) -> None:
        """Stop monitoring a specific device."""
        if device_id in self._monitoring_tasks:
            self._monitoring_tasks[device_id].cancel()
            try:
                await self._monitoring_tasks[device_id]
            except asyncio.CancelledError:
                pass
            del self._monitoring_tasks[device_id]
            logger.info(f"Stopped monitoring device {device_id}")
            
    async def _monitor_device(self, device_id: str) -> None:
        """Monitor a device continuously."""
        interval = self._health_check_intervals.get(device_id, 30.0)
        
        while self._running and device_id in self._devices:
            try:
                await self.check_device_health(device_id)
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring device {device_id}: {e}")
                await asyncio.sleep(interval)
                
    async def check_device_health(self, device_id: str) -> HealthCheckResult:
        """Check the health status of a specific device."""
        if device_id not in self._devices:
            raise ValueError(f"Device {device_id} not registered")
            
        # Get metrics
        metrics = await self._collect_device_metrics(device_id)
        
        # Determine status based on metrics
        status = self._evaluate_device_status(device_id, metrics)
        
        # Create health check result
        result = HealthCheckResult(
            device_id=device_id,
            status=status,
            timestamp=datetime.now(),
            metrics=metrics,
            message=self._generate_status_message(status, metrics),
            details={
                'device_info': self._devices[device_id],
                'thresholds': self._thresholds[device_id]
            }
        )
        
        # Store result
        self._health_checks[device_id] = result
        
        # Check for alerts
        await self._check_alerts(device_id, result)
        
        return result
        
    async def _collect_device_metrics(self, device_id: str) -> DeviceMetrics:
        """Collect metrics for a device."""
        # Use custom check function if available
        if device_id in self._device_check_functions:
            check_func = self._device_check_functions[device_id]
            custom_metrics = await check_func(device_id)
            
            return DeviceMetrics(
                device_id=device_id,
                timestamp=datetime.now(),
                cpu_usage=custom_metrics.get('cpu_usage', 0.0),
                memory_usage=custom_metrics.get('memory_usage', 0.0),
                temperature=custom_metrics.get('temperature', 0.0),
                response_time=custom_metrics.get('response_time', 0.0),
                error_count=custom_metrics.get('error_count', 0),
                custom_metrics=custom_metrics
            )
        
        # Default metrics (simulated)
        return DeviceMetrics(
            device_id=device_id,
            timestamp=datetime.now(),
            cpu_usage=45.0,  # Default healthy values
            memory_usage=50.0,
            temperature=40.0,
            response_time=100.0,
            error_count=0
        )
        
    def _evaluate_device_status(self, device_id: str, metrics: DeviceMetrics) -> DeviceStatus:
        """Evaluate device status based on metrics."""
        thresholds = self._thresholds[device_id]
        
        # Critical conditions
        if (metrics.cpu_usage > thresholds['cpu_usage'] * 1.2 or
            metrics.memory_usage > thresholds['memory_usage'] * 1.2 or
            metrics.temperature > thresholds['temperature'] * 1.2 or
            metrics.response_time > thresholds['response_time'] * 2 or
            metrics.error_count > thresholds['error_count'] * 2):
            return DeviceStatus.CRITICAL
            
        # Degraded conditions
        if (metrics.cpu_usage > thresholds['cpu_usage'] or
            metrics.memory_usage > thresholds['memory_usage'] or
            metrics.temperature > thresholds['temperature'] or
            metrics.response_time > thresholds['response_time'] or
            metrics.error_count > thresholds['error_count']):
            return DeviceStatus.DEGRADED
            
        return DeviceStatus.HEALTHY
        
    def _generate_status_message(self, status: DeviceStatus, metrics: DeviceMetrics) -> str:
        """Generate a status message based on device status and metrics."""
        if status == DeviceStatus.HEALTHY:
            return "Device operating normally"
        elif status == DeviceStatus.DEGRADED:
            return f"Device showing degraded performance - CPU: {metrics.cpu_usage}%, Memory: {metrics.memory_usage}%"
        elif status == DeviceStatus.CRITICAL:
            return f"Device in critical state - CPU: {metrics.cpu_usage}%, Memory: {metrics.memory_usage}%, Errors: {metrics.error_count}"
        else:
            return "Device status unknown"
            
    async def _check_alerts(self, device_id: str, result: HealthCheckResult) -> None:
        """Check if alerts need to be triggered based on health check result."""
        if result.status == DeviceStatus.CRITICAL:
            await self._create_alert(
                device_id=device_id,
                severity=AlertSeverity.CRITICAL,
                message=f"Device {device_id} is in critical state",
                details={'health_check': result}
            )
        elif result.status == DeviceStatus.DEGRADED:
            await self._create_alert(
                device_id=device_id,
                severity=AlertSeverity.WARNING,
                message=f"Device {device_id} is showing degraded performance",
                details={'health_check': result}
            )
            
    async def _create_alert(self, device_id: str, severity: AlertSeverity, 
                          message: str, details: Dict[str, Any]) -> None:
        """Create and trigger an alert."""
        self._alert_counter += 1
        alert_id = f"alert_{self._alert_counter}_{device_id}"
        
        alert = Alert(
            alert_id=alert_id,
            device_id=device_id,
            severity=severity,
            message=message,
            timestamp=datetime.now(),
            details=details
        )
        
        self._alerts[alert_id] = alert
        
        # Trigger alert handlers
        for handler in self._alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
                
    def get_device_status(self, device_id: str) -> Optional[HealthCheckResult]:
        """Get the current health status of a device."""
        return self._health_checks.get(device_id)
        
    def get_all_device_statuses(self) -> Dict[str, HealthCheckResult]:
        """Get health statuses of all devices."""
        return self._health_checks.copy()
        
    def get_device_alerts(self, device_id: str) -> List[Alert]:
        """Get all alerts for a specific device."""
        return [alert for alert in self._alerts.values() 
                if alert.device_id == device_id and not alert.resolved]
                
    def get_all_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return [alert for alert in self._alerts.values() if not alert.resolved]
        
    async def resolve_alert(self, alert_id: str) -> None:
        """Resolve a specific alert."""
        if alert_id in self._alerts:
            self._alerts[alert_id].resolved = True
            self._alerts[alert_id].resolved_at = datetime.now()
            logger.info(f"Alert {alert_id} resolved")
            
    def register_alert_handler(self, handler: Callable) -> None:
        """Register a handler to be called when alerts are triggered."""
        self._alert_handlers.append(handler)
        
    def set_health_check_interval(self, device_id: str, interval: float) -> None:
        """Set the health check interval for a specific device."""
        self._health_check_intervals[device_id] = interval
        
        # Restart monitoring if active
        if device_id in self._monitoring_tasks:
            asyncio.create_task(self._restart_monitoring(device_id))
            
    async def _restart_monitoring(self, device_id: str) -> None:
        """Restart monitoring for a device."""
        await self.stop_monitoring(device_id)
        await self.start_monitoring(device_id)
        
    def set_threshold(self, device_id: str, metric: str, threshold: float) -> None:
        """Set a threshold for a specific metric."""
        if device_id not in self._thresholds:
            self._thresholds[device_id] = {}
        self._thresholds[device_id][metric] = threshold
        
    def get_metrics_history(self, device_id: str, duration: timedelta) -> List[DeviceMetrics]:
        """Get metrics history for a device (placeholder for actual implementation)."""
        # In a real implementation, this would query a time-series database
        if device_id in self._health_checks:
            return [self._health_checks[device_id].metrics]
        return []
        
    def register_device_check_function(self, device_id: str, check_func: Callable) -> None:
        """Register a custom health check function for a device."""
        self._device_check_functions[device_id] = check_func
        
    async def generate_health_report(self) -> Dict[str, Any]:
        """Generate a comprehensive health report for all devices."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_devices': len(self._devices),
            'monitored_devices': len(self._monitoring_tasks),
            'device_statuses': {},
            'active_alerts': len([a for a in self._alerts.values() if not a.resolved]),
            'alerts': []
        }
        
        for device_id, result in self._health_checks.items():
            report['device_statuses'][device_id] = {
                'status': result.status.value,
                'last_check': result.timestamp.isoformat(),
                'metrics': {
                    'cpu_usage': result.metrics.cpu_usage,
                    'memory_usage': result.metrics.memory_usage,
                    'temperature': result.metrics.temperature,
                    'response_time': result.metrics.response_time,
                    'error_count': result.metrics.error_count
                }
            }
            
        for alert in self.get_all_alerts():
            report['alerts'].append({
                'alert_id': alert.alert_id,
                'device_id': alert.device_id,
                'severity': alert.severity.value,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat()
            })
            
        return report


class HealthMonitorService:
    """Service wrapper for DeviceHealthMonitor for backward compatibility."""
    
    def __init__(self):
        self.monitor = DeviceHealthMonitor()
        
    async def initialize(self) -> None:
        """Initialize the health monitor service."""
        await self.monitor.initialize()
        
    async def shutdown(self) -> None:
        """Shutdown the health monitor service."""
        await self.monitor.shutdown()
        
    def __getattr__(self, name):
        """Delegate all other attributes to the monitor."""
        return getattr(self.monitor, name)
```