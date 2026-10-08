import pytest
from unittest.mock import MagicMock

from services.ai_code_generator_orchestrator import (
    AICodeGeneratorOrchestrator,
    BuildCancelled,
)


def _orchestrator(tmp_path, should_abort):
    orch = AICodeGeneratorOrchestrator(
        {"provider": "anthropic", "output_base_path": str(tmp_path), "should_abort": should_abort}
    )
    orch.ai_provider = MagicMock()
    return orch


def test_green_phase_aborts_before_calling_ai_when_cancelled(tmp_path):
    orch = _orchestrator(tmp_path, lambda: True)
    with pytest.raises(BuildCancelled):
        orch.execute_green_phase({"layer_id": "L1"}, {"tests_generated": []})
    orch.ai_provider.generate_code.assert_not_called()


def test_green_phase_runs_normally_when_not_cancelled(tmp_path):
    orch = _orchestrator(tmp_path, lambda: False)
    orch.ai_provider.generate_code.return_value = "x = 1\n"
    orch.MAX_GREEN_RETRIES = 1
    orch.execute_green_phase({"layer_id": "L1"}, {"tests_generated": []})
    orch.ai_provider.generate_code.assert_called_once()
