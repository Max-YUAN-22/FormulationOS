"""Tests for :class:`Orchestrator`, :class:`Report`, :class:`ToolResult`,
and :class:`StubInputResolver`."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest

from formulation_os.orchestrator import (
    Orchestrator,
    Report,
    StubInputResolver,
    ToolResult,
)
from formulation_os.planner import RuleBasedPlanner
from formulation_os.planner.base import Planner
from formulation_os.registry import ToolRegistry
from formulation_os.core.tool import Tool
from tests.conftest import BUILTINS_DIR


# --------------------------------------------------------------------------- #
# Fixtures                                                                    #
# --------------------------------------------------------------------------- #


@pytest.fixture
def registry() -> ToolRegistry:
    return ToolRegistry(BUILTINS_DIR).load_all()


@pytest.fixture
def planner(registry: ToolRegistry) -> RuleBasedPlanner:
    return RuleBasedPlanner(registry)


@pytest.fixture
def orchestrator(planner: RuleBasedPlanner, registry: ToolRegistry) -> Orchestrator:
    return Orchestrator(planner, registry)


class _FakePlanner(Planner):
    """Planner stub that returns a fixed tool list in order.

    Used by tests that need to control the planner's output to test
    the Orchestrator's aggregation behavior (e.g., partial failure).
    """

    def __init__(self, tools: list) -> None:
        self._tools = tools

    def plan(self, query: str, top_k: int = 3) -> list:
        return self._tools[:top_k]


class _TestTool(Tool):
    """Minimal concrete Tool for tests that only exercise the resolver.

    The resolver only reads ``input_schema``; ``execute`` is unused.
    """

    def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover
        return {}


# --------------------------------------------------------------------------- #
# Happy paths                                                                 #
# --------------------------------------------------------------------------- #


def test_orchestrator_runs_literature_for_literature_review_query(orchestrator: Orchestrator) -> None:
    """Real Planner + real builtins + a literature-review query returns a Report
    with a single Literature ToolResult of status 'ok'."""
    report = orchestrator.run("Find recent literature review on solubility", top_k=1)

    assert isinstance(report, Report)
    assert report.status == "ok"
    assert report.query == "Find recent literature review on solubility"
    assert len(report.tool_results) == 1
    tr = report.tool_results[0]
    assert tr.tool_name == "Literature"
    assert tr.status == "ok"
    assert tr.output is not None
    assert "papers" in tr.output
    assert tr.error is None


def test_orchestrator_runs_formulation_for_formulate_query(orchestrator: Orchestrator) -> None:
    """Real Planner routes 'I want to formulate ibuprofen as a tablet' to FormulationAI."""
    report = orchestrator.run("I want to formulate ibuprofen as a tablet", top_k=1)
    assert report.status == "ok"
    assert len(report.tool_results) == 1
    assert report.tool_results[0].tool_name == "FormulationAI"
    assert report.tool_results[0].status == "ok"


def test_orchestrator_top_k_executes_multiple_tools_in_order(registry: ToolRegistry) -> None:
    """With a fixed planner returning 2 tools, both run and the order is preserved."""
    planner = _FakePlanner(
        [registry.get("Literature"), registry.get("FormulationAI")]
    )
    orch = Orchestrator(planner, registry)
    report = orch.run(
        "anything",
        top_k=2,
        inputs={
            "Literature": {"query": "anything"},
            "FormulationAI": {"drug_name": "X"},
        },
    )
    assert report.status == "ok"
    assert [r.tool_name for r in report.tool_results] == ["Literature", "FormulationAI"]


# --------------------------------------------------------------------------- #
# No-match                                                                    #
# --------------------------------------------------------------------------- #


def test_orchestrator_returns_no_match_for_unrelated_query(orchestrator: Orchestrator) -> None:
    """A query with no keyword overlap returns an empty Report with status 'no_match'."""
    report = orchestrator.run("xyzzy foo bar baz qux", top_k=3)
    assert report.status == "no_match"
    assert report.tool_results == []


# --------------------------------------------------------------------------- #
# Input resolution                                                            #
# --------------------------------------------------------------------------- #


def test_orchestrator_stub_resolver_fills_first_string_field(orchestrator: Orchestrator) -> None:
    """The default StubInputResolver puts the query into the tool's first string field."""
    report = orchestrator.run("Find recent literature review on ibuprofen", top_k=1)
    assert report.tool_results[0].input == {"query": "Find recent literature review on ibuprofen"}


def test_caller_inputs_override_stub_resolver(orchestrator: Orchestrator) -> None:
    """Explicit inputs={...} take precedence over the resolver."""
    report = orchestrator.run(
        "ignored query text",
        top_k=1,
        inputs={"Literature": {"query": "explicit query", "max_results": 2}},
    )
    assert report.tool_results[0].input == {"query": "explicit query", "max_results": 2}


def test_caller_inputs_for_unselected_tool_are_ignored(orchestrator: Orchestrator) -> None:
    """Inputs for a tool the planner did not pick are silently ignored."""
    report = orchestrator.run(
        "Find recent literature review on solubility",
        top_k=1,
        inputs={"FormulationAI": {"drug_name": "ignored"}},  # planner picks Literature
    )
    assert report.tool_results[0].tool_name == "Literature"


def test_stub_resolver_fills_first_string_field() -> None:
    """When the first declared property is a string, the resolver uses it."""
    spec_yaml = """
name: Dummy
description: d
input_schema:
  type: object
  properties:
    drug_name: {type: string}
    dose_mg: {type: number}
  required: [drug_name]
output_schema: {type: object}
executor: {type: python, module: x, function: y}
"""
    import yaml
    from formulation_os.core.tool import ToolSpec

    spec = ToolSpec(**yaml.safe_load(spec_yaml))
    tool = _TestTool(spec)
    resolver = StubInputResolver()
    out = resolver.resolve(tool, "ibuprofen")
    assert out == {"drug_name": "ibuprofen"}


def test_stub_resolver_returns_empty_for_no_string_fields() -> None:
    """If no property is a string, the resolver returns an empty dict."""
    spec_yaml = """
name: Dummy
description: d
input_schema:
  type: object
  properties:
    dose_mg: {type: number}
    active: {type: boolean}
output_schema: {type: object}
executor: {type: python, module: x, function: y}
"""
    import yaml
    from formulation_os.core.tool import ToolSpec

    spec = ToolSpec(**yaml.safe_load(spec_yaml))
    tool = _TestTool(spec)
    resolver = StubInputResolver()
    assert resolver.resolve(tool, "anything") == {}


def test_stub_resolver_returns_empty_for_missing_properties() -> None:
    """If input_schema has no 'properties' key, the resolver returns an empty dict."""
    spec_yaml = """
name: Dummy
description: d
input_schema:
  type: object
output_schema: {type: object}
executor: {type: python, module: x, function: y}
"""
    import yaml
    from formulation_os.core.tool import ToolSpec

    spec = ToolSpec(**yaml.safe_load(spec_yaml))
    tool = _TestTool(spec)
    resolver = StubInputResolver()
    assert resolver.resolve(tool, "anything") == {}


# --------------------------------------------------------------------------- #
# Failure handling                                                            #
# --------------------------------------------------------------------------- #


def test_orchestrator_records_error_when_tool_fails(registry: ToolRegistry) -> None:
    """A single-tool run that fails returns Report with status='error' and the error captured.

    Uses a fake planner so the test is decoupled from the planner's
    keyword-routing behavior.
    """
    planner = _FakePlanner([registry.get("FormulationAI")])
    orch = Orchestrator(planner, registry)
    with patch.object(
        registry.get("FormulationAI"),
        "execute",
        side_effect=RuntimeError("synthetic failure"),
    ):
        report = orch.run(
            "anything",
            top_k=1,
            inputs={"FormulationAI": {"drug_name": "Ibuprofen"}},
        )
    assert report.status == "error"
    assert len(report.tool_results) == 1
    tr = report.tool_results[0]
    assert tr.tool_name == "FormulationAI"
    assert tr.status == "error"
    assert tr.output is None
    assert "synthetic failure" in (tr.error or "")


def test_orchestrator_partial_when_some_tools_fail(registry: ToolRegistry) -> None:
    """When top_k=2 and one tool fails, Report status is 'partial' and the
    successful tool's result is still present."""
    planner = _FakePlanner(
        [registry.get("FormulationAI"), registry.get("Literature")]
    )
    orch = Orchestrator(planner, registry)
    with patch.object(
        registry.get("FormulationAI"),
        "execute",
        side_effect=RuntimeError("boom"),
    ):
        report = orch.run(
            "anything",
            top_k=2,
            inputs={
                "FormulationAI": {"drug_name": "X"},
                "Literature": {"query": "anything"},
            },
        )
    assert report.status == "partial"
    assert len(report.tool_results) == 2
    by_name = {r.tool_name: r for r in report.tool_results}
    assert by_name["FormulationAI"].status == "error"
    assert by_name["Literature"].status == "ok"
    assert by_name["Literature"].output is not None


# --------------------------------------------------------------------------- #
# Warnings and metadata                                                       #
# --------------------------------------------------------------------------- #


def test_orchestrator_propagates_warnings_from_tool_output(orchestrator: Orchestrator) -> None:
    """Warnings emitted in a tool's output are surfaced in the ToolResult."""
    # Literature with empty query emits ["MOCK OUTPUT — empty query."]
    report = orchestrator.run(
        "test query",
        top_k=1,
        inputs={"Literature": {"query": ""}},
    )
    assert report.status == "ok"
    assert len(report.tool_results) == 1
    warnings = report.tool_results[0].warnings
    assert any("MOCK" in w for w in warnings)


def test_orchestrator_result_carries_tool_version(orchestrator: Orchestrator) -> None:
    """ToolResult.tool_version reflects the executed Tool's version (currently '0.1.0' for builtins)."""
    report = orchestrator.run("Find recent literature review on solubility", top_k=1)
    assert report.tool_results[0].tool_version == "0.1.0"


def test_orchestrator_measures_duration(orchestrator: Orchestrator) -> None:
    """ToolResult.duration_ms is a non-negative number."""
    report = orchestrator.run("Find recent literature review on solubility", top_k=1)
    assert report.tool_results[0].duration_ms >= 0.0


# --------------------------------------------------------------------------- #
# Report serialization                                                        #
# --------------------------------------------------------------------------- #


def test_report_to_dict_is_json_serializable(orchestrator: Orchestrator) -> None:
    """Report.to_dict() can be round-tripped through json.dumps / json.loads."""
    report = orchestrator.run("Find recent literature review on ibuprofen", top_k=1)
    d = report.to_dict()
    text = json.dumps(d)  # must not raise
    reloaded = json.loads(text)
    assert reloaded["query"] == "Find recent literature review on ibuprofen"
    assert reloaded["status"] == "ok"
    assert len(reloaded["tool_results"]) == 1
    assert reloaded["tool_results"][0]["tool_name"] == "Literature"
    assert reloaded["tool_results"][0]["output"]["papers"] is not None
    # datetime should be ISO string
    assert isinstance(reloaded["produced_at"], str)


def test_report_to_markdown_contains_query_and_tool_output(orchestrator: Orchestrator) -> None:
    """The Markdown rendering includes the query, tool name, and at least one
    recognizable piece of the output."""
    report = orchestrator.run("Find recent literature review on ibuprofen", top_k=1)
    md = report.to_markdown()
    assert "Find recent literature review on ibuprofen" in md
    assert "Literature" in md
    assert "## Literature" in md
    assert "ok" in md
    assert '"papers"' in md  # the output JSON block


def test_report_to_markdown_for_no_match_is_informative(orchestrator: Orchestrator) -> None:
    """The no-match Markdown clearly says so."""
    report = orchestrator.run("xyzzy foo bar baz qux", top_k=3)
    md = report.to_markdown()
    assert "no_match" in md
    assert "No tools matched the query" in md
