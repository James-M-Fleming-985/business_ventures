"""Application configuration."""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/causal_affect"
    )
    
    # API Settings
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    
    # CORS
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")
    
    # Signal Radar Settings
    signal_lookback_days: int = int(os.getenv("SIGNAL_LOOKBACK_DAYS", "7"))
    signal_min_momentum: float = float(os.getenv("SIGNAL_MIN_MOMENTUM", "30.0"))
    signal_min_data_points: int = int(os.getenv("SIGNAL_MIN_DATA_POINTS", "10"))
    
    # Granger Test Settings
    granger_max_lag: int = int(os.getenv("GRANGER_MAX_LAG", "30"))
    granger_min_observations: int = int(os.getenv("GRANGER_MIN_OBSERVATIONS", "50"))
    
    class Config:
        case_sensitive = False
        env_file = ".env"


settings = Settings()
