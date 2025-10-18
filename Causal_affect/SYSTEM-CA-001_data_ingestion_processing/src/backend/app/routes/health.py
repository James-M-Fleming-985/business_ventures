from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
import asyncio

from app.db.session import get_db
from app.core.redis import get_redis
from app.models.health import HealthResponse, HealthStatus, ServiceHealth

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> HealthResponse:
    """Check overall system health."""
    services: Dict[str, ServiceHealth] = {}
    overall_status = HealthStatus.HEALTHY
    
    # Check database
    db_health = await _check_database(db)
    services["database"] = db_health
    if db_health.status != HealthStatus.HEALTHY:
        overall_status = HealthStatus.DEGRADED
    
    # Check Redis
    redis_health = await _check_redis(redis)
    services["redis"] = redis_health
    if redis_health.status != HealthStatus.HEALTHY:
        overall_status = HealthStatus.DEGRADED
    
    # If any critical service is down, mark as unhealthy
    critical_services = ["database"]
    for service in critical_services:
        if services[service].status == HealthStatus.UNHEALTHY:
            overall_status = HealthStatus.UNHEALTHY
            break
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        services=services
    )


@router.get("/live", response_model=Dict[str, str])
async def liveness_probe() -> Dict[str, str]:
    """Simple liveness check for k8s."""
    return {"status": "ok"}


@router.get("/ready", response_model=Dict[str, bool])
async def readiness_probe(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> Dict[str, bool]:
    """Readiness check for k8s."""
    try:
        # Quick DB check
        await db.execute("SELECT 1")
        
        # Quick Redis check
        await redis.ping()
        
        return {"ready": True}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


async def _check_database(db: AsyncSession) -> ServiceHealth:
    """Check database connectivity and response time."""
    start_time = asyncio.get_event_loop().time()
    try:
        result = await db.execute("SELECT 1")
        _ = result.scalar()
        response_time = asyncio.get_event_loop().time() - start_time
        
        return ServiceHealth(
            status=HealthStatus.HEALTHY,
            response_time=response_time,
            details={"connected": True}
        )
    except Exception as e:
        return ServiceHealth(
            status=HealthStatus.UNHEALTHY,
            response_time=None,
            details={"error": str(e), "connected": False}
        )


async def _check_redis(redis: Redis) -> ServiceHealth:
    """Check Redis connectivity and response time."""
    start_time = asyncio.get_event_loop().time()
    try:
        await redis.ping()
        response_time = asyncio.get_event_loop().time() - start_time
        
        # Check memory usage
        info = await redis.info("memory")
        used_memory = info.get("used_memory", 0)
        max_memory = info.get("maxmemory", 0)
        
        details = {
            "connected": True,
            "used_memory_mb": round(used_memory / 1024 / 1024, 2)
        }
        
        if max_memory > 0:
            memory_usage_percent = (used_memory / max_memory) * 100
            details["memory_usage_percent"] = round(memory_usage_percent, 2)
            
            if memory_usage_percent > 90:
                return ServiceHealth(
                    status=HealthStatus.DEGRADED,
                    response_time=response_time,
                    details={**details, "warning": "High memory usage"}
                )
        
        return ServiceHealth(
            status=HealthStatus.HEALTHY,
            response_time=response_time,
            details=details
        )
    except Exception as e:
        return ServiceHealth(
            status=HealthStatus.UNHEALTHY,
            response_time=None,
            details={"error": str(e), "connected": False}
        )
