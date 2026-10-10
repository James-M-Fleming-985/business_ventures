"""Subscription runtime shipped inside every generated MVP.

The security-critical parts of a subscription site (who counts as a subscriber,
what a visitor may see, how prices are set, how Stripe is called) live here,
are tested once in the platform repository and are copied unchanged into each
MVP. They are deliberately *not* written by an LLM per MVP.

Rules this module enforces:
  * Prices are decided on the server from a country table. The browser may
    send a country, never an amount or a currency.
  * Premium fields are removed from responses on the server before they are
    sent; nothing is hidden with CSS or client-side JavaScript.
  * A subscriber is proven by a signed cookie *and* an active Stripe
    subscription that belongs to this MVP.
  * A full live Stripe secret key (sk_live_) is refused. Use a restricted key.
  * Route handlers that call get_access() must be plain ``def`` functions so
    the occasional blocking Stripe call runs in FastAPI's threadpool.
  * The Stripe key needs only Checkout Sessions (write) and Subscriptions (read).
    Billing management uses Stripe's hosted portal login link, not the API.
"""

import base64
import hashlib
import hmac
import html
import json
import logging
import os
import re
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

try:  # billing is optional so a site without Stripe still runs
    import stripe
except ImportError:  # pragma: no cover
    stripe = None

log = logging.getLogger("mvp_runtime")

esc = html.escape


# ---------------------------------------------------------------------------
# Pricing: 99p in the UK, scaled to local purchasing power, in local currency
# ---------------------------------------------------------------------------
# Amounts are Stripe minor units (pence, cents, ...); JPY and KRW are
# zero-decimal so their amount is the number of yen / won.
# Review this table periodically: exchange rates drift. validate_price_table()
# checks every entry against Stripe's minimum charge and a sane GBP range.

BASE_COUNTRY = "GB"
DEFAULT_PRICE = ("usd", 99)
OTHER_COUNTRY = "ZZ"

ZERO_DECIMAL = frozenset({"jpy", "krw"})

COUNTRY_PRICES: Dict[str, Tuple[str, int]] = {}


def _tier(currency: str, amount: int, countries: str) -> None:
    for code in countries.split():
        COUNTRY_PRICES[code] = (currency, amount)


# Tier 1: about 99p
_tier("gbp", 99, "GB")
_tier("usd", 129, "US")
_tier("cad", 179, "CA")
_tier("aud", 199, "AU")
_tier("nzd", 219, "NZ")
_tier("eur", 119, "IE DE FR NL BE AT FI LU")
_tier("chf", 109, "CH")
_tier("sek", 1290, "SE")
_tier("nok", 1290, "NO")
_tier("dkk", 849, "DK")
_tier("sgd", 169, "SG")
_tier("aed", 499, "AE")
_tier("ils", 449, "IL")
_tier("hkd", 990, "HK")
# Tier 2: about 80p
_tier("eur", 99, "ES IT PT GR SI SK EE LV LT MT CY HR")
_tier("pln", 399, "PL")
_tier("czk", 2290, "CZ")
_tier("jpy", 150, "JP")
_tier("krw", 1500, "KR")
# Tier 3: about 60p
_tier("brl", 449, "BR")
_tier("mxn", 1400, "MX")
_tier("myr", 349, "MY")
_tier("thb", 2500, "TH")
_tier("zar", 1399, "ZA")
_tier("ron", 349, "RO")
# Tier 4: about 40p
_tier("inr", 4900, "IN")
_tier("php", 2900, "PH")

COUNTRY_NAMES = {
    "GB": "United Kingdom", "US": "United States", "CA": "Canada", "AU": "Australia",
    "NZ": "New Zealand", "IE": "Ireland", "DE": "Germany", "FR": "France",
    "NL": "Netherlands", "BE": "Belgium", "AT": "Austria", "FI": "Finland",
    "LU": "Luxembourg", "CH": "Switzerland", "SE": "Sweden", "NO": "Norway",
    "DK": "Denmark", "SG": "Singapore", "AE": "United Arab Emirates", "IL": "Israel",
    "HK": "Hong Kong", "ES": "Spain", "IT": "Italy", "PT": "Portugal", "GR": "Greece",
    "SI": "Slovenia", "SK": "Slovakia", "EE": "Estonia", "LV": "Latvia",
    "LT": "Lithuania", "MT": "Malta", "CY": "Cyprus", "HR": "Croatia", "PL": "Poland",
    "CZ": "Czechia", "JP": "Japan", "KR": "South Korea", "BR": "Brazil",
    "MX": "Mexico", "MY": "Malaysia", "TH": "Thailand", "ZA": "South Africa",
    "RO": "Romania", "IN": "India", "PH": "Philippines", OTHER_COUNTRY: "Other countries",
}

# Stripe minimum charge per currency, minor units
# (https://docs.stripe.com/currencies#minimum-and-maximum-charge-amounts).
STRIPE_MINIMUMS = {
    "usd": 50, "aed": 200, "aud": 50, "brl": 50, "cad": 50, "chf": 50, "czk": 1500,
    "dkk": 250, "eur": 50, "gbp": 30, "hkd": 400, "ils": 50, "inr": 50, "jpy": 50,
    "krw": 50, "mxn": 1000, "myr": 200, "nok": 300, "nzd": 50, "php": 50, "pln": 200,
    "ron": 200, "sek": 300, "sgd": 50, "thb": 1000, "zar": 50,
}

# Rough GBP value of one major unit. Only used by validate_price_table().
APPROX_GBP_PER_UNIT = {
    "gbp": 1.0, "usd": 0.77, "cad": 0.555, "aud": 0.50, "nzd": 0.455, "eur": 0.855,
    "chf": 0.935, "sek": 0.08, "nok": 0.074, "dkk": 0.115, "sgd": 0.58, "aed": 0.21,
    "ils": 0.22, "hkd": 0.098, "pln": 0.205, "czk": 0.0355, "jpy": 0.0051,
    "krw": 0.00054, "brl": 0.139, "mxn": 0.0417, "myr": 0.178, "thb": 0.0227,
    "zar": 0.043, "ron": 0.17, "inr": 0.0091, "php": 0.0132,
}

_SYMBOLS = {
    "gbp": "£", "usd": "$", "eur": "€", "cad": "CA$", "aud": "A$", "nzd": "NZ$",
    "sgd": "S$", "hkd": "HK$", "jpy": "¥", "krw": "₩", "inr": "₹", "php": "₱",
    "brl": "R$", "mxn": "MX$", "ils": "₪", "thb": "฿", "zar": "R", "myr": "RM",
}


@dataclass(frozen=True)
class Price:
    country: str
    currency: str
    amount: int


def price_for(country: Optional[str]) -> Price:
    code = (country or "").upper()
    if code in COUNTRY_PRICES:
        currency, amount = COUNTRY_PRICES[code]
        return Price(code, currency, amount)
    return Price(OTHER_COUNTRY, *DEFAULT_PRICE)


def _major(price: Price) -> float:
    return float(price.amount) if price.currency in ZERO_DECIMAL else price.amount / 100.0


def format_price(price: Price) -> str:
    major = _major(price)
    text = f"{major:,.0f}" if price.currency in ZERO_DECIMAL else f"{major:,.2f}"
    symbol = _SYMBOLS.get(price.currency)
    return f"{symbol}{text}" if symbol else f"{text} {price.currency.upper()}"


def approx_gbp_value(price: Price) -> float:
    return _major(price) * APPROX_GBP_PER_UNIT[price.currency]


def validate_price_table() -> List[str]:
    """Return a list of problems; empty means the table is sound."""
    problems = []
    for country, (currency, amount) in COUNTRY_PRICES.items():
        price = Price(country, currency, amount)
        if country not in COUNTRY_NAMES:
            problems.append(f"{country}: no display name")
        if currency not in STRIPE_MINIMUMS:
            problems.append(f"{country}: unknown currency {currency}")
            continue
        if amount < STRIPE_MINIMUMS[currency]:
            problems.append(f"{country}: {amount} {currency} is below Stripe's minimum")
        gbp = approx_gbp_value(price)
        if gbp < 0.35:
            problems.append(f"{country}: about £{gbp:.2f} is too close to Stripe's £0.30 minimum")
        if gbp > 1.5:
            problems.append(f"{country}: about £{gbp:.2f} is far above the 99p base price")
    return problems


_COUNTRY_RE = re.compile(r"^[A-Za-z]{2}$")


def detect_country(request: Request, override: Optional[str] = None) -> str:
    """Best-effort visitor country: explicit choice, CDN header, Accept-Language, else UK."""
    candidates = [override, request.headers.get("cf-ipcountry"), request.headers.get("x-vercel-ip-country")]
    match = re.search(r"-([A-Za-z]{2})\b", request.headers.get("accept-language", ""))
    if match:
        candidates.append(match.group(1))
    for candidate in candidates:
        if candidate and _COUNTRY_RE.match(candidate.strip()):
            return candidate.strip().upper()
    return BASE_COUNTRY


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def app_id() -> str:
    return _env("MVP_APP_ID")


def build_id() -> str:
    return _env("MVP_BUILD_ID")


SAFE_KEY_PREFIXES = ("rk_live_", "rk_test_", "sk_test_")


def _stripe_key() -> str:
    key = _env("STRIPE_SECRET_KEY")
    if not key:
        return ""
    if not key.startswith(SAFE_KEY_PREFIXES):
        log.error("STRIPE_SECRET_KEY refused: MVPs only accept a restricted (rk_) or test (sk_test_) key")
        return ""
    return key


def _session_secret() -> str:
    secret = _env("MVP_SESSION_SECRET")
    return secret if len(secret) >= 32 else ""


def billing_enabled() -> bool:
    return bool(stripe is not None and _stripe_key() and _session_secret() and app_id())


def free_item_limit() -> int:
    try:
        return max(0, int(_env("MVP_FREE_ITEM_LIMIT", "5")))
    except ValueError:
        return 5


_site: Dict[str, Any] = {
    "product_name": "Premium membership",
    "tagline": "",
    "free_features": [],
    "premium_features": [],
    "sample_data": True,
    "ga4_measurement_id": "",
}

_GA4_RE = re.compile(r"^G-[A-Z0-9]{4,20}$")


def _clean(text: Any, limit: int) -> str:
    text = str(text or "").encode("utf-8", "ignore").decode("utf-8")  # drop lone surrogates
    return re.sub(r"[\x00-\x1f\x7f]", " ", text).strip()[:limit]


def configure(
    product_name: str,
    tagline: str = "",
    free_features: Iterable[str] = (),
    premium_features: Iterable[str] = (),
    sample_data: bool = True,
    ga4_measurement_id: str = "",
) -> None:
    _site["product_name"] = _clean(product_name, 80) or "Premium membership"
    _site["tagline"] = _clean(tagline, 200)
    _site["free_features"] = [_clean(f, 120) for f in list(free_features)[:8] if _clean(f, 120)]
    _site["premium_features"] = [_clean(f, 120) for f in list(premium_features)[:8] if _clean(f, 120)]
    _site["sample_data"] = bool(sample_data)
    _site["ga4_measurement_id"] = ga4_measurement_id if _GA4_RE.match(ga4_measurement_id or "") else ""


def site() -> Dict[str, Any]:
    return dict(_site)


# ---------------------------------------------------------------------------
# Subscriber identity: signed cookie + live Stripe check
# ---------------------------------------------------------------------------

COOKIE_NAME = "mvp_sub"
COOKIE_MAX_AGE = 30 * 24 * 3600
ACTIVE_STATUSES = frozenset({"active", "trialing"})
POSITIVE_TTL = 3600
NEGATIVE_TTL = 300
STALE_OK = 24 * 3600
_CACHE_MAX = 10000

_sub_cache: Dict[str, Tuple[bool, float]] = {}
_cache_lock = threading.Lock()


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(payload: bytes) -> bytes:
    return hmac.new(_session_secret().encode(), b"mvp-sub-v1:" + payload, hashlib.sha256).digest()


def issue_token(customer_id: str, now: Optional[float] = None) -> str:
    payload = json.dumps(
        {"cus": customer_id, "aid": app_id(), "exp": int((now or time.time()) + COOKIE_MAX_AGE)},
        separators=(",", ":"),
    ).encode()
    return f"{_b64(payload)}.{_b64(_sign(payload))}"


def read_token(token: Optional[str], now: Optional[float] = None) -> Optional[str]:
    """Return the customer id if the cookie is genuine, unexpired and for this MVP."""
    if not token or not _session_secret() or token.count(".") != 1:
        return None
    try:
        body, signature = token.split(".")
        payload = _unb64(body)
        if not hmac.compare_digest(_unb64(signature), _sign(payload)):
            return None
        data = json.loads(payload)
        if data.get("aid") != app_id() or int(data.get("exp", 0)) < (now or time.time()):
            return None
        customer = data.get("cus")
        return customer if isinstance(customer, str) and customer.startswith("cus_") else None
    except Exception:
        return None


def _plain(value: Any) -> Any:
    """Stripe responses as plain dicts and lists.

    Newer stripe-python versions return objects that are not dicts (no .get()),
    older ones return dict subclasses. Converting once keeps the rest of the
    module independent of the installed version.
    """
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return _plain(to_dict())
    return value


def _stripe_subscription_active(customer_id: str) -> bool:
    subs = _plain(stripe.Subscription.list(customer=customer_id, status="all", limit=20, api_key=_stripe_key()))
    for sub in subs.get("data", []):
        if sub.get("status") in ACTIVE_STATUSES and (sub.get("metadata") or {}).get("app_id") == app_id():
            return True
    return False


def subscription_active(customer_id: str, now: Optional[float] = None) -> bool:
    """Cached Stripe check. Fails closed unless a recent answer exists."""
    current = now or time.time()
    with _cache_lock:
        cached = _sub_cache.get(customer_id)
    if cached and current - cached[1] < (POSITIVE_TTL if cached[0] else NEGATIVE_TTL):
        return cached[0]
    try:
        active = _stripe_subscription_active(customer_id)
    except Exception as exc:
        log.warning("Stripe subscription check failed: %s", type(exc).__name__)
        return bool(cached and current - cached[1] < STALE_OK and cached[0])
    with _cache_lock:
        if len(_sub_cache) >= _CACHE_MAX:
            _sub_cache.clear()
        _sub_cache[customer_id] = (active, current)
    return active


def clear_subscription_cache() -> None:
    with _cache_lock:
        _sub_cache.clear()


@dataclass(frozen=True)
class Access:
    subscriber: bool = False
    customer_id: Optional[str] = None


def get_access(request: Request) -> Access:
    if not billing_enabled():
        return Access()
    customer = read_token(request.cookies.get(COOKIE_NAME))
    if customer and subscription_active(customer):
        return Access(True, customer)
    return Access()


# ---------------------------------------------------------------------------
# Free vs premium content (server-side)
# ---------------------------------------------------------------------------

_STUB_FIELDS = ("id", "title", "category")


def _locked_stub(item: Mapping[str, Any]) -> Dict[str, Any]:
    stub = {key: item[key] for key in _STUB_FIELDS if key in item}
    stub["locked"] = True
    return stub


def visitor_view(item: Mapping[str, Any], premium_fields: Iterable[str]) -> Dict[str, Any]:
    blocked = set(premium_fields) | {"tier"}
    return {key: value for key, value in item.items() if key not in blocked}


def item_for(item: Mapping[str, Any], premium_fields: Iterable[str], access: Access) -> Dict[str, Any]:
    """One item as the viewer is allowed to see it."""
    premium_fields = tuple(premium_fields)
    if access.subscriber:
        full = {key: value for key, value in item.items() if key != "tier"}
        full["locked"] = False
        return full
    if item.get("tier") == "premium":
        stub = _locked_stub(item)
        stub["locked_fields"] = sorted(set(premium_fields) & set(item))
        return stub
    view = visitor_view(item, premium_fields)
    view["locked"] = False
    view["locked_fields"] = sorted(set(premium_fields) & set(item))
    return view


def apply_access(
    items: Iterable[Mapping[str, Any]],
    premium_fields: Iterable[str],
    access: Access,
    free_limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """A list as the viewer may see it: visitors get a free preview, the rest is locked."""
    premium_fields = tuple(premium_fields)
    if access.subscriber:
        return [item_for(item, premium_fields, access) for item in items]
    limit = free_item_limit() if free_limit is None else free_limit
    shown = 0
    result = []
    for item in items:
        if item.get("tier") == "premium" or shown >= limit:
            result.append(_locked_stub(item))
        else:
            result.append(visitor_view(item, premium_fields) | {"locked": False})
            shown += 1
    return result


def find_item(
    items: Iterable[Mapping[str, Any]],
    item_id: str,
    premium_fields: Iterable[str],
    access: Access,
    free_limit: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """One item as the viewer may see it, consistent with apply_access.

    Items hidden by the free-preview limit stay locked when opened by direct URL.
    Returns None when there is no such item.
    """
    items = list(items)
    premium_fields = tuple(premium_fields)
    raw = next((item for item in items if item.get("id") == item_id), None)
    if raw is None:
        return None
    if access.subscriber:
        return item_for(raw, premium_fields, access)
    visible = {v.get("id") for v in apply_access(items, premium_fields, access, free_limit) if not v.get("locked")}
    if raw.get("id") not in visible:
        stub = _locked_stub(raw)
        stub["locked_fields"] = sorted(set(premium_fields) & set(raw))
        return stub
    return item_for(raw, premium_fields, access)


def safe_href(value: Any) -> str:
    """Only http(s) links may be rendered as hyperlinks."""
    text = str(value or "").strip()
    return text if re.match(r"^https?://[^\s\"'<>]+$", text) else ""


# ---------------------------------------------------------------------------
# Rate limiting, client address, public URL
# ---------------------------------------------------------------------------

class _Limiter:
    def __init__(self, limit: int = 10, window: int = 60):
        self.limit, self.window = limit, window
        self._hits: Dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            if len(self._hits) > 50000:
                self._hits.clear()
            hits = self._hits[key]
            while hits and now - hits[0] > self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                return False
            hits.append(now)
            return True

    def clear(self) -> None:
        with self._lock:
            self._hits.clear()


_limiter = _Limiter()


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


def public_base_url(request: Request) -> str:
    configured = _env("MVP_PUBLIC_URL")
    if re.match(r"^https?://[A-Za-z0-9.-]+(:\d+)?$", configured.rstrip("/")):
        return configured.rstrip("/")
    domain = _env("RAILWAY_PUBLIC_DOMAIN")
    if re.match(r"^[A-Za-z0-9.-]+$", domain):
        return f"https://{domain}"
    return str(request.base_url).rstrip("/")


def _is_https(request: Request) -> bool:
    return (
        request.url.scheme == "https"
        or request.headers.get("x-forwarded-proto", "").lower() == "https"
        or public_base_url(request).startswith("https://")
    )


# ---------------------------------------------------------------------------
# HTML shell
# ---------------------------------------------------------------------------

_CSS = (
    "*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;"
    "background:#0f172a;color:#e2e8f0;line-height:1.55}a{color:#38bdf8}"
    "header{display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between;"
    "padding:14px 24px;border-bottom:1px solid #1e293b}"
    "header .brand{font-weight:700;color:#fff;text-decoration:none}"
    "nav a{margin-left:16px;text-decoration:none;color:#94a3b8}nav a.active{color:#fff}"
    "main{max-width:980px;margin:0 auto;padding:28px 20px}"
    ".banner{background:#78350f;color:#fde68a;text-align:center;padding:8px 12px;font-size:14px}"
    ".hero{padding:36px 0 12px}.hero h1{font-size:clamp(28px,5vw,44px);margin:8px 0}"
    ".badge{display:inline-block;background:#164e63;color:#a5f3fc;border-radius:999px;padding:4px 12px;font-size:13px}"
    ".grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fill,minmax(250px,1fr))}"
    ".card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:18px}"
    ".card h3{margin:0 0 6px}.muted{color:#94a3b8}.small{font-size:14px}"
    ".btn{display:inline-block;background:#0ea5e9;color:#04202e;font-weight:700;border:0;border-radius:10px;"
    "padding:11px 20px;text-decoration:none;cursor:pointer;font-size:16px}"
    ".btn.secondary{background:#1e293b;color:#e2e8f0;border:1px solid #475569}"
    ".btn[disabled]{opacity:.5;cursor:not-allowed}"
    ".lock{color:#fbbf24}.cols{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}"
    ".price{font-size:40px;font-weight:800;margin:6px 0}ul.ticks{list-style:none;padding:0}"
    "ul.ticks li:before{content:'\\2713 ';color:#34d399}input,select{background:#0f172a;color:#e2e8f0;"
    "border:1px solid #475569;border-radius:8px;padding:9px;font-size:15px}"
    "footer{max-width:980px;margin:0 auto;padding:24px 20px;color:#64748b;font-size:13px}"
)

SAMPLE_BANNER = (
    '<div class="banner" role="note">Sample data: placeholder content for demonstration. '
    "Real data is coming soon.</div>"
)

_NAV = (("/", "Home"), ("/explore", "Explore"), ("/pricing", "Pricing"), ("/account", "Account"))


def _tracking_head() -> str:
    ga4 = _site["ga4_measurement_id"]
    if not ga4:
        return ""
    return (
        f'<script async src="https://www.googletagmanager.com/gtag/js?id={esc(ga4)}"></script>'
        "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
        f'gtag("js",new Date());gtag("config",{json.dumps(ga4)},{{"send_page_view":true}});</script>'
    )


def _tax_note() -> str:
    on = _env("MVP_STRIPE_AUTOMATIC_TAX").lower() in ("1", "true", "yes")
    return "Taxes may be added at checkout. " if on else ""


def page(title: str, body_html: str, *, active: str = "", description: str = "") -> str:
    """Wrap trusted HTML in the shared shell. Callers must escape dynamic text with esc()."""
    name = esc(_site["product_name"])
    nav = "".join(
        f'<a href="{href}"' + (' class="active"' if href == active else "") + f">{label}</a>"
        for href, label in _NAV
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{esc(title)} | {name}</title>"
        f'<meta name="description" content="{esc(description or _site["tagline"])}">'
        + _tracking_head()
        + "<style>" + _CSS + "</style></head><body>"
        + (SAMPLE_BANNER if _site["sample_data"] else "")
        + f'<header><a class="brand" href="/">{name}</a><nav>{nav}</nav></header>'
        + f"<main>{body_html}</main>"
        + f"<footer>{name}. Prices are per month. {_tax_note()}Cancel any time.</footer>"
        + "</body></html>"
    )


def install_security_headers(app) -> None:
    @app.middleware("http")
    async def _security_headers(request, call_next):
        response = await call_next(request)
        headers = response.headers
        headers.setdefault("X-Content-Type-Options", "nosniff")
        headers.setdefault("X-Frame-Options", "DENY")
        headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if "cache-control" not in headers:
            headers["Cache-Control"] = "private, no-cache"
        vary = headers.get("vary")
        headers["Vary"] = f"{vary}, Cookie" if vary and "cookie" not in vary.lower() else (vary or "Cookie")
        if request.headers.get("x-forwarded-proto", "").lower() == "https":
            headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        return response


# ---------------------------------------------------------------------------
# Pricing, checkout, account routes
# ---------------------------------------------------------------------------

router = APIRouter()

_SESSION_ID_RE = re.compile(r"^cs_[A-Za-z0-9_]{10,200}$")


class CheckoutRequest(BaseModel):
    country: Optional[str] = None


def _features(items: List[str]) -> str:
    return '<ul class="ticks">' + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>"


def pricing_html(request: Request, country: Optional[str] = None) -> str:
    code = detect_country(request, country)
    price = price_for(code)
    selected = code if code in COUNTRY_NAMES else OTHER_COUNTRY
    options = "".join(
        f'<option value="{c}"' + (" selected" if c == selected else "") + f">{esc(n)}</option>"
        for c, n in sorted(COUNTRY_NAMES.items(), key=lambda kv: kv[1])
    )
    enabled = billing_enabled()
    button = (
        '<button class="btn" id="subscribe">Subscribe</button>'
        if enabled
        else '<button class="btn" disabled>Subscriptions open soon</button>'
    )
    free = _site["free_features"] or ["Free preview of the content"]
    premium = _site["premium_features"] or ["Everything in the full library"]
    body = (
        '<div class="hero"><span class="badge">Simple pricing</span><h1>One plan. Fair prices.</h1>'
        f'<p class="muted">The price is set for your country so it stays fair wherever you live. '
        f"You are billed in {esc(price.currency.upper())}.</p></div>"
        '<label class="small muted" for="country">Your country</label> '
        f'<select id="country" onchange="location.search=\'?country=\'+this.value">{options}</select>'
        '<div class="cols" style="margin-top:20px">'
        f'<div class="card"><h3>Free</h3><div class="price">{esc(format_price(Price(price.country, price.currency, 0)))}</div>'
        + _features(free)
        + '<a class="btn secondary" href="/explore">Browse free</a></div>'
        f'<div class="card" style="border-color:#0ea5e9"><h3>Premium</h3>'
        f'<div class="price">{esc(format_price(price))}<span class="small muted"> / month</span></div>'
        + _features(premium)
        + button
        + '<p class="small muted" id="status" role="status"></p></div></div>'
        '<h2>Questions</h2><p class="small"><strong>Can I cancel?</strong> Yes, any time from your account page.</p>'
        '<p class="small"><strong>Why does the price differ by country?</strong> '
        "It is adjusted to local purchasing power and charged in the local currency.</p>"
        + (
            "<script>document.getElementById('subscribe').addEventListener('click',async function(e){"
            "e.target.disabled=true;var s=document.getElementById('status');s.textContent='Opening secure checkout...';"
            "try{var r=await fetch('/api/checkout',{method:'POST',headers:{'Content-Type':'application/json'},"
            "body:JSON.stringify({country:" + json.dumps(selected) + "})});var d=await r.json();"
            "if(d.checkout_url){window.location=d.checkout_url}else{s.textContent=d.error||'Checkout is unavailable.';"
            "e.target.disabled=false}}catch(x){s.textContent='Checkout is unavailable.';e.target.disabled=false}});</script>"
            if enabled
            else ""
        )
    )
    return page("Pricing", body, active="/pricing")


@router.get("/pricing", response_class=HTMLResponse)
def pricing_page(request: Request, country: Optional[str] = None):
    return HTMLResponse(pricing_html(request, country))


@router.get("/api/pricing")
def pricing_json(request: Request, country: Optional[str] = None):
    price = price_for(detect_country(request, country))
    return {"country": price.country, "currency": price.currency, "amount": price.amount,
            "display": format_price(price), "interval": "month"}


def _checkout_params(request: Request, price: Price) -> Dict[str, Any]:
    base = public_base_url(request)
    meta = {"build_id": build_id(), "app_id": app_id(), "pricing_country": price.country}
    price_data: Dict[str, Any] = {
        "currency": price.currency,
        "unit_amount": price.amount,
        "recurring": {"interval": "month"},
    }
    product = _env("STRIPE_PRODUCT_ID")
    if product.startswith("prod_"):
        price_data["product"] = product
    else:
        price_data["product_data"] = {"name": _site["product_name"][:80]}
    params: Dict[str, Any] = {
        "mode": "subscription",
        "line_items": [{"price_data": price_data, "quantity": 1}],
        "success_url": base + "/checkout/success?session_id={CHECKOUT_SESSION_ID}",
        "cancel_url": base + "/checkout/cancel",
        "metadata": meta,
        "subscription_data": {"metadata": meta},
        "allow_promotion_codes": False,
    }
    if _env("MVP_STRIPE_AUTOMATIC_TAX").lower() in ("1", "true", "yes"):
        params["automatic_tax"] = {"enabled": True}
    return params


@router.post("/api/checkout")
def create_checkout(request: Request, payload: Optional[CheckoutRequest] = None):
    if not _limiter.allow(f"checkout:{client_ip(request)}"):
        return JSONResponse({"error": "Too many requests. Please wait a minute."}, status_code=429)
    if not billing_enabled():
        return JSONResponse({"error": "Subscriptions are not open yet."}, status_code=503)
    price = price_for(detect_country(request, payload.country if payload else None))
    try:
        session = _plain(stripe.checkout.Session.create(api_key=_stripe_key(), **_checkout_params(request, price)))
        url = session.get("url")
    except Exception as exc:
        log.error("Checkout creation failed: %s", type(exc).__name__)
        return JSONResponse({"error": "Checkout is unavailable right now."}, status_code=502)
    if not url:
        return JSONResponse({"error": "Checkout is unavailable right now."}, status_code=502)
    return {"checkout_url": url}


def _plain_id(value: Any) -> Optional[str]:
    if isinstance(value, dict):
        value = value.get("id")
    return value if isinstance(value, str) and value.startswith("cus_") else None


def _verified_customer(session: Mapping[str, Any]) -> Optional[str]:
    """The customer id if this Checkout Session is a completed subscription for this MVP."""
    subscription = session.get("subscription")
    if not isinstance(subscription, dict):
        return None
    if (session.get("metadata") or {}).get("app_id") != app_id():
        return None
    if (subscription.get("metadata") or {}).get("app_id") != app_id():
        return None
    if session.get("mode") != "subscription" or session.get("status") != "complete":
        return None
    if session.get("payment_status") not in ("paid", "no_payment_required"):
        return None
    if subscription.get("status") not in ACTIVE_STATUSES:
        return None
    return _plain_id(session.get("customer"))


def _problem_page(title: str, message: str, status: int) -> HTMLResponse:
    body = (f"<h1>{esc(title)}</h1><p>{esc(message)}</p>"
            '<p><a class="btn secondary" href="/pricing">Back to pricing</a></p>')
    return HTMLResponse(page(title, body), status_code=status)


@router.get("/checkout/success")
def checkout_success(request: Request, session_id: str = ""):
    if not _limiter.allow(f"success:{client_ip(request)}"):
        return _problem_page("Please wait", "Too many attempts. Try again in a minute.", 429)
    if not billing_enabled() or not _SESSION_ID_RE.match(session_id):
        return _problem_page("We could not confirm your subscription",
                             "The confirmation link is not valid.", 400)
    try:
        session = _plain(stripe.checkout.Session.retrieve(session_id, expand=["subscription"], api_key=_stripe_key()))
    except Exception as exc:
        log.warning("Checkout verification failed: %s", type(exc).__name__)
        return _problem_page("We could not confirm your subscription",
                             "Please try again in a moment.", 502)
    customer = _verified_customer(session)
    if not customer:
        return _problem_page("We could not confirm your subscription",
                             "The payment is not complete yet. If you were charged, contact support.", 400)

    expected = (session.get("metadata") or {}).get("pricing_country")
    actual = ((session.get("customer_details") or {}).get("address") or {}).get("country")
    if expected and actual and expected not in (actual, OTHER_COUNTRY):
        log.warning("Pricing country %s differs from billing country %s", expected, actual)

    with _cache_lock:
        _sub_cache[customer] = (True, time.time())
    response = RedirectResponse("/account?welcome=1", status_code=303)
    response.set_cookie(COOKIE_NAME, issue_token(customer), max_age=COOKIE_MAX_AGE,
                        httponly=True, samesite="lax", secure=_is_https(request), path="/")
    return response


@router.get("/checkout/cancel", response_class=HTMLResponse)
def checkout_cancel():
    body = ('<h1>Checkout cancelled</h1><p>You have not been charged.</p>'
            '<p><a class="btn" href="/pricing">Back to pricing</a></p>')
    return HTMLResponse(page("Checkout cancelled", body))


_PORTAL_RE = re.compile(r"^https://billing\.stripe\.com/[A-Za-z0-9/_?=&.%-]{1,200}$")


def portal_login_url() -> str:
    """Stripe-hosted customer portal login page (no API permission needed)."""
    url = _env("MVP_STRIPE_PORTAL_LOGIN_URL")
    return url if _PORTAL_RE.match(url) else ""


@router.get("/account", response_class=HTMLResponse)
def account_page(request: Request, welcome: Optional[str] = None):
    access = get_access(request)
    if access.subscriber:
        greeting = "<p>Thank you for subscribing!</p>" if welcome else ""
        manage = portal_login_url()
        billing = (
            f'<a class="btn" href="{esc(manage)}" rel="noopener noreferrer">Manage billing</a> '
            if manage
            else '<p class="small muted">To manage or cancel your subscription, use the link in your Stripe receipt email.</p>'
        )
        body = (
            "<h1>Your account</h1>" + greeting +
            '<p><span class="badge">Premium active</span></p>'
            "<p>" + billing +
            '<form method="post" action="/account/logout" style="display:inline">'
            '<button class="btn secondary" type="submit">Sign out on this device</button></form></p>'
        )
    else:
        body = ("<h1>Your account</h1><p>You are on the free plan.</p>"
                '<p><a class="btn" href="/pricing">See premium</a></p>')
    return HTMLResponse(page("Account", body, active="/account"))


@router.post("/account/logout")
def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(COOKIE_NAME, path="/")
    return response
