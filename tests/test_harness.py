"""Harness validation tests for Sanjuk-Unreal."""

import ast
import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent

SECRET_PATTERNS = [
    re.compile(r'sk-ant-[a-zA-Z0-9_-]{20,}'),
    re.compile(r'sk-proj-[a-zA-Z0-9_-]{20,}'),
    re.compile(r'API_KEY\s*=\s*["\'][a-zA-Z0-9_-]{10,}["\']'),
]


class TestProjectStructure:
    def test_claude_md_exists(self):
        assert (PROJECT_ROOT / "CLAUDE.md").exists()

    def test_required_directories(self):
        for d in ["Tutorial", "Briefing", "UE_bot", "scripts"]:
            assert (PROJECT_ROOT / d).exists(), f"{d}/ missing"

    def test_shared_config_exists(self):
        assert (PROJECT_ROOT / "shared_config.py").exists()

    def test_tutorial_files_have_content(self):
        tutorial = PROJECT_ROOT / "Tutorial"
        md_files = list(tutorial.rglob("*.md"))
        assert len(md_files) >= 5, f"Only {len(md_files)} tutorial files (need >= 5)"


class TestNoHardcodedSecrets:
    def test_no_secrets_in_source(self):
        violations = []
        for py_file in PROJECT_ROOT.rglob("*.py"):
            if "test_" in py_file.name or "__pycache__" in str(py_file):
                continue
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            for pattern in SECRET_PATTERNS:
                if pattern.findall(content):
                    violations.append(str(py_file.relative_to(PROJECT_ROOT)))
        assert not violations, f"Secrets found: {violations}"


class TestPythonSyntax:
    def test_all_py_files_valid(self):
        errors = []
        for py_file in PROJECT_ROOT.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                source = py_file.read_text(encoding="utf-8", errors="ignore")
                ast.parse(source)
            except SyntaxError as e:
                errors.append(f"{py_file.relative_to(PROJECT_ROOT)}: {e}")
        assert not errors, f"Syntax errors: {errors}"
