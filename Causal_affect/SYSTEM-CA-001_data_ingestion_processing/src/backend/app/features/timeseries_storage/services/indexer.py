from typing import List, Dict, Optional, Any
from enum import Enum
import asyncpg
import logging
from pydantic import BaseModel

from .db_connection import TimeseriesDBConnection

logger = logging.getLogger(__name__)


class IndexType(str, Enum):
    BTREE = "btree"
    HASH = "hash"
    GIN = "gin"
    GIST = "gist"
    BRIN = "brin"


class IndexConfig(BaseModel):
    name: str
    table: str
    columns: List[str]
    index_type: IndexType = IndexType.BTREE
    unique: bool = False
    where_clause: Optional[str] = None
    include_columns: Optional[List[str]] = None
    concurrent: bool = True


class IndexStats(BaseModel):
    index_name: str
    table_name: str
    index_size: str
    index_scans: int
    index_reads: int
    index_writes: int


class TimeseriesIndexer:
    """Manages indexes for timeseries data optimization."""
    
    def __init__(self, db_connection: TimeseriesDBConnection):
        self.db = db_connection
    
    async def create_index(self, config: IndexConfig) -> None:
        """Create index with specified configuration."""
        query_parts = [
            "CREATE",
            "UNIQUE" if config.unique else "",
            "INDEX",
            "CONCURRENTLY" if config.concurrent else "",
            f"IF NOT EXISTS {config.name}",
            "ON", config.table,
            f"USING {config.index_type.value}",
            f"({', '.join(config.columns)})"
        ]
        
        if config.include_columns:
            query_parts.append(f"INCLUDE ({', '.join(config.include_columns)})")
            
        if config.where_clause:
            query_parts.append(f"WHERE {config.where_clause}")
            
        query = " ".join(filter(None, query_parts))
        
        async with self.db.get_raw_connection() as conn:
            try:
                await conn.execute(query)
                logger.info(f"Created index {config.name} on {config.table}")
            except Exception as e:
                logger.error(f"Failed to create index: {e}")
                raise
    
    async def create_timeseries_indexes(self, table_name: str) -> None:
        """Create optimized indexes for timeseries queries."""
        indexes = [
            # Primary time-based index
            IndexConfig(
                name=f"{table_name}_timestamp_idx",
                table=table_name,
                columns=["timestamp"],
                index_type=IndexType.BTREE
            ),
            
            # Composite index for sensor queries
            IndexConfig(
                name=f"{table_name}_sensor_id_timestamp_idx",
                table=table_name,
                columns=["sensor_id", "timestamp"],
                index_type=IndexType.BTREE
            ),
            
            # BRIN index for large time ranges
            IndexConfig(
                name=f"{table_name}_timestamp_brin_idx",
                table=table_name,
                columns=["timestamp"],
                index_type=IndexType.BRIN
            )
        ]
        
        for index_config in indexes:
            await self.create_index(index_config)
    
    async def create_metadata_indexes(self, table_name: str) -> None:
        """Create indexes for metadata/tags columns."""
        # GIN index for JSONB tags
        await self.create_index(
            IndexConfig(
                name=f"{table_name}_tags_idx",
                table=table_name,
                columns=["tags"],
                index_type=IndexType.GIN
            )
        )
        
        # Expression index for frequently queried tag
        async with self.db.get_raw_connection() as conn:
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {table_name}_location_idx 
                ON {table_name} ((tags->>'location'))
            """)
    
    async def analyze_index_usage(self, table_name: str) -> List[IndexStats]:
        """Analyze index usage statistics."""
        query = """
            SELECT 
                indexrelname as index_name,
                relname as table_name,
                pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
                idx_scan as index_scans,
                idx_tup_read as index_reads,
                idx_tup_fetch as index_writes
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public' 
            AND relname = $1
            ORDER BY idx_scan DESC
        """
        
        async with self.db.get_raw_connection() as conn:
            rows = await conn.fetch(query, table_name)
            
            return [
                IndexStats(
                    index_name=row['index_name'],
                    table_name=row['table_name'],
                    index_size=row['index_size'],
                    index_scans=row['index_scans'],
                    index_reads=row['index_reads'],
                    index_writes=row['index_writes']
                )
                for row in rows
            ]
    
    async def recommend_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Recommend indexes based on query patterns."""
        recommendations = []
        
        async with self.db.get_raw_connection() as conn:
            # Check for missing indexes on foreign keys
            fk_query = """
                SELECT DISTINCT
                    tc.constraint_name,
                    tc.table_name,
                    kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_name = $1
                    AND NOT EXISTS (
                        SELECT 1 FROM pg_indexes
                        WHERE tablename = tc.table_name
                        AND indexdef LIKE '%' || kcu.column_name || '%'
                    )
            """
            
            fk_results = await conn.fetch(fk_query, table_name)
            for row in fk_results:
                recommendations.append({
                    "reason": "Missing index on foreign key",
                    "column": row['column_name'],
                    "suggested_index": f"CREATE INDEX ON {table_name}({row['column_name']})"
                })
            
            # Check for slow queries without indexes
            slow_query = """
                SELECT 
                    query,
                    calls,
                    mean_exec_time,
                    total_exec_time
                FROM pg_stat_statements
                WHERE query LIKE $1
                    AND mean_exec_time > 100  -- queries slower than 100ms
                ORDER BY mean_exec_time DESC
                LIMIT 10
            """
            
            try:
                slow_results = await conn.fetch(slow_query, f'%{table_name}%')
                for row in slow_results:
                    # Simple pattern matching for WHERE clauses
                    query = row['query'].lower()
                    if 'where' in query:
                        where_idx = query.index('where')
                        where_clause = query[where_idx:]
                        
                        # Extract potential index columns
                        import re
                        columns = re.findall(r'(\w+)\s*[=<>]', where_clause)
                        if columns:
                            recommendations.append({
                                "reason": "Slow query detected",
                                "query": row['query'][:100] + "...",
                                "mean_time_ms": row['mean_exec_time'],
                                "suggested_columns": list(set(columns))
                            })
            except Exception:
                # pg_stat_statements might not be available
                pass
                
        return recommendations
    
    async def reindex_table(self, table_name: str, concurrent: bool = True) -> None:
        """Reindex all indexes on a table."""
        mode = "CONCURRENTLY" if concurrent else ""
        
        async with self.db.get_raw_connection() as conn:
            await conn.execute(f"REINDEX TABLE {mode} {table_name}")
            logger.info(f"Reindexed table {table_name}")
    
    async def drop_unused_indexes(self, table_name: str, min_scans: int = 10) -> List[str]:
        """Drop indexes with low usage."""
        query = """
            SELECT indexrelname
            FROM pg_stat_user_indexes
            WHERE relname = $1
                AND idx_scan < $2
                AND indexrelname NOT LIKE '%_pkey'
                AND indexrelname NOT LIKE '%_constraint'
        """
        
        dropped = []
        async with self.db.get_raw_connection() as conn:
            unused = await conn.fetch(query, table_name, min_scans)
            
            for row in unused:
                index_name = row['indexrelname']
                await conn.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {index_name}")
                dropped.append(index_name)
                logger.info(f"Dropped unused index {index_name}")
                
        return dropped