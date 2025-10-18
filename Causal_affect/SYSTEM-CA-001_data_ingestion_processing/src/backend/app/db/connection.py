"""Database connection and session management."""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from app.core.config import settings
from app.core.exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)

# Create async engine
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    poolclass=NullPool if settings.TESTING else None,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database connection and create TimescaleDB extensions."""
    try:
        async with async_engine.begin() as conn:
            # Check connection
            await conn.execute(text("SELECT 1"))
            logger.info("Database connection established")
            
            # Create TimescaleDB extension if not exists
            await conn.execute(
                text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")
            )
            logger.info("TimescaleDB extension created/verified")
            
            # Create UUID extension if not exists
            await conn.execute(
                text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
            )
            logger.info("UUID extension created/verified")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise DatabaseConnectionError(f"Database initialization failed: {e}")


async def close_db() -> None:
    """Close database connection."""
    await async_engine.dispose()
    logger.info("Database connection closed")


async def check_db_connection() -> bool:
    """Check if database is accessible."""
    try:
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


async def create_hypertable(
    table_name: str,
    time_column: str = "created_at",
    partitioning_column: str | None = None,
    number_partitions: int = 4,
    chunk_time_interval: str = "1 week",
) -> None:
    """Create a TimescaleDB hypertable.
    
    Args:
        table_name: Name of the table to convert
        time_column: Name of the time column for partitioning
        partitioning_column: Optional space partitioning column
        number_partitions: Number of space partitions
        chunk_time_interval: Time interval for chunks
    """
    try:
        async with async_engine.begin() as conn:
            if partitioning_column:
                query = text(
                    f"SELECT create_hypertable('{table_name}', '{time_column}', "
                    f"partitioning_column => '{partitioning_column}', "
                    f"number_partitions => {number_partitions}, "
                    f"chunk_time_interval => INTERVAL '{chunk_time_interval}', "
                    f"if_not_exists => TRUE)"
                )
            else:
                query = text(
                    f"SELECT create_hypertable('{table_name}', '{time_column}', "
                    f"chunk_time_interval => INTERVAL '{chunk_time_interval}', "
                    f"if_not_exists => TRUE)"
                )
            
            await conn.execute(query)
            logger.info(f"Hypertable {table_name} created/verified")
            
    except Exception as e:
        logger.error(f"Failed to create hypertable {table_name}: {e}")
        raise DatabaseConnectionError(f"Hypertable creation failed: {e}")


async def add_retention_policy(
    table_name: str,
    retention_period: str = "30 days",
) -> None:
    """Add retention policy to a hypertable.
    
    Args:
        table_name: Name of the hypertable
        retention_period: How long to keep data
    """
    try:
        async with async_engine.begin() as conn:
            query = text(
                f"SELECT add_retention_policy('{table_name}', "
                f"INTERVAL '{retention_period}', if_not_exists => TRUE)"
            )
            await conn.execute(query)
            logger.info(f"Retention policy added to {table_name}: {retention_period}")
            
    except Exception as e:
        logger.error(f"Failed to add retention policy to {table_name}: {e}")
        raise DatabaseConnectionError(f"Retention policy creation failed: {e}")


async def create_continuous_aggregate(
    view_name: str,
    query: str,
    refresh_interval: str = "1 hour",
) -> None:
    """Create a continuous aggregate view.
    
    Args:
        view_name: Name of the continuous aggregate view
        query: SELECT query for the view
        refresh_interval: How often to refresh the view
    """
    try:
        async with async_engine.begin() as conn:
            # Create the continuous aggregate
            create_query = text(
                f"CREATE MATERIALIZED VIEW IF NOT EXISTS {view_name} "
                f"WITH (timescaledb.continuous) AS {query}"
            )
            await conn.execute(create_query)
            
            # Add refresh policy
            refresh_query = text(
                f"SELECT add_continuous_aggregate_policy('{view_name}', "
                f"start_offset => NULL, "
                f"end_offset => INTERVAL '1 hour', "
                f"schedule_interval => INTERVAL '{refresh_interval}', "
                f"if_not_exists => TRUE)"
            )
            await conn.execute(refresh_query)
            
            logger.info(f"Continuous aggregate {view_name} created")
            
    except Exception as e:
        logger.error(f"Failed to create continuous aggregate {view_name}: {e}")
        raise DatabaseConnectionError(f"Continuous aggregate creation failed: {e}")