"""
Build Intelligence Service

Aggregates the evidence that drives a build iteration:

- Parent build summary (status, errors, duration, files)
- Iteration chain summary (what each prior version was)
- Error patterns to avoid (categories that failed in prior builds)
- Engagement signals (unique visitors, page views, session depth)
- Revenue signals (MRR, subscribers, conversion rate)
- Signal freshness (latest ensemble prediction for the underlying signal pair)

Returned as a structured dict that the spec generator injects into the AI
prompt as evidence — the AI then derives the next iteration's YAML
requirements from what users are actually doing on the live app.

This is the iteration-time counterpart to the recommendation_meta payload
used for initial MVP builds.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def gather_iteration_intelligence(parent_build_id: int, db_session) -> Dict[str, Any]:
    """Collect all behavioural and historical evidence for an iteration.

    Returns a dict with the following keys (any may be ``None`` / empty):

    - ``parent``: summary of the immediate parent build
    - ``chain``: list of prior build summaries from root → parent
    - ``error_patterns``: aggregated error categories across the chain
    - ``engagement``: latest traffic / session metrics
    - ``revenue``: latest MRR / subscriber / conversion metrics
    - ``signal_freshness``: latest ensemble prediction for the signal pair
    - ``prior_files_summary``: list of file paths present in the parent build
    """
    from models import (
        MVPBuild,
        MVPBuildFile,
        ExploitationRecommendation,
    )

    parent = db_session.query(MVPBuild).filter(MVPBuild.id == parent_build_id).first()
    if not parent:
        return {}

    intelligence: Dict[str, Any] = {
        "parent": _summarise_build(parent),
        "chain": _build_chain_summary(parent_build_id, db_session),
        "error_patterns": _aggregate_error_patterns(parent_build_id, db_session),
        "engagement": _gather_engagement(parent, db_session),
        "revenue": _gather_revenue(parent, db_session),
        "signal_freshness": _gather_signal_freshness(parent, db_session),
        "prior_files_summary": _summarise_files(parent_build_id, db_session),
    }
    return intelligence


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _summarise_build(build) -> Dict[str, Any]:
    return {
        "build_id": build.id,
        "iteration_number": build.iteration_number or 1,
        "status": build.status,
        "complexity": build.complexity,
        "iterate_reason": build.iterate_reason,
        "duration_seconds": build.duration_seconds,
        "ai_cost_usd": build.ai_cost_usd,
        "total_errors": build.total_errors or 0,
        "error_breakdown": build.error_breakdown or {},
        "railway_url": build.railway_url,
        "github_url": build.github_url,
        "created_at": build.created_at.isoformat() if build.created_at else None,
    }


def _build_chain_summary(parent_build_id: int, db_session) -> List[Dict[str, Any]]:
    """Walk the chain from the root ancestor down to the immediate parent."""
    from models import MVPBuild

    parent = db_session.query(MVPBuild).filter(MVPBuild.id == parent_build_id).first()
    if not parent:
        return []

    chain: List[Dict[str, Any]] = []
    current = parent
    while current:
        chain.append(_summarise_build(current))
        if not current.parent_build_id:
            break
        current = (
            db_session.query(MVPBuild)
            .filter(MVPBuild.id == current.parent_build_id)
            .first()
        )
    chain.reverse()
    return chain


def _aggregate_error_patterns(parent_build_id: int, db_session) -> Dict[str, int]:
    """Sum error counts by category across the whole iteration chain."""
    chain = _build_chain_summary(parent_build_id, db_session)
    totals: Dict[str, int] = {}
    for entry in chain:
        breakdown = entry.get("error_breakdown") or {}
        for category, count in breakdown.items():
            if isinstance(count, (int, float)):
                totals[category] = totals.get(category, 0) + int(count)
    return totals


def _gather_engagement(build, db_session) -> Dict[str, Any]:
    """Pull the latest engagement metrics for the deployed product."""
    engagement: Dict[str, Any] = {
        "unique_visitors": 0,
        "page_views": 0,
        "avg_session_seconds": None,
        "raw_pageview_events_30d": 0,
        "source": None,
    }

    try:
        from models import ProductDeployment, ProductMetrics, MvpPageView
    except ImportError:
        return engagement

    deployment = (
        db_session.query(ProductDeployment)
        .filter(ProductDeployment.build_id == build.id)
        .order_by(ProductDeployment.created_at.desc())
        .first()
    )
    if deployment:
        latest_metric = (
            db_session.query(ProductMetrics)
            .filter(ProductMetrics.deployment_id == deployment.id)
            .order_by(ProductMetrics.period_end.desc())
            .first()
        )
        if latest_metric:
            engagement.update({
                "unique_visitors": latest_metric.unique_visitors or 0,
                "page_views": latest_metric.page_views or 0,
                "avg_session_seconds": latest_metric.avg_session_seconds,
                "source": latest_metric.source,
                "period_start": latest_metric.period_start.isoformat() if latest_metric.period_start else None,
                "period_end": latest_metric.period_end.isoformat() if latest_metric.period_end else None,
            })

    # Raw page-view beacon counts over the last 30 days
    try:
        cutoff = datetime.utcnow() - timedelta(days=30)
        raw_count = (
            db_session.query(MvpPageView)
            .filter(MvpPageView.build_id == build.id)
            .filter(MvpPageView.created_at >= cutoff)
            .count()
        )
        engagement["raw_pageview_events_30d"] = raw_count
    except Exception as exc:
        logger.debug("Raw page-view query failed: %s", exc)

    return engagement


def _gather_revenue(build, db_session) -> Dict[str, Any]:
    """Pull the latest revenue metrics for the deployed product."""
    revenue: Dict[str, Any] = {
        "mrr_usd": 0.0,
        "subscriber_count": 0,
        "conversion_rate": None,
        "churn_rate": None,
    }

    try:
        from models import ProductDeployment, ProductMetrics
    except ImportError:
        return revenue

    deployment = (
        db_session.query(ProductDeployment)
        .filter(ProductDeployment.build_id == build.id)
        .order_by(ProductDeployment.created_at.desc())
        .first()
    )
    if not deployment:
        return revenue

    latest_metric = (
        db_session.query(ProductMetrics)
        .filter(ProductMetrics.deployment_id == deployment.id)
        .order_by(ProductMetrics.period_end.desc())
        .first()
    )
    if latest_metric:
        revenue.update({
            "mrr_usd": round((latest_metric.mrr_cents or 0) / 100, 2),
            "subscriber_count": latest_metric.subscriber_count or 0,
            "conversion_rate": latest_metric.conversion_rate,
            "churn_rate": latest_metric.churn_rate,
        })

    return revenue


def _gather_signal_freshness(build, db_session) -> Dict[str, Any]:
    """Latest ensemble prediction for the recommendation's signal pair.

    Tells the iteration spec whether the underlying causal signal that
    motivated the original build is still strong, weakening, or pivoted.
    """
    freshness: Dict[str, Any] = {"available": False}

    try:
        from models import (
            ExploitationRecommendation,
            PredictionTracking,
        )
    except ImportError:
        return freshness

    rec = (
        db_session.query(ExploitationRecommendation)
        .filter(ExploitationRecommendation.id == build.recommendation_id)
        .first()
    )
    if not rec:
        return freshness

    latest = (
        db_session.query(PredictionTracking)
        .filter(PredictionTracking.signal_name == rec.signal_display_name)
        .filter(PredictionTracking.target_name == rec.target_display_name)
        .order_by(PredictionTracking.predicted_at.desc())
        .first()
    )
    if not latest:
        return freshness

    freshness.update({
        "available": True,
        "signal_display_name": rec.signal_display_name,
        "target_display_name": rec.target_display_name,
        "predicted_direction": getattr(latest, "predicted_direction", None),
        "predicted_change_pct": getattr(latest, "predicted_change_pct", None),
        "ensemble_confidence": getattr(latest, "ensemble_confidence", None),
        "predicted_at": latest.predicted_at.isoformat() if getattr(latest, "predicted_at", None) else None,
    })
    return freshness


def _summarise_files(parent_build_id: int, db_session) -> List[Dict[str, Any]]:
    """List the parent build's file paths so the AI can preserve contracts."""
    try:
        from models import MVPBuildFile
    except ImportError:
        return []

    files = (
        db_session.query(MVPBuildFile)
        .filter(MVPBuildFile.build_id == parent_build_id)
        .all()
    )
    summary: List[Dict[str, Any]] = []
    for f in files:
        try:
            size = len(f.content.encode("utf-8")) if f.content else 0
        except Exception:
            size = 0
        summary.append({"path": f.file_path, "size_bytes": size})
    return summary


# ---------------------------------------------------------------------------
# Prompt formatter
# ---------------------------------------------------------------------------

def format_intelligence_for_prompt(intelligence: Dict[str, Any]) -> str:
    """Render the intelligence dict as evidence text for the spec AI prompt."""
    if not intelligence:
        return ""

    parent = intelligence.get("parent") or {}
    chain = intelligence.get("chain") or []
    errors = intelligence.get("error_patterns") or {}
    engagement = intelligence.get("engagement") or {}
    revenue = intelligence.get("revenue") or {}
    signal = intelligence.get("signal_freshness") or {}
    files = intelligence.get("prior_files_summary") or []

    lines: List[str] = []
    lines.append("ITERATION INTELLIGENCE — derive the next version's requirements from this evidence.")
    lines.append("")
    lines.append(
        f"This is iteration v{(parent.get('iteration_number') or 1) + 1} "
        f"(parent build #{parent.get('build_id')} — status {parent.get('status')}, "
        f"reason for iteration: {parent.get('iterate_reason') or 'unspecified'})."
    )

    if chain:
        lines.append("")
        lines.append("PRIOR VERSIONS (oldest → newest):")
        for entry in chain:
            lines.append(
                f"  - v{entry.get('iteration_number')}: build #{entry.get('build_id')} "
                f"status={entry.get('status')} errors={entry.get('total_errors')} "
                f"duration={entry.get('duration_seconds')}s"
            )

    if errors:
        lines.append("")
        lines.append("ERROR PATTERNS to avoid (aggregated across chain):")
        for category, count in sorted(errors.items(), key=lambda kv: kv[1], reverse=True):
            if count > 0:
                lines.append(f"  - {category}: {count} occurrence(s)")

    lines.append("")
    lines.append("USER BEHAVIOUR EVIDENCE (live engagement):")
    lines.append(
        f"  - unique_visitors: {engagement.get('unique_visitors', 0)}"
    )
    lines.append(
        f"  - page_views: {engagement.get('page_views', 0)}"
    )
    if engagement.get("avg_session_seconds") is not None:
        lines.append(f"  - avg_session_seconds: {engagement['avg_session_seconds']}")
    lines.append(
        f"  - raw_pageview_events_30d: {engagement.get('raw_pageview_events_30d', 0)}"
    )

    lines.append("")
    lines.append("COMMERCIAL EVIDENCE:")
    lines.append(f"  - MRR: ${revenue.get('mrr_usd', 0):.2f}")
    lines.append(f"  - subscribers: {revenue.get('subscriber_count', 0)}")
    if revenue.get("conversion_rate") is not None:
        lines.append(f"  - conversion_rate: {revenue['conversion_rate']}")
    if revenue.get("churn_rate") is not None:
        lines.append(f"  - churn_rate: {revenue['churn_rate']}")

    if signal.get("available"):
        lines.append("")
        lines.append("CAUSAL SIGNAL FRESHNESS (is the original opportunity still valid?):")
        lines.append(
            f"  - {signal.get('signal_display_name')} → {signal.get('target_display_name')}"
        )
        lines.append(f"  - predicted_direction: {signal.get('predicted_direction')}")
        if signal.get("predicted_change_pct") is not None:
            lines.append(f"  - predicted_change_pct: {signal['predicted_change_pct']}")
        if signal.get("ensemble_confidence") is not None:
            lines.append(f"  - ensemble_confidence: {signal['ensemble_confidence']}")

    if files:
        lines.append("")
        lines.append(f"PRIOR BUILD FILES ({len(files)} total — preserve names/contracts where sensible):")
        for f in files[:30]:
            lines.append(f"  - {f.get('path')} ({f.get('size_bytes', 0)} bytes)")
        if len(files) > 30:
            lines.append(f"  - ... {len(files) - 30} more")

    lines.append("")
    lines.append("ITERATION DIRECTIVE:")
    lines.append(
        "Use the engagement and commercial evidence above to derive what features "
        "to deepen, what to add, and what to drop. If unique_visitors and page_views "
        "are growing but MRR is flat, add or strengthen the conversion path. If MRR "
        "is growing, deepen retention features. If the causal signal is weakening, "
        "consider a pivot. NEVER repeat the listed error patterns. Where prior file "
        "names exist, preserve them unless the change requires renaming."
    )
    return "\n".join(lines)
