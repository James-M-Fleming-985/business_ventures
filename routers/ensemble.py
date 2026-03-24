"""
Ensemble Predictions Router (M2 Track A)

Endpoints:
  GET  /api/ensemble/predictions         — list recent ensemble predictions
  POST /api/ensemble/predict             — run ensemble for a signal→target pair
  POST /api/ensemble/predict-all         — run ensemble for all significant pairs
  GET  /api/ensemble/model-accuracy      — per-model accuracy breakdown
  DELETE /api/ensemble/cleanup-duplicates — remove stale duplicate pending predictions
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models import PredictionTracking, VariableMetadata
from services.ensemble_model import EnsembleModel, LAYER1_SOURCES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ensemble", tags=["Ensemble Predictions"])


@router.get("/predictions")
def list_predictions(
    limit: int = Query(50, ge=1, le=500),
    model_version: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Return recent ensemble predictions."""
    q = db.query(PredictionTracking).filter(
        PredictionTracking.model_version.like("ensemble%")
    )
    if model_version:
        q = q.filter(PredictionTracking.model_version == model_version)

    preds = q.order_by(PredictionTracking.predicted_at.desc()).limit(limit).all()

    return {
        "count": len(preds),
        "predictions": [
            {
                "prediction_id": p.prediction_id,
                "signal": p.signal_name,
                "target": p.target_name,
                "direction": p.predicted_direction,
                "confidence": p.confidence,
                "predicted_value": p.predicted_value,
                "predicted_change_pct": p.predicted_change_pct,
                "model_version": p.model_version,
                "predicted_at": p.predicted_at.isoformat() if p.predicted_at else None,
                "target_date": p.target_date.isoformat() if p.target_date else None,
                "status": p.status,
                "direction_correct": p.direction_correct,
            }
            for p in preds
        ],
    }


@router.post("/predict")
def predict_pair(
    signal_name: str = Query(...),
    target_name: str = Query(...),
    db: Session = Depends(get_db),
):
    """Run ensemble prediction for a single signal→target pair."""
    model = EnsembleModel(db)
    result = model.predict(signal_name, target_name, store=True)
    db.commit()
    return result


@router.post("/predict-all")
def predict_all(
    max_pairs: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Run ensemble predictions for all significant Granger pairs."""
    model = EnsembleModel(db)
    result = model.predict_all_pairs(max_pairs=max_pairs, store=True)
    db.commit()
    return result


@router.delete("/cleanup-duplicates")
def cleanup_duplicates(db: Session = Depends(get_db)):
    """Remove duplicate pending ensemble predictions, keeping only the latest per pair."""
    preds = (
        db.query(PredictionTracking)
        .filter(
            PredictionTracking.model_version.like("ensemble%"),
            PredictionTracking.status == "pending",
        )
        .order_by(PredictionTracking.predicted_at.desc())
        .all()
    )

    seen = set()
    to_delete = []
    for p in preds:
        key = (p.signal_name, p.target_name)
        if key in seen:
            to_delete.append(p)
        else:
            seen.add(key)

    for p in to_delete:
        db.delete(p)
    db.commit()
    return {"deleted": len(to_delete), "unique_pairs_remaining": len(seen)}


@router.delete("/cleanup-same-layer")
def cleanup_same_layer(db: Session = Depends(get_db)):
    """Remove ensemble predictions that violate cross-layer design.

    Deletes predictions where:
    - Both signal and target are the same layer (e.g. wiki→wiki)
    - Signal is L2 and target is L1 (reversed orientation, e.g. stock→wiki)
    Only keeps: L1 signal → L2 target (the correct design).
    """
    preds = (
        db.query(PredictionTracking)
        .filter(PredictionTracking.model_version.like("ensemble%"))
        .all()
    )

    to_delete = []
    for p in preds:
        sig = db.query(VariableMetadata).filter(VariableMetadata.name == p.signal_name).first()
        tgt = db.query(VariableMetadata).filter(VariableMetadata.name == p.target_name).first()
        if not sig or not tgt:
            continue
        sig_l1 = sig.source in LAYER1_SOURCES
        tgt_l1 = tgt.source in LAYER1_SOURCES
        # Keep only L1 signal → L2 target
        if sig_l1 and not tgt_l1:
            continue  # correct orientation — keep
        to_delete.append(p)

    for p in to_delete:
        db.delete(p)
    db.commit()
    return {"deleted_same_layer": len(to_delete), "remaining": len(preds) - len(to_delete)}


@router.get("/model-accuracy")
def model_accuracy(db: Session = Depends(get_db)):
    """Per-model accuracy breakdown from validated predictions."""
    validated = (
        db.query(PredictionTracking)
        .filter(
            PredictionTracking.status == "validated",
            PredictionTracking.direction_correct.isnot(None),
        )
        .all()
    )

    buckets = {}
    for p in validated:
        mv = p.model_version or "unknown"
        if mv not in buckets:
            buckets[mv] = {"total": 0, "correct": 0}
        buckets[mv]["total"] += 1
        if p.direction_correct:
            buckets[mv]["correct"] += 1

    accuracy = {}
    for mv, stats in buckets.items():
        accuracy[mv] = {
            "total": stats["total"],
            "correct": stats["correct"],
            "accuracy_pct": round(stats["correct"] / stats["total"] * 100, 1)
            if stats["total"] > 0
            else 0.0,
        }

    return {"model_accuracy": accuracy, "total_validated": len(validated)}
