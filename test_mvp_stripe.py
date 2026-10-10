"""Stripe settings given to generated MVPs: never the platform's full live key."""

import re
from pathlib import Path

import pytest

from services import mvp_stripe

ROOT = Path(__file__).parent


def test_only_restricted_or_test_keys_are_passed_on():
    env = {"MVP_STRIPE_SECRET_KEY": "rk_live_" + "a" * 20}
    assert mvp_stripe.mvp_stripe_env(env) == {"STRIPE_SECRET_KEY": "rk_live_" + "a" * 20}
    assert mvp_stripe.mvp_stripe_env({"MVP_STRIPE_SECRET_KEY": "sk_test_abc"}) == {"STRIPE_SECRET_KEY": "sk_test_abc"}
    assert mvp_stripe.mvp_stripe_env({"MVP_STRIPE_SECRET_KEY": "rk_test_abc"}) == {"STRIPE_SECRET_KEY": "rk_test_abc"}


@pytest.mark.parametrize("key", ["sk_live_" + "a" * 20, "pk_live_abc", "whsec_abc", "garbage", " "])
def test_unsafe_keys_are_refused(key):
    assert mvp_stripe.mvp_stripe_env({"MVP_STRIPE_SECRET_KEY": key}) == {}


def test_the_platforms_own_stripe_variables_are_never_copied():
    env = {
        "STRIPE_SECRET_KEY": "sk_live_" + "a" * 20, "STRIPE_PUBLISHABLE_KEY": "pk_live_abc",
        "STRIPE_WEBHOOK_SECRET": "whsec_abc", "STRIPE_PRICE_PRO_MONTHLY": "price_1",
    }
    assert mvp_stripe.mvp_stripe_env(env) == {}


def test_optional_product_and_tax_settings():
    env = {"MVP_STRIPE_SECRET_KEY": "rk_test_abc", "MVP_STRIPE_PRODUCT_ID": "prod_123", "MVP_STRIPE_AUTOMATIC_TAX": "true"}
    assert mvp_stripe.mvp_stripe_env(env) == {
        "STRIPE_SECRET_KEY": "rk_test_abc", "STRIPE_PRODUCT_ID": "prod_123", "MVP_STRIPE_AUTOMATIC_TAX": "true"}
    assert "STRIPE_PRODUCT_ID" not in mvp_stripe.mvp_stripe_env({"MVP_STRIPE_PRODUCT_ID": "price_123"})
    assert "MVP_STRIPE_AUTOMATIC_TAX" not in mvp_stripe.mvp_stripe_env({"MVP_STRIPE_AUTOMATIC_TAX": "no"})


def test_hosted_portal_login_link_is_passed_on_only_when_it_is_a_stripe_url():
    ok = "https://billing.stripe.com/p/login/test_abc"
    assert mvp_stripe.mvp_stripe_env({"MVP_STRIPE_PORTAL_LOGIN_URL": ok}) == {"MVP_STRIPE_PORTAL_LOGIN_URL": ok}
    for bad in ("https://evil.example/p/login/x", "http://billing.stripe.com/x", "javascript:alert(1)", ""):
        assert mvp_stripe.mvp_stripe_env({"MVP_STRIPE_PORTAL_LOGIN_URL": bad}) == {}


def test_documented_key_permissions_do_not_include_the_billing_portal():
    doc = mvp_stripe.__doc__
    assert "Checkout Sessions: write" in doc and "Subscriptions: read" in doc
    assert "Customer portal / Billing portal sessions: write" not in doc


def test_session_secrets_are_long_and_unique():
    secrets_ = {mvp_stripe.new_session_secret() for _ in range(20)}
    assert len(secrets_) == 20 and all(len(s) >= 48 for s in secrets_)


def test_build_pipeline_uses_the_restricted_settings_only():
    """Source-level guard: _run_build must not copy the platform's Stripe variables to an MVP."""
    source = (ROOT / "routers" / "dashboard_real.py").read_text()
    assert "mvp_stripe_env" in source and "new_session_secret" in source
    assert "os.getenv(_stripe_var)" not in source
    assert not re.search(r'env_vars\[\s*["\']STRIPE_(SECRET|PUBLISHABLE)_KEY', source)
    assert not re.search(r'for _stripe_var in', source)
    assert "build_requirement_text(" in source
