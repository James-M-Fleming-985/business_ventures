"""
Commercial Intelligence Service (Track G)

Aggregates commercial performance data from ProductDeployment + ProductMetrics
to derive insights about which MVPs succeeded commercially, what features/configs
drove success, and feeds those insights into future build specifications.

Key capabilities:
  1. Aggregate metrics per deployment (revenue, engagement, churn)
  2. Rank deployments by commercial outcome
  3. Identify winning tech stacks, pricing models, and market categories
  4. Generate plain-English reasoning summaries
  5. Produce configuration confidence scores for the spec generator
  6. Map demographic patterns to successful configurations
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from models import (
    MVPBuild,
    ProductDeployment,
    ProductMetrics,
    RevenueEvent,
    ExploitationRecommendation,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Aggregate metrics per deployment
# ---------------------------------------------------------------------------

def get_deployment_metrics_summary(db: Session, deployment_id: int) -> Dict[str, Any]:
    """Return aggregated metrics for a single deployment."""
    metrics = (
        db.query(ProductMetrics)
        .filter(ProductMetrics.deployment_id == deployment_id)
        .order_by(ProductMetrics.period_start.desc())
        .all()
    )
    if not metrics:
        return {
            "deployment_id": deployment_id,
            "periods": 0,
            "latest_mrr_cents": 0,
            "total_revenue_cents": 0,
            "peak_subscribers": 0,
            "avg_conversion_rate": None,
            "avg_churn_rate": None,
            "total_page_views": 0,
            "total_unique_visitors": 0,
        }

    latest = metrics[0]
    total_revenue = sum(m.mrr_cents or 0 for m in metrics)
    peak_subs = max((m.subscriber_count or 0) for m in metrics)
    conv_rates = [m.conversion_rate for m in metrics if m.conversion_rate is not None]
    churn_rates = [m.churn_rate for m in metrics if m.churn_rate is not None]

    return {
        "deployment_id": deployment_id,
        "periods": len(metrics),
        "latest_mrr_cents": latest.mrr_cents or 0,
        "total_revenue_cents": total_revenue,
        "peak_subscribers": peak_subs,
        "avg_conversion_rate": round(sum(conv_rates) / len(conv_rates), 4) if conv_rates else None,
        "avg_churn_rate": round(sum(churn_rates) / len(churn_rates), 4) if churn_rates else None,
        "total_page_views": sum(m.page_views or 0 for m in metrics),
        "total_unique_visitors": sum(m.unique_visitors or 0 for m in metrics),
    }


# ---------------------------------------------------------------------------
# 2. Rank deployments by commercial success
# ---------------------------------------------------------------------------

def rank_deployments(db: Session, limit: int = 50) -> List[Dict[str, Any]]:
    """Return deployments ranked by composite commercial score.

    Score formula (0-100):
      40% revenue (normalised MRR)
      30% engagement (normalised unique visitors)
      20% conversion rate
      10% retention (inverse churn)
    """
    deployments = (
        db.query(ProductDeployment)
        .filter(ProductDeployment.status == "active")
        .all()
    )

    scored: List[Tuple[float, Dict]] = []
    for dep in deployments:
        summary = get_deployment_metrics_summary(db, dep.id)
        mrr = summary["latest_mrr_cents"]
        visitors = summary["total_unique_visitors"]
        conv = summary["avg_conversion_rate"] or 0
        churn = summary["avg_churn_rate"] or 1.0  # default high churn

        # Normalise each dimension to 0-1 (will re-scale after collecting all)
        scored.append((0, {
            "deployment": dep.to_dict(),
            "metrics": summary,
            "raw": {"mrr": mrr, "visitors": visitors, "conv": conv, "churn": churn},
        }))

    if not scored:
        return []

    # Normalise
    max_mrr = max(s[1]["raw"]["mrr"] for s in scored) or 1
    max_vis = max(s[1]["raw"]["visitors"] for s in scored) or 1

    results = []
    for _, item in scored:
        r = item["raw"]
        norm_mrr = r["mrr"] / max_mrr
        norm_vis = r["visitors"] / max_vis
        norm_conv = min(r["conv"], 1.0)
        norm_retain = max(0, 1.0 - r["churn"])

        score = round(
            40 * norm_mrr + 30 * norm_vis + 20 * norm_conv + 10 * norm_retain, 2
        )
        item["commercial_score"] = score
        del item["raw"]
        results.append(item)

    results.sort(key=lambda x: x["commercial_score"], reverse=True)
    return results[:limit]


# ---------------------------------------------------------------------------
# 3. Identify winning configurations
# ---------------------------------------------------------------------------

def get_winning_configurations(db: Session, min_deployments: int = 1) -> Dict[str, Any]:
    """Analyse which tech stacks, pricing models, and market categories
    correlate with the highest commercial scores."""

    ranked = rank_deployments(db, limit=200)
    if not ranked:
        return {"tech_stacks": [], "pricing_models": [], "market_categories": [], "demographics": []}

    # Buckets
    def _bucket(key_fn):
        buckets = defaultdict(list)
        for item in ranked:
            dep = item["deployment"]
            key = key_fn(dep)
            if key:
                buckets[key].append(item["commercial_score"])
        result = []
        for k, scores in buckets.items():
            if len(scores) >= min_deployments:
                result.append({
                    "value": k,
                    "count": len(scores),
                    "avg_score": round(sum(scores) / len(scores), 2),
                    "max_score": max(scores),
                })
        result.sort(key=lambda x: x["avg_score"], reverse=True)
        return result

    # Tech stack: use framework as primary key
    def _tech_key(dep):
        ts = dep.get("tech_stack")
        if isinstance(ts, dict):
            return ts.get("framework", "unknown")
        return None

    return {
        "tech_stacks": _bucket(_tech_key),
        "pricing_models": _bucket(lambda d: d.get("pricing_model")),
        "market_categories": _bucket(lambda d: d.get("market_category")),
        "demographics": _bucket(lambda d: d.get("target_demographic")),
    }


# ---------------------------------------------------------------------------
# 4. Plain-English reasoning summary
# ---------------------------------------------------------------------------

def generate_commercial_reasoning(db: Session) -> str:
    """Generate a plain-English summary of commercial intelligence findings."""
    winning = get_winning_configurations(db)
    ranked = rank_deployments(db, limit=5)

    lines = ["## Commercial Intelligence Summary\n"]

    if not ranked:
        return "No deployed products with metrics data yet. Deploy MVPs and collect engagement/revenue data to enable commercial intelligence."

    # Top performers
    lines.append(f"**Top {len(ranked)} performing deployments** (by composite score):\n")
    for i, item in enumerate(ranked, 1):
        dep = item["deployment"]
        m = item["metrics"]
        mrr_dollars = (m["latest_mrr_cents"] or 0) / 100
        lines.append(
            f"{i}. **{dep['product_name']}** — score {item['commercial_score']}, "
            f"MRR ${mrr_dollars:.2f}, {m['peak_subscribers']} peak subs, "
            f"{m['total_unique_visitors']} visitors"
        )

    # Winning patterns
    for dimension, label in [
        ("tech_stacks", "Tech Stack"),
        ("pricing_models", "Pricing Model"),
        ("market_categories", "Market Category"),
        ("demographics", "Target Demographic"),
    ]:
        items = winning.get(dimension, [])
        if items:
            best = items[0]
            lines.append(
                f"\n**Best {label}:** {best['value']} "
                f"(avg score {best['avg_score']}, {best['count']} deployments)"
            )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 5. Configuration confidence scoring
# ---------------------------------------------------------------------------

def get_configuration_confidence(
    db: Session,
    tech_stack: Optional[str] = None,
    pricing_model: Optional[str] = None,
    market_category: Optional[str] = None,
    target_demographic: Optional[str] = None,
) -> Dict[str, Any]:
    """Score confidence (0-100) for a proposed configuration based on
    historical deployment performance.

    Returns:
        {
          "overall_confidence": 72,
          "breakdown": {
            "tech_stack": {"value": "fastapi", "confidence": 85, "evidence_count": 4},
            "pricing_model": {...},
            "market_category": {...},
            "demographic": {...},
          },
          "recommendation": "High confidence - this config mirrors successful past deployments"
        }
    """
    winning = get_winning_configurations(db)
    breakdown = {}

    def _score_dimension(config_value, dimension_key):
        if not config_value:
            return {"value": None, "confidence": 50, "evidence_count": 0, "reason": "Not specified"}
        items = winning.get(dimension_key, [])
        for item in items:
            if item["value"] and item["value"].lower() == config_value.lower():
                # Scale avg_score (0-100) to confidence, boosted by evidence count
                base = min(item["avg_score"], 100)
                evidence_boost = min(item["count"] * 5, 20)
                confidence = min(round(base + evidence_boost), 100)
                return {
                    "value": config_value,
                    "confidence": confidence,
                    "evidence_count": item["count"],
                    "reason": f"Seen in {item['count']} deployment(s), avg score {item['avg_score']}",
                }
        return {
            "value": config_value,
            "confidence": 30,
            "evidence_count": 0,
            "reason": "No prior deployments with this configuration",
        }

    breakdown["tech_stack"] = _score_dimension(tech_stack, "tech_stacks")
    breakdown["pricing_model"] = _score_dimension(pricing_model, "pricing_models")
    breakdown["market_category"] = _score_dimension(market_category, "market_categories")
    breakdown["demographic"] = _score_dimension(target_demographic, "demographics")

    confidences = [v["confidence"] for v in breakdown.values()]
    overall = round(sum(confidences) / len(confidences)) if confidences else 50

    # Recommendation text
    if overall >= 75:
        rec = "High confidence — this configuration mirrors successful past deployments."
    elif overall >= 50:
        rec = "Moderate confidence — some patterns match prior successes, but limited evidence."
    else:
        rec = "Low confidence — this is a novel configuration with little historical precedent."

    return {
        "overall_confidence": overall,
        "breakdown": breakdown,
        "recommendation": rec,
    }


# ---------------------------------------------------------------------------
# 6. Demographic pattern mapping
# ---------------------------------------------------------------------------

def get_demographic_patterns(db: Session) -> List[Dict[str, Any]]:
    """Map target demographics to their most successful configurations.

    Returns a list of demographic segments with their winning tech stacks,
    pricing models, and average commercial scores.
    """
    ranked = rank_deployments(db, limit=200)
    if not ranked:
        return []

    demo_map = defaultdict(list)
    for item in ranked:
        dep = item["deployment"]
        demo = dep.get("target_demographic")
        if demo:
            demo_map[demo].append(item)

    patterns = []
    for demo, items in demo_map.items():
        scores = [i["commercial_score"] for i in items]

        # Find most common tech stack
        tech_counts = defaultdict(int)
        pricing_counts = defaultdict(int)
        market_counts = defaultdict(int)
        for i in items:
            dep = i["deployment"]
            ts = dep.get("tech_stack")
            if isinstance(ts, dict) and ts.get("framework"):
                tech_counts[ts["framework"]] += 1
            if dep.get("pricing_model"):
                pricing_counts[dep["pricing_model"]] += 1
            if dep.get("market_category"):
                market_counts[dep["market_category"]] += 1

        def _top(counts):
            if not counts:
                return None
            return max(counts, key=counts.get)

        patterns.append({
            "demographic": demo,
            "deployment_count": len(items),
            "avg_score": round(sum(scores) / len(scores), 2),
            "top_tech_stack": _top(tech_counts),
            "top_pricing_model": _top(pricing_counts),
            "top_market_category": _top(market_counts),
        })

    patterns.sort(key=lambda x: x["avg_score"], reverse=True)
    return patterns


# ---------------------------------------------------------------------------
# 7. Spec generator consultation context
# ---------------------------------------------------------------------------

def get_commercial_context_for_spec(
    db: Session,
    market_category: Optional[str] = None,
    target_demographic: Optional[str] = None,
) -> str:
    """Generate a commercial intelligence context block to inject into
    the spec generator AI prompt.

    Returns a text block summarising:
      - Top performing deployments and why
      - Recommended tech stacks and pricing for this market/demographic
      - Configuration confidence assessment
    """
    ranked = rank_deployments(db, limit=5)
    winning = get_winning_configurations(db)

    parts = []
    parts.append("COMMERCIAL INTELLIGENCE CONTEXT (from historical deployment data):")

    if not ranked:
        parts.append("No commercial performance data available yet. Use default best-practice configuration.")
        return "\n".join(parts)

    # Top performers
    parts.append(f"\nTop {len(ranked)} commercially successful deployments:")
    for i, item in enumerate(ranked, 1):
        dep = item["deployment"]
        m = item["metrics"]
        mrr_dollars = (m.get("latest_mrr_cents") or 0) / 100
        parts.append(
            f"  {i}. {dep['product_name']} (score: {item['commercial_score']}) — "
            f"tech: {dep.get('tech_stack', {}).get('framework', '?')}, "
            f"pricing: {dep.get('pricing_model', '?')}, "
            f"MRR: ${mrr_dollars:.2f}, visitors: {m.get('total_unique_visitors', 0)}"
        )

    # Best configurations
    for dim, label in [
        ("tech_stacks", "tech stack"),
        ("pricing_models", "pricing model"),
    ]:
        items = winning.get(dim, [])
        if items:
            top = items[:3]
            values = ", ".join(f"{t['value']} (score {t['avg_score']})" for t in top)
            parts.append(f"\nBest {label}s: {values}")

    # Market-specific advice
    if market_category:
        cats = winning.get("market_categories", [])
        match = next((c for c in cats if c["value"] and c["value"].lower() == market_category.lower()), None)
        if match:
            parts.append(f"\nMarket '{market_category}': avg score {match['avg_score']} across {match['count']} prior deployments.")
        else:
            parts.append(f"\nMarket '{market_category}': no prior deployments — novel category.")

    if target_demographic:
        demos = winning.get("demographics", [])
        match = next((d for d in demos if d["value"] and d["value"].lower() == target_demographic.lower()), None)
        if match:
            parts.append(f"\nDemographic '{target_demographic}': avg score {match['avg_score']} across {match['count']} prior deployments.")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 8. Stripe → ProductMetrics aggregation
# ---------------------------------------------------------------------------

def aggregate_revenue_to_metrics(db: Session, app_id: str, period_days: int = 30) -> Optional[int]:
    """Aggregate RevenueEvent rows into a ProductMetrics row for a deployment.

    Looks up the ProductDeployment by app_id, then sums RevenueEvents for the
    period and upserts a ProductMetrics row.

    Returns the ProductMetrics.id or None if no deployment found.
    """
    deployment = (
        db.query(ProductDeployment)
        .filter(ProductDeployment.app_id == app_id)
        .first()
    )
    if not deployment:
        logger.warning("No ProductDeployment found for app_id=%s", app_id)
        return None

    now = datetime.utcnow()
    period_start = now - timedelta(days=period_days)

    # Sum revenue events for the period
    events = (
        db.query(RevenueEvent)
        .filter(
            RevenueEvent.app_id == app_id,
            RevenueEvent.event_at >= period_start,
            RevenueEvent.event_at <= now,
        )
        .all()
    )

    total_revenue_cents = sum(e.amount_cents or 0 for e in events if e.event_type == "payment_succeeded")
    active_subs = sum(
        1 for e in events
        if e.event_type in ("subscription_created", "subscription_updated")
    )
    cancelled = sum(1 for e in events if e.event_type == "subscription_cancelled")
    net_subs = max(0, active_subs - cancelled)

    # Upsert: check for existing row in this period
    existing = (
        db.query(ProductMetrics)
        .filter(
            ProductMetrics.deployment_id == deployment.id,
            ProductMetrics.period_start == period_start,
        )
        .first()
    )

    if existing:
        existing.mrr_cents = total_revenue_cents
        existing.subscriber_count = net_subs
        existing.source = "stripe"
        pm = existing
    else:
        pm = ProductMetrics(
            deployment_id=deployment.id,
            period_start=period_start,
            period_end=now,
            mrr_cents=total_revenue_cents,
            subscriber_count=net_subs,
            source="stripe",
        )
        db.add(pm)

    db.commit()
    db.refresh(pm)
    logger.info(
        "Aggregated revenue for deployment %d (app_id=%s): MRR=%d cents, subs=%d",
        deployment.id, app_id, total_revenue_cents, net_subs,
    )
    return pm.id


def aggregate_all_deployments(db: Session) -> Dict[str, int]:
    """Run revenue aggregation for all active deployments. Returns counts."""
    deployments = (
        db.query(ProductDeployment)
        .filter(ProductDeployment.status == "active")
        .all()
    )
    success = 0
    skipped = 0
    for dep in deployments:
        result = aggregate_revenue_to_metrics(db, dep.app_id)
        if result:
            success += 1
        else:
            skipped += 1
    return {"aggregated": success, "skipped": skipped, "total": len(deployments)}
