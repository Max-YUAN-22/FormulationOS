"""
Benchmark Evaluation Framework for FormulationOS

Evaluates three approaches:
1. LLM-only baseline (direct GPT recommendation)
2. Mechanism-only baseline (rule-based mechanism matching)
3. FormulationOS (evidence-grounded + context-aware)

Key Metrics (NOT simple accuracy):
- Top-1 Strategy Agreement (with clinical validation)
- Context Violation Rate (falling into mechanism-only traps)
- Explanation Quality (evidence grounding, uncertainty acknowledgment)
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import json


class EvaluationMetric(Enum):
    """Evaluation dimensions for formulation AI systems"""
    TOP1_AGREEMENT = "top1_agreement"  # Does top-1 match expected strategy?
    CONTEXT_VIOLATION = "context_violation"  # Did it fall into mechanism trap?
    EVIDENCE_GROUNDED = "evidence_grounded"  # Is recommendation supported by evidence?
    UNCERTAINTY_ACKNOWLEDGED = "uncertainty_acknowledged"  # Does it acknowledge limitations?
    VALIDATION_PLAN = "validation_plan"  # Does it provide experimental validation?


@dataclass
class FormulationRecommendation:
    """
    Output from a formulation AI system
    """
    system_name: str  # "LLM-only", "Mechanism-only", "FormulationOS"
    drug_name: str

    # Primary recommendation
    top_strategy: str
    confidence_score: float

    # Ranked alternatives
    ranked_strategies: List[Dict[str, float]]  # [{strategy: score}, ...]

    # Reasoning trace
    reasoning_trace: str  # Full explanation
    evidence_cited: List[str]  # Evidence objects referenced
    context_constraints_identified: List[str]  # Practical constraints mentioned

    # Quality indicators
    acknowledges_uncertainty: bool
    provides_validation_plan: bool
    explains_rejection: bool  # Does it explain why alternatives rejected?


@dataclass
class BenchmarkResult:
    """
    Evaluation result for one drug across all systems
    """
    drug_name: str

    # Ground truth
    clinically_validated: List[str]
    expected_top_strategy: str
    mechanism_trap: Optional[str]

    # System outputs
    llm_only: FormulationRecommendation
    mechanism_only: FormulationRecommendation
    formulation_os: FormulationRecommendation

    # Evaluation scores
    scores: Dict[str, Dict[str, float]]  # {system_name: {metric: score}}


def evaluate_top1_agreement(
    recommended: str,
    expected: str,
    clinically_validated: List[str]
) -> float:
    """
    Score: 1.0 if top-1 matches expected OR is in clinically validated list
           0.5 if in validated list but not top expected
           0.0 otherwise

    Rationale: Multiple strategies may be valid, but we prioritize expected top choice
    """
    recommended_clean = recommended.lower().strip()
    expected_clean = expected.lower().strip()

    # Exact match with expected
    if recommended_clean == expected_clean or expected_clean in recommended_clean:
        return 1.0

    # Match with any clinically validated strategy
    for validated in clinically_validated:
        validated_clean = validated.lower().strip()
        if validated_clean in recommended_clean or recommended_clean in validated_clean:
            return 0.5

    return 0.0


def evaluate_context_violation(
    recommended: str,
    mechanism_trap: Optional[str],
    context_constraints_identified: List[str]
) -> float:
    """
    Score: 1.0 if avoided trap OR no trap exists
           0.5 if recommended trap but identified constraints
           0.0 if fell into trap without acknowledging context

    This is the KEY METRIC for demonstrating context-aware reasoning
    """
    if not mechanism_trap:
        return 1.0  # No trap to fall into

    recommended_clean = recommended.lower().strip()
    trap_clean = mechanism_trap.lower().strip()

    # Did it recommend the trap strategy?
    if trap_clean in recommended_clean or recommended_clean in trap_clean:
        # Did it at least identify relevant context constraints?
        if len(context_constraints_identified) > 0:
            return 0.5  # Recommended trap but aware of issues
        else:
            return 0.0  # Fell into trap blindly

    return 1.0  # Avoided the trap


def evaluate_evidence_grounding(
    evidence_cited: List[str],
    reasoning_trace: str
) -> float:
    """
    Score based on evidence citation quality

    1.0: Multiple evidence objects cited with interpretation
    0.7: Some evidence cited
    0.3: Reasoning present but no explicit evidence
    0.0: No reasoning or evidence
    """
    if not reasoning_trace or len(reasoning_trace) < 50:
        return 0.0

    if len(evidence_cited) >= 2:
        return 1.0
    elif len(evidence_cited) == 1:
        return 0.7
    elif "evidence" in reasoning_trace.lower() or "observation" in reasoning_trace.lower():
        return 0.3
    else:
        return 0.3  # Has reasoning but no explicit evidence grounding


def evaluate_uncertainty_acknowledgment(
    acknowledges_uncertainty: bool,
    reasoning_trace: str
) -> float:
    """
    Score: 1.0 if explicitly acknowledges uncertainty/limitations
           0.5 if mentions constraints or validation needs
           0.0 if presents recommendation as certain

    Scientific rigor requires acknowledging what we don't know
    """
    if acknowledges_uncertainty:
        return 1.0

    # Check for uncertainty language
    uncertainty_keywords = [
        "uncertainty", "limitation", "unknown", "requires validation",
        "needs experimental", "to be confirmed", "preliminary"
    ]

    trace_lower = reasoning_trace.lower()
    for keyword in uncertainty_keywords:
        if keyword in trace_lower:
            return 0.5

    return 0.0


def evaluate_validation_plan(
    provides_validation_plan: bool,
    reasoning_trace: str
) -> float:
    """
    Score: 1.0 if provides specific validation experiments
           0.5 if mentions validation need
           0.0 if no validation discussion

    AI Scientist should propose how to test hypotheses
    """
    if provides_validation_plan:
        return 1.0

    # Check for validation language
    validation_keywords = [
        "dissolution test", "characterization", "stability",
        "DSC", "XRPD", "bioavailability", "pharmacokinetic"
    ]

    trace_lower = reasoning_trace.lower()
    matches = sum(1 for keyword in validation_keywords if keyword in trace_lower)

    if matches >= 2:
        return 0.5
    else:
        return 0.0


def compute_benchmark_scores(result: BenchmarkResult) -> Dict[str, Dict[str, float]]:
    """
    Compute all evaluation metrics for all systems
    """
    scores = {}

    for system_name, recommendation in [
        ("LLM-only", result.llm_only),
        ("Mechanism-only", result.mechanism_only),
        ("FormulationOS", result.formulation_os)
    ]:
        scores[system_name] = {
            "top1_agreement": evaluate_top1_agreement(
                recommendation.top_strategy,
                result.expected_top_strategy,
                result.clinically_validated
            ),
            "context_violation_avoided": evaluate_context_violation(
                recommendation.top_strategy,
                result.mechanism_trap,
                recommendation.context_constraints_identified
            ),
            "evidence_grounding": evaluate_evidence_grounding(
                recommendation.evidence_cited,
                recommendation.reasoning_trace
            ),
            "uncertainty_acknowledgment": evaluate_uncertainty_acknowledgment(
                recommendation.acknowledges_uncertainty,
                recommendation.reasoning_trace
            ),
            "validation_plan": evaluate_validation_plan(
                recommendation.provides_validation_plan,
                recommendation.reasoning_trace
            )
        }

    return scores


def aggregate_benchmark_results(results: List[BenchmarkResult]) -> Dict[str, Dict[str, float]]:
    """
    Aggregate scores across all benchmark cases
    Returns: {system_name: {metric: avg_score}}
    """
    system_names = ["LLM-only", "Mechanism-only", "FormulationOS"]
    metric_names = [
        "top1_agreement",
        "context_violation_avoided",
        "evidence_grounding",
        "uncertainty_acknowledgment",
        "validation_plan"
    ]

    aggregated = {system: {metric: [] for metric in metric_names} for system in system_names}

    for result in results:
        scores = compute_benchmark_scores(result)
        for system in system_names:
            for metric in metric_names:
                aggregated[system][metric].append(scores[system][metric])

    # Compute averages
    final_scores = {}
    for system in system_names:
        final_scores[system] = {}
        for metric in metric_names:
            values = aggregated[system][metric]
            final_scores[system][metric] = sum(values) / len(values) if values else 0.0

    return final_scores


def print_benchmark_summary(results: List[BenchmarkResult]):
    """
    Print human-readable benchmark summary
    """
    print("=" * 80)
    print("BENCHMARK EVALUATION SUMMARY")
    print("=" * 80)
    print()

    aggregated = aggregate_benchmark_results(results)

    print("Average Scores Across All Cases:")
    print()

    # Header
    print(f"{'Metric':<30} {'LLM-only':<12} {'Mechanism':<12} {'FormulationOS':<12}")
    print("-" * 80)

    metrics = [
        ("Top-1 Agreement", "top1_agreement"),
        ("Context Violation Avoided", "context_violation_avoided"),
        ("Evidence Grounding", "evidence_grounding"),
        ("Uncertainty Acknowledgment", "uncertainty_acknowledgment"),
        ("Validation Plan", "validation_plan")
    ]

    for metric_name, metric_key in metrics:
        llm_score = aggregated["LLM-only"][metric_key]
        mech_score = aggregated["Mechanism-only"][metric_key]
        fos_score = aggregated["FormulationOS"][metric_key]

        print(f"{metric_name:<30} {llm_score:<12.2f} {mech_score:<12.2f} {fos_score:<12.2f}")

    print()
    print("=" * 80)
    print("KEY FINDINGS:")
    print("=" * 80)

    # Context violation rate (invert to get violation rate)
    context_trap_cases = sum(1 for r in results if r.mechanism_trap is not None)
    if context_trap_cases > 0:
        llm_violations = sum(
            1 for r in results
            if r.mechanism_trap and compute_benchmark_scores(r)["LLM-only"]["context_violation_avoided"] == 0.0
        )
        mech_violations = sum(
            1 for r in results
            if r.mechanism_trap and compute_benchmark_scores(r)["Mechanism-only"]["context_violation_avoided"] == 0.0
        )
        fos_violations = sum(
            1 for r in results
            if r.mechanism_trap and compute_benchmark_scores(r)["FormulationOS"]["context_violation_avoided"] == 0.0
        )

        print(f"Context Violation Rate ({context_trap_cases} cases with known traps):")
        print(f"  LLM-only:        {llm_violations}/{context_trap_cases} = {llm_violations/context_trap_cases*100:.1f}%")
        print(f"  Mechanism-only:  {mech_violations}/{context_trap_cases} = {mech_violations/context_trap_cases*100:.1f}%")
        print(f"  FormulationOS:   {fos_violations}/{context_trap_cases} = {fos_violations/context_trap_cases*100:.1f}%")
        print()


def save_benchmark_results(results: List[BenchmarkResult], output_path: str):
    """
    Save detailed benchmark results to JSON
    """
    output = {
        "summary": aggregate_benchmark_results(results),
        "detailed_results": []
    }

    for result in results:
        scores = compute_benchmark_scores(result)
        output["detailed_results"].append({
            "drug_name": result.drug_name,
            "expected_strategy": result.expected_top_strategy,
            "mechanism_trap": result.mechanism_trap,
            "recommendations": {
                "LLM-only": {
                    "strategy": result.llm_only.top_strategy,
                    "confidence": result.llm_only.confidence_score,
                    "scores": scores["LLM-only"]
                },
                "Mechanism-only": {
                    "strategy": result.mechanism_only.top_strategy,
                    "confidence": result.mechanism_only.confidence_score,
                    "scores": scores["Mechanism-only"]
                },
                "FormulationOS": {
                    "strategy": result.formulation_os.top_strategy,
                    "confidence": result.formulation_os.confidence_score,
                    "scores": scores["FormulationOS"]
                }
            }
        })

    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"✓ Detailed results saved to: {output_path}")


if __name__ == "__main__":
    print("Benchmark Evaluation Framework loaded.")
    print()
    print("Key Metrics:")
    print("  1. Top-1 Agreement: Does recommendation match clinical validation?")
    print("  2. Context Violation Avoided: Does it fall into mechanism-only traps?")
    print("  3. Evidence Grounding: Is reasoning supported by evidence?")
    print("  4. Uncertainty Acknowledgment: Does it acknowledge limitations?")
    print("  5. Validation Plan: Does it propose experimental validation?")
    print()
    print("This is NOT a simple accuracy test.")
    print("This evaluates scientific reasoning quality.")
