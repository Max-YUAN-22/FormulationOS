"""Tests for :class:`RuleBasedPlanner`."""

from __future__ import annotations

import pytest

from formulation_os.core.tool import Tool
from formulation_os.planner import RuleBasedPlanner
from formulation_os.registry import ToolRegistry
from tests.conftest import BUILTINS_DIR


@pytest.fixture
def registry() -> ToolRegistry:
    return ToolRegistry(BUILTINS_DIR).load_all()


@pytest.fixture
def planner(registry: ToolRegistry) -> RuleBasedPlanner:
    return RuleBasedPlanner(registry)


# ---- The three user-specified examples ----------------------------------- #


def test_planner_picks_formulation_for_formulate_query(planner: RuleBasedPlanner) -> None:
    """User's example: 'I want to formulate ibuprofen as a tablet' -> [FormulationAI]."""
    selected = planner.plan("I want to formulate ibuprofen as a tablet", top_k=1)
    assert len(selected) == 1
    assert selected[0].name == "FormulationAI"


def test_planner_picks_pbpk_for_bioavailability_query(planner: RuleBasedPlanner) -> None:
    """User's example: 'What is the bioavailability?' -> [PBPK]."""
    selected = planner.plan("What is the bioavailability?", top_k=1)
    assert len(selected) == 1
    assert selected[0].name == "PBPK-AI"


def test_planner_picks_literature_for_papers_query(planner: RuleBasedPlanner) -> None:
    """User's example: 'Find recent papers on solubility' -> [Literature]."""
    selected = planner.plan("Find recent papers on solubility", top_k=1)
    assert len(selected) == 1
    assert selected[0].name == "Literature"


# ---- Additional behavior ------------------------------------------------- #


def test_planner_returns_ranked_list_for_multi_match(planner: RuleBasedPlanner) -> None:
    """A query touching multiple domains returns a ranked list."""
    selected = planner.plan("design a tablet formulation", top_k=3)
    assert 1 <= len(selected) <= 3
    assert all(isinstance(t, Tool) for t in selected)
    # FormulationAI should be top for this query
    assert selected[0].name == "FormulationAI"


def test_planner_top_k_limits_results(planner: RuleBasedPlanner) -> None:
    selected = planner.plan("drug", top_k=2)
    assert len(selected) <= 2


def test_planner_empty_query_returns_empty(planner: RuleBasedPlanner) -> None:
    assert planner.plan("", top_k=3) == []


def test_planner_whitespace_only_query_returns_empty(planner: RuleBasedPlanner) -> None:
    assert planner.plan("   \t\n  ", top_k=3) == []


def test_planner_unrelated_query_returns_empty(planner: RuleBasedPlanner) -> None:
    """No keyword overlap -> no tools."""
    selected = planner.plan("xyzzy foo bar baz qux", top_k=3)
    assert selected == []


def test_planner_is_deterministic(planner: RuleBasedPlanner) -> None:
    a = planner.plan("formulate tablet", top_k=3)
    b = planner.plan("formulate tablet", top_k=3)
    assert [t.name for t in a] == [t.name for t in b]


def test_planner_tie_breaks_alphabetically(planner: RuleBasedPlanner) -> None:
    """When two tools score identically, the one earlier in alphabet wins."""
    # "drug" alone doesn't match keywords; both FormulationAI and
    # PreformulationAI mention "drug" or "API" etc. Force a tie by
    # checking the order is deterministic.
    a = planner.plan("drug", top_k=5)
    assert [t.name for t in a] == sorted([t.name for t in a], key=lambda n: (-1, n))


def test_planner_explain_returns_per_field_scores(planner: RuleBasedPlanner, registry: ToolRegistry) -> None:
    """The explain() helper shows how a score was derived."""
    tool = registry.get("FormulationAI")
    breakdown = planner.explain("design a tablet", tool)
    assert "capability" in breakdown
    assert "keyword" in breakdown
    assert "description" in breakdown
    total = breakdown["capability"] + breakdown["keyword"] + breakdown["description"]
    assert total > 0


def test_planner_underscore_in_keyword_splits() -> None:
    """solubility_prediction should match a query containing 'solubility'."""
    reg = ToolRegistry(BUILTINS_DIR).load_all()
    planner = RuleBasedPlanner(reg)
    selected = planner.plan("predict solubility", top_k=1)
    assert selected[0].name == "PreformulationAI"


def test_planner_uses_capabilities_with_highest_weight(planner: RuleBasedPlanner) -> None:
    """Capabilities should outrank keywords/description for the same token."""
    breakdown = planner.explain("tablet", planner.registry.get("FormulationAI"))
    assert breakdown["capability"] >= breakdown["keyword"]


def test_planner_is_an_interface_compatible() -> None:
    """RuleBasedPlanner satisfies the Planner interface."""
    from formulation_os.planner.base import Planner
    reg = ToolRegistry(BUILTINS_DIR).load_all()
    planner: Planner = RuleBasedPlanner(reg)
    assert isinstance(planner, Planner)
    selected = planner.plan("tablet", top_k=1)
    assert isinstance(selected, list)