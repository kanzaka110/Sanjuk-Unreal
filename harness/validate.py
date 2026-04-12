#!/usr/bin/env python3
"""Standalone harness validation for Sanjuk-Unreal."""

import ast
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

SECRET_PATTERNS = [
    re.compile(r'sk-ant-[a-zA-Z0-9_-]{20,}'),
    re.compile(r'sk-proj-[a-zA-Z0-9_-]{20,}'),
    re.compile(r'API_KEY\s*=\s*["\'][a-zA-Z0-9_-]{10,}["\']'),
]

REQUIRED_DIRS = ["Tutorial", "Briefing", "UE_bot", "scripts"]
REQUIRED_FILES = ["CLAUDE.md", "shared_config.py"]


def main():
    passed = failed = 0

    # Required files
    missing = [f for f in REQUIRED_FILES if not (PROJECT_ROOT / f).exists()]
    if missing:
        print(f"FAIL: Missing files: {missing}"); failed += 1
    else:
        print(f"PASS: All required files exist"); passed += 1

    # Required dirs
    missing_d = [d for d in REQUIRED_DIRS if not (PROJECT_ROOT / d).exists()]
    if missing_d:
        print(f"FAIL: Missing dirs: {missing_d}"); failed += 1
    else:
        print(f"PASS: All required directories exist"); passed += 1

    # Python syntax
    errors = []
    for py in PROJECT_ROOT.rglob("*.py"):
        if "__pycache__" in str(py): continue
        try:
            ast.parse(py.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError as e:
            errors.append(f"{py.relative_to(PROJECT_ROOT)}: {e}")
    if errors:
        print(f"FAIL: Syntax errors: {errors}"); failed += 1
    else:
        print("PASS: All Python files valid"); passed += 1

    # Secrets
    violations = []
    for py in PROJECT_ROOT.rglob("*.py"):
        if "test_" in py.name or "__pycache__" in str(py): continue
        content = py.read_text(encoding="utf-8", errors="ignore")
        for p in SECRET_PATTERNS:
            if p.findall(content): violations.append(str(py.relative_to(PROJECT_ROOT)))
    if violations:
        print(f"FAIL: Secrets in: {violations}"); failed += 1
    else:
        print("PASS: No secrets detected"); passed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
