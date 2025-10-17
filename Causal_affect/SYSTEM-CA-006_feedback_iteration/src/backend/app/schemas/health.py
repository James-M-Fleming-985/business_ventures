"""Health check response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(
        description="Service health status",
        example="healthy"
    )
    timestamp: datetime = Field(
        description="Current server timestamp",
        example="2023-12-01T12:00:00Z"
    )
    version: Optional[str] = Field(
        default=None,
        description="API version",
        example="1.0.0"
    )
    service: str = Field(
        default="api",
        description="Service name",
        example="api"
    )
    database: Optional[str] = Field(
        default=None,
        description="Database connection status",
        example="connected"
    )
    redis: Optional[str] = Field(
        default=None,
        description="Redis connection status",
        example="connected"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "timestamp": "2023-12-01T12:00:00Z",
                "version": "1.0.0",
                "service": "api",
                "database": "connected",
                "redis": "connected"
            }
        }
    }
