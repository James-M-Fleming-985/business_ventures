"""Public MVP beacon: signed tokens, rate limiting and keyed visitor hashes."""

import os
import tempfile

os.environ.setdefault("DATABASE_URL", f"sqlite:///{os.path.join(tempfile.mkdtemp(), 'beacon.db')}")
os.environ.setdefault("SECRET_KEY", "test-secret-key-0123456789abcdef0123456789")

import hashlib
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import models
from database import get_db
from routers import dashboard_real
from services import beacon_security


@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.delenv("BEACON_ALLOW_UNSIGNED", raising=False)
    # Pin the token cutoff so the fixture's build is unambiguously "new".
    monkeypatch.setenv("BEACON_TOKEN_REQUIRED_FROM", "2026-06-01T00:00:00")
    engine = create_engine(f"sqlite:///{tmp_path / 'beacon.db'}")
    models.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    db = Session()
    db.add(models.MVPBuild(
        recommendation_id=1, complexity="LOW", status="LIVE",
        created_at=datetime(2026, 9, 1),  # after cutoff -> token required
    ))
    db.commit()
    build_id = db.query(models.MVPBuild).first().id
    db.close()

    app = FastAPI()
    app.include_router(dashboard_real.public_router)

    def _get_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _get_db
    beacon_security.beacon_limiter.clear()
    yield TestClient(app), Session, build_id
    beacon_security.beacon_limiter.clear()


def _add_build(Session, created_at):
    db = Session()
    try:
        build = models.MVPBuild(
            recommendation_id=1, complexity="LOW", status="LIVE", created_at=created_at,
        )
        db.add(build)
        db.commit()
        return build.id
    finally:
        db.close()


def _views(Session):
    db = Session()
    try:
        return db.query(models.MvpPageView).count()
    finally:
        db.close()


def test_token_is_bound_to_the_build_id():
    token = beacon_security.sign_build_id(5)
    assert beacon_security.verify_token(5, token)
    assert not beacon_security.verify_token(6, token)
    assert not beacon_security.verify_token(5, "")
    assert not beacon_security.verify_token(5, None)
    assert not beacon_security.verify_token(5, "0" * 32)


def test_visitor_hash_is_keyed_not_a_plain_sha256():
    plain = hashlib.sha256(b"1.2.3.4:agent").hexdigest()
    hashed = beacon_security.hash_visitor("1.2.3.4", "agent")
    assert hashed != plain
    assert hashed == beacon_security.hash_visitor("1.2.3.4", "agent")
    assert hashed != beacon_security.hash_visitor("1.2.3.5", "agent")


def test_beacon_without_token_is_silently_ignored(env):
    client, Session, build_id = env
    r = client.post(f"/api/dashboard/mvp-beacon/{build_id}")
    assert r.status_code == 204
    assert _views(Session) == 0


def test_beacon_with_wrong_token_is_silently_ignored(env):
    client, Session, build_id = env
    r = client.post(f"/api/dashboard/mvp-beacon/{build_id}?t={'0' * 32}")
    assert r.status_code == 204
    assert _views(Session) == 0


def test_beacon_with_valid_token_is_recorded(env):
    client, Session, build_id = env
    token = beacon_security.sign_build_id(build_id)
    r = client.post(f"/api/dashboard/mvp-beacon/{build_id}?t={token}", json={"r": "https://example.com"})
    assert r.status_code == 204
    assert _views(Session) == 1


def test_token_for_one_build_does_not_work_for_another(env):
    client, Session, build_id = env
    r = client.post(f"/api/dashboard/mvp-beacon/{build_id}?t={beacon_security.sign_build_id(build_id + 1)}")
    assert r.status_code == 204
    assert _views(Session) == 0


def test_beacon_is_rate_limited_per_visitor_and_build(env):
    client, Session, build_id = env
    token = beacon_security.sign_build_id(build_id)
    for _ in range(beacon_security.beacon_limiter.limit + 10):
        assert client.post(f"/api/dashboard/mvp-beacon/{build_id}?t={token}").status_code == 204
    assert _views(Session) == beacon_security.beacon_limiter.limit


def test_existing_mvp_built_before_cutoff_counts_without_a_token(env):
    """Engagement must keep working for MVPs deployed before signed beacons."""
    client, Session, _ = env
    legacy_id = _add_build(Session, datetime(2026, 4, 1))  # before the pinned cutoff
    r = client.post(f"/api/dashboard/mvp-beacon/{legacy_id}", json={"r": "https://example.com"})
    assert r.status_code == 204
    assert _views(Session) == 1


def test_legacy_unsigned_beacons_work_only_when_explicitly_allowed(env, monkeypatch):
    client, Session, build_id = env
    monkeypatch.setenv("BEACON_ALLOW_UNSIGNED", "true")
    client.post(f"/api/dashboard/mvp-beacon/{build_id}")
    assert _views(Session) == 1


def test_deployed_mvp_pages_carry_the_signed_beacon(tmp_path, monkeypatch):
    import importlib
    import sys
    from pathlib import Path
    from services.ai_code_generator_orchestrator import AICodeGeneratorOrchestrator

    src = tmp_path / "src"
    src.mkdir()
    (src / "__init__.py").write_text("")
    (src / "layer_mvp_0007.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/api/x')\ndef x():\n    return {'x': 1}\n"
    )
    orchestrator = AICodeGeneratorOrchestrator({"provider": "anthropic", "output_base_path": str(tmp_path)})
    orchestrator.ai_provider = MagicMock()
    orchestrator.ai_provider.generate_code.side_effect = RuntimeError("no AI")
    files = {f["path"]: f["content"] for f in orchestrator._generate_deployment_files(
        Path(tmp_path), spec={"feature_name": "x"}, build_id=7)}
    for path, content in files.items():
        (tmp_path / path).write_text(content)
    monkeypatch.syspath_prepend(str(tmp_path))
    names = ("main", "mvp_runtime", "src", "src.layer_mvp_0007")
    saved = {name: sys.modules.get(name) for name in names}
    for name in names:
        sys.modules.pop(name, None)
    try:
        client = TestClient(importlib.import_module("main").app)
        pages = [client.get(path).text for path in ("/", "/explore", "/pricing", "/account")]
        api = client.get("/api/x")
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    for page in pages:
        assert f"/api/dashboard/mvp-beacon/7?t={beacon_security.sign_build_id(7)}" in page
        assert page.count(beacon_security.BEACON_MARKER) == 1  # exactly one beacon, never doubled
        assert '"click"' in page
    # the AI-written module's own routes are deliberately not served (they would bypass the paywall)
    assert api.status_code == 404


def test_clicks_are_recorded_separately_from_views(env):
    client, Session, build_id = env
    url = f"/api/dashboard/mvp-beacon/{build_id}?t={beacon_security.sign_build_id(build_id)}"
    client.post(url, content='{"e":"view","r":""}', headers={"content-type": "text/plain"})
    client.post(url, content='{"e":"click"}', headers={"content-type": "text/plain"})
    client.post(url, content='{"e":"click"}', headers={"content-type": "text/plain"})
    client.post(url, json={"r": "x"})  # older MVPs send no event type

    db = Session()
    try:
        kinds = sorted(v.event_type for v in db.query(models.MvpPageView).all())
    finally:
        db.close()
    assert kinds == ["click", "click", "view", "view"]


def test_portfolio_engagement_shows_visitors_views_and_clicks(env):
    import asyncio

    client, Session, build_id = env
    url = f"/api/dashboard/mvp-beacon/{build_id}?t={beacon_security.sign_build_id(build_id)}"
    client.post(url, content='{"e":"view"}', headers={"user-agent": "browser-a"})
    client.post(url, content='{"e":"click"}', headers={"user-agent": "browser-a"})
    client.post(url, content='{"e":"click"}', headers={"user-agent": "browser-a"})
    client.post(url, content='{"e":"view"}', headers={"user-agent": "browser-b"})

    db = Session()
    try:
        result = asyncio.run(dashboard_real.list_builds_portfolio(db=db))
    finally:
        db.close()
    row = next(b for b in result["builds"] if b["id"] == build_id)
    assert (row["engagement"], row["page_views"], row["clicks"]) == (2, 2, 2)
