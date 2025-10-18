from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.status import router as status_router
from app.api.control import router as control_router

api_router = APIRouter()

api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(status_router, prefix="/status", tags=["status"])
api_router.include_router(control_router, prefix="/control", tags=["control"])