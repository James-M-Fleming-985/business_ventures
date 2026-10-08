import ast
from unittest.mock import MagicMock

import pytest

from services.ai_code_generator_orchestrator import AICodeGeneratorOrchestrator

clean = AICodeGeneratorOrchestrator._clean_code_fences

TESTS = '''import pytest
from l1 import Adder


class TestAdd:
    def test_add(self):
        assert Adder().add(1, 2) == 3
'''
IMPL = '''class Adder:
    def add(self, a, b):
        return a + b
'''


def chatty(code):
    return f"Here is the file you asked for:\n\n```python\n{code}```\n\nLet me know if you need changes!"


@pytest.mark.parametrize("raw", [
    "import os\nx = 1\n",
    "```python\nimport os\nx = 1\n```\n",
    "Sure, here you go:\n```python\nimport os\nx = 1\n```\nDone.",
    'import os\nS = """```\nhi\n```"""\n',
])
def test_clean_code_fences_returns_valid_python(raw):
    ast.parse(clean(raw))


def test_red_and_green_pass_when_model_wraps_code_in_prose(tmp_path):
    orch = AICodeGeneratorOrchestrator({"provider": "anthropic", "output_base_path": str(tmp_path)})
    orch.ai_provider = MagicMock()
    orch.ai_provider.generate_code.side_effect = [chatty(TESTS), chatty(IMPL)]
    reqs = {"layer_id": "L1", "acceptance_criteria": [], "technical_constraints": {}}

    red = orch.execute_red_phase(reqs)
    green = orch.execute_green_phase(reqs, red)

    assert green["status"] == "PASS"
    assert green["tests_passed"] == 1


def test_red_regenerates_tests_that_are_not_valid_python(tmp_path):
    orch = AICodeGeneratorOrchestrator({"provider": "anthropic", "output_base_path": str(tmp_path)})
    orch.ai_provider = MagicMock()
    orch.ai_provider.generate_code.side_effect = ["def broken(:\n", TESTS]
    orch.execute_red_phase({"layer_id": "L1", "acceptance_criteria": [], "technical_constraints": {}})
    assert orch.ai_provider.generate_code.call_count == 2
