from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import asyncpg
import logging
from pydantic import BaseModel

from .db_connection import TimeseriesDBConnection

logger = logging.getLogger(__name__)


class CompressionAlgorithm(str, Enum):
    GORILLA = "gorilla"
    DELTA_DELTA = "delta-delta"
    DICTIONARY = "dictionary"
    LZ4 = "lz4"


class CompressionConfig(BaseModel):
    algorithm: CompressionAlgorithm = CompressionAlgorithm.GORILLA
    segment_by: List[str] = ["sensor_id"]
    order_by: List[str] = ["timestamp"]
    chunk_time_interval: str = "1 day"
    compress_after: str = "7 days"


class CompressionStats(BaseModel):
    table_name: str
    total_chunks: int
    compressed_chunks: int
    uncompressed_size: str
    compressed_size: str
    compression_ratio: float
    saved_space: str


class TimeseriesCompressor:
    """Manages TimescaleDB compression for storage optimization."""
    
    def __init__(self, db_connection: TimeseriesDBConnection):
        self.db = db_connection
    
    async def setup_compression(
        self,
        table_name: str,
        config: CompressionConfig
    ) -> None:
        """Configure compression settings for hypertable."""
        async with self.db.get_raw_connection() as conn:
            # Build compression settings
            settings = []
            settings.append("timescaledb.compress")
            
            if config.segment_by:
                settings.append(f"timescaledb.compress_segmentby = '{','.join(config.segment_by)}'")
            
            if config.order_by:
                settings.append(f"timescaledb.compress_orderby = '{','.join(config.order_by)}'")
            
            # Apply compression settings
            await conn.execute(f"""
                ALTER TABLE {table_name} SET (
                    {','.join(settings)}
                )
            """)
            
            # Add compression policy
            await conn.execute(f"""
                SELECT add_compression_policy('{table_name}',
                    compress_after => INTERVAL '{config.compress_after}',
                    if_not_exists => TRUE
                )
            """)
            
            logger.info(f"Compression configured for {table_name}")
    
    async def compress_chunks(
        self,
        table_name: str,
        older_than: Optional[datetime] = None
    ) -> int:
        """Manually compress chunks older than specified date."""
        compressed_count = 0
        
        async with self.db.get_raw_connection() as conn:
            # Get uncompressed chunks
            if older_than:
                chunks_query = """
                    SELECT chunk_name
                    FROM timescaledb_information.chunks
                    WHERE hypertable_name = $1
                        AND NOT is_compressed
                        AND range_end < $2
                    ORDER BY range_start
                """
                chunks = await conn.fetch(chunks_query, table_name, older_than)
            else:
                chunks_query = """
                    SELECT chunk_name
                    FROM timescaledb_information.chunks
                    WHERE hypertable_name = $1
                        AND NOT is_compressed
                    ORDER BY range_start
                """
                chunks = await conn.fetch(chunks_query, table_name)
            
            # Compress each chunk
            for chunk in chunks:
                chunk_name = chunk['chunk_name']
                try:
                    await conn.execute(f"SELECT compress_chunk('{chunk_name}')")
                    compressed_count += 1
                    logger.info(f"Compressed chunk {chunk_name}")
                except Exception as e:
                    logger.error(f"Failed to compress chunk {chunk_name}: {e}")
                    
        return compressed_count
    
    async def decompress_chunks(
        self,
        table_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """Decompress chunks in time range for updates."""
        decompressed_count = 0
        
        async with self.db.get_raw_connection() as conn:
            chunks_query = """
                SELECT chunk_name
                FROM timescaledb_information.chunks
                WHERE hypertable_name = $1
                    AND is_compressed
                    AND range_start < $2
                    AND range_end > $3
            """
            
            chunks = await conn.fetch(chunks_query, table_name, end_time, start_time)
            
            for chunk in chunks:
                chunk_name = chunk['chunk_name']
                try:
                    await conn.execute(f"SELECT decompress_chunk('{chunk_name}')")
                    decompressed_count += 1
                    logger.info(f"Decompressed chunk {chunk_name}")
                except Exception as e:
                    logger.error(f"Failed to decompress chunk {chunk_name}: {e}")
                    
        return decompressed_count
    
    async def get_compression_stats(self, table_name: str) -> CompressionStats:
        """Get compression statistics for hypertable."""
        query = """
            WITH stats AS (
                SELECT 
                    COUNT(*) as total_chunks,
                    COUNT(*) FILTER (WHERE is_compressed) as compressed_chunks,
                    COALESCE(SUM(CASE WHEN NOT is_compressed THEN total_bytes ELSE 0 END), 0) as uncompressed_bytes,
                    COALESCE(SUM(CASE WHEN is_compressed THEN total_bytes ELSE 0 END), 0) as compressed_bytes,
                    COALESCE(SUM(before_compression_total_bytes), 0) as original_size
                FROM timescaledb_information.chunks
                WHERE hypertable_name = $1
            )
            SELECT 
                total_chunks,
                compressed_chunks,
                pg_size_pretty(uncompressed_bytes) as uncompressed_size,
                pg_size_pretty(compressed_bytes) as compressed_size,
                CASE 
                    WHEN original_size > 0 
                    THEN ROUND((1.0 - (compressed_bytes::float / original_size)) * 100, 2)
                    ELSE 0 
                END as compression_ratio,
                pg_size_pretty(original_size - compressed_bytes) as saved_space
            FROM stats
        """
        
        async with self.db.get_raw_connection() as conn:
            result = await conn.fetchrow(query, table_name)
            
            if result:
                return CompressionStats(
                    table_name=table_name,
                    total_chunks=result['total_chunks'],
                    compressed_chunks=result['compressed_chunks'],
                    uncompressed_size=result['uncompressed_size'],
                    compressed_size=result['compressed_size'],
                    compression_ratio=result['compression_ratio'],
                    saved_space=result['saved_space']
                )
            else:
                return CompressionStats(
                    table_name=table_name,
                    total_chunks=0,
                    compressed_chunks=0,
                    uncompressed_size="0 bytes",
                    compressed_size="0 bytes",
                    compression_ratio=0.0,
                    saved_space="0 bytes"
                )
    
    async def optimize_compression_settings(
        self,
        table_name: str,
        sample_size: int = 1000
    ) -> Dict[str, Any]:
        """Analyze data and recommend optimal compression settings."""
        recommendations = {
            "current_settings": {},
            "recommendations": [],
            "estimated_savings": {}
        }
        
        async with self.db.get_raw_connection() as conn:
            # Get current settings
            current_query = """
                SELECT 
                    chunk_name,
                    compression_algorithm_name,
                    total_bytes,
                    before_compression_total_bytes
                FROM timescaledb_information.compression_settings cs
                JOIN timescaledb_information.chunks ch USING (hypertable_name)
                WHERE hypertable_name = $1 AND is_compressed
                LIMIT 1
            """
            
            current = await conn.fetchrow(current_query, table_name)
            if current:
                recommendations["current_settings"] = {
                    "algorithm": current['compression_algorithm_name'],
                    "current_ratio": round(
                        (1 - current['total_bytes'] / current['before_compression_total_bytes']) * 100, 2
                    ) if current['before_compression_total_bytes'] > 0 else 0
                }
            
            # Analyze data patterns
            pattern_query = f"""
                WITH sample AS (
                    SELECT 
                        sensor_id,
                        value,
                        LAG(value) OVER (PARTITION BY sensor_id ORDER BY timestamp) as prev_value,
                        timestamp,
                        LAG(timestamp) OVER (PARTITION BY sensor_id ORDER BY timestamp) as prev_timestamp
                    FROM {table_name}
                    WHERE timestamp > NOW() - INTERVAL '1 day'
                    LIMIT {sample_size}
                )
                SELECT 
                    COUNT(DISTINCT sensor_id) as unique_sensors,
                    AVG(ABS(value - prev_value)) as avg_value_delta,
                    STDDEV(value) as value_stddev,
                    AVG(EXTRACT(EPOCH FROM (timestamp - prev_timestamp))) as avg_time_delta
                FROM sample
                WHERE prev_value IS NOT NULL
            """
            
            patterns = await conn.fetchrow(pattern_query)
            
            if patterns:
                # Recommend algorithm based on data patterns
                if patterns['avg_value_delta'] < patterns['value_stddev'] * 0.1:
                    # Values change slowly - delta encoding is good
                    recommendations["recommendations"].append({
                        "setting": "compression_algorithm",
                        "value": "delta-delta",
                        "reason": "Data shows small incremental changes"
                    })
                elif patterns['avg_time_delta'] and patterns['avg_time_delta'] < 60:
                    # High frequency data - Gorilla is optimal
                    recommendations["recommendations"].append({
                        "setting": "compression_algorithm", 
                        "value": "gorilla",
                        "reason": "High frequency timeseries data detected"
                    })
                
                # Segment recommendations
                if patterns['unique_sensors'] > 100:
                    recommendations["recommendations"].append({
                        "setting": "segment_by",
                        "value": "sensor_id",
                        "reason": f"High cardinality ({patterns['unique_sensors']} sensors) benefits from segmentation"
                    })
            
            # Estimate savings
            savings_query = """
                SELECT 
                    SUM(CASE WHEN NOT is_compressed THEN total_bytes ELSE 0 END) as uncompressed_bytes
                FROM timescaledb_information.chunks
                WHERE hypertable_name = $1
            """
            
            savings = await conn.fetchrow(savings_query, table_name)
            if savings and savings['uncompressed_bytes']:
                # Estimate 60-80% compression ratio
                estimated_compressed = savings['uncompressed_bytes'] * 0.3
                estimated_savings = savings['uncompressed_bytes'] * 0.7
                
                recommendations["estimated_savings"] = {
                    "current_uncompressed": f"{savings['uncompressed_bytes'] / (1024**3):.2f} GB",
                    "estimated_compressed": f"{estimated_compressed / (1024**3):.2f} GB",
                    "estimated_savings": f"{estimated_savings / (1024**3):.2f} GB"
                }
                
        return recommendations
    
    async def create_compression_job(
        self,
        table_name: str,
        schedule_interval: str = "1 hour"
    ) -> int:
        """Create background job for compression."""
        async with self.db.get_raw_connection() as conn:
            job_id = await conn.fetchval("""
                SELECT add_job(
                    'compress_chunks',
                    schedule_interval => INTERVAL $1,
                    config => jsonb_build_object(
                        'hypertable_name', $2,
                        'compress_after', '7 days'
                    )
                )
            """, schedule_interval, table_name)
            
            logger.info(f"Created compression job {job_id} for {table_name}")
            return job_id