"""Tests for :class:`ToolRegistry`."""

from __future__ import annotations

import pytest

from formulation_os.core.tool import Tool
from formulation_os.registry import ToolRegistry
from formulation_os.tools import load_tool
from tests.conftest import BUILTINS_DIR


def test_registry_loads_all_five_builtins() -> None:
    reg = ToolRegistry(BUILTINS_DIR).load_all()
    assert len(reg) == 5
    for name in ("FormulationAI", "PreformulationAI", "PBPK-AI", "FormulationDT", "Literature"):
        assert name in reg


def test_registry_get_returns_correct_tool() -> None:
    reg = ToolRegistry(BUILTINS_DIR).load_all()
    tool = reg.get("FormulationAI")
    assert isinstance(tool, Tool)
    assert tool.name == "FormulationAI"


def test_registry_get_unknown_raises_keyerror() -> None:
    reg = ToolRegistry(BUILTINS_DIR).load_all()
    with pytest.raises(KeyError) as excinfo:
        reg.get("NonexistentTool")
    assert "NonexistentTool" in str(excinfo.value)
    assert "FormulationAI" in str(excinfo.value)  # error mentions known tools


def test_registry_try_get_returns_none_for_unknown() -> None:
    reg = ToolRegistry(BUILTINS_DIR).load_all()
    assert reg.try_get("NonexistentTool") is None
    assert reg.try_get("FormulationAI") is not None


def test_registry_list_returns_all_tools() -> None:
    reg = ToolRegistry(BUILTINS_DIR).load_all()
    tools = reg.list()
    assert len(tools) == 5
    assert all(isinstance(t, Tool) for t in tools)


def test_registry_names_returns_sorted() -> None:
    reg = ToolRegistry(BUILTINS_DIR).load_all()
    names = reg.names()
    assert names == sorted(names)
    assert "FormulationAI" in names


def test_registry_list_metadata_returns_cards() -> None:
    reg = ToolRegistry(BUILTINS_DIR).load_all()
    cards = reg.list_metadata()
    assert len(cards) == 5
    for card in cards:
        assert "name" in card
        assert "description" in card
        assert "capabilities" in card


def test_registry_register_in_memory() -> None:
    reg = ToolRegistry()  # no tools_dir
    assert len(reg) == 0
    tool = load_tool(BUILTINS_DIR / "formulation_ai")
    reg.register(tool)
    assert "FormulationAI" in reg
    assert len(reg) == 1
    assert reg.get("FormulationAI") is tool


def test_registry_register_replaces_existing() -> None:
    reg = ToolRegistry(BUILTINS_DIR).load_all()
    new_tool = load_tool(BUILTINS_DIR / "formulation_ai")
    reg.register(new_tool)  # same name
    assert len(reg) == 5  # not 6


def test_registry_load_all_without_dir_raises() -> None:
    reg = ToolRegistry()
    with pytest.raises(ValueError):
        reg.load_all()


def test_registry_iter_yields_tools() -> None:
    reg = ToolRegistry(BUILTINS_DIR).load_all()
    tools = list(reg)
    assert len(tools) == 5
    assert all(isinstance(t, Tool) for t in tools)


def test_registry_contains_only_strings() -> None:
    reg = ToolRegistry(BUILTINS_DIR).load_all()
    assert "FormulationAI" in reg
    assert 42 not in reg  # type: ignore[operator]


def test_registry_empty_when_no_yaml_subdirs(tmp_path) -> None:
    # Create subdirs without tool.yaml
    (tmp_path / "not_a_tool").mkdir()
    (tmp_path / "also_not_a_tool").mkdir()
    reg = ToolRegistry(tmp_path).load_all()
    assert len(reg) == 0