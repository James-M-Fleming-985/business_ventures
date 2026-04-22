"""
Build Telemetry Service (PR5 — Track I autonomous loop closure).

Aggregates per-build engagement and revenue from the existing data sources
(MvpPageView beacons, ProductMetrics from GA4, RevenueEvent from Stripe)
into a single BuildTelemetry row, plus a composite ``learning_score`` the
autonomous loop uses to answer the two governing questions:

    1. What gets the highest engagement?
    2. What gets the highest revenue?

The score is intentionally simple at PR5 — a normalised weighted sum so it
can be charted on day one. PR7 will replace it with prompt-versioned
correlation analysis.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# Weights for the composite learning score. Engagement and revenue are
# treated as equally important — the loop should not optimise revenue at
# the expense of dead apps, nor traffic at the expense of monetisation.
WEIGHT_ENGAGEMENT = 0.5
WEIGHT_REVENUE = 0.5

# Soft caps used to normalise to [0, 1] before weighting. Builds at or
# above the cap saturate at 1.0; tunable via env later.
ENGAGEMENT_VISITORS_CAP = 1000   # 1k uniques saturates engagement
REVENUE_DOLLARS_CAP = 1000.0     # $1,000 total revenue saturates monetisation


def compute_engagement_revenue_score(
    unique_visitors: int,
    total_revenue_cents: int,
) -> float:
    """Return a [0, 1] composite score balancing engagement and revenue."""
    eng = min(1.0, max(0, unique_visitors) / ENGAGEMENT_VISITORS_CAP)
    rev_dollars = max(0, total_revenue_cents) / 100.0
    rev = min(1.0, rev_dollars / REVENUE_DOLLARS_CAP)
    return round(WEIGHT_ENGAGEMENT * eng + WEIGHT_REVENUE * rev, 4)


def recompute_build_telemetry(db: Session, build_id: int) -> Optional[dict]:
    """Recompute and upsert the BuildTelemetry row for a single build.

    Returns the resulting row as a dict, or None if the build does not exist.
    Safe to call repeatedly; idempotent.
    """
    # Imported lazily to keep this module importable in lightweight contexts
    # (e.g. tests / migrations).
    from models import (
        BuildTelemetry,
        MVPBuild,
        MvpPageView,
        ProductDeployment,
        ProductMetrics,
        RevenueEvent,
    )

    build = db.query(MVPBuild).filter(MVPBuild.id == build_id).first()
    if not build:
        return None

    # --- Engagement: prefer GA4-backed ProductMetrics, fall back to raw beacons.
    page_views = 0
    unique_visitors = 0
    avg_session_seconds: Optional[float] = None

    deployment = (
        db.query(ProductDeployment)
        .filter(ProductDeployment.build_id == build_id)
        .order_by(ProductDeployment.deployed_at.desc().nullslast())
        .first()
    )
    if deployment is not None:
        latest = (
            db.query(ProductMetrics)
            .filter(ProductMetrics.deployment_id == deployment.id)
            .order_by(ProductMetrics.period_end.desc())
            .first()
        )
        if latest is not None:
            page_views = latest.page_views or 0
            unique_visitors = latest.unique_visitors or 0
            avg_session_seconds = latest.avg_session_seconds

    if page_views == 0 and unique_visitors == 0:
        # Fall back to raw page-view beacons keyed directly on build_id.
        beacon_total = (
            db.query(func.count(MvpPageView.id))
            .filter(MvpPageView.build_id == build_id)
            .scalar()
            or 0
        )
        beacon_unique = (
            db.query(func.count(func.distinct(MvpPageView.visitor_hash)))
            .filter(MvpPageView.build_id == build_id)
            .scalar()
            or 0
        )
        page_views = beacon_total
        unique_visitors = beacon_unique

    # --- Revenue: prefer direct build_id binding, fall back to deployment.app_id.
    rev_filter = RevenueEvent.build_id == build_id
    rev_count = db.query(RevenueEvent).filter(rev_filter).count()
    if rev_count == 0 and deployment is not None and deployment.app_id:
        rev_filter = RevenueEvent.app_id == deployment.app_id
        rev_count = db.query(RevenueEvent).filter(rev_filter).count()

    total_revenue_cents = (
        db.query(func.coalesce(func.sum(RevenueEvent.amount_cents), 0))
        .filter(rev_filter)
        .scalar()
        or 0
    )

    # MRR + subscriber count: take the most recent ProductMetrics row.
    mrr_cents = 0
    subscriber_count = 0
    if deployment is not None:
        latest = (
            db.query(ProductMetrics)
            .filter(ProductMetrics.deployment_id == deployment.id)
            .order_by(ProductMetrics.period_end.desc())
            .first()
        )
        if latest is not None:
            mrr_cents = latest.mrr_cents or 0
            subscriber_count = latest.subscriber_count or 0

    learning_score = compute_engagement_revenue_score(
        unique_visitors=unique_visitors,
        total_revenue_cents=total_revenue_cents,
    )

    # Upsert
    row = (
        db.query(BuildTelemetry)
        .filter(BuildTelemetry.build_id == build_id)
        .first()
    )
    now = datetime.utcnow()
    if row is None:
        row = BuildTelemetry(build_id=build_id)
        db.add(row)
    row.page_views = page_views
    row.unique_visitors = unique_visitors
    row.avg_session_seconds = avg_session_seconds
    row.total_revenue_cents = int(total_revenue_cents)
    row.mrr_cents = int(mrr_cents)
    row.subscriber_count = int(subscriber_count)
    row.revenue_event_count = int(rev_count)
    row.learning_score = learning_score
    row.last_recomputed_at = now
    db.commit()
    db.refresh(row)

    logger.info(
        "BuildTelemetry recomputed: build=%d visitors=%d revenue_cents=%d score=%.4f",
        build_id, unique_visitors, total_revenue_cents, learning_score,
    )
    return row.to_dict()


def aggregate_lineage_telemetry(db: Session, build_id: int) -> Optional[dict]:
    """PR8c: aggregate engagement + revenue across an entire iteration chain.

    Walks parent_build_id up to the root, then collects every descendant.
    Returns per-iteration breakdown plus chain totals so the loop can answer
    'did iteration N actually beat iteration N-1'.
    """
    from models import MVPBuild, RevenueEvent

    seed = db.query(MVPBuild).filter(MVPBuild.id == build_id).first()
    if seed is None:
        return None

    # Walk up to the root.
    root = seed
    visited = {root.id}
    while root.parent_build_id and root.parent_build_id not in visited:
        parent = db.query(MVPBuild).filter(MVPBuild.id == root.parent_build_id).first()
        if parent is None:
            break
        root = parent
        visited.add(root.id)

    # Collect entire chain by walking children breadth-first.
    chain_ids = [root.id]
    frontier = [root.id]
    while frontier:
        children = (
            db.query(MVPBuild.id)
            .filter(MVPBuild.parent_build_id.in_(frontier))
            .all()
        )
        next_frontier = [cid for (cid,) in children if cid not in chain_ids]
        chain_ids.extend(next_frontier)
        frontier = next_frontier

    # Per-build breakdown.
    iterations = []
    chain_revenue_cents = 0
    chain_event_count = 0
    chain_visitors = 0
    chain_page_views = 0
    for cid in chain_ids:
        # Ensure telemetry is fresh for each leg.
        recompute_build_telemetry(db, cid)
        from models import BuildTelemetry
        bt = db.query(BuildTelemetry).filter(BuildTelemetry.build_id == cid).first()
        b = db.query(MVPBuild).filter(MVPBuild.id == cid).first()
        if bt is None or b is None:
            continue
        iterations.append({
            "build_id": cid,
            "iteration_number": b.iteration_number or 1,
            "status": b.status,
            "page_views": bt.page_views or 0,
            "unique_visitors": bt.unique_visitors or 0,
            "total_revenue_cents": bt.total_revenue_cents or 0,
            "subscriber_count": bt.subscriber_count or 0,
            "learning_score": bt.learning_score,
        })
        chain_revenue_cents += bt.total_revenue_cents or 0
        chain_event_count += bt.revenue_event_count or 0
        chain_visitors += bt.unique_visitors or 0
        chain_page_views += bt.page_views or 0

    iterations.sort(key=lambda x: x["iteration_number"])

    return {
        "root_build_id": root.id,
        "iteration_count": len(iterations),
        "totals": {
            "page_views": chain_page_views,
            "unique_visitors": chain_visitors,
            "total_revenue_cents": chain_revenue_cents,
            "revenue_event_count": chain_event_count,
        },
        "iterations": iterations,
    }
