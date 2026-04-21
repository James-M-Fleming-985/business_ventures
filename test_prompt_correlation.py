"""Tests for PR7 prompt-version stamp + correlation grouping logic."""
from __future__ import annotations

import os
import sys
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


@pytest.fixture
def db_session():
    import models as m
    engine = create_engine("sqlite:///:memory:")
    m.Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _rec(db):
    from models import ExploitationRecommendation
    rec = ExploitationRecommendation(
        signal_name="s", signal_display_name="S",
        target_name="t", target_display_name="T",
        action_type="BUILD",
    )
    db.add(rec); db.commit()
    return rec


def _build(db, rec_id, version, status="LIVE", verified_pct=None, blocked=False):
    from models import MVPBuild
    steps = []
    if blocked:
        steps.append({"step": "VERIFICATION_BLOCKED_DEPLOY", "at": datetime.utcnow().isoformat()})
    ac = None
    if verified_pct is not None:
        ac = {"summary": {"verified_pct": verified_pct}, "by_ac": {}}
    b = MVPBuild(
        recommendation_id=rec_id, complexity="LOW",
        status=status, prompt_version=version,
        ac_verification=ac, build_steps=steps,
    )
    db.add(b); db.commit(); db.refresh(b)
    return b


def _telemetry(db, build_id, score, revenue_cents=0, visitors=0):
    from models import BuildTelemetry
    t = BuildTelemetry(
        build_id=build_id, learning_score=score,
        total_revenue_cents=revenue_cents, unique_visitors=visitors,
    )
    db.add(t); db.commit()
    return t


def test_prompt_version_constant_present():
    from services.ai_code_generator_orchestrator import PROMPT_VERSION
    assert isinstance(PROMPT_VERSION, str) and PROMPT_VERSION


def test_correlation_groups_by_prompt_version(db_session):
    """Replicates the endpoint's grouping logic against in-memory DB."""
    from collections import defaultdict
    from models import BuildTelemetry, MVPBuild

    rec = _rec(db_session)
    b1 = _build(db_session, rec.id, "v1.0", verified_pct=90)
    b2 = _build(db_session, rec.id, "v1.0", verified_pct=70, blocked=True)
    b3 = _build(db_session, rec.id, "v2.0", verified_pct=85, status="FAILED")
    _telemetry(db_session, b1.id, 0.8, revenue_cents=5000, visitors=100)
    _telemetry(db_session, b2.id, 0.4)
    _telemetry(db_session, b3.id, 0.6, revenue_cents=2000, visitors=50)

    builds = db_session.query(MVPBuild).filter(MVPBuild.prompt_version.isnot(None)).all()
    tel = {t.build_id: t for t in db_session.query(BuildTelemetry).all()}

    groups = defaultdict(lambda: {
        "count": 0, "live": 0, "scores": [], "ac": [], "blocked": 0, "rev_cents": 0,
    })
    for b in builds:
        g = groups[b.prompt_version]
        g["count"] += 1
        if b.status == "LIVE":
            g["live"] += 1
        pct = (b.ac_verification or {}).get("summary", {}).get("verified_pct")
        if pct is not None:
            g["ac"].append(pct)
        if any(s.get("step") == "VERIFICATION_BLOCKED_DEPLOY" for s in (b.build_steps or [])):
            g["blocked"] += 1
        t = tel.get(b.id)
        if t and t.learning_score is not None:
            g["scores"].append(t.learning_score)
            g["rev_cents"] += t.total_revenue_cents or 0

    assert groups["v1.0"]["count"] == 2
    assert groups["v1.0"]["live"] == 2
    assert groups["v1.0"]["blocked"] == 1
    assert groups["v1.0"]["rev_cents"] == 5000
    assert sum(groups["v1.0"]["scores"]) / 2 == pytest.approx(0.6, abs=1e-4)
    assert groups["v2.0"]["count"] == 1
    assert groups["v2.0"]["live"] == 0
