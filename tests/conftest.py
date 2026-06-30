"""Shared pytest fixtures and path helpers for FormulationOS tests."""

from __future__ import annotations

from pathlib import Path

import pytest

# FormulationOS project root: parent of the tests/ directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src" / "formulation_os"
BUILTINS_DIR = SRC_ROOT / "tools" / "builtins"


@pytest.fixture(scope="session")
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def builtins_dir() -> Path:
    return BUILTINS_DIR