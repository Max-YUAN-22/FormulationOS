"""Tests for :class:`Report` and :class:`ToolResult` data model and
rendering surfaces (Markdown and JSON)."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from formulation_os.orchestrator import Orchestrator
from formulation_os.planner import RuleBasedPlanner
from formulation_os.registry import ToolRegistry
from formulation_os.report import Report, ToolResult
from tests.conftest import BUILTINS_DIR


# --------------------------------------------------------------------------- #
# Fixtures                                                                    #
# --------------------------------------------------------------------------- #


def _make_report(
    query: str = "test query",
    tool_results: list[ToolResult] | None = None,
    status: str = "ok",
    produced_at: datetime | None = None,
) -> Report:
    """Factory for Report instances used in unit tests."""
    return Report(
        query=query,
        tool_results=tool_results or [],
        produced_at=produced_at or datetime(2026, 6, 30, 12, 0, 0, tzinfo=timezone.utc),
        status=status,  # type: ignore[arg-type]
    )


def _make_tool_result(
    name: str = "Dummy",
    version: str = "0.1.0",
    status: str = "ok",
    output: dict | None = {"result": 42},
    warnings: list[str] | None = None,
    error: str | None = None,
    duration_ms: float = 1.23,
    input_data: dict | None = None,
) -> ToolResult:
    return ToolResult(
        tool_name=name,
        tool_version=version,
        input=input_data or {"q": "x"},
        output=output,
        status=status,  # type: ignore[arg-type]
        error=error,
        duration_ms=duration_ms,
        warnings=warnings or [],
    )


# --------------------------------------------------------------------------- #
# Data model                                                                  #
# --------------------------------------------------------------------------- #


def test_tool_result_default_warnings_is_empty_list() -> None:
    """A freshly constructed ToolResult has warnings=[] (not None, not shared)."""
    a = _make_tool_result()
    b = _make_tool_result()
    a.warnings.append("first mutation")
    assert a.warnings == ["first mutation"]
    assert b.warnings == []  # not shared across instances


# --------------------------------------------------------------------------- #
# to_dict                                                                     #
# --------------------------------------------------------------------------- #


def test_to_dict_round_trip_for_minimal_report() -> None:
    """to_dict() of an empty Report is JSON-serializable."""
    r = _make_report()
    text = json.dumps(r.to_dict())
    reloaded = json.loads(text)
    assert reloaded["query"] == "test query"
    assert reloaded["status"] == "ok"
    assert reloaded["tool_results"] == []
    assert reloaded["produced_at"] == "2026-06-30T12:00:00+00:00"


def test_to_dict_includes_all_tool_result_fields() -> None:
    """to_dict() surfaces every ToolResult field by name."""
    r = _make_report(
        tool_results=[
            _make_tool_result(
                name="Literature",
                output={"papers": [{"title": "X"}], "total_found": 1},
                warnings=["MOCK"],
                duration_ms=4.2,
            )
        ]
    )
    d = r.to_dict()
    tr = d["tool_results"][0]
    assert tr["tool_name"] == "Literature"
    assert tr["tool_version"] == "0.1.0"
    assert tr["input"] == {"q": "x"}
    assert tr["output"] == {"papers": [{"title": "X"}], "total_found": 1}
    assert tr["status"] == "ok"
    assert tr["error"] is None
    assert tr["duration_ms"] == 4.2
    assert tr["warnings"] == ["MOCK"]


def test_to_dict_with_real_orchestrator_run() -> None:
    """End-to-end: a real Orchestrator run produces a Report whose to_dict()
    round-trips through json."""
    registry = ToolRegistry(BUILTINS_DIR).load_all()
    orch = Orchestrator(RuleBasedPlanner(registry), registry)
    report = orch.run("Find recent literature review on ibuprofen", top_k=1)
    text = json.dumps(report.to_dict())
    reloaded = json.loads(text)
    assert reloaded["status"] == "ok"
    assert reloaded["tool_results"][0]["tool_name"] == "Literature"
    assert reloaded["tool_results"][0]["output"]["papers"] is not None


# --------------------------------------------------------------------------- #
# to_markdown — header and footer                                             #
# --------------------------------------------------------------------------- #


def test_markdown_has_title_and_query_and_status() -> None:
    r = _make_report(query="hello", status="ok")
    md = r.to_markdown()
    assert md.startswith("# FormulationOS Report")
    assert "**Query:** hello" in md
    assert "**Status:** OK" in md


def test_markdown_includes_generated_timestamp() -> None:
    """The 'Generated' line uses the Report's produced_at."""
    ts = datetime(2026, 6, 30, 12, 34, 56, tzinfo=timezone.utc)
    md = _make_report(produced_at=ts).to_markdown()
    assert "2026-06-30T12:34:56+00:00" in md


def test_markdown_has_footer_with_formulationos_version() -> None:
    """The footer credits FormulationOS with the v0.1.0 version."""
    md = _make_report().to_markdown()
    assert "*Generated by FormulationOS v0.1.0*" in md


def test_markdown_status_labels_are_human_friendly() -> None:
    """The status line uses the expanded labels, not the raw enum values."""
    for raw, label in [
        ("ok", "OK"),
        ("partial", "PARTIAL"),
        ("error", "ERROR"),
        ("no_match", "NO MATCH"),
    ]:
        md = _make_report(status=raw).to_markdown()
        assert label in md
        # And the raw enum must not leak into the human-readable line
        assert f"**Status:** {raw}" not in md


# --------------------------------------------------------------------------- #
# to_markdown — no-match                                                      #
# --------------------------------------------------------------------------- #


def test_markdown_no_match_uses_explanatory_body() -> None:
    """No-match Reports show a clean explanatory paragraph and no tool sections."""
    r = _make_report(query="xyzzy", status="no_match")
    md = r.to_markdown()
    assert "NO MATCH" in md
    assert "found no Tools" in md
    # No numbered tool sections
    assert "## 1." not in md


# --------------------------------------------------------------------------- #
# to_markdown — single-tool happy path                                        #
# --------------------------------------------------------------------------- #


def test_markdown_single_tool_has_numbered_section_with_subsections() -> None:
    """A one-tool Report produces a numbered section with Input / Output subsections."""
    r = _make_report(
        query="Find recent literature review on ibuprofen",
        tool_results=[
            _make_tool_result(
                name="Literature",
                output={"query": "x", "papers": [{"title": "A"}, {"title": "B"}], "total_found": 2},
                duration_ms=0.42,
            )
        ],
    )
    md = r.to_markdown()
    assert "## 1. Literature v0.1.0" in md
    assert "### Input" in md
    assert "### Output" in md
    assert "```json" in md
    assert "duration_ms" not in md.lower() or "Duration" in md
    assert "**Duration:** 0.42 ms" in md


def test_markdown_includes_executive_summary_for_multi_tool() -> None:
    """Multi-tool Reports show a 'Tools executed (N):' executive summary line."""
    r = _make_report(
        tool_results=[
            _make_tool_result(name="Literature"),
            _make_tool_result(name="FormulationAI"),
        ]
    )
    md = r.to_markdown()
    assert "**Tools executed (2):** `Literature`, `FormulationAI`" in md


def test_markdown_tool_section_preserves_execution_order() -> None:
    """Sections are numbered in the order tool_results appear."""
    r = _make_report(
        tool_results=[
            _make_tool_result(name="First"),
            _make_tool_result(name="Second"),
            _make_tool_result(name="Third"),
        ]
    )
    md = r.to_markdown()
    assert "## 1. First" in md
    assert "## 2. Second" in md
    assert "## 3. Third" in md


# --------------------------------------------------------------------------- #
# to_markdown — warnings and errors                                           #
# --------------------------------------------------------------------------- #


def test_markdown_includes_warnings_when_present() -> None:
    """Tool warnings appear in the metadata list of the tool's section."""
    r = _make_report(
        tool_results=[
            _make_tool_result(name="Literature", warnings=["MOCK OUTPUT — synthetic data"])
        ]
    )
    md = r.to_markdown()
    assert "**Warnings:** MOCK OUTPUT — synthetic data" in md


def test_markdown_omits_warnings_line_when_empty() -> None:
    """When a tool has no warnings, the warnings line is not shown."""
    r = _make_report(tool_results=[_make_tool_result(name="Literature", warnings=[])])
    md = r.to_markdown()
    assert "**Warnings:**" not in md


def test_markdown_includes_error_for_failed_tool() -> None:
    """A failed tool's section shows its error."""
    r = _make_report(
        tool_results=[
            _make_tool_result(
                name="FormulationAI",
                status="error",
                output=None,
                error="synthetic boom",
            )
        ]
    )
    md = r.to_markdown()
    assert "## 1. FormulationAI" in md
    assert "`error`" in md
    assert "`synthetic boom`" in md
    # Failed tool has no output section
    assert md.count("### Output") == 0


def test_markdown_partial_reports_failure_count() -> None:
    """A partial Report (some tools failed) shows the outcome breakdown."""
    r = _make_report(
        status="partial",
        tool_results=[
            _make_tool_result(name="Good", status="ok"),
            _make_tool_result(name="Bad", status="error", output=None, error="x"),
        ],
    )
    md = r.to_markdown()
    assert "**Outcomes:** 1 succeeded, 1 failed." in md
