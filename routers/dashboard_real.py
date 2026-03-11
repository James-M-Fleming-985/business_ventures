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
    RollingCorrelation, APIStatus, AnalysisJob, PredictionTracking,
    ExploitationRecommendation, ExploitationValidation
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
    from sqlalchemy import desc

    try:
        q = db.query(PredictionTracking)
        if status:
            q = q.filter(PredictionTracking.status == status)
        if model_version:
            q = q.filter(PredictionTracking.model_version == model_version)
        predictions = q.order_by(desc(PredictionTracking.predicted_at)).limit(limit).all()

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


def compute_opportunity_score(p_value: float, correlation: float, sample_size: int, momentum: float) -> float:
    """Compute a 0-100 opportunity score from statistical evidence + current momentum.
    
    Factors:
    - p_value_score (0-40): Lower p = higher score, scaled from 0.05 threshold
    - correlation_score (0-30): Stronger absolute correlation = higher
    - sample_size_score (0-15): More data = more reliable, capped at 100
    - momentum_score (0-15): Faster signal change = more urgent opportunity
    """
    # P-value: 0.05 → 0 pts, 0.00 → 40 pts
    p_value_score = max(0, (1 - (p_value or 1.0) / 0.05)) * 40
    
    # Correlation: |r| × 30
    correlation_score = min(abs(correlation or 0), 1.0) * 30
    
    # Sample size: capped at 100 observations
    sample_size_score = min((sample_size or 0) / 100, 1.0) * 15
    
    # Momentum: capped at 100% change rate
    momentum_score = min(abs(momentum or 0) / 100, 1.0) * 15
    
    return round(p_value_score + correlation_score + sample_size_score + momentum_score, 1)


def generate_reasoning(signal_display: str, target_display: str, target_source: str,
                       action_type: str, p_value: float, correlation: float, 
                       lag: int, momentum: float, predicted_direction: str,
                       predicted_change_pct: float) -> str:
    """Generate natural language reasoning for a recommendation."""
    
    # Direction of signal
    signal_dir = "rising" if momentum and momentum > 0 else "falling"
    mom_str = f"{abs(momentum or 0):.1f}%"
    
    # Correlation direction
    corr_str = f"r={correlation:.3f}" if correlation else "r=?"
    p_str = f"p={p_value:.4f}" if p_value else "p=?"
    lag_str = f"lag={lag}mo" if lag else ""
    
    stats = f"({p_str}, {corr_str}" + (f", {lag_str}" if lag_str else "") + ")"
    
    # Action-specific phrasing
    if action_type == 'BUY':
        action_phrase = f"Consider BUYING {target_display}."
    elif action_type == 'SELL':
        action_phrase = f"Consider SELLING/SHORTING {target_display}."
    elif action_type == 'BUILD':
        action_phrase = f"BUILD opportunity: create a product/tool in the {target_display} space."
    else:
        action_phrase = f"Monitor {target_display} for strategic positioning."
    
    # Predicted change
    change_str = ""
    if predicted_change_pct is not None:
        change_str = f" Predicted {predicted_direction or '?'} ~{abs(predicted_change_pct):.1f}%."
    
    return (
        f"{signal_display} pageviews {signal_dir} ({mom_str}) → "
        f"Granger-causes {target_display} {stats}.{change_str} "
        f"{action_phrase}"
    )


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
                            lag, momentum, db) -> dict:
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
    if estimated_monthly >= 50_000 and trend_dir == 'growing' and competition != 'HIGH':
        revenue = 'HIGH'
    elif estimated_monthly >= 10_000 or (trend_dir == 'growing' and competition != 'HIGH'):
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
                             predicted_change_pct) -> str:
    """Generate enriched reasoning text for BUILD recommendations."""
    signal_dir = 'rising' if momentum and momentum > 0 else 'falling'
    mom_str = f"{abs(momentum or 0):.1f}%"
    stats = f"(p={p_value:.4f}, r={correlation:.3f}" + (f", lag={lag}mo" if lag else "") + ")"

    searches = viability.get('estimated_monthly_searches', 0)
    trend = viability.get('search_trend_direction', 'stable')
    revenue = viability.get('revenue_potential', 'LOW')
    duration = viability.get('opportunity_duration_months', 0)
    category = viability.get('market_category', 'general')

    demand_str = f"~{searches:,}/mo searches" if searches else "limited search volume"
    trend_str = f"{trend} demand"
    window_str = f"~{duration}mo opportunity window" if duration else ""

    return (
        f"{signal_display} {signal_dir} ({mom_str}) → "
        f"Granger-causes {target_display} {stats}. "
        f"BUILD opportunity in {category.replace('_', ' ')}: "
        f"{demand_str}, {trend_str}, {revenue} revenue potential"
        + (f", {window_str}" if window_str else "") + "."
    )


@router.get("/exploitation/generate")
async def generate_exploitation_recommendations(db: Session = Depends(get_db)):
    """Scan all FMV signals and generate actionable recommendations from Granger data.
    
    For each Layer 1 signal with significant Granger relationships to non-Wikipedia targets,
    auto-classifies (BUY/SELL/BUILD/MONITOR), scores (0-100), and stores recommendations.
    Deduplicates by signal+target pair — updates existing recommendations.
    Also batch-creates PredictionTracking records for each recommendation.
    """
    from sqlalchemy import or_, and_, desc, asc
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
                
                # Score
                score = compute_opportunity_score(p_value, corr, sample, momentum)
                
                # BUILD-specific viability scoring
                viability = None
                if action_type == 'BUILD':
                    viability = compute_build_viability(
                        var, target_var, p_value, corr, lag, momentum, db
                    )
                    reasoning = generate_build_reasoning(
                        var.display_name, target_var.display_name,
                        viability, p_value, corr, lag, momentum,
                        predicted_direction, predicted_change_pct
                    )
                else:
                    # Generate standard reasoning for BUY/SELL/MONITOR
                    reasoning = generate_reasoning(
                        var.display_name, target_var.display_name, target_var.source,
                        action_type, p_value, corr, lag, momentum,
                        predicted_direction, predicted_change_pct
                    )
                
                # Upsert: update existing or create new
                existing = db.query(ExploitationRecommendation).filter(
                    ExploitationRecommendation.signal_name == var.name,
                    ExploitationRecommendation.target_name == target_var.name
                ).first()
                
                if existing:
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
            "signals_processed": len(layer1_vars)
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
        
        rec.updated_at = datetime.utcnow()
        db.commit()
        
        return rec.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update exploitation recommendation failed: {e}", exc_info=True)
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

        # 2. Build Errors — fetch from control_tower build_error_tracker
        build_metrics = {"total_builds": 0, "error_rate_pct": 0.0, "trend": []}
        try:
            import sys
            control_tower_path = Path(__file__).parent.parent.parent.parent
            if str(control_tower_path) not in sys.path:
                sys.path.insert(0, str(control_tower_path))
            from build_error_tracker import get_metrics_summary
            build_metrics = get_metrics_summary()
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
