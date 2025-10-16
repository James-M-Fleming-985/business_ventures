"""Health check response schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response model."""

    status: Literal["healthy", "unhealthy"] = Field(
        description="Service health status"
    )
    service: str = Field(description="Service name")
    version: str = Field(description="Service version")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "service": "FastAPI Service",
                    "version": "0.1.0",
                }
            ]
        }
    }
