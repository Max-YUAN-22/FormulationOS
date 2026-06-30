"""Workflow Planner: maps NL queries to ranked Tools (Task 3).

The Planner interface is intentionally minimal so it can be swapped
without changing downstream code. The v0.1 implementation is
:class:`~formulation_os.planner.rule_based.RuleBasedPlanner`.

Future implementations will arrive in Phase 2:
- LLM-based Planner (LLM with structured output → DAG)
- Embedding-based retriever (BGE / Qwen + Chroma → top-k)
"""

from formulation_os.planner.base import Planner
from formulation_os.planner.rule_based import RuleBasedPlanner

__all__ = ["Planner", "RuleBasedPlanner"]