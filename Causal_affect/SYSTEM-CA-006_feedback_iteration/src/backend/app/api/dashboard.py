"""Dashboard API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("/overview")
async def get_dashboard_overview() -> dict[str, Any]:
    """Get dashboard overview with key metrics."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not implemented yet"
    )


@router.get("/kpis")
async def get_kpis() -> dict[str, Any]:
    """Get key performance indicators."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not implemented yet"
    )


@router.get("/activity")
async def get_recent_activity() -> dict[str, Any]:
    """Get recent activity feed."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not implemented yet"
    )


@router.get("/charts/engagement")
async def get_engagement_chart_data() -> dict[str, Any]:
    """Get engagement chart data for dashboard."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not implemented yet"
    )


@router.get("/charts/revenue")
async def get_revenue_chart_data() -> dict[str, Any]:
    """Get revenue chart data for dashboard."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not implemented yet"
    )
