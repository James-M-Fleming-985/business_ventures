from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncpg
import logging
from pydantic import BaseModel

from .db_connection import TimeseriesDBConnection

logger = logging.getLogger(__name__)


class PartitionConfig(BaseModel):
    interval: str = "1 day"  # PostgreSQL interval format
    retention_days: int = 30
    chunk_time_interval: str = "1 day"
    compress_after_days: int = 7
    

class PartitionInfo(BaseModel):
    table_name: str
    partition_name: str
    start_time: datetime
    end_time: datetime
    is_compressed: bool
    size_bytes: Optional[int] = None


class TimeseriesPartitioner:
    """Manages TimescaleDB hypertable partitioning."""
    
    def __init__(self, db_connection: TimeseriesDBConnection, config: PartitionConfig):
        self.db = db_connection
        self.config = config
    
    async def create_hypertable(
        self,
        table_name: str,
        time_column: str = "timestamp",
        partitioning_column: Optional[str] = None,
        number_partitions: Optional[int] = None,
        chunk_time_interval: Optional[str] = None
    ) -> None:
        """Convert table to hypertable with automatic partitioning."""
        query_parts = [
            f"SELECT create_hypertable('{table_name}', '{time_column}'"
        ]
        
        if partitioning_column:
            query_parts.append(f", partitioning_column => '{partitioning_column}'")
            
        if number_partitions:
            query_parts.append(f", number_partitions => {number_partitions}")
            
        query_parts.append(f", chunk_time_interval => INTERVAL '{chunk_time_interval or self.config.chunk_time_interval}'")
        query_parts.append(", if_not_exists => TRUE)")
        
        query = "".join(query_parts)
        
        async with self.db.get_raw_connection() as conn:
            try:
                await conn.execute(query)
                logger.info(f"Created hypertable for {table_name}")
                
                # Set retention policy
                await self._set_retention_policy(conn, table_name)
                
                # Enable compression
                await self._enable_compression(conn, table_name)
                
            except Exception as e:
                logger.error(f"Failed to create hypertable: {e}")
                raise
    
    async def _set_retention_policy(self, conn: asyncpg.Connection, table_name: str) -> None:
        """Set data retention policy for hypertable."""
        await conn.execute(f"""
            SELECT add_retention_policy('{table_name}', 
                drop_after => INTERVAL '{self.config.retention_days} days',
                if_not_exists => TRUE)
        """)
    
    async def _enable_compression(self, conn: asyncpg.Connection, table_name: str) -> None:
        """Enable compression policy for old chunks."""
        # Enable compression
        await conn.execute(f"""
            ALTER TABLE {table_name} SET (
                timescaledb.compress,
                timescaledb.compress_segmentby = 'sensor_id'
            )
        """)
        
        # Add compression policy
        await conn.execute(f"""
            SELECT add_compression_policy('{table_name}',
                compress_after => INTERVAL '{self.config.compress_after_days} days',
                if_not_exists => TRUE)
        """)
    
    async def get_partitions(self, table_name: str) -> List[PartitionInfo]:
        """Get information about table partitions."""
        query = """
            SELECT 
                ch.hypertable_name,
                ch.chunk_name,
                ch.range_start,
                ch.range_end,
                ch.is_compressed,
                pg_size_pretty(ch.total_bytes) as size
            FROM timescaledb_information.chunks ch
            WHERE ch.hypertable_name = $1
            ORDER BY ch.range_start DESC
        """
        
        async with self.db.get_raw_connection() as conn:
            rows = await conn.fetch(query, table_name)
            
            return [
                PartitionInfo(
                    table_name=row['hypertable_name'],
                    partition_name=row['chunk_name'],
                    start_time=row['range_start'],
                    end_time=row['range_end'],
                    is_compressed=row['is_compressed'],
                    size_bytes=row.get('total_bytes')
                )
                for row in rows
            ]
    
    async def create_continuous_aggregate(
        self,
        view_name: str,
        source_table: str,
        time_bucket: str,
        aggregations: Dict[str, str]
    ) -> None:
        """Create continuous aggregate view for fast queries."""
        agg_columns = ", ".join([
            f"{agg_func}({column}) as {alias}"
            for alias, (column, agg_func) in aggregations.items()
        ])
        
        query = f"""
            CREATE MATERIALIZED VIEW {view_name}
            WITH (timescaledb.continuous) AS
            SELECT 
                time_bucket('{time_bucket}', timestamp) AS bucket,
                sensor_id,
                {agg_columns}
            FROM {source_table}
            GROUP BY bucket, sensor_id
            WITH NO DATA
        """
        
        async with self.db.get_raw_connection() as conn:
            await conn.execute(query)
            
            # Add refresh policy
            await conn.execute(f"""
                SELECT add_continuous_aggregate_policy('{view_name}',
                    start_offset => INTERVAL '1 month',
                    end_offset => INTERVAL '1 hour',
                    schedule_interval => INTERVAL '1 hour',
                    if_not_exists => TRUE)
            """)
    
    async def optimize_chunks(self, table_name: str) -> None:
        """Reorder chunks for better query performance."""
        async with self.db.get_raw_connection() as conn:
            # Get uncompressed chunks older than 1 day
            chunks = await conn.fetch("""
                SELECT chunk_name 
                FROM timescaledb_information.chunks
                WHERE hypertable_name = $1
                AND NOT is_compressed
                AND range_end < NOW() - INTERVAL '1 day'
            """, table_name)
            
            for chunk in chunks:
                chunk_name = chunk['chunk_name']
                await conn.execute(f"""
                    SELECT reorder_chunk('{chunk_name}', '{table_name}_sensor_id_timestamp_idx')
                """)
                logger.info(f"Reordered chunk {chunk_name}")
    
    async def manual_compression(self, table_name: str, before_date: datetime) -> int:
        """Manually compress chunks before specified date."""
        async with self.db.get_raw_connection() as conn:
            result = await conn.fetchval("""
                SELECT compress_chunk(ch.chunk_name)
                FROM show_chunks($1, older_than => $2) ch
            """, table_name, before_date)
            
            return result or 0
    
    async def get_partition_stats(self, table_name: str) -> Dict[str, Any]:
        """Get partition statistics."""
        async with self.db.get_raw_connection() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_chunks,
                    COUNT(*) FILTER (WHERE is_compressed) as compressed_chunks,
                    pg_size_pretty(SUM(total_bytes)) as total_size,
                    pg_size_pretty(SUM(total_bytes) FILTER (WHERE is_compressed)) as compressed_size
                FROM timescaledb_information.chunks
                WHERE hypertable_name = $1
            """, table_name)
            
            return dict(stats) if stats else {}