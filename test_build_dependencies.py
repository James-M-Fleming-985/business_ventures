"""Generated MVP tests run inside this server's environment, so it must be able to run them."""


def test_fastapi_testclient_works():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()

    @app.get("/ping")
    def ping():
        return {"ok": True}

    assert TestClient(app).get("/ping").json() == {"ok": True}


def test_requirements_never_list_standard_library_or_local_modules(tmp_path, monkeypatch):
    """A stdlib name such as __future__ in requirements.txt makes pip, and so the Railway build, fail."""
    import os
    import tempfile
    from pathlib import Path
    from unittest.mock import MagicMock

    os.environ.setdefault("DATABASE_URL", f"sqlite:///{os.path.join(tempfile.mkdtemp(), 'deps.db')}")
    from services.ai_code_generator_orchestrator import AICodeGeneratorOrchestrator

    src = tmp_path / "src"
    src.mkdir()
    (src / "layer_mvp_0044.py").write_text(
        "from __future__ import annotations\n"
        "import zoneinfo, graphlib\n"
        "import tomllib\n"
        "from . import helpers\n"
        "from .models import Thing\n"
        "from src.other import x\n"
        "import mvp_runtime\n"
        "from fastapi import FastAPI\n"
        "import requests\n"
        "from bs4 import BeautifulSoup\n"
    )
    orch = AICodeGeneratorOrchestrator({"provider": "anthropic", "output_base_path": str(tmp_path)})
    orch.ai_provider = MagicMock()
    orch.ai_provider.generate_code.side_effect = RuntimeError("no AI")
    files = {f["path"]: f["content"] for f in orch._generate_deployment_files(Path(tmp_path), spec={}, build_id=44)}

    packages = files["requirements.txt"].split()
    assert packages == sorted(packages) and "" not in packages
    for bad in ("__future__", "zoneinfo", "graphlib", "tomllib", "src", "mvp_runtime", "helpers", "models"):
        assert bad not in packages, bad
    for needed in ("fastapi", "uvicorn", "stripe", "requests", "beautifulsoup4"):
        assert needed in packages, needed
