"""Workflow JSON schema for GPT Planner.

This module defines the schema for workflow plans produced by the LLM.
The workflow is represented as a DAG (Directed Acyclic Graph) where:
- Each node is a tool invocation
- Edges represent data dependencies between tools
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

__all__ = [
    "WorkflowStep",
    "WorkflowPlan",
    "StepJustification",
    "WORKFLOW_SCHEMA_HINT",
]


class StepJustification(TypedDict, total=False):
    """Structured justification for a workflow step.

    Attributes:
        goal: What this step aims to achieve
        expected_output: What data/results this step produces
        scientific_rationale: Why this step is necessary at this point
        confidence: Planner's confidence in this choice (high/medium/low)
    """

    goal: str
    expected_output: str
    scientific_rationale: str
    confidence: Literal["high", "medium", "low"]


class WorkflowStep(TypedDict, total=False):
    """A single step in the workflow.

    Attributes:
        tool: Name of the tool to invoke (e.g., "PreformulationAI").
        goal: Human-readable description of what this step achieves.
        depends_on: List of step IDs that must complete before this step.
                   Use [] for steps that can run immediately.
        step_id: Unique identifier for this step (e.g., "step_1").
        justification: Scientific reasoning for why this tool is needed at this point.
                      (Optional but recommended for explainability)
    """

    tool: str
    goal: str
    depends_on: list[str]
    step_id: str
    justification: StepJustification | str  # Can be structured or simple string


class WorkflowPlan(TypedDict):
    """Complete workflow plan returned by the LLM.

    Attributes:
        workflow: List of workflow steps in topological order.
        rationale: Brief explanation of the workflow strategy.
    """

    workflow: list[WorkflowStep]
    rationale: str


# Schema hint given to the LLM to guide JSON structure
WORKFLOW_SCHEMA_HINT = """
{
  "workflow": [
    {
      "step_id": "step_1",
      "tool": "PreformulationAI",
      "goal": "Predict physicochemical properties",
      "depends_on": [],
      "justification": {
        "goal": "Determine solubility and permeability",
        "expected_output": "Solubility (mg/mL), BCS class, permeability",
        "scientific_rationale": "Solubility determines formulation strategy. BCS class II needs solubility enhancement.",
        "confidence": "high"
      }
    },
    {
      "step_id": "step_2",
      "tool": "FormulationAI",
      "goal": "Design formulation strategy",
      "depends_on": ["step_1"],
      "justification": {
        "goal": "Select excipients based on drug properties",
        "expected_output": "Excipient list with ratios",
        "scientific_rationale": "BCS class from step_1 informs excipient selection",
        "confidence": "high"
      }
    }
  ],
  "rationale": "Sequential workflow: properties inform formulation design"
}
"""
