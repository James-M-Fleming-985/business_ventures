"""
Scheduled Tasks — M0 Automated Validation

Daily: Update actual values for matured predictions.
Weekly: Snapshot accuracy baselines for trend tracking.
"""

import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)


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
    
    scheduler.start()
    logger.info("✅ APScheduler started — daily validation (02:00 UTC), weekly snapshot (Sun 03:00 UTC)")
    return scheduler
