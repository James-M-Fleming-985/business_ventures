from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import numpy as np

router = APIRouter()

# Mock data storage - in production this would be replaced with actual data source
SIGNAL_DATA = {
    "temperature": {
        "data": np.random.randn(100),
        "has_sufficient_data": True
    },
    "humidity": {
        "data": np.random.randn(100),
        "has_sufficient_data": True
    },
    "pressure": {
        "data": np.random.randn(20),
        "has_sufficient_data": False
    }
}


def calculate_lag_correlation(signal_data: np.ndarray, max_lag: int) -> tuple[List[int], List[float]]:
    """
    Calculate lag correlation for a signal.
    
    Args:
        signal_data: The signal data array
        max_lag: Maximum lag to calculate
        
    Returns:
        Tuple of (lag_days, correlations)
    """
    # Generate lag days from -max_lag to max_lag
    lag_days = list(range(-max_lag, max_lag + 1))
    
    # Calculate correlations for each lag
    correlations = []
    for lag in lag_days:
        if lag == 0:
            correlation = 1.0
        else:
            # Simple autocorrelation calculation
            if lag > 0:
                corr = np.corrcoef(signal_data[:-lag], signal_data[lag:])[0, 1]
            else:
                corr = np.corrcoef(signal_data[-lag:], signal_data[:lag])[0, 1]
            
            # Handle NaN values
            if np.isnan(corr):
                corr = 0.0
            correlations.append(float(corr))
    
    return lag_days, correlations


@router.get("/api/signal-radar/signals/{keyword}/lag-curve")
async def get_lag_curve(
    keyword: str,
    max_lag: Optional[int] = Query(30, description="Maximum lag in days", ge=1)
):
    """
    Get lag curve analysis for a signal identified by keyword.
    
    Args:
        keyword: The signal keyword to analyze
        max_lag: Maximum lag to calculate (default: 30)
        
    Returns:
        Dictionary with lag_days and correlations arrays
        
    Raises:
        HTTPException 404: If keyword is not found
        HTTPException 400: If insufficient data for analysis
    """
    # Check if keyword exists
    if keyword not in SIGNAL_DATA:
        raise HTTPException(status_code=404, detail=f"Signal with keyword '{keyword}' not found")
    
    signal_info = SIGNAL_DATA[keyword]
    
    # Check if there's sufficient data
    if not signal_info["has_sufficient_data"]:
        raise HTTPException(status_code=400, detail="Insufficient data for lag analysis")
    
    # Calculate lag correlation
    lag_days, correlations = calculate_lag_correlation(signal_info["data"], max_lag)
    
    return {
        "lag_days": lag_days,
        "correlations": correlations
    }