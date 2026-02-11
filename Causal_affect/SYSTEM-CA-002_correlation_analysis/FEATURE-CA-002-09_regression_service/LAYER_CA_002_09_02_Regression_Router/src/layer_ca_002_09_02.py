from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.stattools import acf
import pandas as pd

router = APIRouter()

# Mock data storage - in production this would come from a database
SIGNALS_DATA = {
    "bitcoin": {
        "series_1": np.random.randn(100).cumsum() + 50,
        "series_2": np.random.randn(100).cumsum() + 30
    },
    "ethereum": {
        "series_1": np.random.randn(100).cumsum() + 40,
        "series_2": np.random.randn(100).cumsum() + 25
    },
    "insufficient": {
        "series_1": np.array([1, 2]),
        "series_2": np.array([3, 4])
    }
}


def detect_optimal_lag(series_1: np.ndarray, series_2: np.ndarray, max_lag: int = 10) -> int:
    """
    Detect optimal lag between two time series using cross-correlation.
    
    Args:
        series_1: First time series
        series_2: Second time series
        max_lag: Maximum lag to test
        
    Returns:
        Optimal lag value
    """
    if len(series_1) < 20 or len(series_2) < 20:
        return 0
    
    correlations = []
    for lag in range(0, min(max_lag + 1, len(series_1) // 2)):
        if lag == 0:
            corr = np.corrcoef(series_1, series_2)[0, 1]
        else:
            corr = np.corrcoef(series_1[:-lag], series_2[lag:])[0, 1]
        correlations.append(abs(corr))
    
    return int(np.argmax(correlations))


def perform_regression(series_1: np.ndarray, series_2: np.ndarray, lag: int = 0) -> Dict[str, Any]:
    """
    Perform linear regression between two time series with optional lag.
    
    Args:
        series_1: Independent variable (X)
        series_2: Dependent variable (Y)
        lag: Lag to apply to series_2
        
    Returns:
        Dictionary containing regression results
    """
    # Apply lag
    if lag > 0:
        X = series_1[:-lag].reshape(-1, 1)
        y = series_2[lag:]
    else:
        X = series_1.reshape(-1, 1)
        y = series_2
    
    # Perform regression
    model = LinearRegression()
    model.fit(X, y)
    
    # Calculate statistics
    y_pred = model.predict(X)
    beta_1 = float(model.coef_[0])
    beta_0 = float(model.intercept_)
    
    # R-squared
    ss_tot = np.sum((y - np.mean(y))**2)
    ss_res = np.sum((y - y_pred)**2)
    r_squared = float(1 - (ss_res / ss_tot))
    
    # P-value for slope
    n = len(X)
    t_stat = beta_1 / (np.sqrt(ss_res / (n - 2)) / np.sqrt(np.sum((X - np.mean(X))**2)))
    p_value = float(2 * (1 - stats.t.cdf(abs(t_stat), n - 2)))
    
    # Formula
    formula = f"Y = {beta_0:.3f} + {beta_1:.3f} * X"
    if lag > 0:
        formula += f" (lag={lag})"
    
    # Interpretation
    if p_value < 0.05:
        direction = "positive" if beta_1 > 0 else "negative"
        interpretation = f"Statistically significant {direction} relationship (p={p_value:.3f})"
    else:
        interpretation = f"No statistically significant relationship (p={p_value:.3f})"
    
    return {
        "beta_1": beta_1,
        "r_squared": r_squared,
        "p_value": p_value,
        "formula": formula,
        "interpretation": interpretation,
        "lag_applied": lag
    }


@router.get("/api/signal-radar/signals/{keyword}/regression")
async def get_signal_regression(
    keyword: str,
    lag: Optional[int] = Query(None, description="Optional lag parameter to override auto-detected optimal lag")
) -> Dict[str, Any]:
    """
    Perform regression analysis on signal data.
    
    Args:
        keyword: Signal keyword to analyze
        lag: Optional lag parameter
        
    Returns:
        Regression analysis results
        
    Raises:
        HTTPException: 404 if keyword not found, 400 if insufficient data
    """
    # Check if keyword exists
    if keyword not in SIGNALS_DATA:
        raise HTTPException(status_code=404, detail=f"Signal with keyword '{keyword}' not found")
    
    # Get data
    data = SIGNALS_DATA[keyword]
    series_1 = data["series_1"]
    series_2 = data["series_2"]
    
    # Check for sufficient data
    min_data_points = 10
    if len(series_1) < min_data_points or len(series_2) < min_data_points:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient data for regression analysis. Minimum {min_data_points} data points required."
        )
    
    # Determine lag
    if lag is None:
        lag = detect_optimal_lag(series_1, series_2)
    
    # Perform regression
    try:
        results = perform_regression(series_1, series_2, lag)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error performing regression: {str(e)}")