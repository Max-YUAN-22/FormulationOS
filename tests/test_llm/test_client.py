"""Tests for :mod:`formulation_os.llm.client`.

These tests use ``MagicMock`` for the underlying SDK clients and the
``_create_default_*`` factory functions to simulate missing-SDK
conditions. No real API calls are made.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from formulation_os.llm.client import (
    LLMClient,
    MiniMaxClient,
    MockLLMClient,
    OpenAIClient,
    _create_default_anthropic_client,
    _create_default_openai_client,
)


# --------------------------------------------------------------------------- #
# MockLLMClient                                                               #
# --------------------------------------------------------------------------- #


def test_mock_returns_single_response_for_every_call() -> None:
    client = MockLLMClient(response='{"x": 1}')
    assert client.complete_json("sys", "user", "schema") == '{"x": 1}'
    assert client.complete_json("sys2", "user2", "schema2") == '{"x": 1}'
    assert client._call_count == 2


def test_mock_cycles_through_responses_list() -> None:
    client = MockLLMClient(responses=['{"a": 1}', '{"a": 2}', '{"a": 3}'])
    assert client.complete_json("s", "u", "h") == '{"a": 1}'
    assert client.complete_json("s", "u", "h") == '{"a": 2}'
    assert client.complete_json("s", "u", "h") == '{"a": 3}'


def test_mock_uses_callable_response_fn() -> None:
    def fn(system: str, user: str, schema_hint: str) -> str:
        return json.dumps({"echo": user})

    client = MockLLMClient(response_fn=fn)
    out = client.complete_json("s", "hello", "h")
    assert json.loads(out) == {"echo": "hello"}


def test_mock_records_all_calls() -> None:
    client = MockLLMClient(response='{"ok": true}')
    client.complete_json("sys1", "user1", "hint1")
    client.complete_json("sys2", "user2", "hint2")
    assert client.calls == [("sys1", "user1", "hint1"), ("sys2", "user2", "hint2")]


def test_mock_constructor_rejects_multiple_or_no_response_args() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        MockLLMClient()
    with pytest.raises(ValueError, match="exactly one"):
        MockLLMClient(response="x", responses=["y"])


# --------------------------------------------------------------------------- #
# OpenAIClient                                                                #
# --------------------------------------------------------------------------- #


def test_openai_client_constructs_with_mock_client() -> None:
    """The _client kwarg bypasses SDK import and api_key check."""
    mock = MagicMock(name="OpenAI")
    c = OpenAIClient(_client=mock)
    assert c._client is mock
    assert c._model == "gpt-4o-mini"


def test_openai_client_raises_without_key_and_no_mock() -> None:
    with pytest.raises(ValueError, match="api_key"):
        OpenAIClient()


def test_openai_client_raises_without_openai_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    """When the openai import fails, the constructor raises a clear install hint."""
    def boom(api_key: str, base_url: str | None) -> None:
        raise RuntimeError("openai SDK is not installed. Install with: pip install -e '.[llm]'")
    monkeypatch.setattr(
        "formulation_os.llm.client._create_default_openai_client", boom
    )
    with pytest.raises(RuntimeError, match="openai"):
        OpenAIClient(api_key="test-key")


def test_openai_client_complete_json_sends_correct_request_shape() -> None:
    """The OpenAIClient sends the expected model, messages, and response_format."""
    mock_client = MagicMock(name="OpenAI")
    mock_choice = MagicMock(message=MagicMock(content='{"selected_tools": ["A"]}'))
    mock_response = MagicMock(choices=[mock_choice])
    mock_client.chat.completions.create.return_value = mock_response

    c = OpenAIClient(api_key="k", model="gpt-test", _client=mock_client)
    out = c.complete_json("system prompt", "user prompt", "schema-hint")

    assert json.loads(out) == {"selected_tools": ["A"]}
    kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "gpt-test"
    assert kwargs["response_format"] == {"type": "json_object"}
    assert kwargs["messages"][0] == {"role": "system", "content": "system prompt"}
    assert kwargs["messages"][1]["role"] == "user"
    assert "user prompt" in kwargs["messages"][1]["content"]
    assert "schema-hint" in kwargs["messages"][1]["content"]


def test_openai_client_raises_on_non_string_content() -> None:
    mock_client = MagicMock(name="OpenAI")
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=None))]
    )
    c = OpenAIClient(_client=mock_client)
    with pytest.raises(RuntimeError, match="non-string"):
        c.complete_json("s", "u", "h")


# --------------------------------------------------------------------------- #
# MiniMaxClient                                                               #
# --------------------------------------------------------------------------- #


def test_minimax_client_uses_minimax_base_url_by_default() -> None:
    c = MiniMaxClient(_client=MagicMock())
    assert c._base_url == "https://api.minimaxi.com/anthropic"
    assert c._model == "MiniMax-M3"


def test_minimax_client_accepts_custom_base_url() -> None:
    c = MiniMaxClient(base_url="https://custom.example/anthropic", _client=MagicMock())
    assert c._base_url == "https://custom.example/anthropic"


def test_minimax_client_raises_without_key_and_no_mock() -> None:
    with pytest.raises(ValueError, match="api_key"):
        MiniMaxClient()


def test_minimax_client_raises_without_anthropic_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(api_key: str, base_url: str) -> None:
        raise RuntimeError(
            "anthropic SDK is not installed. Install with: pip install -e '.[llm]'"
        )
    monkeypatch.setattr(
        "formulation_os.llm.client._create_default_anthropic_client", boom
    )
    with pytest.raises(RuntimeError, match="anthropic"):
        MiniMaxClient(api_key="test-key")


def test_minimax_client_complete_json_sends_correct_request_shape() -> None:
    """The MiniMaxClient sends the expected model, max_tokens, tool_choice, and
    system prompt (with the schema hint appended)."""
    mock_client = MagicMock(name="Anthropic")
    tool_block = MagicMock()
    tool_block.name = "return_plan"
    tool_block.input = {"selected_tools": ["Literature"]}
    mock_response = MagicMock(content=[tool_block])
    mock_client.messages.create.return_value = mock_response

    c = MiniMaxClient(api_key="k", _client=mock_client)
    out = c.complete_json("system", "user", "schema-hint")

    assert json.loads(out) == {"selected_tools": ["Literature"]}
    kwargs = mock_client.messages.create.call_args.kwargs
    assert kwargs["model"] == "MiniMax-M3"
    assert kwargs["max_tokens"] == 1024
    assert kwargs["tool_choice"] == {"type": "tool", "name": "return_plan"}
    assert kwargs["system"].startswith("system")
    assert "schema-hint" in kwargs["system"]
    # The forced tool is passed through.
    tools = kwargs["tools"]
    assert len(tools) == 1
    assert tools[0]["name"] == "return_plan"
    assert "selected_tools" in tools[0]["input_schema"]["properties"]
    # User message
    assert kwargs["messages"] == [{"role": "user", "content": "user"}]


def test_minimax_client_raises_when_response_has_no_return_plan_block() -> None:
    mock_client = MagicMock(name="Anthropic")
    other_block = MagicMock()
    other_block.name = "other_tool"
    other_block.input = {"x": 1}
    mock_client.messages.create.return_value = MagicMock(content=[other_block])

    c = MiniMaxClient(_client=mock_client)
    with pytest.raises(RuntimeError, match="return_plan"):
        c.complete_json("s", "u", "h")


def test_minimax_client_uses_custom_model() -> None:
    c = MiniMaxClient(model="custom-model", _client=MagicMock())
    assert c._model == "custom-model"


# --------------------------------------------------------------------------- #
# LLMClient ABC                                                               #
# --------------------------------------------------------------------------- #


def test_llm_client_is_abstract() -> None:
    """LLMClient cannot be instantiated directly."""
    with pytest.raises(TypeError):
        LLMClient()  # type: ignore[abstract]
