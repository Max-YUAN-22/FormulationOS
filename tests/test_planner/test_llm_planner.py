"""Tests for :class:`formulation_os.planner.llm.LLMPlanner` and
:func:`formulation_os.planner.llm.make_planner_from_env`."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from formulation_os.llm.client import LLMClient, MockLLMClient
from formulation_os.planner import LLMPlanner, RuleBasedPlanner, make_planner_from_env
from formulation_os.planner.llm import _SYSTEM_PROMPT
from formulation_os.registry import ToolRegistry
from tests.conftest import BUILTINS_DIR


# --------------------------------------------------------------------------- #
# Fixtures                                                                    #
# --------------------------------------------------------------------------- #


@pytest.fixture
def registry() -> ToolRegistry:
    return ToolRegistry(BUILTINS_DIR).load_all()


@pytest.fixture
def llm_planner(registry: ToolRegistry) -> LLMPlanner:
    client = MockLLMClient(response=json.dumps({"selected_tools": ["Literature"]}))
    return LLMPlanner(registry, client)


# --------------------------------------------------------------------------- #
# Happy path                                                                  #
# --------------------------------------------------------------------------- #


def test_llm_planner_returns_tools_in_llm_order(llm_planner: LLMPlanner) -> None:
    """The planner resolves tool names in the order the LLM gave them."""
    client = MockLLMClient(
        response=json.dumps({"selected_tools": ["FormulationAI", "Literature"]})
    )
    registry = ToolRegistry(BUILTINS_DIR).load_all()
    planner = LLMPlanner(registry, client)
    result = planner.plan("anything", top_k=3)
    assert [t.name for t in result] == ["FormulationAI", "Literature"]


def test_llm_planner_respects_top_k(llm_planner: LLMPlanner) -> None:
    client = MockLLMClient(
        response=json.dumps(
            {"selected_tools": ["Literature", "FormulationAI", "PreformulationAI"]}
        )
    )
    registry = ToolRegistry(BUILTINS_DIR).load_all()
    planner = LLMPlanner(registry, client)
    result = planner.plan("anything", top_k=2)
    assert len(result) == 2
    assert [t.name for t in result] == ["Literature", "FormulationAI"]


def test_llm_planner_passes_query_and_tool_cards_to_client(
    llm_planner: LLMPlanner,
) -> None:
    """The user prompt sent to the LLM contains the query and tool metadata."""
    client = MockLLMClient(
        response=json.dumps({"selected_tools": ["Literature"]})
    )
    registry = ToolRegistry(BUILTINS_DIR).load_all()
    planner = LLMPlanner(registry, client)
    planner.plan("Find recent papers on solubility", top_k=1)

    assert len(client.calls) == 1
    system, user, schema_hint = client.calls[0]
    assert system == _SYSTEM_PROMPT
    assert "Find recent papers on solubility" in user
    # Every tool's name and description should be in the user prompt
    for tool in registry:
        assert tool.name in user
    assert "selected_tools" in schema_hint


# --------------------------------------------------------------------------- #
# Robustness                                                                  #
# --------------------------------------------------------------------------- #


def test_llm_planner_filters_unknown_tool_names(llm_planner: LLMPlanner) -> None:
    """Names not in the registry are silently dropped, valid names are kept."""
    client = MockLLMClient(
        response=json.dumps(
            {"selected_tools": ["NoSuchTool", "Literature", "AlsoMissing"]}
        )
    )
    registry = ToolRegistry(BUILTINS_DIR).load_all()
    planner = LLMPlanner(registry, client)
    result = planner.plan("anything", top_k=3)
    assert [t.name for t in result] == ["Literature"]


def test_llm_planner_dedups_duplicate_tool_names(llm_planner: LLMPlanner) -> None:
    """Duplicate names from the LLM collapse to a single entry."""
    client = MockLLMClient(
        response=json.dumps(
            {"selected_tools": ["Literature", "Literature", "FormulationAI"]}
        )
    )
    registry = ToolRegistry(BUILTINS_DIR).load_all()
    planner = LLMPlanner(registry, client)
    result = planner.plan("anything", top_k=3)
    assert [t.name for t in result] == ["Literature", "FormulationAI"]


def test_llm_planner_returns_empty_on_invalid_json(llm_planner: LLMPlanner) -> None:
    client = MockLLMClient(response="not valid json at all")
    registry = ToolRegistry(BUILTINS_DIR).load_all()
    planner = LLMPlanner(registry, client)
    assert planner.plan("anything", top_k=3) == []


def test_llm_planner_returns_empty_on_missing_key(llm_planner: LLMPlanner) -> None:
    client = MockLLMClient(response=json.dumps({"wrong_key": ["Literature"]}))
    registry = ToolRegistry(BUILTINS_DIR).load_all()
    planner = LLMPlanner(registry, client)
    assert planner.plan("anything", top_k=3) == []


def test_llm_planner_returns_empty_on_non_list_selected_tools(
    llm_planner: LLMPlanner,
) -> None:
    client = MockLLMClient(response=json.dumps({"selected_tools": "Literature"}))
    registry = ToolRegistry(BUILTINS_DIR).load_all()
    planner = LLMPlanner(registry, client)
    assert planner.plan("anything", top_k=3) == []


def test_llm_planner_returns_empty_on_llm_exception(llm_planner: LLMPlanner) -> None:
    """An LLM error is swallowed and yields an empty plan (graceful failure)."""
    client = MockLLMClient(response_fn=lambda s, u, h: (_ for _ in ()).throw(RuntimeError("LLM down")))
    registry = ToolRegistry(BUILTINS_DIR).load_all()
    planner = LLMPlanner(registry, client)
    assert planner.plan("anything", top_k=3) == []


def test_llm_planner_returns_empty_for_empty_registry() -> None:
    """With no tools, the planner doesn't even call the LLM."""
    client = MockLLMClient(response="should not be called")
    reg = ToolRegistry(BUILTINS_DIR)  # never .load_all()
    planner = LLMPlanner(reg, client)
    assert planner.plan("anything", top_k=3) == []
    assert client.calls == []


def test_llm_planner_ignores_non_string_tool_names(llm_planner: LLMPlanner) -> None:
    client = MockLLMClient(
        response=json.dumps({"selected_tools": ["Literature", 42, None, "FormulationAI"]})
    )
    registry = ToolRegistry(BUILTINS_DIR).load_all()
    planner = LLMPlanner(registry, client)
    result = planner.plan("anything", top_k=5)
    assert [t.name for t in result] == ["Literature", "FormulationAI"]


# --------------------------------------------------------------------------- #
# make_planner_from_env                                                       #
# --------------------------------------------------------------------------- #


def test_make_planner_from_env_returns_rule_based_by_default(
    monkeypatch: pytest.MonkeyPatch, registry: ToolRegistry
) -> None:
    monkeypatch.delenv("LLM_PLANNER", raising=False)
    planner = make_planner_from_env(registry)
    assert isinstance(planner, RuleBasedPlanner)


def test_make_planner_from_env_falls_back_when_no_key(
    monkeypatch: pytest.MonkeyPatch, registry: ToolRegistry
) -> None:
    """LLM_PLANNER=1 is set but no API key is available — fall back to rule-based."""
    monkeypatch.setenv("LLM_PLANNER", "1")
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    planner = make_planner_from_env(registry)
    assert isinstance(planner, RuleBasedPlanner)


def test_make_planner_from_env_returns_llm_when_enabled(
    monkeypatch: pytest.MonkeyPatch, registry: ToolRegistry
) -> None:
    """With LLM_PLANNER=1 and a key, returns an LLMPlanner."""
    monkeypatch.setenv("LLM_PLANNER", "1")
    monkeypatch.setenv("MINIMAX_API_KEY", "fake-key")

    # Stub the MiniMaxClient to avoid actually constructing an Anthropic client.
    fake_client = MagicMock(spec=LLMClient)
    fake_client.complete_json.return_value = json.dumps(
        {"selected_tools": ["Literature"]}
    )
    monkeypatch.setattr(
        "formulation_os.llm.client.MiniMaxClient",
        lambda **kwargs: fake_client,
    )

    planner = make_planner_from_env(registry)
    assert isinstance(planner, LLMPlanner)
    # And it actually works end-to-end through the env-constructed planner.
    result = planner.plan("anything", top_k=1)
    assert result and result[0].name == "Literature"


def test_make_planner_from_env_falls_back_on_client_construction_error(
    monkeypatch: pytest.MonkeyPatch, registry: ToolRegistry
) -> None:
    """If MiniMaxClient raises during construction, fall back to rule-based."""
    monkeypatch.setenv("LLM_PLANNER", "1")
    monkeypatch.setenv("MINIMAX_API_KEY", "fake-key")

    def boom(**kwargs):
        raise RuntimeError("simulated SDK init failure")

    monkeypatch.setattr("formulation_os.llm.client.MiniMaxClient", boom)

    planner = make_planner_from_env(registry)
    assert isinstance(planner, RuleBasedPlanner)


def test_make_planner_from_env_uses_anthropic_key_as_fallback(
    monkeypatch: pytest.MonkeyPatch, registry: ToolRegistry
) -> None:
    """When MINIMAX_API_KEY is unset but ANTHROPIC_API_KEY is, the latter is used."""
    monkeypatch.setenv("LLM_PLANNER", "1")
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-key")

    captured_kwargs: dict = {}

    def fake_ctor(**kwargs):
        captured_kwargs.update(kwargs)
        return MagicMock(spec=LLMClient)

    monkeypatch.setattr("formulation_os.llm.client.MiniMaxClient", fake_ctor)

    planner = make_planner_from_env(registry)
    assert isinstance(planner, LLMPlanner)
    assert captured_kwargs.get("api_key") == "anthropic-key"
