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

        try:
            from migrations.add_exploitation_recommendations_table import upgrade as run_exploitation_migration
            run_exploitation_migration()
            logger.info("✅ Exploitation recommendations migration complete")
        except Exception as e:
            logger.warning(f"Exploitation migration may have already run: {e}")

        try:
            from migrations.add_prediction_accuracy_columns import upgrade as run_pred_accuracy_migration
            run_pred_accuracy_migration()
            logger.info("✅ Prediction accuracy columns migration complete")
        except Exception as e:
            logger.warning(f"Prediction accuracy migration may have already run: {e}")

        try:
            from migrations.add_target_growth_actual import upgrade as run_target_growth_migration
            run_target_growth_migration()
            logger.info("✅ Target growth actual migration complete")
        except Exception as e:
            logger.warning(f"Target growth migration may have already run: {e}")

        try:
            from migrations.add_revenue_events_table import upgrade as run_revenue_events_migration
            run_revenue_events_migration()
            logger.info("✅ Revenue events table migration complete")
        except Exception as e:
            logger.warning(f"Revenue events migration may have already run: {e}")

        try:
            from migrations.add_commercial_intelligence_tables import upgrade as run_commercial_migration
            run_commercial_migration()
            logger.info("✅ Commercial intelligence tables migration complete")
        except Exception as e:
            logger.warning(f"Commercial intelligence migration may have already run: {e}")

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
            logger.warning(
                f"Granger migration error (may already be applied): {e}")

        # Run exploitation recommendations migration
        try:
            from migrations.add_exploitation_recommendations_table import upgrade as run_exploitation_migration
            run_exploitation_migration()
            migrations_run.append("add_exploitation_recommendations_table")
            logger.info("✅ Exploitation recommendations migration complete")
        except Exception as e:
            logger.warning(
                f"Exploitation migration error (may already be applied): {e}")

        # Run prediction accuracy columns migration
        try:
            from migrations.add_prediction_accuracy_columns import upgrade as run_pred_accuracy_migration
            run_pred_accuracy_migration()
            migrations_run.append("add_prediction_accuracy_columns")
            logger.info("✅ Prediction accuracy columns migration complete")
        except Exception as e:
            logger.warning(
                f"Prediction accuracy migration error (may already be applied): {e}")

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
            logger.info(
                f"Job {job_id}: Force refetch - deleting existing time series data...")

            with get_db_session() as session:
                deleted_count = session.query(TimeSeriesData).delete()
                session.commit()
                logger.info(
                    f"Job {job_id}: Deleted {deleted_count} existing data points")
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
        logger.error(
            f"Job {job_id}: Data ingestion failed: {e}", exc_info=True)
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
        logger.error(
            f"Job {job_id}: Correlation calc failed: {e}", exc_info=True)
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


def _run_backtest_background(job_id: str, months_back: int = 24, max_pairs: int = 0, use_regression: bool = False):
    """Walk-forward backtest: recompute correlations at each historical point and validate.
    
    Args:
        use_regression: If True, use OLS regression slope for predictions (model_version='backtest_regression').
                       If False, use |correlation| * |momentum| formula (model_version='backtest_walkforward').
    """
    import uuid
    import warnings
    import numpy as np
    import pandas as pd
    from scipy.stats import pearsonr
    from datetime import timedelta

    mv_label = 'backtest_regression' if use_regression else 'backtest_walkforward'

    try:
        _active_jobs[job_id]['status'] = 'running'
        _active_jobs[job_id]['stage'] = 'loading_data'
        _active_jobs[job_id]['updated_at'] = datetime.utcnow().isoformat()

        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from database import get_db_session
        from models import ExploitationRecommendation, VariableMetadata, TimeSeriesData, PredictionTracking

        try:
            from statsmodels.tsa.stattools import grangercausalitytests
            granger_available = True
        except ImportError:
            granger_available = False
            logger.warning("statsmodels not available for backtest Granger tests")

        with get_db_session() as db:
            # Get all exploitation recommendation pairs
            recs = db.query(ExploitationRecommendation).all()
            if max_pairs > 0:
                recs = recs[:max_pairs]

            total_pairs = len(recs)
            logger.info(f"Job {job_id}: Starting walk-forward backtest with {total_pairs} pairs, {months_back} months")
            _active_jobs[job_id]['total_pairs'] = total_pairs

            # Build variable lookup: display_name -> (id, name)
            all_vars = db.query(VariableMetadata).filter(VariableMetadata.is_active == True).all()
            var_by_display = {v.display_name: v for v in all_vars}
            var_by_name = {v.name: v for v in all_vars}

            # Pre-fetch all time series data keyed by variable_id
            from sqlalchemy import asc
            all_ts = db.query(TimeSeriesData).order_by(asc(TimeSeriesData.timestamp)).all()
            ts_by_var = {}
            for ts in all_ts:
                ts_by_var.setdefault(ts.variable_id, []).append((ts.timestamp, ts.value))
            del all_ts  # Free memory

            now = datetime.utcnow()
            predictions_created = 0
            predictions_skipped = 0
            direction_correct_count = 0
            direction_total = 0

            for pair_idx, rec in enumerate(recs):
                try:
                    # Resolve variable IDs
                    sig_var = var_by_display.get(rec.signal_display_name) or var_by_name.get(rec.signal_name)
                    tgt_var = var_by_display.get(rec.target_display_name) or var_by_name.get(rec.target_name)
                    if not sig_var or not tgt_var:
                        predictions_skipped += 1
                        continue

                    sig_ts = ts_by_var.get(sig_var.id)
                    tgt_ts = ts_by_var.get(tgt_var.id)
                    if not sig_ts or not tgt_ts:
                        predictions_skipped += 1
                        continue

                    # Convert to pandas Series
                    sig_series = pd.Series(
                        [v for _, v in sig_ts],
                        index=pd.DatetimeIndex([t for t, _ in sig_ts])
                    ).sort_index()
                    tgt_series = pd.Series(
                        [v for _, v in tgt_ts],
                        index=pd.DatetimeIndex([t for t, _ in tgt_ts])
                    ).sort_index()

                    lag_months = rec.optimal_lag or 1
                    lag_days = lag_months * 30

                    # Walk-forward: step backward from 2 months ago to months_back
                    for m in range(2, months_back + 1):
                        prediction_date = now - timedelta(days=m * 30)
                        target_date = prediction_date + timedelta(days=lag_days)

                        # Must have actual data after target_date
                        if target_date > now - timedelta(days=15):
                            continue

                        # Slice data to only what was available at prediction_date
                        sig_slice = sig_series[sig_series.index <= prediction_date]
                        tgt_slice = tgt_series[tgt_series.index <= prediction_date]

                        # Align
                        aligned = pd.DataFrame({'sig': sig_slice, 'tgt': tgt_slice}).sort_index()
                        aligned = aligned.interpolate(method='time', limit_direction='both').dropna()

                        if len(aligned) < 30:
                            continue

                        x = aligned['sig'].values
                        y = aligned['tgt'].values

                        # Compute correlation
                        try:
                            corr, p_val = pearsonr(x, y)
                        except Exception:
                            continue

                        if p_val is None or p_val >= 0.05:
                            continue

                        # Compute Granger
                        granger_p = None
                        granger_lag = lag_months
                        if granger_available and len(aligned) >= 30:
                            try:
                                max_lag = min(4, len(aligned) // 10)
                                if max_lag < 1:
                                    max_lag = 1
                                with warnings.catch_warnings():
                                    warnings.simplefilter("ignore")
                                    data_xy = np.column_stack([y, x])
                                    results = grangercausalitytests(data_xy, maxlag=max_lag, verbose=False)
                                    best_p = 1.0
                                    for lag in range(1, max_lag + 1):
                                        if lag in results:
                                            p = results[lag][0]['ssr_ftest'][1]
                                            if p < best_p:
                                                best_p = p
                                                granger_lag = lag
                                    granger_p = float(best_p)
                            except Exception:
                                granger_p = None

                        if granger_p is not None and granger_p >= 0.05:
                            continue  # Walk-forward: only keep if Granger significant at this point

                        # Compute momentum at prediction_date
                        sig_at_pred = sig_slice.iloc[-1] if len(sig_slice) > 0 else None
                        sig_prev = sig_slice.iloc[-2] if len(sig_slice) > 1 else sig_at_pred
                        if sig_at_pred is None or sig_prev is None or sig_prev == 0:
                            continue
                        momentum = ((sig_at_pred - sig_prev) / abs(sig_prev)) * 100

                        # Baseline target value at prediction_date
                        baseline = tgt_slice.iloc[-1] if len(tgt_slice) > 0 else None
                        if baseline is None or baseline == 0:
                            continue

                        if use_regression:
                            # OLS regression: shift x/y by lag, compute slope
                            lag_shift = max(1, lag_months)
                            if len(x) <= lag_shift + 10:
                                continue
                            x_reg = x[:-lag_shift]
                            y_reg = y[lag_shift:]
                            x_mean = float(np.mean(x_reg))
                            x_var = float(np.sum((x_reg - x_mean) ** 2))
                            if x_var == 0:
                                continue
                            slope = float(np.sum((x_reg - x_mean) * (y_reg - np.mean(y_reg))) / x_var)
                            y_pred_reg = slope * x_reg + (np.mean(y_reg) - slope * x_mean)
                            ss_res = float(np.sum((y_reg - y_pred_reg) ** 2))
                            ss_tot = float(np.sum((y_reg - np.mean(y_reg)) ** 2))
                            r_sq = 1 - ss_res / ss_tot if ss_tot > 0 else 0

                            # Prediction: slope * actual signal change
                            signal_change = (momentum / 100.0) * abs(float(sig_at_pred))
                            predicted_change = slope * signal_change
                            predicted_change_pct = round(abs(predicted_change / baseline) * 100, 2)
                            predicted_value = baseline + predicted_change

                            # Direction from sign of predicted change
                            if predicted_change > 0:
                                predicted_direction = 'up'
                            elif predicted_change < 0:
                                predicted_direction = 'down'
                            else:
                                predicted_direction = 'up' if corr > 0 else 'down'
                        else:
                            # Original formula: |correlation| * |momentum|
                            r_sq = corr ** 2
                            if momentum > 0:
                                predicted_direction = 'up' if corr > 0 else 'down'
                            else:
                                predicted_direction = 'down' if corr > 0 else 'up'
                            predicted_change_pct = round(abs(corr) * abs(momentum), 2)
                            predicted_value = baseline * (1 + predicted_change_pct / 100)

                        # Get actual value near target_date (±15 day window for monthly data)
                        tgt_near_target = tgt_series[
                            (tgt_series.index >= target_date - timedelta(days=15)) &
                            (tgt_series.index <= target_date + timedelta(days=15))
                        ]
                        if len(tgt_near_target) == 0:
                            # Fallback: nearest point before target_date
                            tgt_before = tgt_series[tgt_series.index <= target_date + timedelta(days=30)]
                            if len(tgt_before) == 0:
                                continue
                            actual_value = float(tgt_before.iloc[-1])
                        else:
                            # Pick closest to target_date
                            diffs = abs(tgt_near_target.index - target_date)
                            actual_value = float(tgt_near_target.iloc[diffs.argmin()])

                        # Compute accuracy metrics
                        actual_direction = 'up' if actual_value > baseline else 'down'
                        direction_correct = (actual_direction == predicted_direction)
                        value_error_pct = abs((actual_value - predicted_value) / abs(baseline)) * 100
                        actual_change_pct_val = ((actual_value - baseline) / abs(baseline)) * 100

                        # Compute actual lag (peak/trough scan)
                        scan_end = prediction_date + timedelta(days=max(lag_days * 2, 60))
                        tgt_scan = tgt_series[
                            (tgt_series.index >= prediction_date) &
                            (tgt_series.index <= scan_end)
                        ]
                        actual_lag_days_val = None
                        lag_error_days_val = None
                        if len(tgt_scan) > 0:
                            if predicted_direction == 'up':
                                peak_idx = tgt_scan.idxmax()
                            else:
                                peak_idx = tgt_scan.idxmin()
                            actual_lag_days_val = (peak_idx - prediction_date).days
                            lag_error_days_val = actual_lag_days_val - lag_days

                        # Dedup check
                        existing = db.query(PredictionTracking).filter(
                            PredictionTracking.signal_name == rec.signal_display_name,
                            PredictionTracking.target_name == rec.target_display_name,
                            PredictionTracking.model_version == mv_label,
                            PredictionTracking.predicted_at >= prediction_date - timedelta(days=2),
                            PredictionTracking.predicted_at <= prediction_date + timedelta(days=2),
                        ).first()
                        if existing:
                            predictions_skipped += 1
                            continue

                        # Create validated prediction record
                        pred = PredictionTracking(
                            prediction_id=str(uuid.uuid4())[:12],
                            signal_name=rec.signal_display_name or rec.signal_name,
                            target_name=rec.target_display_name or rec.target_name,
                            predicted_at=prediction_date,
                            target_date=target_date,
                            optimal_lag_days=lag_days,
                            predicted_direction=predicted_direction,
                            predicted_value=round(predicted_value, 4),
                            predicted_change_pct=predicted_change_pct,
                            current_target_value=round(float(baseline), 4),
                            current_signal_value=round(float(sig_at_pred), 4),
                            signal_momentum=round(momentum, 2),
                            r_squared=round(r_sq, 6),
                            confidence='high' if r_sq > 0.25 else 'medium' if r_sq > 0.09 else 'low',
                            model_version=mv_label,
                            actual_value=round(actual_value, 4),
                            actual_direction=actual_direction,
                            direction_correct=direction_correct,
                            value_error_pct=round(value_error_pct, 2),
                            actual_change_pct=round(actual_change_pct_val, 2),
                            actual_lag_days=actual_lag_days_val,
                            lag_error_days=lag_error_days_val,
                            granger_p_value=granger_p,
                            target_source=rec.target_source or 'unknown',
                            status='validated',
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                        )
                        db.add(pred)
                        predictions_created += 1
                        if direction_correct:
                            direction_correct_count += 1
                        direction_total += 1

                        # Batch commit every 50 records
                        if predictions_created % 50 == 0:
                            db.commit()

                except Exception as e:
                    logger.warning(f"Job {job_id}: Pair {pair_idx} failed: {e}")
                    predictions_skipped += 1
                    continue

                # Update progress
                if (pair_idx + 1) % 10 == 0 or pair_idx == total_pairs - 1:
                    pct = round((pair_idx + 1) / total_pairs * 100, 1)
                    _active_jobs[job_id]['stage'] = f'pair {pair_idx + 1}/{total_pairs} ({pct}%)'
                    _active_jobs[job_id]['predictions_created'] = predictions_created
                    _active_jobs[job_id]['updated_at'] = datetime.utcnow().isoformat()

            # Final commit
            db.commit()

        direction_accuracy = round(direction_correct_count / max(1, direction_total) * 100, 1)

        _active_jobs[job_id]['status'] = 'completed'
        _active_jobs[job_id]['stage'] = 'done'
        _active_jobs[job_id]['result'] = {
            'predictions_created': predictions_created,
            'predictions_skipped': predictions_skipped,
            'direction_accuracy': direction_accuracy,
            'direction_correct': direction_correct_count,
            'direction_total': direction_total,
            'total_pairs': total_pairs,
            'months_back': months_back,
        }
        _active_jobs[job_id]['updated_at'] = datetime.utcnow().isoformat()

        logger.info(f"Job {job_id}: ✅ Backtest complete! {predictions_created} predictions created, {direction_accuracy}% direction accuracy")

    except Exception as e:
        logger.error(f"Job {job_id}: Backtest failed: {e}", exc_info=True)
        _active_jobs[job_id]['status'] = 'failed'
        _active_jobs[job_id]['error'] = str(e)
        _active_jobs[job_id]['updated_at'] = datetime.utcnow().isoformat()


@router.post("/run-backtest")
async def run_backtest(
    background_tasks: BackgroundTasks,
    months_back: int = 24,
    max_pairs: int = 0,
    use_regression: bool = False,
):
    """Run walk-forward historical backtest in background.
    
    Uses existing exploitation recommendation pairs, recomputes correlations
    and Granger tests at each historical point using only data available at
    that time, generates predictions, and immediately validates against
    known outcomes.
    
    Args:
        months_back: How many months to backtest (default 24)
        max_pairs: Max signal-target pairs to process (0 = all)
        use_regression: If True, use OLS regression slope instead of |corr|*|momentum|
    """
    job_id = f"backtest_{int(datetime.utcnow().timestamp())}"

    _active_jobs[job_id] = {
        'job_id': job_id,
        'type': 'backtest',
        'status': 'queued',
        'stage': 'initializing',
        'months_back': months_back,
        'max_pairs': max_pairs,
        'predictions_created': 0,
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
    }

    background_tasks.add_task(_run_backtest_background, job_id, months_back, max_pairs, use_regression)

    formula = 'OLS regression slope' if use_regression else '|corr|*|momentum|'
    logger.info(f"Job {job_id}: Queued walk-forward backtest ({months_back} months, max_pairs={max_pairs}, formula={formula})")

    return JSONResponse({
        "status": "queued",
        "message": f"Walk-forward backtest started ({months_back} months, {max_pairs or 'all'} pairs, formula: {formula})",
        "job_id": job_id,
        "poll_url": f"/api/admin/job-status/{job_id}",
    })


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

            vars_with_data = db.query(func.count(
                func.distinct(TimeSeriesData.variable_id))).scalar()

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

            # Variables by source - dynamically get all sources
            source_query = db.query(
                VariableMetadata.source,
                func.count(VariableMetadata.id)
            ).filter(
                VariableMetadata.is_active.is_(True)
            ).group_by(VariableMetadata.source).all()

            source_dist = {source: count for source,
                           count in source_query if source}

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
        "POSTGRES_DB_prefix": os.getenv('POSTGRES_DB', '')[:30] if os.getenv('POSTGRES_DB') else None,
        # API Keys
        "FRED_API_KEY_exists": bool(os.getenv('FRED_API_KEY')),
        "FRED_API_KEY_prefix": os.getenv('FRED_API_KEY', '')[:8] + '...' if os.getenv('FRED_API_KEY') else None,
        "ALPHA_VANTAGE_API_KEY_exists": bool(os.getenv('ALPHA_VANTAGE_API_KEY')),
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
            current_vars = len(
                [v for v in var_stats if v['days_old'] and v['days_old'] <= 30])
            stale_vars = len(
                [v for v in var_stats if v['days_old'] and v['days_old'] > 30])
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


@router.post("/disable-google-trends")
async def disable_google_trends_variables():
    """
    Disable all Google Trends variables - pytrends is blocked from data centers.
    """
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from database import get_db_session
        from models import VariableMetadata

        disabled_count = 0
        with get_db_session() as session:
            trends_vars = session.query(VariableMetadata).filter(
                VariableMetadata.source == 'google_trends',
                VariableMetadata.is_active == True
            ).all()

            for var in trends_vars:
                var.is_active = False
                disabled_count += 1

            session.commit()

        return {
            "status": "success",
            "message": f"Disabled {disabled_count} Google Trends variables",
            "reason": "pytrends is blocked from data centers - use Wikipedia pageviews instead"
        }

    except Exception as e:
        logger.error(f"Error disabling Google Trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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

        logger.info(
            f"✅ Layer 1 setup complete: {result['added']} new variables")

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
            var = session.query(VariableMetadata).filter(
                VariableMetadata.name == variable_name).first()
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
            values = [(d.timestamp.strftime("%Y-%m-%d"), d.value)
                      for d in data]

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
            var = session.query(VariableMetadata).filter(
                VariableMetadata.name == variable_name).first()
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
                is_var1 = r.variable1_id == var.id
                results.append({
                    "other_variable": other_var.name,
                    "other_display": other_var.display_name,
                    "correlation": r.correlation_value,
                    "is_significant": r.is_significant,
                    "granger_xy": r.granger_p_value_xy,
                    "granger_yx": r.granger_p_value_yx,
                    "lags": r.granger_lags,
                    "is_var1": is_var1,
                    "var1_id": r.variable1_id,
                    "var2_id": r.variable2_id
                })

            return {
                "variable": variable_name,
                "granger_results_count": len(results),
                "results": results[:10]  # First 10
            }

    except Exception as e:
        logger.error(f"Debug Granger failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/significant-granger")
async def get_significant_granger():
    """List all significant Granger causality pairs (p < 0.05)"""
    try:
        from database import get_db_session
        from models import CorrelationResult
        from sqlalchemy import or_

        with get_db_session() as session:
            # Find all correlations with significant Granger
            sig_results = session.query(CorrelationResult).filter(
                or_(
                    CorrelationResult.granger_p_value_xy < 0.05,
                    CorrelationResult.granger_p_value_yx < 0.05
                )
            ).all()

            results = []
            for r in sig_results:
                if r.granger_p_value_xy and r.granger_p_value_xy < 0.05:
                    results.append({
                        "cause": r.variable1.display_name if r.variable1 else "Unknown",
                        "cause_name": r.variable1.name if r.variable1 else None,
                        "effect": r.variable2.display_name if r.variable2 else "Unknown",
                        "effect_name": r.variable2.name if r.variable2 else None,
                        "p_value": r.granger_p_value_xy,
                        "correlation": r.correlation_value,
                        "direction": "X->Y"
                    })
                if r.granger_p_value_yx and r.granger_p_value_yx < 0.05:
                    results.append({
                        "cause": r.variable2.display_name if r.variable2 else "Unknown",
                        "cause_name": r.variable2.name if r.variable2 else None,
                        "effect": r.variable1.display_name if r.variable1 else "Unknown",
                        "effect_name": r.variable1.name if r.variable1 else None,
                        "p_value": r.granger_p_value_yx,
                        "correlation": r.correlation_value,
                        "direction": "Y->X"
                    })

            # Sort by p_value
            results.sort(key=lambda x: x["p_value"])

            return {
                "total_significant": len(results),
                "results": results[:25]  # Top 25
            }

    except Exception as e:
        logger.error(f"Significant Granger query failed: {e}", exc_info=True)
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


@router.post("/fetch-reddit-historical")
async def fetch_reddit_historical():
    """
    Fetch extended Reddit data by combining multiple listings (new, hot, top).
    This provides more data points for proper momentum calculation.
    """
    try:
        from database import get_db_session
        from models import VariableMetadata, TimeSeriesData
        from data_fetcher import DataFetcher
        from datetime import datetime

        fetcher = DataFetcher()
        total_points = 0
        success_count = 0

        with get_db_session() as session:
            # Get all Reddit variables
            reddit_vars = session.query(VariableMetadata).filter(
                VariableMetadata.source == 'reddit',
                VariableMetadata.is_active == True
            ).all()

            logger.info(
                f"Fetching historical data for {len(reddit_vars)} Reddit variables")

            for var in reddit_vars:
                try:
                    import json
                    params = json.loads(
                        var.parameters) if var.parameters else {}
                    subreddit = params.get('subreddit')

                    if not subreddit:
                        continue

                    # Use Pullpush for 90 days of history
                    historical_data = fetcher.fetch_reddit_historical(
                        subreddit, days=90)

                    if not historical_data:
                        continue

                    # Store the data
                    for date_str, values in historical_data.items():
                        timestamp = datetime.strptime(date_str, "%Y-%m-%d")

                        # Check for existing
                        existing = session.query(TimeSeriesData).filter(
                            TimeSeriesData.variable_id == var.id,
                            TimeSeriesData.timestamp == timestamp
                        ).first()

                        # Use post count as the value
                        value = float(values.get('posts', 0))

                        if existing:
                            if existing.value != value:
                                existing.value = value
                                existing.fetched_at = datetime.utcnow()
                        else:
                            data_point = TimeSeriesData(
                                variable_id=var.id,
                                timestamp=timestamp,
                                value=value,
                                fetched_at=datetime.utcnow()
                            )
                            session.add(data_point)
                            total_points += 1

                    success_count += 1

                    # Small delay between requests
                    import time
                    time.sleep(1)

                except Exception as e:
                    logger.warning(
                        f"Failed to fetch historical for {var.name}: {e}")
                    continue

            session.commit()

        return {
            "status": "success",
            "message": f"Fetched historical data for {success_count} subreddits",
            "data_points_added": total_points,
            "source": "Pullpush.io (90 days)",
            "next_step": "Reddit signals should now have enough data for momentum"
        }

    except Exception as e:
        logger.error(f"Reddit historical fetch failed: {e}", exc_info=True)
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

        granger_service = GrangerCausalityService(
            max_lag=12, confidence_level=0.05)

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

            logger.info(
                f"Granger: {len(layer1_ids)} Layer 1 vars, {len(layer2_ids)} Layer 2 vars")

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

            logger.info(
                f"Found {len(l1_l2_pairs)} Layer 1 ↔ Layer 2 correlations for Granger testing")
            _active_jobs[job_id]['stage'] = f'testing_{len(l1_l2_pairs)}_pairs'

            tested = 0
            significant = 0

            # Test all pairs (no limit) - each test is fast with aligned data
            for corr in l1_l2_pairs:
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

                    # Set causal_direction (was previously missing from batch job)
                    if result.get('causal_direction'):
                        corr.causal_direction = result['causal_direction']

                    # Set optimal lag from the significant direction
                    # test_causality() returns var1_to_var2.lags, not top-level optimal_lag
                    direction = result.get('causal_direction', 'none')
                    xy_lags = result.get('var1_to_var2', {}).get('lags')
                    yx_lags = result.get('var2_to_var1', {}).get('lags')
                    if direction == 'x_to_y' and xy_lags is not None:
                        corr.granger_lags = int(xy_lags)
                    elif direction == 'y_to_x' and yx_lags is not None:
                        corr.granger_lags = int(yx_lags)
                    elif direction == 'bidirectional':
                        # Use the smaller lag for bidirectional
                        if xy_lags is not None and yx_lags is not None:
                            corr.granger_lags = int(min(xy_lags, yx_lags))
                        elif xy_lags is not None:
                            corr.granger_lags = int(xy_lags)
                        elif yx_lags is not None:
                            corr.granger_lags = int(yx_lags)
                    elif xy_lags is not None:
                        # Fallback: use xy lags if direction unknown
                        corr.granger_lags = int(xy_lags)

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

        logger.info(
            f"Granger complete: {tested} tested, {significant} significant")

    except Exception as e:
        logger.error(f"Granger calc failed: {e}", exc_info=True)
        _active_jobs[job_id]['status'] = 'failed'
        _active_jobs[job_id]['error'] = str(e)
        _active_jobs[job_id]['updated_at'] = datetime.utcnow().isoformat()
