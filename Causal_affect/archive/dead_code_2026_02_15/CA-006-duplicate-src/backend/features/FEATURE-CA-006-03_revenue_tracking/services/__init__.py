"""Revenue tracking services.

Business logic layer for revenue tracking operations including
transaction processing, aggregation, and analytics.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .revenue_service import RevenueService
    from .transaction_service import TransactionService
    from .analytics_service import AnalyticsService
    from .reporting_service import ReportingService

# Service names for dependency injection
SERVICE_NAMES = {
    "revenue": "RevenueService",
    "transaction": "TransactionService",
    "analytics": "AnalyticsService",
    "reporting": "ReportingService",
}

# Service configuration defaults
SERVICE_CONFIG = {
    "cache_ttl": 3600,  # 1 hour default cache
    "batch_size": 1000,
    "max_retries": 3,
    "timeout": 30,
}

__all__ = [
    "SERVICE_NAMES",
    "SERVICE_CONFIG",
]