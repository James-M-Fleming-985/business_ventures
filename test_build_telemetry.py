"""Tests for services.build_telemetry_service (PR5)."""
from __future__ import annotations

import os
import sys
import types
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.build_telemetry_service import (  # noqa: E402
    ENGAGEMENT_VISITORS_CAP,
    REVENUE_DOLLARS_CAP,
    compute_engagement_revenue_score,
)


# ---------- compute_engagement_revenue_score ---------------------------------

def test_score_zero_when_no_signal():
    assert compute_engagement_revenue_score(0, 0) == 0.0


def test_score_one_when_both_saturated():
    score = compute_engagement_revenue_score(
        ENGAGEMENT_VISITORS_CAP * 10,
        int(REVENUE_DOLLARS_CAP * 100 * 10),
    )
    assert score == 1.0


def test_score_balances_engagement_and_revenue_equally():
    only_eng = compute_engagement_revenue_score(ENGAGEMENT_VISITORS_CAP, 0)
    only_rev = compute_engagement_revenue_score(0, int(REVENUE_DOLLARS_CAP * 100))
    assert only_eng == pytest.approx(0.5, abs=1e-4)
    assert only_rev == pytest.approx(0.5, abs=1e-4)


def test_score_negative_inputs_clamped():
    assert compute_engagement_revenue_score(-5, -100) == 0.0


def test_score_partial_signals_sum():
    # Half engagement + half revenue cap -> 0.25 + 0.25 = 0.5
    score = compute_engagement_revenue_score(
        ENGAGEMENT_VISITORS_CAP // 2,
        int(REVENUE_DOLLARS_CAP * 100 // 2),
    )
    assert score == pytest.approx(0.5, abs=1e-4)


# ---------- recompute_build_telemetry ---------------------------------------
# Use SQLite in-memory + the real models to keep this lightweight.

@pytest.fixture
def db_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Models import from main app; need a clean Base.
    import models as m
    engine = create_engine("sqlite:///:memory:")
    m.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _make_build(db, **overrides):
    from models import ExploitationRecommendation, MVPBuild
    rec = ExploitationRecommendation(
        signal_name="sig", signal_display_name="Sig",
        target_name="tgt", target_display_name="Tgt",
        action_type="BUILD",
    )
    db.add(rec)
    db.commit()
    defaults = dict(
        recommendation_id=rec.id,
        complexity="LOW",
        status="LIVE",
        created_at=datetime.utcnow(),
    )
    defaults.update(overrides)
    b = MVPBuild(**defaults)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


def test_recompute_returns_none_for_unknown_build(db_session):
    from services.build_telemetry_service import recompute_build_telemetry
    assert recompute_build_telemetry(db_session, 99999) is None


def test_recompute_zero_telemetry_for_fresh_build(db_session):
    from services.build_telemetry_service import recompute_build_telemetry
    b = _make_build(db_session)
    out = recompute_build_telemetry(db_session, b.id)
    assert out is not None
    assert out["build_id"] == b.id
    assert out["page_views"] == 0
    assert out["unique_visitors"] == 0
    assert out["total_revenue_cents"] == 0
    assert out["learning_score"] == 0.0


def test_recompute_aggregates_revenue_via_build_id(db_session):
    from models import RevenueEvent
    from services.build_telemetry_service import recompute_build_telemetry
    b = _make_build(db_session)
    for amount in (1000, 2500, 500):
        db_session.add(RevenueEvent(
            app_id="x", build_id=b.id,
            event_type="subscription_renewed",
            amount_cents=amount, currency="usd",
            event_at=datetime.utcnow(),
        ))
    db_session.commit()
    out = recompute_build_telemetry(db_session, b.id)
    assert out["total_revenue_cents"] == 4000
    assert out["revenue_event_count"] == 3
    assert out["learning_score"] > 0.0


def test_recompute_falls_back_to_page_view_beacons(db_session):
    from models import MvpPageView
    from services.build_telemetry_service import recompute_build_telemetry
    b = _make_build(db_session)
    for i in range(5):
        db_session.add(MvpPageView(
            build_id=b.id,
            visitor_hash=f"hash_{i % 2}",  # 2 unique visitors, 5 views
        ))
    db_session.commit()
    out = recompute_build_telemetry(db_session, b.id)
    assert out["page_views"] == 5
    assert out["unique_visitors"] == 2


def test_recompute_is_idempotent_upsert(db_session):
    from models import BuildTelemetry
    from services.build_telemetry_service import recompute_build_telemetry
    b = _make_build(db_session)
    recompute_build_telemetry(db_session, b.id)
    recompute_build_telemetry(db_session, b.id)
    rows = db_session.query(BuildTelemetry).filter(BuildTelemetry.build_id == b.id).all()
    assert len(rows) == 1
