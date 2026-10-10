"""Stripe settings handed to generated MVPs.

MVPs are generated, publicly hosted apps, so they must never receive the
platform's full live secret key. They get only a restricted (rk_) or test
(sk_test_) key from MVP_STRIPE_SECRET_KEY. If that is unset or unsafe, no
secret key is injected and the MVP's pricing page shows "Subscriptions open soon".

Restricted key permissions the MVP runtime needs (Stripe Dashboard > Developers >
API keys > Create restricted key). Grant NOTHING else:
  * Checkout Sessions: write      (start checkout, and read a session to verify it)
  * Subscriptions: read           (check a subscriber is still active)
  * Products: read                (only if MVP_STRIPE_PRODUCT_ID is used)
Billing management uses Stripe's hosted customer-portal LOGIN link
(MVP_STRIPE_PORTAL_LOGIN_URL), so the key needs no billing-portal permission.

The key is shared by every MVP. If one MVP were compromised, the key could read
Checkout Sessions and Subscriptions across all of them, so keep MVP code free of
AI-written code (see the orchestrator) and consider Stripe Connect or a
platform-side billing service as the next step.
"""

import logging
import os
import secrets
from typing import Dict, Mapping, Optional

logger = logging.getLogger(__name__)

SAFE_SECRET_PREFIXES = ("rk_live_", "rk_test_", "sk_test_")


def mvp_stripe_env(environ: Optional[Mapping[str, str]] = None) -> Dict[str, str]:
    env = os.environ if environ is None else environ
    result: Dict[str, str] = {}

    key = (env.get("MVP_STRIPE_SECRET_KEY") or "").strip()
    if key:
        if key.startswith(SAFE_SECRET_PREFIXES):
            result["STRIPE_SECRET_KEY"] = key
        else:
            logger.warning(
                "MVP_STRIPE_SECRET_KEY ignored: it must be a restricted (rk_) or test (sk_test_) key"
            )

    portal = (env.get("MVP_STRIPE_PORTAL_LOGIN_URL") or "").strip()
    if portal.startswith("https://billing.stripe.com/"):
        result["MVP_STRIPE_PORTAL_LOGIN_URL"] = portal

    product = (env.get("MVP_STRIPE_PRODUCT_ID") or "").strip()
    if product.startswith("prod_"):
        result["STRIPE_PRODUCT_ID"] = product

    if (env.get("MVP_STRIPE_AUTOMATIC_TAX") or "").strip().lower() in ("1", "true", "yes"):
        result["MVP_STRIPE_AUTOMATIC_TAX"] = "true"
    return result


def new_session_secret() -> str:
    """A fresh signing secret for one MVP's subscriber cookies."""
    return secrets.token_urlsafe(48)
