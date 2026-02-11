from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import grangercausalitytests

router = APIRouter()


class GrangerResult(BaseModel):
    lag: int
    test_statistic: float
    p_value: float
    critical_values: Dict[str, float]


class GrangerModal(BaseModel):
    keyword: str
    target_variable: str
    max_lag: int
    results: List[GrangerResult]
    significant_lags: List[int]
    conclusion: str


# Mock data storage - in production, this would be a database
SIGNAL_DATA = {
    "bitcoin": pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='D'),
        'signal': np.random.randn(100).cumsum() + 100,
        'target': np.random.randn(100).cumsum() + 50
    }),
    "ethereum": pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='D'),
        'signal': np.random.randn(100).cumsum() + 80,
        'target': np.random.randn(100).cumsum() + 40
    }),
    "insufficient": pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=5, freq='D'),
        'signal': [1, 2, 3, 4, 5],
        'target': [2, 3, 4, 5, 6]
    })
}


@router.post("/api/signal-radar/signals/{keyword}/granger", response_model=GrangerModal)
async def granger_analysis(keyword: str, max_lag: Optional[int] = 4):
    """
    Perform Granger causality analysis for the specified keyword signal.
    
    Args:
        keyword: The signal keyword to analyze
        max_lag: Maximum lag to test (default: 4)
        
    Returns:
        GrangerModal: Analysis results including test statistics and conclusions
        
    Raises:
        HTTPException: 404 if keyword not found, 400 if insufficient data
    """
    # Check if keyword exists
    if keyword not in SIGNAL_DATA:
        raise HTTPException(status_code=404, detail=f"Keyword '{keyword}' not found")
    
    # Get data for the keyword
    data = SIGNAL_DATA[keyword]
    
    # Check if there's sufficient data
    min_required_observations = max_lag * 3 + 1
    if len(data) < min_required_observations:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient data for Granger causality test. Need at least {min_required_observations} observations, but only have {len(data)}"
        )
    
    # Prepare data for Granger test
    test_data = data[['target', 'signal']].values
    
    try:
        # Perform Granger causality test
        test_results = grangercausalitytests(test_data, maxlag=max_lag, verbose=False)
        
        results = []
        significant_lags = []
        
        for lag in range(1, max_lag + 1):
            if lag in test_results:
                # Extract F-test results
                f_test = test_results[lag][0]['ssr_ftest']
                test_stat = f_test[0]
                p_value = f_test[1]
                
                # Get critical values
                critical_values = {
                    "1%": 6.635,  # Approximate critical values for F-test
                    "5%": 3.841,
                    "10%": 2.706
                }
                
                result = GrangerResult(
                    lag=lag,
                    test_statistic=test_stat,
                    p_value=p_value,
                    critical_values=critical_values
                )
                results.append(result)
                
                # Check if significant at 5% level
                if p_value < 0.05:
                    significant_lags.append(lag)
        
        # Determine conclusion
        if significant_lags:
            conclusion = f"Granger causality detected at lags: {', '.join(map(str, significant_lags))}. The signal '{keyword}' helps predict the target variable."
        else:
            conclusion = f"No Granger causality detected. The signal '{keyword}' does not help predict the target variable."
        
        return GrangerModal(
            keyword=keyword,
            target_variable="target",
            max_lag=max_lag,
            results=results,
            significant_lags=significant_lags,
            conclusion=conclusion
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error performing Granger causality test: {str(e)}")
