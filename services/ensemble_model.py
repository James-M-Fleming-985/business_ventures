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
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, aliased

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

# Layer 1 sources: fast behavioral signals (Wikipedia pageviews, Reddit activity)
# Layer 2 is everything else (FRED, stocks, ArXiv, GDELT, etc.)
# Ensemble should only predict L1 signal → L2 target (cross-layer pairs)
LAYER1_SOURCES = ("wikipedia", "reddit")

# Feature engineering window sizes (months — data is monthly-aligned)
ROLLING_WINDOWS = [3, 6, 12]


class EnsembleModel:
    """Weighted ensemble combining Granger, OLS, and ARIMA sub-models."""

    # Candidate ARIMA orders — searched once per target, cached
    ARIMA_ORDERS = [(1, 1, 1), (2, 1, 1), (1, 1, 2), (2, 1, 2), (0, 1, 1)]

    def __init__(self, db: Session):
        self.db = db
        self.weights = dict(DEFAULT_WEIGHTS)
        self._arima_order_cache: Dict[str, Tuple[int, int, int]] = {}
        # Weight for blending ARIMA-derived lag with granger lag in _combine.
        # 0.0 = use granger lag only (legacy behaviour).
        self.lag_blend_arima = 0.0
        # v4 knobs
        self.granger_use_coefficient_sign = False  # sign-aware Granger
        self.ols_mode = "levels"  # 'levels' (legacy) or 'differences' (v4)
        self.shrinkage_lambda = 1.0  # 1.0 = no shrinkage, <1.0 shrinks change% toward 0
        # Cache of regression coefficient signs per (signal_id, target_id)
        self._coef_sign_cache: Dict[Tuple[int, int], int] = {}

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
        ols_result = self._ols_predict(signal_ts, target_ts, features=features)
        arima_result = self._arima_predict(target_ts, target_name=target_name)

        sub_models = {
            "granger": granger_result,
            "ols": ols_result,
            "arima": arima_result,
        }

        # Calibrate weights from historical accuracy (if available)
        calibrated = self._calibrate_weights(signal_name, target_name)
        if not calibrated:
            calibrated = self._calibrate_weights_global()
        if calibrated:
            self.weights = calibrated

        # Weighted vote
        ensemble = self._combine(sub_models)
        ensemble["features"] = features
        ensemble["weights_used"] = dict(self.weights)
        ensemble["signal"] = signal_name
        ensemble["target"] = target_name
        ensemble["signal_source"] = signal_var.source
        ensemble["target_source"] = target_var.source

        if store:
            self._store_prediction(signal_var, target_var, ensemble, target_ts)

        return ensemble

    def predict_all_pairs(self, *, max_pairs: int = 200, store: bool = True) -> Dict:
        """Run ensemble predictions for all significant cross-layer Granger pairs.

        Cross-layer means one variable is Layer 1 (behavioral signal:
        Wikipedia, Reddit) and the other is Layer 2 (exploitable macro:
        FRED, stocks, ArXiv, etc.).  The filter is applied at the SQL
        level so ``max_pairs`` is not wasted on same-layer pairs.
        """
        vm1 = aliased(VariableMetadata)
        vm2 = aliased(VariableMetadata)

        # Cross-layer condition: exactly one side must be L1
        cross_layer = or_(
            and_(vm1.source.in_(LAYER1_SOURCES), ~vm2.source.in_(LAYER1_SOURCES)),
            and_(vm2.source.in_(LAYER1_SOURCES), ~vm1.source.in_(LAYER1_SOURCES)),
        )

        pairs = (
            self.db.query(CorrelationResult, vm1, vm2)
            .join(vm1, CorrelationResult.variable1_id == vm1.id)
            .join(vm2, CorrelationResult.variable2_id == vm2.id)
            .filter(
                or_(
                    CorrelationResult.granger_p_value_xy <= GRANGER_P_THRESHOLD,
                    CorrelationResult.granger_p_value_yx <= GRANGER_P_THRESHOLD,
                ),
                cross_layer,
            )
            .order_by(CorrelationResult.abs_correlation.desc())
            .limit(max_pairs)
            .all()
        )

        # Fallback: if no Granger pairs yet, use top correlated significant pairs
        if not pairs:
            pairs = (
                self.db.query(CorrelationResult, vm1, vm2)
                .join(vm1, CorrelationResult.variable1_id == vm1.id)
                .join(vm2, CorrelationResult.variable2_id == vm2.id)
                .filter(
                    CorrelationResult.is_significant.is_(True),
                    cross_layer,
                )
                .order_by(CorrelationResult.abs_correlation.desc())
                .limit(max_pairs)
                .all()
            )

        results = []
        seen_pairs = set()
        for corr_row, var1, var2 in pairs:
            # Assign signal (L1) → target (L2)
            if var1.source in LAYER1_SOURCES:
                signal_var, target_var = var1, var2
            else:
                signal_var, target_var = var2, var1

            # Deduplicate: skip if we've already predicted this pair
            pair_key = tuple(sorted([signal_var.name, target_var.name]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)
            r = self.predict(signal_var.name, target_var.name, store=store)
            results.append(r)

        return {
            "pairs_predicted": len(results),
            "unique_pairs": len(seen_pairs),
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
        # Query both variable orderings — the CorrelationResult may store
        # the pair as (signal, target) or (target, signal)
        corr = (
            self.db.query(CorrelationResult)
            .filter(
                or_(
                    (CorrelationResult.variable1_id == signal_var.id) &
                    (CorrelationResult.variable2_id == target_var.id),
                    (CorrelationResult.variable1_id == target_var.id) &
                    (CorrelationResult.variable2_id == signal_var.id),
                )
            )
            .first()
        )

        if not corr:
            return {"direction": None, "confidence": 0.0, "reason": "no Granger correlation found"}

        # Pick the correct p-value based on which ordering matched
        # If signal=var1, the signal→target direction is stored in granger_p_value_xy
        # If signal=var2, the signal→target direction is stored in granger_p_value_yx
        if corr.variable1_id == signal_var.id:
            p_value = corr.granger_p_value_xy
        else:
            p_value = corr.granger_p_value_yx

        if p_value is None or p_value > GRANGER_P_THRESHOLD:
            return {"direction": None, "confidence": 0.0, "reason": "no significant Granger relationship"}

        # Direction from recent signal momentum
        if len(signal_ts) >= 2:
            recent = [v for _, v in signal_ts[-3:]]
            momentum = (recent[-1] - recent[0]) / abs(recent[0]) if recent[0] != 0 else 0.0
            naive_direction = "up" if momentum > 0 else "down"
        else:
            naive_direction = None
            momentum = 0.0

        # v4: sign-aware Granger — multiply naive momentum direction by the
        # sign of the regression coefficient β (Δy_t = α + Σβ_i Δx_{t-i}).
        # If β is negative, an upward signal predicts a downward target.
        coef_sign = None
        if self.granger_use_coefficient_sign and naive_direction is not None:
            try:
                lag = int(corr.granger_lags or 1)
            except (TypeError, ValueError):
                lag = 1
            coef_sign = self._compute_granger_coefficient_sign(
                signal_var, target_var, signal_ts, target_ts, lag=lag
            )
            if coef_sign is not None and coef_sign < 0:
                direction = "down" if naive_direction == "up" else "up"
            else:
                direction = naive_direction
        else:
            direction = naive_direction

        # Confidence: inverse of p-value, capped at 1.0
        confidence = min(1.0 - p_value, 1.0)

        return {
            "direction": direction,
            "confidence": round(confidence, 4),
            "p_value": p_value,
            "optimal_lag": corr.granger_lags,
            "momentum": round(momentum, 4),
            "coef_sign": coef_sign,
        }

    def _compute_granger_coefficient_sign(
        self,
        signal_var: VariableMetadata,
        target_var: VariableMetadata,
        signal_ts: List[Tuple[datetime, float]],
        target_ts: List[Tuple[datetime, float]],
        lag: int = 1,
    ) -> Optional[int]:
        """Compute sign of summed Granger regression coefficients on first
        differences: Δy_t = α + Σ_{i=1..lag} β_i Δx_{t-i} + γ Δy_{t-1}.

        Returns +1, -1, or None if fit fails / insufficient data.
        Cached per (signal_id, target_id) since coefficient sign is stable
        relative to single-month time series updates.
        """
        cache_key = (signal_var.id, target_var.id)
        if cache_key in self._coef_sign_cache:
            return self._coef_sign_cache[cache_key]

        sig_dict = {d.strftime("%Y-%m"): v for d, v in signal_ts}
        tgt_dict = {d.strftime("%Y-%m"): v for d, v in target_ts}
        common = sorted(set(sig_dict) & set(tgt_dict))
        if len(common) < max(MIN_OLS_TRAIN_MONTHS + lag + 2, 8):
            return None

        x = np.array([sig_dict[k] for k in common], dtype=float)
        y = np.array([tgt_dict[k] for k in common], dtype=float)
        dx = np.diff(x)
        dy = np.diff(y)
        n = len(dy)
        if n <= lag + 2:
            return None

        try:
            # Target rows: Δy_t for t = lag..n-1
            target = dy[lag:]
            rows = len(target)
            X_cols = []
            for i in range(1, lag + 1):
                X_cols.append(dx[lag - i:lag - i + rows])
            # AR(1) term on Δy
            X_cols.append(dy[lag - 1:lag - 1 + rows])
            X_cols.append(np.ones(rows))
            X = np.column_stack(X_cols)
            if X.shape[0] < X.shape[1] + 2:
                return None
            coeffs, _, rank, _ = np.linalg.lstsq(X, target, rcond=None)
            if rank < X.shape[1]:
                return None
            beta_sum = float(np.sum(coeffs[:lag]))
        except Exception as exc:
            logger.debug(f"coef_sign fit failed for {signal_var.name}->{target_var.name}: {exc}")
            self._coef_sign_cache[cache_key] = None
            return None

        sign = 1 if beta_sum >= 0 else -1
        self._coef_sign_cache[cache_key] = sign
        return sign

    # ------------------------------------------------------------------
    # Sub-model: OLS linear regression (expanding window)
    # ------------------------------------------------------------------

    def _ols_predict(
        self,
        signal_ts: List[Tuple[datetime, float]],
        target_ts: List[Tuple[datetime, float]],
        features: Optional[Dict] = None,
    ) -> Dict:
        """Expanding-window OLS regression predicting next target value.

        When *features* are supplied (ma_7, roc_30, volatility_90) they are
        added as extra regressors alongside the raw signal for a multivariate
        fit.  Falls back to univariate if the feature matrix is degenerate.

        When ``self.ols_mode == 'differences'`` (v4), regresses on first
        differences with an autoregressive term:
            Δy_t = α + β·Δx_{t-1} + γ·Δy_{t-1}
        avoiding spurious-regression bias from level-on-level OLS.
        """
        # Align signal and target by date (monthly)
        sig_dict = {d.strftime("%Y-%m"): v for d, v in signal_ts}
        tgt_dict = {d.strftime("%Y-%m"): v for d, v in target_ts}
        common = sorted(set(sig_dict) & set(tgt_dict))

        if len(common) < MIN_OLS_TRAIN_MONTHS:
            return {"direction": None, "confidence": 0.0, "reason": "insufficient aligned data"}

        x_raw = np.array([sig_dict[k] for k in common])
        y = np.array([tgt_dict[k] for k in common])

        # --- v4: differenced VAR(1) regression -----------------------------
        if self.ols_mode == "differences" and len(common) >= MIN_OLS_TRAIN_MONTHS + 2:
            try:
                dx = np.diff(x_raw)
                dy = np.diff(y)
                if len(dy) >= MIN_OLS_TRAIN_MONTHS:
                    target_d = dy[1:]
                    X_d = np.column_stack([
                        dx[:-1],          # β · Δx_{t-1}
                        dy[:-1],          # γ · Δy_{t-1}
                        np.ones(len(target_d)),
                    ])
                    coeffs_d, _, rank_d, _ = np.linalg.lstsq(X_d, target_d, rcond=None)
                    if rank_d >= X_d.shape[1]:
                        # Forecast Δy_{t+1} from latest observed Δx_t and Δy_t
                        x_next_d = np.array([dx[-1], dy[-1], 1.0])
                        delta_y_next = float(x_next_d @ coeffs_d)
                        predicted_y = float(y[-1] + delta_y_next)
                        y_pred_d = X_d @ coeffs_d
                        ss_res = float(np.sum((target_d - y_pred_d) ** 2))
                        ss_tot = float(np.sum((target_d - np.mean(target_d)) ** 2))
                        r_sq = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
                        n_d = len(target_d)
                        p_d = X_d.shape[1]
                        adj_r_sq = (
                            1 - (1 - r_sq) * (n_d - 1) / max(n_d - p_d - 1, 1)
                            if n_d > p_d + 1 else r_sq
                        )
                        y_last = y[-1]
                        change_pct = (
                            (predicted_y - y_last) / abs(y_last) * 100
                        ) if y_last != 0 else 0.0
                        direction = "up" if predicted_y > y_last else "down"
                        confidence = max(0.0, min(adj_r_sq, 1.0))
                        return {
                            "direction": direction,
                            "confidence": round(confidence, 4),
                            "predicted_value": round(predicted_y, 4),
                            "predicted_change_pct": round(change_pct, 2),
                            "r_squared": round(r_sq, 4),
                            "adj_r_squared": round(adj_r_sq, 4),
                            "multivariate": True,
                            "mode": "differences",
                            "sample_size": len(common),
                        }
            except Exception as exc:
                logger.debug(f"differenced OLS failed, falling back: {exc}")
            # fall through to legacy path on failure

        # --- Attempt multivariate OLS when features flag is supplied -------
        # NOTE: `features` is treated as a boolean flag to enable multivariate
        # mode.  Per-row feature columns are built directly from x_raw so the
        # design matrix is genuinely full-rank (the previous implementation
        # broadcast scalar features as constant columns, which collapsed to
        # rank ≤ 2 and silently fell back to univariate — causing v2 to
        # produce identical predictions to v1).
        multivariate = False
        n = len(x_raw)
        if features and n >= MIN_OLS_TRAIN_MONTHS + 6:
            try:
                # Per-row rolling mean (window=3) of the signal
                ma3 = np.array([float(np.mean(x_raw[max(0, i - 2):i + 1])) for i in range(n)])
                # Per-row rolling mean (window=6) of the signal
                ma6 = np.array([float(np.mean(x_raw[max(0, i - 5):i + 1])) for i in range(n)])
                # Per-row 3-period rate of change
                roc = np.array([
                    float((x_raw[i] - x_raw[max(0, i - 3)]) / abs(x_raw[max(0, i - 3)]))
                    if x_raw[max(0, i - 3)] != 0 else 0.0
                    for i in range(n)
                ])
                X = np.column_stack([x_raw, ma3, ma6, roc, np.ones(n)])
                # Least-squares fit
                coeffs_mv, residuals, rank, sv = np.linalg.lstsq(X, y, rcond=None)
                if rank >= X.shape[1]:
                    # Predict using latest row
                    x_next_row = np.array([x_raw[-1], ma3[-1], ma6[-1], roc[-1], 1.0])
                    predicted_y = float(x_next_row @ coeffs_mv)
                    y_pred = X @ coeffs_mv
                    ss_res = float(np.sum((y - y_pred) ** 2))
                    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
                    p = X.shape[1]
                    r_sq = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
                    # Adjusted R² penalises extra regressors
                    adj_r_sq = 1 - (1 - r_sq) * (n - 1) / max(n - p - 1, 1) if n > p + 1 else r_sq
                    multivariate = True
            except Exception:
                pass  # fall through to univariate

        if not multivariate:
            # Univariate fallback: simple y = mx + b
            try:
                coeffs = np.polyfit(x_raw, y, 1)
            except (np.linalg.LinAlgError, ValueError):
                return {"direction": None, "confidence": 0.0, "reason": "OLS fit failed"}

            slope, intercept = coeffs
            predicted_y = slope * x_raw[-1] + intercept

            y_pred = np.polyval(coeffs, x_raw)
            ss_res = float(np.sum((y - y_pred) ** 2))
            ss_tot = float(np.sum((y - np.mean(y)) ** 2))
            r_sq = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
            adj_r_sq = r_sq  # no penalty for univariate

        y_last = y[-1]
        change_pct = ((predicted_y - y_last) / abs(y_last) * 100) if y_last != 0 else 0.0
        direction = "up" if predicted_y > y_last else "down"
        confidence = max(0.0, min(adj_r_sq, 1.0))

        return {
            "direction": direction,
            "confidence": round(confidence, 4),
            "predicted_value": round(predicted_y, 4),
            "predicted_change_pct": round(change_pct, 2),
            "r_squared": round(r_sq, 4),
            "adj_r_squared": round(adj_r_sq, 4),
            "multivariate": multivariate,
            "sample_size": len(common),
        }

    # ------------------------------------------------------------------
    # Sub-model: ARIMA forecasting
    # ------------------------------------------------------------------

    def _arima_predict(self, target_ts: List[Tuple[datetime, float]], target_name: str = "") -> Dict:
        """ARIMA forecast on target variable's own history.

        Tries multiple orders and selects the one with the lowest AIC.
        Caches the winning order per target to avoid repeated search.
        """
        if len(target_ts) < MIN_ARIMA_POINTS:
            return {"direction": None, "confidence": 0.0, "reason": "insufficient data for ARIMA"}

        values = np.array([v for _, v in target_ts])
        last_val = values[-1]

        try:
            from statsmodels.tsa.arima.model import ARIMA

            cache_key = target_name or "default"

            # Use cached order or search for best
            if cache_key in self._arima_order_cache:
                best_order = self._arima_order_cache[cache_key]
                model = ARIMA(values, order=best_order)
                fitted = model.fit()
            else:
                best_aic = float("inf")
                fitted = None
                best_order = (1, 1, 1)
                for order in self.ARIMA_ORDERS:
                    try:
                        m = ARIMA(values, order=order)
                        f = m.fit()
                        if f.aic < best_aic:
                            best_aic = f.aic
                            fitted = f
                            best_order = order
                    except Exception:
                        continue
                if fitted is None:
                    return {"direction": None, "confidence": 0.0, "reason": "all ARIMA orders failed"}
                self._arima_order_cache[cache_key] = best_order

            forecast_result = fitted.get_forecast(steps=1)
            forecast = forecast_result.predicted_mean[0]
            # Confidence from forecast standard error — lower SE → higher confidence
            forecast_se = forecast_result.se_mean[0] if hasattr(forecast_result, 'se_mean') else None
            if forecast_se is not None and abs(last_val) > 0:
                # Normalise SE relative to the last value; cap at 1.0
                confidence = max(0.0, min(1.0 - (forecast_se / abs(last_val)), 1.0))
            else:
                confidence = max(0.0, min(1.0 / (1.0 + abs(fitted.aic) / 1000.0), 1.0))

            direction = "up" if forecast > last_val else "down"
            change_pct = ((forecast - last_val) / abs(last_val) * 100) if last_val != 0 else 0.0

            return {
                "direction": direction,
                "confidence": round(confidence, 4),
                "forecast_value": round(forecast, 4),
                "predicted_change_pct": round(change_pct, 2),
                "aic": round(fitted.aic, 2),
                "order": list(best_order),
                # ARIMA-derived lag proxy (months) — dominant AR order signals
                # how many lags back the model considers significant.
                "optimal_lag_months": int(best_order[0]) if best_order[0] > 0 else 1,
            }
        except Exception as e:
            logger.warning(f"ARIMA fit failed: {e}")
            return {"direction": None, "confidence": 0.0, "reason": f"ARIMA error: {e}"}

    # ------------------------------------------------------------------
    # Feature engineering
    # ------------------------------------------------------------------

    def _arima_predict_fixed(self, target_ts: List[Tuple[datetime, float]]) -> Dict:
        """Fixed ARIMA(1,1,1) — replicates original v1 behaviour for replay."""
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
            aic = fitted.aic
            confidence = max(0.0, min(1.0 / (1.0 + abs(aic) / 1000.0), 1.0))
            return {
                "direction": direction,
                "confidence": round(confidence, 4),
                "forecast_value": round(forecast, 4),
                "predicted_change_pct": round(change_pct, 2),
                "aic": round(aic, 2),
                "order": [1, 1, 1],
                # Fixed ARIMA(1,1,1) — AR order = 1 → 1-month lag proxy
                "optimal_lag_months": 1,
            }
        except Exception as e:
            return {"direction": None, "confidence": 0.0, "reason": f"ARIMA error: {e}"}

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
        change_pct_sum = 0.0
        change_pct_weight = 0.0

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

            # Accumulate weighted predicted_change_pct from sub-models
            sub_change = result.get("predicted_change_pct")
            if sub_change is not None:
                change_pct_sum += w * sub_change
                change_pct_weight += w

        if active_models == 0:
            return {
                "direction": None,
                "confidence": 0.0,
                "predicted_change_pct": None,
                "active_models": 0,
                "sub_models": sub_models,
                "reason": "no sub-models produced a prediction",
            }

        direction = "up" if up_score >= down_score else "down"
        margin = abs(up_score - down_score)
        confidence = (margin / total_weight) if total_weight > 0 else 0.0
        confidence = min(confidence, 1.0)

        # Weighted average change_pct from sub-models that produced one
        predicted_change_pct = None
        if change_pct_weight > 0:
            predicted_change_pct = change_pct_sum / change_pct_weight
            # v4: James-Stein-style shrinkage toward zero to counteract the
            # systematic negative bias inherited from levels-OLS + ARIMA drift.
            # shrinkage_lambda < 1.0 pulls the prediction toward 0%.
            lam = self.shrinkage_lambda
            if lam is not None and lam != 1.0:
                lam = max(0.0, min(float(lam), 1.0))
                predicted_change_pct = predicted_change_pct * lam
            predicted_change_pct = round(predicted_change_pct, 2)

        # Extract lag prediction — blend granger lag with ARIMA-derived lag
        # using self.lag_blend_arima (0.0 = pure granger, 1.0 = pure ARIMA).
        # Per-version blending lets v1/v2/v3 produce visually distinct lag
        # traces on the dashboard even though Granger itself is config-free.
        granger = sub_models.get("granger", {})
        arima = sub_models.get("arima", {})
        granger_lag = granger.get("optimal_lag")
        arima_lag = arima.get("optimal_lag_months")
        if granger_lag is not None and arima_lag is not None and self.lag_blend_arima > 0.0:
            blend = max(0.0, min(self.lag_blend_arima, 1.0))
            optimal_lag = (1.0 - blend) * float(granger_lag) + blend * float(arima_lag)
        else:
            optimal_lag = granger_lag

        return {
            "direction": direction,
            "confidence": round(confidence, 4),
            "predicted_change_pct": predicted_change_pct,
            "optimal_lag": optimal_lag,
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

    def _calibrate_weights_global(self) -> Optional[Dict]:
        """Global weight calibration using ALL validated predictions (any pair).

        Fallback when per-pair calibration lacks data.  Requires ≥ 30
        validated predictions to activate.
        """
        preds = (
            self.db.query(PredictionTracking)
            .filter(
                PredictionTracking.status == "validated",
                PredictionTracking.direction_correct.isnot(None),
            )
            .all()
        )

        if len(preds) < 30:
            return None

        model_stats: Dict[str, Dict[str, int]] = {}
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
                continue
            else:
                continue

            if bucket not in model_stats:
                model_stats[bucket] = {"correct": 0, "total": 0}
            model_stats[bucket]["total"] += 1
            if p.direction_correct:
                model_stats[bucket]["correct"] += 1

        if not model_stats:
            return None

        accuracies = {}
        for m, s in model_stats.items():
            accuracies[m] = s["correct"] / s["total"] if s["total"] > 0 else 0.5

        total_acc = sum(accuracies.values())
        if total_acc == 0:
            return None

        calibrated = {}
        for m in DEFAULT_WEIGHTS:
            calibrated[m] = accuracies[m] / total_acc if m in accuracies else DEFAULT_WEIGHTS[m]

        total = sum(calibrated.values())
        if total > 0:
            calibrated = {k: round(v / total, 4) for k, v in calibrated.items()}

        logger.info(f"Global calibrated weights (from {len(preds)} predictions): {calibrated}")
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
        arima = ensemble.get("sub_models", {}).get("arima", {})
        granger = ensemble.get("sub_models", {}).get("granger", {})

        # Fallback chain for predicted_change_pct: ensemble combined → OLS → ARIMA → Granger momentum
        # Use explicit `is not None` checks — Python `or` treats 0.0 as falsy
        change_pct = ensemble.get("predicted_change_pct")
        if change_pct is None:
            change_pct = ols.get("predicted_change_pct")
        if change_pct is None:
            change_pct = arima.get("predicted_change_pct")
        if change_pct is None and granger.get("momentum") is not None:
            change_pct = round(granger["momentum"] * 100, 2)

        # Dedup: if a pending ensemble prediction exists for the same pair
        # within the last 7 days, update it instead of inserting a duplicate
        cutoff = datetime.utcnow() - timedelta(days=7)
        existing = (
            self.db.query(PredictionTracking)
            .filter(
                PredictionTracking.signal_name == signal_var.name,
                PredictionTracking.target_name == target_var.name,
                PredictionTracking.model_version.like("ensemble%"),
                PredictionTracking.status == "pending",
                PredictionTracking.predicted_at >= cutoff,
            )
            .first()
        )

        # Extract optimal lag from ensemble output (sourced from Granger sub-model)
        optimal_lag = ensemble.get("optimal_lag")

        if existing:
            # Update the existing prediction with fresh results
            existing.predicted_at = datetime.utcnow()
            existing.target_date = datetime.utcnow() + timedelta(days=30)
            existing.predicted_direction = ensemble["direction"]
            existing.predicted_value = ols.get("predicted_value")
            existing.predicted_change_pct = change_pct
            existing.current_target_value = last_target_val
            existing.r_squared = ols.get("r_squared")
            existing.confidence = _confidence_label(ensemble["confidence"])
            existing.granger_p_value = granger.get("p_value")
            existing.optimal_lag_days = optimal_lag
            self.db.flush()
            return

        pred = PredictionTracking(
            prediction_id=f"ensemble_{uuid.uuid4().hex[:12]}",
            signal_name=signal_var.name,
            target_name=target_var.name,
            predicted_at=datetime.utcnow(),
            target_date=datetime.utcnow() + timedelta(days=30),
            predicted_direction=ensemble["direction"],
            predicted_value=ols.get("predicted_value"),
            predicted_change_pct=change_pct,
            current_target_value=last_target_val,
            r_squared=ols.get("r_squared"),
            confidence=_confidence_label(ensemble["confidence"]),
            model_version="ensemble_v2",
            granger_p_value=granger.get("p_value"),
            optimal_lag_days=optimal_lag,
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
# Model version configs for replay
# ------------------------------------------------------------------

MODEL_VERSION_CONFIGS = [
    {
        "version": "v1",
        "label": "Baseline (univariate OLS, fixed ARIMA, default weights)",
        "multivariate_ols": False,
        "adaptive_arima": False,
        "global_calibration": False,
        "lag_blend_arima": 0.0,
    },
    {
        "version": "v2",
        "label": "+Multivariate OLS",
        "multivariate_ols": True,
        "adaptive_arima": False,
        "global_calibration": False,
        "lag_blend_arima": 0.3,
    },
    {
        "version": "v3",
        "label": "+Multivariate OLS +Adaptive ARIMA +Global Calibration",
        "multivariate_ols": True,
        "adaptive_arima": True,
        "global_calibration": True,
        "lag_blend_arima": 0.6,
    },
    {
        "version": "v4",
        "label": "Ensemble v4",
        "multivariate_ols": True,
        "adaptive_arima": True,
        "global_calibration": True,
        "lag_blend_arima": 0.6,
        # v4-specific corrections
        "granger_use_coefficient_sign": True,
        "ols_mode": "differences",
        "shrinkage_lambda": 0.95,
    },
]


def replay_validated_predictions(db: Session, configs: Optional[List[Dict]] = None, max_predictions: int = 500) -> Dict:
    """Replay validated predictions through different model configs.

    For each validated prediction with a known actual direction, loads
    the time series data available at prediction time and re-runs each
    model config.  Returns per-version monthly aggregates suitable for
    overlaying on the existing 3 charts.

    *max_predictions* caps the sample size for performance.  Predictions
    are sampled evenly across time so monthly coverage is preserved.
    """
    from collections import defaultdict
    from statistics import median

    if configs is None:
        configs = MODEL_VERSION_CONFIGS

    # 1. Load all validated predictions with known actuals
    preds = (
        db.query(PredictionTracking)
        .filter(
            PredictionTracking.status == "validated",
            PredictionTracking.actual_direction.isnot(None),
        )
        .order_by(PredictionTracking.predicted_at.asc())
        .all()
    )

    if not preds:
        return {"versions": [], "actuals": {"time_series": []}, "total_predictions": 0}

    # Downsample evenly if too many predictions (preserve time distribution)
    total_available = len(preds)
    if len(preds) > max_predictions:
        step = len(preds) / max_predictions
        preds = [preds[int(i * step)] for i in range(max_predictions)]
        logger.info(f"Replay: sampled {len(preds)} of {total_available} predictions")

    # 2. Preload time series and variables
    var_cache: Dict[str, VariableMetadata] = {}
    ts_cache: Dict[int, List[Tuple[datetime, float]]] = {}

    def get_var(name: str) -> Optional[VariableMetadata]:
        if name not in var_cache:
            # Try name first, then display_name (predictions may store either)
            result = (
                db.query(VariableMetadata)
                .filter(VariableMetadata.name == name)
                .first()
            )
            if result is None:
                result = (
                    db.query(VariableMetadata)
                    .filter(VariableMetadata.display_name == name)
                    .first()
                )
            var_cache[name] = result
        return var_cache[name]

    def get_ts(variable_id: int) -> List[Tuple[datetime, float]]:
        if variable_id not in ts_cache:
            rows = (
                db.query(TimeSeriesData)
                .filter(TimeSeriesData.variable_id == variable_id)
                .order_by(TimeSeriesData.timestamp.asc())
                .all()
            )
            ts_cache[variable_id] = [(r.timestamp, r.value) for r in rows]
        return ts_cache[variable_id]

    # 3. Build actuals monthly aggregation
    actuals_monthly: Dict[str, Dict] = defaultdict(lambda: {
        "act_change": [], "act_lag": [], "count": 0
    })
    for p in preds:
        if p.predicted_at:
            mk = p.predicted_at.strftime("%Y-%m")
            actuals_monthly[mk]["count"] += 1
            if p.actual_change_pct is not None:
                actuals_monthly[mk]["act_change"].append(p.actual_change_pct)
            if p.actual_lag_days is not None:
                actuals_monthly[mk]["act_lag"].append(p.actual_lag_days)

    actuals_ts = []
    for mk in sorted(actuals_monthly.keys()):
        m = actuals_monthly[mk]
        actuals_ts.append({
            "month": mk,
            "avg_actual_change_pct": round(median(m["act_change"]), 2) if m["act_change"] else None,
            "avg_actual_lag": round(sum(m["act_lag"]) / len(m["act_lag"]), 1) if m["act_lag"] else None,
            "count": m["count"],
        })

    # 4. For each config, replay every prediction
    version_results = []
    for cfg in configs:
        model = EnsembleModel(db)
        model._arima_order_cache = {}

        per_pred: Dict[str, Dict] = defaultdict(lambda: {
            "pred_change": [], "pred_lag": [], "direction_correct": [], "count": 0
        })
        total_correct = 0
        total_count = 0

        for p in preds:
            signal_var = get_var(p.signal_name)
            target_var = get_var(p.target_name)
            if not signal_var or not target_var:
                continue

            # Filter time series to data available at prediction time
            full_signal_ts = get_ts(signal_var.id)
            full_target_ts = get_ts(target_var.id)
            cutoff = p.predicted_at
            # Normalise cutoff to naive datetime for comparison with date/datetime timestamps
            if hasattr(cutoff, 'tzinfo') and cutoff.tzinfo is not None:
                cutoff = cutoff.replace(tzinfo=None)
            signal_ts = []
            for d, v in full_signal_ts:
                d_cmp = d if isinstance(d, datetime) else datetime(d.year, d.month, d.day)
                if hasattr(d_cmp, 'tzinfo') and d_cmp.tzinfo is not None:
                    d_cmp = d_cmp.replace(tzinfo=None)
                if d_cmp <= cutoff:
                    signal_ts.append((d, v))
            target_ts = []
            for d, v in full_target_ts:
                d_cmp = d if isinstance(d, datetime) else datetime(d.year, d.month, d.day)
                if hasattr(d_cmp, 'tzinfo') and d_cmp.tzinfo is not None:
                    d_cmp = d_cmp.replace(tzinfo=None)
                if d_cmp <= cutoff:
                    target_ts.append((d, v))

            if len(target_ts) < MIN_OLS_TRAIN_MONTHS:
                continue

            # Run sub-models with the config's settings
            features = model._engineer_features(signal_ts)

            # v4: sign-aware Granger and differenced OLS
            model.granger_use_coefficient_sign = bool(cfg.get("granger_use_coefficient_sign", False))
            model.ols_mode = str(cfg.get("ols_mode", "levels"))

            # OLS: multivariate or univariate
            if cfg.get("multivariate_ols"):
                ols_result = model._ols_predict(signal_ts, target_ts, features=features)
            else:
                ols_result = model._ols_predict(signal_ts, target_ts, features=None)

            # ARIMA: adaptive or fixed
            if cfg.get("adaptive_arima"):
                arima_result = model._arima_predict(target_ts, target_name=p.target_name)
            else:
                # Fixed ARIMA(1,1,1) — replicate v1 behaviour
                arima_result = model._arima_predict_fixed(target_ts)

            # Granger always the same (data-driven, no config knob)
            granger_result = model._granger_predict(signal_var, target_var, signal_ts, target_ts)

            sub_models = {"granger": granger_result, "ols": ols_result, "arima": arima_result}

            # Weights: global calibration or defaults
            if cfg.get("global_calibration"):
                calibrated = model._calibrate_weights(p.signal_name, p.target_name)
                if not calibrated:
                    calibrated = model._calibrate_weights_global()
                if calibrated:
                    model.weights = calibrated
                else:
                    model.weights = dict(DEFAULT_WEIGHTS)
            else:
                model.weights = dict(DEFAULT_WEIGHTS)

            # Apply per-version lag blending so each version produces a
            # distinct optimal_lag in the ensemble output (pure-granger lag
            # is identical across versions and would collapse the Lag chart).
            model.lag_blend_arima = float(cfg.get("lag_blend_arima", 0.0))
            # v4 knobs (no-op for v1/v2/v3)
            model.shrinkage_lambda = float(cfg.get("shrinkage_lambda", 1.0))

            ensemble = model._combine(sub_models)
            pred_direction = ensemble.get("direction")
            if pred_direction is None:
                continue

            is_correct = pred_direction == p.actual_direction
            total_count += 1
            if is_correct:
                total_correct += 1

            mk = p.predicted_at.strftime("%Y-%m")
            per_pred[mk]["count"] += 1
            per_pred[mk]["direction_correct"].append(is_correct)
            if ensemble.get("predicted_change_pct") is not None:
                per_pred[mk]["pred_change"].append(ensemble["predicted_change_pct"])
            if ensemble.get("optimal_lag") is not None:
                per_pred[mk]["pred_lag"].append(ensemble["optimal_lag"] * 30 if ensemble["optimal_lag"] else 30)

        logger.info(f"Replay {cfg['version']}: {total_count}/{len(preds)} succeeded")

        # Build monthly time series for this version
        version_ts = []
        for mk in sorted(per_pred.keys()):
            m = per_pred[mk]
            dc = m["direction_correct"]
            version_ts.append({
                "month": mk,
                "avg_predicted_change_pct": round(median(m["pred_change"]), 2) if m["pred_change"] else None,
                "avg_predicted_lag": round(sum(m["pred_lag"]) / len(m["pred_lag"]), 1) if m["pred_lag"] else None,
                "direction_accuracy": round(sum(dc) / len(dc) * 100, 1) if dc else None,
                "count": m["count"],
            })

        version_results.append({
            "version": cfg["version"],
            "label": cfg["label"],
            "overall_accuracy": round(total_correct / total_count * 100, 1) if total_count > 0 else None,
            "total": total_count,
            "correct": total_correct,
            "time_series": version_ts,
        })

    return {
        "versions": version_results,
        "actuals": {"time_series": actuals_ts},
        "total_predictions": len(preds),
    }


# ------------------------------------------------------------------
# Convenience function for scheduled tasks
# ------------------------------------------------------------------

def run_ensemble_predictions(db_session_factory, max_pairs: int = 200) -> Dict:
    """Entry point for APScheduler — runs ensemble on all significant pairs."""
    session = db_session_factory()
    try:
        # Purge stale pending ensemble predictions older than 7 days
        stale_cutoff = datetime.utcnow() - timedelta(days=7)
        stale_deleted = (
            session.query(PredictionTracking)
            .filter(
                PredictionTracking.model_version.like("ensemble%"),
                PredictionTracking.status == "pending",
                PredictionTracking.predicted_at < stale_cutoff,
            )
            .delete(synchronize_session="fetch")
        )
        if stale_deleted:
            logger.info(f"Purged {stale_deleted} stale pending ensemble predictions")

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
