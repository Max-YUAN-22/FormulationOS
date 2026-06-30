"""Report data model and Markdown / dict rendering.

The :class:`Report` and :class:`ToolResult` dataclasses live here, along
with their serialization helpers. The :class:`Report.to_markdown`
method produces a scientific-report-style rendering suitable for the
Streamlit UI, the CLI, and stand-alone artifact files.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

# FormulationOS version string used in the report footer.
_FOS_VERSION = "0.1.0"


# --------------------------------------------------------------------------- #
# Data model                                                                  #
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
    """Top-level result of an :meth:`~formulation_os.orchestrator.Orchestrator.run` call.

    Attributes:
        query: The user query that produced this Report.
        tool_results: One :class:`ToolResult` per Tool the planner selected.
            Empty when ``status == "no_match"``.
        produced_at: Timestamp of when the Report was assembled (UTC-aware).
        status: ``"ok"`` if every selected tool ran successfully;
            ``"partial"`` if some succeeded and some failed;
            ``"error"`` if every tool failed;
            ``"no_match"`` if the planner returned no tools.
    """

    query: str
    tool_results: list[ToolResult]
    produced_at: datetime
    status: Literal["ok", "no_match", "partial", "error"]

    # ---- JSON surface --------------------------------------------------- #

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

    # ---- Markdown surface ---------------------------------------------- #

    def to_markdown(self) -> str:
        """Return a scientific-report-style Markdown rendering.

        Layout:

        * Header with query, status, generated-at, and (for multi-tool
          runs) a one-line per-tool summary.
        * One numbered section per :class:`ToolResult`, containing
          metadata, input, output, warnings, and (on failure) the error.
        * Footer with the FormulationOS version.

        The no-match and error-only cases get a clean explanatory
        message instead of an empty tool list.
        """
        parts: list[str] = [self._md_header()]

        if not self.tool_results:
            parts.append(self._md_no_match_body())
        else:
            ok_count = sum(1 for r in self.tool_results if r.status == "ok")
            err_count = len(self.tool_results) - ok_count
            parts.append(self._md_executive_summary(ok_count, err_count))
            parts.append("")
            parts.append("---")
            parts.append("")
            for idx, r in enumerate(self.tool_results, start=1):
                parts.append(self._md_tool_section(idx, r))
                parts.append("")

        parts.append(self._md_footer())
        return "\n".join(parts).rstrip() + "\n"

    # ---- Markdown helpers (private) ------------------------------------ #

    def _md_header(self) -> str:
        lines = [
            "# FormulationOS Report",
            "",
            f"**Query:** {self.query}",
            f"**Status:** {_format_status(self.status)}",
            f"**Generated:** {self.produced_at.isoformat()}",
        ]
        return "\n".join(lines)

    def _md_executive_summary(self, ok_count: int, err_count: int) -> str:
        n = len(self.tool_results)
        tools = ", ".join(f"`{r.tool_name}`" for r in self.tool_results)
        summary = f"**Tools executed ({n}):** {tools}"
        if err_count == 0:
            return summary
        return (
            f"{summary}\n"
            f"**Outcomes:** {ok_count} succeeded, {err_count} failed."
        )

    def _md_no_match_body(self) -> str:
        if self.status == "no_match":
            return (
                "\n---\n\n"
                "The Planner found no Tools matching this query. "
                "Try rephrasing, broadening the query, or checking the "
                "available Tools' `planning_hints.keywords`."
            )
        return ""

    def _md_tool_section(self, idx: int, r: ToolResult) -> str:
        lines: list[str] = [
            f"## {idx}. {r.tool_name} v{r.tool_version}",
            "",
            f"- **Status:** `{r.status}`",
            f"- **Duration:** {r.duration_ms:.2f} ms",
        ]
        if r.error:
            lines.append(f"- **Error:** `{r.error}`")
        if r.warnings:
            joined = "; ".join(r.warnings)
            lines.append(f"- **Warnings:** {joined}")

        lines.extend(
            [
                "",
                "### Input",
                "",
                "```json",
                _json_dumps(r.input),
                "```",
            ]
        )

        if r.output is not None:
            lines.extend(
                [
                    "",
                    "### Output",
                    "",
                    "```json",
                    _json_dumps(r.output),
                    "```",
                ]
            )

        return "\n".join(lines)

    def _md_footer(self) -> str:
        return "\n---\n\n*Generated by FormulationOS v{}*".format(_FOS_VERSION)


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def _json_dumps(obj: Any) -> str:
    """Stable, indented JSON dump used inside Markdown reports."""
    return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True)


_STATUS_LABELS: dict[str, str] = {
    "ok": "OK",
    "partial": "PARTIAL (some tools failed)",
    "error": "ERROR (all tools failed)",
    "no_match": "NO MATCH (planner returned no tools)",
}


def _format_status(status: str) -> str:
    """Return a human-friendly label for the Report status."""
    return _STATUS_LABELS.get(status, status)
