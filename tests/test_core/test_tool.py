"""Tests for the :class:`Tool` abstract base class."""

from __future__ import annotations

import pytest

from formulation_os.core.executor_spec import ExecutorSpec
from formulation_os.core.tool import (
    STSError,
    Tool,
    ToolExecutionError,
    ToolSpec,
)


def _spec_with_executor(executor_type: str = "python") -> ToolSpec:
    return ToolSpec.model_validate(
        {
            "name": "Demo",
            "version": "0.1.0",
            "description": "A demo.",
            "executor": {
                "type": executor_type,
                "module": "demo.backend",
                "function": "run",
            },
        }
    )


class _ConcreteTool(Tool):
    def execute(self, input_data):
        return {"echo": input_data}


def test_tool_metadata_proxies() -> None:
    spec = _spec_with_executor()
    tool = _ConcreteTool(spec)
    assert tool.name == "Demo"
    assert tool.version == "0.1.0"
    assert tool.description == "A demo."
    assert tool.input_schema == {"type": "object"}
    assert tool.output_schema == {"type": "object"}
    assert tool.capabilities == []
    assert tool.planning_hints.examples == []


def test_tool_to_card_omits_empty_sections() -> None:
    spec = _spec_with_executor()
    tool = _ConcreteTool(spec)
    card = tool.to_card()
    assert card["name"] == "Demo"
    assert card["description"] == "A demo."
    assert card["capabilities"] == []
    assert "examples" not in card  # empty -> omitted
    assert "keywords" not in card


def test_tool_to_card_includes_examples_and_keywords() -> None:
    spec = ToolSpec.model_validate(
        {
            "name": "Demo",
            "description": "A demo.",
            "executor": {"type": "python", "module": "demo.backend", "function": "run"},
            "planning_hints": {
                "examples": [{"input": {"x": 1}, "output_summary": "y"}],
                "keywords": ["k1", "k2"],
            },
        }
    )
    tool = _ConcreteTool(spec)
    card = tool.to_card()
    assert card["examples"] == [{"input": {"x": 1}, "output_summary": "y"}]
    assert card["keywords"] == ["k1", "k2"]


def test_tool_to_llm_description_shape() -> None:
    spec = ToolSpec.model_validate(
        {
            "name": "Demo",
            "description": "A demo.",
            "executor": {"type": "python", "module": "demo.backend", "function": "run"},
            "input_schema": {"type": "object", "properties": {"x": {"type": "integer"}}},
            "planning_hints": {"examples": [{"input": {"x": 1}, "output_summary": "y"}]},
        }
    )
    tool = _ConcreteTool(spec)
    desc = tool.to_llm_description()
    assert desc["name"] == "Demo"
    assert desc["description"] == "A demo."
    assert desc["parameters"]["properties"]["x"]["type"] == "integer"
    assert desc["examples"] == [{"input": {"x": 1}, "output_summary": "y"}]


def test_tool_execute_must_be_implemented() -> None:
    spec = _spec_with_executor()
    with pytest.raises(TypeError, match="abstract"):
        Tool(spec)


def test_tool_repr() -> None:
    spec = _spec_with_executor()
    tool = _ConcreteTool(spec)
    r = repr(tool)
    assert "Demo" in r and "0.1.0" in r and "mock=False" in r


def test_tool_execution_error_message() -> None:
    err = ToolExecutionError("MyTool", "boom", cause=ValueError("inner"))
    assert "[MyTool]" in str(err)
    assert "boom" in str(err)
    assert err.tool_name == "MyTool"
    assert isinstance(err.cause, ValueError)
    assert isinstance(err, STSError)