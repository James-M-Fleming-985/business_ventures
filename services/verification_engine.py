"""
Verification Engine — REQ-AC Traceability (PR2)

Parses generated test files for ``# REQ-AC-XXX`` comments and maps acceptance
criteria to the test classes/methods that claim to verify them, then cross-
references pytest output to determine pass/fail per AC.

Adapted (minimal) from PROJECT-004 evidence-based traceability validator.
The orchestrator calls :func:`verify_acceptance_criteria` after the GREEN phase.

Conventions
-----------
* A comment line ``# REQ-AC-001`` immediately above a ``class`` or ``def``
  declares that this construct verifies acceptance criterion ``AC-001``.
* Multiple REQ-AC comments may appear in the gap between two declarations
  (a single class/method may verify multiple ACs).
* A class-level REQ-AC tag implicitly applies to every test method in that
  class (test_* methods).

Returned shape (see :func:`verify_acceptance_criteria`)::

    {
        "by_ac": {
            "AC-001": {
                "covered": True,
                "tests": [{"node_id": "...::TestX::test_y", "outcome": "passed"}],
                "passing_count": 1,
                "failing_count": 0,
                "all_passing": True,
            },
            ...
        },
        "summary": {
            "total_acs": 5,
            "covered_acs": 4,
            "fully_verified_acs": 3,
            "coverage_pct": 80.0,
            "verification_pct": 60.0,
            "uncovered_ac_ids": ["AC-005"],
        },
    }
"""

from __future__ import annotations

import ast
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Matches ``# REQ-AC-001`` or ``# REQ-AC-001-FOO`` (AC IDs are typically
# AC-XXX but we allow longer alphanumeric suffixes).
REQ_TAG_RE = re.compile(r"#\s*REQ-(AC-[A-Z0-9_-]+)\b")

# pytest -v output line: ``tests/test_x.py::TestY::test_z PASSED [ 50%]``
PYTEST_LINE_RE = re.compile(
    r"^(?P<node_id>\S+::\S+)\s+(?P<outcome>PASSED|FAILED|ERROR|SKIPPED)\b",
    re.MULTILINE,
)


def _read_source_lines(path: Path) -> List[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        logger.warning("verification_engine: cannot read %s (%s)", path, exc)
        return []


def _collect_preceding_tags(
    source_lines: List[str], decl_lineno: int, last_used_lineno: int
) -> List[str]:
    """Return REQ-AC tag IDs found in comment lines between ``last_used_lineno``
    and ``decl_lineno`` (1-indexed, exclusive of decl line).
    """
    tags: List[str] = []
    # ast lineno is 1-indexed; source_lines is 0-indexed.
    for i in range(last_used_lineno, decl_lineno - 1):
        if i < 0 or i >= len(source_lines):
            continue
        stripped = source_lines[i].strip()
        if not stripped.startswith("#"):
            continue
        for m in REQ_TAG_RE.finditer(stripped):
            tags.append(m.group(1))
    return tags


def parse_req_tags_from_test_file(path: Path) -> Dict[str, List[str]]:
    """Walk ``path`` and return a mapping ``{ac_id: [test_node_id, ...]}``.

    ``test_node_id`` is the pytest-style node id relative to the test file:
    ``<file>::ClassName::method`` or ``<file>::function``.
    """
    path = Path(path)
    source_lines = _read_source_lines(path)
    if not source_lines:
        return {}

    try:
        tree = ast.parse("\n".join(source_lines), filename=str(path))
    except SyntaxError as exc:
        logger.warning("verification_engine: SyntaxError in %s (%s)", path, exc)
        return {}

    file_label = str(path)
    mapping: Dict[str, List[str]] = {}
    cursor_line = 0  # 0-indexed; tracks how far into source_lines we've consumed

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            tags = _collect_preceding_tags(source_lines, node.lineno, cursor_line)
            if node.name.startswith("test_"):
                node_id = f"{file_label}::{node.name}"
                for tag in tags:
                    mapping.setdefault(tag, []).append(node_id)
            cursor_line = node.end_lineno or node.lineno

        elif isinstance(node, ast.ClassDef):
            class_tags = _collect_preceding_tags(
                source_lines, node.lineno, cursor_line
            )
            inner_cursor = node.lineno  # start scanning from the class header line
            for inner in node.body:
                if isinstance(inner, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_tags = _collect_preceding_tags(
                        source_lines, inner.lineno, inner_cursor
                    )
                    if inner.name.startswith("test_"):
                        node_id = f"{file_label}::{node.name}::{inner.name}"
                        for tag in class_tags + method_tags:
                            mapping.setdefault(tag, []).append(node_id)
                    inner_cursor = inner.end_lineno or inner.lineno
            cursor_line = node.end_lineno or node.lineno

        else:
            cursor_line = (node.end_lineno or node.lineno or cursor_line)

    return mapping


def parse_pytest_outcomes(pytest_output: str) -> Dict[str, str]:
    """Return ``{node_id_suffix: outcome_lowercase}`` parsed from ``pytest -v``.

    ``node_id_suffix`` is whatever pytest printed (typically a relative path).
    Matched against test node ids using ``endswith``.
    """
    if not isinstance(pytest_output, str) or not pytest_output:
        return {}
    outcomes: Dict[str, str] = {}
    for m in PYTEST_LINE_RE.finditer(pytest_output):
        outcomes[m.group("node_id")] = m.group("outcome").lower()
    return outcomes


def _resolve_outcome(node_id: str, pytest_outcomes: Dict[str, str]) -> Optional[str]:
    """pytest reports relative paths; our tag map uses absolute. Match by suffix."""
    # Fast path: exact match.
    if node_id in pytest_outcomes:
        return pytest_outcomes[node_id]
    # Suffix match — try progressively shorter trailing components.
    parts = node_id.split("::")
    for start in range(len(parts)):
        candidate = "::".join(parts[start:])
        for k, v in pytest_outcomes.items():
            if k.endswith(candidate):
                return v
    return None


def verify_acceptance_criteria(
    test_files: List[str],
    pytest_output: str,
    acceptance_criteria: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Map acceptance criteria to the tests that claim to verify them and
    determine pass/fail status per AC.

    Parameters
    ----------
    test_files: paths to generated test files (absolute).
    pytest_output: combined stdout+stderr from a ``pytest -v`` invocation.
    acceptance_criteria: list of ``{"criterion_id": "AC-XXX", ...}`` dicts.

    Returns
    -------
    See module docstring for shape.
    """
    # Aggregate REQ-AC tag mappings across all test files.
    tag_to_tests: Dict[str, List[str]] = {}
    for tf in test_files or []:
        for ac_id, node_ids in parse_req_tags_from_test_file(Path(tf)).items():
            tag_to_tests.setdefault(ac_id, []).extend(node_ids)

    pytest_outcomes = parse_pytest_outcomes(pytest_output or "")

    by_ac: Dict[str, Dict[str, Any]] = {}
    for ac in acceptance_criteria or []:
        ac_id = ac.get("criterion_id") if isinstance(ac, dict) else None
        if not ac_id:
            continue
        node_ids = tag_to_tests.get(ac_id, [])
        tests_view = []
        passing = failing = 0
        for nid in node_ids:
            outcome = _resolve_outcome(nid, pytest_outcomes) or "unknown"
            tests_view.append({"node_id": nid, "outcome": outcome})
            if outcome == "passed":
                passing += 1
            elif outcome in ("failed", "error"):
                failing += 1
        by_ac[ac_id] = {
            "covered": bool(node_ids),
            "tests": tests_view,
            "passing_count": passing,
            "failing_count": failing,
            "all_passing": bool(node_ids) and failing == 0 and passing > 0,
        }

    total = len(by_ac)
    covered = sum(1 for v in by_ac.values() if v["covered"])
    fully = sum(1 for v in by_ac.values() if v["all_passing"])
    uncovered = sorted(k for k, v in by_ac.items() if not v["covered"])

    return {
        "by_ac": by_ac,
        "summary": {
            "total_acs": total,
            "covered_acs": covered,
            "fully_verified_acs": fully,
            "coverage_pct": round(100.0 * covered / total, 2) if total else 0.0,
            "verification_pct": round(100.0 * fully / total, 2) if total else 0.0,
            "uncovered_ac_ids": uncovered,
        },
    }
