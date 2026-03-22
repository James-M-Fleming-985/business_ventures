"""
Walk-Forward Validation Service (M1 Phase 3.3 — Track A)

Expanding-window backtest over all signal/target pairs with significant
Granger causality.  For each pair:

  1. Collect aligned monthly time series for signal & target
  2. Train OLS regression on months 1..N
  3. Predict direction + magnitude for month N+1
  4. Slide forward: train on 1..N+1, predict N+2, …
  5. Store each prediction in PredictionTracking (model_version='backtest_walkforward')
  6. Compare predictions against actuals → instant direction accuracy

This gives hundreds of prediction-outcome pairs retroactively, without
waiting months for new predictions to mature.
"""

import logging
import uuid
from datetime import datetime

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from models import (
    CorrelationResult,
    PredictionTracking,
    TimeSeriesData,
    VariableMetadata,
)

logger = logging.getLogger(__name__)

# Minimum months of data in the training window before we start predicting.
MIN_TRAIN_MONTHS = 6

# We only backtest pairs where Granger p-value < this threshold.
GRANGER_P_THRESHOLD = 0.10


def run_walk_forward_backtest(db: Session, max_pairs: int = 200) -> dict:
    """Run walk-forward backtest for all significant Granger pairs.

    Args:
        db: SQLAlchemy session.
        max_pairs: Cap on number of pairs to process (safety limit).

    Returns:
        Summary dict: {pairs_tested, predictions_created, avg_direction_accuracy}.
    """
    # ------------------------------------------------------------------
    # 1. Find significant Granger pairs
    # ------------------------------------------------------------------
    pairs = (
        db.query(CorrelationResult)
        .filter(
            CorrelationResult.causal_direction.isnot(None),
            CorrelationResult.causal_direction != "none",
        )
        .order_by(CorrelationResult.abs_correlation.desc())
        .limit(max_pairs)
        .all()
    )

    if not pairs:
        logger.info("Walk-forward: no Granger pairs found")
        return {"pairs_tested": 0, "predictions_created": 0}

    total_created = 0
    total_correct = 0
    total_validated = 0
    pairs_tested = 0

    for corr in pairs:
        # Determine causal direction → which variable is signal, which is target
        if corr.causal_direction == "x_to_y":
            signal_var_id = corr.variable1_id
            target_var_id = corr.variable2_id
            p_val = corr.granger_p_value_xy
        elif corr.causal_direction == "y_to_x":
            signal_var_id = corr.variable2_id
            target_var_id = corr.variable1_id
            p_val = corr.granger_p_value_yx
        elif corr.causal_direction == "bidirectional":
            # Use the direction with lower p-value
            if (corr.granger_p_value_xy or 1) <= (corr.granger_p_value_yx or 1):
                signal_var_id = corr.variable1_id
                target_var_id = corr.variable2_id
                p_val = corr.granger_p_value_xy
            else:
                signal_var_id = corr.variable2_id
                target_var_id = corr.variable1_id
                p_val = corr.granger_p_value_yx
        else:
            continue

        if p_val is None or p_val > GRANGER_P_THRESHOLD:
            continue

        created, correct, validated = _backtest_pair(
            db, signal_var_id, target_var_id, corr, p_val
        )
        total_created += created
        total_correct += correct
        total_validated += validated
        if created > 0:
            pairs_tested += 1

    accuracy = round(total_correct / total_validated * 100, 1) if total_validated else 0.0
    logger.info(
        f"Walk-forward complete: {pairs_tested} pairs, "
        f"{total_created} predictions, {accuracy}% direction accuracy"
    )
    return {
        "pairs_tested": pairs_tested,
        "predictions_created": total_created,
        "predictions_validated": total_validated,
        "direction_correct": total_correct,
        "avg_direction_accuracy": accuracy,
    }


def _backtest_pair(
    db: Session,
    signal_var_id: int,
    target_var_id: int,
    corr: CorrelationResult,
    p_value: float,
) -> tuple:
    """Walk-forward backtest for a single signal→target pair.

    Returns (predictions_created, direction_correct, predictions_validated).
    """
    signal_var = db.query(VariableMetadata).get(signal_var_id)
    target_var = db.query(VariableMetadata).get(target_var_id)
    if not signal_var or not target_var:
        return 0, 0, 0

    # ------------------------------------------------------------------
    # Fetch and align time series at monthly frequency
    # ------------------------------------------------------------------
    signal_data = (
        db.query(TimeSeriesData)
        .filter(TimeSeriesData.variable_id == signal_var_id)
        .order_by(TimeSeriesData.timestamp)
        .all()
    )
    target_data = (
        db.query(TimeSeriesData)
        .filter(TimeSeriesData.variable_id == target_var_id)
        .order_by(TimeSeriesData.timestamp)
        .all()
    )

    if len(signal_data) < MIN_TRAIN_MONTHS + 2 or len(target_data) < MIN_TRAIN_MONTHS + 2:
        return 0, 0, 0

    # Build pandas Series and resample to monthly mean
    sig_series = pd.Series(
        data=[float(d.value) for d in signal_data],
        index=pd.DatetimeIndex([d.timestamp for d in signal_data]),
    ).resample("MS").mean().dropna()

    tgt_series = pd.Series(
        data=[float(d.value) for d in target_data],
        index=pd.DatetimeIndex([d.timestamp for d in target_data]),
    ).resample("MS").mean().dropna()

    # Align on common months
    aligned = pd.DataFrame({"signal": sig_series, "target": tgt_series}).dropna()
    if len(aligned) < MIN_TRAIN_MONTHS + 2:
        return 0, 0, 0

    # ------------------------------------------------------------------
    # Expanding-window walk-forward
    # ------------------------------------------------------------------
    created = 0
    correct = 0
    validated = 0

    for split_idx in range(MIN_TRAIN_MONTHS, len(aligned) - 1):
        train = aligned.iloc[:split_idx]
        actual_row = aligned.iloc[split_idx]

        x_train = train["signal"].values
        y_train = train["target"].values

        # Simple OLS: y = slope * x + intercept
        if np.std(x_train) == 0:
            continue

        slope, intercept = np.polyfit(x_train, y_train, 1)

        # Predict: use last known signal value to predict next target
        x_last = train["signal"].iloc[-1]
        y_last = train["target"].iloc[-1]
        x_next = aligned["signal"].iloc[split_idx]  # actual signal at prediction month

        predicted_y = slope * x_next + intercept
        predicted_change = predicted_y - y_last
        predicted_direction = "up" if predicted_change > 0 else "down"
        predicted_change_pct = (
            (predicted_change / abs(y_last) * 100) if y_last != 0 else 0.0
        )

        # Actual
        actual_y = actual_row["target"]
        actual_change = actual_y - y_last
        actual_direction = "up" if actual_change > 0 else "down"
        actual_change_pct = (
            (actual_change / abs(y_last) * 100) if y_last != 0 else 0.0
        )

        direction_correct = predicted_direction == actual_direction
        value_error = (
            ((actual_y - predicted_y) / abs(predicted_y) * 100) if predicted_y != 0 else 0.0
        )

        # R-squared on training window
        y_hat = slope * x_train + intercept
        ss_res = np.sum((y_train - y_hat) ** 2)
        ss_tot = np.sum((y_train - np.mean(y_train)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

        prediction_date = aligned.index[split_idx]
        prediction_id = f"wf_{signal_var.name}_{target_var.name}_{prediction_date.strftime('%Y%m')}"

        # Skip if this prediction already exists
        existing = (
            db.query(PredictionTracking)
            .filter(PredictionTracking.prediction_id == prediction_id)
            .first()
        )
        if existing:
            # Count for accuracy stats even if already stored
            if existing.direction_correct is not None:
                validated += 1
                if existing.direction_correct:
                    correct += 1
            continue

        row = PredictionTracking(
            prediction_id=prediction_id,
            signal_name=signal_var.name,
            target_name=target_var.name,
            predicted_at=prediction_date,
            target_date=prediction_date,
            optimal_lag_days=(corr.granger_lags or 1) * 30,
            predicted_direction=predicted_direction,
            predicted_value=round(predicted_y, 4),
            predicted_change_pct=round(predicted_change_pct, 2),
            current_target_value=round(y_last, 4),
            current_signal_value=round(x_last, 4),
            signal_momentum=None,
            r_squared=round(r_squared, 4),
            confidence="medium" if r_squared > 0.3 else "low",
            granger_p_value=p_value,
            target_source=target_var.source,
            model_version="backtest_walkforward",
            # Pre-filled actuals since this is a backtest
            actual_value=round(actual_y, 4),
            actual_direction=actual_direction,
            actual_change_pct=round(actual_change_pct, 2),
            direction_correct=direction_correct,
            value_error_pct=round(value_error, 2),
            status="validated",
        )
        db.add(row)
        created += 1
        validated += 1
        if direction_correct:
            correct += 1

    # Commit per pair to avoid huge transactions
    if created > 0:
        db.commit()
        logger.info(
            f"Walk-forward {signal_var.name}→{target_var.name}: "
            f"{created} predictions, {correct}/{validated} correct"
        )

    return created, correct, validated
