"""
Admin Router for Database Management Operations
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
import sys
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

# In-memory job tracking (use Redis/DB for production)
_active_jobs = {}


@router.post("/initialize-database")
async def initialize_database():
    """
    One-time database initialization endpoint
    Creates tables, seeds variables, runs data ingestion, calculates correlations
    """
    try:
        # Import here to avoid circular dependencies
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from init_database import main as init_db_main
        from data_ingestion_service import DataIngestionService
        from correlation_analysis_service import CorrelationAnalysisService
        from database import get_db_session
        
        logger.info("Starting database initialization...")
        
        # Phase 1: Initialize database schema and seed variables
        logger.info("Phase 1: Creating tables and seeding variables...")
        init_result = init_db_main()
        
        if not init_result:
            raise Exception("Database initialization failed")
        
        # Phase 2A: Data ingestion
        logger.info("Phase 2A: Fetching data from APIs...")
        with get_db_session() as db:
            ingestion_service = DataIngestionService(db)
            ingestion_service.fetch_and_store_all_variables()
        
        # Phase 2B: Correlation analysis
        logger.info("Phase 2B: Calculating correlations...")
        with get_db_session() as db:
            analysis_service = CorrelationAnalysisService(db)
            analysis_service.calculate_all_correlations()
            
            # Get top correlations
            top_correlations = analysis_service.get_top_correlations(limit=10)
        
        logger.info("✅ Database initialization complete!")
        
        return JSONResponse({
            "status": "success",
            "message": "Database initialized successfully",
            "top_correlations": [
                {
                    "variable1": corr.variable1.display_name,
                    "variable2": corr.variable2.display_name,
                    "correlation": round(corr.correlation_value, 4),
                    "p_value": round(corr.p_value, 6) if corr.p_value else None
                }
                for corr in top_correlations
            ]
        })
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Database initialization failed: {str(e)}"
        )


def _run_data_fetch_background(job_id: str):
    """Background task for data fetching"""
    try:
        _active_jobs[job_id]['status'] = 'running'
        _active_jobs[job_id]['stage'] = 'fetching'
        _active_jobs[job_id]['updated_at'] = datetime.utcnow().isoformat()
        
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from data_ingestion_service import DataIngestionService
        
        logger.info(f"Job {job_id}: Starting data ingestion...")
        
        ingestion_service = DataIngestionService()
        result = ingestion_service.fetch_and_store_all_variables()
        
        _active_jobs[job_id]['status'] = 'completed'
        _active_jobs[job_id]['stage'] = 'done'
        _active_jobs[job_id]['result'] = result
        _active_jobs[job_id]['updated_at'] = datetime.utcnow().isoformat()
        
        logger.info(f"Job {job_id}: ✅ Data ingestion complete!")
        
    except Exception as e:
        logger.error(f"Job {job_id}: Data ingestion failed: {e}", exc_info=True)
        _active_jobs[job_id]['status'] = 'failed'
        _active_jobs[job_id]['error'] = str(e)
        _active_jobs[job_id]['updated_at'] = datetime.utcnow().isoformat()


@router.post("/fetch-data")
async def fetch_data(background_tasks: BackgroundTasks):
    """Fetch data from APIs in background - returns job_id for polling"""
    try:
        # Create job ID
        job_id = f"fetch_{int(datetime.utcnow().timestamp())}"
        
        # Initialize job status
        _active_jobs[job_id] = {
            'job_id': job_id,
            'type': 'data_fetch',
            'status': 'queued',
            'stage': 'initializing',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Queue background task
        background_tasks.add_task(_run_data_fetch_background, job_id)
        
        logger.info(f"Job {job_id}: Queued data ingestion")
        
        return JSONResponse({
            "status": "queued",
            "message": "Data fetch started in background",
            "job_id": job_id,
            "poll_url": f"/api/admin/job-status/{job_id}"
        })
        
    except Exception as e:
        logger.error(f"Failed to queue data fetch: {e}", exc_info=True)
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)


def _run_correlation_calc_background(job_id: str):
    """Background task for correlation calculation"""
    try:
        _active_jobs[job_id]['status'] = 'running'
        _active_jobs[job_id]['stage'] = 'calculating'
        _active_jobs[job_id]['updated_at'] = datetime.utcnow().isoformat()
        
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from correlation_analysis_service import CorrelationAnalysisService
        from database import get_db_session
        from models import CorrelationResult
        from sqlalchemy.orm import joinedload
        
        logger.info(f"Job {job_id}: Starting correlation calculation...")
        
        analysis_service = CorrelationAnalysisService()
        analysis_service.calculate_all_correlations()
        
        # Get top correlations
        with get_db_session() as db:
            top_correlations = (
                db.query(CorrelationResult)
                .options(joinedload(CorrelationResult.variable1))
                .options(joinedload(CorrelationResult.variable2))
                .filter(CorrelationResult.is_significant.is_(True))
                .order_by(CorrelationResult.abs_correlation.desc())
                .limit(10)
                .all()
            )
            
            top_corr_list = [
                {
                    "variable1": corr.variable1.display_name,
                    "variable2": corr.variable2.display_name,
                    "correlation": round(corr.correlation_value, 4),
                    "p_value": round(corr.p_value, 6) if corr.p_value else None,
                    "sample_size": corr.sample_size
                }
                for corr in top_correlations
            ]
        
        _active_jobs[job_id]['status'] = 'completed'
        _active_jobs[job_id]['stage'] = 'done'
        _active_jobs[job_id]['result'] = {'top_correlations': top_corr_list}
        _active_jobs[job_id]['updated_at'] = datetime.utcnow().isoformat()
        
        logger.info(f"Job {job_id}: ✅ Correlation calculation complete!")
        
    except Exception as e:
        logger.error(f"Job {job_id}: Correlation calc failed: {e}", exc_info=True)
        _active_jobs[job_id]['status'] = 'failed'
        _active_jobs[job_id]['error'] = str(e)
        _active_jobs[job_id]['updated_at'] = datetime.utcnow().isoformat()


@router.post("/calculate-correlations")
async def calculate_correlations(background_tasks: BackgroundTasks):
    """Calculate correlations in background - returns job_id for polling"""
    try:
        # Create job ID
        job_id = f"corr_{int(datetime.utcnow().timestamp())}"
        
        # Initialize job status
        _active_jobs[job_id] = {
            'job_id': job_id,
            'type': 'correlation_calc',
            'status': 'queued',
            'stage': 'initializing',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Queue background task
        background_tasks.add_task(_run_correlation_calc_background, job_id)
        
        logger.info(f"Job {job_id}: Queued correlation calculation")
        
        return JSONResponse({
            "status": "queued",
            "message": "Correlation calculation started in background",
            "job_id": job_id,
            "poll_url": f"/api/admin/job-status/{job_id}"
        })
        
    except Exception as e:
        logger.error(f"Failed to queue correlation calc: {e}", exc_info=True)
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)


@router.get("/job-status/{job_id}")
async def get_job_status(job_id: str):
    """Poll status of background job"""
    if job_id not in _active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JSONResponse(_active_jobs[job_id])


@router.post("/calculate-correlations")
async def calculate_correlations():
    """Calculate correlations for all variable pairs"""
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from correlation_analysis_service import CorrelationAnalysisService
        from database import get_db_session
        from models import CorrelationResult
        
        logger.info("Starting correlation calculation...")
        
        analysis_service = CorrelationAnalysisService()
        result = analysis_service.calculate_all_correlations()
        
        # Get top correlations from database with eagerly loaded relationships
        from sqlalchemy.orm import joinedload
        
        with get_db_session() as db:
            top_correlations = (
                db.query(CorrelationResult)
                .options(joinedload(CorrelationResult.variable1))
                .options(joinedload(CorrelationResult.variable2))
                .filter(CorrelationResult.is_significant.is_(True))
                .order_by(CorrelationResult.abs_correlation.desc())
                .limit(10)
                .all()
            )
            
            # Build result list while still in session
            top_corr_list = [
                {
                    "variable1": corr.variable1.display_name,
                    "variable2": corr.variable2.display_name,
                    "correlation": round(corr.correlation_value, 4),
                    "p_value": round(corr.p_value, 6) if corr.p_value else None,
                    "sample_size": corr.sample_size
                }
                for corr in top_correlations
            ]
        
        logger.info("✅ Correlation calculation complete!")
        return JSONResponse({
            "status": "success",
            "message": "Correlations calculated successfully",
            "stats": result,
            "top_correlations": top_corr_list
        })
        
    except Exception as e:
        logger.error(f"Correlation calculation failed: {e}", exc_info=True)
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)


@router.get("/data-quality")
async def get_data_quality():
    """Get comprehensive data quality metrics"""
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from database import get_db_session
        from models import VariableMetadata, TimeSeriesData, CorrelationResult
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        with get_db_session() as db:
            # Total variables and data coverage
            total_vars = db.query(VariableMetadata).filter(
                VariableMetadata.is_active.is_(True)
            ).count()
            
            vars_with_data = db.query(func.count(func.distinct(TimeSeriesData.variable_id))).scalar()
            
            # Data freshness by source
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            current_vars = db.query(func.count(func.distinct(TimeSeriesData.variable_id))).filter(
                TimeSeriesData.timestamp >= thirty_days_ago
            ).scalar()
            
            # Total data points and correlations
            total_points = db.query(TimeSeriesData).count()
            total_corrs = db.query(CorrelationResult).count()
            
            # Sample size distribution
            sample_sizes = {
                "0-2": db.query(CorrelationResult).filter(CorrelationResult.sample_size.between(0, 2)).count(),
                "3-9": db.query(CorrelationResult).filter(CorrelationResult.sample_size.between(3, 9)).count(),
                "10-19": db.query(CorrelationResult).filter(CorrelationResult.sample_size.between(10, 19)).count(),
                "20-49": db.query(CorrelationResult).filter(CorrelationResult.sample_size.between(20, 49)).count(),
                "50+": db.query(CorrelationResult).filter(CorrelationResult.sample_size >= 50).count()
            }
            
            # Suspicious correlations (high correlation, low sample size)
            suspicious = db.query(CorrelationResult).filter(
                CorrelationResult.abs_correlation > 0.95,
                CorrelationResult.sample_size < 20
            ).count()
            
            # Variables by source
            source_dist = {}
            for source in ['alpha_vantage', 'usgs', 'nasa_eonet', 'worldbank', 'arxiv', 'clinicaltrials']:
                count = db.query(VariableMetadata).filter(
                    VariableMetadata.source == source,
                    VariableMetadata.is_active.is_(True)
                ).count()
                source_dist[source] = count
            
            return JSONResponse({
                "status": "success",
                "summary": {
                    "total_variables": total_vars,
                    "variables_with_data": vars_with_data,
                    "current_variables": current_vars,
                    "stale_variables": vars_with_data - current_vars,
                    "no_data_variables": total_vars - vars_with_data,
                    "total_data_points": total_points,
                    "total_correlations": total_corrs
                },
                "source_distribution": source_dist,
                "correlation_sample_sizes": sample_sizes,
                "suspicious_correlations": suspicious
            })
    
    except Exception as e:
        logger.error(f"Data quality check failed: {e}", exc_info=True)
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)


@router.get("/health")
async def admin_health():
    """Health check for admin endpoints"""
    return {"status": "ok", "message": "Admin endpoints are available"}


@router.get("/env-check")
async def env_check():
    """Check environment variables (for debugging)"""
    return {
        "DATABASE_URL_exists": bool(os.getenv('DATABASE_URL')),
        "DATABASE_PUBLIC_URL_exists": bool(os.getenv('DATABASE_PUBLIC_URL')),
        "POSTGRES_DB_exists": bool(os.getenv('POSTGRES_DB')),
        "DATABASE_URL_prefix": os.getenv('DATABASE_URL', '')[:30] if os.getenv('DATABASE_URL') else None,
        "DATABASE_PUBLIC_URL_prefix": os.getenv('DATABASE_PUBLIC_URL', '')[:30] if os.getenv('DATABASE_PUBLIC_URL') else None,
        "POSTGRES_DB_prefix": os.getenv('POSTGRES_DB', '')[:30] if os.getenv('POSTGRES_DB') else None
    }


@router.get("/data-quality")
async def data_quality_diagnostic():
    """Run comprehensive data quality diagnostic"""
    try:
        from database import get_db_session
        from models import VariableMetadata, TimeSeriesData, CorrelationResult
        from sqlalchemy import and_
        from datetime import datetime
        from collections import defaultdict
        
        with get_db_session() as session:
            # Variable inventory
            variables = session.query(VariableMetadata).filter(
                VariableMetadata.is_active.is_(True)
            ).all()
            
            source_counts = defaultdict(int)
            for v in variables:
                source_counts[v.source] += 1
            
            # Data coverage
            total_data_points = session.query(TimeSeriesData).count()
            
            # Per-variable stats
            var_stats = []
            for var in variables:
                data_count = session.query(TimeSeriesData).filter(
                    TimeSeriesData.variable_id == var.id
                ).count()
                
                if data_count == 0:
                    var_stats.append({
                        'name': var.display_name,
                        'source': var.source,
                        'points': 0,
                        'start': None,
                        'end': None,
                        'days_old': None
                    })
                    continue
                
                first = session.query(TimeSeriesData).filter(
                    TimeSeriesData.variable_id == var.id
                ).order_by(TimeSeriesData.timestamp.asc()).first()
                
                last = session.query(TimeSeriesData).filter(
                    TimeSeriesData.variable_id == var.id
                ).order_by(TimeSeriesData.timestamp.desc()).first()
                
                days_old = (datetime.utcnow() - last.timestamp).days
                
                var_stats.append({
                    'name': var.display_name,
                    'source': var.source,
                    'points': data_count,
                    'start': first.timestamp.strftime('%Y-%m-%d'),
                    'end': last.timestamp.strftime('%Y-%m-%d'),
                    'days_old': days_old
                })
            
            # Correlation quality
            total_corrs = session.query(CorrelationResult).count()
            
            sample_size_bins = {
                '0-2': session.query(CorrelationResult).filter(
                    CorrelationResult.sample_size < 3
                ).count(),
                '3-9': session.query(CorrelationResult).filter(
                    and_(
                        CorrelationResult.sample_size >= 3,
                        CorrelationResult.sample_size < 10
                    )
                ).count(),
                '10-19': session.query(CorrelationResult).filter(
                    and_(
                        CorrelationResult.sample_size >= 10,
                        CorrelationResult.sample_size < 20
                    )
                ).count(),
                '20-49': session.query(CorrelationResult).filter(
                    and_(
                        CorrelationResult.sample_size >= 20,
                        CorrelationResult.sample_size < 50
                    )
                ).count(),
                '50+': session.query(CorrelationResult).filter(
                    CorrelationResult.sample_size >= 50
                ).count()
            }
            
            # Suspicious correlations
            suspicious = session.query(CorrelationResult).filter(
                and_(
                    CorrelationResult.abs_correlation > 0.95,
                    CorrelationResult.sample_size < 20
                )
            ).count()
            
            # Summary stats
            current_vars = len([v for v in var_stats if v['days_old'] and v['days_old'] <= 30])
            stale_vars = len([v for v in var_stats if v['days_old'] and v['days_old'] > 30])
            no_data_vars = len([v for v in var_stats if v['points'] == 0])
            
            return {
                "status": "success",
                "summary": {
                    "total_variables": len(variables),
                    "variables_with_data": len([v for v in var_stats if v['points'] > 0]),
                    "current_variables": current_vars,
                    "stale_variables": stale_vars,
                    "no_data_variables": no_data_vars,
                    "total_data_points": total_data_points,
                    "total_correlations": total_corrs
                },
                "source_distribution": dict(source_counts),
                "correlation_sample_sizes": sample_size_bins,
                "suspicious_correlations": suspicious,
                "variables": var_stats[:20]  # First 20 for preview
            }
            
    except Exception as e:
        logger.error(f"Data quality diagnostic failed: {e}", exc_info=True)
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)



@router.post("/disable-empty-environmental-vars")
async def disable_empty_environmental_vars():
    """
    Disable environmental variables that have no data in EONET API.
    Only Wildfires, Severe Storms, Volcanoes, and Sea/Lake Ice have data.
    """
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from database import get_db_session
        from models import VariableMetadata
        
        # Categories with no events in EONET
        empty_categories = [
            'env_floods', 'env_droughts', 'env_dust_haze', 
            'env_landslides', 'env_snow', 'env_water_color'
        ]
        
        disabled_count = 0
        with get_db_session() as session:
            for var_name in empty_categories:
                var = session.query(VariableMetadata).filter(
                    VariableMetadata.name == var_name
                ).first()
                
                if var and var.is_active:
                    var.is_active = False
                    disabled_count += 1
                    logger.info(f"Disabled {var.display_name} (no EONET data)")
            
            session.commit()
        
        return {
            "status": "success",
            "message": f"Disabled {disabled_count} empty environmental variables",
            "disabled_vars": empty_categories,
            "reason": "These categories have 0 events in NASA EONET API"
        }
        
    except Exception as e:
        logger.error(f"Error disabling variables: {e}")
        raise HTTPException(status_code=500, detail=str(e))
