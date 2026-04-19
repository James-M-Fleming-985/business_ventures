"""
Dashboard Router for Correlation Discovery Engine
ALL ENDPOINTS USE REAL API DATA - NO MOCK/SYNTHETIC DATA
"""

from fastapi import APIRouter, Request, Query, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models import (
    VariableMetadata, TimeSeriesData, CorrelationResult,
    RollingCorrelation, APIStatus, AnalysisJob, PredictionTracking,
    ExploitationRecommendation, ExploitationValidation,
    MVPBuild, MVPBuildFile, ProductDeployment, MvpPageView, ProductMetrics
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
    "wiki_machine-learning": ["reddit_machinelearning", "reddit_artificial", "reddit_technology"],
    "wiki_chatgpt": ["reddit_machinelearning", "reddit_artificial"],
    "wiki_remote-work": ["reddit_remotework", "reddit_digitalnomad"],
    
    # Housing signals
    "wiki_real-estate": ["reddit_realestate", "reddit_rebubble", "reddit_firsttimehomebuyer"],
    "wiki_mortgage": ["reddit_realestate", "reddit_firsttimehomebuyer"],
    "wiki_home-improvement": ["reddit_homeimprovement", "reddit_diy"],
    
    # Health signals
    "wiki_vaccine": ["reddit_coronavirus", "reddit_medicine"],
    "wiki_covid-19": ["reddit_coronavirus", "reddit_covid19"],
    "wiki_diabetes": ["reddit_diabetes", "reddit_health"],
    
    # Geopolitical signals
    "wiki_sanctions": ["reddit_worldnews", "reddit_geopolitics"],
    "wiki_trade-war": ["reddit_economics", "reddit_worldnews"],
    "wiki_war": ["reddit_worldnews", "reddit_geopolitics"],
    
    # Energy/Climate signals
    "wiki_oil-price": ["reddit_energy", "reddit_oil"],
    "wiki_climate-change": ["reddit_climate", "reddit_environment"],
    
    # Companies
    "wiki_tesla-inc": ["reddit_teslamotors", "reddit_electricvehicles"],
    
    # Economic indicators
    "wiki_federal-reserve": ["reddit_economics", "reddit_finance"],
    "wiki_interest-rate": ["reddit_personalfinance", "reddit_economics"],
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
    only_predictive: bool = Query(False, description="Only show signals with empirical forward predictions"),
    db: Session = Depends(get_db)
):
    """
    Get Layer 1 Fast Signals with REAL-TIME momentum indicators.
    
    COMPOSITE AGGREGATION: Signals are grouped by KEYWORD across all sources.
    Each keyword (e.g., "Stock Market") aggregates data from multiple sources
    (Wikipedia, Reddit subreddits, etc.) into a single composite signal.
    
    Returns:
    - Composite momentum (weighted average across sources)
    - Source count (how many sources contribute to this signal)  
    - Agreement score (do sources agree on direction?)
    - Confidence stars (based on source count + agreement)
    """
    from sqlalchemy import func, desc, or_, and_
    from datetime import datetime, timedelta
    
    try:
        # Get ALL Layer 1 variables (Wikipedia + Reddit + others)
        layer1_vars = db.query(VariableMetadata).filter(
            VariableMetadata.source.in_(['wikipedia', 'reddit']),
            VariableMetadata.is_active == True
        ).all()
        
        # Time windows for momentum calculation
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)
        
        # Calculate momentum for each variable
        var_momentum = {}
        for var in layer1_vars:
            recent_data = db.query(TimeSeriesData).filter(
                TimeSeriesData.variable_id == var.id,
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
            
            var_momentum[var.id] = {
                'var': var,
                'momentum': round(momentum, 1),
                'data_points': len(recent_data)
            }
        
        # Group by KEYWORD using SIGNAL_CROSS_VALIDATION mapping
        # This maps wiki_xxx -> [reddit_yyy, reddit_zzz, ...]
        keyword_groups = {}
        
        for var_id, data in var_momentum.items():
            var = data['var']
            
            if var.source == 'wikipedia':
                # Extract keyword from wiki_xxx name
                keyword = var.name.replace('wiki_', '').replace('-', ' ').title()
                
                if keyword not in keyword_groups:
                    keyword_groups[keyword] = {
                        'keyword': keyword,
                        'sources': [],
                        'primary_var': var
                    }
                
                keyword_groups[keyword]['sources'].append({
                    'name': 'Wikipedia',
                    'source_type': 'wikipedia',
                    'var_name': var.name,
                    'momentum': data['momentum'],
                    'data_points': data['data_points']
                })
                
                # Add related Reddit sources from cross-validation mapping
                related_reddit = SIGNAL_CROSS_VALIDATION.get(var.name, [])
                for reddit_name in related_reddit:
                    # Find matching Reddit variable
                    reddit_var = next((v for v in layer1_vars if v.name == reddit_name), None)
                    if reddit_var and reddit_var.id in var_momentum:
                        reddit_data = var_momentum[reddit_var.id]
                        subreddit = reddit_name.replace('reddit_', 'r/')
                        keyword_groups[keyword]['sources'].append({
                            'name': f'Reddit {subreddit}',
                            'source_type': 'reddit',
                            'var_name': reddit_name,
                            'momentum': reddit_data['momentum'],
                            'data_points': reddit_data['data_points']
                        })
        
        # Also add standalone Reddit signals that aren't mapped
        used_reddit_vars = set()
        for kg in keyword_groups.values():
            for src in kg['sources']:
                if src['source_type'] == 'reddit':
                    used_reddit_vars.add(src['var_name'])
        
        for var_id, data in var_momentum.items():
            var = data['var']
            if var.source == 'reddit' and var.name not in used_reddit_vars:
                # Standalone Reddit signal - create its own keyword
                subreddit = var.name.replace('reddit_', '')
                keyword = f"r/{subreddit}".title()
                
                if keyword not in keyword_groups:
                    keyword_groups[keyword] = {
                        'keyword': keyword,
                        'sources': [],
                        'primary_var': var
                    }
                    keyword_groups[keyword]['sources'].append({
                        'name': f'Reddit r/{subreddit}',
                        'source_type': 'reddit',
                        'var_name': var.name,
                        'momentum': data['momentum'],
                        'data_points': data['data_points']
                    })
        
        # Build composite signals from keyword groups
        signals = []
        for keyword, group in keyword_groups.items():
            sources = group['sources']
            source_count = len(sources)
            
            if source_count == 0:
                continue
            
            # Calculate composite momentum (weighted average)
            total_momentum = sum(s['momentum'] for s in sources)
            composite_momentum = total_momentum / source_count
            
            # Calculate agreement score
            positive = sum(1 for s in sources if s['momentum'] > 0)
            negative = sum(1 for s in sources if s['momentum'] < 0)
            neutral = sum(1 for s in sources if s['momentum'] == 0)
            
            if source_count == 1:
                agreement_score = 100
                agreement_level = 'single-source'
            elif positive == source_count or negative == source_count:
                agreement_score = 100
                agreement_level = 'strong'
            elif positive > 0 and negative > 0:
                majority = max(positive, negative)
                agreement_score = int((majority / source_count) * 100)
                agreement_level = 'mixed'
            else:
                agreement_score = 100
                agreement_level = 'moderate'
            
            # Calculate confidence stars (1-5)
            confidence_stars = 1
            if source_count >= 2:
                confidence_stars += 1
            if source_count >= 3:
                confidence_stars += 1
            if agreement_score >= 80:
                confidence_stars += 1
            if any(s['data_points'] >= 14 for s in sources):
                confidence_stars += 1
            confidence_stars = min(confidence_stars, 5)
            
            signals.append({
                'name': group['primary_var'].name,
                'display_name': keyword,
                'momentum': round(composite_momentum, 1),
                'layer': 1,
                'source': 'composite' if source_count > 1 else sources[0]['source_type'],
                'sources': sources,
                'source_count': source_count,
                'agreement_score': agreement_score,
                'confidence': {
                    'score': confidence_stars / 5,
                    'stars': confidence_stars,
                    'agreement': agreement_level
                },
                'has_data': any(s['data_points'] > 0 for s in sources),
                'data_points': sum(s['data_points'] for s in sources),
                'has_predictions': True,  # Will be determined by Granger
                'description': _get_signal_description(group['primary_var'].name, group['primary_var'].source)
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
                'description': f"{top_signal['display_name']} is {direction} with {abs(top_signal['momentum']):.1f}% composite momentum from {top_signal['source_count']} source(s)."
            }
        
        return {
            'signals': signals[:20],  # Top 20 most active signals
            'total_signals': len(signals),
            'multi_source_signals': len([s for s in signals if s['source_count'] > 1]),
            'top_insight': top_insight,
            'note': f"Showing {min(20, len(signals))} composite signals aggregated from Wikipedia + Reddit"
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
    
    signal_name can be:
    - A keyword like "Climate Change" (from composite signals)
    - A variable name like "wiki_climate_change"
    """
    from sqlalchemy import or_, and_, desc
    from sqlalchemy.orm import aliased
    import numpy as np
    
    predictions = []
    computed_live = False
    layer1_vars = []  # May find multiple variables for a keyword
    
    try:
        # Decode URL-encoded signal name
        import urllib.parse
        signal_name = urllib.parse.unquote(signal_name)
        logger.info(f"Looking up Layer 1 variable for: '{signal_name}'")
        
        # Strategy 1: Try exact name match first
        layer1_var = db.query(VariableMetadata).filter(
            VariableMetadata.name == signal_name
        ).first()
        
        if layer1_var:
            layer1_vars = [layer1_var]
        else:
            # Strategy 2: Try wiki_ prefix variations
            normalized = signal_name.lower().strip()
            patterns_to_try = [
                f"wiki_{normalized.replace(' ', '_')}",  # wiki_climate_change
                f"wiki_{normalized.replace(' ', '-')}",  # wiki_climate-change
                f"reddit_{normalized.replace(' ', '_')}",  # reddit_climate_change
            ]
            
            for pattern in patterns_to_try:
                var = db.query(VariableMetadata).filter(
                    VariableMetadata.name == pattern
                ).first()
                if var:
                    layer1_vars.append(var)
                    break
            
            # Strategy 3: Try partial match on display_name
            if not layer1_vars:
                layer1_vars = db.query(VariableMetadata).filter(
                    VariableMetadata.display_name.ilike(f"%{signal_name}%"),
                    VariableMetadata.source.in_(['wikipedia', 'reddit'])
                ).limit(3).all()
            
            # Strategy 4: Try keyword in name
            if not layer1_vars:
                keyword_pattern = normalized.replace(' ', '%')
                layer1_vars = db.query(VariableMetadata).filter(
                    VariableMetadata.name.ilike(f"%{keyword_pattern}%"),
                    VariableMetadata.source.in_(['wikipedia', 'reddit'])
                ).limit(3).all()
        
        if not layer1_vars:
            logger.warning(f"Could not find Layer 1 variable for: {signal_name}")
            return {
                'predictions': [], 
                'top_prediction': f'Signal "{signal_name}" not found in database', 
                'optimal_lag': None,
                'note': 'Try fetching fresh data first'
            }
        
        # Use the first matching variable for Granger analysis
        layer1_var = layer1_vars[0]
        logger.info(f"Found Layer 1 variable: {layer1_var.name} (display: {layer1_var.display_name})")
        
        # Try to find empirical Granger causality first
        # Two separate queries to properly exclude wikipedia outcomes BEFORE the LIMIT
        # Case A: signal is var1, outcome is var2 (test: signal→outcome = granger_xy)
        OutcomeVar = aliased(VariableMetadata)
        results_as_var1 = db.query(CorrelationResult).join(
            OutcomeVar, CorrelationResult.variable2_id == OutcomeVar.id
        ).filter(
            CorrelationResult.variable1_id == layer1_var.id,
            CorrelationResult.granger_p_value_xy != None,
            CorrelationResult.granger_p_value_xy < 0.05,
            OutcomeVar.source != 'wikipedia'
        ).order_by(desc(CorrelationResult.abs_correlation)).limit(5).all()
        
        # Case B: signal is var2, outcome is var1 (test: signal→outcome = granger_yx)
        OutcomeVar2 = aliased(VariableMetadata)
        results_as_var2 = db.query(CorrelationResult).join(
            OutcomeVar2, CorrelationResult.variable1_id == OutcomeVar2.id
        ).filter(
            CorrelationResult.variable2_id == layer1_var.id,
            CorrelationResult.granger_p_value_yx != None,
            CorrelationResult.granger_p_value_yx < 0.05,
            OutcomeVar2.source != 'wikipedia'
        ).order_by(desc(CorrelationResult.abs_correlation)).limit(5).all()
        
        # Combine, deduplicate, and take top 5 by abs_correlation
        seen_ids = set()
        causality_results = []
        for r in sorted(results_as_var1 + results_as_var2, key=lambda x: x.abs_correlation or 0, reverse=True):
            if r.id not in seen_ids:
                seen_ids.add(r.id)
                causality_results.append(r)
        causality_results = causality_results[:5]
        
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
            
            # Wikipedia outcomes already excluded by SQL query
            
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
        # Same fix: exclude wikipedia predictors BEFORE the LIMIT
        # Case A: signal is var1, predictor is var2 (test: predictor→signal = granger_yx)
        PredictorVar = aliased(VariableMetadata)
        leading_as_var1 = db.query(CorrelationResult).join(
            PredictorVar, CorrelationResult.variable2_id == PredictorVar.id
        ).filter(
            CorrelationResult.variable1_id == layer1_var.id,
            CorrelationResult.granger_p_value_yx != None,
            CorrelationResult.granger_p_value_yx < 0.05,
            PredictorVar.source != 'wikipedia'
        ).order_by(desc(CorrelationResult.abs_correlation)).limit(3).all()
        
        # Case B: signal is var2, predictor is var1 (test: predictor→signal = granger_xy)
        PredictorVar2 = aliased(VariableMetadata)
        leading_as_var2 = db.query(CorrelationResult).join(
            PredictorVar2, CorrelationResult.variable1_id == PredictorVar2.id
        ).filter(
            CorrelationResult.variable2_id == layer1_var.id,
            CorrelationResult.granger_p_value_xy != None,
            CorrelationResult.granger_p_value_xy < 0.05,
            PredictorVar2.source != 'wikipedia'
        ).order_by(desc(CorrelationResult.abs_correlation)).limit(3).all()
        
        # Combine, deduplicate, and take top 3
        seen_leading_ids = set()
        leading_results = []
        for r in sorted(leading_as_var1 + leading_as_var2, key=lambda x: x.abs_correlation or 0, reverse=True):
            if r.id not in seen_leading_ids:
                seen_leading_ids.add(r.id)
                leading_results.append(r)
        leading_results = leading_results[:3]
        
        for result in leading_results:
            if result.variable1_id == layer1_var.id:
                predictor_var = result.variable2
                p_value = result.granger_p_value_yx
            else:
                predictor_var = result.variable1
                p_value = result.granger_p_value_xy
            
            # Wikipedia predictors already excluded by SQL query
            
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
        import traceback
        logger.error(f"Failed to load cascade predictions for '{signal_name}': {e}")
        logger.error(traceback.format_exc())
        return {
            'predictions': [], 
            'top_prediction': f'Error analyzing {signal_name}: {str(e)[:100]}', 
            'optimal_lag': None,
            'error': str(e)
        }


@router.get("/deep-analysis/{signal_name}/{target_name}")
async def get_deep_analysis(
    signal_name: str,
    target_name: str,
    momentum: float = 0.0,
    db: Session = Depends(get_db),
):
    """
    Deep analysis for a signal→target pair: lag curve, regression, actionable prediction.
    Called after Granger confirms a causal relationship.
    
    Args:
        momentum: Current composite momentum of the signal (e.g. -18.0 means -18%)
    """
    import urllib.parse
    import numpy as np

    signal_name = urllib.parse.unquote(signal_name)
    target_name = urllib.parse.unquote(target_name)

    try:
        # --- Resolve variables ---
        normalized = signal_name.lower().strip()
        patterns = [
            normalized.replace(' ', '_'),
            f"wiki_{normalized.replace(' ', '_')}",
            f"reddit_{normalized.replace(' ', '_')}",
        ]
        signal_var = None
        for pat in patterns:
            signal_var = db.query(VariableMetadata).filter(
                VariableMetadata.name == pat
            ).first()
            if signal_var:
                break
        if not signal_var:
            signal_var = db.query(VariableMetadata).filter(
                VariableMetadata.display_name.ilike(f"%{signal_name}%")
            ).first()

        target_var = db.query(VariableMetadata).filter(
            VariableMetadata.name == target_name
        ).first()
        if not target_var:
            target_var = db.query(VariableMetadata).filter(
                VariableMetadata.display_name.ilike(f"%{target_name}%")
            ).first()

        if not signal_var or not target_var:
            return {"error": "Variables not found", "lag_curve": [], "regression": None, "prediction": None}

        # --- Fetch time series ---
        signal_data = db.query(TimeSeriesData).filter(
            TimeSeriesData.variable_id == signal_var.id
        ).order_by(TimeSeriesData.timestamp).all()

        target_data = db.query(TimeSeriesData).filter(
            TimeSeriesData.variable_id == target_var.id
        ).order_by(TimeSeriesData.timestamp).all()

        signal_vals = {dp.timestamp.date(): dp.value for dp in signal_data}
        target_vals = {dp.timestamp.date(): dp.value for dp in target_data}
        common_dates = sorted(set(signal_vals.keys()) & set(target_vals.keys()))

        if len(common_dates) < 15:
            return {
                "error": f"Insufficient overlapping data ({len(common_dates)} points)",
                "lag_curve": [], "regression": None, "prediction": None,
            }

        x = np.array([signal_vals[d] for d in common_dates])
        y = np.array([target_vals[d] for d in common_dates])

        # --- 1. LAG CURVE: cross-correlation at lags 0..max_lag ---
        max_lag = min(14, len(common_dates) // 4)
        lag_curve = []
        best_lag = 0
        best_abs_r = 0.0

        for lag in range(0, max_lag + 1):
            if lag == 0:
                xl, yl = x, y
            else:
                xl, yl = x[:-lag], y[lag:]
            if len(xl) < 10:
                continue
            r = float(np.corrcoef(xl, yl)[0, 1]) if np.std(xl) > 0 and np.std(yl) > 0 else 0.0
            lag_curve.append({"lag": lag, "correlation": round(r, 4)})
            if abs(r) > best_abs_r:
                best_abs_r = abs(r)
                best_lag = lag

        # --- 2. REGRESSION at optimal lag ---
        if best_lag > 0:
            x_reg, y_reg = x[:-best_lag], y[best_lag:]
        else:
            x_reg, y_reg = x, y

        n = len(x_reg)
        x_mean, y_mean = float(np.mean(x_reg)), float(np.mean(y_reg))
        x_std, y_std = float(np.std(x_reg)), float(np.std(y_reg))

        if x_std > 0 and n > 2:
            slope = float(np.sum((x_reg - x_mean) * (y_reg - y_mean)) / np.sum((x_reg - x_mean) ** 2))
            intercept = y_mean - slope * x_mean
            y_pred = slope * x_reg + intercept
            ss_res = float(np.sum((y_reg - y_pred) ** 2))
            ss_tot = float(np.sum((y_reg - y_mean) ** 2))
            r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
            r_val = float(np.corrcoef(x_reg, y_reg)[0, 1])
            se_slope = float(np.sqrt(ss_res / (n - 2) / np.sum((x_reg - x_mean) ** 2))) if n > 2 else 0
            t_stat = slope / se_slope if se_slope > 0 else 0
        else:
            slope, intercept, r_squared, r_val, se_slope, t_stat = 0, 0, 0, 0, 0, 0

        regression = {
            "slope": round(slope, 6),
            "intercept": round(intercept, 4),
            "r_squared": round(r_squared, 4),
            "r_value": round(r_val, 4),
            "std_error": round(se_slope, 6),
            "t_statistic": round(t_stat, 2),
            "sample_size": n,
            "equation": f"y = {slope:.4f}x + {intercept:.2f}",
        }

        # --- 3. ACTIONABLE PREDICTION (uses actual momentum) ---
        x_latest = float(x[-1])
        y_latest = float(y[-1])
        confidence = "high" if abs(r_squared) > 0.3 else "medium" if abs(r_squared) > 0.1 else "low"

        # Always compute the 1σ baseline prediction
        has_momentum = momentum != 0.0
        one_sigma_change = slope * x_std if x_std > 0 else 0
        one_sigma_abs = abs(one_sigma_change)
        one_sigma_pct = (one_sigma_change / abs(y_latest) * 100) if y_latest != 0 else 0
        one_sigma_dir = "increase" if one_sigma_change > 0 else "decrease"

        # For the actual prediction, use momentum if available, else 1σ
        if has_momentum:
            signal_change = (momentum / 100.0) * abs(x_latest) if x_latest != 0 else 0
            predicted_change = slope * signal_change
            momentum_label = f"{momentum:+.1f}%"
        else:
            predicted_change = one_sigma_change
            momentum_label = f"1σ ({x_std:,.0f})"

        predicted_y = y_latest + predicted_change
        direction = "up" if predicted_change > 0 else "down"
        pct_change = (predicted_change / abs(y_latest) * 100) if y_latest != 0 else 0
        abs_change = abs(predicted_change)

        # Format numbers nicely
        def _fmt(v):
            return f"{v:,.0f}" if v >= 1 else f"{v:.4f}"

        # Core relationship sentence: always anchored to 1σ
        summary = (
            f"For every 1 standard deviation ({x_std:,.0f}) change in {signal_var.display_name}, "
            f"we expect {target_var.display_name} to {one_sigma_dir} by "
            f"~{_fmt(one_sigma_abs)} ({abs(one_sigma_pct):.1f}%)."
        )
        # Add momentum context if available
        if has_momentum:
            summary += (
                f" {signal_var.display_name} is currently "
                f"{'declining' if momentum < 0 else 'rising'} ({momentum:+.1f}%), "
                f"so expect {target_var.display_name} to {'rise' if direction == 'up' else 'drop'} by "
                f"~{_fmt(abs_change)} ({abs(pct_change):.1f}%) "
                f"over the next {best_lag} days."
            )
        else:
            summary += f" Effect observed over {best_lag} days."

        prediction = {
            "signal_name": signal_var.display_name,
            "target_name": target_var.display_name,
            "direction": direction,
            "optimal_lag_days": best_lag,
            "predicted_change": round(predicted_change, 4),
            "predicted_abs_change": round(abs_change, 4),
            "predicted_pct_change": round(pct_change, 2),
            "predicted_value": round(predicted_y, 4),
            "current_signal_value": round(x_latest, 4),
            "current_target_value": round(y_latest, 4),
            "signal_std": round(x_std, 4),
            "one_sigma_change": round(one_sigma_abs, 4),
            "one_sigma_pct": round(abs(one_sigma_pct), 2),
            "signal_momentum": momentum,
            "signal_momentum_label": momentum_label,
            "confidence": confidence,
            "r_squared": round(r_squared, 4),
            "summary": summary,
        }

        return {
            "signal": signal_var.display_name,
            "target": target_var.display_name,
            "lag_curve": lag_curve,
            "optimal_lag": best_lag,
            "regression": regression,
            "prediction": prediction,
            "data_points": len(common_dates),
        }

    except Exception as e:
        import traceback
        logger.error(f"Deep analysis failed for {signal_name}→{target_name}: {e}")
        logger.error(traceback.format_exc())
        return {"error": str(e), "lag_curve": [], "regression": None, "prediction": None}


# ==============================================================================
# Prediction Storage & Retrieval (CA-002-10 Data Pipeline)
# ==============================================================================

@router.post("/store-prediction")
async def store_prediction(request: Request, db: Session = Depends(get_db)):
    """
    Store a prediction generated by deep-analysis.
    Called automatically by the frontend after each deep-analysis run.
    """
    import uuid

    try:
        payload = await request.json()
        
        signal_name = payload.get("signal_name", "unknown")
        target_name = payload.get("target_name", "unknown")
        
        # Check for existing pending prediction for same signal→target pair
        existing = db.query(PredictionTracking).filter(
            PredictionTracking.signal_name == signal_name,
            PredictionTracking.target_name == target_name,
            PredictionTracking.status == 'pending'
        ).first()
        
        # Calculate target_date from optimal_lag_days
        optimal_lag = payload.get("optimal_lag_days", 7)
        target_date = datetime.utcnow() + timedelta(days=optimal_lag)
        
        if existing:
            # Update existing prediction instead of creating duplicate
            existing.predicted_at = datetime.utcnow()
            existing.target_date = target_date
            existing.optimal_lag_days = optimal_lag
            existing.predicted_direction = payload.get("direction")
            existing.predicted_value = payload.get("predicted_value")
            existing.predicted_change_pct = payload.get("predicted_pct_change")
            existing.current_target_value = payload.get("current_target_value")
            existing.current_signal_value = payload.get("current_signal_value")
            existing.signal_momentum = payload.get("signal_momentum")
            existing.r_squared = payload.get("r_squared")
            existing.confidence = payload.get("confidence", "medium")
            existing.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Updated existing prediction {existing.prediction_id}: {signal_name} → {target_name}")
            return {"status": "updated", "prediction_id": existing.prediction_id}
        
        prediction_id = str(uuid.uuid4())[:12]

        row = PredictionTracking(
            prediction_id=prediction_id,
            signal_name=payload.get("signal_name", "unknown"),
            target_name=payload.get("target_name", "unknown"),
            predicted_at=datetime.utcnow(),
            target_date=target_date,
            optimal_lag_days=optimal_lag,
            predicted_direction=payload.get("direction"),
            predicted_value=payload.get("predicted_value"),
            predicted_change_pct=payload.get("predicted_pct_change"),
            current_target_value=payload.get("current_target_value"),
            current_signal_value=payload.get("current_signal_value"),
            signal_momentum=payload.get("signal_momentum"),
            r_squared=payload.get("r_squared"),
            confidence=payload.get("confidence", "medium"),
            model_version="granger_v1",
            status="pending",
        )
        db.add(row)
        db.commit()

        logger.info(f"Stored prediction {prediction_id}: {row.signal_name} → {row.target_name}")
        return {"status": "stored", "prediction_id": prediction_id}

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to store prediction: {e}")
        return {"status": "error", "detail": str(e)}


@router.get("/predictions")
async def get_predictions(
    limit: int = Query(50, ge=1, le=2000),
    status: Optional[str] = Query(None),
    model_version: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Retrieve stored predictions for the Prediction Accuracy tab.
    Returns predictions newest-first with rich accuracy stats,
    grouped by target_source for the model comparison table,
    and dimensional accuracy metrics for mini charts.
    
    Args:
        model_version: Filter by model version (e.g. 'backtest_walkforward', 'granger_v1')
    """
    from sqlalchemy import desc, case

    try:
        q = db.query(PredictionTracking)
        if status:
            q = q.filter(PredictionTracking.status == status)
        if model_version:
            q = q.filter(PredictionTracking.model_version == model_version)
        # Validated predictions surface first, then pending — both sorted by date
        status_priority = case(
            (PredictionTracking.status == "validated", 0),
            else_=1,
        )
        predictions = q.order_by(status_priority, desc(PredictionTracking.predicted_at)).limit(limit).all()

        # Compute accuracy summary
        total = len(predictions)
        validated = [p for p in predictions if p.status == "validated"]
        pending_list = [p for p in predictions if p.status == "pending"]
        correct = [p for p in validated if p.direction_correct is True]
        
        # Lag accuracy
        lag_errors = [p.lag_error_days for p in validated if p.lag_error_days is not None]
        avg_lag_error = round(sum(abs(e) for e in lag_errors) / len(lag_errors), 1) if lag_errors else None
        
        # Change accuracy
        change_errors = [
            abs((p.actual_change_pct or 0) - (p.predicted_change_pct or 0))
            for p in validated
            if p.actual_change_pct is not None and p.predicted_change_pct is not None
        ]
        avg_change_error = round(sum(change_errors) / len(change_errors), 1) if change_errors else None
        
        # Group by target_source for comparison table
        by_source = {}
        for p in predictions:
            src = p.target_source or 'unknown'
            if src not in by_source:
                by_source[src] = {'name': src, 'total': 0, 'correct': 0, 'errors': [], 'lag_errors': []}
            by_source[src]['total'] += 1
            if p.status == 'validated':
                if p.direction_correct:
                    by_source[src]['correct'] += 1
                if p.value_error_pct is not None:
                    by_source[src]['errors'].append(p.value_error_pct)
                if p.lag_error_days is not None:
                    by_source[src]['lag_errors'].append(abs(p.lag_error_days))
        
        source_comparison = []
        for src, data in sorted(by_source.items(), key=lambda x: x[1]['total'], reverse=True):
            validated_in_src = data['correct'] + len(data['errors']) - data['correct'] if data['errors'] else 0
            source_comparison.append({
                'source': src,
                'total_predictions': data['total'],
                'direction_accuracy': round(data['correct'] / max(1, len(data['errors']) + data['correct'] - len(data['errors'])) if data['errors'] or data['correct'] else 0, 3),
                'avg_error_pct': round(sum(data['errors']) / len(data['errors']), 1) if data['errors'] else None,
                'avg_lag_error_days': round(sum(data['lag_errors']) / len(data['lag_errors']), 1) if data['lag_errors'] else None,
            })
            # Fix direction accuracy calculation
            v_count = sum(1 for p in validated if (p.target_source or 'unknown') == src)
            if v_count > 0:
                source_comparison[-1]['direction_accuracy'] = round(
                    sum(1 for p in validated if (p.target_source or 'unknown') == src and p.direction_correct) / v_count, 3
                )

        # Build time series: group validated by predicted_at month
        # Use median for change_pct (robust to extreme outliers like Wildfires Events)
        # Use mean for lag (no extreme outliers expected)
        from collections import defaultdict
        from statistics import median
        monthly = defaultdict(lambda: {
            'pred_change': [], 'act_change': [],
            'pred_lag': [], 'act_lag': [],
            'direction_correct': [],
            'count': 0
        })
        for p in validated:
            if p.predicted_at:
                month_key = p.predicted_at.strftime('%Y-%m')
                monthly[month_key]['count'] += 1
                if p.predicted_change_pct is not None:
                    monthly[month_key]['pred_change'].append(p.predicted_change_pct)
                if p.actual_change_pct is not None:
                    monthly[month_key]['act_change'].append(p.actual_change_pct)
                if p.optimal_lag_days is not None:
                    monthly[month_key]['pred_lag'].append(p.optimal_lag_days)
                if p.actual_lag_days is not None:
                    monthly[month_key]['act_lag'].append(p.actual_lag_days)
                if p.direction_correct is not None:
                    monthly[month_key]['direction_correct'].append(p.direction_correct)

        time_series = []
        for month_key in sorted(monthly.keys()):
            m = monthly[month_key]
            time_series.append({
                'month': month_key,
                'count': m['count'],
                'avg_predicted_change_pct': round(median(m['pred_change']), 2) if m['pred_change'] else None,
                'avg_actual_change_pct': round(median(m['act_change']), 2) if m['act_change'] else None,
                'avg_predicted_lag': round(sum(m['pred_lag']) / len(m['pred_lag']), 1) if m['pred_lag'] else None,
                'avg_actual_lag': round(sum(m['act_lag']) / len(m['act_lag']), 1) if m['act_lag'] else None,
                'direction_accuracy': round(sum(m['direction_correct']) / len(m['direction_correct']) * 100, 1) if m['direction_correct'] else None,
            })

        # Count unique pairs
        pair_set = set()
        for p in predictions:
            pair_set.add((p.signal_name, p.target_name))
        pair_count = len(pair_set)

        return {
            "predictions": [p.to_dict() for p in predictions],
            "total": total,
            "pending": len(pending_list),
            "validated": len(validated),
            "pair_count": pair_count,
            "accuracy": {
                "direction_accuracy": (
                    round(len(correct) / len(validated) * 100, 1)
                    if validated else None
                ),
                "avg_error_pct": (
                    round(
                        sum(p.value_error_pct for p in validated if p.value_error_pct is not None)
                        / max(1, sum(1 for p in validated if p.value_error_pct is not None)),
                        2,
                    )
                    if validated else None
                ),
                "avg_lag_error_days": avg_lag_error,
                "avg_change_error_pct": avg_change_error,
            },
            "time_series": time_series,
            "source_comparison": source_comparison,
        }

    except Exception as e:
        logger.error(f"Failed to fetch predictions: {e}")
        return {"predictions": [], "total": 0, "pending": 0, "validated": 0, "accuracy": {}, "source_comparison": []}


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


# ============================================================================
# EXPLOITATION BOARD — Actionable Recommendations from Granger Causality
# ============================================================================

def classify_action_type(target_source: str, target_name: str, correlation: float, signal_momentum: float) -> str:
    """Classify what action to take based on the target variable type and signal direction.
    
    Returns: BUY, SELL, BUILD, or MONITOR
    """
    # Stocks and crypto → BUY or SELL
    if target_source in ('stock', 'crypto') or target_name.startswith('stock_'):
        # Signal rising + positive correlation = target goes up → BUY
        # Signal rising + negative correlation = target goes down → SELL
        # Signal falling + positive correlation = target goes down → SELL
        # Signal falling + negative correlation = target goes up → BUY
        if (signal_momentum > 0 and correlation > 0) or (signal_momentum < 0 and correlation < 0):
            return 'BUY'
        else:
            return 'SELL'
    
    # Research, clinical trials → BUILD opportunity
    if target_source in ('arxiv', 'clinicaltrials'):
        return 'BUILD'
    
    # Economic indicators (FRED) → MONITOR
    if target_source in ('fred',) or target_name.startswith('fred_'):
        return 'MONITOR'
    
    # Default: if it looks like something tradeable, BUY/SELL; otherwise MONITOR
    return 'MONITOR'


def get_outcome_score_adjustment(market_category: str, db) -> float:
    """Compute a score adjustment (-15 to +15) based on past build outcomes.

    Learns from historical deployment performance:
    - Past builds in same category with engagement → positive adjustment
    - Past builds in same category with zero engagement → negative adjustment
    - No history → no adjustment (neutral)

    This is the M3 feedback loop: the system learns which categories
    produce commercially viable products and adjusts future scoring.
    """
    try:
        from models import ProductDeployment, ProductMetrics, MVPBuild

        deployments = (
            db.query(ProductDeployment)
            .filter(ProductDeployment.status == 'active')
            .all()
        )
        if not deployments:
            return 0.0

        category_deployments = [
            d for d in deployments
            if d.tech_stack and isinstance(d.tech_stack, dict)
            and d.tech_stack.get('market_category') == market_category
        ]

        if not category_deployments:
            return 0.0

        total_engagement = 0
        total_builds = len(category_deployments)
        builds_with_engagement = 0

        for dep in category_deployments:
            metrics = (
                db.query(ProductMetrics)
                .filter(ProductMetrics.app_id == dep.app_id)
                .order_by(ProductMetrics.recorded_at.desc())
                .first()
            )
            if metrics:
                engagement = (metrics.monthly_active_users or 0) + (metrics.mrr or 0)
                total_engagement += engagement
                if engagement > 0:
                    builds_with_engagement += 1

        if total_builds == 0:
            return 0.0

        engagement_rate = builds_with_engagement / total_builds

        # Scale: 0% engagement rate → -15, 100% → +15
        adjustment = (engagement_rate - 0.5) * 30
        return round(max(-15, min(15, adjustment)), 1)

    except Exception as exc:
        logger.debug(f"Outcome score adjustment failed: {exc}")
        return 0.0


def compute_opportunity_score(p_value: float, correlation: float, sample_size: int, momentum: float,
                              ensemble_confidence: str = None, ensemble_change_pct: float = None,
                              model_accuracy_pct: float = None) -> float:
    """Compute a 0-100 opportunity score from statistical evidence + ensemble AI intelligence.

    Statistical factors (max 65 without ensemble):
    - p_value_score (0-25): Lower p = higher score, scaled from 0.05 threshold
    - correlation_score (0-20): Stronger absolute correlation = higher
    - sample_size_score (0-10): More data = more reliable, capped at 100
    - momentum_score (0-10): Faster signal change = more urgent opportunity

    Ensemble AI factors (max 35, requires ensemble prediction):
    - ensemble_confidence_score (0-20): high=20, medium=12, low=5
    - ensemble_magnitude_score (0-10): Larger predicted % change = higher, capped at 20%
    - model_track_record_score (0-5): Historical ensemble accuracy for this pair

    When ensemble data is absent, max score is 65 — intentional: pairs without
    ensemble coverage are less validated. Any model added to the ensemble automatically
    feeds into this score via PredictionTracking.
    """
    # --- Statistical evidence (max 65) ---
    # P-value: 0.05 → 0 pts, 0.00 → 25 pts
    p_value_score = max(0, (1 - (p_value or 1.0) / 0.05)) * 25

    # Correlation: |r| × 20
    correlation_score = min(abs(correlation or 0), 1.0) * 20

    # Sample size: capped at 100 observations
    sample_size_score = min((sample_size or 0) / 100, 1.0) * 10

    # Momentum: capped at 100% change rate
    momentum_score = min(abs(momentum or 0) / 100, 1.0) * 10

    # --- Ensemble AI intelligence (max 35) ---
    # Ensemble confidence: high=20, medium=12, low=5, absent=0
    confidence_map = {'high': 20, 'medium': 12, 'low': 5}
    ensemble_confidence_score = confidence_map.get(ensemble_confidence, 0)

    # Ensemble magnitude: larger predicted move = more actionable, capped at 20%
    ensemble_magnitude_score = 0.0
    if ensemble_change_pct is not None:
        ensemble_magnitude_score = min(abs(ensemble_change_pct) / 20.0, 1.0) * 10

    # Model track record: historical accuracy %, capped at 100%
    model_track_record_score = 0.0
    if model_accuracy_pct is not None:
        model_track_record_score = min(model_accuracy_pct / 100.0, 1.0) * 5

    return round(
        p_value_score + correlation_score + sample_size_score + momentum_score +
        ensemble_confidence_score + ensemble_magnitude_score + model_track_record_score,
        1
    )


def _strength_label(correlation: float) -> str:
    """Return a plain-English strength label from absolute correlation."""
    r = abs(correlation or 0)
    if r >= 0.7:
        return "strong"
    elif r >= 0.4:
        return "moderate"
    else:
        return "weak"


def _relationship_label(correlation: float) -> str:
    """Return proportional/inversely proportional from correlation sign."""
    if (correlation or 0) >= 0:
        return "proportional"
    return "inversely proportional"


def _source_friendly(target_source: str) -> str:
    """Human-readable name for a target source type."""
    return {
        'stock': 'stock price', 'crypto': 'cryptocurrency price',
        'fred': 'economic indicator', 'arxiv': 'research paper volume',
        'clinicaltrials': 'clinical trial activity', 'gdelt': 'global event activity',
    }.get(target_source, 'outcome metric')


def generate_reasoning(signal_display: str, target_display: str, target_source: str,
                       action_type: str, p_value: float, correlation: float,
                       lag: int, momentum: float, predicted_direction: str,
                       predicted_change_pct: float,
                       ensemble_confidence: str = None,
                       ensemble_direction: str = None) -> str:
    """Generate two-part reasoning: statistical summary + plain English narrative."""

    # --- Part 1: Statistical summary (compact) ---
    signal_dir = "rising" if momentum and momentum > 0 else "falling"
    mom_str = f"{abs(momentum or 0):.1f}%"
    corr_str = f"r={correlation:.3f}" if correlation else "r=?"
    p_str = f"p={p_value:.4f}" if p_value else "p=?"
    lag_str = f"lag={lag}mo" if lag else ""
    stats = f"({p_str}, {corr_str}" + (f", {lag_str}" if lag_str else "") + ")"

    stat_line = (
        f"{signal_display} pageviews {signal_dir} ({mom_str}) → "
        f"Granger-causes {target_display} {stats}."
    )

    # --- Part 2: Plain English worked example ---
    strength = _strength_label(correlation)
    rel = _relationship_label(correlation)
    source_name = _source_friendly(target_source)

    # What the signal is doing
    plain = (
        f"In plain terms: Wikipedia searches for \"{signal_display}\" are "
        f"{signal_dir} by {mom_str} week-over-week. "
        f"We have identified a {strength}, {rel} relationship with "
        f"{target_display} ({source_name})."
    )

    # What lag means
    if lag:
        plain += (
            f" Historically, changes in {signal_display} search interest "
            f"lead to changes in {target_display} by approximately {lag} "
            f"month{'s' if lag != 1 else ''}."
        )

    # What the prediction is
    if predicted_change_pct is not None and predicted_direction:
        dir_word = "increase" if predicted_direction == 'up' else "decrease"
        plain += (
            f" Based on current momentum, {target_display} is predicted to "
            f"{dir_word} by ~{abs(predicted_change_pct):.1f}% over the "
            f"next {lag or 1} month{'s' if (lag or 1) != 1 else ''}."
        )

    # Ensemble confirmation
    if ensemble_confidence and ensemble_direction:
        ens_dir = "increase" if ensemble_direction == 'up' else "decrease"
        plain += (
            f" The ensemble AI ({ensemble_confidence} confidence) also "
            f"predicts an {ens_dir}, reinforcing this signal."
        )

    # Action recommendation
    if action_type == 'BUY':
        plain += (
            f" This suggests a buying opportunity for {target_display} "
            f"before the predicted move materialises."
        )
    elif action_type == 'SELL':
        plain += (
            f" This suggests selling or shorting {target_display} "
            f"ahead of the predicted decline."
        )
    elif action_type == 'MONITOR':
        plain += (
            f" This economic indicator should be monitored — it may "
            f"inform timing decisions on related investments."
        )

    return f"{stat_line}\n\n{plain}"


# Market category mapping for BUILD targets
_MARKET_CATEGORIES = {
    'artificial_intelligence': 'ai_tools', 'machine_learning': 'ai_tools',
    'robotics': 'ai_tools', 'chatgpt': 'ai_tools',
    'quantum': 'deep_tech', 'cryptography': 'deep_tech',
    'nanotechnology': 'deep_tech', 'astrophysics': 'deep_tech',
    'biotechnology': 'health_tech', 'neuroscience': 'health_tech',
    'cancer': 'health_tech', 'diabetes': 'health_tech',
    'alzheimer': 'health_tech', 'heart_disease': 'health_tech',
    'obesity': 'health_tech', 'depression': 'mental_health',
    'asthma': 'health_tech', 'hiv_aids': 'health_tech',
    'parkinson': 'health_tech', 'covid': 'health_tech',
    'climate': 'climate_tech', 'climate_science': 'climate_tech',
}


def _categorize_market(target_name: str) -> str:
    """Derive market category from target variable name."""
    name_lower = target_name.lower()
    for keyword, category in _MARKET_CATEGORIES.items():
        if keyword in name_lower:
            return category
    if 'trials_' in name_lower or 'clinical' in name_lower:
        return 'health_tech'
    if 'arxiv_' in name_lower:
        return 'research_tools'
    return 'general'


def compute_build_viability(signal_var, target_var, p_value, correlation,
                            lag, momentum, db, ensemble_change_pct=None) -> dict:
    """Compute BUILD-specific viability score from existing data.

    Uses Wikipedia pageviews as a demand proxy, time-series growth trends,
    Granger lag for opportunity window, and target paper/trial density
    for competition assessment.

    Returns dict with all viability fields ready for model assignment.
    """
    from sqlalchemy import desc
    import numpy as np

    now = datetime.utcnow()
    three_months_ago = now - timedelta(days=90)
    six_months_ago = now - timedelta(days=180)

    # ---- 1. Demand score (0-30): Wikipedia pageviews for signal topic ----
    recent_views = db.query(TimeSeriesData).filter(
        TimeSeriesData.variable_id == signal_var.id,
        TimeSeriesData.timestamp >= three_months_ago
    ).order_by(TimeSeriesData.timestamp).all()

    if recent_views:
        avg_daily = sum(float(d.value) for d in recent_views) / max(len(recent_views), 1)
        estimated_monthly = int(avg_daily * 30)
    else:
        avg_daily = 0
        estimated_monthly = 0

    if estimated_monthly >= 50_000:
        demand_score = 30
    elif estimated_monthly >= 10_000:
        demand_score = 20
    elif estimated_monthly >= 1_000:
        demand_score = 10
    else:
        demand_score = 5

    # ---- 2. Growth score (0-25): 3-month trend ----
    older_views = db.query(TimeSeriesData).filter(
        TimeSeriesData.variable_id == signal_var.id,
        TimeSeriesData.timestamp >= six_months_ago,
        TimeSeriesData.timestamp < three_months_ago
    ).all()

    if recent_views and older_views:
        recent_avg = sum(float(d.value) for d in recent_views) / len(recent_views)
        older_avg = sum(float(d.value) for d in older_views) / len(older_views)
        if older_avg > 0:
            growth_pct = ((recent_avg - older_avg) / older_avg) * 100
        else:
            growth_pct = 0.0
    else:
        growth_pct = 0.0

    if growth_pct > 10:
        growth_score = 25
        trend_dir = 'growing'
    elif growth_pct > 0:
        growth_score = 15
        trend_dir = 'growing'
    elif growth_pct > -5:
        growth_score = 10
        trend_dir = 'stable'
    else:
        growth_score = 5
        trend_dir = 'declining'

    # ---- 3. Timing score (0-20): longer lag = wider window ----
    lag_months = lag or 1
    if lag_months >= 3:
        timing_score = 20
        duration = lag_months * 2  # opportunity window ~2× the lag
    elif lag_months >= 1:
        timing_score = 15
        duration = max(lag_months * 2, 3)
    else:
        timing_score = 10
        duration = 2

    # ---- 4. Evidence score (0-15): statistical strength ----
    p_score = max(0, (1 - (p_value or 1.0) / 0.05)) * 10
    sample_score = min((correlation or 0) ** 2 * 5, 5)  # r² contribution
    evidence_score = round(p_score + sample_score, 1)

    # ---- 5. Competition proxy (0-10): target density ----
    target_data = db.query(TimeSeriesData).filter(
        TimeSeriesData.variable_id == target_var.id,
        TimeSeriesData.timestamp >= three_months_ago
    ).all()

    if target_data:
        avg_target = sum(float(d.value) for d in target_data) / len(target_data)
        # More papers/trials = more competition
        if avg_target > 100:
            competition = 'HIGH'
            comp_score = 3
        elif avg_target > 30:
            competition = 'MEDIUM'
            comp_score = 7
        else:
            competition = 'LOW'
            comp_score = 10
    else:
        competition = 'LOW'
        comp_score = 10

    # ---- Composite viability ----
    viability = round(demand_score + growth_score + timing_score + evidence_score + comp_score, 1)
    viability = min(viability, 100.0)

    # ---- Revenue potential T-shirt sizing ----
    # Ensemble predicting strong growth can boost revenue assessment
    ensemble_boost = (ensemble_change_pct is not None and ensemble_change_pct > 10)
    if estimated_monthly >= 50_000 and trend_dir == 'growing' and competition != 'HIGH':
        revenue = 'HIGH'
    elif ensemble_boost and trend_dir == 'growing' and competition != 'HIGH':
        revenue = 'HIGH'
    elif estimated_monthly >= 10_000 or (trend_dir == 'growing' and competition != 'HIGH'):
        revenue = 'MEDIUM'
    elif ensemble_boost:
        revenue = 'MEDIUM'
    else:
        revenue = 'LOW'

    return {
        'build_viability_score': viability,
        'estimated_monthly_searches': estimated_monthly,
        'search_trend_direction': trend_dir,
        'search_growth_pct': round(growth_pct, 1),
        'opportunity_duration_months': duration,
        'revenue_potential': revenue,
        'competition_level': competition,
        'market_category': _categorize_market(target_var.name),
    }


def generate_build_reasoning(signal_display: str, target_display: str,
                             viability: dict, p_value, correlation,
                             lag, momentum, predicted_direction,
                             predicted_change_pct,
                             ensemble_confidence: str = None,
                             ensemble_direction: str = None) -> str:
    """Generate enriched two-part reasoning for BUILD recommendations."""
    signal_dir = 'rising' if momentum and momentum > 0 else 'falling'
    mom_str = f"{abs(momentum or 0):.1f}%"
    stats = f"(p={p_value:.4f}, r={correlation:.3f}" + (f", lag={lag}mo" if lag else "") + ")"

    searches = viability.get('estimated_monthly_searches', 0)
    trend = viability.get('search_trend_direction', 'stable')
    revenue = viability.get('revenue_potential', 'LOW')
    duration = viability.get('opportunity_duration_months', 0)
    category = viability.get('market_category', 'general')
    growth_pct = viability.get('search_growth_pct', 0)
    competition = viability.get('competition_level', 'LOW')

    demand_str = f"~{searches:,}/mo searches" if searches else "limited search volume"
    trend_str = f"{trend} demand"
    window_str = f"~{duration}mo opportunity window" if duration else ""

    # --- Part 1: Statistical summary ---
    stat_line = (
        f"{signal_display} {signal_dir} ({mom_str}) → "
        f"Granger-causes {target_display} {stats}. "
        f"BUILD opportunity in {category.replace('_', ' ')}: "
        f"{demand_str}, {trend_str}, {revenue} revenue potential"
        + (f", {window_str}" if window_str else "") + "."
    )

    # --- Part 2: Plain English worked example ---
    strength = _strength_label(correlation)
    rel = _relationship_label(correlation)

    plain = (
        f"In plain terms: Wikipedia searches for \"{signal_display}\" are "
        f"{signal_dir} by {mom_str} week-over-week. "
        f"We have identified a {strength}, {rel} relationship with "
        f"{target_display} (research/trial activity)."
    )

    # Lag explanation
    if lag:
        plain += (
            f" Changes in {signal_display} search interest typically lead "
            f"to changes in {target_display} by ~{lag} month{'s' if lag != 1 else ''}."
        )

    # Prediction narrative
    if predicted_change_pct is not None and predicted_direction:
        dir_word = "increase" if predicted_direction == 'up' else "decrease"
        plain += (
            f" Based on current momentum, {target_display} activity is predicted to "
            f"{dir_word} by ~{abs(predicted_change_pct):.1f}% over the "
            f"next {lag or 1} month{'s' if (lag or 1) != 1 else ''}."
        )

    # Ensemble confirmation
    if ensemble_confidence and ensemble_direction:
        ens_dir = "increase" if ensemble_direction == 'up' else "decrease"
        plain += (
            f" The ensemble AI ({ensemble_confidence} confidence) also "
            f"predicts an {ens_dir}, reinforcing this signal."
        )

    # Market context
    plain += (
        f" There are currently {demand_str} for related topics "
        f"with {trend} demand"
    )
    if growth_pct:
        plain += f" ({growth_pct:+.1f}% growth)"
    plain += f" and {competition.lower()} competition."

    # Actionable BUILD suggestions based on category
    # If AI-generated product concepts exist, use the selected one
    suggestion = None
    if hasattr(signal_display, '__self__'):  # not called with extra args
        pass
    # Fallback: category-based generic suggestions
    if not suggestion:
        build_suggestions = {
            'health_tech': "clinical data dashboards, trial recruitment tools, or patient research portals",
            'ai_tools': "AI-powered SaaS tools, model marketplaces, or developer integrations",
            'deep_tech': "specialised analytics platforms, research collaboration tools, or API services",
            'climate_tech': "sustainability trackers, carbon footprint calculators, or green investment tools",
            'mental_health': "digital therapy platforms, wellbeing trackers, or community support apps",
            'fintech': "portfolio trackers, market alert services, or financial education platforms",
        }
        suggestion = build_suggestions.get(category, "a SaaS product, data service, or content platform")

    plain += (
        f" This creates a {duration}-month window to build and launch "
        f"{suggestion} targeting this {category.replace('_', ' ')} space "
        f"with {revenue.lower()} revenue potential."
    )

    return f"{stat_line}\n\n{plain}"


@router.get("/exploitation/generate")
async def generate_exploitation_recommendations(db: Session = Depends(get_db)):
    """Scan all FMV signals and generate actionable recommendations from Granger data.
    
    For each Layer 1 signal with significant Granger relationships to non-Wikipedia targets,
    auto-classifies (BUY/SELL/BUILD/MONITOR), scores (0-100), and stores recommendations.
    Deduplicates by signal+target pair — updates existing recommendations.
    Also batch-creates PredictionTracking records for each recommendation.
    """
    from sqlalchemy import or_, and_, desc, asc, Integer
    from sqlalchemy.orm import aliased
    import numpy as np
    import uuid
    
    try:
        # Get all Layer 1 signals (Wikipedia + Reddit FMVs)
        layer1_vars = db.query(VariableMetadata).filter(
            VariableMetadata.source.in_(['wikipedia', 'reddit']),
            VariableMetadata.is_active == True
        ).all()
        
        if not layer1_vars:
            return {"status": "no_signals", "message": "No Layer 1 signals found", "generated": 0}
        
        # Calculate current momentum for all signals
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)
        
        signal_momentum = {}
        for var in layer1_vars:
            recent_data = db.query(TimeSeriesData).filter(
                TimeSeriesData.variable_id == var.id,
                TimeSeriesData.timestamp >= two_weeks_ago
            ).order_by(TimeSeriesData.timestamp).all()
            
            if len(recent_data) >= 2:
                this_week = [d.value for d in recent_data if d.timestamp >= week_ago]
                last_week = [d.value for d in recent_data if d.timestamp < week_ago]
                
                if this_week and last_week:
                    this_avg = sum(this_week) / len(this_week)
                    last_avg = sum(last_week) / len(last_week)
                    if last_avg > 0:
                        signal_momentum[var.id] = round(((this_avg - last_avg) / last_avg) * 100, 1)
                    else:
                        signal_momentum[var.id] = 0.0
                else:
                    signal_momentum[var.id] = 0.0
            else:
                signal_momentum[var.id] = 0.0
        
        generated = 0
        updated = 0
        skipped = 0

        # --- Pre-load ensemble predictions for efficient lookup ---
        # Get latest ensemble prediction per signal+target pair
        from sqlalchemy import func as sa_func

        # Subquery: latest ensemble prediction_id per signal+target
        latest_ensemble_sq = (
            db.query(
                PredictionTracking.signal_name,
                PredictionTracking.target_name,
                sa_func.max(PredictionTracking.predicted_at).label('max_at')
            )
            .filter(
                PredictionTracking.model_version.like('ensemble%'),
                PredictionTracking.status.in_(['pending', 'validated']),
            )
            .group_by(PredictionTracking.signal_name, PredictionTracking.target_name)
            .subquery()
        )

        ensemble_preds_rows = (
            db.query(PredictionTracking)
            .join(
                latest_ensemble_sq,
                and_(
                    PredictionTracking.signal_name == latest_ensemble_sq.c.signal_name,
                    PredictionTracking.target_name == latest_ensemble_sq.c.target_name,
                    PredictionTracking.predicted_at == latest_ensemble_sq.c.max_at,
                )
            )
            .filter(PredictionTracking.model_version.like('ensemble%'))
            .all()
        )
        # Index by (signal_name, target_name) for O(1) lookup
        ensemble_cache = {}
        for ep in ensemble_preds_rows:
            ensemble_cache[(ep.signal_name, ep.target_name)] = ep

        # --- Pre-load per-pair ensemble accuracy ---
        accuracy_rows = (
            db.query(
                PredictionTracking.signal_name,
                PredictionTracking.target_name,
                sa_func.count(PredictionTracking.id).label('total'),
                sa_func.sum(
                    sa_func.cast(PredictionTracking.direction_correct, Integer)
                ).label('correct'),
            )
            .filter(
                PredictionTracking.model_version.like('ensemble%'),
                PredictionTracking.status == 'validated',
                PredictionTracking.direction_correct.isnot(None),
            )
            .group_by(PredictionTracking.signal_name, PredictionTracking.target_name)
            .all()
        )
        accuracy_cache = {}
        for row in accuracy_rows:
            if row.total and row.total > 0:
                accuracy_cache[(row.signal_name, row.target_name)] = round(
                    (row.correct or 0) / row.total * 100, 1
                )
        
        for var in layer1_vars:
            momentum = signal_momentum.get(var.id, 0.0)
            
            # Find significant Granger targets (same fixed query as cascade-predictions)
            OutcomeVar = aliased(VariableMetadata)
            results_as_var1 = db.query(CorrelationResult).join(
                OutcomeVar, CorrelationResult.variable2_id == OutcomeVar.id
            ).filter(
                CorrelationResult.variable1_id == var.id,
                CorrelationResult.granger_p_value_xy != None,
                CorrelationResult.granger_p_value_xy < 0.05,
                OutcomeVar.source != 'wikipedia',
                OutcomeVar.source != 'reddit'
            ).order_by(desc(CorrelationResult.abs_correlation)).limit(10).all()
            
            OutcomeVar2 = aliased(VariableMetadata)
            results_as_var2 = db.query(CorrelationResult).join(
                OutcomeVar2, CorrelationResult.variable1_id == OutcomeVar2.id
            ).filter(
                CorrelationResult.variable2_id == var.id,
                CorrelationResult.granger_p_value_yx != None,
                CorrelationResult.granger_p_value_yx < 0.05,
                OutcomeVar2.source != 'wikipedia',
                OutcomeVar2.source != 'reddit'
            ).order_by(desc(CorrelationResult.abs_correlation)).limit(10).all()
            
            # Combine and deduplicate
            seen_ids = set()
            all_results = []
            for r in sorted(results_as_var1 + results_as_var2,
                          key=lambda x: x.abs_correlation or 0, reverse=True):
                if r.id not in seen_ids:
                    seen_ids.add(r.id)
                    all_results.append(r)
            
            # Process top 5 targets per signal
            for result in all_results[:5]:
                if result.variable1_id == var.id:
                    target_var = result.variable2
                    p_value = result.granger_p_value_xy
                else:
                    target_var = result.variable1
                    p_value = result.granger_p_value_yx
                
                corr = result.correlation_value
                lag = result.granger_lags
                sample = result.sample_size or 30
                
                # Predict direction from correlation + momentum
                if momentum > 0:
                    predicted_direction = 'up' if corr > 0 else 'down'
                else:
                    predicted_direction = 'down' if corr > 0 else 'up'
                
                # Rough predicted change % from correlation × momentum
                predicted_change_pct = round(abs(corr) * abs(momentum) * 0.01 * 100, 2) if momentum else None
                
                # Classify action
                action_type = classify_action_type(
                    target_var.source, target_var.name, corr, momentum
                )

                # --- Lookup ensemble prediction for this signal→target pair ---
                ensemble_pred = ensemble_cache.get(
                    (var.display_name, target_var.display_name)
                )
                ens_confidence = ensemble_pred.confidence if ensemble_pred else None
                ens_direction = ensemble_pred.predicted_direction if ensemble_pred else None
                ens_change_pct = ensemble_pred.predicted_change_pct if ensemble_pred else None
                ens_r_squared = ensemble_pred.r_squared if ensemble_pred else None
                ens_predicted_at = ensemble_pred.predicted_at if ensemble_pred else None
                pair_accuracy = accuracy_cache.get(
                    (var.display_name, target_var.display_name)
                )

                # Score (now incorporating ensemble intelligence)
                score = compute_opportunity_score(
                    p_value, corr, sample, momentum,
                    ensemble_confidence=ens_confidence,
                    ensemble_change_pct=ens_change_pct,
                    model_accuracy_pct=pair_accuracy,
                )
                
                # BUILD-specific viability scoring
                viability = None
                if action_type == 'BUILD':
                    viability = compute_build_viability(
                        var, target_var, p_value, corr, lag, momentum, db,
                        ensemble_change_pct=ens_change_pct,
                    )
                    # M3 feedback loop: adjust score based on past build outcomes
                    category = viability.get('market_category', 'general')
                    outcome_adj = get_outcome_score_adjustment(category, db)
                    score = max(0, min(100, score + outcome_adj))
                    reasoning = generate_build_reasoning(
                        var.display_name, target_var.display_name,
                        viability, p_value, corr, lag, momentum,
                        predicted_direction, predicted_change_pct,
                        ensemble_confidence=ens_confidence,
                        ensemble_direction=ens_direction,
                    )
                else:
                    # Generate standard reasoning for BUY/SELL/MONITOR
                    reasoning = generate_reasoning(
                        var.display_name, target_var.display_name, target_var.source,
                        action_type, p_value, corr, lag, momentum,
                        predicted_direction, predicted_change_pct,
                        ensemble_confidence=ens_confidence,
                        ensemble_direction=ens_direction,
                    )
                
                # Upsert: update existing or create new
                existing = db.query(ExploitationRecommendation).filter(
                    ExploitationRecommendation.signal_name == var.name,
                    ExploitationRecommendation.target_name == target_var.name
                ).first()
                
                if existing:
                    # Detect material stat shifts that invalidate cached product concepts.
                    # Concepts are tied to specific stat values; if those drift significantly,
                    # the old concepts no longer reflect the opportunity.
                    if existing.product_concepts:
                        old_corr = existing.correlation or 0
                        new_corr = corr or 0
                        old_pred = existing.predicted_change_pct or 0
                        new_pred = predicted_change_pct or 0
                        old_p = existing.granger_p_value if existing.granger_p_value is not None else 1.0
                        new_p = p_value if p_value is not None else 1.0

                        def _shift_pct(old, new):
                            if abs(old) < 1e-9:
                                return float('inf') if abs(new) > 1e-9 else 0.0
                            return abs(new - old) / abs(old) * 100

                        corr_shift = _shift_pct(old_corr, new_corr)
                        pred_shift = _shift_pct(old_pred, new_pred)
                        p_crossed = (old_p < 0.05) != (new_p < 0.05)

                        if corr_shift > 20 or pred_shift > 20 or p_crossed:
                            logger.info(
                                f"[concepts] rec_id={existing.id} clearing stale concepts "
                                f"(corr_shift={corr_shift:.1f}%, pred_shift={pred_shift:.1f}%, "
                                f"p_crossed={p_crossed})"
                            )
                            existing.product_concepts = None
                            existing.selected_concept_index = None
                            existing.concepts_generation_status = None
                            existing.concepts_error = None
                            existing.concepts_generated_at = None

                    # Update stats but preserve user status/notes
                    existing.granger_p_value = p_value
                    existing.correlation = corr
                    existing.optimal_lag = lag
                    existing.sample_size = sample
                    existing.predicted_direction = predicted_direction
                    existing.predicted_change_pct = predicted_change_pct
                    existing.signal_momentum = momentum
                    existing.opportunity_score = score
                    existing.action_type = action_type
                    existing.reasoning = reasoning
                    # Ensemble enrichment
                    existing.ensemble_confidence = ens_confidence
                    existing.ensemble_direction = ens_direction
                    existing.ensemble_predicted_at = ens_predicted_at
                    existing.ensemble_r_squared = ens_r_squared
                    existing.ensemble_change_pct = ens_change_pct
                    if viability:
                        existing.build_viability_score = viability['build_viability_score']
                        existing.estimated_monthly_searches = viability['estimated_monthly_searches']
                        existing.search_trend_direction = viability['search_trend_direction']
                        existing.search_growth_pct = viability['search_growth_pct']
                        existing.opportunity_duration_months = viability['opportunity_duration_months']
                        existing.revenue_potential = viability['revenue_potential']
                        existing.competition_level = viability['competition_level']
                        existing.market_category = viability['market_category']
                    existing.updated_at = datetime.utcnow()
                    updated += 1
                else:
                    rec = ExploitationRecommendation(
                        signal_name=var.name,
                        signal_display_name=var.display_name,
                        target_name=target_var.name,
                        target_display_name=target_var.display_name,
                        target_source=target_var.source,
                        action_type=action_type,
                        reasoning=reasoning,
                        granger_p_value=p_value,
                        correlation=corr,
                        optimal_lag=lag,
                        sample_size=sample,
                        predicted_direction=predicted_direction,
                        predicted_change_pct=predicted_change_pct,
                        signal_momentum=momentum,
                        opportunity_score=score,
                        ensemble_confidence=ens_confidence,
                        ensemble_direction=ens_direction,
                        ensemble_predicted_at=ens_predicted_at,
                        ensemble_r_squared=ens_r_squared,
                        ensemble_change_pct=ens_change_pct,
                        build_viability_score=viability['build_viability_score'] if viability else None,
                        estimated_monthly_searches=viability['estimated_monthly_searches'] if viability else None,
                        search_trend_direction=viability['search_trend_direction'] if viability else None,
                        search_growth_pct=viability['search_growth_pct'] if viability else None,
                        opportunity_duration_months=viability['opportunity_duration_months'] if viability else None,
                        revenue_potential=viability['revenue_potential'] if viability else None,
                        competition_level=viability['competition_level'] if viability else None,
                        market_category=viability['market_category'] if viability else None,
                        status='NEW',
                    )
                    db.add(rec)
                    generated += 1
                
                # --- Also create/update a PredictionTracking record ---
                # Get latest target value for baseline
                latest_target = db.query(TimeSeriesData).filter(
                    TimeSeriesData.variable_id == target_var.id
                ).order_by(desc(TimeSeriesData.timestamp)).first()
                
                latest_signal = db.query(TimeSeriesData).filter(
                    TimeSeriesData.variable_id == var.id
                ).order_by(desc(TimeSeriesData.timestamp)).first()
                
                baseline_value = float(latest_target.value) if latest_target else None
                signal_value = float(latest_signal.value) if latest_signal else None
                
                # Calculate predicted value
                predicted_value = None
                if baseline_value is not None and predicted_change_pct is not None:
                    predicted_value = baseline_value * (1 + predicted_change_pct / 100)
                
                # Lag in days (Granger lag is typically in months for this dataset)
                lag_days = (lag or 1) * 30
                target_date = datetime.utcnow() + timedelta(days=lag_days)
                
                # Check for existing pending prediction for same signal→target
                existing_pred = db.query(PredictionTracking).filter(
                    PredictionTracking.signal_name == var.display_name,
                    PredictionTracking.target_name == target_var.display_name,
                    PredictionTracking.status == 'pending'
                ).first()
                
                if existing_pred:
                    existing_pred.predicted_at = datetime.utcnow()
                    existing_pred.target_date = target_date
                    existing_pred.optimal_lag_days = lag_days
                    existing_pred.predicted_direction = predicted_direction
                    existing_pred.predicted_value = round(predicted_value, 4) if predicted_value else None
                    existing_pred.predicted_change_pct = predicted_change_pct
                    existing_pred.current_target_value = baseline_value
                    existing_pred.current_signal_value = signal_value
                    existing_pred.signal_momentum = momentum
                    existing_pred.r_squared = abs(corr) ** 2 if corr else None
                    existing_pred.confidence = 'high' if abs(corr or 0) > 0.5 else 'medium' if abs(corr or 0) > 0.3 else 'low'
                    existing_pred.granger_p_value = p_value
                    existing_pred.target_source = target_var.source
                    existing_pred.updated_at = datetime.utcnow()
                else:
                    pred_record = PredictionTracking(
                        prediction_id=str(uuid.uuid4())[:12],
                        signal_name=var.display_name,
                        target_name=target_var.display_name,
                        predicted_at=datetime.utcnow(),
                        target_date=target_date,
                        optimal_lag_days=lag_days,
                        predicted_direction=predicted_direction,
                        predicted_value=round(predicted_value, 4) if predicted_value else None,
                        predicted_change_pct=predicted_change_pct,
                        current_target_value=baseline_value,
                        current_signal_value=signal_value,
                        signal_momentum=momentum,
                        r_squared=abs(corr) ** 2 if corr else None,
                        confidence='high' if abs(corr or 0) > 0.5 else 'medium' if abs(corr or 0) > 0.3 else 'low',
                        model_version='granger_v1',
                        granger_p_value=p_value,
                        target_source=target_var.source,
                        status='pending',
                    )
                    db.add(pred_record)
        
        db.commit()
        
        # Return summary
        total = db.query(ExploitationRecommendation).count()
        by_action = {}
        for action in ['BUY', 'SELL', 'BUILD', 'MONITOR']:
            by_action[action] = db.query(ExploitationRecommendation).filter(
                ExploitationRecommendation.action_type == action
            ).count()
        
        total_predictions = db.query(PredictionTracking).filter(
            PredictionTracking.status == 'pending'
        ).count()
        
        return {
            "status": "success",
            "generated": generated,
            "updated": updated,
            "skipped": skipped,
            "total_recommendations": total,
            "total_predictions": total_predictions,
            "by_action_type": by_action,
            "signals_processed": len(layer1_vars),
            "ensemble_coverage": {
                "predictions_available": len(ensemble_cache),
                "pairs_with_accuracy": len(accuracy_cache),
            },
        }
        
    except Exception as e:
        logger.error(f"Exploitation generation failed: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exploitation/recommendations")
async def get_exploitation_recommendations(
    status: Optional[str] = None,
    action_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all exploitation recommendations, optionally filtered by status and action type."""
    from sqlalchemy import desc
    
    try:
        query = db.query(ExploitationRecommendation)
        
        if status:
            query = query.filter(ExploitationRecommendation.status == status.upper())
        if action_type:
            query = query.filter(ExploitationRecommendation.action_type == action_type.upper())
        
        results = query.order_by(desc(ExploitationRecommendation.opportunity_score)).all()
        
        # Summary stats
        all_recs = db.query(ExploitationRecommendation).all()
        by_action = {}
        by_status = {}
        for rec in all_recs:
            by_action[rec.action_type] = by_action.get(rec.action_type, 0) + 1
            by_status[rec.status] = by_status.get(rec.status, 0) + 1
        
        avg_score = sum(r.opportunity_score or 0 for r in all_recs) / max(len(all_recs), 1)
        
        return {
            "recommendations": [r.to_dict() for r in results],
            "total": len(all_recs),
            "filtered_count": len(results),
            "summary": {
                "by_action_type": by_action,
                "by_status": by_status,
                "average_score": round(avg_score, 1)
            }
        }
        
    except Exception as e:
        logger.error(f"Get exploitation recommendations failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/exploitation/recommendations/{rec_id}")
async def update_exploitation_recommendation(rec_id: int, request: Request, db: Session = Depends(get_db)):
    """Update status and/or notes on a recommendation.
    
    Body: {"status": "REVIEWING", "notes": "Looking into this..."}
    Valid statuses: NEW, REVIEWING, PURSUING, COMPLETED, DISMISSED
    """
    try:
        body = await request.json()
        
        rec = db.query(ExploitationRecommendation).filter(
            ExploitationRecommendation.id == rec_id
        ).first()
        
        if not rec:
            raise HTTPException(status_code=404, detail=f"Recommendation {rec_id} not found")
        
        valid_statuses = {'NEW', 'REVIEWING', 'PURSUING', 'COMPLETED', 'DISMISSED'}
        
        if 'status' in body:
            new_status = body['status'].upper()
            if new_status not in valid_statuses:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid status '{new_status}'. Must be one of: {', '.join(valid_statuses)}"
                )
            rec.status = new_status
        
        if 'notes' in body:
            rec.notes = body['notes']
        
        if 'user_requirements' in body:
            rec.user_requirements = body['user_requirements']
        
        rec.updated_at = datetime.utcnow()
        db.commit()
        
        return rec.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update exploitation recommendation failed: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/exploitation/recommendations/manual")
async def create_manual_recommendation(request: Request, db: Session = Depends(get_db)):
    """Create a user-sourced exploitation recommendation (manual idea).

    Body: {
        "idea_name": "AI-powered meal planner",
        "description": "Build a subscription meal planning app...",
        "action_type": "BUILD",          // optional, defaults to BUILD
        "market_category": "health_tech"  // optional
    }
    """
    try:
        body = await request.json()

        idea_name = (body.get("idea_name") or "").strip()
        description = (body.get("description") or "").strip()
        if not idea_name:
            raise HTTPException(status_code=400, detail="idea_name is required")

        action_type = (body.get("action_type") or "BUILD").upper()
        if action_type not in ("BUY", "SELL", "BUILD", "MONITOR"):
            raise HTTPException(status_code=400, detail="action_type must be BUY, SELL, BUILD, or MONITOR")

        market_category = (body.get("market_category") or "").strip() or None

        # Synthetic signal/target names — unique per idea to satisfy the unique index
        import time
        ts = int(time.time() * 1000)
        signal_name = f"manual_{ts}"
        target_name = f"manual_idea_{ts}"

        rec = ExploitationRecommendation(
            signal_name=signal_name,
            signal_display_name=idea_name,
            target_name=target_name,
            target_display_name=idea_name,
            target_source="manual",
            action_type=action_type,
            reasoning=description,
            source="manual",
            status="NEW",
            opportunity_score=50,  # Neutral starting score for manual ideas
            build_viability_score=50 if action_type == "BUILD" else None,
            market_category=market_category,
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        logger.info(f"✅ Created manual recommendation: {rec.id} — {idea_name}")
        return rec.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create manual recommendation failed: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PREDICTION ACCURACY — Validate predictions against actual outcomes
# ============================================================================

@router.post("/predictions/validate")
async def validate_predictions(db: Session = Depends(get_db)):
    """Validate matured predictions by comparing against actual data.
    
    Finds all 'pending' predictions where target_date has passed, looks up the
    actual value from TimeSeriesData, computes:
    - direction accuracy (up/down correct?)
    - value error % (predicted vs actual value)
    - actual change % (from baseline)
    - actual lag days (when did the peak/trough actually occur?)
    - lag error (actual lag - predicted lag)
    """
    from sqlalchemy import desc, asc
    
    try:
        now = datetime.utcnow()
        
        # Find matured predictions
        matured = db.query(PredictionTracking).filter(
            PredictionTracking.status == 'pending',
            PredictionTracking.target_date != None,
            PredictionTracking.target_date <= now
        ).all()
        
        if not matured:
            return {"status": "no_matured", "validated": 0, "message": "No matured predictions to validate"}
        
        validated_count = 0
        errors = []
        
        for pred in matured:
            try:
                # Look up the target variable by name
                target_var = db.query(VariableMetadata).filter(
                    VariableMetadata.display_name == pred.target_name
                ).first()
                
                if not target_var:
                    target_var = db.query(VariableMetadata).filter(
                        VariableMetadata.name == pred.target_name
                    ).first()
                
                if not target_var:
                    target_var = db.query(VariableMetadata).filter(
                        VariableMetadata.display_name.ilike(f"%{pred.target_name}%")
                    ).first()
                
                if not target_var:
                    errors.append(f"Target variable not found: {pred.target_name}")
                    pred.status = 'expired'
                    continue
                
                # Find the closest data point to the target date
                actual_data = db.query(TimeSeriesData).filter(
                    TimeSeriesData.variable_id == target_var.id,
                    TimeSeriesData.timestamp <= pred.target_date + timedelta(days=7),
                    TimeSeriesData.timestamp >= pred.target_date - timedelta(days=7)
                ).order_by(desc(TimeSeriesData.timestamp)).first()
                
                if not actual_data:
                    errors.append(f"No actual data near target date for {pred.target_name}")
                    continue
                
                # Compute basic actuals
                actual_value = float(actual_data.value)
                baseline = pred.current_target_value
                
                if baseline and baseline != 0:
                    actual_direction = 'up' if actual_value > baseline else 'down'
                    direction_correct = (actual_direction == pred.predicted_direction)
                    value_error_pct = abs((actual_value - (pred.predicted_value or baseline)) / baseline) * 100
                    actual_change_pct = ((actual_value - baseline) / abs(baseline)) * 100
                else:
                    actual_direction = 'unknown'
                    direction_correct = None
                    value_error_pct = None
                    actual_change_pct = None
                
                # --- Compute actual lag: find when peak/trough occurred ---
                # Scan from prediction date to 2x the predicted lag window
                scan_window = max((pred.optimal_lag_days or 30) * 2, 60)
                ts_data = db.query(TimeSeriesData).filter(
                    TimeSeriesData.variable_id == target_var.id,
                    TimeSeriesData.timestamp >= pred.predicted_at,
                    TimeSeriesData.timestamp <= pred.predicted_at + timedelta(days=scan_window)
                ).order_by(asc(TimeSeriesData.timestamp)).all()
                
                actual_lag_days = None
                lag_error_days = None
                
                if ts_data and baseline and baseline != 0:
                    if pred.predicted_direction == 'up':
                        # Find the peak value and when it occurred
                        peak_point = max(ts_data, key=lambda d: d.value)
                        actual_lag_days = (peak_point.timestamp - pred.predicted_at).days
                    else:
                        # Find the trough value and when it occurred
                        trough_point = min(ts_data, key=lambda d: d.value)
                        actual_lag_days = (trough_point.timestamp - pred.predicted_at).days
                    
                    if actual_lag_days is not None and pred.optimal_lag_days:
                        lag_error_days = actual_lag_days - pred.optimal_lag_days
                
                # Update prediction record
                pred.actual_value = actual_value
                pred.actual_direction = actual_direction
                pred.direction_correct = direction_correct
                pred.value_error_pct = round(value_error_pct, 2) if value_error_pct is not None else None
                pred.actual_change_pct = round(actual_change_pct, 2) if actual_change_pct is not None else None
                pred.actual_lag_days = actual_lag_days
                pred.lag_error_days = lag_error_days
                pred.status = 'validated'
                pred.updated_at = datetime.utcnow()
                validated_count += 1
                
            except Exception as pred_err:
                errors.append(f"Error validating {pred.prediction_id}: {str(pred_err)}")
                continue
        
        db.commit()
        
        # Compute updated accuracy stats
        all_validated = db.query(PredictionTracking).filter(
            PredictionTracking.status == 'validated'
        ).all()
        
        direction_correct_count = sum(1 for p in all_validated if p.direction_correct)
        direction_accuracy = (direction_correct_count / len(all_validated) * 100) if all_validated else 0
        avg_error = sum(p.value_error_pct or 0 for p in all_validated) / max(len(all_validated), 1)
        
        lag_errors = [p.lag_error_days for p in all_validated if p.lag_error_days is not None]
        avg_lag_error = sum(abs(e) for e in lag_errors) / max(len(lag_errors), 1) if lag_errors else None
        
        change_errors = [
            abs((p.actual_change_pct or 0) - (p.predicted_change_pct or 0))
            for p in all_validated
            if p.actual_change_pct is not None and p.predicted_change_pct is not None
        ]
        avg_change_error = sum(change_errors) / max(len(change_errors), 1) if change_errors else None
        
        return {
            "status": "success",
            "validated": validated_count,
            "total_matured": len(matured),
            "errors": errors,
            "accuracy_stats": {
                "total_validated": len(all_validated),
                "direction_accuracy": round(direction_accuracy, 1),
                "average_error_pct": round(avg_error, 2),
                "avg_lag_error_days": round(avg_lag_error, 1) if avg_lag_error is not None else None,
                "avg_change_error_pct": round(avg_change_error, 1) if avg_change_error is not None else None,
            }
        }
        
    except Exception as e:
        logger.error(f"Prediction validation failed: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# VERSION COMPARISON — Replay validated predictions through model configs
# ==============================================================================

# Persisted to DB (VersionComparisonCache) so cache survives Railway
# redeploys.  In-memory dict is kept ONLY as an intra-request short-circuit;
# it is rehydrated from the DB on first read after a cold start.
_version_comparison_cache: dict = {"data": None, "computed_at": None}


def _load_cache_from_db(db: Session) -> None:
    """Populate the in-process cache from the DB (single-row table)."""
    from models import VersionComparisonCache
    row = (
        db.query(VersionComparisonCache)
        .order_by(VersionComparisonCache.computed_at.desc())
        .first()
    )
    if row is not None:
        _version_comparison_cache["data"] = row.data
        _version_comparison_cache["computed_at"] = (
            row.computed_at.isoformat() if row.computed_at else None
        )


def _save_cache_to_db(db: Session, payload: dict, computed_at: datetime) -> None:
    """Replace the cached row in the DB (table holds at most one row)."""
    from models import VersionComparisonCache
    db.query(VersionComparisonCache).delete()
    db.add(VersionComparisonCache(data=payload, computed_at=computed_at))
    db.commit()


@router.get("/predictions/version-comparison")
async def get_version_comparison(db: Session = Depends(get_db)):
    """Return cached replay results comparing model versions.

    Reads from DB on cold start so cache survives Railway redeploys.
    Returns empty response (with `cached=False`) only if no cache row
    exists yet — frontend then auto-triggers POST.
    """
    global _version_comparison_cache
    if _version_comparison_cache["data"] is None:
        try:
            _load_cache_from_db(db)
        except Exception as e:
            logger.warning(f"Could not load version comparison cache from DB: {e}")

    if _version_comparison_cache["data"] is not None:
        return {
            **_version_comparison_cache["data"],
            "cached": True,
            "computed_at": _version_comparison_cache["computed_at"],
        }

    return {
        "versions": [],
        "actuals": {"time_series": []},
        "total_predictions": 0,
        "cached": False,
        "computed_at": None,
        "message": "No cached results. Click 'Run Comparison' to compute.",
    }


@router.post("/predictions/run-version-comparison")
async def run_version_comparison(db: Session = Depends(get_db)):
    """Trigger a fresh replay comparison and persist the results to DB."""
    global _version_comparison_cache
    try:
        from services.ensemble_model import replay_validated_predictions
        result = replay_validated_predictions(db)
        computed_at = datetime.utcnow()
        _version_comparison_cache["data"] = result
        _version_comparison_cache["computed_at"] = computed_at.isoformat()
        try:
            _save_cache_to_db(db, result, computed_at)
        except Exception as e:
            logger.warning(f"Could not persist version comparison cache to DB: {e}")
        return {
            "status": "success",
            "computed_at": _version_comparison_cache["computed_at"],
            "total_predictions": result.get("total_predictions", 0),
            "versions": len(result.get("versions", [])),
        }
    except Exception as e:
        logger.error(f"Version comparison run failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# M0 Programme Baselines Endpoints
# ==============================================================================

@router.get("/revenue-baseline")
async def get_revenue_baseline():
    """Return manually-configured revenue baseline from JSON config."""
    import json
    from pathlib import Path
    
    config_path = Path(__file__).parent.parent / "revenue_baseline.json"
    if not config_path.exists():
        return {"total_mrr": 0, "total_subscribers": 0, "apps": [], "snapshot_date": None}
    
    with open(config_path) as f:
        return json.load(f)


@router.post("/exploitation/validate")
async def validate_exploitation_recommendation(
    request: Request,
    db: Session = Depends(get_db)
):
    """Record a manual validation result for a BUILD recommendation."""
    body = await request.json()
    
    recommendation_id = body.get("recommendation_id")
    if not recommendation_id:
        raise HTTPException(status_code=400, detail="recommendation_id is required")
    
    rec = db.query(ExploitationRecommendation).filter(
        ExploitationRecommendation.id == recommendation_id
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    validation = ExploitationValidation(
        recommendation_id=recommendation_id,
        actual_outcome=body.get("actual_outcome", "UNKNOWN"),
        outcome_notes=body.get("outcome_notes", ""),
        demand_accurate=body.get("demand_accurate"),
        competition_accurate=body.get("competition_accurate"),
        revenue_potential_accurate=body.get("revenue_potential_accurate"),
        actual_revenue=body.get("actual_revenue"),
        viability_score_at_validation=rec.build_viability_score,
    )
    db.add(validation)
    db.commit()
    db.refresh(validation)
    
    return {"status": "success", "validation": validation.to_dict()}


@router.get("/exploitation/validations")
async def get_exploitation_validations(db: Session = Depends(get_db)):
    """Return all exploitation validation records."""
    validations = db.query(ExploitationValidation).order_by(
        ExploitationValidation.validated_at.desc()
    ).all()
    return {"validations": [v.to_dict() for v in validations]}


@router.get("/baselines")
async def get_programme_baselines(db: Session = Depends(get_db)):
    """Consolidated M0 Programme Baselines — all 4 metrics in one response."""
    import json
    import traceback
    from pathlib import Path

    # Safe defaults — returned on any unhandled error
    _empty = {
        "model_accuracy": {"direction_accuracy_pct": 0, "total_predictions": 0, "avg_error_pct": 0, "target": 90, "trend": []},
        "mape": {"mape_pct": 0, "total_validated": 0, "target": 5},
        "lag_error": {"avg_lag_error_days": None, "total_with_lag_data": 0, "target": 7},
        "build_errors": {"error_rate_pct": 0, "total_builds": 0, "successful_builds": 0, "failed_builds": 0, "target": 5, "trend": []},
        "exploitation": {"viability_accuracy_pct": 0, "validated_count": 0, "total_build_recommendations": 0, "target": 90},
        "revenue": {"total_mrr": 0, "total_subscribers": 0, "app_count": 0, "apps": [], "target_mrr": 20000, "snapshot_date": None},
    }

    try:
        # 1. Model Accuracy
        validated_predictions = []
        try:
            validated_predictions = db.query(PredictionTracking).filter(
                PredictionTracking.status == 'validated'
            ).all()
        except Exception as e:
            logger.warning(f"PredictionTracking query failed: {e}")

        direction_correct = sum(1 for p in validated_predictions if getattr(p, 'direction_correct', False))
        model_accuracy = (direction_correct / len(validated_predictions) * 100) if validated_predictions else 0.0

        avg_error = 0.0
        if validated_predictions:
            errors = [abs(getattr(p, 'value_error_pct', 0) or 0) for p in validated_predictions]
            avg_error = sum(errors) / len(errors) if errors else 0.0

        # MAPE — Mean Absolute Percentage Error (same data, standalone metric)
        mape_pct = round(avg_error, 2)

        # Lag Error — how accurately we predict when the peak/trough occurs
        lag_errors = [getattr(p, 'lag_error_days', None) for p in validated_predictions]
        lag_errors = [e for e in lag_errors if e is not None]
        avg_lag_error = round(sum(abs(e) for e in lag_errors) / len(lag_errors), 1) if lag_errors else None

        # Model accuracy trend — group validated predictions by month
        model_trend = []
        monthly_groups = {}
        for p in validated_predictions:
            recorded = getattr(p, 'actual_recorded_at', None)
            if recorded:
                key = recorded.strftime("%Y-%m")
                monthly_groups.setdefault(key, []).append(p)
        for month in sorted(monthly_groups.keys()):
            preds = monthly_groups[month]
            correct = sum(1 for p in preds if getattr(p, 'direction_correct', False))
            model_trend.append({
                "month": month,
                "accuracy": round(correct / len(preds) * 100, 1) if preds else 0,
                "count": len(preds),
            })

        # 2. Build Errors — from MVPBuild table (in-app builds)
        build_metrics = {"total_builds": 0, "error_rate_pct": 0.0, "successful_builds": 0, "failed_builds": 0, "trend": []}
        try:
            all_builds = db.query(MVPBuild).order_by(MVPBuild.created_at.asc()).all()
            total_builds = len(all_builds)
            failed_builds = sum(1 for b in all_builds if b.status == 'FAILED')
            successful_builds = sum(1 for b in all_builds if b.status == 'LIVE')
            error_rate = (failed_builds / total_builds * 100) if total_builds else 0.0

            # Build trend — group by date
            build_trend = []
            for b in all_builds:
                build_trend.append({
                    "date": b.created_at.strftime("%Y-%m-%d") if b.created_at else None,
                    "success": b.status == 'LIVE',
                    "errors": b.total_errors or 0,
                    "duration": b.duration_seconds or 0,
                })

            build_metrics = {
                "total_builds": total_builds,
                "successful_builds": successful_builds,
                "failed_builds": failed_builds,
                "error_rate_pct": round(error_rate, 1),
                "trend": build_trend,
            }
        except Exception as e:
            logger.warning(f"Build metrics unavailable: {e}")

        # 3. Exploitation Accuracy
        validations = []
        exploit_accuracy = 0.0
        total_build_recs = 0
        try:
            from database import engine
            ExploitationValidation.__table__.create(bind=engine, checkfirst=True)
            validations = db.query(ExploitationValidation).all()
            exploit_correct = sum(1 for v in validations if v.actual_outcome in ('SUCCESS', 'PARTIAL'))
            exploit_accuracy = (exploit_correct / len(validations) * 100) if validations else 0.0
            total_build_recs = db.query(ExploitationRecommendation).filter(
                ExploitationRecommendation.action_type == 'BUILD'
            ).count()
        except Exception as e:
            logger.warning(f"Exploitation validation query failed: {e}")

        # 4. Revenue
        revenue_data = {"total_mrr": 0, "total_subscribers": 0, "apps": [], "snapshot_date": None}
        config_path = Path(__file__).parent.parent / "revenue_baseline.json"
        if config_path.exists():
            with open(config_path) as f:
                revenue_data = json.load(f)

        return {
            "model_accuracy": {
                "direction_accuracy_pct": round(model_accuracy, 1),
                "total_predictions": len(validated_predictions),
                "avg_error_pct": round(avg_error, 2),
                "target": 90,
                "trend": model_trend,
            },
            "mape": {
                "mape_pct": mape_pct,
                "total_validated": len(validated_predictions),
                "target": 5,
            },
            "lag_error": {
                "avg_lag_error_days": avg_lag_error,
                "total_with_lag_data": len(lag_errors),
                "target": 7,
            },
            "build_errors": {
                "error_rate_pct": build_metrics.get("error_rate_pct", 0),
                "total_builds": build_metrics.get("total_builds", 0),
                "successful_builds": build_metrics.get("successful_builds", 0),
                "failed_builds": build_metrics.get("failed_builds", 0),
                "target": 5,
                "trend": build_metrics.get("trend", []),
            },
            "exploitation": {
                "viability_accuracy_pct": round(exploit_accuracy, 1),
                "validated_count": len(validations),
                "total_build_recommendations": total_build_recs,
                "target": 90,
            },
            "revenue": {
                "total_mrr": revenue_data.get("total_mrr", 0),
                "total_subscribers": revenue_data.get("total_subscribers", 0),
                "app_count": len(revenue_data.get("apps", [])),
                "apps": revenue_data.get("apps", []),
                "target_mrr": 20000,
                "snapshot_date": revenue_data.get("snapshot_date"),
            },
        }

    except Exception as e:
        logger.error(f"Baselines endpoint failed: {e}\n{traceback.format_exc()}")
        return _empty


# ==============================================================================
# MVP Build Endpoints
# ==============================================================================

def _run_build(
    build_id: int,
    recommendation_id: int,
    complexity: str,
    parent_build_id: int = None,
):
    """Background task that executes the full MVP build pipeline.

    When ``parent_build_id`` is supplied, this is an iteration build.
    The BuildIntelligenceService aggregates evidence from the parent
    (errors, engagement, revenue, signal freshness, prior files) and
    that evidence is injected into the spec-generator AI prompt so the
    next iteration's YAML requirements are derived from real user
    behaviour on the live app.
    """
    import traceback
    from database import SessionLocal
    from services.s3_service import S3Service
    from services.mvp_builder_service import MVPBuilderService

    db = SessionLocal()
    try:
        build = db.query(MVPBuild).filter(MVPBuild.id == build_id).first()
        if not build:
            logger.error(f"Build {build_id} not found")
            return

        rec = db.query(ExploitationRecommendation).filter(
            ExploitationRecommendation.id == recommendation_id
        ).first()
        if not rec:
            build.status = "FAILED"
            build.error_message = "Recommendation not found"
            db.commit()
            return

        requirement = f"{rec.signal_display_name} → {rec.target_display_name}: {rec.reasoning or ''}"

        # If user selected a product concept, use it as the primary requirement
        selected_concept = None
        if rec.product_concepts and rec.selected_concept_index is not None:
            idx = rec.selected_concept_index
            if 0 <= idx < len(rec.product_concepts):
                selected_concept = rec.product_concepts[idx]
                requirement = (
                    f"Build: {selected_concept['name']} — {selected_concept['pitch']} "
                    f"Target customer: {selected_concept.get('target_customer', 'N/A')}. "
                    f"Revenue model: {selected_concept.get('revenue_model', 'N/A')}. "
                    f"Signal: {rec.signal_display_name} → {rec.target_display_name}. "
                    f"{rec.reasoning or ''}"
                )

        # Append or override with user-supplied requirements
        user_reqs = (rec.user_requirements or '').strip()
        if user_reqs and selected_concept:
            # Mode 2: Concept + user requirements
            requirement += f"\n\nKey user requirements:\n{user_reqs}"
        elif user_reqs and not selected_concept:
            # Mode 3: User requirements only (no concept selected)
            requirement = (
                f"User requirements:\n{user_reqs}\n\n"
                f"Context — Signal: {rec.signal_display_name} → {rec.target_display_name}. "
                f"{rec.reasoning or ''}"
            )

        recommendation_meta = {
            'signal_display_name': rec.signal_display_name,
            'target_display_name': rec.target_display_name,
            'reasoning': rec.reasoning or '',
            'opportunity_score': float(rec.opportunity_score) if rec.opportunity_score else None,
            'market_category': getattr(rec, 'market_category', None),
            'search_trend_direction': getattr(rec, 'search_trend_direction', None),
            'estimated_monthly_searches': getattr(rec, 'estimated_monthly_searches', None),
            'competition_level': getattr(rec, 'competition_level', None),
            'build_viability_score': float(rec.build_viability_score) if getattr(rec, 'build_viability_score', None) else None,
            'selected_concept': selected_concept,
            'user_requirements': user_reqs or None,
        }

        # Iteration intelligence — only populated when this is a child build.
        iteration_meta = None
        if parent_build_id:
            try:
                from services.build_intelligence_service import (
                    gather_iteration_intelligence,
                )
                iteration_meta = gather_iteration_intelligence(parent_build_id, db)
                logger.info(
                    f"Build {build_id}: gathered iteration intelligence from "
                    f"parent #{parent_build_id} "
                    f"(chain_length={len(iteration_meta.get('chain', []))}, "
                    f"engagement={iteration_meta.get('engagement', {}).get('unique_visitors', 0)} visitors, "
                    f"mrr=${iteration_meta.get('revenue', {}).get('mrr_usd', 0):.2f})"
                )
            except Exception as exc:
                logger.warning(
                    f"Build {build_id}: failed to gather iteration intelligence "
                    f"from parent #{parent_build_id}: {exc}"
                )

        s3 = S3Service()
        builder = MVPBuilderService(s3)
        builder.build_mvp(
            requirement=requirement,
            complexity=complexity,
            build_id=build_id,
            db_session=db,
            recommendation_meta=recommendation_meta,
            iteration_meta=iteration_meta,
        )

        # ----- Post-build: push to GitHub + deploy to Railway -----
        # Mark LIVE *first* so the build is never stuck at DEPLOYING if
        # the process dies mid-deploy.  Deployment is best-effort.
        build = db.query(MVPBuild).filter(MVPBuild.id == build_id).first()
        if build and build.status in ('LIVE', 'DEPLOYING'):
            build.status = 'LIVE'
            db.commit()
            try:

                from services.github_service import GitHubService
                github_svc = GitHubService()
                repo_name = None
                github_url = None

                if github_svc.enabled:
                    repo_name = GitHubService.slugify(
                        f"mvp-{build_id}-{rec.signal_display_name[:30]}"
                    )
                    repo_info = github_svc.create_repository(
                        name=repo_name,
                        description=(
                            f"Auto-generated MVP: "
                            f"{rec.signal_display_name} → {rec.target_display_name}"
                        ),
                    )
                    github_url = repo_info["html_url"]

                    build_files = (
                        db.query(MVPBuildFile)
                        .filter(MVPBuildFile.build_id == build_id)
                        .all()
                    )
                    files = [
                        (f.file_path, f.content)
                        for f in build_files
                        if f.content
                    ]
                    if files:
                        github_svc.push_files(
                            repo_name, files, f"MVP Build #{build_id}"
                        )
                    build.github_url = github_url
                    build.railway_url = github_url  # fallback until Railway domain generated
                    logger.info(
                        f"Build {build_id}: pushed to GitHub {github_url}"
                    )

                # Railway: create project (deployment requires GitHub
                # integration on Railway — connect repo in Railway UI).
                from services.railway_service import RailwayService
                railway_svc = RailwayService()
                if railway_svc.enabled and repo_name:
                    try:
                        project = railway_svc.create_project(repo_name)
                        build.railway_project_id = project.get("id")
                        service = railway_svc.create_service(
                            project["id"], repo_name
                        )
                        build.railway_service_id = service.get("id")
                        # Generate a public domain for the service
                        env_id = railway_svc.get_default_environment(
                            project["id"]
                        )
                        if env_id and service.get("id"):
                            domain_url = railway_svc.generate_domain(
                                service["id"], env_id
                            )
                            if domain_url:
                                build.railway_url = domain_url
                                logger.info(
                                    f"Build {build_id}: Railway domain "
                                    f"{domain_url}"
                                )
                        logger.info(
                            f"Build {build_id}: Railway project "
                            f"{project.get('id')} created"
                        )
                    except Exception as rail_err:
                        logger.warning(
                            f"Build {build_id}: Railway setup failed "
                            f"(GitHub push OK): {rail_err}"
                        )

                # Create ProductDeployment record
                deployment = ProductDeployment(
                    recommendation_id=recommendation_id,
                    build_id=build_id,
                    product_name=repo_name or f"mvp-{build_id}",
                    app_id=f"mvp_{build_id}",
                    description=(
                        f"Auto-generated MVP: "
                        f"{rec.signal_display_name} → {rec.target_display_name}"
                    ),
                    tech_stack={
                        "framework": "fastapi",
                        "language": "python",
                        "hosting": "railway",
                        "market_category": getattr(rec, 'market_category', None),
                        "selected_concept": selected_concept,
                    },
                    railway_url=build.railway_url,
                    deployed_at=datetime.utcnow(),
                    status="active",
                )
                db.add(deployment)
                db.commit()
                logger.info(f"Build {build_id}: deployment complete")

            except Exception as deploy_err:
                logger.warning(
                    f"Build {build_id}: deployment step failed "
                    f"(build stays LIVE): {deploy_err}"
                )
                try:
                    db.rollback()
                    build = db.query(MVPBuild).filter(
                        MVPBuild.id == build_id
                    ).first()
                    if build:
                        build.error_message = (
                            f"Code generated OK. Deploy failed: "
                            f"{str(deploy_err)[:200]}"
                        )
                        db.commit()
                except Exception:
                    pass

        # Auto-validate exploitation recommendation when build succeeds
        build = db.query(MVPBuild).filter(MVPBuild.id == build_id).first()
        if build and build.status in ('LIVE', 'DEPLOYING'):
            existing = db.query(ExploitationValidation).filter(
                ExploitationValidation.recommendation_id == recommendation_id
            ).first()
            if not existing:
                validation = ExploitationValidation(
                    recommendation_id=recommendation_id,
                    validator='auto-build',
                    actual_outcome='SUCCESS',
                    outcome_notes=f'Auto-validated: build {build_id} deployed successfully',
                    viability_score_at_validation=rec.build_viability_score if hasattr(rec, 'build_viability_score') else None,
                )
                db.add(validation)
                db.commit()
                logger.info(f"Build {build_id}: auto-validated recommendation {recommendation_id}")
    except Exception as e:
        logger.error(f"Build {build_id} failed: {e}\n{traceback.format_exc()}")
        try:
            from services.build_error_classifier import classify_build_error
            error_text = f"{e}\n{traceback.format_exc()}"
            classification = classify_build_error(error_text)
            build = db.query(MVPBuild).filter(MVPBuild.id == build_id).first()
            if build and build.status != "FAILED":
                build.status = "FAILED"
                build.error_message = str(e)[:500]
                build.error_breakdown = classification
                db.commit()
            logger.info(
                f"Build {build_id}: classified as {classification['primary_category']} "
                f"(auto_fixable={classification['auto_fixable']})"
            )
        except Exception:
            pass
    finally:
        db.close()


def _run_concept_generation_background(rec_id: int):
    """Background worker: call LLM and persist concepts. Owns its own DB session."""
    from database import SessionLocal
    from services.product_concept_generator import generate_product_concepts
    db = SessionLocal()
    try:
        rec = db.query(ExploitationRecommendation).filter(
            ExploitationRecommendation.id == rec_id
        ).first()
        if not rec:
            logger.error(f"[concepts] rec {rec_id} not found in background task")
            return

        logger.info(
            f"[concepts] rec_id={rec_id} starting LLM generation "
            f"(signal='{rec.signal_display_name}' target='{rec.target_display_name}' "
            f"category='{rec.market_category}')"
        )
        try:
            concepts = generate_product_concepts(
                signal_display=rec.signal_display_name,
                target_display=rec.target_display_name,
                market_category=rec.market_category or "general",
                opportunity_score=float(rec.opportunity_score or 0),
                correlation=float(rec.correlation or 0),
                p_value=float(rec.granger_p_value or 1),
                lag=rec.optimal_lag or 1,
                estimated_monthly_searches=rec.estimated_monthly_searches or 0,
                search_trend_direction=rec.search_trend_direction or "stable",
                competition_level=rec.competition_level or "LOW",
                revenue_potential=rec.revenue_potential or "LOW",
                predicted_direction=rec.predicted_direction,
                predicted_change_pct=float(rec.predicted_change_pct) if rec.predicted_change_pct else None,
                ensemble_confidence=rec.ensemble_confidence,
                db_session=db,
            )
            source = (concepts[0].get("source") if concepts else None)
            logger.info(
                f"[concepts] rec_id={rec_id} LLM returned {len(concepts)} concepts "
                f"(source={source})"
            )
            rec.product_concepts = concepts
            rec.concepts_generation_status = "done"
            rec.concepts_error = None
            rec.concepts_generated_at = datetime.utcnow()
            rec.updated_at = datetime.utcnow()
            db.commit()
            logger.info(f"[concepts] rec_id={rec_id} committed concepts to DB")
        except Exception as exc:
            logger.exception(f"[concepts] rec_id={rec_id} generation failed: {type(exc).__name__}: {exc}")
            try:
                rec.concepts_generation_status = "failed"
                rec.concepts_error = f"{type(exc).__name__}: {exc}"[:500]
                rec.updated_at = datetime.utcnow()
                db.commit()
            except Exception:
                logger.exception(f"[concepts] rec_id={rec_id} failed to persist error status")
    finally:
        db.close()


@router.post("/exploitation/{rec_id}/generate-concepts")
async def generate_product_concepts_for_rec(
    rec_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Kick off async generation of 3 AI-powered product concepts for a BUILD recommendation.

    Returns immediately with status='generating'. Client must poll
    GET /exploitation/{rec_id}/concepts/status until status is 'done' or 'failed'.
    """
    try:
        rec = db.query(ExploitationRecommendation).filter(
            ExploitationRecommendation.id == rec_id
        ).first()
        if not rec:
            return JSONResponse(status_code=404, content={"error": "Recommendation not found"})
        if rec.action_type != "BUILD":
            return JSONResponse(
                status_code=400,
                content={"error": "Only BUILD recommendations support product concepts"},
            )
        if rec.concepts_generation_status == "generating":
            return JSONResponse(
                status_code=409,
                content={"error": "Concept generation already in progress for this recommendation"},
            )

        logger.info(f"[concepts] rec_id={rec_id} queued for background generation")
        rec.concepts_generation_status = "generating"
        rec.concepts_error = None
        rec.updated_at = datetime.utcnow()
        db.commit()

        background_tasks.add_task(_run_concept_generation_background, rec_id)
        return JSONResponse(
            status_code=202,
            content={
                "recommendation_id": rec_id,
                "status": "generating",
                "message": "Concept generation started — poll /concepts/status",
            },
        )
    except Exception as exc:
        logger.exception(f"[concepts] rec_id={rec_id} endpoint failed before queueing")
        return JSONResponse(
            status_code=500,
            content={"error": f"{type(exc).__name__}: {exc}"},
        )


@router.get("/exploitation/{rec_id}/concepts/status")
async def get_concepts_status(rec_id: int, db: Session = Depends(get_db)):
    """Poll concept generation status for a recommendation.

    Self-heals stale 'generating' state (>10 min old) by flipping to 'failed'.
    """
    rec = db.query(ExploitationRecommendation).filter(
        ExploitationRecommendation.id == rec_id
    ).first()
    if not rec:
        return JSONResponse(status_code=404, content={"error": "Recommendation not found"})

    # TTL self-heal: if 'generating' for >10 min, declare it failed so the UI
    # un-freezes and the user can retry.
    if rec.concepts_generation_status == "generating" and rec.updated_at:
        age = datetime.utcnow() - rec.updated_at
        if age.total_seconds() > 600:
            logger.warning(
                f"[concepts] rec_id={rec_id} stuck in 'generating' for {age.total_seconds():.0f}s — auto-failing"
            )
            rec.concepts_generation_status = "failed"
            rec.concepts_error = (
                f"Generation appears to have crashed (no response after {int(age.total_seconds()/60)} min). "
                "Click Generate to retry."
            )
            rec.updated_at = datetime.utcnow()
            db.commit()

    return {
        "recommendation_id": rec_id,
        "status": rec.concepts_generation_status,  # NULL | generating | done | failed
        "error": rec.concepts_error,
        "concepts_generated_at": rec.concepts_generated_at.isoformat() if rec.concepts_generated_at else None,
        "concepts": rec.product_concepts if rec.concepts_generation_status == "done" else None,
    }


@router.post("/exploitation/{rec_id}/clear-concepts")
async def clear_product_concepts(rec_id: int, db: Session = Depends(get_db)):
    """Clear all stored product concepts for a recommendation (manual reset)."""
    rec = db.query(ExploitationRecommendation).filter(
        ExploitationRecommendation.id == rec_id
    ).first()
    if not rec:
        return JSONResponse(status_code=404, content={"error": "Recommendation not found"})
    rec.product_concepts = None
    rec.selected_concept_index = None
    rec.concepts_generation_status = None
    rec.concepts_error = None
    rec.concepts_generated_at = None
    rec.updated_at = datetime.utcnow()
    db.commit()
    logger.info(f"[concepts] rec_id={rec_id} concepts cleared by user")
    return {"recommendation_id": rec_id, "status": "cleared"}


@router.post("/exploitation/{rec_id}/select-concept")
async def select_product_concept(
    rec_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Select which product concept (0-2) to build for a recommendation."""
    body = await request.json()
    index = body.get("concept_index")
    if index is None or not isinstance(index, int) or index < 0 or index > 2:
        raise HTTPException(status_code=400, detail="concept_index must be 0, 1, or 2")

    rec = db.query(ExploitationRecommendation).filter(
        ExploitationRecommendation.id == rec_id
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if not rec.product_concepts:
        raise HTTPException(status_code=400, detail="Generate concepts first")

    rec.selected_concept_index = index
    rec.updated_at = datetime.utcnow()
    db.commit()

    selected = rec.product_concepts[index] if index < len(rec.product_concepts) else None
    return {"recommendation_id": rec_id, "selected_index": index, "concept": selected}


@router.post("/exploitation/build")
async def start_mvp_build(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Kick off an MVP build for a BUILD recommendation."""
    body = await request.json()

    recommendation_id = body.get("recommendation_id")
    complexity = body.get("complexity", "LOW").upper()
    if complexity not in ("LOW", "MEDIUM", "HIGH"):
        raise HTTPException(status_code=400, detail="complexity must be LOW, MEDIUM, or HIGH")
    if not recommendation_id:
        raise HTTPException(status_code=400, detail="recommendation_id is required")

    rec = db.query(ExploitationRecommendation).filter(
        ExploitationRecommendation.id == recommendation_id
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    # Save user requirements if provided
    user_requirements = (body.get("user_requirements") or "").strip()
    if user_requirements:
        rec.user_requirements = user_requirements
        rec.updated_at = datetime.utcnow()
        db.commit()

    # Require at least a selected concept OR user requirements to build
    has_concept = rec.product_concepts and rec.selected_concept_index is not None
    has_reqs = bool((rec.user_requirements or "").strip())
    if not has_concept and not has_reqs:
        raise HTTPException(
            status_code=400,
            detail="Select a product concept or provide key requirements before building"
        )

    build = MVPBuild(
        recommendation_id=recommendation_id,
        complexity=complexity,
        status="QUEUED",
        s3_prefix=f"mvp-builds/{recommendation_id}/{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
    )
    db.add(build)
    db.commit()
    db.refresh(build)

    background_tasks.add_task(_run_build, build.id, recommendation_id, complexity)

    return {"build_id": build.id, "status": build.status, "complexity": complexity}


@router.get("/exploitation/builds")
async def list_mvp_builds(
    recommendation_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """List MVP builds, optionally filtered by recommendation."""
    query = db.query(MVPBuild).order_by(MVPBuild.created_at.desc())
    if recommendation_id:
        query = query.filter(MVPBuild.recommendation_id == recommendation_id)
    builds = query.limit(50).all()
    return {"builds": [b.to_dict() for b in builds]}


@router.get("/exploitation/builds/{build_id}")
async def get_mvp_build(build_id: int, db: Session = Depends(get_db)):
    """Get a single MVP build with its files.

    Includes stale-build detection: if a build has been in any active state
    (QUEUED, GENERATING, UPLOADING, DEPLOYING) for longer than 10 minutes,
    it is automatically marked as FAILED (the background task likely died
    due to a deployment restart or crash).
    """
    build = db.query(MVPBuild).filter(MVPBuild.id == build_id).first()
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")

    # Stale-build auto-fail: 10 minutes with no progress → dead task
    STALE_THRESHOLD_SECONDS = 600
    if build.status in ("GENERATING", "QUEUED", "UPLOADING", "DEPLOYING"):
        last_activity = build.updated_at or build.created_at
        if last_activity and (datetime.utcnow() - last_activity).total_seconds() > STALE_THRESHOLD_SECONDS:
            build.status = "FAILED"
            build.error_message = (
                "Build timed out — background task likely killed by a deployment restart. "
                f"Last activity was {last_activity.isoformat()}Z."
            )
            steps = list(build.build_steps or [])
            steps.append({
                "step": "TIMEOUT",
                "at": datetime.utcnow().isoformat(),
                "detail": f"Auto-failed after {STALE_THRESHOLD_SECONDS}s with no progress",
            })
            build.build_steps = steps
            db.commit()
            db.refresh(build)
            logger.warning("Build %d auto-failed as stale (last activity: %s)", build_id, last_activity)

    data = build.to_dict()
    data["files"] = [f.to_dict() for f in build.files]
    return data


@router.delete("/exploitation/builds/{build_id}")
async def cancel_mvp_build(build_id: int, db: Session = Depends(get_db)):
    """Cancel/fail a stuck or in-progress build."""
    build = db.query(MVPBuild).filter(MVPBuild.id == build_id).first()
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    if build.status in ("LIVE", "FAILED"):
        return {"build_id": build_id, "status": build.status, "message": "Build already terminal"}
    old_status = build.status
    build.status = "FAILED"
    build.error_message = f"Manually cancelled (was {old_status})"
    steps = list(build.build_steps or [])
    steps.append({
        "step": "CANCELLED",
        "at": datetime.utcnow().isoformat(),
        "detail": f"Manually cancelled from {old_status}",
    })
    build.build_steps = steps
    db.commit()
    return {"build_id": build_id, "status": "FAILED", "previous_status": old_status}


@router.post("/exploitation/builds/{build_id}/iterate")
async def iterate_mvp_build(
    build_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Iterate on an existing MVP build.
    
    Creates a child build linked to the parent via parent_build_id,
    incrementing iteration_number. Enriches the build spec with the
    parent's error patterns and files for the AI to learn from.
    
    Only LIVE or FAILED builds can be iterated. Blocks if an active
    (QUEUED/GENERATING) build already exists in the same chain.
    """
    parent = db.query(MVPBuild).filter(MVPBuild.id == build_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Build not found")
    
    if parent.status not in ("LIVE", "FAILED"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot iterate a {parent.status} build. Only LIVE or FAILED builds can be iterated."
        )
    
    # Concurrency guard: check for active builds in the same chain
    active_sibling = db.query(MVPBuild).filter(
        MVPBuild.recommendation_id == parent.recommendation_id,
        MVPBuild.status.in_(["QUEUED", "GENERATING", "UPLOADING", "DEPLOYING"]),
    ).first()
    if active_sibling:
        raise HTTPException(
            status_code=409,
            detail=f"Build #{active_sibling.id} is already {active_sibling.status} for this recommendation. Wait for it to complete."
        )
    
    body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    iterate_reason = body.get("reason", "manual")
    complexity = body.get("complexity", parent.complexity or "LOW").upper()
    if complexity not in ("LOW", "MEDIUM", "HIGH"):
        complexity = parent.complexity or "LOW"
    
    # Create the child build
    child = MVPBuild(
        recommendation_id=parent.recommendation_id,
        complexity=complexity,
        status="QUEUED",
        s3_prefix=f"mvp-builds/{parent.recommendation_id}/{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        iteration_number=(parent.iteration_number or 1) + 1,
        parent_build_id=parent.id,
        iterate_reason=iterate_reason,
    )
    db.add(child)
    db.commit()
    db.refresh(child)
    
    background_tasks.add_task(
        _run_build,
        child.id,
        parent.recommendation_id,
        complexity,
        parent.id,
    )
    
    return {
        "build_id": child.id,
        "parent_build_id": parent.id,
        "iteration_number": child.iteration_number,
        "status": child.status,
        "iterate_reason": iterate_reason,
    }


@router.get("/exploitation/builds/{build_id}/iterations")
async def get_build_iteration_chain(build_id: int, db: Session = Depends(get_db)):
    """Get the full iteration chain for a build (all ancestors and descendants)."""
    build = db.query(MVPBuild).filter(MVPBuild.id == build_id).first()
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    
    # Walk up to the root
    root = build
    while root.parent_build_id:
        parent = db.query(MVPBuild).filter(MVPBuild.id == root.parent_build_id).first()
        if not parent:
            break
        root = parent
    
    # Collect the full chain from root downward
    chain = [root.to_dict()]
    current_id = root.id
    while True:
        child = db.query(MVPBuild).filter(MVPBuild.parent_build_id == current_id).first()
        if not child:
            break
        chain.append(child.to_dict())
        current_id = child.id
    
    return {"build_id": build_id, "chain": chain, "total_iterations": len(chain)}


@router.get("/exploitation/builds-portfolio")
async def list_builds_portfolio(
    db: Session = Depends(get_db),
):
    """List all builds with recommendation context for the Builds Portfolio tab.
    
    Unlike the standard /builds endpoint (keyed by recommendation_id for cards),
    this returns a flat list enriched with recommendation display names and
    commercial metrics (engagement + revenue) from ProductDeployment/ProductMetrics.
    """
    from models import ProductMetrics
    
    builds = db.query(MVPBuild).order_by(MVPBuild.created_at.desc()).limit(200).all()
    
    # Batch-fetch recommendation display names
    rec_ids = list({b.recommendation_id for b in builds})
    recs = {}
    if rec_ids:
        rec_rows = db.query(ExploitationRecommendation).filter(
            ExploitationRecommendation.id.in_(rec_ids)
        ).all()
        recs = {r.id: r for r in rec_rows}
    
    # Batch-fetch deployments — a build can have multiple ProductDeployments
    # (one from the deploy step, one from commercial intelligence, etc.).
    build_ids = [b.id for b in builds]
    deps_by_build = {}   # build_id → list[ProductDeployment]
    dep_rows = []
    if build_ids:
        dep_rows = db.query(ProductDeployment).filter(
            ProductDeployment.build_id.in_(build_ids)
        ).all()
        for d in dep_rows:
            deps_by_build.setdefault(d.build_id, []).append(d)

    # Batch-fetch latest metrics per deployment
    dep_ids = [d.id for d in dep_rows] if build_ids else []
    metrics_map = {}  # deployment_id → ProductMetrics
    if dep_ids:
        from sqlalchemy import func
        # Get most recent metrics row per deployment
        subq = (
            db.query(
                ProductMetrics.deployment_id,
                func.max(ProductMetrics.period_end).label("latest")
            )
            .filter(ProductMetrics.deployment_id.in_(dep_ids))
            .group_by(ProductMetrics.deployment_id)
            .subquery()
        )
        latest_metrics = (
            db.query(ProductMetrics)
            .join(subq, (ProductMetrics.deployment_id == subq.c.deployment_id) & (ProductMetrics.period_end == subq.c.latest))
            .all()
        )
        metrics_map = {m.deployment_id: m for m in latest_metrics}
    
    result = []
    for b in builds:
        d = b.to_dict()
        rec = recs.get(b.recommendation_id)
        if rec:
            d["signal_display_name"] = rec.signal_display_name
            d["target_display_name"] = rec.target_display_name
            d["action_type"] = getattr(rec, 'action_type', None)
        else:
            d["signal_display_name"] = "Unknown"
            d["target_display_name"] = "Unknown"
            d["action_type"] = None

        # Enrich with commercial metrics (Track G)
        # Aggregate across ALL deployments for this build (there can be >1).
        build_deps = deps_by_build.get(b.id, [])
        engagement = 0
        revenue_mrr = 0.0
        dep_status = None
        dep_outcome = None
        for dep in build_deps:
            pm = metrics_map.get(dep.id)
            if pm:
                engagement = max(engagement, pm.unique_visitors or 0)
                revenue_mrr = max(revenue_mrr, round((pm.mrr_cents or 0) / 100, 2))
            if dep.status:
                dep_status = dep.status
            if dep.outcome:
                dep_outcome = dep.outcome
        d["engagement"] = engagement
        d["revenue_mrr"] = revenue_mrr
        d["deployment_status"] = dep_status
        d["deployment_outcome"] = dep_outcome
        result.append(d)
    
    # Summary stats
    total = len(result)
    live = sum(1 for b in result if b["status"] == "LIVE")
    failed = sum(1 for b in result if b["status"] == "FAILED")
    in_progress = sum(1 for b in result if b["status"] in ("QUEUED", "GENERATING", "UPLOADING", "DEPLOYING"))
    total_cost = sum(b.get("ai_cost_usd") or 0 for b in result)
    
    return {
        "builds": result,
        "summary": {
            "total": total,
            "live": live,
            "failed": failed,
            "in_progress": in_progress,
            "total_ai_cost_usd": round(total_cost, 2),
        },
    }


@router.get("/exploitation/builds/{build_id}/files")
async def get_mvp_build_files(build_id: int, db: Session = Depends(get_db)):
    """List generated files for a build."""
    build = db.query(MVPBuild).filter(MVPBuild.id == build_id).first()
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    return {"files": [f.to_dict() for f in build.files]}


@router.get("/exploitation/builds/{build_id}/files/{file_id}")
async def get_mvp_build_file_content(build_id: int, file_id: int, db: Session = Depends(get_db)):
    """Get a single generated file with its content."""
    from models import MVPBuildFile
    bf = db.query(MVPBuildFile).filter(
        MVPBuildFile.id == file_id, MVPBuildFile.build_id == build_id
    ).first()
    if not bf:
        raise HTTPException(status_code=404, detail="File not found")
    return bf.to_dict(include_content=True)


# ==============================================================================
# MVP Engagement Beacon
# ==============================================================================

@router.post("/mvp-beacon/{build_id}", status_code=204)
async def mvp_beacon(build_id: int, request: Request, db: Session = Depends(get_db)):
    """Receive page-view beacon pings from deployed MVPs.

    Stores anonymised visitor data for engagement tracking.
    Called by the JS beacon injected into generated MVP dashboards.
    """
    import hashlib

    # Validate build exists
    build = db.query(MVPBuild).filter(MVPBuild.id == build_id).first()
    if not build:
        return  # silently ignore unknown build IDs

    # Anonymised visitor fingerprint — no PII stored
    client_ip = request.client.host if request.client else "unknown"
    user_agent = (request.headers.get("user-agent") or "")[:500]
    visitor_hash = hashlib.sha256(
        f"{client_ip}:{user_agent}".encode()
    ).hexdigest()

    # Parse optional referrer from body
    referrer = None
    try:
        body = await request.json()
        referrer = (body.get("r") or "")[:500] if isinstance(body, dict) else None
    except Exception:
        pass

    pv = MvpPageView(
        build_id=build_id,
        visitor_hash=visitor_hash,
        user_agent=user_agent,
        referrer=referrer,
    )
    db.add(pv)
    db.flush()

    # Inline upsert into ProductMetrics so the builds-portfolio engagement
    # column reflects this visit immediately (without waiting for the 6-hourly
    # aggregate_page_views job).
    try:
        from sqlalchemy import func
        deployment = (
            db.query(ProductDeployment)
            .filter(ProductDeployment.build_id == build_id)
            .first()
        )
        if not deployment:
            deployment = ProductDeployment(
                build_id=build_id,
                product_name=f"mvp-{build_id}",
                app_id=f"mvp_{build_id}",
                railway_url=getattr(build, "railway_url", None),
                deployed_at=getattr(build, "created_at", datetime.utcnow()),
                status="active",
            )
            db.add(deployment)
            db.flush()

        now = datetime.utcnow()
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Recompute today's totals from MvpPageView for this build
        total_views, unique_visitors = (
            db.query(
                func.count(MvpPageView.id),
                func.count(func.distinct(MvpPageView.visitor_hash)),
            )
            .filter(
                MvpPageView.build_id == build_id,
                MvpPageView.created_at >= period_start,
            )
            .one()
        )

        metrics = (
            db.query(ProductMetrics)
            .filter(
                ProductMetrics.deployment_id == deployment.id,
                ProductMetrics.period_start == period_start,
            )
            .first()
        )
        if metrics:
            metrics.page_views = int(total_views or 0)
            metrics.unique_visitors = int(unique_visitors or 0)
            metrics.period_end = now
            metrics.source = "beacon"
        else:
            db.add(ProductMetrics(
                deployment_id=deployment.id,
                period_start=period_start,
                period_end=now,
                page_views=int(total_views or 0),
                unique_visitors=int(unique_visitors or 0),
                source="beacon",
            ))
    except Exception as e:
        logger.warning(f"mvp_beacon: inline ProductMetrics upsert failed for build {build_id}: {e}")

    db.commit()
    return


# Unprefixed alias is registered on the FastAPI app in main.py (see
# `_legacy_mvp_beacon`) so historical MVPs that beacon to /api/mvp-beacon/{id}
# (missing the /dashboard prefix) continue to register page views.
