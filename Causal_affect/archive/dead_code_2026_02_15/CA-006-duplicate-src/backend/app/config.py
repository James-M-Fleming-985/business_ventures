"""Application configuration using Pydantic Settings."""

from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    app_name: str = Field(default="FastAPI App", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Environment name",
    )
    
    # API
    api_prefix: str = Field(default="/api", description="API prefix")
    docs_enabled: bool = Field(default=True, description="Enable API documentation")
    
    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://user:password@localhost/dbname",
        description="PostgreSQL connection URL",
    )
    db_pool_size: int = Field(default=20, ge=1, description="Database pool size")
    db_max_overflow: int = Field(default=10, ge=0, description="Database max overflow")
    db_echo_queries: bool = Field(default=False, description="Echo SQL queries")
    
    # Redis
    redis_enabled: bool = Field(default=True, description="Enable Redis caching")
    redis_url: RedisDsn = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    redis_pool_size: int = Field(default=10, ge=1, description="Redis pool size")
    redis_ttl: int = Field(default=3600, ge=1, description="Default Redis TTL in seconds")
    
    # Security
    secret_key: str = Field(
        default="your-secret-key-here",
        description="Secret key for JWT and other cryptographic operations",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expire_minutes: int = Field(default=30, ge=1, description="JWT expiration in minutes")
    
    # CORS
    cors_enabled: bool = Field(default=True, description="Enable CORS")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow credentials in CORS")
    cors_allow_methods: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "PATCH"],
        description="Allowed CORS methods",
    )
    cors_allow_headers: list[str] = Field(
        default=["*"],
        description="Allowed CORS headers",
    )
    
    # Feature Flags
    feature_user_registration: bool = Field(
        default=True,
        description="Enable user registration",
    )
    feature_email_verification: bool = Field(
        default=True,
        description="Enable email verification",
    )
    feature_password_reset: bool = Field(
        default=True,
        description="Enable password reset",
    )
    feature_social_auth: bool = Field(
        default=False,
        description="Enable social authentication",
    )
    feature_two_factor_auth: bool = Field(
        default=False,
        description="Enable two-factor authentication",
    )
    feature_api_rate_limiting: bool = Field(
        default=True,
        description="Enable API rate limiting",
    )
    feature_webhook_notifications: bool = Field(
        default=False,
        description="Enable webhook notifications",
    )
    feature_audit_logging: bool = Field(
        default=True,
        description="Enable audit logging",
    )
    feature_data_export: bool = Field(
        default=False,
        description="Enable data export functionality",
    )
    feature_analytics: bool = Field(
        default=False,
        description="Enable analytics tracking",
    )
    
    # Rate Limiting
    rate_limit_requests: int = Field(
        default=100,
        ge=1,
        description="Rate limit requests per window",
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        ge=1,
        description="Rate limit window in seconds",
    )
    
    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: PostgresDsn) -> str:
        """Convert PostgresDsn to string for asyncpg."""
        return str(v)
    
    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, v: RedisDsn) -> str:
        """Convert RedisDsn to string."""
        return str(v)
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate and normalize environment name."""
        return v.lower()
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic."""
        return self.database_url.replace("postgresql+asyncpg", "postgresql")


# Create settings instance
settings = Settings()
