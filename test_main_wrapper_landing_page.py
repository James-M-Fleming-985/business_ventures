"""Deployed MVPs must serve a landing page at "/" even when the module has its own FastAPI app."""
import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from services.ai_code_generator_orchestrator import AICodeGeneratorOrchestrator

MODULE = '''from fastapi import FastAPI


def create_app():
    app = FastAPI()

    @app.get("/api/v1/thing")
    def thing():
        return {"thing": 1}

    return app


app = create_app()
'''


def test_module_with_own_app_still_gets_landing_page(tmp_path, monkeypatch):
    src = tmp_path / "src"
    src.mkdir()
    (src / "__init__.py").write_text("")
    (src / "layer_mvp_0099.py").write_text(MODULE)

    orch = AICodeGeneratorOrchestrator({"provider": "anthropic", "output_base_path": str(tmp_path)})
    orch.ai_provider = MagicMock()
    orch.ai_provider.generate_code.side_effect = RuntimeError("no AI")  # use fallback wrapper
    files = {f["path"]: f["content"] for f in orch._generate_deployment_files(
        Path(tmp_path), spec={"feature_name": "Thing"}, build_id=99)}

    assert files["Procfile"].startswith("web: uvicorn main:app")
    (tmp_path / "main.py").write_text(files["main.py"])
    monkeypatch.syspath_prepend(str(tmp_path))
    for name in ("main", "src", "src.layer_mvp_0099"):
        sys.modules.pop(name, None)
    client = TestClient(importlib.import_module("main").app)

    home = client.get("/")
    assert home.status_code == 200 and "text/html" in home.headers["content-type"]
    assert client.get("/api/v1/thing").json() == {"thing": 1}


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
