"""
Dashboard Router for Correlation Discovery Engine
ALL ENDPOINTS USE REAL API DATA - NO MOCK/SYNTHETIC DATA
"""

from fastapi import APIRouter, Request, Query, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models import (
    VariableMetadata, TimeSeriesData, CorrelationResult,
    RollingCorrelation, APIStatus, AnalysisJob
)
from correlation_analysis_service import CorrelationAnalysisService
from services.granger_causality_service import GrangerCausalityService
from typing import Optional, List
from datetime import datetime, timedelta
import logging
import math

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="templates")


@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get real statistics from database - NO MOCK DATA"""
    try:
        # Count total data points
        data_points = db.query(TimeSeriesData).count()
        
        # Count active variables
        active_vars = db.query(VariableMetadata).filter(
            VariableMetadata.is_active.is_(True)
        ).count()
        
        # Count significant correlations
        strong_correlations = db.query(CorrelationResult).filter(
            CorrelationResult.is_significant.is_(True),
            CorrelationResult.abs_correlation >= 0.5
        ).count()
        
        # Count active API sources
        active_apis = db.query(APIStatus).filter(
            APIStatus.status == 'active'
        ).count()
        
        # Get last update time
        last_job = db.query(AnalysisJob).filter(
            AnalysisJob.status == 'completed'
        ).order_by(AnalysisJob.end_time.desc()).first()
        
        last_updated = last_job.end_time.strftime("%H:%M:%S") if last_job else "Never"
        
        return {
            "dataPoints": data_points,
            "strongCorrelations": strong_correlations,
            "apiSources": active_apis,
            "totalVariables": active_vars,
            "lastUpdated": last_updated
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            "dataPoints": 0,
            "strongCorrelations": 0,
            "apiSources": 0,
            "totalVariables": 0,
            "lastUpdated": "Error",
            "error": str(e)
        }


@router.get("/heatmap")
async def get_heatmap_data(
    top_n: int = Query(12, ge=5, le=30, description="Number of top variable pairs to show"),
    cross_domain: bool = Query(True, description="Only show correlations across different data sources"),
    min_strength: float = Query(0.3, ge=0.0, le=1.0, description="Minimum absolute correlation strength"),
    db: Session = Depends(get_db)
):
    """
    Get heatmap showing TOP N strongest correlation pairs
    Designed to highlight disparate cross-domain relationships
    Returns focused matrix of strongest pairs (not all-vs-all)
    """
    try:
        # Get correlations from database - USE cross_domain parameter!
        service = CorrelationAnalysisService()
        all_correlations = service.get_top_correlations(
            limit=500,  # Get many candidates for filtering
            min_significance=0.05,
            cross_domain=cross_domain,  # Actually use the cross_domain filter!
            min_sample_size=30  # CRITICAL FIX: Only show correlations with n >= 30
        )
        
        if not all_correlations:
            return {
                "labels": [],
                "matrix": [],
                "message": "No correlations calculated yet. Run data ingestion first."
            }
        
        # Apply strength filter only (cross-domain already filtered by service)
        filtered = []
        for corr in all_correlations:
            # Strength filter
            if abs(corr['correlation_value']) < min_strength:
                continue
            
            filtered.append(corr)
        
        # Deduplicate pairs (keep only one of A-B or B-A)
        seen_pairs = set()
        unique_correlations = []
        for corr in filtered:
            v1, v2 = corr['variable1_name'], corr['variable2_name']
            pair = tuple(sorted([v1, v2]))
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                unique_correlations.append(corr)
        
        # Take top N unique pairs
        top_pairs = unique_correlations[:top_n]
        
        if not top_pairs:
            return {
                "labels": [],
                "matrix": [],
                "message": f"No correlations found above strength threshold {min_strength}. Try lowering min_strength."
            }
        
        # Build focused matrix from ONLY the top pairs
        # Each pair gets one row and one column
        labels = []
        var_to_idx = {}
        
        # Build variable list preserving pair order
        for corr in top_pairs:
            for var_name in [corr['variable1_name'], corr['variable2_name']]:
                if var_name not in var_to_idx:
                    var_to_idx[var_name] = len(labels)
                    labels.append(var_name)
        
        # Initialize matrix: None for missing, 1.0 on diagonal
        n = len(labels)
        matrix = [[None for _ in range(n)] for _ in range(n)]
        metadata = [[None for _ in range(n)] for _ in range(n)]  # Store sample sizes
        for i in range(n):
            matrix[i][i] = 1.0
            metadata[i][i] = {'sample_size': 0, 'p_value': 0, 'dates': ''}
        
        # Fill in correlations (only pairs we have)
        for corr in top_pairs:
            i = var_to_idx[corr['variable1_name']]
            j = var_to_idx[corr['variable2_name']]
            r = corr['correlation_value']
            
            # Store correlation and metadata
            matrix[i][j] = r
            matrix[j][i] = r
            
            meta = {
                'sample_size': corr.get('sample_size', 0),
                'p_value': corr.get('p_value', 0),
                'data_quality': corr.get('data_quality', 'UNKNOWN'),  # NEW: Quality indicator
                'start_date': corr.get('start_date', ''),
                'end_date': corr.get('end_date', '')
            }
            metadata[i][j] = meta
            metadata[j][i] = meta
        
        return {
            "labels": labels,
            "matrix": matrix,
            "metadata": metadata,  # Add metadata for tooltips
            "correlation_count": len(top_pairs),
            "top_n": top_n,
            "cross_domain_filter": cross_domain,
            "min_strength": min_strength
        }
    
    except Exception as e:
        logger.error(f"Error getting heatmap: {e}")
        return {
            "labels": [],
            "matrix": [],
            "error": str(e)
        }


@router.get("/timeseries")
async def get_timeseries_data(
    var1_id: Optional[int] = None,
    var2_id: Optional[int] = None,
    days: int = Query(90, ge=7, le=365),
    db: Session = Depends(get_db)
):
    """
    Get time series of CORRELATION RELATIONSHIP - REAL DATA ONLY
    Shows how correlation between two variables evolves over time
    """
    try:
        if not var1_id or not var2_id:
            # Get top correlation pair if not specified
            top_corr = db.query(CorrelationResult).filter(
                CorrelationResult.is_significant.is_(True)
            ).order_by(CorrelationResult.abs_correlation.desc()).first()
            
            if not top_corr:
                return {"series": [], "message": "No correlations available"}
            
            var1_id = top_corr.variable1_id
            var2_id = top_corr.variable2_id
        
        # Get rolling correlations for this pair
        rolling_corrs = db.query(RollingCorrelation).filter(
            RollingCorrelation.variable1_id == var1_id,
            RollingCorrelation.variable2_id == var2_id
        ).order_by(RollingCorrelation.window_end).all()
        
        if not rolling_corrs:
            # Calculate on-the-fly if not in database
            service = CorrelationAnalysisService()
            rolling_results = service.calculate_rolling_correlations(
                var1_id, var2_id, window_days=30
            )
            
            dates = [r['window_end'].strftime("%Y-%m-%d") for r in rolling_results]
            values = [r['correlation_value'] for r in rolling_results]
        else:
            dates = [rc.window_end.strftime("%Y-%m-%d") for rc in rolling_corrs]
            values = [rc.correlation_value for rc in rolling_corrs]
        
        # Get variable names
        var1 = db.query(VariableMetadata).get(var1_id)
        var2 = db.query(VariableMetadata).get(var2_id)
        
        series_name = f"{var1.display_name} ↔ {var2.display_name} Correlation"
        
        return {
            "series": [{
                "name": series_name,
                "dates": dates,
                "values": values,
                "type": "correlation_evolution"
            }]
        }
    except Exception as e:
        logger.error(f"Error getting timeseries: {e}")
        return {"series": [], "error": str(e)}


@router.get("/network")
async def get_network_data(
    threshold: float = Query(0.5, ge=0, le=1),
    db: Session = Depends(get_db)
):
    """Get correlation network from REAL DATA - connections above threshold"""
    try:
        # Get all significant correlations above threshold with minimum sample size
        correlations = db.query(CorrelationResult).filter(
            CorrelationResult.is_significant.is_(True),
            CorrelationResult.abs_correlation >= threshold,
            CorrelationResult.sample_size >= 30  # CRITICAL: Filter out correlations with insufficient data
        ).all()
        
        if not correlations:
            return {
                "nodes": {
                    "x": [],
                    "y": [],
                    "sizes": [],
                    "colors": [],
                    "labels": []
                },
                "edges": {
                    "x": [],
                    "y": []
                },
                "message": f"No correlations above threshold {threshold}"
            }
        
        # Build variable list
        var_set = set()
        for corr in correlations:
            var_set.add(corr.variable1_id)
            var_set.add(corr.variable2_id)
        
        var_ids = sorted(list(var_set))
        var_id_to_idx = {vid: idx for idx, vid in enumerate(var_ids)}
        
        # Get variable names
        variables = db.query(VariableMetadata).filter(
            VariableMetadata.id.in_(var_ids)
        ).all()
        var_id_to_name = {v.id: v.display_name for v in variables}
        labels = [var_id_to_name.get(vid, f"Var {vid}") for vid in var_ids]
        
        # Calculate circular layout
        n = len(labels)
        angles = [i * 2 * math.pi / n for i in range(n)]
        node_x = [math.cos(a) for a in angles]
        node_y = [math.sin(a) for a in angles]
        
        # Build edges
        edge_x = []
        edge_y = []
        connections = [0] * n
        
        for corr in correlations:
            idx1 = var_id_to_idx.get(corr.variable1_id)
            idx2 = var_id_to_idx.get(corr.variable2_id)
            
            if idx1 is not None and idx2 is not None:
                edge_x.extend([node_x[idx1], node_x[idx2], None])
                edge_y.extend([node_y[idx1], node_y[idx2], None])
                connections[idx1] += 1
                connections[idx2] += 1
        
        # Node sizes and colors based on connections
        node_sizes = [15 + c * 5 for c in connections]
        node_colors = []
        for c in connections:
            if c >= 4:
                node_colors.append('#3b82f6')  # Blue - hub
            elif c >= 2:
                node_colors.append('#8b5cf6')  # Purple - medium
            else:
                node_colors.append('#64748b')  # Gray - isolated
        
        return {
            "nodes": {
                "x": node_x,
                "y": node_y,
                "sizes": node_sizes,
                "colors": node_colors,
                "labels": labels
            },
            "edges": {
                "x": edge_x,
                "y": edge_y
            },
            "correlation_count": len(correlations)
        }
    except Exception as e:
        logger.error(f"Error getting network: {e}")
        return {
            "nodes": {
                "x": [],
                "y": [],
                "sizes": [],
                "colors": [],
                "labels": []
            },
            "edges": {
                "x": [],
                "y": []
            },
            "error": str(e)
        }


@router.get("/leaderboard")
async def get_leaderboard_data(
    limit: int = Query(10, ge=5, le=50),
    db: Session = Depends(get_db)
):
    """Get top correlations ranked by strength - REAL DATA ONLY"""
    try:
        service = CorrelationAnalysisService()
        top_correlations = service.get_top_correlations(
            limit=limit,
            min_significance=0.05,
            min_sample_size=30  # CRITICAL: Filter out correlations with insufficient data
        )
        
        leaderboard = []
        for i, corr in enumerate(top_correlations, 1):
            leaderboard.append({
                "rank": i,
                "var1": corr['variable1_name'],
                "var2": corr['variable2_name'],
                "r": corr['correlation_value'],
                "p": corr['p_value'],
                "abs_correlation": abs(corr['correlation_value']),
                "sample_size": corr['sample_size'],
                "data_quality": corr.get('data_quality', 'UNKNOWN'),  # NEW: Quality indicator
                "significance": "***" if corr['p_value'] < 0.001 else "**" if corr['p_value'] < 0.01 else "*"
            })
        
        return {"leaderboard": leaderboard}
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return {"leaderboard": [], "error": str(e)}


@router.get("/relationship/{var1_name}/{var2_name}")
async def get_relationship_details(
    var1_name: str,
    var2_name: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed relationship analysis for two variables
    Returns data formatted for modal display
    """
    try:
        # Find variables by display_name (exact match or fuzzy)
        var1 = db.query(VariableMetadata).filter(
            VariableMetadata.display_name == var1_name
        ).first()
        
        if not var1:
            var1 = db.query(VariableMetadata).filter(
                VariableMetadata.display_name.ilike(f"%{var1_name}%")
            ).first()
        
        var2 = db.query(VariableMetadata).filter(
            VariableMetadata.display_name == var2_name
        ).first()
        
        if not var2:
            var2 = db.query(VariableMetadata).filter(
                VariableMetadata.display_name.ilike(f"%{var2_name}%")
            ).first()
        
        if not var1 or not var2:
            return {
                "error": "Variables not found",
                "var1": var1_name,
                "var2": var2_name
            }
        
        # Get correlation result (check both directions)
        # ORDER BY calculated_at DESC to get the most recent calculation
        corr = db.query(CorrelationResult).filter(
            ((CorrelationResult.variable1_id == var1.id) &
             (CorrelationResult.variable2_id == var2.id)) |
            ((CorrelationResult.variable1_id == var2.id) &
             (CorrelationResult.variable2_id == var1.id))
        ).order_by(CorrelationResult.calculated_at.desc()).first()
        
        if not corr:
            return {
                "error": "No correlation calculated for this pair",
                "var1": var1_name,
                "var2": var2_name
            }
        
        # Debug logging to track date range issues
        logger.info(f"Correlation {var1_name} vs {var2_name}: sample_size={corr.sample_size}, start={corr.start_date}, end={corr.end_date}")
        
        # Get time series data for scatter plot and overlay
        # CRITICAL: Only use data within the correlation's calculated date range
        # This ensures scatter plot matches the actual correlation sample size
        query_filters_var1 = [TimeSeriesData.variable_id == var1.id]
        query_filters_var2 = [TimeSeriesData.variable_id == var2.id]
        
        if corr.start_date:
            query_filters_var1.append(TimeSeriesData.timestamp >= corr.start_date)
            query_filters_var2.append(TimeSeriesData.timestamp >= corr.start_date)
        
        if corr.end_date:
            query_filters_var1.append(TimeSeriesData.timestamp <= corr.end_date)
            query_filters_var2.append(TimeSeriesData.timestamp <= corr.end_date)
        
        var1_data = db.query(TimeSeriesData).filter(
            *query_filters_var1
        ).order_by(TimeSeriesData.timestamp).all()
        
        var2_data = db.query(TimeSeriesData).filter(
            *query_filters_var2
        ).order_by(TimeSeriesData.timestamp).all()
        
        # Use pandas for proper time series alignment with interpolation
        # This matches the correlation calculation logic (handles different frequencies)
        import pandas as pd
        
        var1_series = pd.Series(
            [dp.value for dp in var1_data],
            index=[dp.timestamp for dp in var1_data]
        )
        var2_series = pd.Series(
            [dp.value for dp in var2_data],
            index=[dp.timestamp for dp in var2_data]
        )
        
        # Combine both series with outer join to get all timestamps
        aligned_data = pd.DataFrame({
            'var1': var1_series,
            'var2': var2_series
        })
        
        # Sort by timestamp
        aligned_data = aligned_data.sort_index()
        
        # Interpolate missing values to align different frequencies
        # (e.g., daily stock prices with quarterly GDP data)
        aligned_data = aligned_data.interpolate(method='time', limit_direction='both')
        
        # Drop any remaining NaN
        aligned_data = aligned_data.dropna()
        
        logger.info(f"Scatter plot alignment: {len(var1_data)} var1 points + {len(var2_data)} var2 points = {len(aligned_data)} aligned points")
        
        # Build scatter plot data from aligned DataFrame
        scatter_data = [
            {
                "x": float(row['var1']),
                "y": float(row['var2']),
                "date": idx.strftime("%Y-%m-%d")
            }
            for idx, row in aligned_data.iterrows()
        ]
        
        # Build time series for overlay
        var1_raw = aligned_data['var1'].tolist()
        var2_raw = aligned_data['var2'].tolist()
        dates = [idx.strftime("%Y-%m-%d") for idx in aligned_data.index]
        
        # Normalize to 0-1 range for visualization (so both series visible)
        var1_min, var1_max = min(var1_raw), max(var1_raw)
        var2_min, var2_max = min(var2_raw), max(var2_raw)
        
        var1_normalized = [
            (v - var1_min) / (var1_max - var1_min)
            if var1_max > var1_min else 0.5
            for v in var1_raw
        ]
        var2_normalized = [
            (v - var2_min) / (var2_max - var2_min)
            if var2_max > var2_min else 0.5
            for v in var2_raw
        ]
        
        timeseries = {
            "dates": dates,
            "var1_values": var1_normalized,  # Normalized for chart
            "var2_values": var2_normalized,   # Normalized for chart
            "var1_raw": var1_raw,             # Original values
            "var2_raw": var2_raw,             # Original values
            "var1_unit": var1.unit,           # Unit for formatting
            "var2_unit": var2.unit            # Unit for formatting
        }
        
        # Determine correlation strength and direction
        abs_r = abs(corr.correlation_value)
        if abs_r >= 0.7:
            strength = "strong"
        elif abs_r >= 0.4:
            strength = "moderate"
        else:
            strength = "weak"
        
        direction = (
            "positive" if corr.correlation_value > 0 else "negative"
        )
        
        # Generate explanation
        r_val = corr.correlation_value
        explanation = (
            f"This {strength} {direction} correlation (r = {r_val:.3f}) "
            f"between {var1.display_name} and {var2.display_name} "
            f"was calculated using {corr.sample_size} data points "
        )
        
        if corr.start_date and corr.end_date:
            start = corr.start_date.strftime('%Y-%m-%d')
            end = corr.end_date.strftime('%Y-%m-%d')
            explanation += f"from {start} to {end}. "
        else:
            explanation += "across the available time period. "
        
        if corr.p_value < 0.001:
            explanation += (
                "The relationship is highly statistically significant "
                "(p < 0.001), meaning there's less than 0.1% probability "
                "this correlation occurred by chance."
            )
        elif corr.p_value < 0.01:
            explanation += (
                "The relationship is very statistically significant "
                "(p < 0.01)."
            )
        elif corr.p_value < 0.05:
            explanation += (
                "The relationship is statistically significant (p < 0.05)."
            )
        else:
            explanation += (
                "Note: This correlation is not statistically significant "
                f"at the 0.05 level (p = {corr.p_value:.4f})."
            )
        
        # Determine stability (simplified for now)
        stability = "stable"
        
        return {
            "var1": var1.display_name,
            "var2": var2.display_name,
            "correlation": corr.correlation_value,
            "p_value": corr.p_value,
            "strength": strength,
            "direction": direction,
            "stability": stability,
            "sample_size": corr.sample_size,
            "actual_scatter_points": len(scatter_data),  # Verify scatter matches sample size
            "date_range": {  # Show actual date range used
                "start": corr.start_date.strftime('%Y-%m-%d') if corr.start_date else None,
                "end": corr.end_date.strftime('%Y-%m-%d') if corr.end_date else None
            },
            "method": corr.method,
            "explanation": explanation,
            "scatter_data": scatter_data,
            "timeseries": timeseries,
            "is_significant": corr.is_significant
        }
    except Exception as e:
        logger.error(f"Error getting relationship: {e}")
        return {
            "error": str(e),
            "var1": var1_name,
            "var2": var2_name
        }


@router.get("/top-variables-timeseries")
async def get_top_variables_timeseries(
    limit: int = Query(
        5, ge=3, le=10,
        description="Number of top variables to show"
    ),
    db: Session = Depends(get_db)
):
    """
    Get time series for top variables from strongest correlations
    Shows raw values (not normalized) for quick trend overview
    """
    try:
        # Get top correlations to find most interesting variables
        service = CorrelationAnalysisService()
        top_correlations = service.get_top_correlations(
            limit=20,  # Get enough correlations
            min_significance=0.05,
            cross_domain=True
        )
        
        if not top_correlations:
            return {
                "series": [],
                "message": "No correlations calculated yet"
            }
        
        # Extract unique variables from top correlations
        var_names = set()
        for corr in top_correlations:
            var_names.add(corr['variable1_name'])
            var_names.add(corr['variable2_name'])
            if len(var_names) >= limit:
                break
        
        # Take first N unique variable names
        selected_vars = list(var_names)[:limit]
        
        # Get variable metadata
        variables = db.query(VariableMetadata).filter(
            VariableMetadata.display_name.in_(selected_vars)
        ).all()
        
        # Build time series for each variable
        series = []
        for var in variables:
            data_points = db.query(TimeSeriesData).filter(
                TimeSeriesData.variable_id == var.id
            ).order_by(TimeSeriesData.timestamp).all()
            
            if data_points:
                dates = [
                    dp.timestamp.strftime("%Y-%m-%d")
                    for dp in data_points
                ]
                raw_values = [float(dp.value) for dp in data_points]
                
                # Normalize to 0-1 range for chart display
                val_min = min(raw_values)
                val_max = max(raw_values)
                normalized = [
                    (v - val_min) / (val_max - val_min)
                    if val_max > val_min else 0.5
                    for v in raw_values
                ]
                
                series.append({
                    "name": var.display_name,
                    "unit": var.unit,
                    "dates": dates,
                    "values": normalized,      # Normalized for display
                    "raw_values": raw_values   # Raw for tooltips
                })
        
        return {
            "series": series,
            "message": f"Showing {len(series)} variables"
        }
        
    except Exception as e:
        logger.error(f"Error getting top variables time series: {e}")
        return {
            "series": [],
            "error": str(e)
        }


@router.get("/api-status")
async def get_api_status(db: Session = Depends(get_db)):
    """Get real-time API health status"""
    try:
        api_statuses = db.query(APIStatus).all()
        
        return {
            "apis": [
                {
                    "source": api.source,
                    "status": api.status,
                    "last_success": (
                        api.last_success.isoformat()
                        if api.last_success else None
                    ),
                    "last_failure": (
                        api.last_failure.isoformat()
                        if api.last_failure else None
                    ),
                    "success_count": api.success_count,
                    "failure_count": api.failure_count,
                    "error_message": api.error_message
                }
                for api in api_statuses
            ]
        }
    except Exception as e:
        logger.error(f"Error getting API status: {e}")
        return {"apis": [], "error": str(e)}


@router.post("/causality/{var1_name}/{var2_name}")
async def test_granger_causality(
    var1_name: str,
    var2_name: str,
    db: Session = Depends(get_db)
):
    """
    Test Granger causality between two variables (Phase 2)
    
    Returns bidirectional causality test results showing which variable
    (if any) Granger-causes the other.
    """
    try:
        # Find variables by display_name
        var1 = db.query(VariableMetadata).filter(
            VariableMetadata.display_name == var1_name
        ).first()
        
        if not var1:
            var1 = db.query(VariableMetadata).filter(
                VariableMetadata.display_name.ilike(f"%{var1_name}%")
            ).first()
        
        var2 = db.query(VariableMetadata).filter(
            VariableMetadata.display_name == var2_name
        ).first()
        
        if not var2:
            var2 = db.query(VariableMetadata).filter(
                VariableMetadata.display_name.ilike(f"%{var2_name}%")
            ).first()
        
        if not var1 or not var2:
            raise HTTPException(
                status_code=404,
                detail=f"Variables not found: {var1_name}, {var2_name}"
            )
        
        # Get existing correlation to use its date range
        corr = db.query(CorrelationResult).filter(
            ((CorrelationResult.variable1_id == var1.id) &
             (CorrelationResult.variable2_id == var2.id)) |
            ((CorrelationResult.variable1_id == var2.id) &
             (CorrelationResult.variable2_id == var1.id))
        ).first()
        
        # Initialize Granger causality service
        granger_service = GrangerCausalityService(max_lag=12, confidence_level=0.05)
        
        # Test causality using the same date range as correlation
        start_date = corr.start_date if corr else None
        end_date = corr.end_date if corr else None
        
        result = granger_service.test_causality(
            var1.id, 
            var2.id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Update correlation result with Granger findings if correlation exists
        if corr:
            corr.causal_direction = result['causal_direction']
            corr.granger_p_value_xy = result['var1_to_var2']['p_value']
            corr.granger_p_value_yx = result['var2_to_var1']['p_value']
            # Convert lags to int (in case it's a numpy type)
            lags_value = result['var1_to_var2']['lags']
            corr.granger_lags = int(lags_value) if lags_value is not None else None
            db.commit()
            
            logger.info(f"Updated correlation {corr.id} with Granger causality results: {result['causal_direction']}")
        
        return result
        
    except ValueError as e:
        logger.error(f"Validation error in Granger test: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error testing Granger causality: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Causality test failed: {str(e)}")


# =============================================================================
# SIGNAL RADAR: Layer 1 Fast Signals → Layer 2 Predictions
# =============================================================================

@router.get("/fast-signals")
async def get_fast_signals(db: Session = Depends(get_db)):
    """
    Get Layer 1 Fast Signals with momentum indicators.
    These are behavioral signals (Wikipedia pageviews, Reddit activity, etc.)
    that move faster than market/economic data.
    """
    from sqlalchemy import func, desc
    
    signals = []
    
    try:
        # Get all Layer 1 (Wikipedia) variables
        layer1_vars = db.query(VariableMetadata).filter(
            VariableMetadata.source == 'wikipedia',
            VariableMetadata.is_active == True
        ).all()
        
        for var in layer1_vars:
            # Get recent data points to calculate momentum
            recent_data = db.query(TimeSeriesData).filter(
                TimeSeriesData.variable_id == var.id
            ).order_by(desc(TimeSeriesData.timestamp)).limit(6).all()
            
            if len(recent_data) >= 2:
                # Calculate month-over-month momentum
                current = recent_data[0].value
                previous = recent_data[1].value
                momentum = ((current - previous) / max(previous, 1)) * 100
            else:
                momentum = 0
            
            signals.append({
                'name': var.name,
                'display_name': var.display_name,
                'momentum': round(momentum, 1),
                'layer': 1,
                'source': var.source,
                'has_data': len(recent_data) > 0
            })
        
        # Sort by absolute momentum (most active first)
        signals.sort(key=lambda x: abs(x['momentum']), reverse=True)
        
        # Generate top insight
        top_insight = None
        if signals:
            top_signal = signals[0]
            direction = 'surging' if top_signal['momentum'] > 10 else 'rising' if top_signal['momentum'] > 0 else 'declining'
            top_insight = {
                'title': f"Top Signal: {top_signal['display_name']}",
                'description': f"{top_signal['display_name']} is {direction} with {abs(top_signal['momentum']):.1f}% momentum. "
                               f"This Layer 1 behavioral signal may predict upcoming Layer 2 market movements."
            }
        
        return {
            'signals': signals[:10],  # Top 10 most active
            'total_layer1_variables': len(layer1_vars),
            'top_insight': top_insight
        }
            
    except Exception as e:
        logger.error(f"Failed to load fast signals: {e}")
        
        # Return placeholder if database query fails
        return {
            'signals': [],
            'total_layer1_variables': 0,
            'top_insight': {
                'title': 'Layer 1 Setup Required',
                'description': 'Run POST /api/admin/setup-layer1-fast-signals to add Wikipedia pageview variables for early signal detection.'
            }
        }


@router.get("/cascade-predictions/{signal_name}")
async def get_cascade_predictions(signal_name: str, db: Session = Depends(get_db)):
    """
    Get Layer 2/3 variables that the selected Layer 1 signal predicts.
    Uses Granger causality results to find predictive relationships.
    """
    from sqlalchemy import or_, and_, desc
    
    predictions = []
    
    try:
        # Find the Layer 1 variable
        layer1_var = db.query(VariableMetadata).filter(
            VariableMetadata.name == signal_name
        ).first()
        
        if not layer1_var:
            return {'predictions': [], 'top_prediction': None, 'optimal_lag': None}
        
        # Find correlations where this variable has Granger causality
        # (meaning Layer 1 signal → Layer 2/3 outcome)
        causality_results = db.query(CorrelationResult).filter(
            or_(
                and_(
                    CorrelationResult.variable1_id == layer1_var.id,
                    CorrelationResult.granger_p_value_xy != None,
                    CorrelationResult.granger_p_value_xy < 0.05
                ),
                and_(
                    CorrelationResult.variable2_id == layer1_var.id,
                    CorrelationResult.granger_p_value_yx != None,
                    CorrelationResult.granger_p_value_yx < 0.05
                )
            ),
            CorrelationResult.is_significant == True
        ).order_by(desc(CorrelationResult.abs_correlation)).limit(5).all()
        
        for result in causality_results:
            # Determine which variable is the outcome
            if result.variable1_id == layer1_var.id:
                outcome_var = result.variable2
                p_value = result.granger_p_value_xy
            else:
                outcome_var = result.variable1
                p_value = result.granger_p_value_yx
            
            # Skip if outcome is also Layer 1
            if outcome_var.source == 'wikipedia':
                continue
            
            predictions.append({
                'name': outcome_var.name,
                'display_name': outcome_var.display_name,
                'direction': 'up' if result.correlation_value > 0 else 'down',
                'p_value': f"{p_value:.4f}",
                'lag': result.granger_lags or 14,
                'correlation': result.correlation_value
            })
        
        # Generate top prediction summary
        top_prediction = None
        optimal_lag = None
        if predictions:
            top = predictions[0]
            top_prediction = f"{layer1_var.display_name} → {top['display_name']} ({top['direction'].upper()})"
            optimal_lag = top['lag']
        
        return {
            'predictions': predictions,
            'top_prediction': top_prediction,
            'optimal_lag': optimal_lag
        }
        
    except Exception as e:
        logger.error(f"Failed to load cascade predictions: {e}")
        return {'predictions': [], 'top_prediction': None, 'optimal_lag': None}


@router.get("/variable-data/{variable_name}")
async def get_variable_data(variable_name: str, db: Session = Depends(get_db)):
    """
    Debug endpoint: Get raw data for a specific variable.
    Useful for diagnosing momentum calculation issues.
    """
    from sqlalchemy import desc
    
    try:
        var = db.query(VariableMetadata).filter(
            VariableMetadata.name == variable_name
        ).first()
        
        if not var:
            return {"error": f"Variable not found: {variable_name}"}
        
        data = db.query(TimeSeriesData).filter(
            TimeSeriesData.variable_id == var.id
        ).order_by(desc(TimeSeriesData.timestamp)).limit(12).all()
        
        return {
            "variable": var.name,
            "display_name": var.display_name,
            "source": var.source,
            "data_points": len(data),
            "recent_values": [
                {
                    "date": dp.timestamp.strftime("%Y-%m-%d"),
                    "value": float(dp.value)
                }
                for dp in data
            ]
        }
    except Exception as e:
        return {"error": str(e)}
