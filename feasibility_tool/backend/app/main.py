from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import subprocess
from app.engines.base import initialize_engines, EngineRegistry
from app.auth import router as auth_router
from app.payments import router as payments_router
from app.database import init_db

# Import version from single source of truth
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from version import __version__, __build_date__, __description__

# Get git commit hash
def get_git_commit():
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], 
                                     stderr=subprocess.DEVNULL).decode('ascii').strip()
    except:
        return 'unknown'

__git_commit__ = get_git_commit()

app = FastAPI(
    title="Feasibility Platform API",
    description="Generic feasibility analysis platform with pluggable engines",
    version=__version__
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()

# Include routers
app.include_router(auth_router)
app.include_router(payments_router)

# CORS middleware - get frontend URL from environment
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Ensure FRONTEND_URL has protocol
if FRONTEND_URL and not FRONTEND_URL.startswith('http://') and not FRONTEND_URL.startswith('https://'):
    FRONTEND_URL = f"https://{FRONTEND_URL}"

allowed_origins = [FRONTEND_URL]

# Also allow common development origins
if "localhost" in FRONTEND_URL or "127.0.0.1" in FRONTEND_URL:
    allowed_origins.extend([
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ])

print(f"✅ CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
registry = initialize_engines()


# Response model
class APIResponse(BaseModel):
    """Standard API response"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return APIResponse(
        success=True,
        data={"status": "healthy"},
        metadata={"service": "feasibility-platform", "version": __version__}
    )


@app.get("/api/version")
async def get_version():
    """Get API version information"""
    return APIResponse(
        success=True,
        data={
            "version": __version__,
            "git_commit": __git_commit__,
            "build_date": __build_date__,
            "description": __description__
        }
    )


@app.get("/api/engines")
async def list_engines():
    """List all available engines"""
    try:
        engines = registry.list_engines()
        return APIResponse(
            success=True,
            data=[engine.dict() for engine in engines]
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error=str(e)
        )


@app.get("/api/engines/{engine_id}/input-schema")
async def get_input_schema(engine_id: str):
    """Get input parameter schema for engine"""
    try:
        engine = registry.get_engine(engine_id)
        if not engine:
            raise HTTPException(status_code=404, detail=f"Engine '{engine_id}' not found")
        
        schema = engine.get_input_schema()
        return APIResponse(
            success=True,
            data={k: v.dict() for k, v in schema.items()}
        )
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(
            success=False,
            error=str(e)
        )


@app.get("/api/engines/{engine_id}/output-schema")
async def get_output_schema(engine_id: str):
    """Get output metric schema for engine"""
    try:
        engine = registry.get_engine(engine_id)
        if not engine:
            raise HTTPException(status_code=404, detail=f"Engine '{engine_id}' not found")
        
        schema = engine.get_output_schema()
        return APIResponse(
            success=True,
            data={k: v.dict() for k, v in schema.items()}
        )
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(
            success=False,
            error=str(e)
        )


@app.post("/api/engines/{engine_id}/calculate")
async def calculate(engine_id: str, inputs: Dict[str, Any]):
    """Perform calculation with specified engine"""
    try:
        engine = registry.get_engine(engine_id)
        if not engine:
            raise HTTPException(status_code=404, detail=f"Engine '{engine_id}' not found")
        
        result = engine.calculate(inputs)
        return APIResponse(
            success=True,
            data=result.dict()
        )
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(
            success=False,
            error=str(e)
        )


@app.get("/api/engines/{engine_id}/target-profiles")
async def get_target_profiles(engine_id: str):
    """Get predefined target profiles"""
    try:
        engine = registry.get_engine(engine_id)
        if not engine:
            raise HTTPException(status_code=404, detail=f"Engine '{engine_id}' not found")
        
        profiles = {
            "Maximum Performance": engine.get_target_profile("Maximum Performance"),
            "Best ROI": engine.get_target_profile("Best ROI"),
            "Balanced": engine.get_target_profile("Balanced")
        }
        
        return APIResponse(
            success=True,
            data=profiles
        )
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(
            success=False,
            error=str(e)
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
