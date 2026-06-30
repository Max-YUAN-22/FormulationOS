"""Tests for :func:`formulation_os.tools.loader.load_tool`."""

from __future__ import annotations

from pathlib import Path

import pytest

from formulation_os.core.tool import Tool, ToolSpecValidationError
from formulation_os.tools.loader import load_tool
from tests.conftest import BUILTINS_DIR


@pytest.mark.parametrize(
    "tool_name",
    ["formulation_ai", "preformulation_ai", "pbpk_ai", "formulation_dt", "literature"],
)
def test_load_each_builtin(tool_name: str) -> None:
    tool = load_tool(BUILTINS_DIR / tool_name)
    assert isinstance(tool, Tool)
    assert tool.name
    assert tool.version
    assert tool.description
    assert isinstance(tool.input_schema, dict)
    assert isinstance(tool.output_schema, dict)


def test_load_builtin_execute_returns_dict() -> None:
    tool = load_tool(BUILTINS_DIR / "formulation_ai")
    out = tool.execute(
        {"drug_name": "Ibuprofen", "target_dose_mg": 200, "dosage_form": "tablet"}
    )
    assert isinstance(out, dict)
    assert out["drug_name"] == "Ibuprofen"
    assert "excipients" in out


def test_load_missing_directory() -> None:
    with pytest.raises(FileNotFoundError):
        load_tool(BUILTINS_DIR / "nonexistent_tool")


def test_load_invalid_yaml(tmp_path: Path) -> None:
    bad = tmp_path / "tool.yaml"
    bad.write_text("name: Demo\nexecutor:\n  type: python\n")
    with pytest.raises(ToolSpecValidationError):
        load_tool(tmp_path)


def test_load_non_mapping_yaml(tmp_path: Path) -> None:
    (tmp_path / "tool.yaml").write_text("- a\n- b\n")
    with pytest.raises(ToolSpecValidationError):
        load_tool(tmp_path)


def test_load_unknown_executor_type(tmp_path: Path) -> None:
    (tmp_path / "tool.yaml").write_text(
        "name: Demo\n"
        "description: x\n"
        "executor:\n"
        "  type: quantum\n"
    )
    with pytest.raises(ToolSpecValidationError):
        load_tool(tmp_path)