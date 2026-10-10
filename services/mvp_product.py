"""Product identity for generated MVPs.

A *product* is one live site: one GitHub repo, one Railway service, one web
address, one app id (which Stripe subscriptions and subscriber cookies are
bound to) and one session secret. The first build of a product creates it;
every iteration is a new *revision* deployed to the same product, so
subscribers, the address and search ranking carry over.
"""

import ast
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

MAX_CHAIN_DEPTH = 100
_GITHUB_REPO_RE = re.compile(r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$")

# Railway variables an iteration must never change: changing them would log out
# subscribers, detach Stripe subscriptions or move the site.
PROTECTED_ENV_VARS = frozenset({
    "MVP_APP_ID", "MVP_SESSION_SECRET", "MVP_PUBLIC_URL", "PORT",
    "STRIPE_SECRET_KEY", "STRIPE_PRODUCT_ID", "MVP_STRIPE_PORTAL_LOGIN_URL",
})


def root_build(db, build):
    """The first build of the product this build belongs to."""
    from models import MVPBuild

    current, seen = build, {build.id}
    for _ in range(MAX_CHAIN_DEPTH):
        if not current.parent_build_id:
            return current
        parent = db.query(MVPBuild).filter(MVPBuild.id == current.parent_build_id).first()
        if parent is None or parent.id in seen:
            return current
        seen.add(parent.id)
        current = parent
    return current


def product_app_id(db, build) -> str:
    """The app id Stripe and subscriber cookies use; constant across iterations."""
    return f"mvp_{root_build(db, build).id}"


def parse_github_repo(url: Optional[str]) -> Optional[Dict[str, str]]:
    match = _GITHUB_REPO_RE.match((url or "").strip())
    if not match:
        return None
    owner, name = match.group(1), match.group(2)
    return {"owner": owner, "name": name, "full_name": f"{owner}/{name}"}


@dataclass(frozen=True)
class DeploymentTarget:
    """Where an iteration deploys: the existing product's repo and Railway service."""

    app_id: str
    repo_name: Optional[str] = None
    repo_full_name: Optional[str] = None
    github_url: Optional[str] = None
    railway_project_id: Optional[str] = None
    railway_service_id: Optional[str] = None
    railway_url: Optional[str] = None

    @property
    def has_repo(self) -> bool:
        return bool(self.repo_name)

    @property
    def has_railway(self) -> bool:
        return bool(self.railway_project_id and self.railway_service_id)


def iteration_target(db, build) -> Optional[DeploymentTarget]:
    """The product an iteration should update in place, or None for a brand-new product.

    Uses the nearest ancestor that was actually published, so iterating a
    failed iteration still updates the live site.
    """
    from models import MVPBuild

    if not getattr(build, "parent_build_id", None):
        return None
    app_id = product_app_id(db, build)
    current, seen = build, {build.id}
    for _ in range(MAX_CHAIN_DEPTH):
        if not current.parent_build_id:
            break
        parent = db.query(MVPBuild).filter(MVPBuild.id == current.parent_build_id).first()
        if parent is None or parent.id in seen:
            break
        seen.add(parent.id)
        repo = parse_github_repo(parent.github_url)
        if repo:
            railway_url = parent.railway_url
            if railway_url and railway_url.startswith("https://github.com/"):
                railway_url = None
            return DeploymentTarget(
                app_id=app_id,
                repo_name=repo["name"],
                repo_full_name=repo["full_name"],
                github_url=parent.github_url,
                railway_project_id=parent.railway_project_id,
                railway_service_id=parent.railway_service_id,
                railway_url=railway_url,
            )
        current = parent
    return DeploymentTarget(app_id=app_id)


def extract_site(main_py: Optional[str]) -> Optional[Dict[str, Any]]:
    """Read the SITE content dict from a generated main.py without executing it."""
    if not main_py:
        return None
    try:
        tree = ast.parse(main_py)
    except SyntaxError:
        return None
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "SITE"
        ):
            try:
                value = ast.literal_eval(node.value)
            except (ValueError, SyntaxError):
                return None
            return value if isinstance(value, dict) else None
    return None


def published_site(db, build_id: int) -> Optional[Dict[str, Any]]:
    """The SITE content a build deployed, if it used the subscription-site template."""
    from models import MVPBuildFile

    row = (
        db.query(MVPBuildFile)
        .filter(MVPBuildFile.build_id == build_id, MVPBuildFile.file_path == "main.py")
        .first()
    )
    return extract_site(row.content if row else None)


def chain_site(db, build) -> Optional[Dict[str, Any]]:
    """Content of the most recent earlier revision that used the subscription-site template."""
    from models import MVPBuild

    current, seen = build, {build.id}
    for _ in range(MAX_CHAIN_DEPTH):
        if not current.parent_build_id:
            return None
        parent = db.query(MVPBuild).filter(MVPBuild.id == current.parent_build_id).first()
        if parent is None or parent.id in seen:
            return None
        seen.add(parent.id)
        site = published_site(db, parent.id)
        if site:
            return site
        current = parent
    return None


def group_revisions(rows, parent_of, extra_parent_lookup=None):
    """Group per-build rows (dicts with "id") into one row per product.

    ``parent_of`` maps build id -> parent build id for every known build.
    ``extra_parent_lookup(build_id)`` may return the parent of a build that is
    not in ``parent_of`` (e.g. an older root outside the listed page).
    Returns ``{root_id: [rows oldest first]}``.
    """
    parent_of = dict(parent_of)

    def root_of(build_id):
        seen = set()
        current = build_id
        for _ in range(MAX_CHAIN_DEPTH):
            if current in seen:
                return current
            seen.add(current)
            if current not in parent_of and extra_parent_lookup is not None:
                parent_of[current] = extra_parent_lookup(current)
            parent = parent_of.get(current)
            if not parent:
                return current
            current = parent
        return current

    products = {}
    for row in rows:
        products.setdefault(root_of(row["id"]), []).append(row)
    for revisions in products.values():
        revisions.sort(key=lambda r: r["id"])
    return products


ACTIVE_STATUSES = ("QUEUED", "GENERATING", "UPLOADING", "DEPLOYING")
STALE_AFTER_MINUTES = 30


def fail_stale_builds(db, now=None, max_idle_minutes: int = STALE_AFTER_MINUTES) -> int:
    """Mark builds that stopped making progress (e.g. killed by a server restart) as FAILED.

    Builds run inside the web process, so a restart kills them silently and
    they would otherwise stay QUEUED for ever and block iterations.
    """
    from datetime import datetime, timedelta

    from models import MVPBuild

    cutoff = (now or datetime.utcnow()) - timedelta(minutes=max_idle_minutes)
    stale = (
        db.query(MVPBuild)
        .filter(MVPBuild.status.in_(ACTIVE_STATUSES))
        .filter(MVPBuild.updated_at < cutoff)
        .all()
    )
    for build in stale:
        build.status = "FAILED"
        build.error_message = (
            f"Interrupted: no progress for {max_idle_minutes} minutes "
            "(usually a server restart). Iterate or rebuild to try again."
        )
        build.build_steps = list(build.build_steps or []) + [
            {"step": "INTERRUPTED", "at": datetime.utcnow().isoformat(), "detail": build.error_message}
        ]
    if stale:
        db.commit()
        logger.info("Marked %d stale build(s) as FAILED", len(stale))
    return len(stale)
