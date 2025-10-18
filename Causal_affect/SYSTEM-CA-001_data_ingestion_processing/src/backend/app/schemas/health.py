from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field


class ServiceStatus(str, Enum):
    """Service health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ServiceHealth(BaseModel):
    """Individual service health check."""
    status: ServiceStatus
    message: Optional[str] = None
    latency_ms: Optional[float] = Field(None, description="Service response time in milliseconds")
    metadata: Optional[Dict[str, any]] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: ServiceStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    services: Dict[str, ServiceHealth] = Field(
        default_factory=dict,
        description="Health status of individual services"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2023-11-20T10:30:00Z",
                "version": "1.0.0",
                "services": {
                    "database": {
                        "status": "healthy",
                        "latency_ms": 2.5
                    },
                    "redis": {
                        "status": "healthy",
                        "latency_ms": 0.8
                    }
                }
            }
        }