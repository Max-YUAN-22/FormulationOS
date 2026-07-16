"""Workflow Validator for scientific workflow verification.

This module implements workflow validation to check:
1. Dependency legality (no cycles, valid step references)
2. Input/output compatibility between steps
3. Missing required steps
4. Scientific constraints

This closes the loop: Planner → Workflow → Validator → Feedback
"""

from __future__ import annotations

from typing import Any, Literal

from formulation_os.planner.workflow_schema import WorkflowPlan, WorkflowStep
from formulation_os.registry.registry import ToolRegistry

__all__ = ["WorkflowValidator", "ValidationResult", "ValidationIssue"]


class ValidationIssue:
    """A single validation issue found in a workflow.

    Attributes:
        severity: "error" (blocks execution) or "warning" (advisory)
        step_id: The step where the issue was found (or None for workflow-level)
        issue_type: Category of the issue
        message: Human-readable description
        suggestion: Optional suggestion for fixing the issue
    """

    def __init__(
        self,
        severity: Literal["error", "warning"],
        issue_type: str,
        message: str,
        step_id: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        self.severity = severity
        self.step_id = step_id
        self.issue_type = issue_type
        self.message = message
        self.suggestion = suggestion

    def __repr__(self) -> str:
        step_info = f" at {self.step_id}" if self.step_id else ""
        return f"<ValidationIssue {self.severity}: {self.issue_type}{step_info}>"


class ValidationResult:
    """Result of workflow validation.

    Attributes:
        is_valid: True if no errors (warnings are okay)
        issues: List of validation issues found
        can_execute: Whether the workflow can be executed
    """

    def __init__(self) -> None:
        self.issues: list[ValidationIssue] = []

    @property
    def is_valid(self) -> bool:
        """True if no errors found (warnings are okay)."""
        return not any(issue.severity == "error" for issue in self.issues)

    @property
    def can_execute(self) -> bool:
        """Same as is_valid - workflow can execute if no errors."""
        return self.is_valid

    @property
    def errors(self) -> list[ValidationIssue]:
        """All error-level issues."""
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """All warning-level issues."""
        return [issue for issue in self.issues if issue.severity == "warning"]

    def add_error(
        self,
        issue_type: str,
        message: str,
        step_id: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        """Add an error-level issue."""
        self.issues.append(
            ValidationIssue("error", issue_type, message, step_id, suggestion)
        )

    def add_warning(
        self,
        issue_type: str,
        message: str,
        step_id: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        """Add a warning-level issue."""
        self.issues.append(
            ValidationIssue("warning", issue_type, message, step_id, suggestion)
        )


class WorkflowValidator:
    """Validates scientific workflows for correctness and completeness.

    This validator checks:
    - Dependency graph legality (no cycles, valid references)
    - Tool existence in registry
    - Input/output compatibility (future enhancement)
    - Missing required dependencies (future enhancement)

    Args:
        registry: Tool registry for validating tool names
    """

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def validate(self, workflow_plan: WorkflowPlan) -> ValidationResult:
        """Validate a complete workflow plan.

        Args:
            workflow_plan: The workflow to validate

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult()
        workflow = workflow_plan.get("workflow", [])

        if not workflow:
            result.add_error(
                "empty_workflow",
                "Workflow contains no steps",
                suggestion="Add at least one step to the workflow"
            )
            return result

        # Build step ID set for validation
        step_ids = {step["step_id"] for step in workflow}

        # Validate each step
        for step in workflow:
            self._validate_step(step, step_ids, result)

        # Check for dependency cycles
        self._check_cycles(workflow, result)

        return result

    def _validate_step(
        self,
        step: WorkflowStep,
        all_step_ids: set[str],
        result: ValidationResult,
    ) -> None:
        """Validate a single workflow step."""
        step_id = step.get("step_id")
        tool_name = step.get("tool")

        # Check tool exists
        if not tool_name:
            result.add_error(
                "missing_tool",
                f"Step {step_id} has no tool specified",
                step_id=step_id
            )
            return

        tool = self.registry.try_get(tool_name)
        if tool is None:
            result.add_error(
                "unknown_tool",
                f"Tool '{tool_name}' not found in registry",
                step_id=step_id,
                suggestion=f"Available tools: {', '.join(t.name for t in self.registry)}"
            )

        # Check dependencies reference valid steps
        depends_on = step.get("depends_on", [])
        for dep_id in depends_on:
            if dep_id not in all_step_ids:
                result.add_error(
                    "invalid_dependency",
                    f"Step {step_id} depends on non-existent step '{dep_id}'",
                    step_id=step_id
                )

    def _check_cycles(
        self,
        workflow: list[WorkflowStep],
        result: ValidationResult,
    ) -> None:
        """Check for dependency cycles in the workflow."""
        # Build adjacency list
        graph: dict[str, list[str]] = {}
        for step in workflow:
            step_id = step["step_id"]
            graph[step_id] = step.get("depends_on", [])

        # DFS-based cycle detection
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for step_id in graph:
            if step_id not in visited:
                if has_cycle(step_id):
                    result.add_error(
                        "dependency_cycle",
                        "Workflow contains a dependency cycle",
                        suggestion="Remove circular dependencies between steps"
                    )
                    return
