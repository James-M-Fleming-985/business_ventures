from datetime import datetime
from typing import Any, Dict

import redis.asyncio as redis
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_redis
from app.models.health import HealthResponse, ServiceStatus

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
) -> HealthResponse:
    """Check health status of all services."""
    services: Dict[str, ServiceStatus] = {}
    overall_status = "healthy"
    
    # Database health
    try:
        result = await db.execute(text("SELECT 1"))
        await result.scalar()
        services["database"] = ServiceStatus(
            status="healthy",
            message="Connected",
            timestamp=datetime.utcnow(),
        )
    except Exception as e:
        overall_status = "unhealthy"
        services["database"] = ServiceStatus(
            status="unhealthy",
            message=f"Connection failed: {str(e)}",
            timestamp=datetime.utcnow(),
        )
    
    # Redis health
    try:
        await redis_client.ping()
        services["redis"] = ServiceStatus(
            status="healthy",
            message="Connected",
            timestamp=datetime.utcnow(),
        )
    except Exception as e:
        overall_status = "degraded" if overall_status == "healthy" else overall_status
        services["redis"] = ServiceStatus(
            status="unhealthy",
            message=f"Connection failed: {str(e)}",
            timestamp=datetime.utcnow(),
        )
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        services=services,
    )


@router.get("/live", status_code=status.HTTP_204_NO_CONTENT)
async def liveness() -> None:
    """Simple liveness check."""
    return None


@router.get("/ready")
async def readiness(
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
) -> Dict[str, Any]:
    """Check if service is ready to handle requests."""
    ready = True
    checks = {}
    
    try:
        result = await db.execute(text("SELECT 1"))
        await result.scalar()
        checks["database"] = True
    except Exception:
        ready = False
        checks["database"] = False
    
    try:
        await redis_client.ping()
        checks["redis"] = True
    except Exception:
        ready = False
        checks["redis"] = False
    
    return {
        "ready": ready,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }