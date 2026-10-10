"""Deployed MVPs serve a landing page at "/" and never expose or import the AI-written module."""
import importlib
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", f"sqlite:///{os.path.join(tempfile.mkdtemp(), 'landing.db')}")

from services.ai_code_generator_orchestrator import AICodeGeneratorOrchestrator  # noqa: E402

MODULE = '''import os
from pathlib import Path

from fastapi import FastAPI

# Importing this module would be observable: the MVP must never do it.
Path(os.environ["MODULE_IMPORT_MARKER"]).write_text("imported")


def create_app():
    app = FastAPI()

    @app.get("/api/v1/thing")
    def thing():
        return {"thing": 1}

    return app


app = create_app()
'''


@pytest.fixture(autouse=True)
def restore_modules():
    """Generated MVPs are imported as "main"; never leave them behind for other tests."""
    names = ("main", "mvp_runtime", "src", "src.layer_mvp_0099")
    saved = {name: sys.modules.get(name) for name in names}
    yield
    for name, module in saved.items():
        if module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = module


def test_module_with_own_app_is_never_exposed_but_landing_page_is_served(tmp_path, monkeypatch):
    marker = tmp_path / "marker"
    monkeypatch.setenv("MODULE_IMPORT_MARKER", str(marker))
    src = tmp_path / "src"
    src.mkdir()
    (src / "__init__.py").write_text("")
    (src / "layer_mvp_0099.py").write_text(MODULE)

    orch = AICodeGeneratorOrchestrator({"provider": "anthropic", "output_base_path": str(tmp_path)})
    orch.ai_provider = MagicMock()
    orch.ai_provider.generate_code.side_effect = RuntimeError("no AI")  # use default content
    files = {f["path"]: f["content"] for f in orch._generate_deployment_files(
        Path(tmp_path), spec={"feature_name": "Thing"}, build_id=99)}

    assert files["Procfile"].startswith("web: uvicorn main:app")
    assert "src." not in files["main.py"] and "_module_app" not in files["main.py"]
    for path, content in files.items():
        (tmp_path / path).write_text(content)
    monkeypatch.syspath_prepend(str(tmp_path))
    for name in ("main", "mvp_runtime", "src", "src.layer_mvp_0099"):
        sys.modules.pop(name, None)
    client = TestClient(importlib.import_module("main").app)

    home = client.get("/")
    assert home.status_code == 200 and "text/html" in home.headers["content-type"]
    # AI-written routes would bypass the paywall, so they must not be served...
    assert client.get("/api/v1/thing").status_code == 404
    # ...and AI-written code must not run beside the Stripe key and session secret.
    assert not marker.exists()


def test_truncated_ai_wrapper_falls_back_to_valid_main(tmp_path):
    import ast

    src = tmp_path / "src"
    src.mkdir()
    (src / "layer_mvp_0099.py").write_text(MODULE)
    orch = AICodeGeneratorOrchestrator({"provider": "anthropic", "output_base_path": str(tmp_path)})
    orch.ai_provider = MagicMock()
    orch.ai_provider.generate_code.return_value = (
        "from fastapi import FastAPI\napp = FastAPI()\nDASHBOARD_HTML = '''<html><body>cut off here"
    )

    main_py = orch._generate_main_wrapper(src, "layer_mvp_0099", spec={"feature_name": "Thing"}, build_id=99)

    ast.parse(main_py)
    assert orch.ai_provider.generate_code.call_args.kwargs["max_tokens"] == orch.MAIN_WRAPPER_MAX_TOKENS
