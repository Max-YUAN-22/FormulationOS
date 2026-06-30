"""LLM client abstraction and concrete implementations.

The :class:`LLMClient` is a thin interface ("send a system+user prompt, get
back a JSON string") so that the rest of FormulationOS does not depend on
any particular provider SDK.

Concrete implementations:

* :class:`OpenAIClient` — uses the OpenAI SDK with JSON mode.
* :class:`MiniMaxClient` — uses the Anthropic SDK against MiniMax's
  Anthropic-compatible endpoint (``https://api.minimaxi.com/anthropic``,
  default model ``MiniMax-M3``).
* :class:`MockLLMClient` — returns a fixed response; used by tests and
  offline development. The :class:`~formulation_os.planner.llm.LLMPlanner`
  is fully tested via this client, so no real API call is required in CI.

Both OpenAIClient and MiniMaxClient lazily import their SDKs, so the module
remains importable without them installed. Install the SDKs with::

    pip install -e ".[llm]"
"""

from formulation_os.llm.client import (
    LLMClient,
    MiniMaxClient,
    MockLLMClient,
    OpenAIClient,
)

__all__ = [
    "LLMClient",
    "MiniMaxClient",
    "MockLLMClient",
    "OpenAIClient",
]
