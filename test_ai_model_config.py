"""Anthropic model configuration and response handling."""

import importlib
import pathlib
import sys
import types
from unittest.mock import MagicMock

RETIRED_MODEL = "claude-sonnet-4-20250514"


def _block(kind, text=None):
    return types.SimpleNamespace(type=kind, text=text)


def _reload_provider(monkeypatch, model_env=None):
    if model_env is None:
        monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    else:
        monkeypatch.setenv("ANTHROPIC_MODEL", model_env)
    import services.ai_provider as module
    return importlib.reload(module)


def test_retired_model_is_not_hardcoded_anywhere_in_services():
    root = pathlib.Path(__file__).parent / "services"
    offenders = [p.name for p in root.glob("*.py") if RETIRED_MODEL in p.read_text()]
    assert offenders == []


def test_default_model_is_not_the_retired_one(monkeypatch):
    module = _reload_provider(monkeypatch)
    assert module.DEFAULT_ANTHROPIC_MODEL == "claude-sonnet-5-5"
    assert module.AnthropicProvider(api_key="k").model == "claude-sonnet-5-5"


def test_model_can_be_overridden_from_environment(monkeypatch):
    module = _reload_provider(monkeypatch, "claude-some-future-model")
    assert module.AnthropicProvider(api_key="k").model == "claude-some-future-model"
    _reload_provider(monkeypatch)


def test_response_text_skips_thinking_blocks(monkeypatch):
    module = _reload_provider(monkeypatch)
    message = types.SimpleNamespace(
        content=[_block("thinking"), _block("text", "hello "), _block("text", "world")]
    )
    assert module.response_text(message) == "hello world"


def test_provider_returns_text_when_thinking_block_comes_first(monkeypatch):
    module = _reload_provider(monkeypatch)
    message = types.SimpleNamespace(
        stop_reason="end_turn", content=[_block("thinking"), _block("text", "generated code")]
    )
    fake_client = MagicMock()
    fake_client.messages.create.return_value = message
    fake_anthropic = types.SimpleNamespace(Anthropic=lambda api_key: fake_client)
    monkeypatch.setitem(sys.modules, "anthropic", fake_anthropic)

    result = module.AnthropicProvider(api_key="k").generate_code("write code")

    assert result == "generated code"
    assert fake_client.messages.create.call_args.kwargs["model"] == "claude-sonnet-5-5"
