"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = Field(default="FastAPI Service", description="Application name")
    DEBUG: bool = Field(default=False, description="Debug mode")
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development", description="Environment name"
    )

    # Database
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/app",
        description="PostgreSQL database URL",
    )
    DB_POOL_SIZE: int = Field(default=5, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(
        default=10, description="Maximum overflow connections"
    )
    DB_ECHO: bool = Field(default=False, description="Echo SQL queries")

    # Redis
    REDIS_URL: RedisDsn = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )
    REDIS_POOL_SIZE: int = Field(default=10, description="Redis connection pool size")

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(
        default=True, description="Allow credentials in CORS"
    )
    CORS_ALLOW_METHODS: list[str] = Field(
        default=["*"], description="Allowed HTTP methods"
    )
    CORS_ALLOW_HEADERS: list[str] = Field(
        default=["*"], description="Allowed HTTP headers"
    )

    # Feature Flags
    ENABLE_METRICS: bool = Field(default=True, description="Enable metrics collection")
    ENABLE_TRACING: bool = Field(default=False, description="Enable request tracing")
    ENABLE_RATE_LIMITING: bool = Field(
        default=True, description="Enable rate limiting"
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        default="json", description="Log format (json or text)"
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
