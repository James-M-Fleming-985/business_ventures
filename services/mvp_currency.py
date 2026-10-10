"""Approximate GBP conversion for MVP revenue.

MVPs charge in local currencies (see templates/mvp/runtime/mvp_runtime.py), but the
platform's revenue totals add up ``amount_cents`` without looking at the currency.
So payments attributed to an MVP are recorded in GBP pence and the original amount
and currency are kept in ``metadata_json``.

The rates are approximate and exist only so MVPs can be compared with each other.
They are not for accounting: Stripe remains the source of truth. A test keeps this
table identical to the one shipped inside the MVP runtime.
"""

from typing import Optional

ZERO_DECIMAL = frozenset({"jpy", "krw"})

APPROX_GBP_PER_UNIT = {
    "gbp": 1.0, "usd": 0.77, "cad": 0.555, "aud": 0.50, "nzd": 0.455, "eur": 0.855,
    "chf": 0.935, "sek": 0.08, "nok": 0.074, "dkk": 0.115, "sgd": 0.58, "aed": 0.21,
    "ils": 0.22, "hkd": 0.098, "pln": 0.205, "czk": 0.0355, "jpy": 0.0051,
    "krw": 0.00054, "brl": 0.139, "mxn": 0.0417, "myr": 0.178, "thb": 0.0227,
    "zar": 0.043, "ron": 0.17, "inr": 0.0091, "php": 0.0132,
}


def to_gbp_minor(amount_minor: int, currency: str) -> Optional[int]:
    """Convert an amount in a currency's minor units to GBP pence, or None if the currency is unknown."""
    rate = APPROX_GBP_PER_UNIT.get((currency or "").lower())
    if rate is None:
        return None
    major = float(amount_minor) if (currency or "").lower() in ZERO_DECIMAL else amount_minor / 100.0
    return max(0, round(major * rate * 100))
