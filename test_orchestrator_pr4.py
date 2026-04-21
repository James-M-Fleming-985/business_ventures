"""Unit tests for PR4 orchestrator auto-REFACTOR retry loop + threshold."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from services.ai_code_generator_orchestrator import (
    DEFAULT_MAX_VERIFICATION_RETRIES,
    DEFAULT_MIN_VERIFICATION_PCT,
    AICodeGeneratorOrchestrator,
)


def _make_orch(min_pct=80.0, max_retries=2):
    with patch(
        "services.ai_code_generator_orchestrator.AIProviderFactory"
    ) as factory:
        factory.create_provider.return_value = MagicMock(
            validate_configuration=MagicMock(return_value=False)
        )
        return AICodeGeneratorOrchestrator(
            {
                "output_base_path": "/tmp",
                "min_verification_pct": min_pct,
                "max_verification_retries": max_retries,
            }
        )


def test_threshold_defaults():
    orch = _make_orch()
    assert orch.min_verification_pct == 80.0
    assert orch.max_verification_retries == 2


def test_threshold_overridable_via_config():
    orch = _make_orch(min_pct=60.0, max_retries=4)
    assert orch.min_verification_pct == 60.0
    assert orch.max_verification_retries == 4


def test_full_cycle_no_retry_when_threshold_met(monkeypatch):
    orch = _make_orch(min_pct=80.0, max_retries=3)
    red = MagicMock(return_value={"phase": "RED", "tests_failed": 0})
    green = MagicMock(return_value={"phase": "GREEN"})
    refactor = MagicMock(return_value={"phase": "REFACTOR"})
    verify = MagicMock(
        return_value={
            "phase": "VERIFICATION",
            "summary": {"verification_pct": 100.0},
            "ac_verification": {"summary": {"verification_pct": 100.0}, "by_ac": {}},
        }
    )
    orch.execute_red_phase = red
    orch.execute_green_phase = green
    orch.execute_refactor_phase = refactor
    orch.execute_verification_phase = verify

    result = orch.execute_full_cycle({"acceptance_criteria": []})

    assert green.call_count == 1
    assert verify.call_count == 1
    assert result["phases"]["VERIFICATION"]["attempts"] == 1
    assert result["phases"]["VERIFICATION"]["threshold_met"] is True


def test_full_cycle_retries_up_to_max_when_below_threshold():
    orch = _make_orch(min_pct=80.0, max_retries=2)
    red = MagicMock(return_value={"phase": "RED", "tests_failed": 0})
    green = MagicMock(return_value={"phase": "GREEN"})
    refactor = MagicMock(return_value={"phase": "REFACTOR"})
    # Always returns 50% — never crosses threshold; should run initial + 2 retries
    verify = MagicMock(
        return_value={
            "phase": "VERIFICATION",
            "summary": {"verification_pct": 50.0},
            "ac_verification": {"summary": {"verification_pct": 50.0}, "by_ac": {}},
        }
    )
    orch.execute_red_phase = red
    orch.execute_green_phase = green
    orch.execute_refactor_phase = refactor
    orch.execute_verification_phase = verify

    result = orch.execute_full_cycle({"acceptance_criteria": []})

    assert green.call_count == 3  # initial + 2 retries
    assert verify.call_count == 3
    assert result["phases"]["VERIFICATION"]["attempts"] == 3
    assert result["phases"]["VERIFICATION"]["threshold_met"] is False


def test_full_cycle_stops_retrying_once_threshold_met():
    orch = _make_orch(min_pct=80.0, max_retries=3)
    red = MagicMock(return_value={"phase": "RED", "tests_failed": 0})
    green = MagicMock(return_value={"phase": "GREEN"})
    refactor = MagicMock(return_value={"phase": "REFACTOR"})
    pcts = iter([40.0, 60.0, 90.0, 100.0])

    def _verify(_green):
        pct = next(pcts)
        return {
            "phase": "VERIFICATION",
            "summary": {"verification_pct": pct},
            "ac_verification": {"summary": {"verification_pct": pct}, "by_ac": {}},
        }

    orch.execute_red_phase = red
    orch.execute_green_phase = green
    orch.execute_refactor_phase = refactor
    orch.execute_verification_phase = _verify

    result = orch.execute_full_cycle({"acceptance_criteria": []})

    # Threshold first crossed on the 3rd verification (90%), so 3 attempts total
    assert green.call_count == 3
    assert result["phases"]["VERIFICATION"]["attempts"] == 3
    assert result["phases"]["VERIFICATION"]["threshold_met"] is True
