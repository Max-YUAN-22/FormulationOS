"""Report: structured result of a FormulationOS execution.

The :class:`Report` is the canonical artifact produced by the
Orchestrator. It carries:

* The original user query.
* A :class:`ToolResult` for each Tool the Planner selected and ran.
* The overall status (``ok`` / ``partial`` / ``error`` / ``no_match``).
* A timestamp.

It exposes two rendering surfaces:

* :meth:`Report.to_dict` — JSON-serializable, for storage and APIs.
* :meth:`Report.to_markdown` — human-readable, for display in the
  Streamlit UI, the CLI, or as a research artifact.

This module owns the data model and the rendering logic. The
Orchestrator constructs :class:`Report` and :class:`ToolResult`
instances; it does not format them.
"""

from formulation_os.report.report import Report, ToolResult

__all__ = ["Report", "ToolResult"]
