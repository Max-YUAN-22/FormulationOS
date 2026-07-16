"""Tests for WorkflowPlanner (GPT-based workflow generation)."""

from __future__ import annotations

import json

import pytest

from formulation_os.llm.client import MockLLMClient
from formulation_os.planner.workflow_planner import WorkflowPlanner
from formulation_os.registry import ToolRegistry
from tests.conftest import BUILTINS_DIR


@pytest.fixture
def registry() -> ToolRegistry:
    """Tool registry with builtin tools."""
    return ToolRegistry(BUILTINS_DIR).load_all()


def test_workflow_planner_basic(registry: ToolRegistry) -> None:
    """Test basic workflow generation."""
    # Mock LLM response with a valid workflow
    mock_response = json.dumps({
        "workflow": [
            {
                "step_id": "step_1",
                "tool": "PreformulationAI",
                "goal": "Predict solubility",
                "depends_on": []
            },
            {
                "step_id": "step_2",
                "tool": "FormulationAI",
                "goal": "Recommend formulation",
                "depends_on": ["step_1"]
            }
        ],
        "rationale": "Sequential pipeline for oral formulation"
    })

    client = MockLLMClient(response=mock_response)
    planner = WorkflowPlanner(registry, client)

    plan = planner.plan_workflow("Design an oral formulation for ibuprofen")

    assert plan is not None
    assert "workflow" in plan
    assert "rationale" in plan
    assert len(plan["workflow"]) == 2
    assert plan["workflow"][0]["tool"] == "PreformulationAI"
    assert plan["workflow"][1]["depends_on"] == ["step_1"]


def test_workflow_planner_invalid_tool(registry: ToolRegistry) -> None:
    """Test that invalid tool names are filtered out."""
    mock_response = json.dumps({
        "workflow": [
            {
                "step_id": "step_1",
                "tool": "InvalidTool",
                "goal": "Do something",
                "depends_on": []
            },
            {
                "step_id": "step_2",
                "tool": "FormulationAI",
                "goal": "Recommend formulation",
                "depends_on": ["step_1"]
            }
        ],
        "rationale": "Test workflow"
    })

    client = MockLLMClient(response=mock_response)
    planner = WorkflowPlanner(registry, client)

    plan = planner.plan_workflow("Test query")

    # Invalid tool should be filtered out
    assert plan is not None
    assert len(plan["workflow"]) == 1
    assert plan["workflow"][0]["tool"] == "FormulationAI"


def test_workflow_planner_llm_failure(registry: ToolRegistry) -> None:
    """Test graceful handling of LLM failures."""
    def failing_response(system: str, user: str, schema: str) -> str:
        raise RuntimeError("LLM API failed")

    client = MockLLMClient(response_fn=failing_response)
    planner = WorkflowPlanner(registry, client)

    plan = planner.plan_workflow("Test query")

    # Should return None on failure, not crash
    assert plan is None


def test_workflow_planner_invalid_json(registry: ToolRegistry) -> None:
    """Test handling of invalid JSON response."""
    client = MockLLMClient(response="not valid json {")
    planner = WorkflowPlanner(registry, client)

    plan = planner.plan_workflow("Test query")

    assert plan is None


def test_workflow_planner_complex_dag(registry: ToolRegistry) -> None:
    """Test complex DAG with parallel branches."""
    mock_response = json.dumps({
        "workflow": [
            {
                "step_id": "step_1",
                "tool": "PreformulationAI",
                "goal": "Predict properties",
                "depends_on": []
            },
            {
                "step_id": "step_2",
                "tool": "FormulationAI",
                "goal": "Design formulation",
                "depends_on": ["step_1"]
            },
            {
                "step_id": "step_3",
                "tool": "FormulationDT",
                "goal": "Simulate dissolution",
                "depends_on": ["step_2"]
            },
            {
                "step_id": "step_4",
                "tool": "PBPK-AI",
                "goal": "Predict PK",
                "depends_on": ["step_2"]
            }
        ],
        "rationale": "Parallel testing of dissolution and PK"
    })

    client = MockLLMClient(response=mock_response)
    planner = WorkflowPlanner(registry, client)

    plan = planner.plan_workflow("Complete formulation analysis")

    assert plan is not None
    assert len(plan["workflow"]) == 4
    # Steps 3 and 4 both depend on step_2, can run in parallel
    assert plan["workflow"][2]["depends_on"] == ["step_2"]
    assert plan["workflow"][3]["depends_on"] == ["step_2"]
