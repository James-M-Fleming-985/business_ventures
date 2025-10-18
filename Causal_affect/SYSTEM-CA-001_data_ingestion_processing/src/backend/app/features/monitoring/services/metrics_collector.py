"""Metrics Collector Service - Layer: Metrics Collection

Collects system and feature metrics for Prometheus.
"""

from prometheus_client import Counter, Gauge, Histogram
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and exposes metrics for monitoring."""
    
    def __init__(self):
        """Initialize metrics collector."""
        # Request metrics
        self.request_count = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        
        self.request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint']
        )
        
        # Feature metrics
        self.feature_status = Gauge(
            'feature_status',
            'Feature health status (1=healthy, 0=unhealthy)',
            ['feature_name']
        )
        
        self.data_processed = Counter(
            'data_records_processed_total',
            'Total data records processed',
            ['feature', 'status']
        )
        
        # System metrics
        self.active_connections = Gauge(
            'active_db_connections',
            'Number of active database connections'
        )
        
        logger.info("MetricsCollector initialized with Prometheus metrics")
    
    async def record_request(
        self, 
        method: str, 
        endpoint: str, 
        status: int,
        duration: float
    ) -> None:
        """Record HTTP request metrics.
        
        Args:
            method: HTTP method (GET, POST, etc)
            endpoint: Request endpoint path
            status: HTTP status code
            duration: Request duration in seconds
        """
        self.request_count.labels(
            method=method,
            endpoint=endpoint,
            status=str(status)
        ).inc()
        
        self.request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    async def update_feature_status(
        self, 
        feature_name: str, 
        is_healthy: bool
    ) -> None:
        """Update feature health status.
        
        Args:
            feature_name: Name of the feature
            is_healthy: Whether feature is healthy
        """
        self.feature_status.labels(feature_name=feature_name).set(
            1.0 if is_healthy else 0.0
        )
    
    async def record_data_processed(
        self, 
        feature: str, 
        count: int = 1,
        success: bool = True
    ) -> None:
        """Record data processing metrics.
        
        Args:
            feature: Feature that processed the data
            count: Number of records processed
            success: Whether processing succeeded
        """
        status = 'success' if success else 'failure'
        self.data_processed.labels(
            feature=feature,
            status=status
        ).inc(count)
    
    async def update_db_connections(self, count: int) -> None:
        """Update active database connections gauge.
        
        Args:
            count: Current number of active connections
        """
        self.active_connections.set(count)
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary.
        
        Returns:
            Dictionary of current metric values
        """
        return {
            'active_db_connections': self.active_connections._value._value,
            'features_monitored': len(self.feature_status._metrics),
            'metrics_available': True
        }
