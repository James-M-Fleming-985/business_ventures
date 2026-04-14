"""Build Error Pattern Classifier (M3 Track B).

Classifies MVP build failures into categories and attempts common auto-fixes.
Feeds error patterns back into the system to reduce build error rate to <= 15%.
"""
import logging
import re
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Error categories with regex patterns
ERROR_PATTERNS = {
    "import_error": [
        re.compile(r"ModuleNotFoundError: No module named '([^']+)'", re.IGNORECASE),
        re.compile(r"ImportError: cannot import name '([^']+)'", re.IGNORECASE),
        re.compile(r"ImportError: No module named", re.IGNORECASE),
    ],
    "syntax_error": [
        re.compile(r"SyntaxError:", re.IGNORECASE),
        re.compile(r"IndentationError:", re.IGNORECASE),
        re.compile(r"TabError:", re.IGNORECASE),
    ],
    "name_error": [
        re.compile(r"NameError: name '([^']+)' is not defined", re.IGNORECASE),
    ],
    "type_error": [
        re.compile(r"TypeError:", re.IGNORECASE),
    ],
    "attribute_error": [
        re.compile(r"AttributeError:", re.IGNORECASE),
    ],
    "test_failure": [
        re.compile(r"FAILED.*test_", re.IGNORECASE),
        re.compile(r"AssertionError", re.IGNORECASE),
        re.compile(r"assert .+ ==", re.IGNORECASE),
    ],
    "config_error": [
        re.compile(r"KeyError:", re.IGNORECASE),
        re.compile(r"FileNotFoundError:", re.IGNORECASE),
        re.compile(r"PermissionError:", re.IGNORECASE),
        re.compile(r"No such file or directory", re.IGNORECASE),
    ],
    "runtime_error": [
        re.compile(r"RuntimeError:", re.IGNORECASE),
        re.compile(r"RecursionError:", re.IGNORECASE),
        re.compile(r"MemoryError:", re.IGNORECASE),
    ],
    "timeout": [
        re.compile(r"TimeoutError:", re.IGNORECASE),
        re.compile(r"timed? ?out", re.IGNORECASE),
    ],
    "dependency_missing": [
        re.compile(r"pip install", re.IGNORECASE),
        re.compile(r"requirements.*not.*satisfied", re.IGNORECASE),
    ],
}


def classify_build_error(stderr: str) -> Dict:
    """Classify a build error into categories with match details.

    Returns:
        {
            "primary_category": "import_error",
            "categories": {"import_error": 2, "syntax_error": 0, ...},
            "details": ["ModuleNotFoundError: No module named 'foo'"],
            "auto_fixable": True,
            "suggested_fix": "Add 'foo' to requirements.txt"
        }
    """
    if not stderr:
        return {
            "primary_category": "unknown",
            "categories": {},
            "details": [],
            "auto_fixable": False,
            "suggested_fix": None,
        }

    categories = {}
    details = []

    for category, patterns in ERROR_PATTERNS.items():
        count = 0
        for pattern in patterns:
            matches = pattern.findall(stderr)
            if matches:
                count += len(matches)
                for m in matches[:3]:  # Limit details
                    detail = m if isinstance(m, str) else str(m)
                    details.append(f"[{category}] {detail}")
        categories[category] = count

    # Determine primary category (most matches)
    primary = "unknown"
    max_count = 0
    for cat, count in categories.items():
        if count > max_count:
            max_count = count
            primary = cat

    # Check if auto-fixable
    auto_fixable, suggested_fix = _check_auto_fixable(primary, stderr, details)

    return {
        "primary_category": primary,
        "categories": categories,
        "details": details[:10],
        "auto_fixable": auto_fixable,
        "suggested_fix": suggested_fix,
    }


def _check_auto_fixable(category: str, stderr: str, details: list) -> Tuple[bool, Optional[str]]:
    """Check if the error can be auto-fixed."""
    if category == "import_error":
        # Extract missing module names
        missing = re.findall(r"No module named '([^']+)'", stderr)
        if missing:
            return True, f"Add missing packages to requirements.txt: {', '.join(set(missing))}"

    if category == "config_error":
        # Missing __init__.py
        if "__init__" in stderr or "No such file or directory" in stderr:
            return True, "Create missing __init__.py files in package directories"

    if category == "syntax_error":
        # Indentation issues
        if "IndentationError" in stderr or "TabError" in stderr:
            return True, "Fix indentation (convert tabs to 4 spaces)"

    return False, None


def attempt_auto_fix(
    error_classification: Dict,
    generated_files: Dict[str, str],
) -> Optional[Dict[str, str]]:
    """Attempt to auto-fix classified errors in generated files.

    Args:
        error_classification: Output from classify_build_error()
        generated_files: Dict of {file_path: content} from the build

    Returns:
        Fixed files dict if fix applied, None if not fixable
    """
    category = error_classification.get("primary_category")
    if not error_classification.get("auto_fixable"):
        return None

    fixed = dict(generated_files)
    applied = False

    if category == "import_error":
        # Ensure requirements.txt includes missing packages
        req_path = next((p for p in fixed if p.endswith("requirements.txt")), None)
        if req_path:
            stderr_text = " ".join(error_classification.get("details", []))
            missing = re.findall(r"No module named '([^'.]+)'", stderr_text)
            if missing:
                existing = fixed[req_path]
                for pkg in set(missing):
                    if pkg not in existing:
                        existing += f"\n{pkg}"
                        applied = True
                fixed[req_path] = existing

    if category == "config_error":
        # Add missing __init__.py files
        dirs_seen = set()
        for path in list(fixed.keys()):
            parts = path.split("/")
            for i in range(1, len(parts)):
                dir_path = "/".join(parts[:i])
                init_path = f"{dir_path}/__init__.py"
                if dir_path not in dirs_seen and init_path not in fixed:
                    # Check if this directory has .py files (is a package)
                    has_py = any(
                        p.startswith(dir_path + "/") and p.endswith(".py")
                        for p in fixed
                    )
                    if has_py:
                        fixed[init_path] = ""
                        applied = True
                dirs_seen.add(dir_path)

    if category == "syntax_error":
        # Fix tab/space issues
        for path, content in fixed.items():
            if path.endswith(".py") and "\t" in content:
                fixed[path] = content.replace("\t", "    ")
                applied = True

    return fixed if applied else None
