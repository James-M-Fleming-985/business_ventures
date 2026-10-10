"""Product concepts: the signal is timing evidence, the product serves the audience of the predicted topic."""

import json
import os
import sys
import tempfile
from types import SimpleNamespace

import pytest

os.environ.setdefault("DATABASE_URL", f"sqlite:///{os.path.join(tempfile.mkdtemp(), 'concepts.db')}")

from services import product_concept_generator as pcg  # noqa: E402

ARGS = dict(
    signal_display="Dog food", target_display="Ice cream", market_category="consumer",
    opportunity_score=71.0, correlation=0.62, p_value=0.01, lag=2,
    estimated_monthly_searches=40000, search_trend_direction="rising", competition_level="medium",
    revenue_potential="medium", predicted_direction="up", predicted_change_pct=12.5,
)

AI_REPLY = [
    {"name": "Scoop Finder", "format": "directory", "pitch": "Find great ice cream.", "target_customer": "Ice cream fans",
     "why_now": "Demand is rising", "free_tier": "Browse", "premium_tier": "Full details", "content_source": "Council open data",
     "revenue_model": "£500 per month enterprise", "defensibility": "Curation", "complexity": "LOW"},
    {"name": "Deal Watch", "format": "not-a-format", "pitch": "Cheapest scoops.", "complexity": "extreme"},
    "junk",
    {"pitch": "no name so dropped"},
    {"name": "Weekly Digest", "format": "digest", "pitch": "One email a week."},
    {"name": "Fourth concept", "pitch": "Cut off at three."},
]


def fake_anthropic(monkeypatch, reply_text, captured):
    client = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: (
        captured.update(kw) or SimpleNamespace(
            content=[SimpleNamespace(type="text", text=reply_text)],
            usage=SimpleNamespace(input_tokens=100, output_tokens=200)))))
    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=lambda api_key: client))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


def test_prompt_treats_the_signal_as_timing_not_the_product(monkeypatch):
    captured = {}
    fake_anthropic(monkeypatch, json.dumps(AI_REPLY), captured)
    pcg.generate_product_concepts(**ARGS)
    prompt = captured["messages"][0]["content"]
    assert "It is NOT the product" in prompt
    assert 'Audience topic (the demand we expect to move): "Ice cream"' in prompt
    assert 'Leading signal (timing evidence only): "Dog food"' in prompt
    assert "Do not propose prices" in prompt and "Never rely on invented facts" in prompt
    assert "Predicted direction: up by 12.5%" in prompt
    assert "core value" not in prompt


def test_ai_output_is_validated_into_a_fixed_shape(monkeypatch):
    fake_anthropic(monkeypatch, json.dumps(AI_REPLY), {})
    concepts = pcg.generate_product_concepts(**ARGS)
    assert [c["name"] for c in concepts] == ["Scoop Finder", "Deal Watch", "Weekly Digest"]
    assert [c["rank"] for c in concepts] == [1, 2, 3]
    assert all(c["source"] == "ai" for c in concepts)
    assert all(c["revenue_model"] == pcg.REVENUE_MODEL for c in concepts)  # the AI never sets the price
    assert concepts[1]["format"] == "hub" and concepts[1]["complexity"] == "LOW"
    for key in ("name", "pitch", "target_customer", "revenue_model", "defensibility", "complexity",
                "format", "why_now", "free_tier", "premium_tier", "content_source"):
        assert all(key in c for c in concepts), key
    assert concepts[2]["content_source"] == pcg.SAMPLE_SOURCE


def test_fenced_json_is_accepted(monkeypatch):
    fake_anthropic(monkeypatch, "```json\n" + json.dumps(AI_REPLY[:1]) + "\n```", {})
    assert pcg.generate_product_concepts(**ARGS)[0]["name"] == "Scoop Finder"


@pytest.mark.parametrize("reply", ["not json", "[]", "{}", '[{"pitch": "x"}]', '["a", "b"]'])
def test_unusable_ai_output_uses_template_concepts(monkeypatch, reply):
    fake_anthropic(monkeypatch, reply, {})
    concepts = pcg.generate_product_concepts(**ARGS)
    assert len(concepts) == 3 and all(c["source"] == "template" for c in concepts)


def test_missing_api_key_uses_template_concepts(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    concepts = pcg.generate_product_concepts(**ARGS)
    assert len(concepts) == 3 and all(c["source"] == "template" for c in concepts)


def test_template_concepts_serve_the_audience_not_the_relationship():
    concepts = pcg.generate_product_concepts.__globals__["_fallback_concepts"]("Dog food", "Ice cream", "consumer")
    assert len(concepts) == 3 and len({c["format"] for c in concepts}) >= 2
    for concept in concepts:
        assert "Ice cream" in concept["name"] and "Dog food" not in concept["name"] + concept["pitch"]
        assert concept["revenue_model"] == pcg.REVENUE_MODEL and concept["content_source"] == pcg.SAMPLE_SOURCE
        text = json.dumps(concept).lower()
        assert not any(word in text for word in ("api", "dashboard", "forecaster", "alert service", "granger"))
        assert concept["complexity"] == "LOW"


def test_normalise_concepts_rejects_non_lists_and_empty_results():
    for bad in (None, {}, "x", 5):
        with pytest.raises(ValueError):
            pcg.normalise_concepts(bad)
    with pytest.raises(ValueError):
        pcg.normalise_concepts([{"name": "no pitch"}])


def test_normalise_concepts_limits_field_lengths():
    long = "x" * 1000
    concept = pcg.normalise_concepts([{"name": long, "pitch": long, "target_customer": long, "free_tier": long}])[0]
    assert len(concept["name"]) == 80 and len(concept["pitch"]) == 220 and len(concept["free_tier"]) == 220


# --- requirement text ----------------------------------------------------------

def full_concept():
    return pcg.normalise_concepts(AI_REPLY)[0]


def test_requirement_demotes_the_signal_to_timing_context():
    text = pcg.build_requirement_text(full_concept(), "Dog food", "Ice cream", "r=0.62")
    assert text.startswith("Build: Scoop Finder (directory)")
    for label in ("Audience:", "Why now:", "FREE:", "PREMIUM:", "CONTENT SOURCE:", "Revenue model:"):
        assert label in text
    before, _, after = text.partition("Timing context only (do NOT build around this)")
    assert "Dog food" not in before and "Dog food predicts Ice cream" in after


def test_requirement_for_an_old_style_concept_has_no_placeholders():
    old = {"name": "Old Tool", "pitch": "Does a thing.", "target_customer": "Analysts", "revenue_model": "£9/mo"}
    text = pcg.build_requirement_text(old, "A", "B")
    assert "None" not in text and "N/A" not in text and "FREE:" not in text
    assert "Old Tool" in text and "Revenue model: £9/mo" in text


def test_requirement_without_a_concept_targets_the_audience():
    text = pcg.build_requirement_text(None, "Dog food", "Ice cream", "because")
    assert text.startswith("Build a subscription website for people interested in Ice cream")
    assert "do NOT build around this" in text and "FREE" not in text.split("Timing")[0].upper().replace("FREE PREVIEW", "")
