"""Security and behaviour tests for the shared MVP subscription runtime."""

import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent / "templates" / "mvp" / "runtime"))
import mvp_runtime as rt  # noqa: E402

SECRET = "s" * 40
PREMIUM = ("details", "contact")
ITEMS = [
    {"id": f"i{n}", "title": f"Item {n}", "category": "Guides", "summary": f"Summary {n}",
     "tier": "free", "details": f"SECRET-DETAILS-{n}", "contact": f"SECRET-CONTACT-{n}"}
    for n in range(1, 8)
] + [{"id": "p1", "title": "Premium only", "category": "Deals", "summary": "SECRET-SUMMARY-P",
      "tier": "premium", "details": "SECRET-DETAILS-P", "contact": "SECRET-CONTACT-P"}]


class FakeStripe:
    """Records calls and returns canned answers, mirroring the parts of stripe we use."""

    def __init__(self):
        self.created, self.listed = [], []
        self.sessions, self.subscriptions = {}, {}
        self.fail = False
        self.checkout = SimpleNamespace(Session=SimpleNamespace(create=self._create, retrieve=self._retrieve))
        self.Subscription = SimpleNamespace(list=self._list)

    def _create(self, **params):
        if self.fail:
            raise RuntimeError("stripe down")
        self.created.append(params)
        return {"url": "https://checkout.stripe.com/c/pay/cs_test_abc"}

    def _retrieve(self, session_id, **params):
        if self.fail:
            raise RuntimeError("stripe down")
        return self.sessions[session_id]

    def _list(self, **params):
        self.listed.append(params)
        if self.fail:
            raise RuntimeError("stripe down")
        return {"data": self.subscriptions.get(params["customer"], [])}


def good_session(app_id="mvp_7", customer="cus_123", status="active", **overrides):
    session = {
        "id": "cs_test_abcdefghijklmnop",
        "mode": "subscription",
        "status": "complete",
        "payment_status": "paid",
        "customer": customer,
        "metadata": {"app_id": app_id, "pricing_country": "GB"},
        "subscription": {"status": status, "metadata": {"app_id": app_id}},
        "customer_details": {"address": {"country": "GB"}},
    }
    session.update(overrides)
    return session


@pytest.fixture()
def env(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "rk_test_restricted")
    monkeypatch.setenv("MVP_SESSION_SECRET", SECRET)
    monkeypatch.setenv("MVP_APP_ID", "mvp_7")
    monkeypatch.setenv("MVP_BUILD_ID", "7")
    monkeypatch.setenv("MVP_PUBLIC_URL", "https://shop.example.com")
    monkeypatch.delenv("STRIPE_PRODUCT_ID", raising=False)
    monkeypatch.delenv("MVP_STRIPE_AUTOMATIC_TAX", raising=False)
    fake = FakeStripe()
    monkeypatch.setattr(rt, "stripe", fake)
    rt.clear_subscription_cache()
    rt._limiter.clear()
    rt.configure("Ice Cream Hub", "Everything ice cream", ["Free preview"], ["Everything"])

    app = FastAPI()
    rt.install_security_headers(app)
    app.include_router(rt.router)

    @app.get("/items")
    def items(request: Request):
        return rt.apply_access(ITEMS, PREMIUM, rt.get_access(request))

    @app.get("/item/{item_id}")
    def item(item_id: str, request: Request):
        return rt.find_item(ITEMS, item_id, PREMIUM, rt.get_access(request), free_limit=5)

    client = TestClient(app, base_url="https://shop.example.com")
    return client, fake


def subscribe(client, fake, customer="cus_123"):
    fake.sessions["cs_test_abcdefghijklmnop"] = good_session(customer=customer)
    response = client.get("/checkout/success?session_id=cs_test_abcdefghijklmnop", follow_redirects=False)
    assert response.status_code == 303
    return response


# --- price table ------------------------------------------------------------

def test_price_table_is_valid():
    assert rt.validate_price_table() == []


def test_uk_price_is_99p():
    price = rt.price_for("GB")
    assert (price.currency, price.amount) == ("gbp", 99)
    assert rt.format_price(price) == "£0.99"


def test_local_currency_and_cheaper_in_lower_income_countries():
    gbp = {c: rt.approx_gbp_value(rt.price_for(c)) for c in ("GB", "DE", "PL", "BR", "IN", "PH")}
    assert rt.price_for("IN").currency == "inr" and rt.price_for("BR").currency == "brl"
    assert rt.price_for("DE").currency == "eur" and rt.price_for("PL").currency == "pln"
    assert gbp["IN"] < gbp["BR"] < gbp["PL"] < gbp["GB"]
    assert gbp["PH"] < gbp["BR"]


def test_zero_decimal_currencies_are_not_multiplied():
    assert rt.format_price(rt.price_for("JP")) == "¥150"
    assert rt.price_for("JP").amount == 150


def test_unknown_country_falls_back_to_usd():
    price = rt.price_for("XX")
    assert (price.country, price.currency, price.amount) == ("ZZ", "usd", 99)
    assert rt.price_for(None).currency == "usd"


def test_country_detection_order_and_validation(env):
    client, _ = env
    request = lambda headers: SimpleNamespace(headers=headers)  # noqa: E731
    assert rt.detect_country(request({"accept-language": "en-GB,en;q=0.9"})) == "GB"
    assert rt.detect_country(request({"accept-language": "pt-BR"})) == "BR"
    assert rt.detect_country(request({"cf-ipcountry": "IN", "accept-language": "en-GB"})) == "IN"
    assert rt.detect_country(request({}), override="de") == "DE"
    assert rt.detect_country(request({}), override="<script>") == "GB"
    assert rt.detect_country(request({})) == "GB"


# --- configuration guards ---------------------------------------------------

def test_full_live_secret_key_is_refused(env, monkeypatch):
    client, fake = env
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_" + "x" * 24)
    assert rt.billing_enabled() is False
    assert client.post("/api/checkout", json={"country": "GB"}).status_code == 503
    assert fake.created == []


@pytest.mark.parametrize("key", ["rk_live_" + "x" * 20, "rk_test_abc", "sk_test_abc"])
def test_restricted_and_test_keys_are_accepted(env, monkeypatch, key):
    monkeypatch.setenv("STRIPE_SECRET_KEY", key)
    assert rt.billing_enabled() is True


def test_short_session_secret_disables_billing(env, monkeypatch):
    monkeypatch.setenv("MVP_SESSION_SECRET", "too-short")
    assert rt.billing_enabled() is False


def test_missing_stripe_library_disables_billing(env, monkeypatch):
    monkeypatch.setattr(rt, "stripe", None)
    assert rt.billing_enabled() is False


# --- checkout: the server decides the price ---------------------------------

def test_client_cannot_choose_amount_or_currency(env):
    client, fake = env
    response = client.post("/api/checkout", json={"country": "IN", "amount": 1, "currency": "usd"})
    assert response.status_code == 200
    assert response.json() == {"checkout_url": "https://checkout.stripe.com/c/pay/cs_test_abc"}
    price_data = fake.created[0]["line_items"][0]["price_data"]
    assert (price_data["currency"], price_data["unit_amount"]) == ("inr", 4900)
    assert price_data["recurring"] == {"interval": "month"}


def test_checkout_uses_uk_price_by_default(env):
    client, fake = env
    client.post("/api/checkout")
    price_data = fake.created[0]["line_items"][0]["price_data"]
    assert (price_data["currency"], price_data["unit_amount"]) == ("gbp", 99)


def test_checkout_attributes_revenue_and_uses_configured_urls(env):
    client, fake = env
    response = client.post("/api/checkout", json={"country": "GB"}, headers={"host": "evil.example"})
    params = fake.created[0]
    assert params["mode"] == "subscription"
    assert params["metadata"]["app_id"] == "mvp_7" and params["metadata"]["build_id"] == "7"
    assert params["subscription_data"]["metadata"]["app_id"] == "mvp_7"
    assert params["success_url"] == "https://shop.example.com/checkout/success?session_id={CHECKOUT_SESSION_ID}"
    assert params["cancel_url"] == "https://shop.example.com/checkout/cancel"
    assert "evil.example" not in str(params)
    assert response.status_code == 200


def test_checkout_uses_configured_product_and_optional_tax(env, monkeypatch):
    client, fake = env
    monkeypatch.setenv("STRIPE_PRODUCT_ID", "prod_abc123")
    monkeypatch.setenv("MVP_STRIPE_AUTOMATIC_TAX", "true")
    client.post("/api/checkout")
    params = fake.created[0]
    assert params["line_items"][0]["price_data"]["product"] == "prod_abc123"
    assert "product_data" not in params["line_items"][0]["price_data"]
    assert params["automatic_tax"] == {"enabled": True}


def test_checkout_stripe_failure_is_generic(env):
    client, fake = env
    fake.fail = True
    response = client.post("/api/checkout")
    assert response.status_code == 502
    assert "stripe down" not in response.text


def test_checkout_is_rate_limited(env):
    client, _ = env
    statuses = [client.post("/api/checkout").status_code for _ in range(12)]
    assert statuses[:10] == [200] * 10
    assert statuses[10:] == [429, 429]


# --- subscriber cookie ------------------------------------------------------

def test_token_round_trip():
    assert rt.read_token(rt.issue_token("cus_abc")) == "cus_abc" if rt._session_secret() else True


def test_token_round_trip_with_secret(env):
    assert rt.read_token(rt.issue_token("cus_abc")) == "cus_abc"


def test_tampered_tokens_are_rejected(env):
    token = rt.issue_token("cus_abc")
    body, signature = token.split(".")
    forged_body = rt._b64(b'{"cus":"cus_other","aid":"mvp_7","exp":9999999999}')
    assert rt.read_token(f"{forged_body}.{signature}") is None
    assert rt.read_token(f"{body}.{rt._b64(b'x' * 32)}") is None
    assert rt.read_token(body) is None
    assert rt.read_token(token + ".extra") is None
    assert rt.read_token("not-a-token") is None
    assert rt.read_token("") is None and rt.read_token(None) is None


def test_expired_token_is_rejected(env):
    old = rt.issue_token("cus_abc", now=time.time() - rt.COOKIE_MAX_AGE - 10)
    assert rt.read_token(old) is None


def test_token_for_another_mvp_is_rejected(env, monkeypatch):
    token = rt.issue_token("cus_abc")
    monkeypatch.setenv("MVP_APP_ID", "mvp_8")
    assert rt.read_token(token) is None


def test_token_signed_with_another_secret_is_rejected(env, monkeypatch):
    token = rt.issue_token("cus_abc")
    monkeypatch.setenv("MVP_SESSION_SECRET", "t" * 40)
    assert rt.read_token(token) is None


# --- Stripe subscription check ----------------------------------------------

def sub(status="active", app_id="mvp_7"):
    return {"status": status, "metadata": {"app_id": app_id}}


def test_active_subscription_for_this_mvp_counts(env):
    _, fake = env
    fake.subscriptions["cus_1"] = [sub("canceled"), sub("trialing")]
    assert rt.subscription_active("cus_1") is True


@pytest.mark.parametrize("status", ["canceled", "past_due", "unpaid", "incomplete", "paused"])
def test_inactive_statuses_do_not_count(env, status):
    _, fake = env
    fake.subscriptions["cus_1"] = [sub(status)]
    assert rt.subscription_active("cus_1") is False


def test_subscription_to_another_mvp_does_not_count(env):
    _, fake = env
    fake.subscriptions["cus_1"] = [sub("active", app_id="mvp_99")]
    assert rt.subscription_active("cus_1") is False


def test_stripe_outage_fails_closed_without_a_recent_answer(env):
    _, fake = env
    fake.fail = True
    assert rt.subscription_active("cus_1") is False


def test_stripe_outage_keeps_recent_subscribers_for_a_while(env):
    _, fake = env
    fake.subscriptions["cus_1"] = [sub()]
    now = time.time()
    assert rt.subscription_active("cus_1", now=now) is True
    fake.fail = True
    assert rt.subscription_active("cus_1", now=now + rt.POSITIVE_TTL + 5) is True
    assert rt.subscription_active("cus_1", now=now + rt.STALE_OK + 5) is False


def test_cancellation_takes_effect_after_the_cache_expires(env):
    _, fake = env
    fake.subscriptions["cus_1"] = [sub()]
    now = time.time()
    assert rt.subscription_active("cus_1", now=now) is True
    fake.subscriptions["cus_1"] = [sub("canceled")]
    assert rt.subscription_active("cus_1", now=now + 60) is True
    assert rt.subscription_active("cus_1", now=now + rt.POSITIVE_TTL + 5) is False


def test_stripe_is_not_called_on_every_request(env):
    _, fake = env
    fake.subscriptions["cus_1"] = [sub()]
    for _ in range(5):
        rt.subscription_active("cus_1")
    assert len(fake.listed) == 1


# --- free vs premium separation ---------------------------------------------

def test_visitor_never_receives_premium_content(env):
    client, _ = env
    body = client.get("/items").text
    assert "SECRET-" not in body
    listing = client.get("/items").json()
    assert sum(1 for i in listing if "summary" in i) == 5  # free preview limit
    assert sum(1 for i in listing if not i.get("locked")) == 5
    assert all(set(i) <= {"id", "title", "category", "locked"} for i in listing if i.get("locked"))
    assert "SECRET-SUMMARY-P" not in body


def test_visitor_item_detail_hides_premium_fields_but_names_them(env):
    client, _ = env
    detail = client.get("/item/i1").json()
    assert "details" not in detail and "contact" not in detail and "tier" not in detail
    assert detail["locked"] is False and detail["locked_fields"] == ["contact", "details"]
    assert detail["summary"] == "Summary 1"


def test_premium_tier_item_is_a_stub_for_visitors(env):
    client, _ = env
    detail = client.get("/item/p1").json()
    assert detail == {"id": "p1", "title": "Premium only", "category": "Deals", "locked": True,
                      "locked_fields": ["contact", "details"]}


def test_forged_cookie_is_treated_as_a_visitor(env):
    client, _ = env
    client.cookies.set("mvp_sub", rt._b64(b'{"cus":"cus_1","aid":"mvp_7","exp":9999999999}') + "." + rt._b64(b"x" * 32))
    assert "SECRET-" not in client.get("/items").text


def test_valid_cookie_without_active_subscription_is_a_visitor(env):
    client, fake = env
    fake.subscriptions["cus_1"] = [sub("canceled")]
    client.cookies.set("mvp_sub", rt.issue_token("cus_1"))
    assert "SECRET-" not in client.get("/items").text


def test_subscriber_sees_everything(env):
    client, fake = env
    fake.subscriptions["cus_123"] = [sub()]
    subscribe(client, fake)
    body = client.get("/items").text
    assert "SECRET-DETAILS-1" in body and "SECRET-DETAILS-P" in body and "SECRET-SUMMARY-P" in body
    assert client.get("/item/i1").json()["details"] == "SECRET-DETAILS-1"
    assert client.get("/item/p1").json()["locked"] is False


def test_apply_access_limit_and_helpers():
    visitor = rt.Access()
    result = rt.apply_access(ITEMS, PREMIUM, visitor, free_limit=2)
    assert [bool(i.get("locked")) for i in result[:4]] == [False, False, True, True]
    assert rt.apply_access(ITEMS, PREMIUM, visitor, free_limit=0)[0]["locked"] is True
    full = rt.apply_access(ITEMS, PREMIUM, rt.Access(True, "cus_1"))
    assert all("details" in i for i in full) and all("tier" not in i for i in full)
    assert rt.visitor_view(ITEMS[0], PREMIUM).keys() == {"id", "title", "category", "summary"}


def test_safe_href_only_allows_http_links():
    assert rt.safe_href("https://example.com/a?b=1") == "https://example.com/a?b=1"
    assert rt.safe_href("javascript:alert(1)") == ""
    assert rt.safe_href("data:text/html,x") == ""
    assert rt.safe_href('https://a.com/"onmouseover="x') == ""
    assert rt.safe_href(None) == ""


# --- checkout success -------------------------------------------------------

def test_success_sets_a_secure_http_only_cookie(env):
    client, fake = env
    response = subscribe(client, fake)
    cookie = response.headers["set-cookie"].lower()
    assert "mvp_sub=" in cookie and "httponly" in cookie and "samesite=lax" in cookie and "secure" in cookie
    assert response.headers["location"] == "/account?welcome=1"


def test_success_verifies_subscription_belongs_to_this_mvp(env):
    client, fake = env
    fake.sessions["cs_test_abcdefghijklmnop"] = good_session(app_id="mvp_99")
    response = client.get("/checkout/success?session_id=cs_test_abcdefghijklmnop")
    assert response.status_code == 400 and "set-cookie" not in response.headers


@pytest.mark.parametrize(
    "overrides",
    [
        {"status": "open"},
        {"payment_status": "unpaid"},
        {"mode": "payment"},
        {"customer": None},
        {"customer": "not-a-customer"},
        {"subscription": "sub_123"},
        {"subscription": {"status": "incomplete", "metadata": {"app_id": "mvp_7"}}},
        {"subscription": {"status": "active", "metadata": {"app_id": "other"}}},
        {"metadata": {}},
    ],
)
def test_success_rejects_incomplete_or_foreign_sessions(env, overrides):
    client, fake = env
    fake.sessions["cs_test_abcdefghijklmnop"] = good_session(**overrides)
    response = client.get("/checkout/success?session_id=cs_test_abcdefghijklmnop")
    assert response.status_code == 400 and "set-cookie" not in response.headers


@pytest.mark.parametrize("bad", ["", "abc", "cs_", "../../etc", "cs_test_abc def", "sub_1234567890123", "cs_" + "a" * 300])
def test_success_rejects_malformed_session_ids_without_calling_stripe(env, bad):
    client, fake = env
    fake.sessions = {}
    assert client.get("/checkout/success", params={"session_id": bad}).status_code == 400


def test_success_stripe_error_is_generic(env):
    client, fake = env
    fake.fail = True
    response = client.get("/checkout/success?session_id=cs_test_abcdefghijklmnop")
    assert response.status_code == 502 and "stripe down" not in response.text


def test_success_with_mismatched_billing_country_still_works_but_is_logged(env, caplog):
    client, fake = env
    fake.sessions["cs_test_abcdefghijklmnop"] = good_session(
        metadata={"app_id": "mvp_7", "pricing_country": "IN"},
        customer_details={"address": {"country": "GB"}},
    )
    with caplog.at_level("WARNING", logger="mvp_runtime"):
        response = client.get("/checkout/success?session_id=cs_test_abcdefghijklmnop", follow_redirects=False)
    assert response.status_code == 303
    assert "differs from billing country" in caplog.text


# --- account, portal, logout ------------------------------------------------

def test_account_page_reflects_subscription(env):
    client, fake = env
    assert "free plan" in client.get("/account").text
    fake.subscriptions["cus_123"] = [sub()]
    subscribe(client, fake)
    assert "Premium active" in client.get("/account").text


def test_billing_portal_api_no_longer_exists_and_stripe_portal_is_never_called(env):
    client, fake = env
    fake.subscriptions["cus_123"] = [sub()]
    subscribe(client, fake)
    assert client.post("/api/billing-portal").status_code == 404
    assert not hasattr(fake, "billing_portal")  # any use of it would have raised


def test_manage_billing_uses_the_hosted_login_link_only_when_valid(env, monkeypatch):
    client, fake = env
    fake.subscriptions["cus_123"] = [sub()]
    subscribe(client, fake)
    assert "use the link in your Stripe receipt email" in client.get("/account").text
    monkeypatch.setenv("MVP_STRIPE_PORTAL_LOGIN_URL", "https://billing.stripe.com/p/login/test_abc123")
    html = client.get("/account").text
    assert 'href="https://billing.stripe.com/p/login/test_abc123"' in html and "Manage billing" in html
    for bad in ("https://evil.example/p/login/x", "javascript:alert(1)", "http://billing.stripe.com/p/login/x",
                'https://billing.stripe.com/"onclick="x'):
        monkeypatch.setenv("MVP_STRIPE_PORTAL_LOGIN_URL", bad)
        assert "Manage billing" not in client.get("/account").text, bad


def test_logout_clears_the_cookie(env):
    client, fake = env
    fake.subscriptions["cus_123"] = [sub()]
    subscribe(client, fake)
    response = client.post("/account/logout", follow_redirects=False)
    assert response.status_code == 303 and "mvp_sub=" in response.headers["set-cookie"]
    assert 'max-age=0' in response.headers["set-cookie"].lower()


# --- pages, escaping, headers, tracking -------------------------------------

def test_pricing_page_shows_local_price_and_escapes_everything(env):
    client, _ = env
    rt.configure("<script>alert(1)</script> Hub", "<img src=x onerror=alert(1)>", ["<b>x</b>"], ["<i>y</i>"])
    html = client.get("/pricing?country=IN").text
    assert "<script>alert(1)</script>" not in html and "<img src=x" not in html
    assert "<b>x</b>" not in html and "&lt;b&gt;x&lt;/b&gt;" in html
    assert "₹49.00" in html and "INR" in html
    assert 'value="IN" selected' in html


def test_pricing_page_survives_hostile_country_parameter(env):
    client, _ = env
    response = client.get("/pricing", params={"country": "\"><script>alert(1)</script>"})
    assert response.status_code == 200 and "<script>alert(1)</script>" not in response.text
    assert "£0.99" in response.text
    assert client.get("/pricing?country=ZZ").status_code == 200


def test_pricing_without_billing_shows_disabled_button(env, monkeypatch):
    client, _ = env
    monkeypatch.delenv("STRIPE_SECRET_KEY")
    html = client.get("/pricing").text
    assert "Subscriptions open soon" in html and 'id="subscribe"' not in html


def test_pricing_json(env):
    client, _ = env
    assert client.get("/api/pricing?country=GB").json() == {
        "country": "GB", "currency": "gbp", "amount": 99, "display": "£0.99", "interval": "month"}


def test_security_headers_and_cache_rules(env):
    client, _ = env
    response = client.get("/pricing")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "cookie" in response.headers["vary"].lower()
    assert response.headers["cache-control"] == "private, no-cache"
    assert client.get("/items", headers={"x-forwarded-proto": "https"}).headers["strict-transport-security"]


def test_sample_banner_and_google_analytics(env):
    client, _ = env
    rt.configure("Hub", sample_data=True, ga4_measurement_id="G-ABCD1234")
    html = client.get("/pricing").text
    assert "Sample data" in html
    assert "googletagmanager.com/gtag/js?id=G-ABCD1234" in html
    assert "mvp-beacon" not in html  # the platform injects its engagement beacon, not the site
    rt.configure("Hub", sample_data=False)
    assert "Sample data" not in client.get("/pricing").text


def test_invalid_analytics_id_is_dropped(env):
    client, _ = env
    rt.configure("Hub", ga4_measurement_id='G-1"></script><script>x')
    html = client.get("/pricing").text
    assert "googletagmanager" not in html and "<script>x" not in html


def test_public_base_url_ignores_untrusted_host_header(env, monkeypatch):
    client, fake = env
    monkeypatch.delenv("MVP_PUBLIC_URL")
    monkeypatch.setenv("RAILWAY_PUBLIC_DOMAIN", "mvp-7.up.railway.app")
    client.post("/api/checkout", headers={"host": "evil.example"})
    assert fake.created[0]["success_url"].startswith("https://mvp-7.up.railway.app/")
    monkeypatch.setenv("MVP_PUBLIC_URL", "javascript:alert(1)")
    client.post("/api/checkout")
    assert fake.created[1]["success_url"].startswith("https://mvp-7.up.railway.app/")


def test_client_ip_uses_the_proxy_appended_address():
    request = SimpleNamespace(headers={"x-forwarded-for": "6.6.6.6, 203.0.113.9"}, client=None)
    assert rt.client_ip(request) == "203.0.113.9"


# --- newer stripe-python returns objects that are not dicts -------------------

class ModernStripeObject:
    """Mimics stripe-python >= 15: item access and to_dict(), but no dict methods such as .get()."""

    def __init__(self, data):
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def to_dict(self):
        return self._data

    def __getattr__(self, name):
        raise AttributeError(f"'{name}' is a dict method, but this is not a dict")


def modernize(fake):
    for namespace, name in (
        (fake.checkout.Session, "create"), (fake.checkout.Session, "retrieve"),
        (fake.Subscription, "list"),
    ):
        original = getattr(namespace, name)
        setattr(namespace, name, lambda *a, _original=original, **k: ModernStripeObject(_original(*a, **k)))


def test_runtime_works_with_stripe_objects_that_are_not_dicts(env):
    client, fake = env
    modernize(fake)
    assert client.post("/api/checkout", json={"country": "GB"}).json()["checkout_url"].startswith("https://checkout.stripe.com/")
    fake.subscriptions["cus_123"] = [sub()]
    subscribe(client, fake)
    assert "SECRET-DETAILS-1" in client.get("/items").text
    assert "Premium active" in client.get("/account").text


def test_missing_checkout_url_is_a_clean_error(env):
    client, fake = env
    fake._create = lambda **params: {}
    fake.checkout.Session.create = fake._create
    assert client.post("/api/checkout").status_code == 502


def test_footer_only_mentions_tax_when_automatic_tax_is_on(env, monkeypatch):
    client, _ = env
    assert "Taxes may be added" not in client.get("/pricing").text
    monkeypatch.setenv("MVP_STRIPE_AUTOMATIC_TAX", "true")
    assert "Taxes may be added at checkout" in client.get("/pricing").text


# --- free-preview limit applies to direct item URLs --------------------------------

def test_find_item_keeps_items_beyond_the_free_limit_locked(env):
    client, _ = env
    inside = client.get("/item/i5").json()
    beyond = client.get("/item/i6").json()
    assert inside["locked"] is False and inside["summary"] == "Summary 5" and "details" not in inside
    assert beyond == {"id": "i6", "title": "Item 6", "category": "Guides", "locked": True,
                      "locked_fields": ["contact", "details"]}
    assert client.get("/item/p1").json()["locked"] is True


def test_find_item_unknown_id_and_subscriber(env):
    visitor = rt.Access()
    assert rt.find_item(ITEMS, "nope", PREMIUM, visitor) is None
    full = rt.find_item(ITEMS, "i6", PREMIUM, rt.Access(True, "cus_1"))
    assert full["details"] == "SECRET-DETAILS-6" and full["locked"] is False
    assert rt.find_item(ITEMS, "i1", PREMIUM, visitor, free_limit=0)["locked"] is True


# --- lone surrogates must not crash page rendering ----------------------------------

def test_lone_surrogates_in_configuration_do_not_break_pages(env):
    client, _ = env
    rt.configure("Hub \ud800 name", "tag \udfff line", ["feature \ud800"], ["premium \udc00"])
    response = client.get("/pricing")
    assert response.status_code == 200 and "Hub  name" in response.text.replace("\ufffd", "")


# --- favicon --------------------------------------------------------------------

def test_favicon_matches_the_platform_files():
    root = Path(__file__).parent / "static"
    assert rt._FAVICON_ICO == (root / "favicon.ico").read_bytes()
    assert rt.FAVICON_SVG.strip() == (root / "favicon.svg").read_text().strip()


def test_favicon_is_served_and_linked_from_every_page(env):
    client, _ = env
    ico = client.get("/favicon.ico")
    assert ico.status_code == 200 and ico.headers["content-type"] == "image/x-icon"
    assert ico.content == rt._FAVICON_ICO and "max-age=86400" in ico.headers["cache-control"]
    svg = client.get("/favicon.svg")
    assert svg.status_code == 200 and svg.headers["content-type"].startswith("image/svg+xml")
    assert svg.headers["x-content-type-options"] == "nosniff"
    for path in ("/pricing", "/account", "/checkout/cancel"):
        html = client.get(path).text
        assert '<link rel="icon" href="/favicon.svg" type="image/svg+xml">' in html, path
        assert '<link rel="icon" href="/favicon.ico" sizes="any">' in html, path
