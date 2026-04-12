"""Pytest configuration for Sanjuk-Unreal."""

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture
def project_root():
    return PROJECT_ROOT
