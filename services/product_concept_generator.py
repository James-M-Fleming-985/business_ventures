"""Generate specific, commercially defensible product concepts using AI.

Replaces the hardcoded build_suggestions dictionary with LLM-generated
product concepts tailored to each specific exploitation opportunity.
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def _stamp(concepts: List[Dict], source: str) -> List[Dict]:
    """Tag each concept with its origin (ai|template) and a generation timestamp."""
    ts = datetime.now(timezone.utc).isoformat()
    for c in concepts:
        c["source"] = source
        c["generated_at"] = ts
    return concepts


FORMATS = ("directory", "comparison", "calendar", "guide", "digest", "hub")
COMPLEXITIES = ("LOW", "MEDIUM", "HIGH")
# Pricing is decided by the platform (see templates/mvp/runtime/mvp_runtime.py),
# never by the AI, so every concept carries the same revenue model.
REVENUE_MODEL = "Monthly subscription from £0.99, adjusted to local purchasing power and currency"
SAMPLE_SOURCE = "Placeholder sample data until a real source is connected"


def _clip(value, limit: int) -> str:
    if not isinstance(value, (str, int, float)) or isinstance(value, bool):
        return ""
    return " ".join(str(value).encode("utf-8", "ignore").decode("utf-8").split())[:limit]


def normalise_concepts(raw) -> List[Dict]:
    """Validate AI output into at most 3 concepts with a fixed shape.

    The original keys (name, pitch, target_customer, revenue_model, defensibility,
    complexity) are always present so the dashboard keeps working.
    """
    if not isinstance(raw, list):
        raise ValueError("Expected a JSON array")
    concepts: List[Dict] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        name, pitch = _clip(entry.get("name"), 80), _clip(entry.get("pitch"), 220)
        if not name or not pitch:
            continue
        fmt = _clip(entry.get("format"), 20).lower()
        complexity = _clip(entry.get("complexity"), 10).upper()
        concepts.append({
            "name": name,
            "format": fmt if fmt in FORMATS else "hub",
            "pitch": pitch,
            "target_customer": _clip(entry.get("target_customer"), 220) or "People interested in this topic",
            "why_now": _clip(entry.get("why_now"), 200),
            "free_tier": _clip(entry.get("free_tier"), 220),
            "premium_tier": _clip(entry.get("premium_tier"), 220),
            "content_source": _clip(entry.get("content_source"), 220) or SAMPLE_SOURCE,
            "revenue_model": REVENUE_MODEL,
            "defensibility": _clip(entry.get("defensibility"), 220),
            "complexity": complexity if complexity in COMPLEXITIES else "LOW",
        })
        if len(concepts) == 3:
            break
    if not concepts:
        raise ValueError("No usable concepts in AI response")
    for rank, concept in enumerate(concepts, start=1):
        concept["rank"] = rank
    return concepts


def build_requirement_text(
    concept: Optional[Dict],
    signal_display: str,
    target_display: str,
    reasoning: str = "",
) -> str:
    """The build requirement. The signal is timing context, never the subject of the product."""
    timing = (
        f"Timing context only (do NOT build around this): {signal_display} predicts "
        f"{target_display}. {reasoning or ''}"
    ).strip()
    if not concept:
        return (
            f"Build a subscription website for people interested in {target_display}. "
            f"Offer a free preview and premium content. {timing}"
        )
    parts = [f"Build: {concept['name']} ({concept.get('format', 'hub')}) — {concept['pitch']}"]
    for label, key in (
        ("Audience", "target_customer"),
        ("Why now", "why_now"),
        ("FREE", "free_tier"),
        ("PREMIUM", "premium_tier"),
        ("CONTENT SOURCE", "content_source"),
        ("Revenue model", "revenue_model"),
    ):
        if concept.get(key):
            parts.append(f"{label}: {concept[key]}.")
    parts.append(timing)
    return " ".join(parts)


def generate_product_concepts(
    signal_display: str,
    target_display: str,
    market_category: str,
    opportunity_score: float,
    correlation: float,
    p_value: float,
    lag: int,
    estimated_monthly_searches: int,
    search_trend_direction: str,
    competition_level: str,
    revenue_potential: str,
    predicted_direction: str = None,
    predicted_change_pct: float = None,
    ensemble_confidence: str = None,
    db_session=None,
) -> List[Dict]:
    """Generate 3 ranked product concepts for a BUILD exploitation opportunity.

    Each concept includes: name, pitch, target_customer, revenue_model,
    defensibility, and estimated build complexity.

    Falls back to template-based suggestions if AI is unavailable.
    """
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        logger.warning("ANTHROPIC_API_KEY not set — using template fallback for product concepts")
        return _stamp(_fallback_concepts(signal_display, target_display, market_category), "template")

    # Gather outcome history for this market category if available
    outcome_context = ""
    if db_session:
        outcome_context = _get_outcome_context(db_session, market_category)

    direction = (
        f"- Predicted direction: {predicted_direction} by {abs(predicted_change_pct or 0):.1f}%"
        " (if \"down\", build for people looking for alternatives, savings or substitutes)\n"
        if predicted_direction
        else ""
    )
    confidence = f"- AI ensemble confidence: {ensemble_confidence}\n" if ensemble_confidence else ""
    prompt = f"""You are the product strategist for an autonomous system that SENSES emerging signals, \
PREDICTS which demand will grow or shrink because of them, and builds subscription products that \
EXPLOIT that predicted demand.

HOW TO USE THE SIGNAL (important):
The statistical relationship tells us WHEN and WHERE demand is moving. It is the reason to build now.
It is NOT the product. Do not build a tracker, dashboard, forecaster or analytics tool of the
relationship, and do not make the leading signal the subject of the product. Build something for the
PEOPLE who are becoming interested in the predicted-demand topic.

PREDICTED DEMAND:
- Audience topic (the demand we expect to move): "{target_display}"
- Leading signal (timing evidence only): "{signal_display}"
- Evidence: {signal_display} Granger-causes {target_display} (p={p_value:.4f}, r={correlation:.3f}, lag={lag} months)
- Market category: {market_category.replace('_', ' ')}
- Monthly search demand: ~{estimated_monthly_searches:,}; demand trend: {search_trend_direction}
- Competition: {competition_level}; revenue potential: {revenue_potential}
- Opportunity score: {opportunity_score:.0f}/100
{direction}{confidence}{outcome_context}

TASK: propose 3 subscription products for the audience of "{target_display}".

RULES:
1. Each product is a SPECIFIC site people would subscribe to for information or content, for example a
   curated directory or guide, a price or deal comparison, a release or event calendar, a buyer's guide,
   a curated digest, or a resources hub. Not a generic "analytics dashboard".
2. Use at least 2 different formats across the 3 concepts.
3. State what is FREE (enough to attract and convince visitors) and what is PREMIUM (what a subscriber
   pays for). Premium must be concrete details, not just "more".
4. State the content source: where the real content would come from (public datasets, APIs, official
   sites, curation). Never rely on invented facts, prices, addresses or contacts.
5. Include a one-line "why now" that uses the prediction as the timing hook.
6. It must be buildable as a LOW-complexity MVP.
7. Do not propose prices. Pricing is fixed by the platform.
8. Rank by likelihood of turning visitors into paying subscribers; concept 1 is the strongest.

Return ONLY a JSON array of exactly 3 objects with these fields:
- "name": short product name (3-6 words)
- "format": one of directory, comparison, calendar, guide, digest, hub
- "pitch": one-sentence value to the subscriber
- "target_customer": the audience (who they are and what they want)
- "why_now": one line tying the prediction to timing
- "free_tier": what visitors see for free
- "premium_tier": what subscribers get
- "content_source": where the real content comes from
- "defensibility": why it is hard to copy
- "complexity": "LOW", "MEDIUM" or "HIGH"

Output ONLY valid JSON, no markdown fences or explanation."""

    try:
        import anthropic
        from services.ai_provider import DEFAULT_ANTHROPIC_MODEL, response_text
        client = anthropic.Anthropic(api_key=anthropic_key)
        resp = client.messages.create(
            model=DEFAULT_ANTHROPIC_MODEL,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
            timeout=60.0,
        )
        text = response_text(resp).strip()
        cost = (resp.usage.input_tokens * 0.003 + resp.usage.output_tokens * 0.015) / 1000

        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3].rstrip()
        if text.startswith("json"):
            text = text[4:].lstrip()

        concepts = normalise_concepts(json.loads(text))

        logger.info(
            f"Generated {len(concepts)} product concepts for "
            f"{signal_display}→{target_display} (${cost:.4f})"
        )
        return _stamp(concepts, "ai")

    except Exception as exc:
        logger.error(f"AI product concept generation failed: {exc}")
        return _stamp(_fallback_concepts(signal_display, target_display, market_category), "template")


def _get_outcome_context(db_session, market_category: str) -> str:
    """Query past deployment outcomes to inform concept generation."""
    try:
        from models import ProductDeployment, ProductMetrics
        deployments = (
            db_session.query(ProductDeployment)
            .filter(ProductDeployment.status == "active")
            .order_by(ProductDeployment.deployed_at.desc())
            .limit(10)
            .all()
        )
        if not deployments:
            return ""

        lines = ["\nHISTORICAL DEPLOYMENT OUTCOMES (learn from these):"]
        for d in deployments:
            metrics = (
                db_session.query(ProductMetrics)
                .filter(ProductMetrics.app_id == d.app_id)
                .order_by(ProductMetrics.recorded_at.desc())
                .first()
            )
            engagement = metrics.monthly_active_users if metrics else 0
            mrr = metrics.mrr if metrics else 0
            lines.append(
                f"- {d.product_name}: engagement={engagement}, MRR=£{mrr:.0f}, "
                f"tech={d.tech_stack}"
            )

        # Category-specific guidance
        same_cat = [
            d for d in deployments
            if d.tech_stack and d.tech_stack.get("market_category") == market_category
        ]
        if same_cat:
            lines.append(f"\nNote: {len(same_cat)} past build(s) in {market_category} — consider what worked/failed.")

        return "\n".join(lines)
    except Exception as exc:
        logger.debug(f"Outcome context lookup failed: {exc}")
        return ""


def _fallback_concepts(
    signal_display: str, target_display: str, market_category: str
) -> List[Dict]:
    """Template concepts when the AI is unavailable: sites for the audience of the predicted topic."""
    topic = target_display
    return normalise_concepts([
        {
            "name": f"{topic} Guide",
            "format": "guide",
            "pitch": f"A curated guide to {topic}, so enthusiasts find the best of it faster.",
            "target_customer": f"People who are getting more interested in {topic}",
            "why_now": f"Interest in {topic} is predicted to move soon",
            "free_tier": "Browse the guide and read short summaries of the top entries",
            "premium_tier": "Full details, insider tips and contact information for every entry",
            "content_source": SAMPLE_SOURCE,
            "defensibility": "Curation quality and a growing archive",
            "complexity": "LOW",
        },
        {
            "name": f"{topic} Deal Watch",
            "format": "comparison",
            "pitch": f"Compare options and spot good value in {topic}.",
            "target_customer": f"Value-conscious buyers of {topic}",
            "why_now": f"Demand for {topic} is expected to change, which moves prices",
            "free_tier": "A weekly shortlist of the best-value picks",
            "premium_tier": "The full comparison table and price-drop alerts",
            "content_source": SAMPLE_SOURCE,
            "defensibility": "A price history nobody else keeps",
            "complexity": "LOW",
        },
        {
            "name": f"{topic} Weekly Digest",
            "format": "digest",
            "pitch": f"One short weekly email on what is new in {topic}.",
            "target_customer": f"Busy fans of {topic} who want the highlights",
            "why_now": f"The audience for {topic} is growing right now",
            "free_tier": "The headline items each week",
            "premium_tier": "The complete digest with the full archive",
            "content_source": SAMPLE_SOURCE,
            "defensibility": "Consistent curation and a loyal readership",
            "complexity": "LOW",
        },
    ])
