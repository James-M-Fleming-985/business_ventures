"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

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
    APP_NAME: str = Field(default="FastAPI Application")
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")

    # Database
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/app"
    )
    DB_POOL_SIZE: int = Field(default=5)
    DB_MAX_OVERFLOW: int = Field(default=10)
    DB_POOL_TIMEOUT: int = Field(default=30)
    DB_ECHO: bool = Field(default=False)

    # Redis
    REDIS_URL: Optional[RedisDsn] = Field(default="redis://localhost:6379/0")
    REDIS_POOL_SIZE: int = Field(default=10)

    # CORS
    CORS_ORIGINS: list[str] = Field(default=["*"])
    CORS_CREDENTIALS: bool = Field(default=True)
    CORS_METHODS: list[str] = Field(default=["*"])
    CORS_HEADERS: list[str] = Field(default=["*"])

    # Feature Flags
    ENABLE_REDIS_CACHE: bool = Field(default=True)
    ENABLE_REQUEST_LOGGING: bool = Field(default=True)
    ENABLE_METRICS: bool = Field(default=False)

    # Security
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
