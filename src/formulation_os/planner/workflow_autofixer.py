"""Automatic Workflow Repair - Fix common workflow validation errors.

This module automatically repairs invalid workflows by:
- Adding missing dependencies
- Replacing unavailable tools with alternatives
- Fixing circular dependencies
- Completing incomplete workflow structures

Example:
    fixer = WorkflowAutoFixer(registry, validator)
    fixed_plan, changes = fixer.fix(invalid_plan)

    if fixed_plan:
        print(f"Fixed workflow with {len(changes)} changes")
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from formulation_os.planner.workflow_schema import WorkflowPlan, WorkflowStep
from formulation_os.planner.workflow_validator import WorkflowValidator, ValidationIssue
from formulation_os.registry.registry import ToolRegistry

__all__ = ["WorkflowAutoFixer", "RepairAction"]


@dataclass
class RepairAction:
    """A repair action applied to the workflow.

    Attributes:
        action_type: Type of repair (replace_tool, add_dependency, remove_step, etc.)
        target: Step ID or tool name affected
        description: Human-readable description of the change
        details: Additional details about the repair
    """

    action_type: str
    target: str
    description: str
    details: dict[str, Any]


class WorkflowAutoFixer:
    """Automatically repair invalid workflows.

    Args:
        registry: Tool registry to check tool availability
        validator: Workflow validator for checking validity
        max_iterations: Maximum repair attempts (default 3)
    """

    def __init__(
        self,
        registry: ToolRegistry,
        validator: WorkflowValidator,
        max_iterations: int = 3,
    ):
        self.registry = registry
        self.validator = validator
        self.max_iterations = max_iterations

    def fix(
        self, plan: WorkflowPlan
    ) -> tuple[WorkflowPlan | None, list[RepairAction]]:
        """Attempt to fix an invalid workflow.

        Args:
            plan: The workflow plan to fix

        Returns:
            (fixed_plan, repair_actions) if successful, (None, []) if unfixable
        """
        current_plan = plan
        all_actions: list[RepairAction] = []

        for iteration in range(self.max_iterations):
            validation_result = self.validator.validate(current_plan["workflow"])

            if validation_result.is_valid:
                # Successfully fixed!
                return current_plan, all_actions

            # Try to fix errors
            fixed_plan, actions = self._apply_repairs(
                current_plan, validation_result.errors
            )

            if not actions:
                # No repairs possible
                return None, all_actions

            all_actions.extend(actions)
            current_plan = fixed_plan

        # Max iterations reached without success
        return None, all_actions

    def _apply_repairs(
        self,
        plan: WorkflowPlan,
        errors: list[ValidationIssue],
    ) -> tuple[WorkflowPlan, list[RepairAction]]:
        """Apply repairs for validation errors.

        Returns:
            (repaired_plan, actions_taken)
        """
        workflow = list(plan["workflow"])  # Make a copy
        actions: list[RepairAction] = []

        for error in errors:
            if error.issue_type == "unknown_tool":
                # Try to replace with alternative tool
                action = self._replace_tool(workflow, error)
                if action:
                    actions.append(action)

            elif error.issue_type == "invalid_dependency":
                # Fix dependency reference
                action = self._fix_dependency(workflow, error)
                if action:
                    actions.append(action)

            elif error.issue_type == "circular_dependency":
                # Break cycle by removing problematic dependency
                action = self._break_cycle(workflow, error)
                if action:
                    actions.append(action)

            elif error.issue_type == "missing_step_id":
                # Add generated step ID
                action = self._add_step_id(workflow, error)
                if action:
                    actions.append(action)

        if actions:
            return {"workflow": workflow, "rationale": plan.get("rationale", "")}, actions
        else:
            return plan, []

    def _replace_tool(
        self, workflow: list[WorkflowStep], error: ValidationIssue
    ) -> RepairAction | None:
        """Replace an unknown tool with an alternative."""
        # Extract step with unknown tool
        for step in workflow:
            if step.get("tool") == error.message.split("'")[1]:
                unknown_tool = step["tool"]

                # Try to find alternative
                alternative = self._find_alternative_tool(unknown_tool)

                if alternative:
                    step["tool"] = alternative
                    return RepairAction(
                        action_type="replace_tool",
                        target=step.get("step_id", "unknown"),
                        description=f"Replaced '{unknown_tool}' with '{alternative}'",
                        details={"old_tool": unknown_tool, "new_tool": alternative},
                    )

        return None

    def _find_alternative_tool(self, unknown_tool: str) -> str | None:
        """Find an alternative tool based on name similarity."""
        available_tools = [tool.name for tool in self.registry]

        # Simple heuristics
        unknown_lower = unknown_tool.lower()

        for tool_name in available_tools:
            tool_lower = tool_name.lower()

            # Check if they share significant parts of the name
            if (
                unknown_lower in tool_lower
                or tool_lower in unknown_lower
                or unknown_lower.replace("-", "") == tool_lower.replace("-", "")
            ):
                return tool_name

        return None

    def _fix_dependency(
        self, workflow: list[WorkflowStep], error: ValidationIssue
    ) -> RepairAction | None:
        """Fix an invalid dependency reference."""
        # Extract step ID and invalid dependency from error message
        parts = error.message.split("'")
        if len(parts) >= 4:
            step_id = parts[1]
            invalid_dep = parts[3]

            # Remove the invalid dependency
            for step in workflow:
                if step.get("step_id") == step_id:
                    deps = step.get("depends_on", [])
                    if invalid_dep in deps:
                        deps.remove(invalid_dep)
                        return RepairAction(
                            action_type="remove_dependency",
                            target=step_id,
                            description=f"Removed invalid dependency '{invalid_dep}'",
                            details={"removed_dependency": invalid_dep},
                        )

        return None

    def _break_cycle(
        self, workflow: list[WorkflowStep], error: ValidationIssue
    ) -> RepairAction | None:
        """Break a circular dependency by removing one dependency."""
        # Extract cycle information from error message
        # For simplicity, remove the last dependency that creates the cycle
        if "cycle" in error.message.lower():
            # Find the last step and remove one of its dependencies
            if workflow:
                last_step = workflow[-1]
                deps = last_step.get("depends_on", [])
                if deps:
                    removed_dep = deps.pop()
                    return RepairAction(
                        action_type="break_cycle",
                        target=last_step.get("step_id", "unknown"),
                        description=f"Removed dependency '{removed_dep}' to break cycle",
                        details={"removed_dependency": removed_dep},
                    )

        return None

    def _add_step_id(
        self, workflow: list[WorkflowStep], error: ValidationIssue
    ) -> RepairAction | None:
        """Add a missing step ID."""
        for i, step in enumerate(workflow):
            if "step_id" not in step or not step["step_id"]:
                step_id = f"step_{i + 1}"
                step["step_id"] = step_id
                return RepairAction(
                    action_type="add_step_id",
                    target=step_id,
                    description=f"Added missing step ID: {step_id}",
                    details={"step_index": i},
                )

        return None
