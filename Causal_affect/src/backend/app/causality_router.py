"""
Causality Analysis Router
Endpoints for Granger causality testing, lag analysis, and regression quantification.

Phase 2-4 of the exploitation pathway.
Integrates: FEATURE-CA-002-02 (Granger), CA-002-06 (Causality API),
            CA-002-08 (Lag Analysis), CA-002-09 (Regression)
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import sys
import numpy as np
from pathlib import Path
from pydantic import BaseModel, Field

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import Granger test implementation (Feature 02 - original)
ca002_path = Path(__file__).parent.parent.parent.parent / "SYSTEM-CA-002_correlation_analysis"
granger_path = ca002_path / "FEATURE-CA-002-02_causality_testing" / "LAYER-CA-002-02-01_granger_test" / "src"
sys.path.insert(0, str(granger_path))

try:
    from implementation import GrangerCausalityTest, GrangerTestResult
    GRANGER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Granger test not available: {e}")
    GRANGER_AVAILABLE = False
    GrangerCausalityTest = None
    GrangerTestResult = None

# Import Feature 06 - Causality API Service
feature_06_path = ca002_path / "FEATURE-CA-002-06_causality_api_service" / "src"

try:
    import importlib.util as _ilu
    _spec06 = _ilu.spec_from_file_location(
        "feature_integration_06", feature_06_path / "feature_integration.py"
    )
    _mod06 = _ilu.module_from_spec(_spec06)
    _spec06.loader.exec_module(_mod06)
    CausalityOrchestrator = _mod06.FeatureOrchestrator
    CAUSALITY_SERVICE_AVAILABLE = True
    _causality_service = CausalityOrchestrator()
except Exception as e:
    logging.warning(f"Causality API service (CA-002-06) not available: {e}")
    CAUSALITY_SERVICE_AVAILABLE = False
    _causality_service = None

# Import Feature 08 - Lag Analysis Service
feature_08_path = ca002_path / "FEATURE-CA-002-08_lag_analysis_service" / "src"

try:
    _spec08 = _ilu.spec_from_file_location(
        "feature_integration_08", feature_08_path / "feature_integration.py"
    )
    _mod08 = _ilu.module_from_spec(_spec08)
    _spec08.loader.exec_module(_mod08)
    LagOrchestrator = _mod08.FeatureOrchestrator
    LAG_SERVICE_AVAILABLE = True
    _lag_service = LagOrchestrator()
except Exception as e:
    logging.warning(f"Lag analysis service (CA-002-08) not available: {e}")
    LAG_SERVICE_AVAILABLE = False
    _lag_service = None

# Import Feature 09 - Regression Quantification Service
feature_09_path = ca002_path / "FEATURE-CA-002-09_regression_service" / "src"

try:
    _spec09 = _ilu.spec_from_file_location(
        "feature_integration_09", feature_09_path / "feature_integration.py"
    )
    _mod09 = _ilu.module_from_spec(_spec09)
    _spec09.loader.exec_module(_mod09)
    RegressionOrchestrator = _mod09.FeatureOrchestrator
    REGRESSION_SERVICE_AVAILABLE = True
    _regression_service = RegressionOrchestrator()
except Exception as e:
    logging.warning(f"Regression service (CA-002-09) not available: {e}")
    REGRESSION_SERVICE_AVAILABLE = False
    _regression_service = None

from .database import get_db

# Import schema with correct path
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from features.FEATURE_CA_001_03_timeseries_storage.db.schema import timeseries_data_table
except ImportError:
    # Try alternative path with hyphens
    try:
        import importlib.util
        schema_path = Path(__file__).parent.parent / "features" / "FEATURE-CA-001-03_timeseries_storage" / "db" / "schema.py"
        spec = importlib.util.spec_from_file_location("schema", schema_path)
        schema_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(schema_module)
        timeseries_data_table = schema_module.timeseries_data_table
    except Exception as e:
        logging.error(f"Could not import timeseries schema: {e}")
        timeseries_data_table = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/causality", tags=["causality"])


async def get_timeseries_by_name(
    db: AsyncSession,
    metric_name: str,
    lookback_days: int = 365
) -> Optional[np.ndarray]:
    """
    Fetch time series data for a metric.
    
    Args:
        db: Database session
        metric_name: Name of the metric/variable
        lookback_days: How many days of data to fetch
        
    Returns:
        Numpy array of values, or None if not found
    """
    if timeseries_data_table is None:
        return None
        
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=lookback_days)
    
    query = select(
        timeseries_data_table.c.value,
        timeseries_data_table.c.timestamp
    ).where(
        and_(
            timeseries_data_table.c.metric_name == metric_name,
            timeseries_data_table.c.timestamp >= start_time,
            timeseries_data_table.c.timestamp <= end_time
        )
    ).order_by(
        timeseries_data_table.c.timestamp.asc()
    )
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    if not rows:
        return None
        
    return np.array([row.value for row in rows])


def determine_causal_direction(
    p_value_xy: float,
    p_value_yx: float,
    significance: float = 0.05
) -> str:
    """
    Determine causal direction based on p-values from both tests.
    
    Returns: 'X->Y', 'Y->X', 'bidirectional', or 'none'
    """
    x_causes_y = p_value_xy < significance
    y_causes_x = p_value_yx < significance
    
    if x_causes_y and y_causes_x:
        return "bidirectional"
    elif x_causes_y:
        return "X->Y"
    elif y_causes_x:
        return "Y->X"
    else:
        return "none"


@router.get("/health")
async def causality_health() -> Dict[str, Any]:
    """Health check for causality service."""
    return {
        "status": "healthy" if GRANGER_AVAILABLE else "degraded",
        "granger_available": GRANGER_AVAILABLE,
        "causality_service_available": CAUSALITY_SERVICE_AVAILABLE,
        "lag_service_available": LAG_SERVICE_AVAILABLE,
        "regression_service_available": REGRESSION_SERVICE_AVAILABLE,
        "timestamp": datetime.utcnow().isoformat()
    }


# =============================================================================
# FEATURE CA-002-06: Causality API Service Endpoints
# =============================================================================

class GrangerTestRequest(BaseModel):
    """Request body for multi-variable Granger causality test."""
    data: Dict[str, List[float]] = Field(..., description="Variable name -> time series values")
    target_variable: str = Field(..., description="Variable to test as effect")
    predictor_variables: List[str] = Field(..., description="Variables to test as causes")
    max_lag: int = Field(default=10, ge=1, le=30)
    significance_level: float = Field(default=0.05, ge=0.01, le=0.1)


@router.post("/granger/test")
async def run_granger_service(request: GrangerTestRequest) -> Dict[str, Any]:
    """
    Run multi-variable Granger causality test via the Causality API Service (CA-002-06).

    Tests whether predictor variables Granger-cause the target variable.
    """
    if not CAUSALITY_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Causality API service (CA-002-06) not available"
        )

    result = _causality_service.perform_granger_causality_test(
        data=request.data,
        target_variable=request.target_variable,
        predictor_variables=request.predictor_variables,
    )
    return result.to_dict()


@router.get("/granger/status")
async def granger_service_status() -> Dict[str, Any]:
    """Get status of the Granger causality service (CA-002-06)."""
    if not CAUSALITY_SERVICE_AVAILABLE:
        return {"available": False, "error": "Service not loaded"}

    result = _causality_service.get_status()
    return result.to_dict()


# =============================================================================
# FEATURE CA-002-08: Lag Analysis Service Endpoints
# =============================================================================

class LagAnalysisRequest(BaseModel):
    """Request body for lag analysis between two time series."""
    series_1: List[float] = Field(..., description="First time series")
    series_2: List[float] = Field(..., description="Second time series")
    max_lag: Optional[int] = Field(default=None, description="Override max lag")


class BatchLagRequest(BaseModel):
    """Request body for batch lag analysis."""
    series_pairs: List[Dict[str, Any]] = Field(
        ..., description="List of {id, series_1, series_2} dicts"
    )


@router.post("/lag/analyze")
async def analyze_lag(request: LagAnalysisRequest) -> Dict[str, Any]:
    """
    Perform lag analysis between two time series (CA-002-08).

    Finds the optimal time lag and cross-correlation between two series.
    """
    if not LAG_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Lag analysis service (CA-002-08) not available"
        )

    kwargs = {}
    if request.max_lag is not None:
        kwargs["max_lag"] = request.max_lag

    result = _lag_service.analyze_lag(
        request.series_1,
        request.series_2,
        **kwargs,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return {
        "success": result.success,
        "data": result.data,
        "metadata": result.metadata,
        "timestamp": result.timestamp.isoformat() if result.timestamp else None,
    }


@router.post("/lag/batch")
async def batch_lag_analysis(request: BatchLagRequest) -> Dict[str, Any]:
    """
    Perform lag analysis on multiple time series pairs (CA-002-08).
    """
    if not LAG_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Lag analysis service (CA-002-08) not available"
        )

    result = _lag_service.batch_analyze(request.series_pairs)

    return {
        "success": result.success,
        "data": result.data,
        "timestamp": result.timestamp.isoformat() if result.timestamp else None,
    }


@router.get("/lag/health")
async def lag_service_health() -> Dict[str, Any]:
    """Health check for the lag analysis service (CA-002-08)."""
    if not LAG_SERVICE_AVAILABLE:
        return {"available": False, "error": "Service not loaded"}

    result = _lag_service.health_check()
    return {
        "available": True,
        "healthy": result.success,
        "data": result.data,
    }


# =============================================================================
# FEATURE CA-002-09: Regression Quantification Service Endpoints
# =============================================================================

class RegressionRequest(BaseModel):
    """Request body for regression quantification."""
    model_type: str = Field(default="linear_regression", description="Regression model type")
    data_source: str = Field(..., description="Data source identifier")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Model parameters (confidence_level, validation_split, etc.)",
    )


@router.post("/regression/quantify")
async def run_regression(request: RegressionRequest) -> Dict[str, Any]:
    """
    Execute regression quantification analysis (CA-002-09).

    Quantifies the strength and nature of causal relationships via regression.
    """
    if not REGRESSION_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Regression service (CA-002-09) not available"
        )

    result = _regression_service.execute_regression_quantification({
        "model_type": request.model_type,
        "data_source": request.data_source,
        "parameters": request.parameters,
    })

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return {
        "success": result.success,
        "data": result.data,
        "feature_id": result.feature_id,
        "operation": result.operation,
        "metadata": result.metadata,
        "timestamp": result.timestamp,
    }


@router.get("/regression/info")
async def regression_service_info() -> Dict[str, Any]:
    """Get regression service information (CA-002-09)."""
    if not REGRESSION_SERVICE_AVAILABLE:
        return {"available": False, "error": "Service not loaded"}

    result = _regression_service.get_service_info()
    return {
        "available": True,
        "data": result.data,
    }


@router.get("/regression/health")
async def regression_service_health() -> Dict[str, Any]:
    """Health check for the regression service (CA-002-09)."""
    if not REGRESSION_SERVICE_AVAILABLE:
        return {"available": False, "error": "Service not loaded"}

    result = _regression_service.health_check()
    return {
        "available": True,
        "healthy": result.success,
        "data": result.data,
    }


# =============================================================================
# FEATURE CA-002-02: Original Granger Pairwise Test (catch-all route — MUST be last)
# =============================================================================

@router.get("/{var1_name}/{var2_name}")
async def test_causality(
    var1_name: str,
    var2_name: str,
    max_lag: int = Query(default=10, ge=1, le=30, description="Maximum lag to test"),
    significance: float = Query(default=0.05, ge=0.01, le=0.1, description="Significance level"),
    lookback_days: int = Query(default=365, ge=30, le=730, description="Days of data to use"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Run Granger causality test between two variables.
    
    Tests both directions:
    - Does var1 Granger-cause var2? (X→Y)
    - Does var2 Granger-cause var1? (Y→X)
    
    Args:
        var1_name: Name of first variable (potential cause X)
        var2_name: Name of second variable (potential effect Y)
        max_lag: Maximum number of lags to test
        significance: P-value threshold for significance
        lookback_days: How many days of historical data to use
        
    Returns:
        Causality test results including direction
    """
    if not GRANGER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Granger causality testing not available - missing dependencies"
        )
    
    # Fetch time series data for both variables
    x_data = await get_timeseries_by_name(db, var1_name, lookback_days)
    if x_data is None or len(x_data) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Variable '{var1_name}' not found or has no data"
        )
    
    y_data = await get_timeseries_by_name(db, var2_name, lookback_days)
    if y_data is None or len(y_data) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Variable '{var2_name}' not found or has no data"
        )
    
    # Align time series lengths
    min_len = min(len(x_data), len(y_data))
    
    if min_len < max_lag + 10:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient data points ({min_len}) for lag={max_lag}. Need at least {max_lag + 10}."
        )
    
    x_aligned = x_data[-min_len:]
    y_aligned = y_data[-min_len:]
    
    # Initialize Granger test
    granger = GrangerCausalityTest(
        max_lag=max_lag,
        confidence_level=significance
    )
    
    try:
        # Test both directions
        result_xy = granger.test(x_aligned, y_aligned)
        result_yx = granger.test(y_aligned, x_aligned)
        
        # Determine overall causal direction
        causal_direction = determine_causal_direction(
            result_xy.p_value,
            result_yx.p_value,
            significance
        )
        
        # Map direction to readable names
        direction_names = {
            "X->Y": f"{var1_name} → {var2_name}",
            "Y->X": f"{var2_name} → {var1_name}",
            "bidirectional": f"{var1_name} ↔ {var2_name}",
            "none": "No significant causality"
        }
        
        return {
            "var1": var1_name,
            "var2": var2_name,
            "n_observations": int(min_len),
            "test_x_causes_y": {
                "hypothesis": f"{var1_name} Granger-causes {var2_name}",
                "f_statistic": float(result_xy.test_statistic),
                "p_value": float(result_xy.p_value),
                "optimal_lag": int(result_xy.lags),
                "is_significant": bool(result_xy.reject_null),
                "aic": result_xy.aic,
                "bic": result_xy.bic
            },
            "test_y_causes_x": {
                "hypothesis": f"{var2_name} Granger-causes {var1_name}",
                "f_statistic": float(result_yx.test_statistic),
                "p_value": float(result_yx.p_value),
                "optimal_lag": int(result_yx.lags),
                "is_significant": bool(result_yx.reject_null),
                "aic": result_yx.aic,
                "bic": result_yx.bic
            },
            "causal_direction": causal_direction,
            "causal_direction_readable": direction_names[causal_direction],
            "significance_level": significance,
            "tested_at": datetime.utcnow().isoformat(),
            "interpretation": _generate_interpretation(
                var1_name, var2_name,
                result_xy, result_yx,
                causal_direction
            )
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error running Granger test: {e}")
        raise HTTPException(status_code=500, detail=f"Error running causality test: {str(e)}")


def _generate_interpretation(
    var1: str,
    var2: str,
    result_xy: 'GrangerTestResult',
    result_yx: 'GrangerTestResult',
    direction: str
) -> str:
    """Generate human-readable interpretation of results."""
    
    if direction == "X->Y":
        return (
            f"{var1} significantly Granger-causes {var2} (p={result_xy.p_value:.4f}). "
            f"Past values of {var1} help predict {var2} with optimal lag of {result_xy.lags} periods. "
            f"The reverse is not significant (p={result_yx.p_value:.4f})."
        )
    elif direction == "Y->X":
        return (
            f"{var2} significantly Granger-causes {var1} (p={result_yx.p_value:.4f}). "
            f"Past values of {var2} help predict {var1} with optimal lag of {result_yx.lags} periods. "
            f"The reverse is not significant (p={result_xy.p_value:.4f})."
        )
    elif direction == "bidirectional":
        return (
            f"Bidirectional causality detected. "
            f"{var1} → {var2} (p={result_xy.p_value:.4f}, lag={result_xy.lags}) and "
            f"{var2} → {var1} (p={result_yx.p_value:.4f}, lag={result_yx.lags})."
        )
    else:
        return (
            f"No significant Granger causality detected in either direction "
            f"(p-values: {result_xy.p_value:.4f} and {result_yx.p_value:.4f})."
        )
