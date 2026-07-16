"""Enhanced Workflow Planner with Capability-Aware Planning.

This version reads tool metadata (capabilities, dependencies, constraints)
and uses them for intelligent workflow planning, moving from template
generation to reasoning-based planning.
"""

from __future__ import annotations

import json
from typing import Any

from formulation_os.llm.client import LLMClient
from formulation_os.planner.workflow_schema import WorkflowPlan
from formulation_os.registry.registry import ToolRegistry

__all__ = ["CapabilityAwarePlanner"]


def _extract_tool_metadata(tool: Any) -> dict[str, Any]:
    """Extract planning-relevant metadata from a Tool.

    Args:
        tool: Tool instance

    Returns:
        Dict with capabilities, dependencies, and hints
    """
    metadata: dict[str, Any] = {
        "name": tool.name,
        "description": tool.description or "",
        "capabilities": [],
        "domain": None,
        "dependencies": {},
        "keywords": [],
        "notes": ""
    }

    # Extract from spec if available
    spec_data = tool.spec.model_dump() if hasattr(tool, 'spec') else {}

    # Capabilities from semantics
    semantics = spec_data.get("semantics", {})
    if isinstance(semantics, dict):
        metadata["capabilities"] = semantics.get("capabilities", [])
        metadata["domain"] = semantics.get("domain")

    # Scientific dependencies
    sci_deps = spec_data.get("scientific_dependencies", {})
    if isinstance(sci_deps, dict):
        metadata["dependencies"] = {
            "upstream_required": sci_deps.get("upstream_capabilities_required", []),
            "upstream_optional": sci_deps.get("upstream_capabilities_optional", []),
            "rationale": sci_deps.get("rationale", "")
        }

    # Planning hints
    hints = spec_data.get("planning_hints", {})
    if isinstance(hints, dict):
        metadata["keywords"] = hints.get("keywords", [])
        metadata["notes"] = hints.get("notes", "")

    return metadata


_CAPABILITY_AWARE_SYSTEM_PROMPT = """You are an AI Formulation Scientist planning pharmaceutical R&D workflows.

Your task: Given a user query, design a scientifically sound workflow by:
1. Analyzing which tool CAPABILITIES match the query
2. Respecting DEPENDENCIES between tools
3. Explaining your REASONING for each step

Key principles:
- Choose tools based on their capabilities, not just names
- Respect upstream dependencies (required > optional)
- Different formulation types need different workflows
- Provide scientific rationale for each step

Respond with JSON matching the schema. Include clear justification."""


class CapabilityAwarePlanner:
    """Workflow planner that reasons about tool capabilities and dependencies.

    This planner reads tool metadata and uses it for intelligent planning,
    rather than following fixed templates.

    Args:
        registry: Tool registry
        client: LLM client
    """

    def __init__(self, registry: ToolRegistry, client: LLMClient) -> None:
        self.registry = registry
        self.client = client

    def plan_workflow(self, query: str) -> WorkflowPlan | None:
        """Generate capability-aware workflow plan.

        Args:
            query: User's natural language request

        Returns:
            WorkflowPlan with justified steps, or None if planning fails
        """
        # Extract metadata for all tools
        tools_metadata = []
        for tool in self.registry:
            metadata = _extract_tool_metadata(tool)
            tools_metadata.append(metadata)

        # Build enhanced user prompt with metadata
        user_prompt = self._build_prompt_with_metadata(query, tools_metadata)

        # Update schema hint to include justification
        schema_hint = """
{
  "workflow": [
    {
      "step_id": "step_1",
      "tool": "ToolName",
      "goal": "What this step achieves",
      "depends_on": [],
      "justification": "Why this tool and why now"
    }
  ],
  "rationale": "Overall workflow strategy"
}
"""

        try:
            raw_response = self.client.complete_json(
                _CAPABILITY_AWARE_SYSTEM_PROMPT,
                user_prompt,
                schema_hint
            )
        except Exception as e:
            print(f"LLM call failed: {e}")
            return None

        try:
            data = json.loads(raw_response)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"JSON parse failed: {e}")
            return None

        # Validate and filter
        if not isinstance(data, dict):
            return None

        workflow = data.get("workflow")
        if not isinstance(workflow, list):
            return None

        # Validate tool names
        validated_steps = []
        for step in workflow:
            if not isinstance(step, dict):
                continue

            tool_name = step.get("tool")
            if not tool_name or self.registry.try_get(tool_name) is None:
                continue

            validated_steps.append(step)

        if not validated_steps:
            return None

        return {
            "workflow": validated_steps,
            "rationale": data.get("rationale", "")
        }

    def _build_prompt_with_metadata(
        self,
        query: str,
        tools_metadata: list[dict[str, Any]]
    ) -> str:
        """Build enhanced prompt including tool capabilities and dependencies."""
        prompt_parts = [f"User Query: {query}", "", "Available Tools:"]

        for tool_meta in tools_metadata:
            prompt_parts.append(f"\n**{tool_meta['name']}**")
            prompt_parts.append(f"Description: {tool_meta['description']}")

            if tool_meta['capabilities']:
                caps = ', '.join(tool_meta['capabilities'])
                prompt_parts.append(f"Capabilities: {caps}")

            deps = tool_meta['dependencies']
            if deps.get('upstream_required'):
                prompt_parts.append(
                    f"Requires: {', '.join(deps['upstream_required'])}"
                )
            if deps.get('upstream_optional'):
                prompt_parts.append(
                    f"Benefits from: {', '.join(deps['upstream_optional'])}"
                )

            if deps.get('rationale'):
                prompt_parts.append(f"Note: {deps['rationale']}")

        prompt_parts.append("\nDesign a workflow that:")
        prompt_parts.append("1. Uses appropriate tool capabilities")
        prompt_parts.append("2. Respects dependencies")
        prompt_parts.append("3. Includes justification for each step")

        return "\n".join(prompt_parts)
