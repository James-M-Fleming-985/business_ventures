"""
Causal Affect - FastAPI Application
Main application entry point with all feature routers
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Import routers
from app.health import router as health_router
from app.features import (
    feedback_router,
    iteration_router,
    analysis_router,
    notification_router,
    export_router
)
from app.signal_radar_router import router as signal_radar_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Causal Affect - Behavioral Signal Analysis",
    description="Discover and exploit cause-effect relationships in behavioral data",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - configure based on your deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(signal_radar_router)
app.include_router(feedback_router)
app.include_router(iteration_router)
app.include_router(analysis_router)
app.include_router(notification_router)
app.include_router(export_router)

@app.on_startup
async def startup_event():
    """Initialize application on startup."""
    logger.info("🚀 Starting Causal Affect application...")
    logger.info("📊 Signal Radar endpoints registered")
    logger.info("✅ Application ready")

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "application": "Causal Affect",
        "version": "2.0.0",
        "description": "Behavioral Signal Analysis Platform",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "signal_radar": "/api/signal-radar",
            "feedback": "/api/feedback",
            "iterations": "/api/iterations",
            "analysis": "/api/analysis"
        },
        "status": "operational"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload in development
        log_level="info"
    )
