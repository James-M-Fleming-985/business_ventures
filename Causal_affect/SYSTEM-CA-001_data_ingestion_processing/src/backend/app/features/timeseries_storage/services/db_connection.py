from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    database: str = "timeseries_db"
    user: str = "postgres"
    password: str = "postgres"
    min_pool_size: int = 10
    max_pool_size: int = 20
    command_timeout: float = 60.0
    
    @property
    def async_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def sync_url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class TimeseriesDBConnection:
    """Manages TimescaleDB connections with async support."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._engine: Optional[create_async_engine] = None
        self._sessionmaker: Optional[async_sessionmaker] = None
        self._raw_pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self) -> None:
        """Initialize database connections and enable TimescaleDB."""
        try:
            # SQLAlchemy async engine
            self._engine = create_async_engine(
                self.config.async_url,
                pool_size=self.config.min_pool_size,
                max_overflow=self.config.max_pool_size - self.config.min_pool_size,
                pool_pre_ping=True,
                echo=False
            )
            
            self._sessionmaker = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Raw asyncpg pool for performance-critical operations
            self._raw_pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                min_size=self.config.min_pool_size,
                max_size=self.config.max_pool_size,
                command_timeout=self.config.command_timeout
            )
            
            # Enable TimescaleDB extension
            async with self.get_raw_connection() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
                
            logger.info("Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get SQLAlchemy async session."""
        if not self._sessionmaker:
            raise RuntimeError("Database not initialized")
            
        async with self._sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    @asynccontextmanager
    async def get_raw_connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Get raw asyncpg connection for performance-critical operations."""
        if not self._raw_pool:
            raise RuntimeError("Database not initialized")
            
        async with self._raw_pool.acquire() as connection:
            yield connection
    
    async def execute_batch(self, query: str, data: list) -> None:
        """Execute batch insert for high throughput."""
        async with self.get_raw_connection() as conn:
            await conn.executemany(query, data)
    
    async def close(self) -> None:
        """Close all database connections."""
        if self._engine:
            await self._engine.dispose()
            
        if self._raw_pool:
            await self._raw_pool.close()
            
        logger.info("Database connections closed")
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.get_raw_connection() as conn:
                result = await conn.fetchval("SELECT 1")
                return result == 1
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# Global instance
_db_connection: Optional[TimeseriesDBConnection] = None


def get_db_connection(config: Optional[DatabaseConfig] = None) -> TimeseriesDBConnection:
    """Get or create database connection instance."""
    global _db_connection
    
    if _db_connection is None:
        if config is None:
            config = DatabaseConfig()
        _db_connection = TimeseriesDBConnection(config)
    
    return _db_connection