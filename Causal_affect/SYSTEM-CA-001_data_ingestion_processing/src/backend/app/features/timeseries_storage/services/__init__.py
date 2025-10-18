"""TimeSeries storage services."""

from typing import Protocol, runtime_checkable
from datetime import datetime
from typing import Any, Dict, List, Optional, Union


@runtime_checkable
class TimeSeriesStorageService(Protocol):
    """Protocol for TimeSeries storage operations."""
    
    async def store(
        self,
        metric_name: str,
        value: Union[float, int],
        timestamp: Optional[datetime] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> str:
        """Store a single time series data point."""
        ...
    
    async def store_batch(
        self,
        metric_name: str,
        data_points: List[Dict[str, Any]],
    ) -> List[str]:
        """Store multiple time series data points."""
        ...
    
    async def delete(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        tags: Optional[Dict[str, str]] = None,
    ) -> int:
        """Delete time series data within a time range."""
        ...


@runtime_checkable
class TimeSeriesQueryService(Protocol):
    """Protocol for TimeSeries query operations."""
    
    async def query(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        tags: Optional[Dict[str, str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query time series data within a time range."""
        ...
    
    async def get_latest(
        self,
        metric_name: str,
        tags: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get the latest data point for a metric."""
        ...
    
    async def get_metrics(
        self,
        prefix: Optional[str] = None,
    ) -> List[str]:
        """List available metrics."""
        ...


@runtime_checkable
class TimeSeriesAggregationService(Protocol):
    """Protocol for TimeSeries aggregation operations."""
    
    async def aggregate(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        aggregation: str,
        interval: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform aggregation on time series data."""
        ...
    
    async def downsample(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        interval: str,
        aggregation: str = "avg",
        tags: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """Downsample time series data."""
        ...


class TimeSeriesService:
    """Main service for TimeSeries operations."""
    
    def __init__(
        self,
        storage_service: TimeSeriesStorageService,
        query_service: TimeSeriesQueryService,
        aggregation_service: TimeSeriesAggregationService,
    ) -> None:
        self.storage = storage_service
        self.query = query_service
        self.aggregation = aggregation_service
    
    async def store_metric(
        self,
        metric_name: str,
        value: Union[float, int],
        timestamp: Optional[datetime] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> str:
        """Store a metric data point."""
        return await self.storage.store(
            metric_name=metric_name,
            value=value,
            timestamp=timestamp,
            tags=tags,
        )
    
    async def query_range(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        tags: Optional[Dict[str, str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query metrics within a time range."""
        return await self.query.query(
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time,
            tags=tags,
            limit=limit,
        )
    
    async def get_aggregated(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        aggregation: str,
        interval: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """Get aggregated metric data."""
        return await self.aggregation.aggregate(
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time,
            aggregation=aggregation,
            interval=interval,
            tags=tags,
        )


__all__ = [
    "TimeSeriesService",
    "TimeSeriesStorageService",
    "TimeSeriesQueryService",
    "TimeSeriesAggregationService",
]