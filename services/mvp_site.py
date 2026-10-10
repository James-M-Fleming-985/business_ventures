"""Site content for generated MVPs, and the rendering of their main.py.

The AI supplies *content* (copy, categories, sample items) as JSON. That JSON is
validated and sanitised here, then rendered into a fixed, tested template
(templates/mvp/runtime/site_main.py.tpl) that uses the shared mvp_runtime
module. No AI-written code is executed for the site, so the paywall and Stripe
logic cannot be broken or leaked by a bad generation.
"""

import ast
import json
import logging
import pprint
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

RUNTIME_DIR = Path(__file__).resolve().parent.parent / "templates" / "mvp" / "runtime"

FORMATS = ("directory", "comparison", "calendar", "guide", "digest", "hub")
RESERVED_KEYS = {"id", "title", "category", "summary", "tier", "locked", "locked_fields", "is_sample"}
MAX_ITEMS = 12
MIN_ITEMS = 3
PLACEHOLDER_PREMIUM = "Premium details appear here once real data is connected."
DEFAULT_PREMIUM_FIELDS = [
    {"key": "details", "label": "Full details"},
    {"key": "insider_tip", "label": "Insider tip"},
    {"key": "contact", "label": "Contact information"},
]

_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{0,24}$")
_GA4_RE = re.compile(r"^G-[A-Z0-9]{4,20}$")


def runtime_source() -> str:
    return (RUNTIME_DIR / "mvp_runtime.py").read_text(encoding="utf-8")


def _text(value: Any, limit: int) -> str:
    if not isinstance(value, (str, int, float)) or isinstance(value, bool):
        return ""
    cleaned = re.sub(r"[\x00-\x1f\x7f]+", " ", str(value).encode("utf-8", "ignore").decode("utf-8"))
    return re.sub(r"\s+", " ", cleaned).strip()[:limit]


def _slug(value: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", value.lower())).strip("-")[:40]


def _looks_real(value: str) -> bool:
    """Sample content must not carry URLs, e-mail addresses or phone numbers."""
    return bool(
        "://" in value
        or "www." in value.lower()
        or "@" in value
        or re.search(r"\+?\d[\d\s().-]{7,}\d", value)
    )


def _string_list(value: Any, fallback: List[str], limit: int = 6, width: int = 100) -> List[str]:
    if not isinstance(value, list):
        return list(fallback)
    cleaned = [_text(v, width) for v in value[:limit]]
    cleaned = [c for c in cleaned if c]
    return cleaned or list(fallback)


def tracking_config(ga4_id: str = "") -> Dict[str, str]:
    """Google Analytics id for every page. The engagement beacon is injected into each
    MVP page by the middleware the orchestrator appends to main.py, not by the site."""
    return {"ga4_measurement_id": ga4_id if _GA4_RE.match(ga4_id or "") else ""}


def _concept(spec: Optional[dict]) -> Dict[str, Any]:
    meta = (spec or {}).get("_meta") or {}
    return meta.get("selected_concept") or {}


def default_site(spec: Optional[dict], build_id: Optional[int] = None, ga4_id: str = "") -> Dict[str, Any]:
    """A complete, safe site built only from what we already know. Used when the AI is unavailable."""
    spec = spec or {}
    meta = spec.get("_meta") or {}
    concept = _concept(spec)
    topic = _text(meta.get("target_display_name"), 40) or "this topic"
    name = _text(concept.get("name"), 60) or _text(spec.get("feature_name"), 60) or f"{topic} Hub"
    categories = ["Guides", "Deals", "New releases", "Local picks"]
    items = []
    for n in range(1, 9):
        items.append(
            {
                "id": f"sample-{n}",
                "title": f"{topic} sample {n}",
                "category": categories[(n - 1) % len(categories)],
                "summary": f"Placeholder summary for sample {n}. Real {topic} content will appear here.",
                "tier": "premium" if n > 6 else "free",
                "details": PLACEHOLDER_PREMIUM,
                "insider_tip": PLACEHOLDER_PREMIUM,
                "contact": PLACEHOLDER_PREMIUM,
            }
        )
    site = {
        "name": name,
        "tagline": _text(concept.get("pitch"), 160) or f"Everything worth knowing about {topic}, in one place.",
        "why_now": _text(concept.get("why_now"), 90) or f"Interest in {topic} is rising",
        "free_features": _string_list(
            [concept.get("free_tier")] if concept.get("free_tier") else None,
            ["Free preview of the latest entries", "Browse by category", "Search"],
        ),
        "premium_features": _string_list(
            [concept.get("premium_tier")] if concept.get("premium_tier") else None,
            ["Every entry in full", "Insider tips and contact details", "New entries as they appear"],
        ),
        "premium_fields": [f["key"] for f in DEFAULT_PREMIUM_FIELDS],
        "field_labels": {f["key"]: f["label"] for f in DEFAULT_PREMIUM_FIELDS},
        "items": items,
        "sample_data": True,
    }
    site.update(tracking_config(ga4_id))
    return site


def normalise_site(raw: Any, fallback: Dict[str, Any]) -> Dict[str, Any]:
    """Turn untrusted AI output into a safe site, filling gaps from the fallback."""
    if not isinstance(raw, dict):
        return fallback
    site = dict(fallback)
    site["name"] = _text(raw.get("name"), 60) or fallback["name"]
    site["tagline"] = _text(raw.get("tagline"), 160) or fallback["tagline"]
    site["why_now"] = _text(raw.get("why_now"), 90) or fallback["why_now"]
    site["free_features"] = _string_list(raw.get("free_features"), fallback["free_features"])
    site["premium_features"] = _string_list(raw.get("premium_features"), fallback["premium_features"])

    fields = []
    for entry in raw.get("premium_fields") or []:
        if isinstance(entry, dict):
            key = _text(entry.get("key"), 25)
            label = _text(entry.get("label"), 40)
            if _KEY_RE.match(key) and key not in RESERVED_KEYS and label and key not in [f["key"] for f in fields]:
                fields.append({"key": key, "label": label})
    fields = fields[:4] or DEFAULT_PREMIUM_FIELDS
    keys = [f["key"] for f in fields]
    site["premium_fields"] = keys
    site["field_labels"] = {f["key"]: f["label"] for f in fields}

    items: List[Dict[str, Any]] = []
    seen = set()
    for entry in (raw.get("items") or [])[:MAX_ITEMS]:
        if not isinstance(entry, dict):
            continue
        title = _text(entry.get("title"), 80)
        if not title or _looks_real(title):
            continue
        item_id = _slug(_text(entry.get("id"), 40) or title) or f"item-{len(items) + 1}"
        if item_id in seen:
            item_id = f"{item_id[:34]}-{len(items) + 1}"
        seen.add(item_id)
        item = {
            "id": item_id,
            "title": title,
            "category": _text(entry.get("category"), 40) or "General",
            "summary": _text(entry.get("summary"), 240),
            "tier": "premium" if entry.get("tier") == "premium" else "free",
        }
        if _looks_real(item["summary"]):
            item["summary"] = ""
        for key in keys:
            value = _text(entry.get(key), 400)
            item[key] = PLACEHOLDER_PREMIUM if not value or _looks_real(value) else value
        items.append(item)
    site["items"] = items if len(items) >= MIN_ITEMS else fallback["items"]
    if site["items"] is fallback["items"] and keys != fallback["premium_fields"]:
        site["premium_fields"] = fallback["premium_fields"]
        site["field_labels"] = fallback["field_labels"]
    site["sample_data"] = True
    return site


def site_prompt(spec: Optional[dict], requirement: str = "") -> str:
    meta = (spec or {}).get("_meta") or {}
    concept = _concept(spec)
    topic = _text(meta.get("target_display_name"), 60) or "the topic"

    def line(label: str, value: Any) -> str:
        value = _text(value, 300)
        return f"- {label}: {value}\n" if value else ""

    return (
        "You write the CONTENT for a small subscription website. Output ONLY one JSON object, "
        "no markdown fences and no commentary.\n\n"
        "PRODUCT BRIEF\n"
        + line("Topic the audience cares about", topic)
        + line("Product idea", concept.get("name"))
        + line("Format", concept.get("format"))
        + line("One-line pitch", concept.get("pitch"))
        + line("Audience", concept.get("target_customer"))
        + line("Why now", concept.get("why_now"))
        + line("Free tier", concept.get("free_tier"))
        + line("Premium tier", concept.get("premium_tier"))
        + line("Requirement", requirement)
        + "\nRULES\n"
        f"1. Write for people interested in {topic}. Do not mention statistics, signals, correlations, "
        "forecasts or dashboards.\n"
        "2. Every entry is a SAMPLE placeholder. Use obviously fictional names (for example "
        '"Sample Shop A"). NEVER include real brands, businesses, people, addresses, phone numbers, '
        "e-mail addresses, web links, prices or factual claims.\n"
        f"3. Provide between {MIN_ITEMS + 3} and 10 items. The last one or two may have \"tier\":\"premium\".\n"
        "4. Premium fields hold the extra detail a subscriber pays for (choose 2 to 4 keys, lowercase "
        "letters, digits or underscore, never id/title/category/summary/tier).\n\n"
        "JSON SHAPE\n"
        '{"name": "...", "tagline": "...", "why_now": "...", '
        '"free_features": ["..."], "premium_features": ["..."], '
        '"premium_fields": [{"key": "details", "label": "Full details"}], '
        '"items": [{"id": "slug", "title": "...", "category": "...", "summary": "...", '
        '"tier": "free", "details": "..."}]}\n'
    )


def parse_site_json(text: str) -> Optional[dict]:
    if not text:
        return None
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def render_main(site: Dict[str, Any]) -> str:
    """Render main.py from the fixed template. The result is checked to be valid Python."""
    template = (RUNTIME_DIR / "site_main.py.tpl").read_text(encoding="utf-8")
    literal = pprint.pformat(site, width=100, sort_dicts=False)
    source = template.replace("__SITE__", literal, 1)
    ast.parse(source)
    return source
