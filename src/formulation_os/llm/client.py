"""LLM client implementations.

The :class:`LLMClient` ABC defines a single method,
:meth:`LLMClient.complete_json`, that takes a system prompt, a user prompt,
and a schema hint, and returns a raw JSON string. Parsing and validation
are the caller's responsibility.

Three concrete implementations ship:

* :class:`OpenAIClient` — OpenAI SDK, ``response_format={"type": "json_object"}``.
* :class:`MiniMaxClient` — Anthropic SDK against MiniMax's
  Anthropic-compatible endpoint. Uses a forced tool call
  (``tool_choice={"type": "tool", ...}``) to obtain structured JSON.
* :class:`MockLLMClient` — returns a fixed / scripted response; tests only.

Both SDK-backed clients accept an optional ``_client`` keyword argument
for dependency injection in tests, so tests can verify request shape
without mocking ``sys.modules``.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Callable

__all__ = [
    "LLMClient",
    "MiniMaxClient",
    "MockLLMClient",
    "OpenAIClient",
]


# --------------------------------------------------------------------------- #
# ABC                                                                         #
# --------------------------------------------------------------------------- #


class LLMClient(ABC):
    """Send a system+user prompt, get back a JSON string.

    Implementations are responsible for picking the right SDK, applying
    any provider-specific JSON-mode tricks (OpenAI ``response_format`` or
    Anthropic tool use), and returning a raw JSON string. Parsing and
    schema validation are the caller's responsibility.
    """

    @abstractmethod
    def complete_json(self, system: str, user: str, schema_hint: str) -> str:
        """Return a JSON string conforming to ``schema_hint``.

        Args:
            system: The system prompt.
            user: The user prompt.
            schema_hint: A human-readable description of the expected JSON
                schema. Used to guide the model; not enforced.

        Returns:
            A JSON string. The caller parses it with ``json.loads``.
        """
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# OpenAI                                                                      #
# --------------------------------------------------------------------------- #


def _create_default_openai_client(api_key: str, base_url: str | None) -> Any:
    """Construct an OpenAI SDK client. Patched in tests to simulate missing SDK."""
    try:
        from openai import OpenAI as _OpenAI
    except ImportError as e:
        raise RuntimeError(
            "openai SDK is not installed. Install with: pip install -e '.[llm]'"
        ) from e
    if base_url:
        return _OpenAI(api_key=api_key, base_url=base_url)
    return _OpenAI(api_key=api_key)


class OpenAIClient(LLMClient):
    """LLMClient backed by the OpenAI SDK with JSON mode.

    Args:
        api_key: OpenAI API key. Required unless ``_client`` is provided.
        model: Model name (default ``gpt-4o-mini``).
        base_url: Optional override for the API base URL.
        _client: Pre-constructed OpenAI client. Used by tests; bypasses
            the SDK import and the API-key check.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
        *,
        _client: Any | None = None,
    ) -> None:
        if _client is None:
            if not api_key:
                raise ValueError("api_key is required when _client is not provided")
            _client = _create_default_openai_client(api_key, base_url)
        self._client = _client
        self._model = model

    def complete_json(self, system: str, user: str, schema_hint: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": user + "\n\nRespond with JSON matching: " + schema_hint,
                },
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if not isinstance(content, str):
            raise RuntimeError(f"OpenAI returned non-string content: {content!r}")
        return content


# --------------------------------------------------------------------------- #
# MiniMax (Anthropic-compatible)                                              #
# --------------------------------------------------------------------------- #


# Default base URL for MiniMax's Anthropic-compatible endpoint.
_MINIMAX_BASE_URL = "https://api.minimaxi.com/anthropic"
_MINIMAX_DEFAULT_MODEL = "MiniMax-M3"

# Tool schema used to force structured output from the Anthropic-compatible
# API. The model is forced to call this tool via ``tool_choice``, which
# guarantees a structured ``input`` block on the response.
_PLAN_TOOL: dict[str, Any] = {
    "name": "return_plan",
    "description": "Return the complete workflow plan as a JSON object with workflow steps and rationale.",
    "input_schema": {
        "type": "object",
        "properties": {
            "workflow": {
                "type": "array",
                "description": "List of workflow steps in execution order",
                "items": {
                    "type": "object",
                    "properties": {
                        "step_id": {
                            "type": "string",
                            "description": "Unique identifier for this step (e.g., 'step_1')"
                        },
                        "tool": {
                            "type": "string",
                            "description": "Name of the tool to invoke"
                        },
                        "goal": {
                            "type": "string",
                            "description": "What this step aims to achieve"
                        },
                        "depends_on": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of step IDs that must complete before this step"
                        },
                        "justification": {
                            "type": "string",
                            "description": "Scientific reasoning for why this tool is needed"
                        }
                    },
                    "required": ["step_id", "tool", "goal", "depends_on"]
                }
            },
            "rationale": {
                "type": "string",
                "description": "Brief explanation of the overall workflow strategy"
            }
        },
        "required": ["workflow", "rationale"],
    },
}


def _create_default_anthropic_client(api_key: str, base_url: str) -> Any:
    """Construct an Anthropic SDK client. Patched in tests to simulate missing SDK."""
    try:
        from anthropic import Anthropic as _Anthropic
    except ImportError as e:
        raise RuntimeError(
            "anthropic SDK is not installed. Install with: pip install -e '.[llm]'"
        ) from e
    return _Anthropic(api_key=api_key, base_url=base_url)


class MiniMaxClient(LLMClient):
    """LLMClient backed by MiniMax (Anthropic-compatible protocol).

    MiniMax exposes an Anthropic-compatible API at
    ``https://api.minimaxi.com/anthropic``. We use the Anthropic SDK with
    a custom ``base_url``. To force structured JSON output we use a forced
    tool call (``tool_choice={"type": "tool", "name": "return_plan"}``)
    and parse the tool's ``input`` field as JSON.

    Args:
        api_key: API key for the MiniMax endpoint.
        model: Model name (default ``MiniMax-M3``).
        base_url: Override the API base URL (default
            ``https://api.minimaxi.com/anthropic``).
        max_tokens: Max tokens for the response (default 1024).
        _client: Pre-constructed Anthropic client. Used by tests; bypasses
            the SDK import and the API-key check.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = _MINIMAX_DEFAULT_MODEL,
        base_url: str = _MINIMAX_BASE_URL,
        max_tokens: int = 1024,
        *,
        _client: Any | None = None,
    ) -> None:
        if _client is None:
            if not api_key:
                raise ValueError("api_key is required when _client is not provided")
            _client = _create_default_anthropic_client(api_key, base_url)
        self._client = _client
        self._model = model
        self._base_url = base_url
        self._max_tokens = max_tokens

    def complete_json(self, system: str, user: str, schema_hint: str) -> str:
        full_system = system + "\n\nThe expected JSON shape is: " + schema_hint
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=full_system,
            tools=[_PLAN_TOOL],
            tool_choice={"type": "tool", "name": "return_plan"},
            messages=[{"role": "user", "content": user}],
        )
        # With tool_choice forcing a specific tool, the response should
        # always contain exactly one tool_use block. We still scan
        # defensively in case a non-Anthropic-compatible endpoint returns
        # something unexpected.
        for block in response.content:
            name = getattr(block, "name", None)
            if name == "return_plan":
                input_data = getattr(block, "input", None)
                if isinstance(input_data, dict):
                    return json.dumps(input_data)
        raise RuntimeError(
            "MiniMax response did not include the expected 'return_plan' tool call."
        )


# --------------------------------------------------------------------------- #
# Mock                                                                        #
# --------------------------------------------------------------------------- #


class MockLLMClient(LLMClient):
    """In-memory :class:`LLMClient` for tests and offline development.

    Configure with exactly one of:

    * ``response``: a single JSON string returned for every call.
    * ``responses``: a list of JSON strings, returned in order (one per call).
    * ``response_fn``: a callable ``(system, user, schema_hint) -> str`` that
      produces the response dynamically based on the prompt.

    The ``calls`` attribute records every ``complete_json`` invocation as a
    ``(system, user, schema_hint)`` tuple, so tests can assert on what
    was sent to the model.
    """

    def __init__(
        self,
        response: str | None = None,
        *,
        response_fn: Callable[[str, str, str], str] | None = None,
        responses: list[str] | None = None,
    ) -> None:
        provided = sum(x is not None for x in (response, response_fn, responses))
        if provided != 1:
            raise ValueError(
                "MockLLMClient: exactly one of `response`, `response_fn`, or "
                "`responses` must be provided."
            )
        self._response = response
        self._response_fn = response_fn
        self._responses = list(responses) if responses else []
        self._call_count = 0
        self.calls: list[tuple[str, str, str]] = []

    def complete_json(self, system: str, user: str, schema_hint: str) -> str:
        self.calls.append((system, user, schema_hint))
        self._call_count += 1
        if self._response_fn is not None:
            return self._response_fn(system, user, schema_hint)
        if self._responses:
            return self._responses.pop(0)
        if self._response is not None:
            return self._response
        raise RuntimeError("MockLLMClient has no response configured")
