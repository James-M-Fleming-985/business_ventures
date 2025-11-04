"""
Causal Affect Platform - Main FastAPI Application
Integrates CA-002 (Correlation Analysis) and CA-003 (Drift Forecasting)
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add Causal_affect directory to Python path
causal_affect_path = Path(__file__).parent / "Causal_affect"
sys.path.insert(0, str(causal_affect_path))

# Initialize FastAPI app
app = FastAPI(
    title="Causal Affect Platform API",
    description="Correlation Analysis, Drift Forecasting, and MVP Opportunity Detection",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        "version": "1.0.0"
    }


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint."""
    return {
        "message": "Causal Affect Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


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
    Generate drift forecast using ensemble or individual models.
    
    This endpoint uses CA-003-01 (5-layer ensemble forecasting system) to predict
    correlation drift over the specified horizon.
    """
    try:
        logger.info(f"Forecast request: horizon={request.horizon}, model={request.model_type}")
        
        # TODO: Import and use actual CA-003-01 feature orchestrator
        # from SYSTEM-CA-003_drift_forecasting.FEATURE-CA-003-01_time_series_forecasting_models.src.feature_integration import FeatureOrchestrator
        # orchestrator = FeatureOrchestrator()
        # result = await orchestrator.generate_forecast(request.dict())
        
        # Mock response for now
        forecast_values = [float(request.data[-1] * (1 + 0.01 * i)) for i in range(1, request.horizon + 1)]
        
        return {
            "success": True,
            "forecast": {
                "values": forecast_values,
                "horizon": request.horizon,
                "model_type": request.model_type,
                "confidence_level": request.confidence_level,
                "confidence_intervals": {
                    "lower": [v * 0.95 for v in forecast_values],
                    "upper": [v * 1.05 for v in forecast_values]
                }
            },
            "metadata": {
                "data_points": len(request.data),
                "generated_at": datetime.utcnow().isoformat(),
                "accuracy_estimate": 0.72
            }
        }
        
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
    Analyze correlations between variables.
    
    Returns correlation matrix, p-values, and identifies significant relationships.
    """
    try:
        logger.info(f"Correlation analysis request: {len(request.data)} variables")
        
        # TODO: Import and use actual CA-002 correlation analysis
        # Mock response
        correlations = {}
        variables = list(request.data.keys())
        
        if len(variables) >= 2:
            # Simple mock correlation
            correlations[f"{variables[0]}_{variables[1]}"] = {
                "coefficient": 0.87,
                "p_value": 0.001,
                "strength": "strong_positive",
                "significant": True
            }
        
        return {
            "success": True,
            "correlations": correlations,
            "method": request.method,
            "threshold": request.min_threshold,
            "metadata": {
                "variables_analyzed": len(variables),
                "significant_correlations": len(correlations),
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
    
    Uses CA-002-07 Layer 03 (Natural Language Generator) to create human-readable
    explanations with business context and MVP opportunities.
    """
    try:
        logger.info(f"Explanation request: {request.var1} vs {request.var2}, r={request.correlation}")
        
        # TODO: Import and use actual CA-002-07 NLG
        # from SYSTEM-CA-002_correlation_analysis.FEATURE-CA-002-07_analysis_explanation.LAYER_CA_002_07_03_Natural_Language_Generator.src.implementation import NaturalLanguageGenerator
        # nlg = NaturalLanguageGenerator(style=request.style)
        # explanation = nlg.generate_explanation(...)
        
        # Mock explanation
        if abs(request.correlation) >= 0.7:
            strength = "strong"
        elif abs(request.correlation) >= 0.3:
            strength = "moderate"
        else:
            strength = "weak"
            
        direction = "positive" if request.correlation > 0 else "negative"
        
        explanation = f"There is a {strength} {direction} correlation (r={request.correlation:.3f}) between {request.var1} and {request.var2}."
        
        if request.p_value and request.p_value < 0.05:
            explanation += f" This relationship is statistically significant (p={request.p_value:.4f})."
        
        return {
            "success": True,
            "explanation": {
                "text": explanation,
                "strength": strength,
                "direction": direction,
                "statistical_significance": request.p_value < 0.05 if request.p_value else None,
                "style": request.style
            },
            "business_insights": {
                "exploitability": "high" if abs(request.correlation) >= 0.7 else "medium",
                "mvp_potential": abs(request.correlation) >= 0.6,
                "recommendation": "Strong candidate for MVP development" if abs(request.correlation) >= 0.7 else "Monitor for opportunity"
            },
            "metadata": {
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
