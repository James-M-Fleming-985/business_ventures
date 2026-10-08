"""Auth hardening: 2FA, registration gate, throttling and admin-only APIs."""

import os
import tempfile

_DB_FILE = os.path.join(tempfile.mkdtemp(), "auth_test.db")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_DB_FILE}")
os.environ.setdefault("SECRET_KEY", "test-secret-key-0123456789abcdef0123456789")

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import models
from database import get_db
from routers import admin, auth, dashboard_real
from services import mfa
from services.auth import create_user

PASSWORD = "correct-horse-9"


@pytest.fixture()
def env(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    models.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    app = FastAPI()
    for router in (auth.router, admin.router, dashboard_real.router, dashboard_real.public_router):
        app.include_router(router)

    def _get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    mfa.login_throttle.clear()
    os.environ.pop("ALLOW_REGISTRATION", None)
    yield TestClient(app), Session
    mfa.login_throttle.clear()


def _make_user(Session, email, role=None):
    db = Session()
    user = create_user(db, email, PASSWORD)
    if role:
        user.role = role
        db.commit()
    db.close()


def _login(client, email="owner@example.com", **extra):
    client.cookies.clear()
    return client.post("/api/auth/login", data={"email": email, "password": PASSWORD, **extra})


# --- TOTP primitives -------------------------------------------------------

def test_hotp_matches_rfc4226_vectors():
    import base64
    secret = base64.b32encode(b"12345678901234567890").decode()
    assert [mfa._hotp(secret, i) for i in range(3)] == ["755224", "287082", "359152"]


def test_totp_matches_rfc6238_vector():
    import base64
    secret = base64.b32encode(b"12345678901234567890").decode()
    assert mfa._hotp(secret, 59 // 30, digits=8) == "94287082"


def test_verify_totp_rejects_replay_and_wrong_codes():
    secret = mfa.generate_secret()
    step = mfa.current_step()
    code = mfa.totp_code(secret, step)
    assert mfa.verify_totp(secret, code) == step
    assert mfa.verify_totp(secret, code, last_step=step) is None
    assert mfa.verify_totp(secret, "000000" if code != "000000" else "111111") is None
    assert mfa.verify_totp(secret, "abc") is None


# --- login / registration --------------------------------------------------

def test_login_works_and_session_cookie_authenticates(env):
    client, Session = env
    _make_user(Session, "owner@example.com")
    assert _login(client).status_code == 200
    assert client.get("/api/auth/me").status_code == 200


def test_wrong_password_is_rejected(env):
    client, Session = env
    _make_user(Session, "owner@example.com")
    client.cookies.clear()
    r = client.post("/api/auth/login", data={"email": "owner@example.com", "password": "nope-nope-nope"})
    assert r.status_code == 401
    assert client.get("/api/auth/me").status_code == 401


def test_registration_closed_once_a_user_exists(env):
    client, Session = env
    first = client.post("/api/auth/register", data={"email": "owner@example.com", "password": PASSWORD})
    assert first.status_code == 200
    client.cookies.clear()
    second = client.post("/api/auth/register", data={"email": "other@example.com", "password": PASSWORD})
    assert second.status_code == 403


def test_registration_can_be_reopened_with_flag(env, monkeypatch):
    client, Session = env
    _make_user(Session, "owner@example.com")
    monkeypatch.setenv("ALLOW_REGISTRATION", "true")
    r = client.post("/api/auth/register", data={"email": "other@example.com", "password": PASSWORD})
    assert r.status_code == 200


def test_login_is_throttled_after_repeated_failures(env):
    client, Session = env
    _make_user(Session, "owner@example.com")
    for _ in range(5):
        r = client.post("/api/auth/login", data={"email": "owner@example.com", "password": "bad-bad-bad"})
        assert r.status_code == 401
    assert client.post("/api/auth/login", data={"email": "owner@example.com", "password": "bad-bad-bad"}).status_code == 429
    assert _login(client).status_code == 429


# --- admin-only gating -----------------------------------------------------

PROTECTED = [
    ("post", "/api/dashboard/exploitation/build", {"json": {"recommendation_id": 1}}),
    ("get", "/api/dashboard/exploitation/builds", {}),
    ("get", "/api/dashboard/exploitation/stripe/healthcheck", {}),
    ("get", "/api/admin/env-check", {}),
]


@pytest.mark.parametrize("method,path,kwargs", PROTECTED)
def test_protected_routes_reject_anonymous(env, method, path, kwargs):
    client, _ = env
    client.cookies.clear()
    assert getattr(client, method)(path, **kwargs).status_code == 401


@pytest.mark.parametrize("method,path,kwargs", PROTECTED)
def test_protected_routes_reject_non_admin(env, method, path, kwargs):
    client, Session = env
    _make_user(Session, "owner@example.com")
    _make_user(Session, "free@example.com")
    assert _login(client, "free@example.com").status_code == 200
    assert getattr(client, method)(path, **kwargs).status_code == 403


def test_protected_routes_allow_admin(env):
    client, Session = env
    _make_user(Session, "owner@example.com")
    assert _login(client).status_code == 200
    assert client.get("/api/admin/env-check").status_code == 200
    # authenticated, so it reaches the handler and fails on the missing recommendation
    assert client.post("/api/dashboard/exploitation/build", json={"recommendation_id": 999}).status_code == 404


def test_mvp_beacon_stays_public(env):
    client, _ = env
    client.cookies.clear()
    assert client.post("/api/dashboard/mvp-beacon/12345").status_code == 204


# --- two-factor lifecycle --------------------------------------------------

def _enroll(client):
    secret = client.post("/api/auth/2fa/setup").json()["secret"]
    step = mfa.current_step()
    r = client.post("/api/auth/2fa/enable", data={"code": mfa.totp_code(secret, step)})
    assert r.status_code == 200, r.text
    return secret, step, r.json()["recovery_codes"]


def test_two_factor_login_flow(env):
    client, Session = env
    _make_user(Session, "owner@example.com")
    assert _login(client).status_code == 200
    secret, enrolled_step, recovery = _enroll(client)
    assert len(recovery) == mfa.RECOVERY_CODE_COUNT

    no_code = _login(client)
    assert no_code.status_code == 401 and no_code.json()["mfa_required"] is True
    assert client.get("/api/auth/me").status_code == 401

    assert _login(client, totp_code="000000").status_code == 401

    next_code = mfa.totp_code(secret, enrolled_step + 1)
    assert _login(client, totp_code=next_code).status_code == 200
    assert client.get("/api/auth/me").status_code == 200

    # same code cannot be reused
    assert _login(client, totp_code=next_code).status_code == 401


def test_recovery_code_works_once(env):
    client, Session = env
    _make_user(Session, "owner@example.com")
    _login(client)
    _, _, recovery = _enroll(client)

    assert _login(client, totp_code=recovery[0]).status_code == 200
    assert _login(client, totp_code=recovery[0]).status_code == 401
    assert _login(client, totp_code=recovery[1]).status_code == 200


def test_enable_requires_valid_code_and_disable_requires_credentials(env):
    client, Session = env
    _make_user(Session, "owner@example.com")
    _login(client)
    client.post("/api/auth/2fa/setup")
    assert client.post("/api/auth/2fa/enable", data={"code": "000000"}).status_code == 400

    secret, enrolled_step, recovery = _enroll(client)
    bad = client.post("/api/auth/2fa/disable", data={"password": "wrong-wrong", "code": recovery[0]})
    assert bad.status_code == 401
    ok = client.post("/api/auth/2fa/disable", data={"password": PASSWORD, "code": recovery[0]})
    assert ok.status_code == 200
    assert _login(client).status_code == 200


# --- migration -------------------------------------------------------------

def test_totp_migration_upgrades_old_users_table_and_is_idempotent(tmp_path):
    from sqlalchemy import inspect, text
    from migrations.add_totp_columns import TOTP_COLUMNS, upgrade

    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR(255))"))
        conn.execute(text("INSERT INTO users (email) VALUES ('owner@example.com')"))

    assert set(upgrade(engine)) == set(TOTP_COLUMNS)
    assert upgrade(engine) == []
    assert set(TOTP_COLUMNS) <= {c["name"] for c in inspect(engine).get_columns("users")}

    with engine.connect() as conn:
        row = conn.execute(text("SELECT totp_enabled, totp_last_step FROM users")).one()
    assert not row[0] and row[1] == 0


# --- logout ----------------------------------------------------------------

def test_logout_page_clears_session_cookies():
    import main
    client = TestClient(main.app, follow_redirects=False)
    r = client.get("/logout", cookies={"access_token": "x", "refresh_token": "y"})
    cleared = " ".join(v for k, v in r.headers.multi_items() if k == "set-cookie")
    assert r.status_code == 307
    assert "access_token" in cleared and "refresh_token" in cleared
