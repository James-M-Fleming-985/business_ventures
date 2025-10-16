from fastapi import APIRouter
from app.config import settings

router = APIRouter(tags=["health"])

@router.get("/health")
def health_check():
    return {"status": "healthy", "service": "feedback-orchestrator"}

@router.get("/features")
def feature_flags():
    return {
        "FEATURE-CA-006-02": settings.feature_ca_006_02_enabled,
        "FEATURE-CA-006-03": settings.feature_ca_006_03_enabled,
        "FEATURE-CA-006-04": settings.feature_ca_006_04_enabled,
        "FEATURE-CA-006-05": settings.feature_ca_006_05_enabled,
        "FEATURE-CA-006-06": settings.feature_ca_006_06_enabled,
    }
