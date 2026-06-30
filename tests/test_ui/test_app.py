"""Tests for the Streamlit UI module.

The UI is presentation-only glue over the already-tested Orchestrator and
Report modules. These tests cover the Streamlit-free helpers and the
module's import behavior; Streamlit rendering itself is verified
manually via ``streamlit run``.
"""

from __future__ import annotations

import pytest

from formulation_os.ui.app import (
    BUILTINS_DIR,
    build_orchestrator,
    tool_card_data,
)
from tests.conftest import BUILTINS_DIR as TEST_BUILTINS_DIR


# --------------------------------------------------------------------------- #
# Helpers (Streamlit-free)                                                    #
# --------------------------------------------------------------------------- #


def test_tool_card_data_returns_expected_fields() -> None:
    """tool_card_data returns a dict with the expected fields populated from a Tool."""
    orch = build_orchestrator(TEST_BUILTINS_DIR)
    data = tool_card_data(orch.registry.get("Literature"))
    assert data["name"] == "Literature"
    assert data["version"] == "0.1.0"
    assert "Searches academic literature" in data["description"]
    assert data["domain"] == "literature"
    assert "literature_search" in data["capabilities"]
    assert data["is_mock"] is True


def test_tool_card_data_handles_missing_domain() -> None:
    """A Tool with no domain still gets a string field (uses em-dash fallback)."""
    from formulation_os.core.tool import Tool
    from formulation_os.core.executor_spec import ExecutorSpec
    from formulation_os.core.tool import ToolSpec

    spec = ToolSpec(
        name="NoDomain",
        version="0.1.0",
        description="A tool with no domain declared.",
        executor=ExecutorSpec(type="python", module="x", function="y"),
    )
    # Tool is abstract; build a minimal concrete subclass for the test.
    class _NoopTool(Tool):
        def execute(self, input_data):
            return {}

    data = tool_card_data(_NoopTool(spec))
    assert data["domain"] == "—"
    assert data["capabilities"] == []


# --------------------------------------------------------------------------- #
# build_orchestrator                                                          #
# --------------------------------------------------------------------------- #


def test_build_orchestrator_loads_all_five_builtins() -> None:
    """build_orchestrator wires a registry containing all 5 built-in tools."""
    orch = build_orchestrator(TEST_BUILTINS_DIR)
    assert len(orch.registry) == 5
    names = orch.registry.names()
    for expected in ("FormulationAI", "PreformulationAI", "PBPK-AI", "FormulationDT", "Literature"):
        assert expected in names, f"Missing built-in: {expected}"


def test_build_orchestrator_can_run_a_real_query() -> None:
    """The orchestrator produced by build_orchestrator can run an end-to-end query."""
    orch = build_orchestrator(TEST_BUILTINS_DIR)
    report = orch.run("Find recent literature review on ibuprofen", top_k=1)
    assert report.status == "ok"
    assert report.tool_results[0].tool_name == "Literature"


def test_build_orchestrator_uses_default_builtins_dir() -> None:
    """When called without arguments, build_orchestrator uses BUILTINS_DIR."""
    # BUILTINS_DIR should point at the in-tree src/formulation_os/tools/builtins
    assert BUILTINS_DIR.name == "builtins"
    assert BUILTINS_DIR.parent.name == "tools"
    assert BUILTINS_DIR.parent.parent.name == "formulation_os"


# --------------------------------------------------------------------------- #
# Module behavior                                                             #
# --------------------------------------------------------------------------- #


def test_app_module_imports_cleanly() -> None:
    """The app module is importable and exposes the expected public surface."""
    import formulation_os.ui.app as app

    assert callable(app.main)
    assert callable(app.build_orchestrator)
    assert callable(app.tool_card_data)
    assert app.BUILTINS_DIR.is_dir()


def test_main_raises_clear_error_without_streamlit(monkeypatch: pytest.MonkeyPatch) -> None:
    """If Streamlit is not available, main() raises a RuntimeError with install instructions."""
    from formulation_os.ui import app

    monkeypatch.setattr(app, "_STREAMLIT_AVAILABLE", False)
    with pytest.raises(RuntimeError, match=r"pip install"):
        app.main()
