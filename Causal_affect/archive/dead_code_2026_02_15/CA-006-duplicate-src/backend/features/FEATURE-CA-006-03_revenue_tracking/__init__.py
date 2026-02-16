"""Revenue tracking feature module.

Provides functionality for tracking and analyzing revenue metrics,
including transaction processing, revenue aggregation, and reporting.
"""

from typing import Final

__version__: Final[str] = "1.0.0"
__feature_id__: Final[str] = "FEATURE-CA-006-03"
__feature_name__: Final[str] = "Revenue Tracking"

# Feature metadata
FEATURE_METADATA = {
    "id": __feature_id__,
    "name": __feature_name__,
    "version": __version__,
    "description": "Revenue tracking and analytics system",
    "status": "active",
    "dependencies": [
        "sqlalchemy>=2.0.0",
        "pydantic>=2.0.0",
        "redis>=4.5.0",
        "fastapi>=0.104.0"
    ],
    "api_endpoints": [
        "/api/v1/revenue",
        "/api/v1/revenue/transactions",
        "/api/v1/revenue/analytics",
        "/api/v1/revenue/reports"
    ],
    "permissions": [
        "revenue:read",
        "revenue:write",
        "revenue:analytics",
        "revenue:reports"
    ]
}

# Public API exports
__all__ = [
    "__version__",
    "__feature_id__",
    "__feature_name__",
    "FEATURE_METADATA",
]