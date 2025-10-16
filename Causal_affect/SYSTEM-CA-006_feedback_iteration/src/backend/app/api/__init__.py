"""API routers package."""

from fastapi import APIRouter

from app.api import dashboard, engagement, iteration, prioritization, revenue

api_router = APIRouter()

api_router.include_router(
    engagement.router,
    prefix="/engagement",
    tags=["engagement"]
)

api_router.include_router(
    revenue.router,
    prefix="/revenue",
    tags=["revenue"]
)

api_router.include_router(
    prioritization.router,
    prefix="/prioritization",
    tags=["prioritization"]
)

api_router.include_router(
    iteration.router,
    prefix="/iteration",
    tags=["iteration"]
)

api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["dashboard"]
)

__all__ = ["api_router"]
