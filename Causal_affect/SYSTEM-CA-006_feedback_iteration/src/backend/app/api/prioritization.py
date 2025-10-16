"""Prioritization API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("/features")
async def get_prioritized_features() -> dict[str, Any]:
    """Get prioritized features list."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not implemented yet"
    )


@router.post("/calculate")
async def calculate_priorities() -> dict[str, Any]:
    """Calculate feature priorities using scoring algorithm."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not implemented yet"
    )


@router.get("/scores/{feature_id}")
async def get_feature_score(feature_id: int) -> dict[str, Any]:
    """Get priority score for specific feature."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not implemented yet"
    )


@router.put("/features/{feature_id}/priority")
async def update_feature_priority(feature_id: int) -> dict[str, Any]:
    """Update priority for specific feature."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not implemented yet"
    )
