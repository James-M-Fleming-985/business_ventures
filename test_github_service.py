"""Generated MVP repositories must never be created public."""

import importlib
import sys
from unittest.mock import MagicMock, patch


def _load_service_module():
    with patch.dict(sys.modules, {"github": MagicMock()}):
        sys.modules.pop("services.github_service", None)
        return importlib.import_module("services.github_service")


def test_create_repository_is_private():
    module = _load_service_module()

    with patch.dict("os.environ", {"GITHUB_TOKEN": "t", "GITHUB_ORG": "o"}):
        service = module.GitHubService()

    user = MagicMock()
    user.create_repo.return_value = MagicMock(
        full_name="o/mvp-1", html_url="https://github.com/o/mvp-1", clone_url="c"
    )
    service._client = MagicMock()
    service._client.get_user.return_value = user

    service.create_repository("mvp-1", "desc")

    assert user.create_repo.call_args.kwargs["private"] is True
