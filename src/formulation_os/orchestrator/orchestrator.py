"""Orchestrator implementation.

The Orchestrator is the topmost user-facing API for executing a single
user query against the FormulationOS system. It:

1. Calls the Planner to rank Tools for the query.
2. Resolves ``input_data`` for each Tool (via :class:`InputResolver`
   or caller-provided ``inputs`` dict).
3. Executes each Tool through its Executor (the Tool's own ``execute``).
4. Collects per-tool results into a :class:`Report`.
5. Continues on individual Tool failures — the result for the failed
   Tool is recorded with ``status="error"`` and the overall Report
   status becomes ``"partial"`` (or ``"error"`` if all failed).

v0.1 limitations (all future work):
- Sequential execution only (parallelism lands in Task 5).
- No DAG. Top-k tools from the planner are executed independently.
- No caching, no incremental re-execution (Task 5).
- No retry policy.
"""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

from formulation_os.core.tool import Tool
from formulation_os.planner.base import Planner
from formulation_os.registry.registry import ToolRegistry


# --------------------------------------------------------------------------- #
# Input resolution                                                            #
# --------------------------------------------------------------------------- #


class InputResolver(ABC):
    """Maps a free-form user query to a Tool's typed input dict.

    v0.1 ships only :class:`StubInputResolver`. An LLM-based resolver
    will land alongside the LLM-based Planner in a later version.
    """

    @abstractmethod
    def resolve(self, tool: Tool, query: str) -> dict[str, Any]:
        """Return input data for ``tool`` given the user ``query``."""
        raise NotImplementedError


class StubInputResolver(InputResolver):
    """Picks the first ``string`` field of the Tool's input schema and
    stuffs the query into it.

    Good enough for end-to-end smoke tests with mock Tools. Not suitable
    for production — an LLM-based resolver is required to map free-form
    queries onto typed tool inputs in real use.
    """

    def resolve(self, tool: Tool, query: str) -> dict[str, Any]:
        props = tool.input_schema.get("properties", {})
        if not isinstance(props, dict):
            return {}
        for name, spec in props.items():
            if isinstance(spec, dict) and spec.get("type") == "string":
                return {name: query}
        return {}


# --------------------------------------------------------------------------- #
# Result and Report types                                                     #
# --------------------------------------------------------------------------- #


@dataclass
class ToolResult:
    """Result of a single Tool execution within an Orchestrator run."""

    tool_name: str
    tool_version: str
    input: dict[str, Any]
    output: dict[str, Any] | None
    status: Literal["ok", "error"]
    error: str | None = None
    duration_ms: float = 0.0
    warnings: list[str] = field(default_factory=list)


@dataclass
class Report:
    """Top-level result of an :meth:`Orchestrator.run` call.

    Attributes:
        query: The user query that produced this Report.
        tool_results: One :class:`ToolResult` per Tool the planner selected.
            Empty when ``status == "no_match"``.
        produced_at: UTC timestamp of when the Report was assembled.
        status: ``"ok"`` if every selected tool ran successfully;
            ``"partial"`` if some succeeded and some failed;
            ``"error"`` if every tool failed;
            ``"no_match"`` if the planner returned no tools.
    """

    query: str
    tool_results: list[ToolResult]
    produced_at: datetime
    status: Literal["ok", "no_match", "partial", "error"]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict representation."""
        return {
            "query": self.query,
            "status": self.status,
            "produced_at": self.produced_at.isoformat(),
            "tool_results": [
                {
                    "tool_name": r.tool_name,
                    "tool_version": r.tool_version,
                    "input": r.input,
                    "output": r.output,
                    "status": r.status,
                    "error": r.error,
                    "duration_ms": r.duration_ms,
                    "warnings": r.warnings,
                }
                for r in self.tool_results
            ],
        }

    def to_markdown(self) -> str:
        """Return a human-readable Markdown rendering of the Report."""
        lines: list[str] = [
            "# Orchestrator Report",
            "",
            f"**Query:** {self.query}",
            f"**Status:** {self.status}",
            f"**Produced at:** {self.produced_at.isoformat()}",
            "",
        ]
        if not self.tool_results:
            lines.append("_No tools matched the query._")
            return "\n".join(lines) + "\n"

        for r in self.tool_results:
            lines.append(f"## {r.tool_name} v{r.tool_version}")
            lines.append("")
            lines.append(f"- **Status:** {r.status}")
            lines.append(f"- **Duration:** {r.duration_ms:.2f} ms")
            if r.error:
                lines.append(f"- **Error:** {r.error}")
            if r.warnings:
                lines.append(f"- **Warnings:** {'; '.join(r.warnings)}")
            lines.append("")
            lines.append("**Input:**")
            lines.append("")
            lines.append("```json")
            lines.append(_json_dumps(r.input))
            lines.append("```")
            if r.output is not None:
                lines.append("")
                lines.append("**Output:**")
                lines.append("")
                lines.append("```json")
                lines.append(_json_dumps(r.output))
                lines.append("```")
            lines.append("")
        return "\n".join(lines)


def _json_dumps(obj: Any) -> str:
    """Stable, indented JSON dump used inside Markdown reports."""
    return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True)


# --------------------------------------------------------------------------- #
# Orchestrator                                                                #
# --------------------------------------------------------------------------- #


class Orchestrator:
    """Wires Planner → Tool execution → Report.

    The Orchestrator is the highest-level API in FormulationOS v0.1.
    Call :meth:`run` with a natural-language query; get back a
    :class:`Report` containing the planner's chosen tools executed and
    their outputs collected.

    Args:
        planner: A :class:`~formulation_os.planner.base.Planner`
            implementation (e.g., :class:`RuleBasedPlanner`).
        registry: A :class:`~formulation_os.registry.registry.ToolRegistry`
            holding the Tools the planner can route to.
        input_resolver: Optional :class:`InputResolver`. Defaults to
            :class:`StubInputResolver`. Replace with an LLM-based
            resolver in production use.
    """

    def __init__(
        self,
        planner: Planner,
        registry: ToolRegistry,
        input_resolver: InputResolver | None = None,
    ) -> None:
        self.planner = planner
        self.registry = registry
        self.input_resolver: InputResolver = input_resolver or StubInputResolver()

    def run(
        self,
        query: str,
        top_k: int = 1,
        inputs: dict[str, dict[str, Any]] | None = None,
    ) -> Report:
        """Execute a query through the full pipeline.

        Args:
            query: Natural-language user query.
            top_k: Maximum number of Tools to execute (defaults to 1).
                The Planner may return fewer if fewer have non-zero
                relevance.
            inputs: Optional per-Tool input overrides. Keys are Tool
                names, values are input dicts. Takes precedence over
                the configured :class:`InputResolver`. Inputs for Tools
                the planner did not select are ignored.

        Returns:
            A :class:`Report` aggregating the planner's picks, each
            Tool's execution result, and the overall status.
        """
        inputs = inputs or {}
        tools = self.planner.plan(query, top_k=top_k)

        if not tools:
            return Report(
                query=query,
                tool_results=[],
                produced_at=datetime.now(timezone.utc),
                status="no_match",
            )

        results: list[ToolResult] = []
        for tool in tools:
            results.append(self._run_one(tool, query, inputs))

        status: Literal["ok", "no_match", "partial", "error"] = self._aggregate_status(results)
        return Report(
            query=query,
            tool_results=results,
            produced_at=datetime.now(timezone.utc),
            status=status,
        )

    # ---- Internals ------------------------------------------------------ #

    def _run_one(
        self,
        tool: Tool,
        query: str,
        inputs: dict[str, dict[str, Any]],
    ) -> ToolResult:
        """Execute a single Tool, capturing timing, output, and warnings."""
        if tool.name in inputs:
            input_data = inputs[tool.name]
        else:
            input_data = self.input_resolver.resolve(tool, query)

        start = time.perf_counter()
        try:
            output = tool.execute(input_data)
        except Exception as e:  # noqa: BLE001 — orchestrator must record any failure
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

    @staticmethod
    def _aggregate_status(results: list[ToolResult]) -> Literal["ok", "no_match", "partial", "error"]:
        """Derive the overall Report status from per-Tool results."""
        if not results:
            return "no_match"
        ok_count = sum(1 for r in results if r.status == "ok")
        if ok_count == len(results):
            return "ok"
        if ok_count == 0:
            return "error"
        return "partial"
