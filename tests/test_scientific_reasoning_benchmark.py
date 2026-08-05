"""
Scientific Reasoning Benchmark Test for FormulationOS

This test validates the Evidence → Mechanism → Hypothesis reasoning chain.

Test Philosophy:
    We are NOT testing code correctness.
    We are testing SCIENTIFIC REASONING correctness.

Success Criteria:
    1. Evidence correctly interprets physicochemical properties
    2. Mechanisms are properly inferred from evidence
    3. Strategies match pharmaceutical logic
    4. Confidence scores reflect evidence strength
    5. Uncertainties are identified appropriately
    6. Reasoning is transparent and traceable

Benchmark Drugs:
    1. Ibuprofen - BCS II, solubility challenge
    2. Carbamazepine - poor solubility + polymorphism
    3. Ritonavir - extreme lipophilicity, SEDDS candidate
    4. Metformin - high solubility, permeability challenge
    5. Paclitaxel - extreme insolubility, complex formulation
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from formulation_os.agent.evidence_manager import (
    EvidenceManager,
    Evidence,
    ScientificMechanism,
    EvidenceSource,
    EvidenceType
)
from formulation_os.agent.hypothesis_ranker import (
    HypothesisRanker,
    create_hypothesis_ranker_from_evidence
)
from formulation_os.agent.context_reasoner import DrugContext


def print_section(title: str):
    """Pretty print section headers"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_subsection(title: str):
    """Pretty print subsection headers"""
    print(f"\n--- {title} ---\n")


def test_ibuprofen_reasoning():
    """
    Test Case 1: Ibuprofen

    Expected behavior:
    - BCS II → DISSOLUTION_LIMITATION
    - LogS=-3.97 → SOLUBILITY_LIMITATION
    - LogP=3.8 → LIPID_SOLUBILIZATION
    - Hypotheses: solid_dispersion (top), nanocrystal, SEDDS
    - Confidence: ~0.75-0.85 for top hypothesis
    """
    print_section("TEST CASE 1: IBUPROFEN")

    # Simulate PreformulationAI tool output
    tool_result = {
        "drug_name": "Ibuprofen",
        "bcs_class": "II",
        "LogS": -3.97,
        "LogP": 3.8,
        "molecular_weight": 206.28,
        "description": "NSAIDs, oral administration"
    }

    print("Input (PreformulationAI output):")
    for key, value in tool_result.items():
        print(f"  {key}: {value}")

    # Create evidence manager and capture evidence
    evidence_mgr = EvidenceManager()
    evidence_list = evidence_mgr.capture_from_tool_call("preformulation_fundamentals", tool_result)

    print_subsection("EVIDENCE LAYER")
    print(f"Generated {len(evidence_list)} evidence objects:\n")

    for idx, evidence in enumerate(evidence_list, 1):
        print(f"Evidence #{idx}:")
        print(f"  Observation: {evidence.observation}")
        print(f"  Interpretation: {evidence.interpretation}")
        print(f"  Mechanism: {evidence.mechanism.value}")
        print(f"  Confidence: {evidence.confidence:.2f}")
        print(f"  Implications: {evidence.implications}")
        print()

    # Verify mechanisms
    print_subsection("MECHANISM LAYER")
    mechanisms = evidence_mgr.get_all_mechanisms()
    print(f"Identified {len(mechanisms)} mechanisms:\n")
    for mechanism in mechanisms:
        evidence_count = len(evidence_mgr.get_evidence_by_mechanism(mechanism))
        print(f"  • {mechanism.value} ({evidence_count} evidence)")

    # Create drug context for context-aware reasoning
    print_subsection("DRUG CONTEXT")
    drug_context = DrugContext(
        molecular_weight=tool_result["molecular_weight"],
        logP=tool_result["LogP"],
        logS=tool_result["LogS"],
        bcs_class=tool_result["bcs_class"],
        dose=200.0,  # Ibuprofen typical dose
        route="oral"
    )
    print(f"MW={drug_context.molecular_weight:.1f} Da, LogP={drug_context.logP:.1f}, "
          f"LogS={drug_context.logS:.1f}, BCS={drug_context.bcs_class}")

    # Generate hypotheses with context reasoning
    print_subsection("HYPOTHESIS GENERATION (with Context Reasoning)")
    ranker = create_hypothesis_ranker_from_evidence(evidence_mgr, drug_context)

    print(f"Generated {len(ranker.hypotheses)} hypotheses:\n")
    for hypothesis in ranker.hypotheses:
        print(f"  • {hypothesis.strategy_name}")
        print(f"    Mechanisms: {', '.join(m.value for m in hypothesis.supporting_mechanisms)}")
        print(f"    Evidence: {len(hypothesis.supporting_evidence)} items")
        print()

    # Rank hypotheses
    print_subsection("HYPOTHESIS RANKING")
    ranked = ranker.rank_hypotheses()

    for idx, hypothesis in enumerate(ranked, 1):
        print(f"H{idx}: {hypothesis.strategy_name} [Confidence: {hypothesis.final_confidence:.3f}]")
        print(f"  Evidence strength: {hypothesis.evidence_strength:.3f}")
        print(f"  Mechanism compatibility: {hypothesis.mechanism_compatibility:.3f}")
        print(f"  Uncertainty penalty: {hypothesis.uncertainty_penalty:.3f}")
        print(f"  Mechanisms: {', '.join(m.value for m in hypothesis.supporting_mechanisms)}")
        print(f"  Uncertainties: {len(hypothesis.uncertainties)}")
        print()

    # Full reasoning trace for top hypothesis
    print_subsection("DETAILED REASONING (Top Hypothesis)")
    if ranked:
        print(ranked[0].reasoning_trace)

    # Generate full report
    print_subsection("COMPLETE RANKING REPORT")
    report = ranker.generate_ranking_report()
    print(report)

    # Validation
    print_subsection("SCIENTIFIC VALIDATION")

    validation_checks = []

    # Check 1: BCS II should trigger dissolution/solubility mechanisms
    has_dissolution = ScientificMechanism.DISSOLUTION_LIMITATION in mechanisms
    has_solubility = ScientificMechanism.SOLUBILITY_LIMITATION in mechanisms
    validation_checks.append(("BCS II → dissolution/solubility mechanisms", has_dissolution or has_solubility))

    # Check 2: Top hypothesis should be solid_dispersion or nanocrystal
    top_strategy = ranked[0].strategy_name if ranked else None
    validation_checks.append(("Top strategy is solid_dispersion/nanocrystal", top_strategy in ["solid_dispersion", "nanocrystal"]))

    # Check 3: Confidence should be reasonably high (>0.6)
    top_confidence = ranked[0].final_confidence if ranked else 0
    validation_checks.append(("Top confidence > 0.6", top_confidence > 0.6))

    # Check 4: Uncertainties should be identified
    top_uncertainties = len(ranked[0].uncertainties) if ranked else 0
    validation_checks.append(("Uncertainties identified", top_uncertainties > 0))

    # Check 5: Validation methods should be specified
    top_validation = len(ranked[0].validation_methods) if ranked else 0
    validation_checks.append(("Validation methods specified", top_validation > 0))

    print("\nValidation Results:")
    all_passed = True
    for check_name, result in validation_checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {check_name}")
        if not result:
            all_passed = False

    print(f"\n{'✅ ALL CHECKS PASSED' if all_passed else '❌ SOME CHECKS FAILED'}")

    return all_passed


def test_carbamazepine_reasoning():
    """
    Test Case 2: Carbamazepine

    Challenge: Poor solubility + polymorphism
    Expected: Solid dispersion or cocrystal as top hypotheses
    """
    print_section("TEST CASE 2: CARBAMAZEPINE (Polymorphism Challenge)")

    tool_result = {
        "drug_name": "Carbamazepine",
        "bcs_class": "II",
        "LogS": -4.12,
        "LogP": 2.45,
        "molecular_weight": 236.27
    }

    print("Input:")
    for key, value in tool_result.items():
        print(f"  {key}: {value}")

    evidence_mgr = EvidenceManager()
    evidence_mgr.capture_from_tool_call("preformulation_fundamentals", tool_result)

    drug_context = DrugContext(
        molecular_weight=tool_result["molecular_weight"],
        logP=tool_result["LogP"],
        logS=tool_result["LogS"],
        bcs_class=tool_result["bcs_class"],
        dose=200.0,
        route="oral",
        polymorphism=True
    )

    ranker = create_hypothesis_ranker_from_evidence(evidence_mgr, drug_context)
    ranked = ranker.rank_hypotheses()

    print_subsection("TOP 3 HYPOTHESES")
    for idx, hypothesis in enumerate(ranked[:3], 1):
        print(f"H{idx}: {hypothesis.strategy_name} [{hypothesis.final_confidence:.3f}]")
        print(f"     Context compatibility: {hypothesis.context_compatibility:.3f}")

    # Validation: Should prioritize strategies addressing polymorphism
    top_strategy = ranked[0].strategy_name if ranked else None
    polymorphism_suitable = top_strategy in ["solid_dispersion", "cocrystal", "salt_formation"]

    print(f"\n{'✅ PASS' if polymorphism_suitable else '❌ FAIL'} - Top strategy suitable for polymorphism")

    return polymorphism_suitable


def test_ritonavir_reasoning():
    """
    Test Case 3: Ritonavir

    Challenge: Extreme lipophilicity, very poor aqueous solubility
    Expected: SEDDS or lipid formulation as top hypotheses
    """
    print_section("TEST CASE 3: RITONAVIR (Lipophilic Drug)")

    tool_result = {
        "drug_name": "Ritonavir",
        "bcs_class": "II",
        "LogS": -6.2,
        "LogP": 5.63,
        "molecular_weight": 720.95
    }

    print("Input:")
    for key, value in tool_result.items():
        print(f"  {key}: {value}")

    evidence_mgr = EvidenceManager()
    evidence_mgr.capture_from_tool_call("preformulation_fundamentals", tool_result)

    drug_context = DrugContext(
        molecular_weight=tool_result["molecular_weight"],
        logP=tool_result["LogP"],
        logS=tool_result["LogS"],
        bcs_class=tool_result["bcs_class"],
        dose=100.0,
        route="oral"
    )

    ranker = create_hypothesis_ranker_from_evidence(evidence_mgr, drug_context)
    ranked = ranker.rank_hypotheses()

    print_subsection("TOP 3 HYPOTHESES")
    for idx, hypothesis in enumerate(ranked[:3], 1):
        print(f"H{idx}: {hypothesis.strategy_name} [{hypothesis.final_confidence:.3f}]")
        print(f"     Context compatibility: {hypothesis.context_compatibility:.3f}")

    # Validation: Should include lipid-based strategies
    strategies = [h.strategy_name for h in ranked[:3]]
    has_lipid_strategy = any(s in ["SEDDS", "lipid_formulation", "solid_lipid_nanoparticle"] for s in strategies)

    print(f"\n{'✅ PASS' if has_lipid_strategy else '❌ FAIL'} - Lipid-based strategy in top 3")

    return has_lipid_strategy


def test_metformin_reasoning():
    """
    Test Case 4: Metformin

    Challenge: High solubility but low permeability (BCS III)
    Expected: Permeation enhancer strategies
    """
    print_section("TEST CASE 4: METFORMIN (Permeability Challenge)")

    tool_result = {
        "drug_name": "Metformin",
        "bcs_class": "III",
        "LogS": -0.5,
        "LogP": -0.8,
        "molecular_weight": 129.16
    }

    print("Input:")
    for key, value in tool_result.items():
        print(f"  {key}: {value}")

    evidence_mgr = EvidenceManager()
    evidence_mgr.capture_from_tool_call("preformulation_fundamentals", tool_result)

    drug_context = DrugContext(
        molecular_weight=tool_result["molecular_weight"],
        logP=tool_result["LogP"],
        logS=tool_result["LogS"],
        bcs_class=tool_result["bcs_class"],
        dose=500.0,
        route="oral"
    )

    mechanisms = evidence_mgr.get_all_mechanisms()
    print_subsection("MECHANISMS IDENTIFIED")
    for mechanism in mechanisms:
        print(f"  • {mechanism.value}")

    ranker = create_hypothesis_ranker_from_evidence(evidence_mgr, drug_context)
    ranked = ranker.rank_hypotheses()

    print_subsection("TOP 3 HYPOTHESES")
    for idx, hypothesis in enumerate(ranked[:3], 1):
        print(f"H{idx}: {hypothesis.strategy_name} [{hypothesis.final_confidence:.3f}]")

    # Validation: Should identify permeability barrier
    has_permeability_mechanism = ScientificMechanism.PERMEABILITY_BARRIER in mechanisms

    print(f"\n{'✅ PASS' if has_permeability_mechanism else '❌ FAIL'} - Permeability barrier identified")

    return has_permeability_mechanism


def test_paclitaxel_reasoning():
    """
    Test Case 5: Paclitaxel

    Challenge: Extreme insolubility, large molecule, complex formulation
    Expected: Multiple strategies with lower confidence (uncertainty high)
    """
    print_section("TEST CASE 5: PACLITAXEL (Extreme Challenge)")

    tool_result = {
        "drug_name": "Paclitaxel",
        "bcs_class": "IV",
        "LogS": -7.4,
        "LogP": 3.0,
        "molecular_weight": 853.91
    }

    print("Input:")
    for key, value in tool_result.items():
        print(f"  {key}: {value}")

    evidence_mgr = EvidenceManager()
    evidence_mgr.capture_from_tool_call("preformulation_fundamentals", tool_result)

    drug_context = DrugContext(
        molecular_weight=tool_result["molecular_weight"],
        logP=tool_result["LogP"],
        logS=tool_result["LogS"],
        bcs_class=tool_result["bcs_class"],
        dose=30.0,
        route="oral"
    )

    ranker = create_hypothesis_ranker_from_evidence(evidence_mgr, drug_context)
    ranked = ranker.rank_hypotheses()

    print_subsection("ALL HYPOTHESES")
    for idx, hypothesis in enumerate(ranked, 1):
        print(f"H{idx}: {hypothesis.strategy_name} [{hypothesis.final_confidence:.3f}]")
        print(f"     Context compatibility: {hypothesis.context_compatibility:.3f}")
        print(f"     Uncertainties: {len(hypothesis.uncertainties)}")

    # Validation: Multiple strategies should be generated, confidence should reflect difficulty
    num_hypotheses = len(ranked)
    top_confidence = ranked[0].final_confidence if ranked else 0

    print(f"\n{'✅ PASS' if num_hypotheses >= 3 else '❌ FAIL'} - Multiple strategies generated ({num_hypotheses})")
    print(f"{'✅ PASS' if top_confidence < 0.85 else '❌ FAIL'} - Confidence reflects complexity ({top_confidence:.3f})")

    return num_hypotheses >= 3 and top_confidence < 0.85


def run_benchmark_suite():
    """Run complete benchmark suite"""
    print("\n" + "🧪" * 40)
    print("  FORMULATION OS SCIENTIFIC REASONING BENCHMARK")
    print("🧪" * 40 + "\n")

    print("Objective: Validate Evidence → Mechanism → Hypothesis reasoning chain")
    print("Success: Hypotheses match pharmaceutical formulation logic\n")

    results = {}

    # Run all tests
    results["Ibuprofen"] = test_ibuprofen_reasoning()
    results["Carbamazepine"] = test_carbamazepine_reasoning()
    results["Ritonavir"] = test_ritonavir_reasoning()
    results["Metformin"] = test_metformin_reasoning()
    results["Paclitaxel"] = test_paclitaxel_reasoning()

    # Summary
    print_section("BENCHMARK SUMMARY")

    passed = sum(results.values())
    total = len(results)

    print("Test Results:\n")
    for drug, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {drug}")

    print(f"\n{'=' * 80}")
    print(f"  OVERALL: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print(f"{'=' * 80}\n")

    if passed == total:
        print("🎉 ALL TESTS PASSED - Scientific reasoning chain is validated!")
        print("\nNext Steps:")
        print("  1. Add DrugContext layer for dose/route considerations")
        print("  2. Refine uncertainty identification")
        print("  3. Integrate into main FormulationOS application")
    else:
        print("⚠️  Some tests failed - review mechanism mappings and confidence calculations")

    return passed == total


if __name__ == "__main__":
    success = run_benchmark_suite()
    sys.exit(0 if success else 1)
