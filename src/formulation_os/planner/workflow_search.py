"""Workflow Search Engine - Generate and compare multiple workflow plans.

This module implements a search-based approach to workflow planning:
- Generate N candidate workflows for a query
- Score each workflow based on multiple criteria
- Return ranked list of workflows

Example:
    query = "Design an oral formulation for aspirin"
    engine = WorkflowSearchEngine(planner, registry, n_candidates=3)
    candidates = engine.search(query)

    for candidate in candidates:
        print(f"Score: {candidate.score}")
        print(f"Workflow: {candidate.plan}")
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from formulation_os.planner.workflow_planner import WorkflowPlanner
from formulation_os.planner.workflow_schema import WorkflowPlan
from formulation_os.planner.workflow_validator import WorkflowValidator
from formulation_os.registry.registry import ToolRegistry

__all__ = ["WorkflowSearchEngine", "WorkflowCandidate"]


@dataclass
class WorkflowCandidate:
    """A candidate workflow with its score.

    Attributes:
        plan: The workflow plan
        score: Overall quality score (0-1, higher is better)
        metrics: Detailed scoring metrics
        rank: Rank in search results (1 = best)
    """

    plan: WorkflowPlan
    score: float
    metrics: dict[str, float]
    rank: int


class WorkflowSearchEngine:
    """Generate and rank multiple workflow candidates.

    Args:
        planner: Workflow planner to use
        registry: Tool registry for validation
        n_candidates: Number of candidates to generate (default 3)
        temperature: LLM temperature for diversity (default 0.8)
    """

    def __init__(
        self,
        planner: WorkflowPlanner,
        registry: ToolRegistry,
        n_candidates: int = 3,
        temperature: float = 0.8,
    ):
        self.planner = planner
        self.validator = WorkflowValidator(registry)
        self.n_candidates = n_candidates
        self.temperature = temperature

    def search(self, query: str, context: dict[str, Any] | None = None) -> list[WorkflowCandidate]:
        """Generate and rank multiple workflow candidates.

        Args:
            query: User's natural language query
            context: Optional context (e.g., drug properties, constraints)

        Returns:
            List of WorkflowCandidate objects, sorted by score (best first)
        """
        candidates = []

        # Generate N candidate workflows
        for i in range(self.n_candidates):
            plan = self.planner.plan(query, context)

            if plan is None:
                continue

            # Score this candidate
            score, metrics = self._score_workflow(plan)

            candidates.append(WorkflowCandidate(
                plan=plan,
                score=score,
                metrics=metrics,
                rank=0  # Will be set after sorting
            ))

        # Sort by score (descending)
        candidates.sort(key=lambda c: c.score, reverse=True)

        # Assign ranks
        for rank, candidate in enumerate(candidates, start=1):
            candidate.rank = rank

        return candidates

    def _score_workflow(self, plan: WorkflowPlan) -> tuple[float, dict[str, float]]:
        """Score a workflow based on multiple criteria.

        Returns:
            (overall_score, metrics_dict)
        """
        metrics = {}

        # 1. Validity score (0 or 1)
        validation_result = self.validator.validate(plan["workflow"])
        metrics["validity"] = 1.0 if validation_result.is_valid else 0.0

        # 2. Completeness score (0-1)
        # Check if workflow has justifications
        steps_with_justification = sum(
            1 for step in plan["workflow"]
            if step.get("justification")
        )
        metrics["completeness"] = steps_with_justification / max(len(plan["workflow"]), 1)

        # 3. Complexity score (0-1, simpler is better)
        # Prefer workflows with 3-6 steps
        num_steps = len(plan["workflow"])
        if 3 <= num_steps <= 6:
            metrics["complexity"] = 1.0
        elif num_steps < 3:
            metrics["complexity"] = 0.5  # Too simple
        else:
            metrics["complexity"] = max(0.0, 1.0 - (num_steps - 6) * 0.1)  # Too complex

        # 4. Parallelism score (0-1)
        # Reward workflows that can run steps in parallel
        max_parallel_steps = self._count_max_parallel(plan["workflow"])
        metrics["parallelism"] = min(1.0, max_parallel_steps / 2.0)

        # 5. Rationale quality score (0-1)
        rationale_length = len(plan.get("rationale", ""))
        if rationale_length > 100:
            metrics["rationale_quality"] = 1.0
        elif rationale_length > 50:
            metrics["rationale_quality"] = 0.7
        else:
            metrics["rationale_quality"] = 0.3

        # Compute weighted overall score
        weights = {
            "validity": 0.4,       # Most important
            "completeness": 0.2,
            "complexity": 0.2,
            "parallelism": 0.1,
            "rationale_quality": 0.1,
        }

        overall_score = sum(metrics[k] * weights[k] for k in weights)

        return overall_score, metrics

    def _count_max_parallel(self, workflow: list[dict[str, Any]]) -> int:
        """Count maximum number of steps that can run in parallel."""
        if not workflow:
            return 0

        # Build dependency graph
        step_deps = {step["step_id"]: set(step.get("depends_on", [])) for step in workflow}

        # Count steps at each level
        max_parallel = 0
        completed = set()

        while len(completed) < len(workflow):
            # Find steps that can run now (all deps completed)
            ready = [
                step_id for step_id, deps in step_deps.items()
                if step_id not in completed and deps.issubset(completed)
            ]

            if not ready:
                break  # Cycle detected or error

            max_parallel = max(max_parallel, len(ready))
            completed.update(ready)

        return max_parallel
