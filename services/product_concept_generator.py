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

    prompt = f"""You are a product strategist for an autonomous business-building system. Given a statistically validated market signal, generate 3 specific, commercially defensible product concepts.

MARKET SIGNAL:
- Signal: "{signal_display}" (Wikipedia search interest)
- Target: "{target_display}" (correlated activity)
- Relationship: {signal_display} Granger-causes {target_display} (p={p_value:.4f}, r={correlation:.3f}, lag={lag} months)
- Market category: {market_category.replace('_', ' ')}
- Monthly search demand: ~{estimated_monthly_searches:,}
- Demand trend: {search_trend_direction}
- Competition: {competition_level}
- Revenue potential: {revenue_potential}
- Opportunity score: {opportunity_score:.0f}/100
{f'- Predicted direction: {predicted_direction} by {abs(predicted_change_pct or 0):.1f}%' if predicted_direction else ''}
{f'- AI ensemble confidence: {ensemble_confidence}' if ensemble_confidence else ''}
{outcome_context}

REQUIREMENTS:
1. Each concept must be a SPECIFIC product (not generic like "analytics dashboard")
2. Each must have a clear target customer who would PAY for it
3. Each must have defensibility (proprietary data enrichment, workflow integration, or unique insight)
4. Rank by commercial viability — concept 1 should be the strongest
5. Consider the statistical relationship — use the lag/prediction as the product's core value

Return ONLY a JSON array with exactly 3 objects, each with these fields:
- "name": short product name (3-6 words)
- "pitch": one-sentence value proposition (what it does for the customer)
- "target_customer": who pays (be specific: role, company type, pain point)
- "revenue_model": how it makes money (subscription, usage-based, freemium, etc.)
- "defensibility": why competitors can't easily replicate this
- "complexity": "LOW", "MEDIUM", or "HIGH"

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

        concepts = json.loads(text)
        if not isinstance(concepts, list) or len(concepts) == 0:
            raise ValueError("Expected a non-empty JSON array")

        # Ensure exactly 3 concepts
        concepts = concepts[:3]
        for i, c in enumerate(concepts):
            c["rank"] = i + 1
            c.setdefault("complexity", "MEDIUM")

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
    """Template-based fallback when AI is unavailable."""
    category_templates = {
        "health_tech": [
            {
                "name": f"{signal_display} Clinical Alert Service",
                "pitch": f"Real-time alerts when {signal_display} search interest predicts changes in {target_display} activity",
                "target_customer": "Healthcare market researchers and pharma business development teams",
                "revenue_model": "Monthly subscription ($49-199/mo based on alert frequency)",
                "defensibility": "Proprietary Granger-causal signal processing with predictive lead time",
                "complexity": "MEDIUM",
            },
            {
                "name": f"{target_display} Trend Forecaster",
                "pitch": f"Forecast {target_display} trends using leading indicators from public search behaviour",
                "target_customer": "Clinical trial recruitment firms needing demand forecasting",
                "revenue_model": "Usage-based API pricing ($0.01/query)",
                "defensibility": "Multi-source ensemble model with continuously validated predictions",
                "complexity": "LOW",
            },
            {
                "name": f"{market_category.replace('_', ' ').title()} Intelligence Dashboard",
                "pitch": f"Monitor {signal_display} signals and their downstream impact on {target_display}",
                "target_customer": "Health tech investors evaluating market timing",
                "revenue_model": "Freemium with premium tier ($99/mo)",
                "defensibility": "Curated signal→outcome mappings with accuracy tracking",
                "complexity": "HIGH",
            },
        ],
        "fintech": [
            {
                "name": f"{signal_display} Market Signal API",
                "pitch": f"Trade signals based on {signal_display} interest predicting {target_display} movements",
                "target_customer": "Quantitative traders and algorithmic trading firms",
                "revenue_model": "Monthly subscription with tiered data access ($99-499/mo)",
                "defensibility": "Validated causal relationships with documented prediction accuracy",
                "complexity": "MEDIUM",
            },
            {
                "name": f"{target_display} Sentiment Tracker",
                "pitch": f"Track public sentiment shifts that lead {target_display} by {2} months",
                "target_customer": "Retail investors and financial advisors",
                "revenue_model": "Freemium with premium alerts ($19/mo)",
                "defensibility": "Real-time sentiment scoring from multiple public data sources",
                "complexity": "LOW",
            },
            {
                "name": f"Alternative Data for {target_display}",
                "pitch": f"Alternative data feed combining {signal_display} trends with {target_display} predictions",
                "target_customer": "Hedge funds and asset managers",
                "revenue_model": "Enterprise licensing ($2,000/mo)",
                "defensibility": "Ensemble model with walk-forward validation and documented Sharpe ratio",
                "complexity": "HIGH",
            },
        ],
    }

    # Generic fallback
    default = [
        {
            "name": f"{signal_display} Prediction API",
            "pitch": f"API service predicting {target_display} changes based on {signal_display} trends",
            "target_customer": f"Analysts and researchers in the {market_category.replace('_', ' ')} space",
            "revenue_model": "Usage-based API pricing with free tier",
            "defensibility": "Statistically validated causal model with continuous accuracy tracking",
            "complexity": "LOW",
        },
        {
            "name": f"{signal_display} Alert Service",
            "pitch": f"Automated alerts when {signal_display} signals predict significant {target_display} movements",
            "target_customer": f"Decision-makers in {market_category.replace('_', ' ')} needing early warning",
            "revenue_model": "Monthly subscription ($29-99/mo)",
            "defensibility": "Proprietary signal processing with documented lead time advantage",
            "complexity": "MEDIUM",
        },
        {
            "name": f"{market_category.replace('_', ' ').title()} Intelligence Platform",
            "pitch": f"Full analytics platform connecting {signal_display} trends to {target_display} outcomes",
            "target_customer": f"Strategy teams and consultants in {market_category.replace('_', ' ')}",
            "revenue_model": "Freemium with enterprise tier",
            "defensibility": "Multi-signal ensemble model with feedback loop improving over time",
            "complexity": "HIGH",
        },
    ]

    concepts = category_templates.get(market_category, default)
    for i, c in enumerate(concepts):
        c["rank"] = i + 1
    return concepts
