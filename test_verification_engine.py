"""Unit tests for services.verification_engine (PR2)."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from services.verification_engine import (
    parse_pytest_outcomes,
    parse_req_tags_from_test_file,
    verify_acceptance_criteria,
)


def _write(tmp_path: Path, name: str, body: str) -> Path:
    p = tmp_path / name
    p.write_text(textwrap.dedent(body).lstrip("\n"))
    return p


# ---------------------------------------------------------------------------
# parse_req_tags_from_test_file
# ---------------------------------------------------------------------------

def test_parses_method_level_req_tag(tmp_path):
    test_file = _write(tmp_path, "test_a.py", """
        class TestThing:
            # REQ-AC-001
            def test_one(self):
                assert True

            # REQ-AC-002
            def test_two(self):
                assert True
    """)
    mapping = parse_req_tags_from_test_file(test_file)
    assert sorted(mapping.keys()) == ["AC-001", "AC-002"]
    assert mapping["AC-001"][0].endswith("::TestThing::test_one")
    assert mapping["AC-002"][0].endswith("::TestThing::test_two")


def test_class_level_tag_applies_to_all_methods(tmp_path):
    test_file = _write(tmp_path, "test_b.py", """
        # REQ-AC-010
        class TestSuite:
            def test_x(self): pass
            def test_y(self): pass
    """)
    mapping = parse_req_tags_from_test_file(test_file)
    assert "AC-010" in mapping
    assert len(mapping["AC-010"]) == 2


def test_multiple_tags_on_one_method(tmp_path):
    test_file = _write(tmp_path, "test_c.py", """
        class T:
            # REQ-AC-001
            # REQ-AC-002
            def test_combo(self):
                pass
    """)
    mapping = parse_req_tags_from_test_file(test_file)
    assert "AC-001" in mapping and "AC-002" in mapping
    assert mapping["AC-001"][0].endswith("::T::test_combo")
    assert mapping["AC-002"][0].endswith("::T::test_combo")


def test_module_level_function_tag(tmp_path):
    test_file = _write(tmp_path, "test_d.py", """
        # REQ-AC-100
        def test_module_level():
            assert True
    """)
    mapping = parse_req_tags_from_test_file(test_file)
    assert mapping["AC-100"][0].endswith("::test_module_level")


def test_non_test_methods_ignored(tmp_path):
    test_file = _write(tmp_path, "test_e.py", """
        # REQ-AC-001
        class TestX:
            # REQ-AC-002
            def helper(self):
                pass
            # REQ-AC-003
            def test_real(self):
                pass
    """)
    mapping = parse_req_tags_from_test_file(test_file)
    # helper is not a test_ method, so AC-002 should have no tests assigned
    assert "AC-002" not in mapping
    # test_real picks up the class-level AC-001 plus its own AC-003
    assert "AC-001" in mapping and "AC-003" in mapping


def test_syntax_error_returns_empty(tmp_path):
    test_file = _write(tmp_path, "test_bad.py", "def broken(:\n    pass\n")
    assert parse_req_tags_from_test_file(test_file) == {}


# ---------------------------------------------------------------------------
# parse_pytest_outcomes
# ---------------------------------------------------------------------------

def test_parses_passed_failed_skipped():
    out = textwrap.dedent("""
        ============================= test session starts ==============================
        tests/test_x.py::TestY::test_a PASSED                                    [ 25%]
        tests/test_x.py::TestY::test_b FAILED                                    [ 50%]
        tests/test_x.py::test_top SKIPPED                                        [ 75%]
        tests/test_x.py::TestY::test_c ERROR                                     [100%]
    """)
    outcomes = parse_pytest_outcomes(out)
    assert outcomes["tests/test_x.py::TestY::test_a"] == "passed"
    assert outcomes["tests/test_x.py::TestY::test_b"] == "failed"
    assert outcomes["tests/test_x.py::test_top"] == "skipped"
    assert outcomes["tests/test_x.py::TestY::test_c"] == "error"


# ---------------------------------------------------------------------------
# verify_acceptance_criteria
# ---------------------------------------------------------------------------

def test_full_verification_report(tmp_path):
    test_file = _write(tmp_path, "test_full.py", """
        class TestFeature:
            # REQ-AC-001
            def test_alpha(self): pass

            # REQ-AC-002
            def test_beta(self): pass
    """)
    pytest_output = (
        f"{test_file}::TestFeature::test_alpha PASSED [ 50%]\n"
        f"{test_file}::TestFeature::test_beta FAILED [100%]\n"
    )
    acs = [
        {"criterion_id": "AC-001"},
        {"criterion_id": "AC-002"},
        {"criterion_id": "AC-003"},  # not covered
    ]

    report = verify_acceptance_criteria([str(test_file)], pytest_output, acs)

    assert report["by_ac"]["AC-001"]["covered"] is True
    assert report["by_ac"]["AC-001"]["all_passing"] is True
    assert report["by_ac"]["AC-002"]["covered"] is True
    assert report["by_ac"]["AC-002"]["all_passing"] is False
    assert report["by_ac"]["AC-002"]["failing_count"] == 1
    assert report["by_ac"]["AC-003"]["covered"] is False

    summary = report["summary"]
    assert summary["total_acs"] == 3
    assert summary["covered_acs"] == 2
    assert summary["fully_verified_acs"] == 1
    assert summary["uncovered_ac_ids"] == ["AC-003"]


def test_pytest_relative_path_matches_absolute_node_id(tmp_path):
    """Pytest typically prints relative paths; tag map uses absolute paths."""
    test_file = _write(tmp_path, "test_rel.py", """
        class T:
            # REQ-AC-001
            def test_one(self): pass
    """)
    # Simulate pytest output using just the basename
    pytest_output = "test_rel.py::T::test_one PASSED [100%]\n"
    report = verify_acceptance_criteria(
        [str(test_file)], pytest_output, [{"criterion_id": "AC-001"}]
    )
    assert report["by_ac"]["AC-001"]["all_passing"] is True


def test_empty_inputs_safe():
    report = verify_acceptance_criteria([], "", [])
    assert report["by_ac"] == {}
    assert report["summary"]["total_acs"] == 0
    assert report["summary"]["coverage_pct"] == 0.0
