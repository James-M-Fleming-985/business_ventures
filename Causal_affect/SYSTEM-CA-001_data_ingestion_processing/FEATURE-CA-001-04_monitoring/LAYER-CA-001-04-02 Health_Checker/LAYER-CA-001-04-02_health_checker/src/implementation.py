```python
"""Health Checker Module

This module provides functionality to monitor system health metrics including CPU usage,
memory usage, disk usage, and network connectivity.
"""

import psutil
import socket
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import requests
from dataclasses import dataclass, field


@dataclass
class HealthMetrics:
    """Data class to store health metrics."""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    network_status: bool = True
    timestamp: datetime = field(default_factory=datetime.now)


class HealthChecker:
    """Main class for monitoring system health."""
    
    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        """Initialize HealthChecker with optional thresholds.
        
        Args:
            thresholds: Dictionary with keys 'cpu', 'memory', 'disk' and threshold values
        """
        self.thresholds = thresholds or {
            'cpu': 80.0,
            'memory': 80.0,
            'disk': 80.0
        }
        self._history: List[HealthMetrics] = []
        self._alerts: List[str] = []
    
    def check_cpu(self) -> float:
        """Check current CPU usage percentage.
        
        Returns:
            CPU usage percentage
        """
        return psutil.cpu_percent(interval=0.1)
    
    def check_memory(self) -> float:
        """Check current memory usage percentage.
        
        Returns:
            Memory usage percentage
        """
        return psutil.virtual_memory().percent
    
    def check_disk(self, path: str = '/') -> float:
        """Check disk usage percentage for given path.
        
        Args:
            path: Path to check disk usage for
            
        Returns:
            Disk usage percentage
        """
        return psutil.disk_usage(path).percent
    
    def check_network(self, host: str = 'google.com', port: int = 80, timeout: int = 5) -> bool:
        """Check network connectivity.
        
        Args:
            host: Host to check connectivity to
            port: Port to connect to
            timeout: Connection timeout in seconds
            
        Returns:
            True if network is available, False otherwise
        """
        try:
            socket.create_connection((host, port), timeout=timeout)
            return True
        except (socket.timeout, socket.error):
            return False
    
    def get_metrics(self) -> HealthMetrics:
        """Get current system health metrics.
        
        Returns:
            HealthMetrics object with current system metrics
        """
        metrics = HealthMetrics(
            cpu_percent=self.check_cpu(),
            memory_percent=self.check_memory(),
            disk_percent=self.check_disk(),
            network_status=self.check_network()
        )
        self._history.append(metrics)
        self._check_thresholds(metrics)
        return metrics
    
    def _check_thresholds(self, metrics: HealthMetrics) -> None:
        """Check if metrics exceed thresholds and generate alerts.
        
        Args:
            metrics: Current health metrics
        """
        if metrics.cpu_percent > self.thresholds['cpu']:
            alert = f"CPU usage ({metrics.cpu_percent:.1f}%) exceeds threshold ({self.thresholds['cpu']}%)"
            self._alerts.append(alert)
        
        if metrics.memory_percent > self.thresholds['memory']:
            alert = f"Memory usage ({metrics.memory_percent:.1f}%) exceeds threshold ({self.thresholds['memory']}%)"
            self._alerts.append(alert)
        
        if metrics.disk_percent > self.thresholds['disk']:
            alert = f"Disk usage ({metrics.disk_percent:.1f}%) exceeds threshold ({self.thresholds['disk']}%)"
            self._alerts.append(alert)
        
        if not metrics.network_status:
            alert = "Network connectivity issue detected"
            self._alerts.append(alert)
    
    def get_alerts(self) -> List[str]:
        """Get list of current alerts.
        
        Returns:
            List of alert messages
        """
        return self._alerts.copy()
    
    def clear_alerts(self) -> None:
        """Clear all alerts."""
        self._alerts.clear()
    
    def get_history(self, limit: Optional[int] = None) -> List[HealthMetrics]:
        """Get metrics history.
        
        Args:
            limit: Maximum number of historical entries to return
            
        Returns:
            List of HealthMetrics from history
        """
        if limit is None:
            return self._history.copy()
        return self._history[-limit:] if limit > 0 else []
    
    def get_summary(self) -> Dict[str, any]:
        """Get summary of current system health.
        
        Returns:
            Dictionary with health summary
        """
        current = self.get_metrics()
        return {
            'timestamp': current.timestamp.isoformat(),
            'status': 'healthy' if not self._alerts else 'unhealthy',
            'metrics': {
                'cpu': current.cpu_percent,
                'memory': current.memory_percent,
                'disk': current.disk_percent,
                'network': current.network_status
            },
            'alerts': self.get_alerts(),
            'thresholds': self.thresholds.copy()
        }
    
    def monitor(self, interval: int = 60, duration: Optional[int] = None) -> None:
        """Monitor system health continuously.
        
        Args:
            interval: Time between checks in seconds
            duration: Total monitoring duration in seconds (None for infinite)
        """
        start_time = time.time()
        
        while True:
            self.get_metrics()
            
            if duration is not None and (time.time() - start_time) >= duration:
                break
            
            time.sleep(interval)


class SystemMonitor:
    """Extended monitoring class with additional features."""
    
    def __init__(self, health_checker: Optional[HealthChecker] = None):
        """Initialize SystemMonitor.
        
        Args:
            health_checker: Optional HealthChecker instance to use
        """
        self.health_checker = health_checker or HealthChecker()
        self._services: Dict[str, Dict] = {}
    
    def add_service(self, name: str, url: str, expected_status: int = 200) -> None:
        """Add a service to monitor.
        
        Args:
            name: Service name
            url: Service URL to check
            expected_status: Expected HTTP status code
        """
        self._services[name] = {
            'url': url,
            'expected_status': expected_status,
            'last_check': None,
            'status': None
        }
    
    def check_services(self) -> Dict[str, bool]:
        """Check all registered services.
        
        Returns:
            Dictionary mapping service names to their status
        """
        results = {}
        
        for name, config in self._services.items():
            try:
                response = requests.get(config['url'], timeout=5)
                is_healthy = response.status_code == config['expected_status']
                results[name] = is_healthy
                config['status'] = is_healthy
                config['last_check'] = datetime.now()
            except requests.RequestException:
                results[name] = False
                config['status'] = False
                config['last_check'] = datetime.now()
        
        return results
    
    def get_system_info(self) -> Dict[str, any]:
        """Get detailed system information.
        
        Returns:
            Dictionary with system information
        """
        return {
            'platform': {
                'system': psutil.LINUX if hasattr(psutil, 'LINUX') else 'unknown',
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
            },
            'cpu': {
                'count': psutil.cpu_count(),
                'count_logical': psutil.cpu_count(logical=True),
                'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'used': psutil.virtual_memory().used,
                'free': psutil.virtual_memory().free
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'free': psutil.disk_usage('/').free
            },
            'network': {
                'interfaces': list(psutil.net_if_addrs().keys())
            }
        }
    
    def get_processes(self, sort_by: str = 'cpu', limit: int = 10) -> List[Dict]:
        """Get top processes by CPU or memory usage.
        
        Args:
            sort_by: Sort by 'cpu' or 'memory'
            limit: Number of processes to return
            
        Returns:
            List of process information dictionaries
        """
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        sort_key = 'cpu_percent' if sort_by == 'cpu' else 'memory_percent'
        processes.sort(key=lambda x: x.get(sort_key, 0), reverse=True)
        
        return processes[:limit]


def create_health_checker(config: Optional[Dict] = None) -> HealthChecker:
    """Factory function to create configured HealthChecker instance.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured HealthChecker instance
    """
    if config:
        thresholds = config.get('thresholds', {})
        return HealthChecker(thresholds)
    return HealthChecker()


def format_bytes(bytes_value: int) -> str:
    """Format bytes to human readable format.
    
    Args:
        bytes_value: Number of bytes
        
    Returns:
        Formatted string (e.g., '1.5 GB')
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def generate_report(health_checker: HealthChecker) -> str:
    """Generate a health report.
    
    Args:
        health_checker: HealthChecker instance
        
    Returns:
        Formatted health report string
    """
    summary = health_checker.get_summary()
    
    report = f"System Health Report\n"
    report += f"Generated: {summary['timestamp']}\n"
    report += f"Status: {summary['status'].upper()}\n\n"
    
    report += "Metrics:\n"
    report += f"  CPU Usage: {summary['metrics']['cpu']:.1f}%\n"
    report += f"  Memory Usage: {summary['metrics']['memory']:.1f}%\n"
    report += f"  Disk Usage: {summary['metrics']['disk']:.1f}%\n"
    report += f"  Network: {'Connected' if summary['metrics']['network'] else 'Disconnected'}\n\n"
    
    if summary['alerts']:
        report += "Alerts:\n"
        for alert in summary['alerts']:
            report += f"  - {alert}\n"
    else:
        report += "No alerts\n"
    
    return report
```