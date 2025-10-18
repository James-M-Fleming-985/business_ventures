"""Service for managing TimescaleDB partitions and compression."""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class PartitionerError(Exception):
    """Base exception for Partitioner errors."""
    pass


class TimeSeriesPartitioner:
    """Manages TimescaleDB hypertable partitioning and compression policies."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_hypertable(
        self,
        table_name: str = "timeseries_data",
        time_column: str = "timestamp",
        chunk_interval: str = "1 day"
    ) -> bool:
        """Create a hypertable from existing table."""
        try:
            query = text("""
                SELECT create_hypertable(
                    :table_name,
                    :time_column,
                    chunk_time_interval => INTERVAL :chunk_interval,
                    if_not_exists => TRUE
                )
            """)
            
            await self.session.execute(
                query,
                {
                    "table_name": table_name,
                    "time_column": time_column,
                    "chunk_interval": chunk_interval
                }
            )
            await self.session.commit()
            
            logger.info(f"Hypertable created for {table_name}")
            return True
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise PartitionerError(f"Failed to create hypertable: {e}")
    
    async def add_compression_policy(
        self,
        table_name: str = "timeseries_data",
        compress_after: str = "7 days",
        orderby_column: str = "timestamp",
        segmentby_column: Optional[str] = "metric_name"
    ) -> int:
        """Add compression policy to hypertable."""
        try:
            # First, enable compression on the hypertable
            alter_query = text("""
                ALTER TABLE :table_name SET (
                    timescaledb.compress,
                    timescaledb.compress_orderby = :orderby_column,
                    timescaledb.compress_segmentby = :segmentby_column
                )
            """)
            
            await self.session.execute(
                alter_query,
                {
                    "table_name": table_name,
                    "orderby_column": orderby_column,
                    "segmentby_column": segmentby_column
                }
            )
            
            # Then add compression policy
            policy_query = text("""
                SELECT add_compression_policy(
                    :table_name,
                    INTERVAL :compress_after,
                    if_not_exists => TRUE
                )
            """)
            
            result = await self.session.execute(
                policy_query,
                {
                    "table_name": table_name,
                    "compress_after": compress_after
                }
            )
            await self.session.commit()
            
            policy_id = result.scalar()
            logger.info(f"Compression policy added with ID: {policy_id}")
            return policy_id
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise PartitionerError(f"Failed to add compression policy: {e}")
    
    async def add_retention_policy(
        self,
        table_name: str = "timeseries_data",
        drop_after: str = "30 days"
    ) -> int:
        """Add data retention policy to hypertable."""
        try:
            query = text("""
                SELECT add_retention_policy(
                    :table_name,
                    INTERVAL :drop_after,
                    if_not_exists => TRUE
                )
            """)
            
            result = await self.session.execute(
                query,
                {
                    "table_name": table_name,
                    "drop_after": drop_after
                }
            )
            await self.session.commit()
            
            policy_id = result.scalar()
            logger.info(f"Retention policy added with ID: {policy_id}")
            return policy_id
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise PartitionerError(f"Failed to add retention policy: {e}")
    
    async def get_chunk_info(self, table_name: str = "timeseries_data") -> List[Dict[str, Any]]:
        """Get information about chunks for a hypertable."""
        try:
            query = text("""
                SELECT 
                    chunk_name,
                    range_start,
                    range_end,
                    is_compressed,
                    before_compression_total_bytes,
                    after_compression_total_bytes
                FROM timescaledb_information.chunks
                WHERE hypertable_name = :table_name
                ORDER BY range_start DESC
            """)
            
            result = await self.session.execute(
                query,
                {"table_name": table_name}
            )
            
            chunks = []
            for row in result.fetchall():
                chunk_info = {
                    "chunk_name": row.chunk_name,
                    "range_start": row.range_start,
                    "range_end": row.range_end,
                    "is_compressed": row.is_compressed,
                    "size_before_compression": row.before_compression_total_bytes,
                    "size_after_compression": row.after_compression_total_bytes
                }
                
                if row.is_compressed and row.before_compression_total_bytes:
                    chunk_info["compression_ratio"] = (
                        row.before_compression_total_bytes / row.after_compression_total_bytes
                    )
                
                chunks.append(chunk_info)
            
            return chunks
        except SQLAlchemyError as e:
            raise PartitionerError(f"Failed to get chunk info: {e}")
    
    async def compress_chunks(
        self,
        table_name: str = "timeseries_data",
        older_than: Optional[datetime] = None
    ) -> int:
        """Manually compress chunks older than specified time."""
        if older_than is None:
            older_than = datetime.utcnow() - timedelta(days=7)
        
        try:
            query = text("""
                SELECT compress_chunk(c.oid)
                FROM show_chunks(:table_name, older_than => :older_than) c
                WHERE NOT is_compressed(c.oid)
            """)
            
            result = await self.session.execute(
                query,
                {
                    "table_name": table_name,
                    "older_than": older_than
                }
            )
            await self.session.commit()
            
            compressed_count = result.rowcount
            logger.info(f"Compressed {compressed_count} chunks")
            return compressed_count
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise PartitionerError(f"Failed to compress chunks: {e}")
    
    async def reorder_chunk(
        self,
        chunk_name: str,
        index_name: str
    ) -> None:
        """Reorder a chunk by specified index for better compression."""
        try:
            query = text("""
                SELECT reorder_chunk(:chunk_name, :index_name)
            """)
            
            await self.session.execute(
                query,
                {
                    "chunk_name": chunk_name,
                    "index_name": index_name
                }
            )
            await self.session.commit()
            
            logger.info(f"Reordered chunk {chunk_name} by {index_name}")
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise PartitionerError(f"Failed to reorder chunk: {e}")
    
    async def get_compression_stats(self, table_name: str = "timeseries_data") -> Dict[str, Any]:
        """Get compression statistics for hypertable."""
        try:
            query = text("""
                SELECT 
                    COUNT(*) FILTER (WHERE is_compressed) as compressed_chunks,
                    COUNT(*) FILTER (WHERE NOT is_compressed) as uncompressed_chunks,
                    SUM(before_compression_total_bytes) as total_before_compression,
                    SUM(after_compression_total_bytes) as total_after_compression
                FROM timescaledb_information.chunks
                WHERE hypertable_name = :table_name
            """)
            
            result = await self.session.execute(
                query,
                {"table_name": table_name}
            )
            
            row = result.first()
            stats = {
                "compressed_chunks": row.compressed_chunks or 0,
                "uncompressed_chunks": row.uncompressed_chunks or 0,
                "total_chunks": (row.compressed_chunks or 0) + (row.uncompressed_chunks or 0),
                "size_before_compression": row.total_before_compression or 0,
                "size_after_compression": row.total_after_compression or 0
            }
            
            if stats["size_before_compression"] > 0:
                stats["compression_ratio"] = (
                    stats["size_before_compression"] / stats["size_after_compression"]
                )
                stats["space_saved"] = (
                    stats["size_before_compression"] - stats["size_after_compression"]
                )
            
            return stats
        except SQLAlchemyError as e:
            raise PartitionerError(f"Failed to get compression stats: {e}")
