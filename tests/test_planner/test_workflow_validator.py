"""Tests for WorkflowValidator."""

import pytest

from formulation_os.planner.workflow_schema import WorkflowPlan
from formulation_os.planner.workflow_validator import WorkflowValidator
from formulation_os.registry import ToolRegistry
from tests.conftest import BUILTINS_DIR


@pytest.fixture
def registry() -> ToolRegistry:
    """Tool registry with builtin tools."""
    return ToolRegistry(BUILTINS_DIR).load_all()


@pytest.fixture
def validator(registry: ToolRegistry) -> WorkflowValidator:
    """WorkflowValidator instance."""
    return WorkflowValidator(registry)


def test_validator_valid_workflow(validator: WorkflowValidator) -> None:
    """Test validation of a valid workflow."""
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
                "goal": "Design formulation",
                "depends_on": ["step_1"],
            }
        ],
        "rationale": "Test workflow"
    }

    result = validator.validate(workflow_plan)

    assert result.is_valid
    assert result.can_execute
    assert len(result.errors) == 0


def test_validator_unknown_tool(validator: WorkflowValidator) -> None:
    """Test detection of unknown tool."""
    workflow_plan: WorkflowPlan = {
        "workflow": [
            {
                "step_id": "step_1",
                "tool": "UnknownTool",
                "goal": "Do something",
                "depends_on": [],
            }
        ],
        "rationale": "Test"
    }

    result = validator.validate(workflow_plan)

    assert not result.is_valid
    assert len(result.errors) == 1
    assert result.errors[0].issue_type == "unknown_tool"
    assert "UnknownTool" in result.errors[0].message


def test_validator_invalid_dependency(validator: WorkflowValidator) -> None:
    """Test detection of invalid dependency reference."""
    workflow_plan: WorkflowPlan = {
        "workflow": [
            {
                "step_id": "step_1",
                "tool": "FormulationAI",
                "goal": "Design",
                "depends_on": ["step_99"],  # Non-existent step
            }
        ],
        "rationale": "Test"
    }

    result = validator.validate(workflow_plan)

    assert not result.is_valid
    assert len(result.errors) == 1
    assert result.errors[0].issue_type == "invalid_dependency"


def test_validator_cycle_detection(validator: WorkflowValidator) -> None:
    """Test detection of dependency cycles."""
    workflow_plan: WorkflowPlan = {
        "workflow": [
            {
                "step_id": "step_1",
                "tool": "PreformulationAI",
                "goal": "A",
                "depends_on": ["step_2"],
            },
            {
                "step_id": "step_2",
                "tool": "FormulationAI",
                "goal": "B",
                "depends_on": ["step_1"],  # Cycle!
            }
        ],
        "rationale": "Cyclic workflow"
    }

    result = validator.validate(workflow_plan)

    assert not result.is_valid
    assert len(result.errors) == 1
    assert result.errors[0].issue_type == "dependency_cycle"


def test_validator_empty_workflow(validator: WorkflowValidator) -> None:
    """Test detection of empty workflow."""
    workflow_plan: WorkflowPlan = {
        "workflow": [],
        "rationale": "Empty"
    }

    result = validator.validate(workflow_plan)

    assert not result.is_valid
    assert len(result.errors) == 1
    assert result.errors[0].issue_type == "empty_workflow"
