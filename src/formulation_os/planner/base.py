"""Abstract Planner interface.

A Planner maps a natural-language query to a ranked list of Tools.
All Planner implementations in FormulationOS implement this interface,
so the Workflow Runtime can consume any of them interchangeably.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from formulation_os.core.tool import Tool


class Planner(ABC):
    """Map a user query to a ranked list of Tools.

    Implementations:
    - :class:`~formulation_os.planner.rule_based.RuleBasedPlanner` (v0.1)
    - LLM-based planner (Phase 2, future)
    - Embedding-based retriever (Task 3 v2, future)
    """

    @abstractmethod
    def plan(self, query: str, top_k: int = 3) -> list[Tool]:
        """Return the top-k Tools most relevant to ``query``, ranked.

        Args:
            query: Natural-language user query.
            top_k: Maximum number of Tools to return. The Planner may
                return fewer (e.g., if fewer than ``top_k`` tools have
                non-zero relevance).

        Returns:
            A list of :class:`Tool` instances, sorted from most to
            least relevant. Empty list if no tool is relevant.
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"