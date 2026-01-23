"""
API Router for Signal Radar and Composite Signal Aggregation
Handles endpoints for retrieving and analyzing fast-moving behavioral signals
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 
                "SYSTEM-CA-002_correlation_analysis" / 
                "FEATURE-CA-002-01_statistical_correlation" / "src"))

try:
    from composite_signal_aggregator import (
        aggregate_signals,
        get_signal_details,
        get_available_matching_modes,
        SourceSignal,
        CompositeSignal,
        MatchingMode
    )
except ImportError as e:
    print(f"Warning: Could not import composite_signal_aggregator: {e}")
    aggregate_signals = None

router = APIRouter(prefix="/api/signal-radar", tags=["signal-radar"])


@router.get("/matching-modes")
async def get_matching_modes() -> Dict[str, Any]:
    """
    Get available keyword matching modes for signal aggregation.
    
    Returns dropdown options for UI with implementation status.
    """
    if get_available_matching_modes is None:
        raise HTTPException(status_code=500, detail="Aggregator not available")
    
    modes = get_available_matching_modes()
    return {
        "modes": modes,
        "default": "simple",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/signals/composite")
async def get_composite_signals(
    matching_mode: str = Query(default="simple", description="Keyword matching mode: simple, fuzzy, or sophisticated"),
    min_momentum: float = Query(default=30.0, description="Minimum momentum threshold (%)"),
    min_sources: int = Query(default=1, description="Minimum number of sources required")
) -> Dict[str, Any]:
    """
    Get aggregated composite signals from multiple sources.
    
    This endpoint:
    1. Retrieves all fast-moving signals from various sources (Wikipedia, Reddit, Twitter, etc.)
    2. Groups them by keyword using the specified matching mode
    3. Creates weighted composite signals
    4. Returns them sorted by momentum
    
    Args:
        matching_mode: How to match keywords across sources (simple/fuzzy/sophisticated)
        min_momentum: Filter out signals below this momentum threshold
        min_sources: Only show signals validated by at least this many sources
        
    Returns:
        Dictionary with composite signals and metadata
    """
    if aggregate_signals is None:
        raise HTTPException(status_code=500, detail="Aggregator not available")
    
    try:
        # TODO: Replace this with actual data retrieval from your system
        # This should query CA-001 TimescaleDB for trending signals
        raw_signals = _get_raw_signals_from_database()
        
        # Filter by minimum momentum
        raw_signals = [s for s in raw_signals if abs(s.momentum) >= min_momentum]
        
        # Convert matching mode string to enum
        try:
            mode_enum = MatchingMode(matching_mode.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid matching mode: {matching_mode}. Use: simple, fuzzy, or sophisticated"
            )
        
        # Aggregate signals
        composites = aggregate_signals(raw_signals, matching_mode=mode_enum)
        
        # Filter by minimum source count
        composites = [c for c in composites if c.source_count >= min_sources]
        
        # Convert to JSON-serializable format
        result = {
            "signals": [
                {
                    "keyword": comp.keyword.title(),
                    "momentum": round(comp.composite_momentum, 1),
                    "source_count": comp.source_count,
                    "confidence_level": comp.confidence_level,
                    "confidence_stars": comp.confidence_stars,
                    "agreement_score": round(comp.agreement_score, 1),
                    "sources": [
                        {
                            "name": src.source.title(),
                            "momentum": round(src.momentum, 1)
                        }
                        for src in comp.sources
                    ]
                }
                for comp in composites
            ],
            "metadata": {
                "total_signals": len(composites),
                "matching_mode": matching_mode,
                "filters": {
                    "min_momentum": min_momentum,
                    "min_sources": min_sources
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error aggregating signals: {str(e)}")


@router.get("/signals/{keyword}/details")
async def get_signal_detail(
    keyword: str,
    matching_mode: str = Query(default="simple")
) -> Dict[str, Any]:
    """
    Get detailed breakdown of a specific composite signal for modal display.
    
    This endpoint is called when user clicks a signal card to see:
    - Individual source breakdown
    - Source weights
    - Agreement score details
    - Metadata for Granger analysis
    
    Args:
        keyword: The keyword to get details for
        matching_mode: Matching mode used for aggregation
        
    Returns:
        Detailed signal information for modal display
    """
    try:
        # Get all composites
        raw_signals = _get_raw_signals_from_database()
        mode_enum = MatchingMode(matching_mode.lower())
        composites = aggregate_signals(raw_signals, matching_mode=mode_enum)
        
        # Find the requested signal
        normalized_keyword = keyword.lower().strip()
        matching_signal = None
        
        for comp in composites:
            if comp.keyword.lower() == normalized_keyword:
                matching_signal = comp
                break
        
        if not matching_signal:
            raise HTTPException(status_code=404, detail=f"Signal '{keyword}' not found")
        
        # Get detailed breakdown
        details = get_signal_details(matching_signal)
        details["timestamp"] = datetime.utcnow().isoformat()
        
        return details
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving signal details: {str(e)}")


@router.post("/signals/{keyword}/granger")
async def run_granger_analysis(
    keyword: str,
    target_variable: str,
    matching_mode: str = Query(default="simple")
) -> Dict[str, Any]:
    """
    Run Granger causality analysis for a composite signal.
    
    This endpoint is called when user clicks "Run Granger Analysis" in the modal.
    
    Args:
        keyword: The signal keyword to analyze
        target_variable: What to predict (e.g., "HR_software_stocks")
        matching_mode: Matching mode used for aggregation
        
    Returns:
        Granger test results with predictions
    """
    try:
        # Get the composite signal
        raw_signals = _get_raw_signals_from_database()
        mode_enum = MatchingMode(matching_mode.lower())
        composites = aggregate_signals(raw_signals, matching_mode=mode_enum)
        
        # Find matching signal
        normalized_keyword = keyword.lower().strip()
        matching_signal = None
        
        for comp in composites:
            if comp.keyword.lower() == normalized_keyword:
                matching_signal = comp
                break
        
        if not matching_signal:
            raise HTTPException(status_code=404, detail=f"Signal '{keyword}' not found")
        
        if matching_signal.composite_timeseries is None:
            raise HTTPException(
                status_code=400, 
                detail="No time series data available for this signal"
            )
        
        # TODO: Implement actual Granger causality test using composite_timeseries
        # This should call the granger test from FEATURE-CA-002-02
        # For now, return placeholder
        
        result = {
            "keyword": matching_signal.keyword.title(),
            "target": target_variable,
            "granger_results": {
                "f_statistic": 28.4,  # TODO: Replace with actual test
                "p_value": 0.00001,
                "r_value": -0.72,
                "optimal_lag": 15,
                "n_observations": 487,
                "is_causal": True
            },
            "prediction": {
                "direction": "down",
                "magnitude": -12.0,
                "lag_days": 15,
                "confidence": "Very High"
            },
            "metadata": {
                "source_count": matching_signal.source_count,
                "agreement_score": matching_signal.agreement_score,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running Granger analysis: {str(e)}")


def _get_raw_signals_from_database() -> List[SourceSignal]:
    """
    Retrieve raw signals from database.
    
    TODO: Replace this placeholder with actual database queries to CA-001 TimescaleDB
    This should query for trending signals from all sources.
    
    Returns:
        List of SourceSignal objects
    """
    # Placeholder data - replace with actual DB queries
    import numpy as np
    
    return [
        SourceSignal(
            keyword="Layoff",
            source="wikipedia",
            momentum=64.6,
            data_points=500,
            timestamp=datetime.utcnow().isoformat(),
            raw_data=np.random.randn(500)
        ),
        SourceSignal(
            keyword="layoff",
            source="twitter",
            momentum=72.1,
            data_points=1200,
            timestamp=datetime.utcnow().isoformat(),
            raw_data=np.random.randn(500)
        ),
        SourceSignal(
            keyword="layoffs",
            source="reddit",
            momentum=60.3,
            data_points=800,
            timestamp=datetime.utcnow().isoformat(),
            raw_data=np.random.randn(500)
        ),
        SourceSignal(
            keyword="unemployment",
            source="google_trends",
            momentum=45.8,
            data_points=600,
            timestamp=datetime.utcnow().isoformat(),
            raw_data=np.random.randn(500)
        ),
    ]
