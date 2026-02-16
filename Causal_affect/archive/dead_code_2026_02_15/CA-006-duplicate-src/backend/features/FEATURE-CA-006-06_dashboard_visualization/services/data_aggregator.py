from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.schemas import (
    MetricType,
    TimeRange,
    AggregatedData,
    MetricValue,
    TrendData,
    ComparisonData
)
from ..db.models import DashboardMetric, MetricSnapshot
from ..exceptions import DataAggregationError


class DataAggregator:
    """Service for aggregating dashboard metrics data."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_aggregated_metrics(
        self,
        dashboard_id: str,
        time_range: TimeRange,
        group_by: Optional[str] = None
    ) -> List[AggregatedData]:
        """Get aggregated metrics for a dashboard within time range."""
        try:
            end_time = datetime.utcnow()
            start_time = self._calculate_start_time(end_time, time_range)

            query = (
                select(MetricSnapshot)
                .join(DashboardMetric)
                .where(
                    and_(
                        DashboardMetric.dashboard_id == dashboard_id,
                        MetricSnapshot.timestamp >= start_time,
                        MetricSnapshot.timestamp <= end_time
                    )
                )
                .order_by(MetricSnapshot.timestamp)
            )

            result = await self.session.execute(query)
            snapshots = result.scalars().all()

            return self._aggregate_snapshots(snapshots, group_by)

        except Exception as e:
            raise DataAggregationError(f"Failed to aggregate metrics: {str(e)}")

    async def calculate_metric_trends(
        self,
        metric_id: str,
        time_range: TimeRange,
        interval: str = "hour"
    ) -> TrendData:
        """Calculate trend data for a specific metric."""
        try:
            end_time = datetime.utcnow()
            start_time = self._calculate_start_time(end_time, time_range)

            # Get current period data
            current_data = await self._get_metric_data(
                metric_id, start_time, end_time, interval
            )

            # Get previous period data for comparison
            period_delta = end_time - start_time
            prev_end = start_time
            prev_start = start_time - period_delta
            
            previous_data = await self._get_metric_data(
                metric_id, prev_start, prev_end, interval
            )

            return self._calculate_trends(current_data, previous_data)

        except Exception as e:
            raise DataAggregationError(f"Failed to calculate trends: {str(e)}")

    async def compare_metrics(
        self,
        metric_ids: List[str],
        time_range: TimeRange
    ) -> ComparisonData:
        """Compare multiple metrics within time range."""
        try:
            end_time = datetime.utcnow()
            start_time = self._calculate_start_time(end_time, time_range)

            comparison_data = ComparisonData(metrics=[])

            for metric_id in metric_ids:
                metric_data = await self._get_metric_summary(
                    metric_id, start_time, end_time
                )
                comparison_data.metrics.append(metric_data)

            return comparison_data

        except Exception as e:
            raise DataAggregationError(f"Failed to compare metrics: {str(e)}")

    async def get_metric_statistics(
        self,
        metric_id: str,
        time_range: TimeRange
    ) -> Dict[str, float]:
        """Get statistical summary for a metric."""
        try:
            end_time = datetime.utcnow()
            start_time = self._calculate_start_time(end_time, time_range)

            query = (
                select(
                    func.avg(MetricSnapshot.value).label('avg'),
                    func.min(MetricSnapshot.value).label('min'),
                    func.max(MetricSnapshot.value).label('max'),
                    func.stddev(MetricSnapshot.value).label('stddev'),
                    func.count(MetricSnapshot.id).label('count')
                )
                .where(
                    and_(
                        MetricSnapshot.metric_id == metric_id,
                        MetricSnapshot.timestamp >= start_time,
                        MetricSnapshot.timestamp <= end_time
                    )
                )
            )

            result = await self.session.execute(query)
            stats = result.one()

            return {
                "average": float(stats.avg or 0),
                "minimum": float(stats.min or 0),
                "maximum": float(stats.max or 0),
                "std_dev": float(stats.stddev or 0),
                "count": int(stats.count or 0)
            }

        except Exception as e:
            raise DataAggregationError(f"Failed to get statistics: {str(e)}")

    def _calculate_start_time(
        self,
        end_time: datetime,
        time_range: TimeRange
    ) -> datetime:
        """Calculate start time based on time range."""
        delta_map = {
            TimeRange.HOUR: timedelta(hours=1),
            TimeRange.DAY: timedelta(days=1),
            TimeRange.WEEK: timedelta(weeks=1),
            TimeRange.MONTH: timedelta(days=30),
            TimeRange.QUARTER: timedelta(days=90),
            TimeRange.YEAR: timedelta(days=365)
        }
        return end_time - delta_map.get(time_range, timedelta(days=1))

    def _aggregate_snapshots(
        self,
        snapshots: List[MetricSnapshot],
        group_by: Optional[str]
    ) -> List[AggregatedData]:
        """Aggregate snapshot data."""
        if not group_by:
            return [self._create_aggregated_data(snapshots)]

        grouped = {}
        for snapshot in snapshots:
            key = self._get_group_key(snapshot, group_by)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(snapshot)

        return [
            self._create_aggregated_data(group, key)
            for key, group in grouped.items()
        ]

    def _create_aggregated_data(
        self,
        snapshots: List[MetricSnapshot],
        group_key: Optional[str] = None
    ) -> AggregatedData:
        """Create aggregated data from snapshots."""
        if not snapshots:
            return AggregatedData(
                metric_type=MetricType.GAUGE,
                values=[],
                summary={}
            )

        values = [
            MetricValue(
                timestamp=s.timestamp,
                value=s.value,
                metadata=s.metadata
            )
            for s in snapshots
        ]

        summary = {
            "total": sum(s.value for s in snapshots),
            "average": sum(s.value for s in snapshots) / len(snapshots),
            "count": len(snapshots)
        }

        if group_key:
            summary["group"] = group_key

        return AggregatedData(
            metric_type=snapshots[0].metric.metric_type,
            values=values,
            summary=summary
        )

    def _get_group_key(self, snapshot: MetricSnapshot, group_by: str) -> str:
        """Get grouping key from snapshot."""
        if group_by == "hour":
            return snapshot.timestamp.strftime("%Y-%m-%d %H:00")
        elif group_by == "day":
            return snapshot.timestamp.strftime("%Y-%m-%d")
        elif group_by == "metric":
            return snapshot.metric.name
        else:
            return snapshot.metadata.get(group_by, "unknown")

    async def _get_metric_data(
        self,
        metric_id: str,
        start_time: datetime,
        end_time: datetime,
        interval: str
    ) -> List[Dict[str, Any]]:
        """Get metric data grouped by interval."""
        interval_func = self._get_interval_function(interval)
        
        query = (
            select(
                interval_func.label('interval'),
                func.avg(MetricSnapshot.value).label('avg_value'),
                func.count(MetricSnapshot.id).label('count')
            )
            .where(
                and_(
                    MetricSnapshot.metric_id == metric_id,
                    MetricSnapshot.timestamp >= start_time,
                    MetricSnapshot.timestamp <= end_time
                )
            )
            .group_by('interval')
            .order_by('interval')
        )

        result = await self.session.execute(query)
        return [
            {
                "interval": row.interval,
                "value": float(row.avg_value or 0),
                "count": int(row.count)
            }
            for row in result
        ]

    def _get_interval_function(self, interval: str):
        """Get SQL function for time interval grouping."""
        if interval == "minute":
            return func.date_trunc('minute', MetricSnapshot.timestamp)
        elif interval == "hour":
            return func.date_trunc('hour', MetricSnapshot.timestamp)
        elif interval == "day":
            return func.date_trunc('day', MetricSnapshot.timestamp)
        else:
            return func.date_trunc('hour', MetricSnapshot.timestamp)

    def _calculate_trends(
        self,
        current: List[Dict[str, Any]],
        previous: List[Dict[str, Any]]
    ) -> TrendData:
        """Calculate trend data from current and previous periods."""
        current_sum = sum(d["value"] for d in current)
        previous_sum = sum(d["value"] for d in previous) or 1
        
        change_percent = ((current_sum - previous_sum) / previous_sum) * 100
        trend = "up" if change_percent > 0 else "down" if change_percent < 0 else "stable"
        
        return TrendData(
            current_value=current_sum,
            previous_value=previous_sum,
            change_percent=change_percent,
            trend=trend,
            data_points=[
                MetricValue(
                    timestamp=d["interval"],
                    value=d["value"]
                )
                for d in current
            ]
        )

    async def _get_metric_summary(
        self,
        metric_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Get summary data for a metric."""
        stats = await self.get_metric_statistics(
            metric_id,
            TimeRange.DAY  # Default to day for comparison
        )
        
        query = (
            select(DashboardMetric)
            .where(DashboardMetric.id == metric_id)
        )
        
        result = await self.session.execute(query)
        metric = result.scalar_one_or_none()
        
        if not metric:
            raise DataAggregationError(f"Metric {metric_id} not found")
        
        return {
            "id": metric_id,
            "name": metric.name,
            "type": metric.metric_type,
            "unit": metric.unit,
            "statistics": stats
        }
