"""Every route must require a login unless it is explicitly public by design."""

import os
import sys
import tempfile

os.environ.setdefault("DATABASE_URL", f"sqlite:///{os.path.join(tempfile.mkdtemp(), 'guard.db')}")
os.environ.setdefault("SECRET_KEY", "test-secret-key-0123456789abcdef0123456789")

# Public on purpose: pages, login/registration, Stripe's webhook, the MVP beacon.
PUBLIC_ROUTES = {
    ("GET", "/"),
    ("GET", "/login"),
    ("GET", "/logout"),
    ("GET", "/register"),
    ("GET", "/dashboard"),  # page redirects to /login itself when not authenticated
    ("GET", "/subscription"),
    ("GET", "/subscription/success"),
    ("GET", "/subscription/cancel"),
    ("GET", "/favicon.ico"),
    ("GET", "/health"),
    ("GET", "/api/auth/check-first-user"),
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/logout"),
    ("POST", "/api/auth/register"),
    ("GET", "/api/subscription/config"),
    ("POST", "/api/subscription/webhook"),
    ("POST", "/api/dashboard/mvp-beacon/{build_id}"),
}


def test_no_route_is_open_unless_allowlisted():
    stale = sys.modules.get("main")
    if stale is not None and not hasattr(stale, "BUILD_VERSION"):
        sys.modules.pop("main")  # a generated MVP's main left behind by another test
    import main

    spec = main.app.openapi()
    open_routes = {
        (method.upper(), path)
        for path, operations in spec["paths"].items()
        for method, operation in operations.items()
        if method in {"get", "post", "put", "patch", "delete"} and not operation.get("security")
    }
    unexpected = sorted(open_routes - PUBLIC_ROUTES)
    assert unexpected == [], f"Routes with no authentication: {unexpected}"
