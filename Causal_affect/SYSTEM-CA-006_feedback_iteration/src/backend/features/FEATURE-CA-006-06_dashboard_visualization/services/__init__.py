"""Dashboard Visualization Services.

Core business logic for dashboard operations including:
- Dashboard configuration and management
- Metrics aggregation and calculation
- Real-time data streaming
- Cache management for performance
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .dashboard_service import DashboardService
    from .metrics_aggregation_service import MetricsAggregationService
    from .realtime_update_service import RealtimeUpdateService
    from .cache_service import CacheService
    from .widget_service import WidgetService
    from .analytics_service import AnalyticsService

# Service exports
__all__ = [
    "DashboardService",
    "MetricsAggregationService",
    "RealtimeUpdateService",
    "CacheService",
    "WidgetService",
    "AnalyticsService",
]

# Service configuration defaults
SERVICE_CONFIG = {
    "cache_ttl": 300,  # 5 minutes default cache TTL
    "realtime_update_interval": 5,  # 5 seconds for real-time updates
    "max_widgets_per_dashboard": 20,
    "max_dashboards_per_user": 10,
    "metrics_batch_size": 1000,
    "aggregation_intervals": ["1m", "5m", "15m", "1h", "1d"],
    "supported_chart_types": [
        "line",
        "bar",
        "pie",
        "scatter",
        "heatmap",
        "gauge",
        "table",
    ],
    "supported_metrics": [
        "player_count",
        "game_sessions",
        "revenue",
        "engagement_rate",
        "retention_rate",
        "conversion_rate",
        "system_performance",
        "error_rate",
    ],
}

# WebSocket event types for real-time updates
WS_EVENT_TYPES = {
    "METRIC_UPDATE": "metric_update",
    "WIDGET_UPDATE": "widget_update",
    "DASHBOARD_UPDATE": "dashboard_update",
    "ALERT_TRIGGERED": "alert_triggered",
    "CONNECTION_STATUS": "connection_status",
}

# Error codes specific to dashboard services
ERROR_CODES = {
    "DASHBOARD_NOT_FOUND": "DSH001",
    "WIDGET_NOT_FOUND": "DSH002",
    "METRIC_NOT_AVAILABLE": "DSH003",
    "CACHE_ERROR": "DSH004",
    "AGGREGATION_ERROR": "DSH005",
    "REALTIME_CONNECTION_ERROR": "DSH006",
    "PERMISSION_DENIED": "DSH007",
    "INVALID_CONFIGURATION": "DSH008",
    "LIMIT_EXCEEDED": "DSH009",
}