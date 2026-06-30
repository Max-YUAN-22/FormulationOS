"""Workflow Planner: maps NL queries to ranked Tools.

The Planner interface is intentionally minimal so it can be swapped
without changing downstream code.

Implementations:

* :class:`RuleBasedPlanner` — v0.1 default. Keyword/token overlap
  across capabilities, planning_hints.keywords, and description.
* :class:`LLMPlanner` — opt-in (Task 7). Delegates to an LLM via
  :class:`~formulation_os.llm.client.LLMClient`. Use
  :func:`make_planner_from_env` to choose at runtime based on env vars.
"""

from formulation_os.planner.base import Planner
from formulation_os.planner.llm import LLMPlanner, make_planner_from_env
from formulation_os.planner.rule_based import RuleBasedPlanner

__all__ = [
    "LLMPlanner",
    "Planner",
    "RuleBasedPlanner",
    "make_planner_from_env",
]
