"""Rule-based keyword-matching Planner.

This is the v0.1 Planner. It is intentionally simple:

- Tokenize the query (lowercase, split on non-alphanumeric + ``_``).
- For each Tool, score by token overlap across three fields:
    * ``capabilities``       — weight 3.0
    * ``planning_hints.keywords`` — weight 2.0
    * ``description``        — weight 1.0
- Return the top-k Tools with score > 0, sorted by score desc.

Limitations:
- No semantic understanding ("bioavailability" doesn't match "PK").
- No query intent understanding ("find papers on X" may pick the
  property-predictor for X if X is also a property).
- No synonym handling beyond what authors put in keywords.

It is intentionally easy to replace: implement
:class:`~formulation_os.planner.base.Planner` with an LLM-based or
embedding-based strategy and the rest of the system does not change.
"""

from __future__ import annotations

import re
from typing import Iterable

from formulation_os.core.tool import Tool
from formulation_os.planner.base import Planner
from formulation_os.registry.registry import ToolRegistry


_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> set[str]:
    """Lowercase + split on whitespace, underscore, and punctuation.

    ``solubility_prediction`` becomes ``{"solubility", "prediction"}``.
    """
    return set(_TOKEN_RE.findall(text.lower()))


class RuleBasedPlanner(Planner):
    """Keyword-matching Planner. Cheap, deterministic, easy to test."""

    # Field weights
    WEIGHT_CAPABILITY = 3.0
    WEIGHT_KEYWORD = 2.0
    WEIGHT_DESCRIPTION = 1.0

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def plan(self, query: str, top_k: int = 3) -> list[Tool]:
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scored = [(self._score(query_tokens, tool), tool) for tool in self.registry]
        # Stable sort: higher score first, then alphabetical name for ties
        scored.sort(key=lambda x: (-x[0], x[1].name))
        return [tool for score, tool in scored if score > 0][:top_k]

    # ---- Internals ------------------------------------------------------ #

    def _score(self, query_tokens: Iterable[str], tool: Tool) -> float:
        query_tokens = set(query_tokens)
        cap_tokens = _tokenize(" ".join(tool.capabilities))
        kw_tokens = _tokenize(" ".join(tool.spec.planning_hints.keywords))
        desc_tokens = _tokenize(tool.description)

        score = 0.0
        for tok in query_tokens:
            if tok in cap_tokens:
                score += self.WEIGHT_CAPABILITY
            if tok in kw_tokens:
                score += self.WEIGHT_KEYWORD
            if tok in desc_tokens:
                score += self.WEIGHT_DESCRIPTION
        return score

    def explain(self, query: str, tool: Tool) -> dict[str, float]:
        """Debug helper: return per-field scores for a single (query, tool) pair."""
        tokens = _tokenize(query)
        cap_tokens = _tokenize(" ".join(tool.capabilities))
        kw_tokens = _tokenize(" ".join(tool.spec.planning_hints.keywords))
        desc_tokens = _tokenize(tool.description)
        return {
            "capability": sum(self.WEIGHT_CAPABILITY for t in tokens if t in cap_tokens),
            "keyword":    sum(self.WEIGHT_KEYWORD    for t in tokens if t in kw_tokens),
            "description": sum(self.WEIGHT_DESCRIPTION for t in tokens if t in desc_tokens),
        }