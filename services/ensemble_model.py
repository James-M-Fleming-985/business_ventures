"""
Ensemble Model Service (M2 Track A)

Combines three sub-models into a confidence-weighted ensemble:
  1. Granger causality direction + lag predictions
  2. OLS linear regression (expanding-window walk-forward)
  3. ARIMA time-series forecasting

Each sub-model produces a direction prediction (up/down) with confidence.
The ensemble weights by historical accuracy per-signal and returns a
combined prediction with overall confidence score.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy.orm import Session

from database import get_db_session
from models import (
    CorrelationResult,
    PredictionTracking,
    TimeSeriesData,
    VariableMetadata,
)

logger = logging.getLogger(__name__)

# Minimum data points required per sub-model
MIN_OLS_TRAIN_MONTHS = 6
MIN_ARIMA_POINTS = 24
GRANGER_P_THRESHOLD = 0.10

# Default sub-model weights (overridden by calibrate_weights)
DEFAULT_WEIGHTS = {
    "granger": 0.40,
    "ols": 0.35,
    "arima": 0.25,
}

# Feature engineering window sizes
ROLLING_WINDOWS = [7, 30, 90]


class EnsembleModel:
    """Weighted ensemble combining Granger, OLS, and ARIMA sub-models."""

    def __init__(self, db: Session):
        self.db = db
        self.weights = dict(DEFAULT_WEIGHTS)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def predict(
        self,
        signal_name: str,
        target_name: str,
        *,
        store: bool = True,
    ) -> Dict:
        """Generate an ensemble prediction for a signal→target pair.

        Returns dict with keys:
            direction, confidence, predicted_change_pct,
            sub_models (per-model detail), features (engineered values).
        """
        signal_var = self._get_variable(signal_name)
        target_var = self._get_variable(target_name)

        if not signal_var or not target_var:
            return {"error": f"Variable not found: {signal_name} or {target_name}"}

        signal_ts = self._load_timeseries(signal_var.id)
        target_ts = self._load_timeseries(target_var.id)

        if len(target_ts) < MIN_OLS_TRAIN_MONTHS:
            return {"error": f"Insufficient data for {target_name} ({len(target_ts)} points)"}

        # Feature engineering on signal
        features = self._engineer_features(signal_ts)

        # Run each sub-model
        granger_result = self._granger_predict(signal_var, target_var, signal_ts, target_ts)
        ols_result = self._ols_predict(signal_ts, target_ts)
        arima_result = self._arima_predict(target_ts)

        sub_models = {
            "granger": granger_result,
            "ols": ols_result,
            "arima": arima_result,
        }

        # Calibrate weights from historical accuracy (if available)
        calibrated = self._calibrate_weights(signal_name, target_name)
        if calibrated:
            self.weights = calibrated

        # Weighted vote
        ensemble = self._combine(sub_models)
        ensemble["features"] = features
        ensemble["weights_used"] = dict(self.weights)
        ensemble["signal"] = signal_name
        ensemble["target"] = target_name

        if store:
            self._store_prediction(signal_var, target_var, ensemble, target_ts)

        return ensemble

    def predict_all_pairs(self, *, max_pairs: int = 200, store: bool = True) -> Dict:
        """Run ensemble predictions for all significant Granger pairs."""
        pairs = (
            self.db.query(CorrelationResult)
            .filter(
                CorrelationResult.granger_p_value_xy <= GRANGER_P_THRESHOLD,
                CorrelationResult.causal_direction.in_(["x_to_y", "bidirectional"]),
            )
            .limit(max_pairs)
            .all()
        )

        results = []
        for pair in pairs:
            var1 = self.db.query(VariableMetadata).get(pair.variable1_id)
            var2 = self.db.query(VariableMetadata).get(pair.variable2_id)
            if var1 and var2:
                r = self.predict(var1.name, var2.name, store=store)
                results.append(r)

        correct = sum(1 for r in results if r.get("direction"))
        return {
            "pairs_predicted": len(results),
            "predictions": results,
        }

    # ------------------------------------------------------------------
    # Sub-model: Granger causality
    # ------------------------------------------------------------------

    def _granger_predict(
        self,
        signal_var: VariableMetadata,
        target_var: VariableMetadata,
        signal_ts: List[Tuple[datetime, float]],
        target_ts: List[Tuple[datetime, float]],
    ) -> Dict:
        """Use stored Granger results to predict direction + lag."""
        corr = (
            self.db.query(CorrelationResult)
            .filter(
                CorrelationResult.variable1_id == signal_var.id,
                CorrelationResult.variable2_id == target_var.id,
            )
            .first()
        )

        if not corr or corr.granger_p_value_xy is None or corr.granger_p_value_xy > GRANGER_P_THRESHOLD:
            return {"direction": None, "confidence": 0.0, "reason": "no significant Granger relationship"}

        # Direction from recent signal momentum
        if len(signal_ts) >= 2:
            recent = [v for _, v in signal_ts[-3:]]
            momentum = (recent[-1] - recent[0]) / abs(recent[0]) if recent[0] != 0 else 0.0
            direction = "up" if momentum > 0 else "down"
        else:
            direction = None
            momentum = 0.0

        # Confidence: inverse of p-value, capped at 1.0
        confidence = min(1.0 - corr.granger_p_value_xy, 1.0)

        return {
            "direction": direction,
            "confidence": round(confidence, 4),
            "p_value": corr.granger_p_value_xy,
            "optimal_lag": corr.granger_lags,
            "momentum": round(momentum, 4),
        }

    # ------------------------------------------------------------------
    # Sub-model: OLS linear regression (expanding window)
    # ------------------------------------------------------------------

    def _ols_predict(
        self,
        signal_ts: List[Tuple[datetime, float]],
        target_ts: List[Tuple[datetime, float]],
    ) -> Dict:
        """Expanding-window OLS regression predicting next target value."""
        # Align signal and target by date (monthly)
        sig_dict = {d.strftime("%Y-%m"): v for d, v in signal_ts}
        tgt_dict = {d.strftime("%Y-%m"): v for d, v in target_ts}
        common = sorted(set(sig_dict) & set(tgt_dict))

        if len(common) < MIN_OLS_TRAIN_MONTHS:
            return {"direction": None, "confidence": 0.0, "reason": "insufficient aligned data"}

        x = np.array([sig_dict[k] for k in common])
        y = np.array([tgt_dict[k] for k in common])

        # OLS fit on full training window
        try:
            coeffs = np.polyfit(x, y, 1)
        except (np.linalg.LinAlgError, ValueError):
            return {"direction": None, "confidence": 0.0, "reason": "OLS fit failed"}

        slope, intercept = coeffs

        # Predict next value using latest signal value
        x_next = x[-1]
        y_last = y[-1]
        predicted_y = slope * x_next + intercept
        change_pct = ((predicted_y - y_last) / abs(y_last) * 100) if y_last != 0 else 0.0
        direction = "up" if predicted_y > y_last else "down"

        # R-squared as confidence
        y_pred = np.polyval(coeffs, x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        confidence = max(0.0, min(r_squared, 1.0))

        return {
            "direction": direction,
            "confidence": round(confidence, 4),
            "predicted_value": round(predicted_y, 4),
            "predicted_change_pct": round(change_pct, 2),
            "r_squared": round(r_squared, 4),
            "slope": round(slope, 6),
            "sample_size": len(common),
        }

    # ------------------------------------------------------------------
    # Sub-model: ARIMA forecasting
    # ------------------------------------------------------------------

    def _arima_predict(self, target_ts: List[Tuple[datetime, float]]) -> Dict:
        """ARIMA(1,1,1) forecast on target variable's own history."""
        if len(target_ts) < MIN_ARIMA_POINTS:
            return {"direction": None, "confidence": 0.0, "reason": "insufficient data for ARIMA"}

        values = np.array([v for _, v in target_ts])
        last_val = values[-1]

        try:
            from statsmodels.tsa.arima.model import ARIMA

            model = ARIMA(values, order=(1, 1, 1))
            fitted = model.fit()
            forecast = fitted.forecast(steps=1)[0]

            direction = "up" if forecast > last_val else "down"
            change_pct = ((forecast - last_val) / abs(last_val) * 100) if last_val != 0 else 0.0

            # AIC-based confidence: lower AIC → higher confidence (normalised)
            aic = fitted.aic
            confidence = max(0.0, min(1.0 / (1.0 + abs(aic) / 1000.0), 1.0))

            return {
                "direction": direction,
                "confidence": round(confidence, 4),
                "forecast_value": round(forecast, 4),
                "predicted_change_pct": round(change_pct, 2),
                "aic": round(aic, 2),
            }
        except Exception as e:
            logger.warning(f"ARIMA fit failed: {e}")
            return {"direction": None, "confidence": 0.0, "reason": f"ARIMA error: {e}"}

    # ------------------------------------------------------------------
    # Feature engineering
    # ------------------------------------------------------------------

    def _engineer_features(self, ts: List[Tuple[datetime, float]]) -> Dict:
        """Compute rolling averages, rate of change, and volatility."""
        if len(ts) < max(ROLLING_WINDOWS):
            return {}

        values = np.array([v for _, v in ts])

        features = {}
        for window in ROLLING_WINDOWS:
            if len(values) >= window:
                rolling = values[-window:]
                features[f"ma_{window}"] = round(float(np.mean(rolling)), 4)
                features[f"std_{window}"] = round(float(np.std(rolling)), 4)

        # Rate of change (latest vs 30 periods ago)
        if len(values) >= 30 and values[-30] != 0:
            features["roc_30"] = round(float((values[-1] - values[-30]) / abs(values[-30]) * 100), 2)

        # Volatility (coefficient of variation over last 90 points)
        if len(values) >= 90:
            recent = values[-90:]
            mean = np.mean(recent)
            if mean != 0:
                features["volatility_90"] = round(float(np.std(recent) / abs(mean)), 4)

        return features

    # ------------------------------------------------------------------
    # Ensemble combination
    # ------------------------------------------------------------------

    def _combine(self, sub_models: Dict[str, Dict]) -> Dict:
        """Weighted vote across sub-models to produce ensemble prediction."""
        up_score = 0.0
        down_score = 0.0
        total_weight = 0.0
        active_models = 0

        for model_name, result in sub_models.items():
            w = self.weights.get(model_name, 0.0)
            direction = result.get("direction")
            conf = result.get("confidence", 0.0)

            if direction is None:
                continue

            active_models += 1
            weighted = w * conf

            if direction == "up":
                up_score += weighted
            else:
                down_score += weighted

            total_weight += weighted

        if active_models == 0:
            return {
                "direction": None,
                "confidence": 0.0,
                "active_models": 0,
                "sub_models": sub_models,
                "reason": "no sub-models produced a prediction",
            }

        direction = "up" if up_score >= down_score else "down"
        margin = abs(up_score - down_score)
        confidence = (margin / total_weight) if total_weight > 0 else 0.0
        confidence = min(confidence, 1.0)

        return {
            "direction": direction,
            "confidence": round(confidence, 4),
            "up_score": round(up_score, 4),
            "down_score": round(down_score, 4),
            "active_models": active_models,
            "sub_models": sub_models,
        }

    # ------------------------------------------------------------------
    # Weight calibration from historical accuracy
    # ------------------------------------------------------------------

    def _calibrate_weights(self, signal_name: str, target_name: str) -> Optional[Dict]:
        """Compute per-model accuracy from validated predictions and return weights."""
        # Query validated predictions grouped by model_version
        preds = (
            self.db.query(PredictionTracking)
            .filter(
                PredictionTracking.signal_name == signal_name,
                PredictionTracking.target_name == target_name,
                PredictionTracking.status == "validated",
                PredictionTracking.direction_correct.isnot(None),
            )
            .all()
        )

        if len(preds) < 10:
            return None  # Not enough data to calibrate

        model_stats = {}
        for p in preds:
            mv = p.model_version or "unknown"
            bucket = None
            if "granger" in mv:
                bucket = "granger"
            elif "ols" in mv or "walkforward" in mv or "backtest" in mv:
                bucket = "ols"
            elif "arima" in mv:
                bucket = "arima"
            elif "ensemble" in mv:
                continue  # don't use ensemble predictions to calibrate ensemble
            else:
                continue

            if bucket not in model_stats:
                model_stats[bucket] = {"correct": 0, "total": 0}
            model_stats[bucket]["total"] += 1
            if p.direction_correct:
                model_stats[bucket]["correct"] += 1

        if not model_stats:
            return None

        # Compute accuracy-based weights
        accuracies = {}
        for m, s in model_stats.items():
            accuracies[m] = s["correct"] / s["total"] if s["total"] > 0 else 0.5

        total_acc = sum(accuracies.values())
        if total_acc == 0:
            return None

        calibrated = {}
        for m in DEFAULT_WEIGHTS:
            if m in accuracies:
                calibrated[m] = accuracies[m] / total_acc
            else:
                calibrated[m] = DEFAULT_WEIGHTS[m]

        # Renormalise to sum to 1.0
        total = sum(calibrated.values())
        if total > 0:
            calibrated = {k: round(v / total, 4) for k, v in calibrated.items()}

        logger.info(f"Calibrated weights for {signal_name}→{target_name}: {calibrated}")
        return calibrated

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_variable(self, name: str) -> Optional[VariableMetadata]:
        return (
            self.db.query(VariableMetadata)
            .filter(VariableMetadata.name == name)
            .first()
        )

    def _load_timeseries(self, variable_id: int) -> List[Tuple[datetime, float]]:
        rows = (
            self.db.query(TimeSeriesData)
            .filter(TimeSeriesData.variable_id == variable_id)
            .order_by(TimeSeriesData.timestamp.asc())
            .all()
        )
        return [(r.timestamp, r.value) for r in rows]

    def _store_prediction(
        self,
        signal_var: VariableMetadata,
        target_var: VariableMetadata,
        ensemble: Dict,
        target_ts: List[Tuple[datetime, float]],
    ) -> None:
        """Persist ensemble prediction as PredictionTracking record."""
        if not ensemble.get("direction"):
            return

        last_target_val = target_ts[-1][1] if target_ts else None
        ols = ensemble.get("sub_models", {}).get("ols", {})

        pred = PredictionTracking(
            prediction_id=f"ensemble_{uuid.uuid4().hex[:12]}",
            signal_name=signal_var.name,
            target_name=target_var.name,
            predicted_at=datetime.utcnow(),
            target_date=datetime.utcnow() + timedelta(days=30),
            predicted_direction=ensemble["direction"],
            predicted_value=ols.get("predicted_value"),
            predicted_change_pct=ols.get("predicted_change_pct"),
            current_target_value=last_target_val,
            r_squared=ols.get("r_squared"),
            confidence=_confidence_label(ensemble["confidence"]),
            model_version="ensemble_v1",
            granger_p_value=ensemble.get("sub_models", {}).get("granger", {}).get("p_value"),
            status="pending",
        )
        self.db.add(pred)
        self.db.flush()


def _confidence_label(score: float) -> str:
    if score >= 0.7:
        return "high"
    elif score >= 0.4:
        return "medium"
    return "low"


# ------------------------------------------------------------------
# Convenience function for scheduled tasks
# ------------------------------------------------------------------

def run_ensemble_predictions(db_session_factory, max_pairs: int = 200) -> Dict:
    """Entry point for APScheduler — runs ensemble on all significant pairs."""
    session = db_session_factory()
    try:
        model = EnsembleModel(session)
        result = model.predict_all_pairs(max_pairs=max_pairs, store=True)
        session.commit()
        logger.info(
            f"Ensemble predictions complete: {result['pairs_predicted']} pairs"
        )
        return result
    except Exception as e:
        session.rollback()
        logger.error(f"Ensemble prediction run failed: {e}")
        return {"error": str(e)}
    finally:
        session.close()
