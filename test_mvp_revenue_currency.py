"""MVP payments in local currencies must not corrupt the platform's revenue totals."""

import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", f"sqlite:///{os.path.join(tempfile.mkdtemp(), 'revenue.db')}")
os.environ.setdefault("SECRET_KEY", "test-secret-key-0123456789abcdef0123456789")

from sqlalchemy import create_engine, func  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

import models  # noqa: E402
from services import mvp_currency, stripe_service  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent / "templates" / "mvp" / "runtime"))
import mvp_runtime as rt  # noqa: E402


@pytest.fixture()
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'rev.db'}")
    models.Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def log(db, event_id, amount, currency, app_id="mvp_7", build_id=7, event_type="invoice.payment_succeeded"):
    data = {"customer": "cus_1", "amount_paid": amount, "currency": currency}
    if app_id:
        data["metadata"] = {"app_id": app_id, "build_id": str(build_id)}
    stripe_service._log_revenue_event(db, {"id": event_id, "created": 1_700_000_000}, event_type, data)
    return db.query(models.RevenueEvent).filter_by(stripe_event_id=event_id).one()


def test_rate_table_matches_the_one_shipped_in_the_mvp_runtime():
    assert mvp_currency.APPROX_GBP_PER_UNIT == rt.APPROX_GBP_PER_UNIT
    assert mvp_currency.ZERO_DECIMAL == rt.ZERO_DECIMAL


def test_every_runtime_price_converts_to_a_sensible_gbp_amount():
    for country, (currency, amount) in rt.COUNTRY_PRICES.items():
        pence = mvp_currency.to_gbp_minor(amount, currency)
        assert 35 <= pence <= 150, (country, currency, amount, pence)


@pytest.mark.parametrize(
    "amount,currency,expected",
    [(99, "gbp", 99), (129, "usd", 99), (4900, "inr", 45), (150, "jpy", 76), (1500, "krw", 81),
     (449, "brl", 62), (0, "inr", 0)],
)
def test_conversion_examples(amount, currency, expected):
    assert mvp_currency.to_gbp_minor(amount, currency) == expected


def test_unknown_currency_is_not_converted():
    assert mvp_currency.to_gbp_minor(500, "xyz") is None
    assert mvp_currency.to_gbp_minor(500, "") is None


def test_indian_mvp_payment_is_not_counted_as_49_pounds(db):
    event = log(db, "evt_inr", 4900, "inr")
    assert event.currency == "gbp" and event.amount_cents == 45
    assert event.app_id == "mvp_7" and event.build_id == 7
    assert event.metadata_json == {"original_amount_minor": 4900, "original_currency": "inr",
                                   "approximate_gbp_conversion": True}


def test_zero_decimal_currency_is_not_inflated(db):
    event = log(db, "evt_jpy", 150, "jpy")
    assert event.amount_cents == 76 and event.currency == "gbp"


def test_gbp_mvp_payment_is_unchanged(db):
    event = log(db, "evt_gbp", 99, "gbp")
    assert (event.amount_cents, event.currency, event.metadata_json) == (99, "gbp", None)


def test_unknown_currency_mvp_payment_is_kept_as_received(db):
    event = log(db, "evt_xyz", 500, "xyz")
    assert (event.amount_cents, event.currency, event.metadata_json) == (500, "xyz", None)


def test_platform_own_revenue_is_not_converted(db):
    event = log(db, "evt_platform", 999, "usd", app_id=None)
    assert event.app_id == "causal_affect"
    assert (event.amount_cents, event.currency, event.metadata_json) == (999, "usd", None)


def test_mixed_currency_mvp_revenue_sums_sensibly(db):
    log(db, "e1", 99, "gbp")
    log(db, "e2", 4900, "inr")
    log(db, "e3", 129, "usd")
    log(db, "e4", 150, "jpy")
    total = db.query(func.coalesce(func.sum(models.RevenueEvent.amount_cents), 0)).scalar()
    assert total == 99 + 45 + 99 + 76  # about £3.19, not the 5,278 "pounds" raw minor units would give


def test_duplicate_stripe_events_are_still_ignored(db):
    log(db, "evt_dup", 4900, "inr")
    stripe_service._log_revenue_event(
        db, {"id": "evt_dup", "created": 1_700_000_000}, "invoice.payment_succeeded",
        {"customer": "cus_1", "amount_paid": 4900, "currency": "inr", "metadata": {"app_id": "mvp_7", "build_id": "7"}})
    assert db.query(models.RevenueEvent).filter_by(stripe_event_id="evt_dup").count() == 1
