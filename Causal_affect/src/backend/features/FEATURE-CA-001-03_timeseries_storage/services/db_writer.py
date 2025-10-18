"""Service for writing time-series data to TimescaleDB."""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ..models.timeseries_data import TimeSeriesDataCreate, TimeSeriesData
from ..db.schema import timeseries_data_table

logger = logging.getLogger(__name__)


class TimeSeriesWriterError(Exception):
    """Base exception for TimeSeriesWriter errors."""
    pass


class TimeSeriesWriter:
    """Handles writing time-series data to TimescaleDB with batching and compression."""
    
    def __init__(self, session: AsyncSession, batch_size: int = 1000):
        self.session = session
        self.batch_size = batch_size
        self._write_buffer: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
    
    async def write_single(self, data: TimeSeriesDataCreate) -> TimeSeriesData:
        """Write a single time-series data point."""
        try:
            stmt = insert(timeseries_data_table).values(
                timestamp=data.timestamp,
                metric_name=data.metric_name,
                value=data.value,
                tags=data.tags,
                metadata=data.metadata
            ).returning(timeseries_data_table)
            
            result = await self.session.execute(stmt)
            row = result.first()
            await self.session.commit()
            
            return TimeSeriesData(
                id=row.id,
                timestamp=row.timestamp,
                metric_name=row.metric_name,
                value=row.value,
                tags=row.tags,
                metadata=row.metadata,
                created_at=row.created_at
            )
        except IntegrityError as e:
            await self.session.rollback()
            raise TimeSeriesWriterError(f"Duplicate entry: {e}")
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise TimeSeriesWriterError(f"Database error: {e}")
    
    async def write_batch(self, data_list: List[TimeSeriesDataCreate]) -> int:
        """Write multiple time-series data points in a batch."""
        if not data_list:
            return 0
        
        try:
            values = [
                {
                    "timestamp": data.timestamp,
                    "metric_name": data.metric_name,
                    "value": data.value,
                    "tags": data.tags,
                    "metadata": data.metadata
                }
                for data in data_list
            ]
            
            stmt = insert(timeseries_data_table).values(values)
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            return result.rowcount
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise TimeSeriesWriterError(f"Batch write error: {e}")
    
    async def add_to_buffer(self, data: TimeSeriesDataCreate) -> None:
        """Add data to write buffer for later batch processing."""
        async with self._lock:
            self._write_buffer.append({
                "timestamp": data.timestamp,
                "metric_name": data.metric_name,
                "value": data.value,
                "tags": data.tags,
                "metadata": data.metadata
            })
            
            if len(self._write_buffer) >= self.batch_size:
                await self._flush_buffer()
    
    async def _flush_buffer(self) -> int:
        """Flush the write buffer to database."""
        if not self._write_buffer:
            return 0
        
        try:
            stmt = insert(timeseries_data_table).values(self._write_buffer)
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            count = result.rowcount
            self._write_buffer.clear()
            return count
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise TimeSeriesWriterError(f"Buffer flush error: {e}")
    
    async def flush(self) -> int:
        """Manually flush the write buffer."""
        async with self._lock:
            return await self._flush_buffer()
    
    async def query_range(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        tags: Optional[Dict[str, str]] = None,
        limit: int = 1000
    ) -> List[TimeSeriesData]:
        """Query time-series data within a time range."""
        try:
            query = text("""
                SELECT id, timestamp, metric_name, value, tags, metadata, created_at
                FROM timeseries_data
                WHERE metric_name = :metric_name
                AND timestamp >= :start_time
                AND timestamp <= :end_time
                AND (:tags IS NULL OR tags @> :tags)
                ORDER BY timestamp DESC
                LIMIT :limit
            """)
            
            result = await self.session.execute(
                query,
                {
                    "metric_name": metric_name,
                    "start_time": start_time,
                    "end_time": end_time,
                    "tags": tags,
                    "limit": limit
                }
            )
            
            rows = result.fetchall()
            return [
                TimeSeriesData(
                    id=row.id,
                    timestamp=row.timestamp,
                    metric_name=row.metric_name,
                    value=row.value,
                    tags=row.tags,
                    metadata=row.metadata,
                    created_at=row.created_at
                )
                for row in rows
            ]
        except SQLAlchemyError as e:
            raise TimeSeriesWriterError(f"Query error: {e}")
    
    async def aggregate(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        interval: str = "1 hour",
        aggregation: str = "avg"
    ) -> List[Dict[str, Any]]:
        """Perform time-based aggregation on metrics."""
        agg_funcs = {
            "avg": "AVG",
            "sum": "SUM",
            "min": "MIN",
            "max": "MAX",
            "count": "COUNT"
        }
        
        if aggregation not in agg_funcs:
            raise ValueError(f"Invalid aggregation: {aggregation}")
        
        try:
            query = text(f"""
                SELECT 
                    time_bucket(:interval, timestamp) AS bucket,
                    {agg_funcs[aggregation]}(value) AS value,
                    COUNT(*) AS count
                FROM timeseries_data
                WHERE metric_name = :metric_name
                AND timestamp >= :start_time
                AND timestamp <= :end_time
                GROUP BY bucket
                ORDER BY bucket
            """)
            
            result = await self.session.execute(
                query,
                {
                    "interval": interval,
                    "metric_name": metric_name,
                    "start_time": start_time,
                    "end_time": end_time
                }
            )
            
            return [
                {
                    "timestamp": row.bucket,
                    "value": float(row.value),
                    "count": row.count
                }
                for row in result.fetchall()
            ]
        except SQLAlchemyError as e:
            raise TimeSeriesWriterError(f"Aggregation error: {e}")
