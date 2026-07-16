"""Workflow Orchestrator for DAG execution.

This orchestrator executes workflows with dependencies (DAG structure)
planned by the WorkflowPlanner. Unlike the basic Orchestrator which
executes tools sequentially, this orchestrator:

1. Respects tool dependencies (depends_on)
2. Executes tools in topological order
3. Passes outputs between dependent tools
4. Supports parallel execution of independent tools (future)
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Literal

from formulation_os.core.tool import Tool
from formulation_os.orchestrator.orchestrator import InputResolver, StubInputResolver
from formulation_os.planner.workflow_schema import WorkflowPlan, WorkflowStep
from formulation_os.registry.registry import ToolRegistry
from formulation_os.report.report import Report, ToolResult

__all__ = ["WorkflowOrchestrator"]


class WorkflowOrchestrator:
    """Orchestrates workflow execution with DAG dependencies.

    Args:
        registry: Tool registry for resolving tool names
        input_resolver: Optional input resolver for generating tool inputs
    """

    def __init__(
        self,
        registry: ToolRegistry,
        input_resolver: InputResolver | None = None,
    ) -> None:
        self.registry = registry
        self.input_resolver: InputResolver = input_resolver or StubInputResolver()

    def execute_workflow(
        self,
        workflow_plan: WorkflowPlan,
        query: str,
        initial_inputs: dict[str, Any] | None = None,
    ) -> Report:
        """Execute a complete workflow plan.

        Args:
            workflow_plan: The workflow plan from WorkflowPlanner
            query: Original user query
            initial_inputs: Optional initial inputs (e.g., drug_name)

        Returns:
            Report with all tool results
        """
        initial_inputs = initial_inputs or {}
        workflow = workflow_plan["workflow"]

        if not workflow:
            return Report(
                query=query,
                tool_results=[],
                produced_at=datetime.now(timezone.utc),
                status="no_match",
            )

        # Execute workflow in topological order
        results: dict[str, ToolResult] = {}
        step_outputs: dict[str, dict[str, Any]] = {}

        for step in workflow:
            result = self._execute_step(step, query, initial_inputs, step_outputs)
            results[step["step_id"]] = result

            # Store output for dependent steps
            if result.status == "ok" and result.output:
                step_outputs[step["step_id"]] = result.output

        # Convert to list for Report
        result_list = [results[step["step_id"]] for step in workflow]
        status = self._aggregate_status(result_list)

        return Report(
            query=query,
            tool_results=result_list,
            produced_at=datetime.now(timezone.utc),
            status=status,
        )

    def _execute_step(
        self,
        step: WorkflowStep,
        query: str,
        initial_inputs: dict[str, Any],
        step_outputs: dict[str, dict[str, Any]],
    ) -> ToolResult:
        """Execute a single workflow step.

        Args:
            step: Workflow step to execute
            query: Original query
            initial_inputs: Initial inputs from user
            step_outputs: Outputs from previous steps

        Returns:
            ToolResult for this step
        """
        tool = self.registry.try_get(step["tool"])
        if tool is None:
            return ToolResult(
                tool_name=step["tool"],
                tool_version="unknown",
                input={},
                output=None,
                status="error",
                error=f"Tool '{step['tool']}' not found in registry",
                duration_ms=0.0,
            )

        # Build input data from dependencies
        input_data = self._resolve_input(tool, step, query, initial_inputs, step_outputs)

        # Execute tool
        start = time.perf_counter()
        try:
            output = tool.execute(input_data)
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000.0
            return ToolResult(
                tool_name=tool.name,
                tool_version=tool.version,
                input=input_data,
                output=None,
                status="error",
                error=str(e),
                duration_ms=duration_ms,
            )

        duration_ms = (time.perf_counter() - start) * 1000.0

        # Extract warnings if present
        warnings: list[str] = []
        if isinstance(output, dict):
            raw_warnings = output.get("warnings")
            if isinstance(raw_warnings, list):
                warnings = [str(w) for w in raw_warnings]

        return ToolResult(
            tool_name=tool.name,
            tool_version=tool.version,
            input=input_data,
            output=output,
            status="ok",
            duration_ms=duration_ms,
            warnings=warnings,
        )

    def _resolve_input(
        self,
        tool: Tool,
        step: WorkflowStep,
        query: str,
        initial_inputs: dict[str, Any],
        step_outputs: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Resolve input for a tool, combining initial inputs and dependency outputs.

        Args:
            tool: The tool to execute
            step: Current workflow step
            query: Original query
            initial_inputs: User-provided initial inputs
            step_outputs: Outputs from completed steps

        Returns:
            Input dict for the tool
        """
        # Start with initial inputs
        input_data = dict(initial_inputs)

        # Merge outputs from dependencies
        for dep_id in step.get("depends_on", []):
            if dep_id in step_outputs:
                dep_output = step_outputs[dep_id]
                if isinstance(dep_output, dict):
                    # Merge dependency output into input
                    # Simple strategy: copy all fields
                    input_data.update(dep_output)

        # If still missing required inputs, use resolver
        if not input_data:
            input_data = self.input_resolver.resolve(tool, query)

        return input_data

    @staticmethod
    def _aggregate_status(
        results: list[ToolResult],
    ) -> Literal["ok", "no_match", "partial", "error"]:
        """Derive overall status from tool results."""
        if not results:
            return "no_match"
        ok_count = sum(1 for r in results if r.status == "ok")
        if ok_count == len(results):
            return "ok"
        if ok_count == 0:
            return "error"
        return "partial"
