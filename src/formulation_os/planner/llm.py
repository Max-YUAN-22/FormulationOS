"""LLM-based Planner (Task 7).

Maps a natural-language query to a ranked list of :class:`Tool` instances
by asking an LLM. Uses :class:`~formulation_os.llm.client.LLMClient` to
send the prompt and parse the response.

The LLM is given the tool cards (from :meth:`Tool.to_llm_description`) and
asked to return a JSON list of tool names in priority order. The Planner:

1. Resolves the names against the registry.
2. Preserves the LLM's order.
3. Deduplicates.
4. Filters out unknown names.
5. Truncates to ``top_k``.

If the LLM returns invalid JSON, raises an exception, or times out, the
Planner returns an empty list (same as a no-match rule-based result).
Errors are silently swallowed at the Planner boundary so a flaky LLM
does not crash the Orchestrator. Upstream logging can be added later.
"""

from __future__ import annotations

import json
import os

from formulation_os.core.tool import Tool
from formulation_os.llm.client import LLMClient
from formulation_os.planner.base import Planner
from formulation_os.registry.registry import ToolRegistry

__all__ = ["LLMPlanner", "make_planner_from_env"]


_SYSTEM_PROMPT = (
    "You are a workflow planner for FormulationOS, a pharmaceutical research "
    "operating system. Given a user query and a list of available tools, "
    "select the top-k tools most relevant to the query, in priority order. "
    "Respond ONLY with the JSON object specified in the schema hint — no "
    "prose, no markdown, no commentary."
)

_SCHEMA_HINT = '{"selected_tools": ["tool_name_1", "tool_name_2", ...]}'


class LLMPlanner(Planner):
    """Planner that delegates tool selection to an LLM.

    Args:
        registry: The :class:`ToolRegistry` the planner routes to.
        client: The :class:`LLMClient` used to query the LLM.
    """

    def __init__(self, registry: ToolRegistry, client: LLMClient) -> None:
        self.registry = registry
        self.client = client

    def plan(self, query: str, top_k: int = 3) -> list[Tool]:
        tools = list(self.registry)
        if not tools:
            return []

        cards = [tool.to_llm_description() for tool in tools]
        names = [tool.name for tool in tools]
        user_prompt = (
            f"Available tools (JSON):\n{json.dumps(cards, indent=2)}\n\n"
            f"Tool names you may select: {', '.join(names)}\n\n"
            f"Query: {query}\n\n"
            f"Select the top {top_k} tool(s) for this query."
        )

        try:
            raw = self.client.complete_json(_SYSTEM_PROMPT, user_prompt, _SCHEMA_HINT)
        except Exception:
            return []

        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []

        selected = data.get("selected_tools")
        if not isinstance(selected, list):
            return []

        result: list[Tool] = []
        for name in selected[:top_k]:
            if not isinstance(name, str):
                continue
            tool = self.registry.try_get(name)
            if tool is not None and tool not in result:
                result.append(tool)
        return result


# --------------------------------------------------------------------------- #
# Env-based factory                                                           #
# --------------------------------------------------------------------------- #


def make_planner_from_env(registry: ToolRegistry) -> Planner:
    """Construct a Planner based on environment variables.

    Behavior:

    * If ``LLM_PLANNER=1``: build an :class:`LLMPlanner` backed by
      :class:`~formulation_os.llm.client.MiniMaxClient`. Reads
      ``MINIMAX_API_KEY`` (or ``ANTHROPIC_API_KEY`` as fallback).
    * Otherwise: return a :class:`RuleBasedPlanner`.
    * If the LLM client fails to initialize (missing SDK, missing key,
      etc.): fall back to :class:`RuleBasedPlanner` silently.

    The rule-based fallback is intentional: the system should keep working
    when the LLM is unavailable, not crash.
    """
    # Local import to avoid a circular dependency at module load time.
    from formulation_os.planner.rule_based import RuleBasedPlanner

    if os.environ.get("LLM_PLANNER") != "1":
        return RuleBasedPlanner(registry)

    api_key = os.environ.get("MINIMAX_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return RuleBasedPlanner(registry)

    try:
        from formulation_os.llm.client import MiniMaxClient

        client = MiniMaxClient(api_key=api_key)
    except Exception:
        return RuleBasedPlanner(registry)

    return LLMPlanner(registry, client)
