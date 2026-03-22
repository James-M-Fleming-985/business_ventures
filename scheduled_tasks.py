"""
Scheduled Tasks — M0 Automated Validation + M1 Daily Ingestion + Walk-forward

Daily 01:00 UTC: Ingest fresh Wikipedia pageviews (55 variables × daily+monthly).
Daily 01:30 UTC: Ingest fresh Reddit activity (20+ subreddits × 30-day window).
Daily 02:00 UTC: Update actual values for matured predictions.
Weekly Sun 03:00 UTC: Snapshot accuracy baselines for trend tracking.
Weekly Mon 04:00 UTC: Walk-forward backtest for all significant Granger pairs.
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
    
    # Daily at 02:00 UTC — validate matured predictions
    scheduler.add_job(
        update_prediction_actuals,
        CronTrigger(hour=2, minute=0),
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
    
    scheduler.start()
    logger.info(
        "✅ APScheduler started — "
        "Wikipedia ingestion (01:00 UTC), Reddit ingestion (01:30 UTC), "
        "daily validation (02:00 UTC), weekly snapshot (Sun 03:00 UTC), "
        "walk-forward backtest (Mon 04:00 UTC)"
    )
    return scheduler
