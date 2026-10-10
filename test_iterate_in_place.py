"""Iterations update the existing product in place: same repo, Railway service, address and subscribers."""

import importlib
import os
import tempfile

os.environ.setdefault("DATABASE_URL", f"sqlite:///{os.path.join(tempfile.mkdtemp(), 'iterate.db')}")
os.environ.setdefault("SECRET_KEY", "test-secret-key-0123456789abcdef0123456789")

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

import database  # noqa: E402
import models  # noqa: E402
from routers import dashboard_real  # noqa: E402
from services import mvp_product, mvp_site  # noqa: E402

LIVE_SITE = {
    "name": "Crude Signals Weekly",
    "tagline": "Plain-English oil price briefings",
    "why_now": "Oil interest is climbing",
    "free_features": ["Weekly headline"],
    "premium_features": ["Full briefing"],
    "premium_fields": ["details"],
    "field_labels": {"details": "Full details"},
    "items": [
        {"id": f"brief-{n}", "title": f"Sample briefing {n}", "category": "Briefings",
         "summary": f"Summary {n}", "tier": "free", "details": f"DETAIL-{n}"}
        for n in range(1, 6)
    ],
    "sample_data": True,
    "ga4_measurement_id": "",
}


# --- fakes -----------------------------------------------------------------------

class FakeGitHub:
    calls = []

    def __init__(self):
        self.enabled = True

    @staticmethod
    def slugify(name, max_len=60):
        return name.lower().replace(" ", "-")[:max_len]

    def create_repository(self, name, description=""):
        FakeGitHub.calls.append(("create_repository", name))
        return {"full_name": f"owner/{name}", "html_url": f"https://github.com/owner/{name}",
                "clone_url": "", "default_branch": "main"}

    def push_files(self, repo_name, files, commit_message="", replace=False):
        FakeGitHub.calls.append(("push_files", repo_name, replace, sorted(path for path, _ in files)))
        return "abc123"


class FakeRailway:
    calls = []

    def __init__(self):
        self.enabled = True

    def create_project(self, name):
        FakeRailway.calls.append(("create_project", name))
        return {"id": f"proj-{name}"}

    def create_service(self, project_id, name):
        FakeRailway.calls.append(("create_service", project_id))
        return {"id": f"svc-{name}"}

    def get_default_environment(self, project_id):
        FakeRailway.calls.append(("get_default_environment", project_id))
        return f"env-{project_id}"

    def generate_domain(self, service_id, env_id):
        FakeRailway.calls.append(("generate_domain", service_id))
        return f"https://{service_id}.up.railway.app"

    def upsert_variables(self, project_id, env_id, service_id, variables):
        FakeRailway.calls.append(("upsert_variables", service_id, dict(variables)))
        return len(variables)

    def connect_repo(self, service_id, repo_full_name, branch="main"):
        FakeRailway.calls.append(("connect_repo", service_id, repo_full_name))


class FakeS3:
    def __init__(self, *a, **k):
        pass


class FakeBuilder:
    """Stands in for the AI pipeline: marks the build LIVE and stores a rendered site."""

    def __init__(self, s3):
        pass

    def build_mvp(self, requirement, complexity, build_id, db_session, recommendation_meta=None, iteration_meta=None):
        spec = {"feature_name": "x", "_meta": recommendation_meta or {}}
        if iteration_meta:
            spec["_iteration_meta"] = iteration_meta
        FakeBuilder.last_spec = spec
        main_py = mvp_site.render_main(mvp_site.keep_identity(mvp_site.default_site(spec, build_id), spec))
        db_session.add(models.MVPBuildFile(build_id=build_id, file_path="main.py", s3_key=f"mvp/{build_id}/main.py", content=main_py))
        build = db_session.query(models.MVPBuild).get(build_id)
        build.status = "LIVE"
        db_session.commit()


@pytest.fixture()
def env(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'it.db'}")
    models.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    monkeypatch.setattr(database, "SessionLocal", Session)
    # Patch the modules _run_build will actually import (sys.modules), not a stale
    # package attribute another test may have left behind.
    for module_name, attr, fake in (
        ("services.github_service", "GitHubService", FakeGitHub),
        ("services.railway_service", "RailwayService", FakeRailway),
        ("services.s3_service", "S3Service", FakeS3),
        ("services.mvp_builder_service", "MVPBuilderService", FakeBuilder),
    ):
        monkeypatch.setattr(importlib.import_module(module_name), attr, fake)
    monkeypatch.setenv("MVP_STRIPE_SECRET_KEY", "rk_test_abc")
    FakeGitHub.calls, FakeRailway.calls = [], []

    db = Session()
    rec = models.ExploitationRecommendation(
        signal_name="wiki_oil", signal_display_name="Oil Price", target_name="t",
        target_display_name="Petrol", action_type="BUILD", status="NEW",
    )
    db.add(rec)
    db.commit()
    rec_id = rec.id
    db.close()
    return Session, rec_id


def add_build(Session, rec_id, **fields):
    db = Session()
    build = models.MVPBuild(recommendation_id=rec_id, complexity="LOW", status=fields.pop("status", "QUEUED"), **fields)
    db.add(build)
    db.commit()
    build_id = build.id
    db.close()
    return build_id


def publish_parent(Session, rec_id, site=LIVE_SITE, **overrides):
    fields = dict(
        status="LIVE",
        github_url="https://github.com/owner/mvp-45-oil",
        railway_project_id="proj-45", railway_service_id="svc-45",
        railway_url="https://mvp-45.up.railway.app",
    )
    fields.update(overrides)
    parent_id = add_build(Session, rec_id, **fields)
    if site is not None:
        db = Session()
        db.add(models.MVPBuildFile(build_id=parent_id, file_path="main.py", s3_key=f"mvp/{parent_id}/main.py", content=mvp_site.render_main(site)))
        db.commit()
        db.close()
    return parent_id


def get(Session, model, **filters):
    db = Session()
    try:
        return db.query(model).filter_by(**filters).all()
    finally:
        db.close()


# --- the build pipeline --------------------------------------------------------

def test_first_build_creates_a_new_product(env):
    Session, rec_id = env
    build_id = add_build(Session, rec_id)
    dashboard_real._run_build(build_id, rec_id, "LOW")

    assert ("create_repository", f"mvp-{build_id}-oil-price") in FakeGitHub.calls
    assert ("push_files", f"mvp-{build_id}-oil-price", False, ["main.py"]) in FakeGitHub.calls
    names = [c[0] for c in FakeRailway.calls]
    assert "create_project" in names and "create_service" in names and "connect_repo" in names
    env_vars = next(c[2] for c in FakeRailway.calls if c[0] == "upsert_variables")
    assert env_vars["MVP_APP_ID"] == f"mvp_{build_id}" and len(env_vars["MVP_SESSION_SECRET"]) >= 48
    assert env_vars["STRIPE_SECRET_KEY"] == "rk_test_abc"


def test_iteration_updates_the_existing_site_in_place(env):
    Session, rec_id = env
    parent_id = publish_parent(Session, rec_id)
    child_id = add_build(Session, rec_id, parent_build_id=parent_id, iteration_number=2)

    dashboard_real._run_build(child_id, rec_id, "LOW", parent_id)

    # same repo, one new commit replacing the files; no new repo
    assert not any(c[0] == "create_repository" for c in FakeGitHub.calls)
    assert FakeGitHub.calls == [("push_files", "mvp-45-oil", True, ["main.py"])]
    # same Railway service; nothing created or reconnected
    names = [c[0] for c in FakeRailway.calls]
    assert not {"create_project", "create_service", "generate_domain", "connect_repo"} & set(names)
    upserts = [c for c in FakeRailway.calls if c[0] == "upsert_variables"]
    assert len(upserts) == 1 and upserts[0][1] == "svc-45"
    # identity kept: the session secret and app id are never touched, so subscribers stay signed in
    assert set(upserts[0][2]) <= {"MVP_BUILD_ID", "STRIPE_SECRET_KEY", "STRIPE_PRODUCT_ID",
                                  "MVP_STRIPE_PORTAL_LOGIN_URL", "MVP_STRIPE_AUTOMATIC_TAX"}
    assert upserts[0][2]["MVP_BUILD_ID"] == str(child_id)
    assert not set(upserts[0][2]) & {"MVP_SESSION_SECRET", "MVP_APP_ID", "MVP_PUBLIC_URL"}

    child = get(Session, models.MVPBuild, id=child_id)[0]
    assert child.github_url == "https://github.com/owner/mvp-45-oil"
    assert (child.railway_project_id, child.railway_service_id) == ("proj-45", "svc-45")
    assert child.railway_url == "https://mvp-45.up.railway.app"
    assert any(step["step"] == "RAILWAY_UPDATED_IN_PLACE" for step in child.build_steps)
    deployment = get(Session, models.ProductDeployment, build_id=child_id)[0]
    assert deployment.app_id == f"mvp_{parent_id}"


def test_iteration_improves_the_live_content_and_keeps_its_name(env):
    Session, rec_id = env
    parent_id = publish_parent(Session, rec_id)
    child_id = add_build(Session, rec_id, parent_build_id=parent_id, iteration_number=2)

    dashboard_real._run_build(child_id, rec_id, "LOW", parent_id)

    assert FakeBuilder.last_spec["_iteration_meta"]["parent_site"]["name"] == "Crude Signals Weekly"
    main_py = get(Session, models.MVPBuildFile, build_id=child_id, file_path="main.py")[0].content
    site = mvp_product.extract_site(main_py)
    assert site["name"] == "Crude Signals Weekly"
    # with no AI available, the live content is kept rather than replaced by placeholders
    assert [i["id"] for i in site["items"]] == [f"brief-{n}" for n in range(1, 6)]


def test_iteration_of_an_iteration_still_targets_the_original_product(env):
    Session, rec_id = env
    root_id = publish_parent(Session, rec_id)
    middle_id = publish_parent(Session, rec_id, parent_build_id=root_id, iteration_number=2)
    leaf_id = add_build(Session, rec_id, parent_build_id=middle_id, iteration_number=3)

    dashboard_real._run_build(leaf_id, rec_id, "LOW", middle_id)

    assert get(Session, models.ProductDeployment, build_id=leaf_id)[0].app_id == f"mvp_{root_id}"
    assert FakeGitHub.calls == [("push_files", "mvp-45-oil", True, ["main.py"])]


def test_iterating_a_failed_iteration_updates_the_last_published_site(env):
    Session, rec_id = env
    root_id = publish_parent(Session, rec_id)
    failed_id = add_build(Session, rec_id, status="FAILED", parent_build_id=root_id, iteration_number=2)
    leaf_id = add_build(Session, rec_id, parent_build_id=failed_id, iteration_number=3)

    dashboard_real._run_build(leaf_id, rec_id, "LOW", failed_id)

    leaf = get(Session, models.MVPBuild, id=leaf_id)[0]
    assert leaf.railway_service_id == "svc-45" and leaf.railway_url == "https://mvp-45.up.railway.app"
    assert FakeBuilder.last_spec["_iteration_meta"]["parent_site"]["name"] == "Crude Signals Weekly"


def test_iteration_of_a_product_never_deployed_to_railway_creates_its_service(env):
    Session, rec_id = env
    parent_id = publish_parent(Session, rec_id, railway_project_id=None, railway_service_id=None,
                               railway_url="https://github.com/owner/mvp-45-oil")
    child_id = add_build(Session, rec_id, parent_build_id=parent_id, iteration_number=2)

    dashboard_real._run_build(child_id, rec_id, "LOW", parent_id)

    assert FakeGitHub.calls[0] == ("push_files", "mvp-45-oil", True, ["main.py"])
    assert ("connect_repo", f"svc-mvp-{child_id}", "owner/mvp-45-oil") in FakeRailway.calls
    env_vars = next(c[2] for c in FakeRailway.calls if c[0] == "upsert_variables")
    assert env_vars["MVP_APP_ID"] == f"mvp_{parent_id}"


def test_new_product_env_scan_never_overwrites_protected_variables(env):
    Session, rec_id = env
    build_id = add_build(Session, rec_id)
    db = Session()
    db.add(models.MVPBuildFile(build_id=build_id, file_path="src/x.py", s3_key="k",
                               content='os.getenv("MVP_SESSION_SECRET"); os.getenv("OTHER_KEY")'))
    db.commit()
    db.close()
    dashboard_real._run_build(build_id, rec_id, "LOW")
    env_vars = next(c[2] for c in FakeRailway.calls if c[0] == "upsert_variables")
    assert env_vars["MVP_SESSION_SECRET"] != "CONFIGURE_ME" and env_vars["OTHER_KEY"] == "CONFIGURE_ME"


# --- helpers ----------------------------------------------------------------------

def test_parse_github_repo():
    assert mvp_product.parse_github_repo("https://github.com/owner/mvp-45-oil") == {
        "owner": "owner", "name": "mvp-45-oil", "full_name": "owner/mvp-45-oil"}
    assert mvp_product.parse_github_repo("https://github.com/owner/repo.git")["name"] == "repo"
    for bad in (None, "", "https://evil.com/owner/repo", "https://github.com/owner", "javascript:x"):
        assert mvp_product.parse_github_repo(bad) is None


def test_extract_site_reads_literals_and_never_executes_code():
    assert mvp_product.extract_site(mvp_site.render_main(LIVE_SITE))["name"] == "Crude Signals Weekly"
    assert mvp_product.extract_site("SITE = __import__('os').system('x')") is None
    assert mvp_product.extract_site("not python (") is None
    assert mvp_product.extract_site("OTHER = {}") is None
    assert mvp_product.extract_site(None) is None


def test_chain_cycles_do_not_loop_forever(env):
    Session, rec_id = env
    a = add_build(Session, rec_id)
    b = add_build(Session, rec_id, parent_build_id=a)
    db = Session()
    db.query(models.MVPBuild).get(a).parent_build_id = b
    db.commit()
    build = db.query(models.MVPBuild).get(b)
    assert mvp_product.root_build(db, build).id in (a, b)
    assert mvp_product.chain_site(db, build) is None
    assert mvp_product.iteration_target(db, build).repo_name is None
    db.close()


def test_iteration_prompt_carries_the_live_site_and_naming_rule():
    spec = {"_meta": {"target_display_name": "Petrol"},
            "_iteration_meta": {"parent_site": LIVE_SITE, "engagement": {"unique_visitors": 0}}}
    prompt = mvp_site.site_prompt(spec)
    assert "IMPROVE THE EXISTING LIVE SITE" in prompt
    assert 'Keep the name exactly: "Crude Signals Weekly"' in prompt
    assert '"id": "brief-1"' in prompt and "DETAIL-1" not in prompt  # premium text is not needed
    assert "IMPROVE THE EXISTING LIVE SITE" not in mvp_site.site_prompt({"_meta": {}})


def test_keep_identity_restores_the_name_after_ai_renames_it():
    spec = {"_iteration_meta": {"parent_site": LIVE_SITE}}
    site = mvp_site.normalise_site({"name": "Brand New Name", "items": LIVE_SITE["items"]},
                                   mvp_site.default_site(spec))
    assert mvp_site.keep_identity(site, spec)["name"] == "Crude Signals Weekly"
    assert mvp_site.keep_identity(site, {})["name"] == "Brand New Name"


# --- Builds table: one row per MVP ----------------------------------------------------

def test_group_revisions_groups_by_original_build():
    rows = [{"id": 47}, {"id": 46}, {"id": 45}, {"id": 44}]
    parents = {47: 46, 46: 45, 45: None, 44: None}
    products = mvp_product.group_revisions(rows, parents)
    assert {k: [r["id"] for r in v] for k, v in products.items()} == {45: [45, 46, 47], 44: [44]}


def test_group_revisions_looks_up_parents_outside_the_page_and_survives_cycles():
    rows = [{"id": 9}]
    assert list(mvp_product.group_revisions(rows, {9: 5}, lambda bid: {5: 2, 2: None}[bid])) == [2]
    assert len(mvp_product.group_revisions([{"id": 1}, {"id": 2}], {1: 2, 2: 1})) >= 1


def test_builds_portfolio_shows_one_row_per_mvp(env):
    import asyncio

    Session, rec_id = env
    v1 = publish_parent(Session, rec_id)
    v2 = publish_parent(Session, rec_id, parent_build_id=v1, iteration_number=2, ai_cost_usd=0.04)
    v3 = add_build(Session, rec_id, parent_build_id=v2, iteration_number=3)
    other = add_build(Session, rec_id, status="LIVE")

    db = Session()
    for bid, vhash, kind in ((v1, "alice", "view"), (v1, "alice", "click"), (v2, "alice", "view"), (v2, "bob", "view")):
        db.add(models.MvpPageView(build_id=bid, visitor_hash=vhash, event_type=kind))
    db.commit()
    try:
        result = asyncio.run(dashboard_real.list_builds_portfolio(db=db))
    finally:
        db.close()

    rows = {r["product_id"]: r for r in result["builds"]}
    assert set(rows) == {v1, other}
    mvp = rows[v1]
    assert mvp["id"] == v3 and mvp["iteration_number"] == 3 and mvp["status"] == "QUEUED"  # actions use the latest
    assert [r["id"] for r in mvp["revisions"]] == [v1, v2, v3]
    assert mvp["engagement"] == 2  # alice visited two versions but counts once
    assert (mvp["page_views"], mvp["clicks"]) == (3, 1)
    assert mvp["total_ai_cost_usd"] == 0.04
    assert result["summary"]["total"] == 2 and result["summary"]["in_progress"] == 1


def test_builds_table_labels_and_sorts_by_mvp_number():
    from pathlib import Path

    html = (Path(__file__).parent / "templates" / "dashboard.html").read_text()
    js = (Path(__file__).parent / "static" / "js" / "dashboard.js").read_text()
    assert "MVP # <span" in html and "'#' + (b.product_id || b.id)" in html
    assert "x-for=\"r in (b.revisions || [])\"" in html
    assert "case 'id': va = a.product_id || a.id || 0;" in js


# --- builds killed by a restart must not block iterations ----------------------------

def test_stale_builds_are_marked_failed_and_fresh_ones_are_left_alone(env):
    from datetime import datetime, timedelta

    Session, rec_id = env
    old = add_build(Session, rec_id, status="QUEUED")
    fresh = add_build(Session, rec_id, status="GENERATING")
    done = add_build(Session, rec_id, status="LIVE")
    db = Session()
    db.query(models.MVPBuild).filter_by(id=old).update({"updated_at": datetime.utcnow() - timedelta(minutes=45)})
    db.query(models.MVPBuild).filter_by(id=done).update({"updated_at": datetime.utcnow() - timedelta(days=3)})
    db.commit()

    assert mvp_product.fail_stale_builds(db) == 1
    statuses = {b.id: b.status for b in db.query(models.MVPBuild).all()}
    assert statuses[old] == "FAILED" and statuses[fresh] == "GENERATING" and statuses[done] == "LIVE"
    stale = db.query(models.MVPBuild).get(old)
    assert "Interrupted" in stale.error_message and stale.build_steps[-1]["step"] == "INTERRUPTED"
    db.close()


def test_iterate_is_not_blocked_by_a_build_killed_by_a_restart(env, monkeypatch):
    import asyncio
    from datetime import datetime, timedelta
    from types import SimpleNamespace

    Session, rec_id = env
    live = publish_parent(Session, rec_id)
    dead = add_build(Session, rec_id, status="QUEUED", parent_build_id=live, iteration_number=2)
    db = Session()
    db.query(models.MVPBuild).filter_by(id=dead).update({"updated_at": datetime.utcnow() - timedelta(hours=1)})
    db.commit()

    class Request:
        headers = {"content-type": "application/json"}

        async def json(self):
            return {"reason": "manual"}

    tasks = SimpleNamespace(add_task=lambda *a, **k: None)
    try:
        result = asyncio.run(dashboard_real.iterate_mvp_build(live, Request(), tasks, db))
    finally:
        db.close()
    assert result["status"] == "QUEUED" and result["parent_build_id"] == live
