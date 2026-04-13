"""
Scheduled Tasks — M0 Automated Validation + M1 Daily Ingestion + M2 Intelligence

Daily 01:00 UTC: Ingest fresh Wikipedia pageviews (55 variables × daily+monthly).
Daily 01:30 UTC: Ingest fresh Reddit activity (20+ subreddits × 30-day window).
Daily 02:00 UTC: Ingest GDELT global event tone (20 themes × 30-day window).
Daily 02:30 UTC: Update actual values for matured predictions.
Weekly Sun 03:00 UTC: Snapshot accuracy baselines for trend tracking.
Weekly Mon 04:00 UTC: Walk-forward backtest for all significant Granger pairs.
Daily 05:00 UTC: Ensemble model predictions (Granger + OLS + ARIMA).
Every 6h:      Aggregate MVP page-view beacons into ProductMetrics.
"""

import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)


def ingest_wikipedia_daily(db_session_factory):
    """Daily job: fetch fresh Wikipedia pageviews for all active wiki variables.

    Calls the existing DataIngestionService._fetch_wikipedia_pageviews_data()
    which fetches both daily (90-day window) and monthly (5-year window) data
    and upserts into TimeSeriesData.
    """
    try:
        from data_ingestion_service import DataIngestionService
        service = DataIngestionService()
        result = service._fetch_wikipedia_pageviews_data()
        logger.info(f"Scheduled Wikipedia ingestion complete: {result}")
    except Exception as e:
        logger.error(f"Scheduled Wikipedia ingestion failed: {e}", exc_info=True)


def ingest_reddit_daily(db_session_factory):
    """Daily job: fetch fresh Reddit activity for all active subreddit variables.

    Calls the existing DataIngestionService._fetch_reddit_activity_data()
    which fetches 30-day post counts and upserts into TimeSeriesData.
    Rate-limited internally (2s between subreddits).
    """
    try:
        from data_ingestion_service import DataIngestionService
        service = DataIngestionService()
        result = service._fetch_reddit_activity_data()
        logger.info(f"Scheduled Reddit ingestion complete: {result}")
    except Exception as e:
        logger.error(f"Scheduled Reddit ingestion failed: {e}", exc_info=True)


def ingest_gdelt_daily(db_session_factory):
    """Daily job: fetch GDELT global event tone for all active GDELT themes.

    Calls DataIngestionService._fetch_gdelt_data() which fetches 30-day
    tone data and upserts into TimeSeriesData.
    Rate-limited internally (3s between themes).
    """
    try:
        from data_ingestion_service import DataIngestionService
        service = DataIngestionService()
        result = service._fetch_gdelt_data()
        logger.info(f"Scheduled GDELT ingestion complete: {result}")
    except Exception as e:
        logger.error(f"Scheduled GDELT ingestion failed: {e}", exc_info=True)


def run_ensemble_predictions_job(db_session_factory):
    """Daily job: run ensemble model predictions for all significant Granger pairs.

    Combines Granger + OLS + ARIMA sub-models, stores predictions in
    PredictionTracking with model_version='ensemble_v1'.
    """
    try:
        from services.ensemble_model import run_ensemble_predictions
        result = run_ensemble_predictions(db_session_factory)
        logger.info(f"Scheduled ensemble predictions complete: {result}")
    except Exception as e:
        logger.error(f"Scheduled ensemble predictions failed: {e}", exc_info=True)


def update_prediction_actuals(db_session_factory):
    """Daily job: fetch actual values for matured predictions (target_date <= today).
    
    Calls the same logic as POST /predictions/validate but runs unattended.
    """
    from models import PredictionTracking
    
    try:
        db = db_session_factory()
        today = date.today()
        
        matured = db.query(PredictionTracking).filter(
            PredictionTracking.status == 'pending',
            PredictionTracking.target_date <= today
        ).all()
        
        if not matured:
            logger.info("Scheduled validation: no matured predictions to process")
            db.close()
            return
        
        validated_count = 0
        for pred in matured:
            try:
                # Look up actual value from time series data
                from models import TimeSeriesData
                actual_record = db.query(TimeSeriesData).filter(
                    TimeSeriesData.variable_id == pred.medium_variable_id,
                    TimeSeriesData.date >= pred.target_date
                ).order_by(TimeSeriesData.date.asc()).first()
                
                if actual_record and actual_record.value is not None:
                    pred.actual_value = actual_record.value
                    pred.actual_recorded_at = datetime.utcnow()
                    
                    # Compute direction
                    if pred.baseline_value is not None:
                        pred.actual_direction = 'up' if actual_record.value > pred.baseline_value else 'down'
                        pred.direction_correct = (pred.actual_direction == pred.predicted_direction)
                        
                        if pred.baseline_value != 0:
                            pred.actual_change_pct = (
                                (actual_record.value - pred.baseline_value) / abs(pred.baseline_value) * 100
                            )
                        
                        if pred.predicted_value and pred.predicted_value != 0:
                            pred.value_error_pct = (
                                (actual_record.value - pred.predicted_value) / abs(pred.predicted_value) * 100
                            )
                    
                    pred.status = 'validated'
                    validated_count += 1
                    
            except Exception as e:
                logger.warning(f"Failed to validate prediction {pred.prediction_id}: {e}")
                continue
        
        db.commit()
        logger.info(f"Scheduled validation complete: {validated_count}/{len(matured)} predictions validated")
        db.close()
        
    except Exception as e:
        logger.error(f"Scheduled prediction validation failed: {e}", exc_info=True)


def run_walk_forward_backtest(db_session_factory):
    """Weekly job: expanding-window walk-forward backtest for significant Granger pairs.

    Writes validated predictions (model_version='backtest_walkforward') to
    PredictionTracking so that accuracy metrics reflect out-of-sample performance.
    """
    try:
        from services.walk_forward_validator import run_walk_forward_backtest as _run
        db = db_session_factory()
        summary = _run(db)
        db.close()
        logger.info(f"Scheduled walk-forward backtest complete: {summary}")
    except Exception as e:
        logger.error(f"Scheduled walk-forward backtest failed: {e}", exc_info=True)


def snapshot_baselines(db_session_factory):
    """Weekly job: compute and log current accuracy baselines."""
    from models import PredictionTracking, ExploitationRecommendation, ExploitationValidation
    
    try:
        db = db_session_factory()
        
        # Model accuracy
        validated = db.query(PredictionTracking).filter(
            PredictionTracking.status == 'validated'
        ).all()
        
        direction_correct = sum(1 for p in validated if p.direction_correct)
        model_accuracy = (direction_correct / len(validated) * 100) if validated else 0.0
        
        # Exploitation accuracy
        validations = db.query(ExploitationValidation).all()
        exploit_correct = sum(1 for v in validations if v.actual_outcome in ('SUCCESS', 'PARTIAL'))
        exploit_accuracy = (exploit_correct / len(validations) * 100) if validations else 0.0
        
        # Log the snapshot
        logger.info(
            f"Weekly baseline snapshot — "
            f"Model accuracy: {model_accuracy:.1f}% ({len(validated)} validated), "
            f"Exploitation accuracy: {exploit_accuracy:.1f}% ({len(validations)} validated)"
        )
        
        db.close()
        
    except Exception as e:
        logger.error(f"Baseline snapshot failed: {e}", exc_info=True)


def aggregate_page_views(db_session_factory):
    """Aggregate MvpPageView rows into ProductMetrics for engagement tracking.

    Counts page_views and unique_visitors (distinct visitor_hash) per build
    for the period since the last aggregation. Upserts into ProductMetrics
    via the ProductDeployment join.
    """
    try:
        from sqlalchemy import func
        from models import (
            MvpPageView, ProductDeployment, ProductMetrics, MVPBuild,
        )

        db = db_session_factory()
        now = datetime.utcnow()

        # Get all builds with page views
        build_stats = (
            db.query(
                MvpPageView.build_id,
                func.count(MvpPageView.id).label("total_views"),
                func.count(func.distinct(MvpPageView.visitor_hash)).label("unique_visitors"),
            )
            .group_by(MvpPageView.build_id)
            .all()
        )

        if not build_stats:
            logger.info("Page-view aggregation: no beacon data to process")
            db.close()
            return

        updated = 0
        for build_id, total_views, unique_visitors in build_stats:
            # Find or create ProductDeployment for this build
            deployment = (
                db.query(ProductDeployment)
                .filter(ProductDeployment.build_id == build_id)
                .first()
            )
            if not deployment:
                # Auto-create a minimal deployment record
                build = db.query(MVPBuild).get(build_id)
                if not build:
                    continue
                deployment = ProductDeployment(
                    build_id=build_id,
                    product_name=f"mvp-{build_id}",
                    app_id=f"mvp_{build_id}",
                    railway_url=build.railway_url,
                    deployed_at=build.created_at,
                    status="active",
                )
                db.add(deployment)
                db.flush()

            # Upsert ProductMetrics — one row per deployment per day
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = now

            metrics = (
                db.query(ProductMetrics)
                .filter(
                    ProductMetrics.deployment_id == deployment.id,
                    ProductMetrics.period_start == period_start,
                )
                .first()
            )
            if metrics:
                metrics.page_views = total_views
                metrics.unique_visitors = unique_visitors
                metrics.period_end = period_end
                metrics.source = "beacon"
            else:
                metrics = ProductMetrics(
                    deployment_id=deployment.id,
                    period_start=period_start,
                    period_end=period_end,
                    page_views=total_views,
                    unique_visitors=unique_visitors,
                    source="beacon",
                )
                db.add(metrics)
            updated += 1

        db.commit()
        db.close()
        logger.info(
            f"Page-view aggregation complete: updated metrics for {updated} builds"
        )

    except Exception as e:
        logger.error(f"Page-view aggregation failed: {e}", exc_info=True)


def init_scheduler(db_session_factory):
    """Initialise APScheduler with daily and weekly jobs."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.warning("APScheduler not installed — scheduled tasks disabled. Install with: pip install apscheduler")
        return None
    
    scheduler = BackgroundScheduler()
    
    # Daily at 01:00 UTC — ingest Wikipedia pageviews (M1 Track A)
    scheduler.add_job(
        ingest_wikipedia_daily,
        CronTrigger(hour=1, minute=0),
        args=[db_session_factory],
        id='daily_wikipedia_ingestion',
        name='Daily Wikipedia pageview ingestion',
        replace_existing=True,
    )
    
    # Daily at 01:30 UTC — ingest Reddit activity (M1 Track A)
    scheduler.add_job(
        ingest_reddit_daily,
        CronTrigger(hour=1, minute=30),
        args=[db_session_factory],
        id='daily_reddit_ingestion',
        name='Daily Reddit activity ingestion',
        replace_existing=True,
    )
    
    # Daily at 02:00 UTC — ingest GDELT global sentiment (M2 Track B)
    scheduler.add_job(
        ingest_gdelt_daily,
        CronTrigger(hour=2, minute=0),
        args=[db_session_factory],
        id='daily_gdelt_ingestion',
        name='Daily GDELT sentiment ingestion',
        replace_existing=True,
    )
    
    # Daily at 02:30 UTC — validate matured predictions
    scheduler.add_job(
        update_prediction_actuals,
        CronTrigger(hour=2, minute=30),
        args=[db_session_factory],
        id='daily_prediction_validation',
        name='Daily prediction actual-value update',
        replace_existing=True,
    )
    
    # Weekly Sunday at 03:00 UTC — snapshot baselines
    scheduler.add_job(
        snapshot_baselines,
        CronTrigger(day_of_week='sun', hour=3, minute=0),
        args=[db_session_factory],
        id='weekly_baseline_snapshot',
        name='Weekly baseline accuracy snapshot',
        replace_existing=True,
    )
    
    # Weekly Monday at 04:00 UTC — walk-forward backtest
    scheduler.add_job(
        run_walk_forward_backtest,
        CronTrigger(day_of_week='mon', hour=4, minute=0),
        args=[db_session_factory],
        id='weekly_walk_forward_backtest',
        name='Weekly walk-forward backtest',
        replace_existing=True,
    )
    
    # Daily at 05:00 UTC — ensemble model predictions (M2 Track A)
    scheduler.add_job(
        run_ensemble_predictions_job,
        CronTrigger(hour=5, minute=0),
        args=[db_session_factory],
        id='daily_ensemble_predictions',
        name='Daily ensemble model predictions',
        replace_existing=True,
    )
    
    # Every 6 hours — aggregate MVP page-view beacons into ProductMetrics
    scheduler.add_job(
        aggregate_page_views,
        CronTrigger(hour='*/6', minute=30),
        args=[db_session_factory],
        id='aggregate_mvp_page_views',
        name='MVP page-view aggregation',
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info(
        "✅ APScheduler started — "
        "Wikipedia (01:00), Reddit (01:30), GDELT (02:00), "
        "validation (02:30), snapshot (Sun 03:00), "
        "walk-forward (Mon 04:00), ensemble (05:00), "
        "page-view agg (*/6:30 UTC)"
    )
    return scheduler
