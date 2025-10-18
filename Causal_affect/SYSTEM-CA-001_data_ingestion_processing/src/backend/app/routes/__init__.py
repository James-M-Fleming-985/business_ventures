from fastapi import APIRouter

from app.routes.health import router as health_router
from app.routes.status import router as status_router

api_router = APIRouter()

api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(status_router, prefix="/status", tags=["status"])
