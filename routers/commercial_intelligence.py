"""
Commercial Intelligence Router (Track G — M2)

Exposes commercial intelligence data for the dashboard and
for the spec generator to consult during YAML generation.

Endpoints:
  GET  /api/commercial-intelligence           — full intelligence dashboard
  GET  /api/commercial-intelligence/rankings   — ranked deployments
  GET  /api/commercial-intelligence/winning    — winning configurations
  GET  /api/commercial-intelligence/reasoning  — plain-English summary
  POST /api/commercial-intelligence/confidence — configuration confidence score
  GET  /api/commercial-intelligence/demographics — demographic patterns
  POST /api/commercial-intelligence/aggregate  — trigger revenue aggregation
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from database import get_db
from services.commercial_intelligence_service import (
    aggregate_all_deployments,
    generate_commercial_reasoning,
    get_configuration_confidence,
    get_demographic_patterns,
    get_winning_configurations,
    rank_deployments,
)

from services.auth import require_admin

router = APIRouter(
    prefix="/api/commercial-intelligence",
    tags=["commercial-intelligence"],
    dependencies=[Depends(require_admin)],
)


class ConfidenceRequest(BaseModel):
    tech_stack: Optional[str] = None
    pricing_model: Optional[str] = None
    market_category: Optional[str] = None
    target_demographic: Optional[str] = None


@router.get("")
def commercial_intelligence_dashboard(db: Session = Depends(get_db)):
    """Full commercial intelligence dashboard payload.

    Returns rankings, winning configs, reasoning, and demographics in one call.
    """
    return {
        "rankings": rank_deployments(db, limit=20),
        "winning_configurations": get_winning_configurations(db),
        "reasoning": generate_commercial_reasoning(db),
        "demographics": get_demographic_patterns(db),
    }


@router.get("/rankings")
def get_rankings(limit: int = 20, db: Session = Depends(get_db)):
    """Deployments ranked by composite commercial score."""
    return {"rankings": rank_deployments(db, limit=limit)}


@router.get("/winning")
def get_winning(db: Session = Depends(get_db)):
    """Winning tech stacks, pricing models, market categories, demographics."""
    return get_winning_configurations(db)


@router.get("/reasoning")
def get_reasoning(db: Session = Depends(get_db)):
    """Plain-English commercial intelligence summary."""
    return {"reasoning": generate_commercial_reasoning(db)}


@router.post("/confidence")
def check_confidence(body: ConfidenceRequest, db: Session = Depends(get_db)):
    """Score confidence for a proposed build configuration."""
    return get_configuration_confidence(
        db,
        tech_stack=body.tech_stack,
        pricing_model=body.pricing_model,
        market_category=body.market_category,
        target_demographic=body.target_demographic,
    )


@router.get("/demographics")
def get_demographics(db: Session = Depends(get_db)):
    """Demographic patterns mapped to successful configurations."""
    return {"patterns": get_demographic_patterns(db)}


@router.post("/aggregate")
def trigger_aggregation(db: Session = Depends(get_db)):
    """Manually trigger revenue aggregation for all active deployments."""
    result = aggregate_all_deployments(db)
    return {"status": "ok", **result}
