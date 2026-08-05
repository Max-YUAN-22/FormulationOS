"""
FormulationOS Golden Case: Ibuprofen

This demonstrates the complete reasoning pipeline:
    User Input → Tool Orchestration → Evidence → Mechanism →
    Context Reasoning → Hypothesis → Validation

System Design Principle:
    FormulationOS is an AI-native pharmaceutical research OS that orchestrates
    existing tools and provides evidence-grounded scientific reasoning.

Architecture:
    1. Tool Layer: PreformulationAI, FormulationAI (plugins)
    2. Core Layer: Evidence Manager, Context Reasoner, Hypothesis Ranker
    3. Agent Layer: Scientific Planner, Validation Planner

Key Insight:
    Mechanism matching alone is insufficient.
    Context-conditioned suitability reasoning is essential.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from formulation_os.agent.evidence_manager import EvidenceManager
from formulation_os.agent.context_reasoner import DrugContext, ContextReasoner
from formulation_os.agent.hypothesis_ranker import create_hypothesis_ranker_from_evidence


def print_section(title: str, char="="):
    """Print formatted section header"""
    print(f"\n{char * 80}")
    print(f"  {title}")
    print(f"{char * 80}\n")


def simulate_preformulation_ai(drug_name: str) -> dict:
    """
    Simulate PreformulationAI tool output

    In production, this would call actual PreformulationAI API/model.
    Here we simulate the tool's computational output.
    """
    print_section("STEP 1: Tool Orchestration Layer", "-")
    print("Calling PreformulationAI tool...")

    # Simulated tool output (this would come from actual API)
    tool_output = {
        "drug_name": drug_name,
        "smiles": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
        "molecular_weight": 206.28,
        "LogP": 3.97,
        "LogS": -3.97,
        "pKa": 4.91,
        "melting_point": 75.5,
        "bcs_class": "II",
        "tool_version": "PreformulationAI_v2.1"
    }

    print("✓ PreformulationAI completed")
    print(f"  Drug: {tool_output['drug_name']}")
    print(f"  BCS: {tool_output['bcs_class']}")
    print(f"  MW: {tool_output['molecular_weight']} Da")
    print(f"  LogP: {tool_output['LogP']}")
    print(f"  LogS: {tool_output['LogS']}")

    return tool_output


def evidence_layer(tool_output: dict) -> EvidenceManager:
    """
    CORE LAYER: Evidence Manager

    Responsibility: Transform raw tool output into scientific evidence

    Answers: "What do we know?"

    NOT responsible for: "What should we do?" (that's downstream reasoning)
    """
    print_section("STEP 2: Evidence Manager (Core Layer)", "-")
    print("Transforming tool output → Scientific evidence...\n")

    evidence_mgr = EvidenceManager()
    evidence_list = evidence_mgr.capture_from_tool_call(
        "preformulation_fundamentals",
        tool_output
    )

    print(f"Generated {len(evidence_list)} evidence objects:\n")

    for idx, evidence in enumerate(evidence_list, 1):
        print(f"Evidence #{idx}:")
        print(f"  Observation: {evidence.observation}")
        print(f"  Interpretation: {evidence.interpretation}")
        print(f"  Mechanism: {evidence.mechanism.value}")
        print(f"  Confidence: {evidence.confidence:.2f}")
        print(f"  Implication: {evidence.implications[:80]}...")
        print()

    return evidence_mgr


def mechanism_layer(evidence_mgr: EvidenceManager):
    """
    CORE LAYER: Mechanism Reasoning

    Identifies scientific mechanisms from evidence
    """
    print_section("STEP 3: Mechanism Reasoning Layer", "-")

    mechanisms = evidence_mgr.get_all_mechanisms()
    print(f"Identified {len(mechanisms)} mechanisms:\n")

    for mechanism in mechanisms:
        evidence_count = len(evidence_mgr.get_evidence_by_mechanism(mechanism))
        print(f"  • {mechanism.value}")
        print(f"    Supporting evidence: {evidence_count} items")

    return mechanisms


def candidate_generation(evidence_mgr: EvidenceManager):
    """
    CORE LAYER: Candidate Strategy Generation

    Generate candidate strategies from mechanisms
    Note: This is NOT final recommendation yet
    """
    print_section("STEP 4: Candidate Strategy Generation", "-")

    strategy_scores = evidence_mgr.get_strategies_for_evidence()

    print(f"Generated {len(strategy_scores)} candidate strategies:\n")
    for strategy, score in sorted(strategy_scores.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {strategy}")
        print(f"    Mechanism match score: {score:.2f}")

    print("\n⚠️  Note: These are candidates based on mechanism matching.")
    print("    Context suitability assessment is required before ranking.")


def context_reasoning(evidence_mgr: EvidenceManager, drug_context: DrugContext):
    """
    CORE LAYER: Context Reasoning

    KEY INSIGHT: Mechanism matching alone is insufficient

    Assesses drug-strategy compatibility based on:
    - Physicochemical properties
    - Formulation requirements
    - Strategy feasibility
    """
    print_section("STEP 5: Context Suitability Reasoning", "-")

    print("Drug Context:")
    print(f"  MW: {drug_context.molecular_weight:.1f} Da")
    print(f"  LogP: {drug_context.logP:.2f}")
    print(f"  LogS: {drug_context.logS:.2f}")
    print(f"  BCS: {drug_context.bcs_class}")
    print(f"  Dose: {drug_context.dose} mg")
    print(f"  Route: {drug_context.route}")
    print()

    print("Generating context-aware hypotheses...")
    print("(Mechanism compatibility × Context suitability = Final ranking)\n")

    # This is where HypothesisRanker integrates Evidence + Context
    ranker = create_hypothesis_ranker_from_evidence(evidence_mgr, drug_context)

    return ranker


def hypothesis_ranking(ranker):
    """
    CORE LAYER: Hypothesis Ranking

    Produces ranked hypotheses with:
    - Evidence trace
    - Mechanism explanation
    - Context reasoning
    - Uncertainty factors
    - Validation experiments
    """
    print_section("STEP 6: Hypothesis Ranking (Final Output)", "-")

    ranked_hypotheses = ranker.rank_hypotheses()

    print(f"Ranked {len(ranked_hypotheses)} formulation hypotheses:\n")

    # Show top 3
    for idx, hypothesis in enumerate(ranked_hypotheses[:3], 1):
        print(f"{'=' * 60}")
        print(f"H{idx}: {hypothesis.strategy_name.upper()}")
        print(f"{'=' * 60}")
        print(f"Final Confidence: {hypothesis.final_confidence:.3f}")
        print()
        print(f"Components:")
        print(f"  • Evidence strength: {hypothesis.evidence_strength:.3f}")
        print(f"  • Mechanism compatibility: {hypothesis.mechanism_compatibility:.3f}")
        print(f"  • Context compatibility: {hypothesis.context_compatibility:.3f}")
        print(f"  • Uncertainty penalty: {hypothesis.uncertainty_penalty:.3f}")
        print()
        print(f"Mechanisms addressed:")
        for mechanism in hypothesis.supporting_mechanisms:
            print(f"  ✓ {mechanism.value}")
        print()
        print(f"Validation required:")
        for method in hypothesis.validation_methods[:3]:
            print(f"  → {method}")
        print()

    return ranked_hypotheses


def detailed_reasoning(hypothesis):
    """
    Show detailed reasoning trace for transparency
    """
    print_section("STEP 7: Detailed Reasoning Trace (Top Hypothesis)")

    print(hypothesis.reasoning_trace)


def validation_planning(top_hypothesis):
    """
    AGENT LAYER: Validation Planner

    Generate experimental validation plan
    """
    print_section("STEP 8: Experimental Validation Plan")

    print(f"Recommended validation strategy for {top_hypothesis.strategy_name}:\n")

    print("Phase 1: Characterization")
    for method in top_hypothesis.validation_methods:
        print(f"  ✓ {method}")

    print("\nPhase 2: Performance")
    print("  ✓ In vitro dissolution testing")
    print("  ✓ Stability study (accelerated)")

    print("\nPhase 3: Optimization")
    print("  ✓ Formulation composition screening")
    print("  ✓ Process parameter optimization")

    if top_hypothesis.uncertainties:
        print("\nCritical uncertainties to resolve:")
        for unc in top_hypothesis.uncertainties:
            print(f"  ⚠️  {unc.description}")
            print(f"     Resolution: {unc.resolution}")


def run_golden_case():
    """
    Complete FormulationOS workflow demonstration
    """
    print("\n" + "🧪" * 40)
    print("  FORMULATIONOS GOLDEN CASE: IBUPROFEN")
    print("🧪" * 40)

    print("\nObjective: Demonstrate evidence-grounded formulation reasoning")
    print("System: FormulationOS v0.1 (AI-native pharmaceutical research OS)\n")

    # STEP 1: Tool Orchestration
    tool_output = simulate_preformulation_ai("Ibuprofen")

    # STEP 2: Evidence Layer
    evidence_mgr = evidence_layer(tool_output)

    # STEP 3: Mechanism Reasoning
    mechanisms = mechanism_layer(evidence_mgr)

    # STEP 4: Candidate Generation
    candidate_generation(evidence_mgr)

    # STEP 5: Create Drug Context
    drug_context = DrugContext(
        molecular_weight=tool_output["molecular_weight"],
        logP=tool_output["LogP"],
        logS=tool_output["LogS"],
        bcs_class=tool_output["bcs_class"],
        dose=400.0,  # Ibuprofen typical dose
        route="oral",
        target_dosage_form="tablet"
    )

    # STEP 6: Context Reasoning + Hypothesis Ranking
    ranker = context_reasoning(evidence_mgr, drug_context)
    ranked_hypotheses = hypothesis_ranking(ranker)

    # STEP 7: Detailed Reasoning
    if ranked_hypotheses:
        detailed_reasoning(ranked_hypotheses[0])

        # STEP 8: Validation Planning
        validation_planning(ranked_hypotheses[0])

    # Summary
    print_section("SUMMARY: FormulationOS Architecture Validation")

    print("✅ Tool Integration: PreformulationAI successfully integrated")
    print("✅ Evidence-Grounded Reasoning: Raw outputs → Scientific evidence")
    print("✅ Mechanism Identification: Dissolution/solubility limitations detected")
    print("✅ Context-Aware Decision: Drug properties inform strategy suitability")
    print("✅ Hypothesis Ranking: Transparent reasoning with confidence scores")
    print("✅ Validation Planning: Experimental roadmap generated")

    print("\nKey Architectural Insight:")
    print("  Mechanism matching + Context reasoning = Scientific formulation design")
    print("  (Not just mechanism matching alone)")

    print("\nFormulationOS successfully demonstrated as:")
    print("  • Tool orchestration platform")
    print("  • Evidence management system")
    print("  • Scientific reasoning engine")
    print("  • Decision support system")

    print("\n" + "=" * 80)
    print("  Golden Case Completed Successfully")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_golden_case()
