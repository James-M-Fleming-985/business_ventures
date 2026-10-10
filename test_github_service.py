"""Generated MVP repositories must never be created public."""

import importlib
import sys
from unittest.mock import MagicMock, patch


def _load_service_module():
    import services

    original = getattr(services, "github_service", None)
    with patch.dict(sys.modules, {"github": MagicMock()}):
        sys.modules.pop("services.github_service", None)
        module = importlib.import_module("services.github_service")
    # Don't leave the copy built on a fake `github` library attached to the package.
    if original is not None:
        services.github_service = original
    else:
        delattr(services, "github_service")
    return module


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


def test_existing_public_repo_is_made_private():
    module = _load_service_module()

    class FakeGithubException(Exception):
        status = 422

    module.GithubException = FakeGithubException

    with patch.dict("os.environ", {"GITHUB_TOKEN": "t", "GITHUB_ORG": "o"}):
        service = module.GitHubService()

    existing = MagicMock(full_name="o/mvp-1", html_url="h", clone_url="c", private=False)
    service._client = MagicMock()
    service._client.get_user.return_value.create_repo.side_effect = FakeGithubException()
    service._client.get_repo.return_value = existing

    service.create_repository("mvp-1", "desc")

    existing.edit.assert_called_once_with(private=True)
