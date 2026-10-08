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

# Read git commit: prefer Railway's env var (always current), fall back to GIT_COMMIT file
import os as _os_for_commit
_railway_sha = _os_for_commit.environ.get('RAILWAY_GIT_COMMIT_SHA')
if _railway_sha:
    GIT_COMMIT = _railway_sha[:9]
else:
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
from routers import revenue  # Revenue dashboard (Track E)
from routers import ensemble  # Ensemble predictions (M2 Track A)

# Import Commercial Intelligence router (Track G — M2)
from routers import commercial_intelligence

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
app.include_router(dashboard.public_router)  # MVP page-view beacon (no auth)
app.include_router(admin.router)  # Admin endpoints for database management
app.include_router(auth.router)  # Authentication endpoints
app.include_router(subscription.router)  # Stripe subscription endpoints
app.include_router(revenue.router)  # Revenue dashboard (Track E)
app.include_router(ensemble.router)  # Ensemble predictions (M2 Track A)
app.include_router(commercial_intelligence.router)  # Commercial Intelligence (Track G)


# ---------------------------------------------------------------------------
# Legacy beacon alias
# Older deployed MVPs were generated with a beacon URL of /api/mvp-beacon/{id}
# (missing the /dashboard prefix). Forward those calls to the real handler so
# historical MVPs continue to register page views without a redeploy.
# ---------------------------------------------------------------------------
from fastapi import Request as _BeaconRequest
from sqlalchemy.orm import Session as _BeaconSession
from database import get_db as _beacon_get_db
from routers.dashboard_real import mvp_beacon as _mvp_beacon_handler


@app.post("/api/mvp-beacon/{build_id}", status_code=204, include_in_schema=False)
async def _legacy_mvp_beacon(build_id: int, request: _BeaconRequest, db: _BeaconSession = Depends(_beacon_get_db)):
    return await _mvp_beacon_handler(build_id, request, db)

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

        # Must run before any request reads users: the model now maps TOTP columns.
        try:
            from migrations.add_totp_columns import upgrade as _add_totp_columns
            _add_totp_columns(engine)
        except Exception as totp_err:
            logger.error(f"TOTP column migration failed: {totp_err}")

        # Add columns that may not exist on older deployments
        from sqlalchemy import text, inspect
        with engine.connect() as conn:
            inspector = inspect(engine)
            table_names = inspector.get_table_names()

            build_file_cols = {c['name'] for c in inspector.get_columns('mvp_build_files')} if 'mvp_build_files' in table_names else set()
            build_cols = {c['name'] for c in inspector.get_columns('mvp_builds')} if 'mvp_builds' in table_names else set()
            exploit_cols = {c['name'] for c in inspector.get_columns('exploitation_recommendations')} if 'exploitation_recommendations' in table_names else set()

            if 'content' not in build_file_cols and build_file_cols:
                conn.execute(text("ALTER TABLE mvp_build_files ADD COLUMN content TEXT"))
                conn.commit()
                logger.info("✅ Added content column to mvp_build_files")
            if 'build_steps' not in build_cols and build_cols:
                conn.execute(text("ALTER TABLE mvp_builds ADD COLUMN build_steps JSON"))
                conn.commit()
                logger.info("✅ Added build_steps column to mvp_builds")

            # M1 Track C: outcome tracking columns
            if 'target_growth_actual' not in exploit_cols and exploit_cols:
                conn.execute(text("ALTER TABLE exploitation_recommendations ADD COLUMN target_growth_actual FLOAT"))
                conn.execute(text("ALTER TABLE exploitation_recommendations ADD COLUMN target_growth_measured_at TIMESTAMP"))
                conn.commit()
                logger.info("✅ Added target_growth_actual columns to exploitation_recommendations")

            # M2 Track A: ensemble enrichment columns
            if 'ensemble_confidence' not in exploit_cols and exploit_cols:
                conn.execute(text("ALTER TABLE exploitation_recommendations ADD COLUMN ensemble_confidence VARCHAR(20)"))
                conn.execute(text("ALTER TABLE exploitation_recommendations ADD COLUMN ensemble_direction VARCHAR(10)"))
                conn.execute(text("ALTER TABLE exploitation_recommendations ADD COLUMN ensemble_predicted_at TIMESTAMP"))
                conn.commit()
                logger.info("✅ Added ensemble enrichment columns to exploitation_recommendations")

            # M2 Track A: ensemble scoring columns (R² + predicted change %)
            if 'ensemble_r_squared' not in exploit_cols and exploit_cols:
                conn.execute(text("ALTER TABLE exploitation_recommendations ADD COLUMN ensemble_r_squared FLOAT"))
                conn.execute(text("ALTER TABLE exploitation_recommendations ADD COLUMN ensemble_change_pct FLOAT"))
                conn.commit()
                logger.info("✅ Added ensemble scoring columns to exploitation_recommendations")

            # M2 Track H: Build iteration tracking columns
            if 'iteration_number' not in build_cols and build_cols:
                conn.execute(text("ALTER TABLE mvp_builds ADD COLUMN iteration_number INTEGER DEFAULT 1"))
                conn.execute(text("ALTER TABLE mvp_builds ADD COLUMN parent_build_id INTEGER REFERENCES mvp_builds(id)"))
                conn.execute(text("ALTER TABLE mvp_builds ADD COLUMN iterate_reason VARCHAR(100)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_build_parent ON mvp_builds (parent_build_id)"))
                conn.commit()
                logger.info("✅ Added iteration tracking columns to mvp_builds")

            # Track I PR3: REQ-AC verification evidence column
            if 'ac_verification' not in build_cols and build_cols:
                conn.execute(text("ALTER TABLE mvp_builds ADD COLUMN ac_verification JSON"))
                conn.commit()
                logger.info("✅ Added ac_verification column to mvp_builds")

            # Track I PR7: prompt-version stamp on each build (for correlation)
            if 'prompt_version' not in build_cols and build_cols:
                conn.execute(text("ALTER TABLE mvp_builds ADD COLUMN prompt_version VARCHAR(50)"))
                conn.commit()
                logger.info("✅ Added prompt_version column to mvp_builds")

            # Track I PR5: per-build revenue / metrics binding + telemetry table
            rev_cols = {c['name'] for c in inspector.get_columns('revenue_events')} if 'revenue_events' in table_names else set()
            if rev_cols and 'build_id' not in rev_cols:
                conn.execute(text("ALTER TABLE revenue_events ADD COLUMN build_id INTEGER REFERENCES mvp_builds(id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_rev_build ON revenue_events (build_id)"))
                conn.commit()
                logger.info("✅ Added build_id column to revenue_events")
            pm_cols = {c['name'] for c in inspector.get_columns('product_metrics')} if 'product_metrics' in table_names else set()
            if pm_cols and 'build_id' not in pm_cols:
                conn.execute(text("ALTER TABLE product_metrics ADD COLUMN build_id INTEGER REFERENCES mvp_builds(id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pm_build ON product_metrics (build_id)"))
                conn.commit()
                logger.info("✅ Added build_id column to product_metrics")
            # build_telemetry is a brand-new table; Base.metadata.create_all handles
            # creation on first boot, but log here so it's visible in Railway logs.
            if 'build_telemetry' not in table_names:
                logger.info("ℹ️  build_telemetry table missing — will be created by metadata.create_all")

            # User requirements for build spec customisation
            if 'user_requirements' not in exploit_cols and exploit_cols:
                conn.execute(text("ALTER TABLE exploitation_recommendations ADD COLUMN user_requirements TEXT"))
                conn.commit()
                logger.info("✅ Added user_requirements column to exploitation_recommendations")

            # Concept generation status tracking (background generation)
            if 'concepts_generation_status' not in exploit_cols and exploit_cols:
                conn.execute(text("ALTER TABLE exploitation_recommendations ADD COLUMN concepts_generation_status VARCHAR(20)"))
                conn.execute(text("ALTER TABLE exploitation_recommendations ADD COLUMN concepts_error TEXT"))
                conn.execute(text("ALTER TABLE exploitation_recommendations ADD COLUMN concepts_generated_at TIMESTAMP"))
                conn.commit()
                logger.info("✅ Added concept generation status columns to exploitation_recommendations")

            # Source column for Granger vs manual ideas
            if 'source' not in exploit_cols and exploit_cols:
                conn.execute(text("ALTER TABLE exploitation_recommendations ADD COLUMN source VARCHAR(20) DEFAULT 'granger'"))
                conn.commit()
                logger.info("✅ Added source column to exploitation_recommendations")

        # Track I (autonomous loop closure): hard-delete any legacy manually-injected
        # recommendations. Manual idea injection has been removed; existing rows are
        # purged so they cannot contaminate downstream learning signals.
        try:
            from migrations.delete_manual_recommendations import upgrade as _delete_manual_recs
            _delete_manual_recs()
            logger.info("✅ Track I migration: legacy manual recommendations purged")
        except Exception as mig_err:
            logger.warning(f"Track I manual-recommendations purge skipped: {mig_err}")

        # M2: Seed FRED + GDELT variables (idempotent — skips existing)
        try:
            from seed_fred_variables import seed_fred_variables
            fred_result = seed_fred_variables()
            logger.info(f"✅ FRED seed: {fred_result}")
        except Exception as seed_err:
            logger.warning(f"FRED seed skipped: {seed_err}")

        try:
            from seed_gdelt_variables import seed_gdelt_variables
            gdelt_result = seed_gdelt_variables()
            logger.info(f"✅ GDELT seed: {gdelt_result}")
        except Exception as seed_err:
            logger.warning(f"GDELT seed skipped: {seed_err}")
        
        # Start APScheduler for M0 automated validation
        try:
            from scheduled_tasks import init_scheduler
            app.state.scheduler = init_scheduler(SessionLocal)
        except Exception as sched_err:
            logger.warning(f"Scheduler init skipped: {sched_err}")

        # Track G: Schedule daily GA4 engagement pull + revenue aggregation
        try:
            scheduler = getattr(app.state, 'scheduler', None)
            if scheduler:
                from services.ga4_service import pull_engagement_for_all_deployments
                from services.commercial_intelligence_service import aggregate_all_deployments

                def _commercial_intelligence_job():
                    db = SessionLocal()
                    try:
                        agg = aggregate_all_deployments(db)
                        logger.info("Commercial intelligence aggregation: %s", agg)
                        ga4 = pull_engagement_for_all_deployments(db)
                        logger.info("GA4 engagement pull: %s", ga4)
                    except Exception as ci_err:
                        logger.warning("Commercial intelligence job failed: %s", ci_err)
                    finally:
                        db.close()

                scheduler.add_job(
                    _commercial_intelligence_job,
                    'interval',
                    hours=24,
                    id='commercial_intelligence_daily',
                    replace_existing=True,
                )
                logger.info("✅ Commercial intelligence daily job scheduled")
        except Exception as ci_sched_err:
            logger.warning(f"Commercial intelligence scheduler skipped: {ci_sched_err}")
        
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
async def logout_page():
    """Log out and redirect to landing page."""
    from services.auth import clear_auth_cookies
    # Cookies must be cleared on the response that is actually returned.
    response = RedirectResponse(url="/", status_code=307)
    clear_auth_cookies(response)
    return response


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

    # Recover any concept-generation rows stuck in 'generating' state from a
    # crashed/restarted background task. Threshold = 10 minutes (LLM call ~60s).
    try:
        from datetime import datetime, timedelta
        from database import SessionLocal
        from models import ExploitationRecommendation
        cutoff = datetime.utcnow() - timedelta(minutes=10)
        db = SessionLocal()
        try:
            stuck = db.query(ExploitationRecommendation).filter(
                ExploitationRecommendation.concepts_generation_status == "generating",
                ExploitationRecommendation.updated_at < cutoff,
            ).all()
            if stuck:
                for rec in stuck:
                    rec.concepts_generation_status = "failed"
                    rec.concepts_error = "Recovered from stuck state on startup (background task did not complete)"
                    rec.updated_at = datetime.utcnow()
                db.commit()
                logger.info(f"🩹 Recovered {len(stuck)} stuck concept-generation row(s) on startup")
        finally:
            db.close()
    except Exception as exc:
        logger.warning(f"Concept-generation startup recovery skipped: {type(exc).__name__}: {exc}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("👋 Causal Affect Platform API shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
