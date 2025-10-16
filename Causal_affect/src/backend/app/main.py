from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.health import router as health_router
from app.features import (
    feedback_router,
    iteration_router,
    analysis_router,
    notification_router,
    export_router
)
from app.exceptions import (
    FeatureDisabledException,
    ResourceNotFoundException,
    ValidationException
)

app = FastAPI(title="Feedback Collection & Iteration Orchestrator", version="1.0.0")

origins = settings.cors_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(FeatureDisabledException)
async def feature_disabled_handler(request: Request, exc: FeatureDisabledException):
    return JSONResponse(
        status_code=403,
        content={"detail": f"Feature {exc.feature} is disabled"}
    )

@app.exception_handler(ResourceNotFoundException)
async def resource_not_found_handler(request: Request, exc: ResourceNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"detail": f"{exc.resource} with id {exc.resource_id} not found"}
    )

@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.message}
    )

app.include_router(health_router)
app.include_router(feedback_router)
app.include_router(iteration_router)
app.include_router(analysis_router)
app.include_router(notification_router)
app.include_router(export_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
