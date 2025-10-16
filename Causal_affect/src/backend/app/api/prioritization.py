"""Prioritization API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("/features")
async def get_prioritized_features() -> dict[str, Any]:
    """Get prioritized list of features."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not implemented yet",
    )


@router.post("/features")
async def create_feature() -> dict[str, Any]:
    """Create a new feature for prioritization."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not implemented yet",
    )


@router.put("/features/{feature_id}")
async def update_feature(feature_id: int) -> dict[str, Any]:
    """Update feature details."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not implemented yet",
    )


@router.post("/features/{feature_id}/score")
async def score_feature(feature_id: int) -> dict[str, Any]:
    """Calculate priority score for a feature."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not implemented yet",
    )


@router.get("/frameworks")
async def get_prioritization_frameworks() -> dict[str, Any]:
    """Get available prioritization frameworks."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not implemented yet",
    )


@router.post("/compare")
async def compare_features() -> dict[str, Any]:
    """Compare multiple features."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not implemented yet",
    )
