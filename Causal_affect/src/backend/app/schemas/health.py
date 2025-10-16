"""Health check schema models."""

from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="Application version")
    database: str = Field(default="unknown", description="Database connection status")
    redis: Optional[str] = Field(default=None, description="Redis connection status")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "version": "0.1.0",
                    "database": "connected",
                    "redis": "connected",
                }
            ]
        }
    }
