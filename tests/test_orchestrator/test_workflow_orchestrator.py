"""Tests for WorkflowOrchestrator (DAG execution)."""

from __future__ import annotations

import pytest

from formulation_os.orchestrator.workflow_orchestrator import WorkflowOrchestrator
from formulation_os.planner.workflow_schema import WorkflowPlan
from formulation_os.registry import ToolRegistry
from tests.conftest import BUILTINS_DIR


@pytest.fixture
def registry() -> ToolRegistry:
    """Tool registry with builtin tools."""
    return ToolRegistry(BUILTINS_DIR).load_all()


@pytest.fixture
def orchestrator(registry: ToolRegistry) -> WorkflowOrchestrator:
    """WorkflowOrchestrator instance."""
    return WorkflowOrchestrator(registry)


def test_workflow_orchestrator_single_step(
    orchestrator: WorkflowOrchestrator,
) -> None:
    """Test executing a single-step workflow."""
    workflow_plan: WorkflowPlan = {
        "workflow": [
            {
                "step_id": "step_1",
                "tool": "PreformulationAI",
                "goal": "Predict properties",
                "depends_on": [],
            }
        ],
        "rationale": "Single step test",
    }

    report = orchestrator.execute_workflow(
        workflow_plan,
        "Test query",
        initial_inputs={"drug_name": "Ibuprofen"}
    )

    assert report.status == "ok"
    assert len(report.tool_results) == 1
    assert report.tool_results[0].tool_name == "PreformulationAI"
    assert report.tool_results[0].status == "ok"


def test_workflow_orchestrator_sequential(
    orchestrator: WorkflowOrchestrator,
) -> None:
    """Test executing a sequential workflow."""
    workflow_plan: WorkflowPlan = {
        "workflow": [
            {
                "step_id": "step_1",
                "tool": "PreformulationAI",
                "goal": "Predict properties",
                "depends_on": [],
            },
            {
                "step_id": "step_2",
                "tool": "FormulationAI",
                "goal": "Recommend formulation",
                "depends_on": ["step_1"],
            },
        ],
        "rationale": "Sequential pipeline",
    }

    report = orchestrator.execute_workflow(
        workflow_plan,
        "Design oral formulation",
        initial_inputs={"drug_name": "Aspirin", "dosage_form": "tablet"}
    )

    assert report.status == "ok"
    assert len(report.tool_results) == 2
    assert report.tool_results[0].tool_name == "PreformulationAI"
    assert report.tool_results[1].tool_name == "FormulationAI"
    # Both should succeed
    assert all(r.status == "ok" for r in report.tool_results)


def test_workflow_orchestrator_invalid_tool(
    orchestrator: WorkflowOrchestrator,
) -> None:
    """Test handling of invalid tool names."""
    workflow_plan: WorkflowPlan = {
        "workflow": [
            {
                "step_id": "step_1",
                "tool": "InvalidTool",
                "goal": "Do something",
                "depends_on": [],
            }
        ],
        "rationale": "Test invalid tool",
    }

    report = orchestrator.execute_workflow(
        workflow_plan,
        "Test query",
    )

    assert report.status == "error"
    assert len(report.tool_results) == 1
    assert report.tool_results[0].status == "error"
    assert "not found" in report.tool_results[0].error


def test_workflow_orchestrator_empty_workflow(
    orchestrator: WorkflowOrchestrator,
) -> None:
    """Test handling of empty workflow."""
    workflow_plan: WorkflowPlan = {
        "workflow": [],
        "rationale": "Empty workflow",
    }

    report = orchestrator.execute_workflow(workflow_plan, "Test query")

    assert report.status == "no_match"
    assert len(report.tool_results) == 0
