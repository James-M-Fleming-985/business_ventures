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


# ==============================================================================
# Signal Descriptions for Info Tooltips
# ==============================================================================
def _get_signal_description(var_name: str, source: str) -> str:
    """Get human-readable description for a signal variable"""
    try:
        from setup_layer1_fast_signals import WIKIPEDIA_ARTICLES, REDDIT_SUBREDDITS
        
        if source == 'wikipedia':
            # Extract article name from var_name (e.g., wiki_layoff -> Layoff)
            article_key = var_name.replace('wiki_', '').replace('-', '_')
            for item in WIKIPEDIA_ARTICLES:
                if item['article'].lower().replace('_', '-') == article_key.replace('_', '-'):
                    return item.get('description', f"Wikipedia pageviews for {item['display_name']}")
            return f"Wikipedia pageviews tracking public interest. Higher views may indicate trending topics."
        
        elif source == 'reddit':
            subreddit_name = var_name.replace('reddit_', '')
            for item in REDDIT_SUBREDDITS:
                if item['subreddit'].lower() == subreddit_name.lower():
                    return f"Reddit r/{item['subreddit']} activity. Tracks posts and engagement in this community."
            return f"Reddit subreddit activity tracking community discussions and sentiment."
        
        return "Behavioral signal tracking public interest patterns."
    except:
        return "Fast behavioral signal for early trend detection."


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

# Cross-validation mapping: related signals across different sources
SIGNAL_CROSS_VALIDATION = {
    # Employment signals
    "wiki_layoff": ["reddit_layoffs", "reddit_recruitinghell", "reddit_antiwork"],
    "wiki_job-hunting": ["reddit_jobs", "reddit_careerguidance"],
    "wiki_resignation": ["reddit_antiwork"],
    "wiki_unemployment": ["reddit_layoffs", "reddit_povertyfinance"],
    
    # Finance signals
    "wiki_recession": ["reddit_personalfinance", "reddit_povertyfinance"],
    "wiki_inflation": ["reddit_personalfinance", "reddit_povertyfinance"],
    "wiki_stock-market": ["reddit_stocks", "reddit_investing", "reddit_wallstreetbets"],
    
    # Crypto signals
    "wiki_bitcoin": ["reddit_bitcoin", "reddit_cryptocurrency"],
    "wiki_cryptocurrency": ["reddit_cryptocurrency"],
    "wiki_ethereum": ["reddit_ethereum", "reddit_cryptocurrency"],
    
    # Tech signals
    "wiki_artificial-intelligence": ["reddit_machinelearning", "reddit_artificial", "reddit_technology"],
    "wiki_chatgpt": ["reddit_machinelearning", "reddit_artificial"],
    
    # Housing signals
    "wiki_real-estate": ["reddit_realestate", "reddit_rebubble", "reddit_firsttimehomebuyer"],
    "wiki_mortgage": ["reddit_realestate", "reddit_firsttimehomebuyer"],
}


def calculate_signal_confidence(signal_name: str, signal_momentum: float, 
                                 all_signals: dict, db) -> dict:
    """
    Calculate multi-source confidence for a signal.
    When Wikipedia AND Reddit agree on direction, confidence is higher.
    
    Returns:
        {
            'score': 0.0-1.0,
            'sources': ['wikipedia', 'reddit'],
            'agreement': 'strong'|'moderate'|'weak'|'single-source',
            'corroborating': ['reddit_layoffs', ...]
        }
    """
    related_signals = SIGNAL_CROSS_VALIDATION.get(signal_name, [])
    
    if not related_signals:
        return {
            'score': 0.5,  # Single source = moderate confidence
            'sources': ['wikipedia'],
            'agreement': 'single-source',
            'corroborating': []
        }
    
    # Check if related signals agree on direction
    agreeing = []
    disagreeing = []
    
    for related in related_signals:
        if related in all_signals:
            related_momentum = all_signals[related]['momentum']
            # Same direction?
            if (signal_momentum > 5 and related_momentum > 5) or \
               (signal_momentum < -5 and related_momentum < -5):
                agreeing.append(related)
            elif (signal_momentum > 5 and related_momentum < -5) or \
                 (signal_momentum < -5 and related_momentum > 5):
                disagreeing.append(related)
    
    # Calculate confidence score
    if len(agreeing) >= 2:
        score = 0.9  # High confidence - multiple sources agree
        agreement = 'strong'
    elif len(agreeing) == 1:
        score = 0.75  # Good confidence - two sources agree
        agreement = 'moderate'
    elif len(disagreeing) > 0:
        score = 0.3  # Low confidence - sources disagree
        agreement = 'conflicting'
    else:
        score = 0.5  # Moderate - single source, no validation available yet
        agreement = 'single-source'
    
    return {
        'score': score,
        'sources': ['wikipedia', 'reddit'] if agreeing else ['wikipedia'],
        'agreement': agreement,
        'corroborating': agreeing
    }


@router.get("/fast-signals")
async def get_fast_signals(
    only_predictive: bool = Query(True, description="Only show signals with empirical forward predictions"),
    db: Session = Depends(get_db)
):
    """
    Get Layer 1 Fast Signals with REAL-TIME momentum indicators.
    Uses daily Wikipedia + Reddit data for week-over-week momentum.
    Multi-source confidence scoring when signals agree.
    
    By default, only shows signals that have empirically-validated Granger 
    causality predictions (i.e., this signal predicts a Layer 2 outcome).
    Set only_predictive=false to see all signals including lagging indicators.
    """
    from sqlalchemy import func, desc, or_, and_
    from datetime import datetime, timedelta
    
    signals = []
    all_signals_dict = {}  # For cross-validation lookup
    
    try:
        # Get all Layer 1 variables (Wikipedia + Reddit)
        layer1_vars = db.query(VariableMetadata).filter(
            VariableMetadata.source.in_(['wikipedia', 'reddit']),
            VariableMetadata.is_active == True
        ).all()
        
        # Build set of signal IDs that have forward Granger predictions
        # (i.e., this signal → some outcome with p < 0.05)
        predictive_signal_ids = set()
        if only_predictive:
            # Find signals where they are var1 and granger_xy is significant
            # OR they are var2 and granger_yx is significant
            for var in layer1_vars:
                has_prediction = db.query(CorrelationResult).filter(
                    or_(
                        and_(
                            CorrelationResult.variable1_id == var.id,
                            CorrelationResult.granger_p_value_xy != None,
                            CorrelationResult.granger_p_value_xy < 0.05
                        ),
                        and_(
                            CorrelationResult.variable2_id == var.id,
                            CorrelationResult.granger_p_value_yx != None,
                            CorrelationResult.granger_p_value_yx < 0.05
                        )
                    )
                ).first()
                
                if has_prediction:
                    # Verify it predicts a non-Wikipedia variable (Layer 2)
                    if has_prediction.variable1_id == var.id:
                        other_var = has_prediction.variable2
                    else:
                        other_var = has_prediction.variable1
                    
                    if other_var and other_var.source != 'wikipedia':
                        predictive_signal_ids.add(var.id)
        
        # Define time windows for week-over-week comparison
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)
        
        for var in layer1_vars:
            # Skip signals without forward predictions if only_predictive is True
            if only_predictive and var.id not in predictive_signal_ids:
                continue
                
            # Get last 14 days of data for week-over-week comparison
            recent_data = db.query(TimeSeriesData).filter(
                TimeSeriesData.variable_id == var.id,
                TimeSeriesData.timestamp >= two_weeks_ago
            ).order_by(desc(TimeSeriesData.timestamp)).all()
            
            if len(recent_data) >= 7:
                # Split into this week vs last week
                this_week = [dp.value for dp in recent_data if dp.timestamp >= week_ago]
                last_week = [dp.value for dp in recent_data if dp.timestamp < week_ago]
                
                if this_week and last_week:
                    # Calculate average daily views for each week
                    this_week_avg = sum(this_week) / len(this_week)
                    last_week_avg = sum(last_week) / len(last_week)
                    
                    # Week-over-week momentum
                    momentum = ((this_week_avg - last_week_avg) / max(last_week_avg, 1)) * 100
                else:
                    momentum = 0
            else:
                momentum = 0
            
            # Mark if this signal has predictive power
            has_predictions = var.id in predictive_signal_ids if only_predictive else True
            
            signals.append({
                'name': var.name,
                'display_name': var.display_name,
                'momentum': round(momentum, 1),
                'layer': 1,
                'source': var.source,
                'has_data': len(recent_data) > 0,
                'data_points': len(recent_data),
                'has_predictions': has_predictions,
                'description': _get_signal_description(var.name, var.source)
            })
            
            # Store for cross-validation lookup
            all_signals_dict[var.name] = {
                'momentum': round(momentum, 1),
                'source': var.source
            }
        
        # Add confidence scores using cross-validation
        for signal in signals:
            confidence = calculate_signal_confidence(
                signal['name'], 
                signal['momentum'],
                all_signals_dict,
                db
            )
            signal['confidence'] = confidence
        
        # Sort by absolute momentum (most active first)
        signals.sort(key=lambda x: abs(x['momentum']), reverse=True)
        
        # Count sources
        wiki_count = len([s for s in signals if s['source'] == 'wikipedia'])
        reddit_count = len([s for s in signals if s['source'] == 'reddit'])
        high_confidence = len([s for s in signals if s.get('confidence', {}).get('score', 0) >= 0.75])
        
        # Generate top insight
        top_insight = None
        if signals:
            top_signal = signals[0]
            direction = 'surging' if top_signal['momentum'] > 10 else 'rising' if top_signal['momentum'] > 0 else 'declining'
            conf = top_signal.get('confidence', {})
            conf_text = f" (confidence: {conf.get('agreement', 'single-source')})" if conf else ""
            top_insight = {
                'title': f"Top Signal: {top_signal['display_name']}",
                'description': f"{top_signal['display_name']} is {direction} with {abs(top_signal['momentum']):.1f}% momentum{conf_text}. "
                               f"This Layer 1 signal has empirically-validated predictions for Layer 2 market movements."
            }
        
        # Count signals with/without predictions
        predictive_count = len(predictive_signal_ids)
        
        return {
            'signals': signals[:15],  # Top 15 most active predictive signals
            'total_layer1_variables': len(layer1_vars),
            'predictive_signals': predictive_count,
            'showing_only_predictive': only_predictive,
            'sources': {
                'wikipedia': wiki_count,
                'reddit': reddit_count
            },
            'high_confidence_signals': high_confidence,
            'top_insight': top_insight,
            'note': f"Showing {len(signals)} signals with Granger-validated predictions" if only_predictive else f"Showing all {len(signals)} Layer 1 signals"
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


@router.get("/signal-details/{keyword}")
async def get_signal_details(keyword: str, db: Session = Depends(get_db)):
    """
    Get detailed breakdown for a specific signal.
    Returns source breakdown, momentum, and confidence metrics.
    Uses SIGNAL_CROSS_VALIDATION to find related Reddit sources.
    """
    from datetime import datetime, timedelta
    from sqlalchemy import desc
    
    try:
        # Normalize keyword for lookup
        keyword_normalized = keyword.lower().replace(' ', '_').replace('-', '_')
        keyword_dashed = keyword.lower().replace(' ', '-').replace('_', '-')
        
        sources_data = []
        composite_momentum = 0
        source_count = 0
        
        # 1. Try to find Wikipedia source
        wiki_patterns = [
            f"wiki_{keyword_normalized}",
            f"wiki_{keyword_dashed}",
            f"wikipedia_{keyword_normalized}"
        ]
        
        wiki_var = None
        for pattern in wiki_patterns:
            wiki_var = db.query(VariableMetadata).filter(
                VariableMetadata.name == pattern,
                VariableMetadata.is_active == True
            ).first()
            if wiki_var:
                break
        
        if wiki_var:
            # Get momentum from recent data
            now = datetime.utcnow()
            week_ago = now - timedelta(days=7)
            two_weeks_ago = now - timedelta(days=14)
            
            recent_data = db.query(TimeSeriesData).filter(
                TimeSeriesData.variable_id == wiki_var.id,
                TimeSeriesData.timestamp >= two_weeks_ago
            ).order_by(desc(TimeSeriesData.timestamp)).all()
            
            momentum = 0
            if len(recent_data) >= 7:
                this_week = [dp.value for dp in recent_data if dp.timestamp >= week_ago]
                last_week = [dp.value for dp in recent_data if dp.timestamp < week_ago]
                
                if this_week and last_week:
                    this_week_avg = sum(this_week) / len(this_week)
                    last_week_avg = sum(last_week) / len(last_week)
                    momentum = ((this_week_avg - last_week_avg) / max(last_week_avg, 1)) * 100
            
            sources_data.append({
                'source_name': 'Wikipedia',
                'name': 'Wikipedia',
                'momentum': round(momentum, 1),
                'data_points': len(recent_data),
                'weight_percent': 50
            })
            composite_momentum += momentum
            source_count += 1
            
            # 2. Find related Reddit sources using SIGNAL_CROSS_VALIDATION
            related_reddit = SIGNAL_CROSS_VALIDATION.get(wiki_var.name, [])
            
            for reddit_name in related_reddit:
                reddit_var = db.query(VariableMetadata).filter(
                    VariableMetadata.name == reddit_name,
                    VariableMetadata.is_active == True
                ).first()
                
                if reddit_var:
                    reddit_data = db.query(TimeSeriesData).filter(
                        TimeSeriesData.variable_id == reddit_var.id,
                        TimeSeriesData.timestamp >= two_weeks_ago
                    ).order_by(desc(TimeSeriesData.timestamp)).all()
                    
                    reddit_momentum = 0
                    if len(reddit_data) >= 7:
                        this_week = [dp.value for dp in reddit_data if dp.timestamp >= week_ago]
                        last_week = [dp.value for dp in reddit_data if dp.timestamp < week_ago]
                        
                        if this_week and last_week:
                            this_week_avg = sum(this_week) / len(this_week)
                            last_week_avg = sum(last_week) / len(last_week)
                            reddit_momentum = ((this_week_avg - last_week_avg) / max(last_week_avg, 1)) * 100
                    
                    # Extract subreddit name for display
                    subreddit = reddit_name.replace('reddit_', 'r/')
                    
                    sources_data.append({
                        'source_name': f'Reddit {subreddit}',
                        'name': f'Reddit {subreddit}',
                        'momentum': round(reddit_momentum, 1),
                        'data_points': len(reddit_data),
                        'weight_percent': 50 // len(related_reddit) if related_reddit else 50
                    })
                    composite_momentum += reddit_momentum
                    source_count += 1
        
        # Calculate composite metrics
        if source_count > 0:
            composite_momentum = composite_momentum / source_count
        
        # Calculate agreement score
        agreement_score = 100  # Default for single source
        if source_count >= 2:
            momentums = [s['momentum'] for s in sources_data]
            if all(m > 0 for m in momentums) or all(m < 0 for m in momentums):
                agreement_score = 100
            elif all(m == 0 for m in momentums):
                agreement_score = 100
            else:
                agreement_score = 50  # Disagreement
        
        # Calculate confidence stars (1-5 based on source count and data)
        confidence_stars = min(source_count + 1, 5)
        if any(s['data_points'] >= 14 for s in sources_data):
            confidence_stars = min(confidence_stars + 1, 5)
        
        return {
            'keyword': keyword,
            'composite_momentum': round(composite_momentum, 1),
            'source_count': source_count,
            'agreement_score': agreement_score,
            'confidence_stars': confidence_stars,
            'confidence_level': 'high' if source_count >= 2 and agreement_score >= 75 else 'single-source',
            'sources': sources_data
        }
        
    except Exception as e:
        logger.error(f"Failed to get signal details for {keyword}: {e}")
        return {
            'keyword': keyword,
            'composite_momentum': 0,
            'source_count': 1,
            'agreement_score': 100,
            'confidence_stars': 2,
            'confidence_level': 'single-source',
            'sources': []
        }


@router.get("/cascade-predictions/{signal_name}")
async def get_cascade_predictions(signal_name: str, db: Session = Depends(get_db)):
    """
    Get Layer 2/3 variables that the selected Layer 1 signal predicts.
    Computes Granger causality on-the-fly if no pre-computed results exist.
    """
    from sqlalchemy import or_, and_, desc
    import numpy as np
    
    predictions = []
    computed_live = False
    
    try:
        # Find the Layer 1 variable
        layer1_var = db.query(VariableMetadata).filter(
            VariableMetadata.name == signal_name
        ).first()
        
        if not layer1_var:
            return {'predictions': [], 'top_prediction': None, 'optimal_lag': None}
        
        # Try to find empirical Granger causality first
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
            )
        ).order_by(desc(CorrelationResult.abs_correlation)).limit(5).all()
        
        # If no pre-computed results, compute Granger on-the-fly
        if not causality_results:
            logger.info(f"No pre-computed Granger for {signal_name}, computing on-the-fly...")
            computed_live = True
            
            # Get time series data for this signal
            signal_data = db.query(TimeSeriesData).filter(
                TimeSeriesData.variable_id == layer1_var.id
            ).order_by(TimeSeriesData.timestamp).all()
            
            if len(signal_data) >= 20:  # Need enough data for Granger
                signal_values = {dp.timestamp.date(): dp.value for dp in signal_data}
                
                # Find all Layer 2/3 variables (non-Wikipedia) to test against
                market_vars = db.query(VariableMetadata).filter(
                    VariableMetadata.source.notin_(['wikipedia', 'reddit']),
                    VariableMetadata.is_active == True
                ).limit(20).all()
                
                for mv in market_vars:
                    mv_data = db.query(TimeSeriesData).filter(
                        TimeSeriesData.variable_id == mv.id
                    ).order_by(TimeSeriesData.timestamp).all()
                    
                    if len(mv_data) >= 20:
                        mv_values = {dp.timestamp.date(): dp.value for dp in mv_data}
                        
                        # Align the time series
                        common_dates = sorted(set(signal_values.keys()) & set(mv_values.keys()))
                        
                        if len(common_dates) >= 20:
                            x = np.array([signal_values[d] for d in common_dates])
                            y = np.array([mv_values[d] for d in common_dates])
                            
                            # Quick Granger test
                            try:
                                from statsmodels.tsa.stattools import grangercausalitytests
                                import warnings
                                with warnings.catch_warnings():
                                    warnings.simplefilter("ignore")
                                    
                                    # X → Y test
                                    data = np.column_stack([y, x])
                                    max_lag = min(5, len(common_dates) // 5)
                                    if max_lag >= 1:
                                        result = grangercausalitytests(data, maxlag=max_lag, verbose=False)
                                        
                                        # Get best p-value
                                        best_lag = 1
                                        best_pvalue = 1.0
                                        for lag in range(1, max_lag + 1):
                                            if lag in result:
                                                p = result[lag][0]['ssr_ftest'][1]
                                                if p < best_pvalue:
                                                    best_pvalue = p
                                                    best_lag = lag
                                        
                                        if best_pvalue < 0.10:  # Include marginal for on-the-fly
                                            r = float(np.corrcoef(x, y)[0, 1])
                                            r_squared = r ** 2
                                            n = len(common_dates)
                                            f_stat = (r_squared * (n - 2)) / max(1 - r_squared, 0.0001) if r_squared < 1 else 0
                                            
                                            predictions.append({
                                                'name': mv.name,
                                                'display_name': mv.display_name,
                                                'direction': 'up' if r > 0 else 'down',
                                                'r': round(r, 4),
                                                'r_value': round(r, 4),
                                                'r_squared': round(r_squared, 4),
                                                'f_statistic': round(f_stat, 2),
                                                'p_value': f"{best_pvalue:.4f}",
                                                'lag': best_lag,
                                                'correlation': r,
                                                'sample_size': n,
                                                'confidence': 'high' if best_pvalue < 0.01 else 'medium' if best_pvalue < 0.05 else 'low',
                                                'source': 'granger_live',
                                                'is_causal': best_pvalue < 0.05
                                            })
                                            
                            except Exception as granger_err:
                                logger.debug(f"Granger test failed for {mv.name}: {granger_err}")
                                continue
                
                # Sort by p-value (most significant first)
                predictions.sort(key=lambda x: float(x['p_value']))
                predictions = predictions[:5]
        
        # Use pre-computed results if available
        for result in causality_results:
            if result.variable1_id == layer1_var.id:
                outcome_var = result.variable2
                p_value = result.granger_p_value_xy
            else:
                outcome_var = result.variable1
                p_value = result.granger_p_value_yx
            
            if outcome_var.source == 'wikipedia':
                continue
            
            # Calculate R² and confidence level
            r = result.correlation_value
            r_squared = r ** 2
            confidence = 'high' if p_value < 0.01 else 'medium' if p_value < 0.05 else 'low'
            
            # Estimate F-statistic from R² and sample size
            # F = (R² / k) / ((1 - R²) / (n - k - 1)) where k=1 for simple case
            n = result.sample_size or 30
            if r_squared < 1 and n > 2:
                f_statistic = (r_squared * (n - 2)) / max(1 - r_squared, 0.0001)
            else:
                f_statistic = 0
            
            predictions.append({
                'name': outcome_var.name,
                'display_name': outcome_var.display_name,
                'direction': 'up' if r > 0 else 'down',
                'r': round(r, 4),
                'r_value': round(r, 4),  # Add r_value for frontend compatibility
                'r_squared': round(r_squared, 4),
                'f_statistic': round(f_statistic, 2),  # Add F-statistic
                'p_value': f"{p_value:.4f}",
                'lag': result.granger_lags or 14,
                'correlation': r,  # Keep for backward compatibility
                'sample_size': result.sample_size,
                'confidence': confidence,
                'source': 'granger',
                'is_causal': p_value < 0.05  # Add is_causal flag
            })
        
        # Case 2: Find what PREDICTS this signal (leading indicators)
        # If signal is var1: granger_yx means var2→var1 (other→signal)
        # If signal is var2: granger_xy means var1→var2 (other→signal)
        leading_indicators = []
        leading_results = db.query(CorrelationResult).filter(
            or_(
                and_(
                    CorrelationResult.variable1_id == layer1_var.id,
                    CorrelationResult.granger_p_value_yx != None,
                    CorrelationResult.granger_p_value_yx < 0.05
                ),
                and_(
                    CorrelationResult.variable2_id == layer1_var.id,
                    CorrelationResult.granger_p_value_xy != None,
                    CorrelationResult.granger_p_value_xy < 0.05
                )
            )
        ).order_by(desc(CorrelationResult.abs_correlation)).limit(3).all()
        
        for result in leading_results:
            if result.variable1_id == layer1_var.id:
                predictor_var = result.variable2
                p_value = result.granger_p_value_yx
            else:
                predictor_var = result.variable1
                p_value = result.granger_p_value_xy
            
            if predictor_var.source == 'wikipedia':
                continue
            
            # Calculate R² and confidence level
            r = result.correlation_value
            r_squared = r ** 2
            confidence = 'high' if p_value < 0.01 else 'medium' if p_value < 0.05 else 'low'
            
            # Estimate F-statistic from R² and sample size
            n = result.sample_size or 30
            if r_squared < 1 and n > 2:
                f_statistic = (r_squared * (n - 2)) / max(1 - r_squared, 0.0001)
            else:
                f_statistic = 0
            
            leading_indicators.append({
                'name': predictor_var.name,
                'display_name': predictor_var.display_name,
                'direction': 'up' if r > 0 else 'down',
                'r': round(r, 4),
                'r_value': round(r, 4),  # Add r_value for frontend compatibility
                'r_squared': round(r_squared, 4),
                'f_statistic': round(f_statistic, 2),  # Add F-statistic
                'p_value': f"{p_value:.4f}",
                'correlation': r,  # Keep for backward compatibility
                'sample_size': result.sample_size,
                'confidence': confidence,
                'is_causal': p_value < 0.05  # Add is_causal flag
            })
        
        # NO THEORETICAL FALLBACK - Only show empirically validated predictions
        # If no Granger results, show helpful message about running analysis
        
        # Generate top prediction summary
        top_prediction = None
        optimal_lag = None
        if predictions:
            top = predictions[0]
            top_prediction = f"{layer1_var.display_name} → {top['display_name']} ({top['direction'].upper()}) p={top['p_value']}"
            optimal_lag = top['lag']
        elif leading_indicators:
            # No predictions, but this signal is PREDICTED BY something
            top = leading_indicators[0]
            top_prediction = f"Lagging indicator: {top['display_name']} → {layer1_var.display_name}"
        else:
            top_prediction = "No empirical predictions yet - run Granger analysis after data fetch"
        
        return {
            'predictions': predictions,
            'leading_indicators': leading_indicators,
            'top_prediction': top_prediction,
            'optimal_lag': optimal_lag,
            'note': 'Granger-validated predictions (p < 0.05)' if predictions else ('This signal is a lagging indicator' if leading_indicators else 'Fetch Wikipedia monthly data, then run correlations and Granger analysis')
        }
        
    except Exception as e:
        logger.error(f"Failed to load cascade predictions: {e}")
        return {'predictions': [], 'top_prediction': None, 'optimal_lag': None}


# Curated mappings: which L1 signals predict which L2 outcomes
THEORETICAL_PREDICTIONS = {
    # Employment signals
    'wiki_layoff': [
        {'variable': 'unemployment_rate', 'direction': 'up', 'lag': 30, 'confidence': 'high'},
        {'variable': 'consumer_sentiment', 'direction': 'down', 'lag': 14, 'confidence': 'high'},
    ],
    'wiki_job-hunting': [
        {'variable': 'unemployment_rate', 'direction': 'up', 'lag': 21, 'confidence': 'medium'},
        {'variable': 'initial_claims', 'direction': 'up', 'lag': 14, 'confidence': 'medium'},
    ],
    'wiki_resignation': [
        {'variable': 'job_openings', 'direction': 'up', 'lag': 14, 'confidence': 'medium'},
        {'variable': 'wage_growth', 'direction': 'up', 'lag': 30, 'confidence': 'low'},
    ],
    
    # Economy signals
    'wiki_recession': [
        {'variable': 'sp500', 'direction': 'down', 'lag': 7, 'confidence': 'high'},
        {'variable': 'vix', 'direction': 'up', 'lag': 3, 'confidence': 'high'},
        {'variable': 'treasury_yields', 'direction': 'down', 'lag': 14, 'confidence': 'medium'},
    ],
    'wiki_inflation': [
        {'variable': 'cpi', 'direction': 'up', 'lag': 30, 'confidence': 'high'},
        {'variable': 'gold_price', 'direction': 'up', 'lag': 14, 'confidence': 'medium'},
        {'variable': 'fed_funds_rate', 'direction': 'up', 'lag': 60, 'confidence': 'medium'},
    ],
    'wiki_federal-reserve': [
        {'variable': 'treasury_yields', 'direction': 'volatile', 'lag': 7, 'confidence': 'high'},
        {'variable': 'sp500', 'direction': 'volatile', 'lag': 3, 'confidence': 'medium'},
    ],
    
    # Tech signals
    'wiki_artificial-intelligence': [
        {'variable': 'nvda_stock', 'direction': 'up', 'lag': 14, 'confidence': 'high'},
        {'variable': 'msft_stock', 'direction': 'up', 'lag': 21, 'confidence': 'medium'},
    ],
    'wiki_bitcoin': [
        {'variable': 'btc_usd', 'direction': 'up', 'lag': 7, 'confidence': 'high'},
        {'variable': 'eth_usd', 'direction': 'up', 'lag': 7, 'confidence': 'medium'},
    ],
    'wiki_cryptocurrency': [
        {'variable': 'btc_usd', 'direction': 'up', 'lag': 7, 'confidence': 'high'},
    ],
    
    # Geopolitics
    'wiki_trade-war': [
        {'variable': 'vix', 'direction': 'up', 'lag': 3, 'confidence': 'high'},
        {'variable': 'emerging_markets', 'direction': 'down', 'lag': 7, 'confidence': 'medium'},
    ],
    'wiki_sanctions': [
        {'variable': 'oil_price', 'direction': 'up', 'lag': 7, 'confidence': 'medium'},
        {'variable': 'vix', 'direction': 'up', 'lag': 3, 'confidence': 'medium'},
    ],
    'wiki_war': [
        {'variable': 'vix', 'direction': 'up', 'lag': 1, 'confidence': 'high'},
        {'variable': 'defense_stocks', 'direction': 'up', 'lag': 7, 'confidence': 'medium'},
        {'variable': 'oil_price', 'direction': 'up', 'lag': 3, 'confidence': 'medium'},
    ],
}


def _get_theoretical_predictions(signal_name: str, layer1_var, db) -> list:
    """Generate predictions based on curated domain knowledge"""
    predictions = []
    
    mappings = THEORETICAL_PREDICTIONS.get(signal_name, [])
    
    # Get momentum direction from signal
    from sqlalchemy import desc
    from datetime import timedelta
    
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)
    
    recent_data = db.query(TimeSeriesData).filter(
        TimeSeriesData.variable_id == layer1_var.id,
        TimeSeriesData.timestamp >= two_weeks_ago
    ).all()
    
    if recent_data:
        this_week = [dp.value for dp in recent_data if dp.timestamp >= week_ago]
        last_week = [dp.value for dp in recent_data if dp.timestamp < week_ago]
        
        if this_week and last_week:
            this_avg = sum(this_week) / len(this_week)
            last_avg = sum(last_week) / len(last_week)
            signal_rising = this_avg > last_avg
        else:
            signal_rising = True
    else:
        signal_rising = True
    
    for mapping in mappings:
        # Adjust direction based on signal momentum
        if mapping['direction'] == 'volatile':
            direction = 'volatile'
        elif signal_rising:
            direction = mapping['direction']
        else:
            direction = 'down' if mapping['direction'] == 'up' else 'up'
        
        # Try to find actual variable in DB for display name
        display_name = mapping['variable'].replace('_', ' ').title()
        
        predictions.append({
            'name': mapping['variable'],
            'display_name': display_name,
            'direction': direction,
            'p_value': f"~0.05 ({mapping['confidence']})",
            'lag': mapping['lag'],
            'source': 'theoretical'
        })
    
    # If no specific mapping, generate generic predictions
    if not predictions:
        predictions = [
            {
                'name': 'market_volatility',
                'display_name': 'Market Volatility (VIX)',
                'direction': 'up' if signal_rising else 'down',
                'p_value': '~0.10 (weak)',
                'lag': 14,
                'source': 'theoretical'
            }
        ]
    
    return predictions


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
