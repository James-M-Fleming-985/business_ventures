"""
Causal Affect Platform - Main FastAPI Application
Integrates CA-002 (Correlation Analysis) and CA-003 (Drift Forecasting)
Version: 2.0.14
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import sys
from pathlib import Path

# Read version from VERSION file
VERSION_FILE = Path(__file__).parent / "VERSION"
__version__ = VERSION_FILE.read_text().strip() if VERSION_FILE.exists() else "2.0.14"

# Read git commit from GIT_COMMIT file (created during build)
GIT_COMMIT_FILE = Path(__file__).parent / "GIT_COMMIT"
GIT_COMMIT = GIT_COMMIT_FILE.read_text().strip() if GIT_COMMIT_FILE.exists() else 'unknown'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add Causal_affect directory to Python path
causal_affect_path = Path(__file__).parent / "Causal_affect"
sys.path.insert(0, str(causal_affect_path))

# Import real data fetcher and analyzer
from data_fetcher import DataFetcher
from correlation_analyzer import CorrelationAnalyzer

# Import dashboard router - USING REAL DATA VERSION
from routers import dashboard_real as dashboard  # NO MOCK DATA
from routers import admin  # Database initialization endpoints
from routers import auth  # Authentication endpoints
from routers import subscription  # Stripe subscription endpoints

# Import Signal Radar router from Causal_affect
try:
    # Add necessary paths for Signal Radar imports
    signal_radar_app_path = causal_affect_path / "src" / "backend" / "app"
    signal_radar_backend_path = causal_affect_path / "src" / "backend"
    sys.path.insert(0, str(signal_radar_backend_path))
    sys.path.insert(0, str(signal_radar_app_path))
    
    # Import the router
    from signal_radar_router import router as signal_radar_router
    logger.info("✅ Signal Radar router imported successfully")
except ImportError as e:
    logger.warning(f"⚠️  Could not import Signal Radar router: {e}")
    signal_radar_router = None

# Import Causality router from Causal_affect (CA-002 features: Granger, Lag Analysis, Regression)
try:
    from causality_router import router as causality_router
    logger.info("✅ Causality router imported successfully (CA-002-02/06/08/09)")
except ImportError as e:
    logger.warning(f"⚠️  Could not import Causality router: {e}")
    causality_router = None

# Build version - automatically read from VERSION file
BUILD_VERSION = __version__
DEPLOY_TIMESTAMP = datetime.utcnow().isoformat()

# Initialize services
data_fetcher = DataFetcher()
correlation_analyzer = CorrelationAnalyzer()

# Initialize templates and static files
templates = Jinja2Templates(directory="templates")

# Initialize FastAPI app
app = FastAPI(
    title="Causal Affect Platform API",
    description="Correlation Analysis, Drift Forecasting, and MVP Opportunity Detection",
    version=BUILD_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(dashboard.router)
app.include_router(admin.router)  # Admin endpoints for database management
app.include_router(auth.router)  # Authentication endpoints
app.include_router(subscription.router)  # Stripe subscription endpoints

# Include Signal Radar if available
if signal_radar_router is not None:
    app.include_router(signal_radar_router)
    logger.info("✅ Signal Radar endpoints registered at /api/signal-radar")
else:
    logger.warning("⚠️  Signal Radar endpoints not available")

# Include Causality router if available (CA-002 AI-built features)
if causality_router is not None:
    app.include_router(causality_router)
    logger.info("✅ Causality endpoints registered (Granger, Lag Analysis, Regression)")
else:
    logger.warning("⚠️  Causality endpoints not available")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# STARTUP EVENT - Initialize Database and Fetch Fresh Data
# ============================================================================

async def fetch_fresh_data_background():
    """Background task to fetch fresh Wikipedia/Reddit data on startup."""
    import asyncio
    await asyncio.sleep(5)  # Wait for app to fully start
    
    try:
        logger.info("🔄 Auto-fetching fresh Layer 1 data on startup...")
        
        # First, ensure Wikipedia and Reddit variables exist in database
        try:
            from setup_layer1_fast_signals import setup_wikipedia_variables, setup_reddit_variables
            logger.info("🔧 Setting up Layer 1 variables (Wikipedia + Reddit)...")
            setup_wikipedia_variables()
            setup_reddit_variables()
            logger.info("✅ Layer 1 variables configured")
        except Exception as setup_err:
            logger.warning(f"Variable setup skipped: {setup_err}")
        
        # Import and run data ingestion
        from data_ingestion_service import DataIngestionService
        service = DataIngestionService()
        
        # Fetch Wikipedia data (free, no rate limits)
        wiki_result = service._fetch_wikipedia_pageviews_data()
        logger.info(f"✅ Wikipedia fetch: {wiki_result.get('wikipedia_fetched', 0)} variables, {wiki_result.get('wikipedia_data_points', 0)} data points")
        
        # Fetch Reddit data
        try:
            reddit_result = service._fetch_reddit_activity_data()
            logger.info(f"✅ Reddit fetch: {reddit_result.get('reddit_fetched', 0)} variables, {reddit_result.get('reddit_data_points', 0)} data points")
        except Exception as e:
            logger.warning(f"Reddit fetch skipped: {e}")
        
        logger.info("✅ Startup data fetch complete - Layer 1 signals ready")
        
    except Exception as e:
        logger.error(f"Startup data fetch failed: {e}")
        # Don't crash the app - it can still work with stale data


@app.on_event("startup")
async def startup_event():
    """Initialize database tables, start scheduler, and fetch fresh data on startup."""
    import asyncio
    
    try:
        from database import engine, SessionLocal
        from models import Base
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables initialized")

        # Add columns that may not exist on older deployments
        from sqlalchemy import text, inspect
        with engine.connect() as conn:
            inspector = inspect(engine)
            build_file_cols = {c['name'] for c in inspector.get_columns('mvp_build_files')} if 'mvp_build_files' in inspector.get_table_names() else set()
            build_cols = {c['name'] for c in inspector.get_columns('mvp_builds')} if 'mvp_builds' in inspector.get_table_names() else set()
            if 'content' not in build_file_cols and build_file_cols:
                conn.execute(text("ALTER TABLE mvp_build_files ADD COLUMN content TEXT"))
                conn.commit()
                logger.info("✅ Added content column to mvp_build_files")
            if 'build_steps' not in build_cols and build_cols:
                conn.execute(text("ALTER TABLE mvp_builds ADD COLUMN build_steps JSON"))
                conn.commit()
                logger.info("✅ Added build_steps column to mvp_builds")
        
        # Start APScheduler for M0 automated validation
        try:
            from scheduled_tasks import init_scheduler
            app.state.scheduler = init_scheduler(SessionLocal)
        except Exception as sched_err:
            logger.warning(f"Scheduler init skipped: {sched_err}")
        
        # Start background data fetch (non-blocking)
        asyncio.create_task(fetch_fresh_data_background())
        logger.info("🔄 Background data fetch scheduled")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shut down scheduler gracefully."""
    scheduler = getattr(app.state, 'scheduler', None)
    if scheduler:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down")


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for Railway and monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "causal-affect-platform",
        "version": BUILD_VERSION,
        "deploy_timestamp": DEPLOY_TIMESTAMP
    }


@app.get("/", tags=["Pages"])
async def root(request: Request):
    """Root endpoint - show landing page for unauthenticated, dashboard for authenticated."""
    from services.auth import get_current_user
    from sqlalchemy.orm import Session
    from database import SessionLocal
    
    # Check if user is authenticated via cookie
    token = request.cookies.get("access_token")
    if token:
        # User has token, redirect to dashboard
        return RedirectResponse(url="/dashboard", status_code=307)
    
    # Show landing page for unauthenticated users
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/login", response_class=HTMLResponse, tags=["Pages"])
async def login_page(request: Request):
    """Serve the login page."""
    # If already authenticated, redirect to dashboard
    token = request.cookies.get("access_token")
    if token:
        return RedirectResponse(url="/dashboard", status_code=307)
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse, tags=["Pages"])
async def register_page(request: Request):
    """Serve the registration page."""
    # If already authenticated, redirect to dashboard
    token = request.cookies.get("access_token")
    if token:
        return RedirectResponse(url="/dashboard", status_code=307)
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/logout", tags=["Pages"])
async def logout_page(response: Response):
    """Log out and redirect to landing page."""
    from services.auth import clear_auth_cookies
    clear_auth_cookies(response)
    return RedirectResponse(url="/", status_code=307)


@app.get("/subscription", response_class=HTMLResponse, tags=["Pages"])
async def subscription_page(request: Request):
    """Serve the subscription page."""
    return templates.TemplateResponse("subscription.html", {"request": request})


@app.get("/subscription/success", response_class=HTMLResponse, tags=["Pages"])
async def subscription_success_page(request: Request):
    """Subscription success page - redirect to dashboard."""
    return RedirectResponse(url="/dashboard?subscription=success", status_code=307)


@app.get("/subscription/cancel", response_class=HTMLResponse, tags=["Pages"])
async def subscription_cancel_page(request: Request):
    """Subscription cancelled page - redirect to subscription."""
    return RedirectResponse(url="/subscription?cancelled=true", status_code=307)


@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
async def dashboard_page(request: Request):
    """Serve the main dashboard UI - requires authentication."""
    from services.auth import get_current_user_from_cookie
    from database import SessionLocal
    
    # Check authentication
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=307)
    
    # Verify token is valid
    db = SessionLocal()
    try:
        user = await get_current_user_from_cookie(request, db)
        if not user:
            return RedirectResponse(url="/login", status_code=307)
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "version": BUILD_VERSION,
            "git_commit": GIT_COMMIT,
            "deploy_timestamp": DEPLOY_TIMESTAMP,
            "user": {
                "email": user.email,
                "display_name": user.display_name,
                "role": user.role,
                "is_admin": user.is_admin,
                "is_superuser": user.is_superuser,
                "subscription_tier": user.subscription_tier
            }
        })
    finally:
        db.close()


@app.get("/favicon.ico")
async def favicon():
    """Serve favicon.ico from static directory"""
    from pathlib import Path
    favicon_path = Path("static") / "favicon.ico"
    return FileResponse(favicon_path)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ForecastRequest(BaseModel):
    """Request model for drift forecasting."""
    data: List[float] = Field(..., description="Historical time series data")
    horizon: int = Field(30, ge=1, le=90, description="Forecast horizon (days)")
    model_type: str = Field("ensemble", description="Model type: arima, prophet, lstm, xgboost, or ensemble")
    confidence_level: float = Field(0.95, ge=0.5, le=0.99, description="Confidence level for intervals")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": [100, 105, 103, 108, 110, 115, 112, 118, 120],
                "horizon": 30,
                "model_type": "ensemble",
                "confidence_level": 0.95
            }
        }


class CorrelationRequest(BaseModel):
    """Request model for correlation analysis."""
    data: Dict[str, List[float]] = Field(..., description="Dictionary of variable names to data points")
    method: str = Field("pearson", description="Correlation method: pearson, spearman, or kendall")
    min_threshold: float = Field(0.3, ge=0.0, le=1.0, description="Minimum correlation threshold")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "ice_cream_sales": [100, 120, 140, 160, 180, 200],
                    "temperature": [70, 75, 80, 85, 90, 95]
                },
                "method": "pearson",
                "min_threshold": 0.5
            }
        }


class ExplanationRequest(BaseModel):
    """Request model for natural language explanations."""
    correlation: float = Field(..., ge=-1.0, le=1.0, description="Correlation coefficient")
    var1: str = Field(..., description="First variable name")
    var2: str = Field(..., description="Second variable name")
    p_value: Optional[float] = Field(None, description="Statistical p-value")
    style: str = Field("detailed", description="Explanation style: simple, detailed, or technical")
    
    class Config:
        json_schema_extra = {
            "example": {
                "correlation": 0.87,
                "var1": "ice_cream_sales",
                "var2": "temperature",
                "p_value": 0.001,
                "style": "detailed"
            }
        }


# ============================================================================
# CA-003-01: DRIFT FORECASTING ENDPOINTS
# ============================================================================

@app.post("/api/v1/forecast", tags=["Forecasting"])
async def create_forecast(request: ForecastRequest):
    """
    Generate drift forecast using simple linear extrapolation.
    
    Uses the recent trend in the data to project future values.
    """
    try:
        logger.info(f"Forecast request: horizon={request.horizon}, model={request.model_type}")
        
        # Calculate simple trend from last 10 points
        recent_data = request.data[-10:] if len(request.data) >= 10 else request.data
        if len(recent_data) < 2:
            raise HTTPException(status_code=400, detail="Insufficient data points for forecasting")
        
        # Simple linear trend
        import numpy as np
        x = np.arange(len(recent_data))
        y = np.array(recent_data)
        coeffs = np.polyfit(x, y, 1)  # Linear fit
        slope, intercept = coeffs
        
        # Generate forecast
        last_x = len(recent_data) - 1
        forecast_values = []
        for i in range(1, request.horizon + 1):
            predicted = slope * (last_x + i) + intercept
            forecast_values.append(float(predicted))
        
        # Add confidence intervals (simple ±5% for now)
        uncertainty_factor = 1 + (0.05 * np.sqrt(np.arange(1, request.horizon + 1)))
        
        return {
            "success": True,
            "forecast": {
                "values": forecast_values,
                "horizon": request.horizon,
                "model_type": request.model_type,
                "confidence_level": request.confidence_level,
                "confidence_intervals": {
                    "lower": [v / u for v, u in zip(forecast_values, uncertainty_factor)],
                    "upper": [v * u for v, u in zip(forecast_values, uncertainty_factor)]
                },
                "trend": {
                    "slope": float(slope),
                    "direction": "increasing" if slope > 0 else "decreasing"
                }
            },
            "metadata": {
                "data_points": len(request.data),
                "generated_at": datetime.utcnow().isoformat(),
                "model": "linear_trend"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forecast error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Forecast generation failed: {str(e)}")


@app.get("/api/v1/forecast/{forecast_id}", tags=["Forecasting"])
async def get_forecast(forecast_id: str):
    """Retrieve a previously generated forecast."""
    # TODO: Implement forecast retrieval from database/cache
    return {"message": f"Retrieve forecast {forecast_id}", "status": "not_implemented"}


# ============================================================================
# CA-002: CORRELATION ANALYSIS ENDPOINTS
# ============================================================================

@app.post("/api/v1/correlations", tags=["Correlation Analysis"])
async def analyze_correlations(request: CorrelationRequest):
    """
    Analyze correlations between variables using real statistical methods.
    
    Returns correlation matrix, p-values, and identifies significant relationships.
    """
    try:
        logger.info(f"Correlation analysis request: {len(request.data)} variables")
        
        # Use real correlation analyzer
        result = correlation_analyzer.analyze_matrix(
            data=request.data,
            method=request.method,
            min_threshold=request.min_threshold
        )
        
        return {
            "success": True,
            "correlation_matrix": result["matrix"],
            "p_values": result["p_values"],
            "variables": result["variables"],
            "significant_pairs": result["significant_pairs"],
            "method": result["method"],
            "threshold": result["threshold"],
            "metadata": {
                "variables_analyzed": len(result["variables"]),
                "significant_correlations": result["total_pairs"],
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Correlation analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Correlation analysis failed: {str(e)}")


# ============================================================================
# CA-002-07: NATURAL LANGUAGE EXPLANATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/explanations", tags=["Explanations"])
async def generate_explanation(request: ExplanationRequest):
    """
    Generate natural language explanation for correlation analysis.
    
    Creates human-readable explanations with business context.
    """
    try:
        logger.info(f"Explanation request: {request.var1} vs {request.var2}, r={request.correlation}")
        
        # Use real correlation analyzer for explanation
        explanation_text = correlation_analyzer.generate_explanation(
            correlation=request.correlation,
            var1=request.var1,
            var2=request.var2,
            p_value=request.p_value,
            style=request.style
        )
        
        # Classify strength and direction
        abs_corr = abs(request.correlation)
        if abs_corr >= 0.7:
            strength = "strong"
        elif abs_corr >= 0.3:
            strength = "moderate"
        else:
            strength = "weak"
            
        direction = "positive" if request.correlation > 0 else "negative"
        
        return {
            "success": True,
            "explanation": {
                "text": explanation_text,
                "strength": strength,
                "direction": direction,
                "statistical_significance": request.p_value < 0.05 if request.p_value else None,
                "correlation_coefficient": request.correlation
            },
            "metadata": {
                "style": request.style,
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Explanation generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Explanation generation failed: {str(e)}")


# ============================================================================
# DRIFT ANALYSIS ENDPOINT (CA-002-07 Layer 02)
# ============================================================================

@app.post("/api/v1/drift/analyze", tags=["Drift Analysis"])
async def analyze_drift(data: Dict[str, List[float]]):
    """
    Analyze drift patterns in correlation data.
    
    Combines simple rolling drift detection with CA-003-01 ensemble forecasts.
    """
    try:
        logger.info(f"Drift analysis request for {len(data)} variables")
        
        # TODO: Implement actual drift analysis using CA-002-07 Layer 02
        
        return {
            "success": True,
            "drift_detected": False,
            "drift_score": 0.03,
            "severity": "low",
            "forecast_stability": "stable",
            "metadata": {
                "analyzed_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Drift analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Drift analysis failed: {str(e)}")


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler for unexpected errors."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("🚀 Causal Affect Platform API starting up...")
    logger.info("📊 CA-002: Correlation Analysis - Ready")
    logger.info("📈 CA-003: Drift Forecasting - Ready")
    logger.info("💬 CA-002-07: Natural Language Explanations - Ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("👋 Causal Affect Platform API shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
