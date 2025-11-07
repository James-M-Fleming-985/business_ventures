"""
Dashboard Router for Correlation Discovery Engine
ALL ENDPOINTS USE REAL API DATA - NO MOCK/SYNTHETIC DATA
"""

from fastapi import APIRouter, Request, Query, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models import (
    VariableMetadata, TimeSeriesData, CorrelationResult,
    RollingCorrelation, APIStatus, AnalysisJob
)
from correlation_analysis_service import CorrelationAnalysisService
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
    top_n: int = Query(20, ge=5, le=100),
    cross_domain: bool = Query(False, description="Only show cross-domain correlations"),
    db: Session = Depends(get_db)
):
    """
    Get TOP N correlations for heatmap - REAL DATA ONLY
    Shows strongest correlations ranked by |r| as a matrix
    """
    try:
        # Get top N significant correlations
        service = CorrelationAnalysisService()
        top_correlations = service.get_top_correlations(
            limit=top_n,
            min_significance=0.05,
            cross_domain=cross_domain
        )
        
        if not top_correlations:
            return {
                "labels": [],
                "matrix": [],
                "message": "No correlations calculated yet. Run data ingestion first."
            }
        
        # Build variable list from top correlations
        var_names = set()
        for corr in top_correlations:
            var_names.add((corr['variable1_id'], corr['variable1_name']))
            var_names.add((corr['variable2_id'], corr['variable2_name']))
        
        var_list = sorted(list(var_names), key=lambda x: x[0])
        labels = [name for _, name in var_list]
        var_id_to_idx = {var_id: idx for idx, (var_id, _) in enumerate(var_list)}
        
        # Build correlation matrix (use None for missing pairs instead of 0.0)
        n = len(labels)
        matrix = [[None if i != j else 1.0 for j in range(n)] for i in range(n)]
        
        # Per-cell details for UI popouts
        details = {}
        
        for corr in top_correlations:
            idx1 = var_id_to_idx.get(corr['variable1_id'])
            idx2 = var_id_to_idx.get(corr['variable2_id'])
            
            if idx1 is not None and idx2 is not None:
                r_value = corr['correlation_value']
                matrix[idx1][idx2] = r_value
                matrix[idx2][idx1] = r_value  # Symmetric
                
                # Store details for both directions
                for i, j in [(idx1, idx2), (idx2, idx1)]:
                    key = f"{i}_{j}"
                    details[key] = {
                        "correlation": round(r_value, 4),
                        "p_value": round(corr['p_value'], 6) if corr['p_value'] else None,
                        "sample_size": corr['sample_size'],
                        "method": corr.get('method', 'pearson')
                    }
        
        return {
            "labels": labels,
            "matrix": matrix,
            "details": details,
            "correlation_count": len(top_correlations),
            "top_n": top_n,
            "cross_domain": cross_domain
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
        # Get all significant correlations above threshold
        correlations = db.query(CorrelationResult).filter(
            CorrelationResult.is_significant.is_(True),
            CorrelationResult.abs_correlation >= threshold
        ).all()
        
        if not correlations:
            return {
                "node_x": [],
                "node_y": [],
                "labels": [],
                "edge_x": [],
                "edge_y": [],
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
            "node_x": node_x,
            "node_y": node_y,
            "node_sizes": node_sizes,
            "node_colors": node_colors,
            "labels": labels,
            "edge_x": edge_x,
            "edge_y": edge_y,
            "correlation_count": len(correlations)
        }
    except Exception as e:
        logger.error(f"Error getting network: {e}")
        return {
            "node_x": [],
            "node_y": [],
            "labels": [],
            "edge_x": [],
            "edge_y": [],
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
            min_significance=0.05
        )
        
        leaderboard = []
        for i, corr in enumerate(top_correlations, 1):
            leaderboard.append({
                "rank": i,
                "variable1": corr['variable1_name'],
                "variable2": corr['variable2_name'],
                "correlation": corr['correlation_value'],
                "abs_correlation": abs(corr['correlation_value']),
                "p_value": corr['p_value'],
                "sample_size": corr['sample_size'],
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
    """Get detailed relationship analysis for two variables - REAL DATA ONLY"""
    try:
        # Find variables by name
        var1 = db.query(VariableMetadata).filter(
            VariableMetadata.display_name.ilike(f"%{var1_name}%")
        ).first()
        
        var2 = db.query(VariableMetadata).filter(
            VariableMetadata.display_name.ilike(f"%{var2_name}%")
        ).first()
        
        if not var1 or not var2:
            return {"error": "Variables not found"}
        
        # Get correlation result
        corr = db.query(CorrelationResult).filter(
            ((CorrelationResult.variable1_id == var1.id) & (CorrelationResult.variable2_id == var2.id)) |
            ((CorrelationResult.variable1_id == var2.id) & (CorrelationResult.variable2_id == var1.id))
        ).first()
        
        if not corr:
            return {"error": "No correlation calculated for this pair"}
        
        # Get scatter plot data
        var1_data = db.query(TimeSeriesData).filter(
            TimeSeriesData.variable_id == var1.id
        ).order_by(TimeSeriesData.timestamp).limit(100).all()
        
        var2_data = db.query(TimeSeriesData).filter(
            TimeSeriesData.variable_id == var2.id
        ).order_by(TimeSeriesData.timestamp).limit(100).all()
        
        # Align data by timestamp
        var1_dict = {dp.timestamp: dp.value for dp in var1_data}
        var2_dict = {dp.timestamp: dp.value for dp in var2_data}
        
        common_timestamps = set(var1_dict.keys()) & set(var2_dict.keys())
        
        x_values = [var1_dict[ts] for ts in sorted(common_timestamps)]
        y_values = [var2_dict[ts] for ts in sorted(common_timestamps)]
        
        return {
            "variable1": var1.display_name,
            "variable2": var2.display_name,
            "correlation": corr.correlation_value,
            "p_value": corr.p_value,
            "method": corr.method,
            "sample_size": corr.sample_size,
            "scatter": {
                "x": x_values,
                "y": y_values,
                "x_label": f"{var1.display_name} ({var1.unit})",
                "y_label": f"{var2.display_name} ({var2.unit})"
            },
            "is_significant": corr.is_significant
        }
    except Exception as e:
        logger.error(f"Error getting relationship: {e}")
        return {"error": str(e)}


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
                    "last_success": api.last_success.isoformat() if api.last_success else None,
                    "last_failure": api.last_failure.isoformat() if api.last_failure else None,
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
