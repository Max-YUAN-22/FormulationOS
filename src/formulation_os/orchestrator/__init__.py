"""Orchestrator: wires Planner → Tool execution → Report.

The Orchestrator is the topmost user-facing API for executing a single
user query against the FormulationOS system.

In v0.1 it is intentionally simple:
- Sequential execution (no parallelism; future task)
- No DAG (one query → one tool, or top-k independent tools)
- No caching, no incremental re-execution
- No retry policy

Replacing any single piece — planner, input resolver, executor — does
not require touching the others, since they communicate through small
interfaces (:class:`Planner`, :class:`InputResolver`, :class:`Tool`).
"""

from formulation_os.orchestrator.orchestrator import (
    InputResolver,
    Orchestrator,
    StubInputResolver,
)

__all__ = [
    "InputResolver",
    "Orchestrator",
    "StubInputResolver",
]
