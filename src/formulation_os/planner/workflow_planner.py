"""GPT-based Workflow Planner.

This planner uses an LLM to generate a complete workflow DAG from a
natural-language query. Unlike the LLMPlanner (which only selects tools),
this planner produces a structured workflow with dependencies.

Example:
    Query: "Design an oral formulation for Drug X"

    Output:
    {
      "workflow": [
        {"step_id": "step_1", "tool": "PreformulationAI",
         "goal": "Predict solubility", "depends_on": []},
        {"step_id": "step_2", "tool": "FormulationAI",
         "goal": "Recommend formulation", "depends_on": ["step_1"]},
        {"step_id": "step_3", "tool": "PBPK",
         "goal": "Estimate bioavailability", "depends_on": ["step_2"]}
      ],
      "rationale": "Sequential pipeline for oral formulation design"
    }
"""

from __future__ import annotations

import json
from typing import Any

from formulation_os.llm.client import LLMClient
from formulation_os.planner.workflow_schema import (
    WORKFLOW_SCHEMA_HINT,
    WorkflowPlan,
)
from formulation_os.registry.registry import ToolRegistry

__all__ = ["WorkflowPlanner"]


_SYSTEM_PROMPT = """You are a workflow planner for FormulationOS, a pharmaceutical research operating system.

Given a user query about drug formulation, design a complete workflow that orchestrates multiple scientific tools.

Available tools:
- PreformulationAI: Predicts physicochemical properties (solubility, stability, etc.)
- FormulationAI: Recommends formulation strategies and excipients
- FormulationDT: Simulates dissolution profiles (digital twin)
- PBPK: Predicts pharmacokinetics and bioavailability
- Literature: Searches scientific literature

Your task:
1. Analyze the user's request
2. Select relevant tools
3. Define the execution order and dependencies
4. Each step should have a clear goal
5. Use "depends_on" to specify which steps must complete first

Guidelines:
- Start with PreformulationAI if properties are needed
- FormulationAI typically depends on PreformulationAI
- PBPK typically comes after FormulationAI
- FormulationDT can run in parallel with PBPK
- Use Literature for background research

Respond ONLY with valid JSON matching the schema - no prose, no markdown."""


class WorkflowPlanner:
    """LLM-based workflow planner that generates DAG workflows.

    Args:
        registry: Tool registry for validation
        client: LLM client for generating workflows
    """

    def __init__(self, registry: ToolRegistry, client: LLMClient) -> None:
        self.registry = registry
        self.client = client

    def plan_workflow(self, query: str) -> WorkflowPlan | None:
        """Generate a workflow plan from a natural language query.

        Args:
            query: User's natural language request

        Returns:
            WorkflowPlan dict with workflow steps and rationale,
            or None if planning fails
        """
        # Get available tool names for context
        available_tools = [tool.name for tool in self.registry]

        user_prompt = f"""User Query: {query}

Available tools: {', '.join(available_tools)}

Generate a workflow plan that addresses this query."""

        try:
            raw_response = self.client.complete_json(
                _SYSTEM_PROMPT,
                user_prompt,
                WORKFLOW_SCHEMA_HINT
            )
        except Exception as e:
            # LLM call failed - return None
            print(f"LLM call failed: {e}")
            return None

        try:
            data = json.loads(raw_response)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"JSON parse failed: {e}")
            return None

        # Basic validation
        if not isinstance(data, dict):
            return None

        workflow = data.get("workflow")
        if not isinstance(workflow, list):
            return None

        # Validate tool names exist in registry
        validated_steps = []
        for step in workflow:
            if not isinstance(step, dict):
                continue

            tool_name = step.get("tool")
            if not tool_name or self.registry.try_get(tool_name) is None:
                # Skip steps with invalid tool names
                continue

            validated_steps.append(step)

        if not validated_steps:
            return None

        return {
            "workflow": validated_steps,
            "rationale": data.get("rationale", "")
        }
