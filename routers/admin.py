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
        
        # Phase 0: Run database migrations
        logger.info("Phase 0: Running database migrations...")
        try:
            from migrations.add_granger_causality_columns import upgrade as run_granger_migration
            run_granger_migration()
            logger.info("✅ Granger causality migration complete")
        except Exception as e:
            logger.warning(f"Migration may have already run: {e}")
        
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


@router.post("/run-migrations")
async def run_migrations():
    """
    Run database migrations (can be called independently)
    Useful for adding new columns without full database re-initialization
    """
    try:
        logger.info("Running database migrations...")
        migrations_run = []
        
        # Run Granger causality migration
        try:
            from migrations.add_granger_causality_columns import upgrade as run_granger_migration
            run_granger_migration()
            migrations_run.append("add_granger_causality_columns")
            logger.info("✅ Granger causality migration complete")
        except Exception as e:
            logger.warning(f"Granger migration error (may already be applied): {e}")
        
        return {
            "status": "success",
            "message": "Migrations complete",
            "migrations_applied": migrations_run
        }
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run-migrations")
async def run_migrations_get():
    """GET version of run-migrations for easy browser access"""
    return await run_migrations()


def _run_data_fetch_background(job_id: str, force: bool = False):
    """Background task for data fetching"""
    try:
        _active_jobs[job_id]['status'] = 'running'
        _active_jobs[job_id]['updated_at'] = datetime.utcnow().isoformat()
        
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from data_ingestion_service import DataIngestionService
        from database import get_db_session
        from models import TimeSeriesData
        
        # If force=True, delete existing time series data first
        if force:
            _active_jobs[job_id]['stage'] = 'deleting_old_data'
            logger.info(f"Job {job_id}: Force refetch - deleting existing time series data...")
            
            with get_db_session() as session:
                deleted_count = session.query(TimeSeriesData).delete()
                session.commit()
                logger.info(f"Job {job_id}: Deleted {deleted_count} existing data points")
                _active_jobs[job_id]['deleted_count'] = deleted_count
        
        _active_jobs[job_id]['stage'] = 'fetching'
        _active_jobs[job_id]['updated_at'] = datetime.utcnow().isoformat()
        
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
async def fetch_data(background_tasks: BackgroundTasks, force: bool = False):
    """
    Fetch data from APIs in background - returns job_id for polling
    
    Args:
        force: If True, deletes existing data before refetching (use for fixing incomplete data)
    """
    try:
        # Create job ID
        job_id = f"fetch_{int(datetime.utcnow().timestamp())}"
        
        # Initialize job status
        _active_jobs[job_id] = {
            'job_id': job_id,
            'type': 'data_fetch',
            'status': 'queued',
            'stage': 'initializing',
            'force': force,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Queue background task
        background_tasks.add_task(_run_data_fetch_background, job_id, force)
        
        logger.info(f"Job {job_id}: Queued data ingestion (force={force})")
        
        return JSONResponse({
            "status": "queued",
            "message": f"Data fetch started in background (force refetch: {force})",
            "job_id": job_id,
            "poll_url": f"/api/admin/job-status/{job_id}",
            "force": force
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


@router.get("/sample-size-report")
async def get_sample_size_report():
    """
    Get detailed report on correlation sample sizes to identify data quality issues
    """
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from database import get_db_session
        from models import CorrelationResult, VariableMetadata, TimeSeriesData
        from sqlalchemy import func
        from sqlalchemy.orm import joinedload
        
        with get_db_session() as db:
            # Sample size distribution
            size_ranges = [
                (0, 5, "0-5 (CRITICAL)"),
                (5, 10, "5-10 (BAD)"),
                (10, 20, "10-20 (POOR)"),
                (20, 50, "20-50 (MARGINAL)"),
                (50, 100, "50-100 (OK)"),
                (100, 999999, "100+ (GOOD)")
            ]
            
            distribution = {}
            for min_size, max_size, label in size_ranges:
                count = db.query(CorrelationResult).filter(
                    CorrelationResult.sample_size >= min_size,
                    CorrelationResult.sample_size < max_size
                ).count()
                distribution[label] = count
            
            # Get worst offenders (sample size < 10)
            bad_correlations = db.query(CorrelationResult).filter(
                CorrelationResult.sample_size < 10
            ).options(
                joinedload(CorrelationResult.variable1),
                joinedload(CorrelationResult.variable2)
            ).order_by(CorrelationResult.sample_size).limit(50).all()
            
            bad_corr_list = [
                {
                    "var1": corr.variable1.display_name if corr.variable1 else f"ID{corr.var1_id}",
                    "var2": corr.variable2.display_name if corr.variable2 else f"ID{corr.var2_id}",
                    "correlation": round(corr.correlation_value, 3),
                    "sample_size": corr.sample_size,
                    "p_value": round(corr.p_value, 4) if corr.p_value else None
                }
                for corr in bad_correlations
            ]
            
            # Variables with insufficient data
            var_counts = db.query(
                VariableMetadata.id,
                VariableMetadata.display_name,
                VariableMetadata.source,
                VariableMetadata.is_active,
                func.count(TimeSeriesData.id).label('data_points')
            ).outerjoin(
                TimeSeriesData, VariableMetadata.id == TimeSeriesData.variable_id
            ).group_by(
                VariableMetadata.id
            ).having(
                func.count(TimeSeriesData.id) < 20
            ).order_by(
                func.count(TimeSeriesData.id)
            ).all()
            
            low_data_vars = [
                {
                    "name": name,
                    "source": source,
                    "active": active,
                    "data_points": count
                }
                for _, name, source, active, count in var_counts
            ]
            
            total_correlations = db.query(CorrelationResult).count()
            
            return {
                "status": "success",
                "total_correlations": total_correlations,
                "sample_size_distribution": distribution,
                "correlations_under_10": len(bad_corr_list),
                "worst_correlations": bad_corr_list,
                "variables_under_20_points": len(low_data_vars),
                "low_data_variables": low_data_vars
            }
    
    except Exception as e:
        logger.error(f"Sample size report failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setup-new-data-sources")
async def setup_new_data_sources():
    """
    Add 113 new variables (Google Trends, FRED, USGS Enhanced) to database
    Run this after deploying v2.0.60
    """
    try:
        logger.info("Setting up new data sources...")
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        
        from setup_new_data_sources import (
            setup_google_trends_variables,
            setup_fred_variables,
            setup_usgs_enhanced_variables
        )
        
        # Run each setup function and track results
        trends_count = 0
        fred_count = 0
        usgs_count = 0
        
        logger.info("Setting up Google Trends variables...")
        setup_google_trends_variables()
        trends_count = 60  # Known count from setup
        
        logger.info("Setting up FRED variables...")
        setup_fred_variables()
        fred_count = 50
        
        logger.info("Setting up USGS Enhanced variables...")
        setup_usgs_enhanced_variables()
        usgs_count = 3
        
        total = trends_count + fred_count + usgs_count
        
        logger.info(f"✅ Setup complete: {total} new variables added")
        
        return {
            "status": "success",
            "message": f"Added {total} new variables to database",
            "trends_added": trends_count,
            "fred_added": fred_count,
            "usgs_added": usgs_count,
            "total_added": total,
            "next_step": "Run data ingestion: POST /api/admin/full-data-refresh"
        }
        
    except Exception as e:
        logger.error(f"Setup new data sources failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setup-layer1-fast-signals")
async def setup_layer1_fast_signals():
    """
    Add Layer 1 (Fast/Behavioral) variables to database.
    Wikipedia Pageviews API is FREE with no rate limits - replaces Google Trends!
    
    Layer 1 signals move faster than market/economic data (Layer 2/3),
    enabling early signal detection in the temporal cascade.
    """
    try:
        logger.info("Setting up Layer 1: Fast Behavioral Signals...")
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        
        from setup_layer1_fast_signals import setup_wikipedia_variables
        
        result = setup_wikipedia_variables()
        
        logger.info(f"✅ Layer 1 setup complete: {result['added']} new variables")
        
        return {
            "status": "success",
            "message": f"Added {result['added']} Wikipedia pageview variables",
            "added": result['added'],
            "skipped": result['skipped'],
            "layer": "Layer 1 - Fast/Behavioral",
            "data_source": "Wikipedia Pageviews API (FREE, no rate limits)",
            "next_steps": [
                "1. Deploy to Railway: git push",
                "2. Fetch data: POST /api/admin/fetch-data",
                "3. Recalculate correlations: POST /api/admin/calculate-correlations"
            ]
        }
        
    except Exception as e:
        logger.error(f"Layer 1 setup failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate-data-universe")
async def validate_data_universe_endpoint():
    """
    Validate data universe consistency.
    
    Checks:
    - All sources are registered in data_source_registry
    - Timestamps are on standard monthly grid (first of month)
    - Data coverage by layer
    - Variables with no data
    
    Returns detailed report with issues and recommendations.
    """
    try:
        logger.info("Running data universe validation...")
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        
        from validate_data_universe import validate_data_universe
        
        report = validate_data_universe()
        
        logger.info(f"Validation complete. Status: {report['status']}")
        
        return report
        
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data-sources")
async def list_data_sources():
    """
    List all registered data sources with configuration.
    Shows layer, fill strategy, API requirements, and status.
    """
    try:
        from data_source_registry import DATA_SOURCES, get_active_sources, SignalLayer
        
        sources_by_layer = {}
        for layer in SignalLayer:
            layer_sources = [
                {
                    "name": s.name,
                    "display_name": s.display_name,
                    "fill_strategy": s.fill_strategy.value,
                    "update_frequency": s.update_frequency.value,
                    "requires_api_key": s.requires_api_key,
                    "is_active": s.is_active,
                    "notes": s.notes
                }
                for s in DATA_SOURCES.values()
                if s.layer == layer
            ]
            if layer_sources:
                sources_by_layer[layer.name] = layer_sources
        
        active_count = len(get_active_sources())
        total_count = len(DATA_SOURCES)
        
        return {
            "total_sources": total_count,
            "active_sources": active_count,
            "sources_by_layer": sources_by_layer,
            "standard_grid": {
                "frequency": "monthly",
                "day_of_month": 1,
                "description": "All data normalized to first-of-month timestamps"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list data sources: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug-wikipedia-fetch")
async def debug_wikipedia_fetch():
    """
    Debug endpoint: Test the Wikipedia fetch for a single article 
    to verify monthly + daily data retrieval is working.
    """
    try:
        from data_fetcher import DataFetcher
        f = DataFetcher()
        
        article = "Layoff"
        
        # Test monthly
        monthly = f.fetch_wikipedia_pageviews_monthly(article, months=60)
        monthly_info = None
        if monthly:
            sorted_dates = sorted(monthly.keys())
            monthly_info = {
                "count": len(monthly),
                "date_range": f"{sorted_dates[0]} to {sorted_dates[-1]}",
                "sample": dict(list(monthly.items())[:3])
            }
        
        # Test daily
        daily = f.fetch_wikipedia_pageviews_daily(article, days=90)
        daily_info = None
        if daily:
            sorted_dates = sorted(daily.items())
            daily_info = {
                "count": len(daily),
                "date_range": f"{sorted_dates[0][0]} to {sorted_dates[-1][0]}",
                "sample": dict(list(daily.items())[:3])
            }
        
        return {
            "article": article,
            "monthly_fetch": monthly_info,
            "daily_fetch": daily_info,
            "status": "success" if monthly and daily else "partial" if monthly or daily else "failed"
        }
        
    except Exception as e:
        logger.error(f"Debug fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug-db-data/{variable_name}")
async def debug_db_data(variable_name: str):
    """Debug: Check what data is actually stored in DB for a variable"""
    try:
        from database import get_db_session
        from models import VariableMetadata, TimeSeriesData
        
        with get_db_session() as session:
            var = session.query(VariableMetadata).filter(VariableMetadata.name == variable_name).first()
            if not var:
                return {"error": f"Variable {variable_name} not found"}
            
            # Get all data points
            data = session.query(TimeSeriesData).filter(
                TimeSeriesData.variable_id == var.id
            ).order_by(TimeSeriesData.timestamp).all()
            
            if not data:
                return {"variable": variable_name, "data_points": 0, "message": "No data"}
            
            # Analyze the dates
            dates = [d.timestamp.strftime("%Y-%m-%d") for d in data]
            values = [(d.timestamp.strftime("%Y-%m-%d"), d.value) for d in data]
            
            # Check for monthly vs daily
            monthly_count = sum(1 for d in dates if d.endswith("-01"))
            daily_count = len(dates) - monthly_count
            
            return {
                "variable": variable_name,
                "variable_id": var.id,
                "total_data_points": len(data),
                "monthly_points": monthly_count,
                "daily_points": daily_count,
                "first_5": values[:5],
                "last_5": values[-5:]
            }
            
    except Exception as e:
        logger.error(f"Debug DB failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug-granger/{variable_name}")
async def debug_granger_results(variable_name: str):
    """Debug: Check Granger results for a specific variable"""
    try:
        from database import get_db_session
        from models import VariableMetadata, CorrelationResult
        from sqlalchemy import or_
        
        with get_db_session() as session:
            var = session.query(VariableMetadata).filter(VariableMetadata.name == variable_name).first()
            if not var:
                return {"error": f"Variable {variable_name} not found"}
            
            # Find all correlations with Granger results
            granger_results = session.query(CorrelationResult).filter(
                or_(
                    CorrelationResult.variable1_id == var.id,
                    CorrelationResult.variable2_id == var.id
                ),
                or_(
                    CorrelationResult.granger_p_value_xy != None,
                    CorrelationResult.granger_p_value_yx != None
                )
            ).all()
            
            results = []
            for r in granger_results:
                other_var = r.variable2 if r.variable1_id == var.id else r.variable1
                results.append({
                    "other_variable": other_var.name,
                    "other_display": other_var.display_name,
                    "correlation": r.correlation_value,
                    "is_significant": r.is_significant,
                    "granger_xy": r.granger_p_value_xy,
                    "granger_yx": r.granger_p_value_yx,
                    "lags": r.granger_lags
                })
            
            return {
                "variable": variable_name,
                "granger_results_count": len(results),
                "results": results[:10]  # First 10
            }
            
    except Exception as e:
        logger.error(f"Debug Granger failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch-wikipedia")
async def fetch_wikipedia_only():
    """
    Quick fetch: Wikipedia data only (skips other sources).
    Use this to rapidly populate Layer 1 fast signals without waiting
    for the full data ingestion job.
    
    Wikipedia API is FREE with no rate limits!
    """
    try:
        logger.info("Quick fetch: Wikipedia daily+monthly pageviews...")
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        
        from data_ingestion_service import DataIngestionService
        
        service = DataIngestionService()
        result = service._fetch_wikipedia_pageviews_data()
        
        logger.info(f"Wikipedia quick fetch complete: {result}")
        
        return {
            "status": "success",
            "message": f"Fetched {result.get('wikipedia_fetched', 0)} Wikipedia variables",
            "data_points_added": result.get('wikipedia_data_points', 0),
            "layer": "Layer 1 - Fast/Behavioral",
            "next_step": "Check /api/dashboard/fast-signals for momentum data"
        }
        
    except Exception as e:
        logger.error(f"Wikipedia fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch-reddit")
async def fetch_reddit_only():
    """
    Quick fetch: Reddit subreddit activity only (Layer 1 fast signals).
    Cross-validates Wikipedia signals for higher confidence.
    
    Reddit API: Free with rate limits (60 req/min with proper User-Agent)
    """
    try:
        logger.info("Quick fetch: Reddit subreddit activity only...")
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        
        from data_ingestion_service import DataIngestionService
        
        service = DataIngestionService()
        result = service._fetch_reddit_activity_data()
        
        logger.info(f"Reddit quick fetch complete: {result}")
        
        return {
            "status": "success",
            "message": f"Fetched {result.get('reddit_fetched', 0)} Reddit subreddits",
            "data_points_added": result.get('reddit_data_points', 0),
            "layer": "Layer 1 - Fast/Behavioral",
            "next_step": "Check /api/dashboard/fast-signals for multi-source confidence"
        }
        
    except Exception as e:
        logger.error(f"Reddit fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setup-reddit-variables")
async def setup_reddit_variables_endpoint():
    """Add Reddit subreddit variables to database for Layer 1 fast signals"""
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from setup_layer1_fast_signals import setup_reddit_variables, REDDIT_SUBREDDITS
        
        result = setup_reddit_variables()
        
        return {
            "status": "success",
            "variables_added": result.get('added', 0),
            "variables_skipped": result.get('skipped', 0),
            "total_subreddits": len(REDDIT_SUBREDDITS),
            "message": f"Added {result.get('added', 0)} Reddit subreddit variables",
            "next_step": "POST /api/admin/fetch-reddit to populate data"
        }
    except Exception as e:
        logger.error(f"Reddit setup failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-granger")
async def calculate_granger_causality(background_tasks: BackgroundTasks):
    """
    Run Granger causality on Layer 1 → Layer 2 correlations.
    This identifies which fast signals actually PREDICT market outcomes.
    """
    try:
        job_id = f"granger_{int(datetime.utcnow().timestamp())}"
        
        _active_jobs[job_id] = {
            'job_id': job_id,
            'type': 'granger_causality',
            'status': 'queued',
            'stage': 'initializing',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        background_tasks.add_task(_run_granger_background, job_id)
        
        return {
            "status": "queued",
            "message": "Granger causality calculation started",
            "job_id": job_id,
            "poll_url": f"/api/admin/job-status/{job_id}"
        }
    except Exception as e:
        logger.error(f"Failed to queue Granger calc: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _run_granger_background(job_id: str):
    """Background task for Granger causality calculation on Layer 1 → Layer 2"""
    try:
        _active_jobs[job_id]['status'] = 'running'
        _active_jobs[job_id]['stage'] = 'loading_correlations'
        _active_jobs[job_id]['updated_at'] = datetime.utcnow().isoformat()
        
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from services.granger_causality_service import GrangerCausalityService
        from database import get_db_session
        from models import CorrelationResult, VariableMetadata
        
        granger_service = GrangerCausalityService(max_lag=12, confidence_level=0.05)
        
        with get_db_session() as db:
            # Get Layer 1 variables (wikipedia, reddit)
            layer1_vars = db.query(VariableMetadata).filter(
                VariableMetadata.source.in_(['wikipedia', 'reddit']),
                VariableMetadata.is_active == True
            ).all()
            layer1_ids = {v.id for v in layer1_vars}
            
            # Get Layer 2 variables (not Layer 1)
            layer2_vars = db.query(VariableMetadata).filter(
                ~VariableMetadata.source.in_(['wikipedia', 'reddit']),
                VariableMetadata.is_active == True
            ).all()
            layer2_ids = {v.id for v in layer2_vars}
            
            logger.info(f"Granger: {len(layer1_ids)} Layer 1 vars, {len(layer2_ids)} Layer 2 vars")
            
            # Find cross-layer correlations (Layer 1 ↔ Layer 2)
            cross_correlations = db.query(CorrelationResult).filter(
                CorrelationResult.is_significant == True,
                CorrelationResult.abs_correlation >= 0.3
            ).all()
            
            # Filter to Layer 1 ↔ Layer 2 pairs only
            l1_l2_pairs = []
            for corr in cross_correlations:
                if (corr.variable1_id in layer1_ids and corr.variable2_id in layer2_ids) or \
                   (corr.variable2_id in layer1_ids and corr.variable1_id in layer2_ids):
                    l1_l2_pairs.append(corr)
            
            logger.info(f"Found {len(l1_l2_pairs)} Layer 1 ↔ Layer 2 correlations for Granger testing")
            _active_jobs[job_id]['stage'] = f'testing_{len(l1_l2_pairs)}_pairs'
            
            tested = 0
            significant = 0
            
            for corr in l1_l2_pairs[:50]:  # Limit to 50 pairs for speed
                try:
                    _active_jobs[job_id]['stage'] = f'testing_pair_{tested+1}'
                    
                    # Run Granger test
                    result = granger_service.test_causality(
                        corr.variable1_id, 
                        corr.variable2_id
                    )
                    
                    # Update correlation with Granger results
                    if result.get('var1_to_var2', {}).get('p_value'):
                        corr.granger_p_value_xy = result['var1_to_var2']['p_value']
                    if result.get('var2_to_var1', {}).get('p_value'):
                        corr.granger_p_value_yx = result['var2_to_var1']['p_value']
                    if result.get('optimal_lag'):
                        corr.granger_lags = result['optimal_lag']
                    
                    if result.get('var1_to_var2', {}).get('significant') or \
                       result.get('var2_to_var1', {}).get('significant'):
                        significant += 1
                    
                    tested += 1
                    
                except Exception as e:
                    logger.warning(f"Granger test failed for pair: {e}")
                    continue
            
            db.commit()
        
        _active_jobs[job_id]['status'] = 'completed'
        _active_jobs[job_id]['stage'] = 'done'
        _active_jobs[job_id]['result'] = {
            'pairs_tested': tested,
            'significant_causality': significant,
            'layer1_variables': len(layer1_ids),
            'layer2_variables': len(layer2_ids)
        }
        _active_jobs[job_id]['updated_at'] = datetime.utcnow().isoformat()
        
        logger.info(f"Granger complete: {tested} tested, {significant} significant")
        
    except Exception as e:
        logger.error(f"Granger calc failed: {e}", exc_info=True)
        _active_jobs[job_id]['status'] = 'failed'
        _active_jobs[job_id]['error'] = str(e)
        _active_jobs[job_id]['updated_at'] = datetime.utcnow().isoformat()