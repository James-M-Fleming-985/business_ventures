"""Site content builder: validation of AI output, rendering, and the generated site end to end."""

import importlib.util
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", f"sqlite:///{os.path.join(tempfile.mkdtemp(), 'site.db')}")
os.environ.setdefault("SECRET_KEY", "test-secret-key-0123456789abcdef0123456789")

from services import mvp_site  # noqa: E402
from services.ai_code_generator_orchestrator import AICodeGeneratorOrchestrator  # noqa: E402
from test_mvp_runtime import FakeStripe, good_session, sub  # noqa: E402

SPEC = {
    "feature_name": "Ice Cream Hub",
    "_meta": {
        "target_display_name": "Ice cream",
        "selected_concept": {
            "name": "Scoop Guide",
            "format": "guide",
            "pitch": "The best scoops near you.",
            "target_customer": "Ice cream fans",
            "why_now": "Ice cream interest is about to rise",
            "free_tier": "Browse the guide",
            "premium_tier": "Full details and contacts",
        },
    },
    "_requirement_text": "Build: Scoop Guide (guide)",
}

GOOD_JSON = """```json
{"name": "Scoop Guide", "tagline": "Find the best scoops.", "why_now": "Summer is coming",
 "free_features": ["Browse the guide"], "premium_features": ["Full details"],
 "premium_fields": [{"key": "details", "label": "Full details"}, {"key": "tip", "label": "Insider tip"}],
 "items": [
  {"id": "a", "title": "Sample Parlour A", "category": "Parlours", "summary": "A fictional parlour.", "details": "PREMIUM-A", "tip": "TIP-A"},
  {"id": "b", "title": "Sample Parlour B", "category": "Parlours", "summary": "Another one.", "details": "PREMIUM-B", "tip": "TIP-B"},
  {"id": "c", "title": "Sample Van C", "category": "Vans", "summary": "A fictional van.", "details": "PREMIUM-C", "tip": "TIP-C"},
  {"id": "d", "title": "Sample Brand D", "category": "Brands", "summary": "A fictional brand.", "details": "PREMIUM-D", "tip": "TIP-D", "tier": "premium"}
 ]}
```"""


def fallback():
    return mvp_site.default_site(SPEC, build_id=7, ga4_id="G-ABCD1234")


# --- default site -------------------------------------------------------------

def test_default_site_is_complete_and_audience_focused():
    site = fallback()
    assert site["name"] == "Scoop Guide" and site["sample_data"] is True
    assert len(site["items"]) == 8 and site["premium_fields"] == ["details", "insider_tip", "contact"]
    assert any(i["tier"] == "premium" for i in site["items"])
    content = str({k: v for k, v in site.items() if k not in ("beacon_url", "ga4_measurement_id")}).lower()
    assert "dashboard" not in content and "granger" not in content and "correlation" not in content


def test_default_site_without_any_spec_still_works():
    site = mvp_site.default_site(None)
    assert site["name"] and len(site["items"]) >= mvp_site.MIN_ITEMS


# --- normalising untrusted AI output --------------------------------------------

def test_good_ai_content_is_used():
    site = mvp_site.normalise_site(mvp_site.parse_site_json(GOOD_JSON), fallback())
    assert [i["id"] for i in site["items"]] == ["a", "b", "c", "d"]
    assert site["premium_fields"] == ["details", "tip"] and site["field_labels"]["tip"] == "Insider tip"
    assert site["items"][3]["tier"] == "premium" and site["items"][0]["tier"] == "free"
    assert site["items"][0]["details"] == "PREMIUM-A"
    assert site["ga4_measurement_id"] == "G-ABCD1234" and "beacon_url" not in site


@pytest.mark.parametrize("raw", [None, [], "text", 5, {}])
def test_unusable_ai_output_falls_back(raw):
    base = fallback()
    result = mvp_site.normalise_site(raw, base)
    assert result["items"] == base["items"] and result["name"] == base["name"]


def test_too_few_valid_items_falls_back_to_default_items():
    raw = {"name": "X", "items": [{"title": "Only one"}]}
    base = fallback()
    assert mvp_site.normalise_site(raw, base)["items"] == base["items"]


def test_reserved_or_invalid_premium_keys_are_rejected():
    raw = {"premium_fields": [{"key": "tier", "label": "x"}, {"key": "id", "label": "x"}, {"key": "Bad Key", "label": "x"},
                              {"key": "ok_key", "label": "OK"}, {"key": "ok_key", "label": "dup"}, "junk", {"key": "locked", "label": "x"}],
           "items": [{"title": f"Sample {n}", "ok_key": "v"} for n in range(5)]}
    site = mvp_site.normalise_site(raw, fallback())
    assert site["premium_fields"] == ["ok_key"]


def test_item_fields_outside_the_declared_premium_fields_are_dropped():
    raw = {"premium_fields": [{"key": "details", "label": "Details"}],
           "items": [{"title": f"Sample {n}", "details": "d", "secret_extra": "LEAK", "link": "x"} for n in range(5)]}
    site = mvp_site.normalise_site(raw, fallback())
    assert all("secret_extra" not in i and "link" not in i for i in site["items"])


def test_real_looking_contact_data_is_replaced_in_sample_content():
    raw = {"items": [{"title": f"Sample {n}", "summary": "Call +44 20 7946 0958 now", "details": "Visit https://real.example.com",
                      "insider_tip": "mail me@real.com", "contact": "01234 567890"} for n in range(5)]}
    site = mvp_site.normalise_site(raw, fallback())
    for item in site["items"]:
        assert item["summary"] == ""
        assert item["details"] == item["insider_tip"] == item["contact"] == mvp_site.PLACEHOLDER_PREMIUM


def test_titles_that_look_real_are_skipped():
    raw = {"items": [{"title": "Visit www.real.com"}, {"title": "Email a@b.com"}] + [{"title": f"Sample {n}"} for n in range(4)]}
    assert len(mvp_site.normalise_site(raw, fallback())["items"]) == 4


def test_limits_and_unique_ids():
    raw = {"name": "N" * 500, "tagline": "T" * 500,
           "items": [{"id": "same", "title": f"Sample {n}", "summary": "S" * 900} for n in range(30)]}
    site = mvp_site.normalise_site(raw, fallback())
    assert len(site["name"]) == 60 and len(site["tagline"]) == 160
    assert len(site["items"]) == mvp_site.MAX_ITEMS
    ids = [i["id"] for i in site["items"]]
    assert len(set(ids)) == len(ids) and all(len(i) <= 40 for i in ids)
    assert all(len(i["summary"]) <= 240 for i in site["items"])


def test_control_characters_are_removed():
    raw = {"name": "Evil\x00Name\r\nTwo", "items": [{"title": f"Sample {n}\x1b[31m"} for n in range(4)]}
    site = mvp_site.normalise_site(raw, fallback())
    assert "\x00" not in site["name"] and "\n" not in site["name"] and "\x1b" not in str(site["items"])


def test_parse_site_json_handles_fences_prose_and_garbage():
    assert mvp_site.parse_site_json('Here you go: {"name": "x"} thanks')["name"] == "x"
    assert mvp_site.parse_site_json("```json\n{\"a\": 1}\n```") == {"a": 1}
    assert mvp_site.parse_site_json("not json") is None
    assert mvp_site.parse_site_json("{broken") is None
    assert mvp_site.parse_site_json("[1, 2]") is None
    assert mvp_site.parse_site_json("") is None


def test_tracking_config_validates_ids():
    assert mvp_site.tracking_config("G-ABCD1234") == {"ga4_measurement_id": "G-ABCD1234"}
    assert mvp_site.tracking_config('G-1"><script>')["ga4_measurement_id"] == ""
    assert mvp_site.tracking_config("") == {"ga4_measurement_id": ""}


def test_site_prompt_is_audience_focused_and_forbids_real_facts():
    prompt = mvp_site.site_prompt(SPEC, "Build: Scoop Guide")
    assert "Ice cream" in prompt and "SAMPLE" in prompt and "fictional" in prompt
    assert "Do not mention statistics" in prompt and "JSON" in prompt
    assert "dashboard" not in prompt.replace("or dashboards", "")


# --- rendering ---------------------------------------------------------------------

def test_render_main_is_valid_python_even_for_hostile_content():
    """Hostile text must stay data: it round-trips through the SITE literal and is never code."""
    import ast

    hostile = '"""\'\'\'\\ ); import os; os.system("x") #'
    raw = {"name": hostile, "tagline": hostile,
           "items": [{"title": f"Sample {n} {hostile}", "summary": hostile, "details": hostile} for n in range(5)]}
    site = mvp_site.normalise_site(raw, fallback())
    source = mvp_site.render_main(site)
    tree = ast.parse(source)

    assert not any(isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "system" for n in ast.walk(tree))
    assert not any(isinstance(n, ast.Import) and any(a.name == "subprocess" for a in n.names) for n in ast.walk(tree))
    assign = next(n for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "SITE")
    assert ast.literal_eval(assign.value) == site


def load_site(tmp_path, site, monkeypatch, env=True):
    """Render a site into tmp_path and import it the way uvicorn would."""
    (tmp_path / "main.py").write_text(mvp_site.render_main(site))
    (tmp_path / "mvp_runtime.py").write_text(mvp_site.runtime_source())
    monkeypatch.syspath_prepend(str(tmp_path))
    sys.modules.pop("mvp_runtime", None)
    spec = importlib.util.spec_from_file_location("generated_site_main", tmp_path / "main.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if env:
        monkeypatch.setenv("STRIPE_SECRET_KEY", "rk_test_restricted")
        monkeypatch.setenv("MVP_SESSION_SECRET", "s" * 40)
        monkeypatch.setenv("MVP_APP_ID", "mvp_7")
        monkeypatch.setenv("MVP_BUILD_ID", "7")
        monkeypatch.setenv("MVP_PUBLIC_URL", "https://shop.example.com")
    fake = FakeStripe()
    monkeypatch.setattr(module.rt, "stripe", fake)
    module.rt.clear_subscription_cache()
    module.rt._limiter.clear()
    return module, TestClient(module.app, base_url="https://shop.example.com"), fake


@pytest.fixture()
def cleanup_modules():
    saved = sys.modules.get("mvp_runtime")
    yield
    if saved is not None:
        sys.modules["mvp_runtime"] = saved
    else:
        sys.modules.pop("mvp_runtime", None)


@pytest.fixture()
def ai_site(tmp_path, monkeypatch, cleanup_modules):
    site = mvp_site.normalise_site(mvp_site.parse_site_json(GOOD_JSON), fallback())
    return load_site(tmp_path, site, monkeypatch)


def test_landing_explore_item_and_pricing_pages_render(ai_site):
    _, client, _ = ai_site
    home = client.get("/")
    assert home.status_code == 200 and "Scoop Guide" in home.text and "Summer is coming" in home.text
    assert "Sample data" in home.text and "G-ABCD1234" in home.text
    assert "Sample Parlour A" in client.get("/explore").text
    assert "Sample Parlour A" in client.get("/item/a").text
    pricing = client.get("/pricing?country=GB")
    assert pricing.status_code == 200 and "£0.99" in pricing.text and 'id="subscribe"' in pricing.text
    assert client.get("/health").json() == {"status": "healthy"}
    assert client.get("/favicon.ico").status_code == 200
    assert '<link rel="icon" href="/favicon.ico"' in home.text


def test_visitor_never_receives_premium_content_anywhere(ai_site):
    _, client, _ = ai_site
    pages = ["/", "/explore", "/item/a", "/item/d", "/api/items", "/api/items/a", "/api/items/d", "/pricing", "/account"]
    for path in pages:
        text = client.get(path).text
        assert "PREMIUM-" not in text and "TIP-" not in text, path
    assert client.get("/item/d").status_code == 200
    assert "Subscribe to unlock" in client.get("/explore").text or "Premium" in client.get("/explore").text
    listing = client.get("/api/items").json()
    assert listing["subscriber"] is False
    assert next(i for i in listing["items"] if i["id"] == "d") == {
        "id": "d", "title": "Sample Brand D", "category": "Brands", "locked": True}


def test_subscriber_gets_premium_content(ai_site):
    _, client, fake = ai_site
    fake.subscriptions["cus_123"] = [sub()]
    fake.sessions["cs_test_abcdefghijklmnop"] = good_session()
    assert client.get("/checkout/success?session_id=cs_test_abcdefghijklmnop", follow_redirects=False).status_code == 303
    assert "PREMIUM-A" in client.get("/item/a").text and "TIP-A" in client.get("/item/a").text
    assert "PREMIUM-D" in client.get("/item/d").text
    assert client.get("/api/items/a").json()["details"] == "PREMIUM-A"
    assert "Premium active" in client.get("/account").text


def test_unknown_or_malicious_item_ids_are_404(ai_site):
    _, client, _ = ai_site
    for bad in ("nope", "../../etc/passwd", "A", "a%00", "x" * 80, "a;b"):
        assert client.get(f"/item/{bad}").status_code in (404, 422), bad
        assert client.get(f"/api/items/{bad}").status_code in (404, 422), bad


def test_docs_and_openapi_are_not_exposed(ai_site):
    _, client, _ = ai_site
    assert client.get("/docs").status_code == 404 and client.get("/openapi.json").status_code == 404


def test_security_headers_are_present(ai_site):
    _, client, _ = ai_site
    headers = client.get("/").headers
    assert headers["x-frame-options"] == "DENY" and headers["x-content-type-options"] == "nosniff"
    assert "cookie" in headers["vary"].lower()


def test_xss_in_ai_content_is_escaped(tmp_path, monkeypatch, cleanup_modules):
    payload = "<script>alert(1)</script>"
    raw = {"name": payload, "tagline": payload, "why_now": payload, "free_features": [payload], "premium_features": [payload],
           "premium_fields": [{"key": "details", "label": payload}],
           "items": [{"id": f"x{n}", "title": f"Sample {n} {payload}", "category": payload, "summary": payload,
                      "details": payload} for n in range(5)]}
    _, client, _ = load_site(tmp_path, mvp_site.normalise_site(raw, fallback()), monkeypatch)
    for path in ("/", "/explore", "/item/x1", "/pricing"):
        assert payload not in client.get(path).text, path
    assert "&lt;script&gt;" in client.get("/explore").text


def test_javascript_links_are_never_rendered_as_hyperlinks(tmp_path, monkeypatch, cleanup_modules):
    raw = {"premium_fields": [{"key": "link", "label": "Link"}],
           "items": [{"id": f"x{n}", "title": f"Sample {n}", "link": "javascript:alert(1)"} for n in range(5)]}
    _, client, fake = load_site(tmp_path, mvp_site.normalise_site(raw, fallback()), monkeypatch)
    fake.subscriptions["cus_123"] = [sub()]
    fake.sessions["cs_test_abcdefghijklmnop"] = good_session()
    client.get("/checkout/success?session_id=cs_test_abcdefghijklmnop", follow_redirects=False)
    html = client.get("/item/x1").text
    assert 'href="javascript:' not in html and "javascript:alert(1)" in html


def test_site_works_with_default_content_and_without_stripe(tmp_path, monkeypatch, cleanup_modules):
    for name in ("STRIPE_SECRET_KEY", "MVP_SESSION_SECRET", "MVP_APP_ID"):
        monkeypatch.delenv(name, raising=False)
    _, client, _ = load_site(tmp_path, fallback(), monkeypatch, env=False)
    assert client.get("/").status_code == 200
    pricing = client.get("/pricing").text
    assert "Subscriptions open soon" in pricing and 'id="subscribe"' not in pricing
    assert client.post("/api/checkout").status_code == 503
    assert "Premium details appear here" not in client.get("/api/items").text


# --- orchestrator integration ------------------------------------------------------

def make_orchestrator(tmp_path, reply):
    orch = AICodeGeneratorOrchestrator({"provider": "anthropic", "output_base_path": str(tmp_path)})
    orch.ai_provider = MagicMock()
    if isinstance(reply, Exception):
        orch.ai_provider.generate_code.side_effect = reply
    else:
        orch.ai_provider.generate_code.return_value = reply
    return orch


def test_orchestrator_uses_valid_ai_content(tmp_path):
    orch = make_orchestrator(tmp_path, GOOD_JSON)
    main_py = orch._generate_main_wrapper(tmp_path / "src", "m", spec=SPEC, build_id=7)
    assert "Sample Parlour A" in main_py and "import mvp_runtime as rt" in main_py
    assert orch.ai_provider.generate_code.call_args.kwargs["max_tokens"] == orch.MAIN_WRAPPER_MAX_TOKENS


@pytest.mark.parametrize("reply", ["not json at all", "from fastapi import FastAPI\napp = FastAPI()", RuntimeError("no AI"), ""])
def test_orchestrator_falls_back_to_default_content(tmp_path, reply):
    orch = make_orchestrator(tmp_path, reply)
    main_py = orch._generate_main_wrapper(tmp_path / "src", "m", spec=SPEC, build_id=7)
    compile(main_py, "main.py", "exec")
    assert "Ice cream sample 1" in main_py


def test_deployment_files_ship_the_shared_runtime_and_stripe(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "layer_mvp_0007.py").write_text("class A:\n    pass\n")
    orch = make_orchestrator(tmp_path, GOOD_JSON)
    files = {f["path"]: f["content"] for f in orch._generate_deployment_files(Path(tmp_path), spec=SPEC, build_id=7)}
    assert files["mvp_runtime.py"] == mvp_site.runtime_source()
    assert "stripe" in files["requirements.txt"].split() and "fastapi" in files["requirements.txt"].split()
    assert files["Procfile"].startswith("web: uvicorn main:app")


def test_the_platform_live_stripe_key_never_reaches_generated_files(tmp_path, monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_" + "x" * 24)
    monkeypatch.setenv("MVP_STRIPE_SECRET_KEY", "rk_live_" + "y" * 24)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "layer_mvp_0007.py").write_text("class A:\n    pass\n")
    orch = make_orchestrator(tmp_path, GOOD_JSON)
    blob = "".join(f["content"] for f in orch._generate_deployment_files(Path(tmp_path), spec=SPEC, build_id=7))
    assert "x" * 24 not in blob and "y" * 24 not in blob


def test_items_beyond_the_free_limit_are_locked_by_direct_url_too(tmp_path, monkeypatch, cleanup_modules):
    raw = {"premium_fields": [{"key": "details", "label": "Details"}],
           "items": [{"id": f"x{n}", "title": f"Sample {n}", "summary": f"Sum {n}", "details": f"HIDDEN-{n}"} for n in range(1, 9)]}
    monkeypatch.setenv("MVP_FREE_ITEM_LIMIT", "2")
    _, client, _ = load_site(tmp_path, mvp_site.normalise_site(raw, fallback()), monkeypatch)
    assert "Sum 2" in client.get("/item/x2").text and "Sum 3" not in client.get("/item/x3").text
    assert client.get("/api/items/x3").json() == {"id": "x3", "title": "Sample 3", "category": "General",
                                                   "locked": True, "locked_fields": ["details"]}
    assert "Subscribe to unlock" in client.get("/item/x3").text or "Premium content" in client.get("/item/x3").text
    assert "HIDDEN-" not in client.get("/item/x3").text + client.get("/item/x2").text


def test_lone_surrogates_in_ai_content_do_not_crash_pages(tmp_path, monkeypatch, cleanup_modules):
    raw = {"name": "Hub \ud800", "tagline": "tag \udfff", "why_now": "now \ud800",
           "items": [{"id": f"s{n}", "title": f"Sample {n} \ud800", "summary": "ok \udc00"} for n in range(5)]}
    site = mvp_site.normalise_site(raw, fallback())
    assert all(ch not in str(site) for ch in ("\ud800", "\udfff", "\udc00"))
    _, client, _ = load_site(tmp_path, site, monkeypatch)
    for path in ("/", "/explore", "/item/s1", "/pricing", "/api/items"):
        assert client.get(path).status_code == 200, path
