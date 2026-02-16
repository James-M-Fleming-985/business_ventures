"""Dashboard Visualization Feature Module.

Provides real-time dashboard visualization capabilities for game analytics,
player behavior tracking, and system monitoring.
"""

from typing import Final

__version__: Final[str] = "1.0.0"
__feature_id__: Final[str] = "FEATURE-CA-006-06"
__feature_name__: Final[str] = "Dashboard Visualization"

# Feature metadata
FEATURE_METADATA = {
    "id": __feature_id__,
    "name": __feature_name__,
    "version": __version__,
    "description": "Real-time dashboard visualization for game analytics and monitoring",
    "dependencies": [
        "fastapi>=0.104.0",
        "sqlalchemy>=2.0.0",
        "pydantic>=2.0.0",
        "redis>=4.0.0",
        "websockets>=11.0.0",
    ],
    "api_endpoints": [
        "/api/v1/dashboard",
        "/api/v1/dashboard/analytics",
        "/api/v1/dashboard/metrics",
        "/api/v1/dashboard/realtime",
        "/ws/dashboard/updates",
    ],
    "models": [
        "DashboardConfig",
        "DashboardMetric",
        "DashboardWidget",
        "RealtimeUpdate",
    ],
    "services": [
        "DashboardService",
        "MetricsAggregationService",
        "RealtimeUpdateService",
        "CacheService",
    ],
}

__all__ = [
    "__version__",
    "__feature_id__",
    "__feature_name__",
    "FEATURE_METADATA",
]