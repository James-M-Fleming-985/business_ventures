from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.db.session import get_db
from app.core.redis import get_redis
from app.models.status import (
    FeatureStatus,
    FeatureStatusCreate,
    FeatureStatusUpdate,
    FeatureStatusResponse,
    SystemStatus,
    SystemStatusResponse,
    StatusType
)
from app.services.status import StatusService
from app.core.exceptions import FeatureNotFoundError

router = APIRouter()


@router.get("/features", response_model=List[FeatureStatusResponse])
async def list_feature_statuses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_type: Optional[StatusType] = None,
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> List[FeatureStatusResponse]:
    """List all feature statuses with filtering options."""
    service = StatusService(db, redis)
    return await service.list_features(
        skip=skip,
        limit=limit,
        status_type=status_type,
        active_only=active_only
    )


@router.get("/features/{feature_id}", response_model=FeatureStatusResponse)
async def get_feature_status(
    feature_id: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> FeatureStatusResponse:
    """Get status for a specific feature."""
    service = StatusService(db, redis)
    try:
        return await service.get_feature_status(feature_id)
    except FeatureNotFoundError:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Feature {feature_id} not found"
        )


@router.post("/features", response_model=FeatureStatusResponse)
async def create_feature_status(
    feature: FeatureStatusCreate,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> FeatureStatusResponse:
    """Create a new feature status entry."""
    service = StatusService(db, redis)
    return await service.create_feature_status(feature)


@router.put("/features/{feature_id}", response_model=FeatureStatusResponse)
async def update_feature_status(
    feature_id: str,
    update: FeatureStatusUpdate,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> FeatureStatusResponse:
    """Update an existing feature status."""
    service = StatusService(db, redis)
    try:
        return await service.update_feature_status(feature_id, update)
    except FeatureNotFoundError:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Feature {feature_id} not found"
        )


@router.delete("/features/{feature_id}")
async def delete_feature_status(
    feature_id: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> Dict[str, str]:
    """Delete a feature status entry."""
    service = StatusService(db, redis)
    try:
        await service.delete_feature_status(feature_id)
        return {"message": f"Feature {feature_id} deleted successfully"}
    except FeatureNotFoundError:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Feature {feature_id} not found"
        )


@router.get("/system", response_model=SystemStatusResponse)
async def get_system_status(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> SystemStatusResponse:
    """Get overall system status including all components."""
    service = StatusService(db, redis)
    return await service.get_system_status()


@router.post("/features/{feature_id}/toggle")
async def toggle_feature(
    feature_id: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> Dict[str, Any]:
    """Toggle a feature on/off."""
    service = StatusService(db, redis)
    try:
        new_status = await service.toggle_feature(feature_id)
        return {
            "feature_id": feature_id,
            "active": new_status,
            "toggled_at": datetime.utcnow()
        }
    except FeatureNotFoundError:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Feature {feature_id} not found"
        )


@router.get("/features/{feature_id}/history", response_model=List[Dict[str, Any]])
async def get_feature_history(
    feature_id: str,
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> List[Dict[str, Any]]:
    """Get status history for a feature."""
    service = StatusService(db, redis)
    try:
        return await service.get_feature_history(feature_id, days)
    except FeatureNotFoundError:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Feature {feature_id} not found"
        )


@router.post("/features/bulk-update")
async def bulk_update_features(
    updates: List[Dict[str, Any]],
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> Dict[str, Any]:
    """Bulk update multiple feature statuses."""
    service = StatusService(db, redis)
    results = await service.bulk_update_features(updates)
    return {
        "updated": results["success"],
        "failed": results["failed"],
        "total": len(updates)
    }
