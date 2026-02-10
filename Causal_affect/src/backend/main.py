"""
Causal Affect - FastAPI Application
Main application entry point with all feature routers
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
from pathlib import Path

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
from app.causality_router import router as causality_router
from app.database import init_db, close_db
from app.config import settings

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
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(signal_radar_router)
app.include_router(causality_router)
app.include_router(feedback_router)
app.include_router(iteration_router)
app.include_router(analysis_router)
app.include_router(notification_router)
app.include_router(export_router)

# Serve static files for React frontend
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")
    logger.info(f"📁 Serving static files from {static_dir}")


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("🚀 Starting Causal Affect application...")
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    logger.info("📊 Signal Radar endpoints registered")
    logger.info("✅ Application ready")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down...")
    await close_db()
    logger.info("Database connections closed")

@app.get("/")
async def root():
    """Root endpoint - serve React app."""
    static_dir = Path(__file__).parent / "static"
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    # Fallback to API info if no frontend
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

# Catch-all route for React Router (must be last)
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """Serve React app for all routes not handled by API."""
    # Don't intercept API routes
    if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc"):
        return {"error": "Not found"}
    
    static_dir = Path(__file__).parent / "static"
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"error": "Frontend not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload in development
        log_level="info"
    )
