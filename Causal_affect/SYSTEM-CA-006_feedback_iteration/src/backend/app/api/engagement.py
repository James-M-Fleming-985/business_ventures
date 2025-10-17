"""Engagement API router - placeholder for future implementation."""

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/engagement", tags=["engagement"])


@router.get("/metrics")
async def get_engagement_metrics():
    """Get engagement metrics - not yet implemented."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Engagement metrics endpoint not yet implemented"
    )


@router.get("/trends")
async def get_engagement_trends():
    """Get engagement trends - not yet implemented."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Engagement trends endpoint not yet implemented"
    )
