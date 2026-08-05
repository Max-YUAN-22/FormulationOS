"""
FormulationOS Benchmark Cases

Carefully selected drugs representing different formulation challenges
to validate Context-Aware Reasoning vs. LLM-only and Mechanism-only approaches.

Selection Criteria:
1. Cover diverse BCS classes and physicochemical challenges
2. Have well-established formulation approaches (ground truth available)
3. Include cases where context reasoning should catch practical constraints
"""

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class BenchmarkDrug:
    """
    A benchmark drug case for evaluating formulation AI systems
    """
    drug_name: str
    smiles: str

    # Physicochemical properties
    molecular_weight: float
    logp: float
    logs: float  # Aqueous solubility
    bcs_class: str
    dose: float  # Typical dose in mg

    # Primary formulation challenge
    primary_challenge: str

    # Ground truth: clinically validated strategies
    clinically_validated_strategies: List[str]

    # Expected ranking for FormulationOS
    expected_top_strategy: str

    # Context constraints that should be identified
    context_constraints: List[str]

    # Strategies that mechanism-only approach might incorrectly prioritize
    mechanism_only_trap: Optional[str] = None
    trap_reason: Optional[str] = None


# ============================================================================
# Benchmark Suite: 8 Representative Drugs
# ============================================================================

BENCHMARK_CASES = [

    # Case 1: Ibuprofen (BCS II, moderate dose, hydrophobic weak acid)
    BenchmarkDrug(
        drug_name="Ibuprofen",
        smiles="CC(C)Cc1ccc(cc1)C(C)C(=O)O",
        molecular_weight=206.28,
        logp=3.5,
        logs=-3.97,
        bcs_class="II",
        dose=400.0,
        primary_challenge="Poor aqueous solubility (dissolution-limited)",
        clinically_validated_strategies=[
            "Solid dispersion",
            "Nanocrystal",
            "Salt formation"
        ],
        expected_top_strategy="Solid dispersion",
        context_constraints=[
            "High dose (400mg) limits cyclodextrin feasibility",
            "Manufacturing scalability required for OTC market",
            "Stability critical for long shelf life"
        ],
        mechanism_only_trap="Cyclodextrin complexation",
        trap_reason="MW suits cavity, but dose burden creates practical constraint"
    ),

    # Case 2: Carbamazepine (BCS II, low dose, polymorphism issue)
    BenchmarkDrug(
        drug_name="Carbamazepine",
        smiles="NC(=O)N1c2ccccc2C=Cc3ccccc13",
        molecular_weight=236.27,
        logp=2.45,
        logs=-3.2,
        bcs_class="II",
        dose=200.0,
        primary_challenge="Poor solubility + polymorphism (crystal form instability)",
        clinically_validated_strategies=[
            "Solid dispersion",
            "Cocrystal",
            "Cyclodextrin complex"
        ],
        expected_top_strategy="Solid dispersion",
        context_constraints=[
            "Form IV → Form III transition in solid state",
            "Amorphization prevents polymorphic transition",
            "Moderate dose allows polymer formulations"
        ],
        mechanism_only_trap=None,
        trap_reason=None
    ),

    # Case 3: Ritonavir (BCS II/IV, very lipophilic, high dose)
    BenchmarkDrug(
        drug_name="Ritonavir",
        smiles="CC(C)c1nc(cn1C(C)C)CN(C)C(=O)NC(C(C)C)CC(C(Cc2ccccc2)NC(=O)OCC3CCCCC3)O",
        molecular_weight=720.95,
        logp=5.63,
        logs=-5.8,
        bcs_class="II/IV",
        dose=600.0,
        primary_challenge="Extreme lipophilicity + poor solubility",
        clinically_validated_strategies=[
            "Lipid-based formulation (SEDDS/SMEDDS)",
            "Solid dispersion"
        ],
        expected_top_strategy="Lipid-based formulation",
        context_constraints=[
            "Very high LogP (5.63) favors lipid carriers",
            "High MW (721 Da) limits cyclodextrin",
            "High dose (600mg) requires efficient solubilization"
        ],
        mechanism_only_trap="Cyclodextrin",
        trap_reason="MW too large for efficient cavity inclusion"
    ),

    # Case 4: Paclitaxel (BCS IV, extremely poor solubility, low dose)
    BenchmarkDrug(
        drug_name="Paclitaxel",
        smiles="CC1=C2[C@@]([C@]([C@H]([C@@H]3[C@]4([C@H](OC4)C[C@@H]([C@]3(C(=O)[C@@H]2OC(=O)C)C)O)OC(=O)C)OC(=O)c5ccccc5)(C[C@@H]1OC(=O)[C@H](O)[C@@H](NC(=O)c6ccccc6)c7ccccc7)O)(C)C",
        molecular_weight=853.91,
        logp=3.0,
        logs=-6.5,
        bcs_class="IV",
        dose=175.0,  # mg/m² for IV, but considering oral development
        primary_challenge="Extremely poor solubility + high MW",
        clinically_validated_strategies=[
            "Nanocrystal",
            "Polymeric micelles",
            "Albumin nanoparticle (Abraxane)"
        ],
        expected_top_strategy="Nanocrystal",
        context_constraints=[
            "Very high MW (854 Da) excludes cyclodextrin",
            "Low permeability (BCS IV) limits simple solubilization",
            "Particle size reduction critical"
        ],
        mechanism_only_trap="Cyclodextrin",
        trap_reason="MW far exceeds cavity capacity"
    ),

    # Case 5: Celecoxib (BCS II, moderate lipophilicity)
    BenchmarkDrug(
        drug_name="Celecoxib",
        smiles="Cc1ccc(cc1)c2cc(nn2c3ccc(cc3)S(=O)(=O)N)C(F)(F)F",
        molecular_weight=381.37,
        logp=3.5,
        logs=-4.3,
        bcs_class="II",
        dose=200.0,
        primary_challenge="Poor solubility (dissolution-limited absorption)",
        clinically_validated_strategies=[
            "Solid dispersion",
            "Nanocrystal",
            "Self-emulsifying"
        ],
        expected_top_strategy="Solid dispersion",
        context_constraints=[
            "Moderate dose (200mg) allows polymer formulations",
            "BCS II → dissolution enhancement sufficient",
            "Amorphization provides supersaturation"
        ],
        mechanism_only_trap=None,
        trap_reason=None
    ),

    # Case 6: Fenofibrate (BCS II, lipophilic, prodrug consideration)
    BenchmarkDrug(
        drug_name="Fenofibrate",
        smiles="CC(C)(Oc1ccc(cc1)C(=O)c2ccc(Cl)cc2)C(=O)OC(C)C",
        molecular_weight=360.83,
        logp=5.24,
        logs=-6.2,
        bcs_class="II",
        dose=145.0,
        primary_challenge="Very poor solubility + high lipophilicity",
        clinically_validated_strategies=[
            "Nanocrystal (TriCor)",
            "Solid dispersion",
            "Self-emulsifying"
        ],
        expected_top_strategy="Nanocrystal",
        context_constraints=[
            "High LogP (5.24) suggests lipid affinity",
            "Particle size reduction very effective (TriCor precedent)",
            "Moderate dose compatible with nanocrystal"
        ],
        mechanism_only_trap=None,
        trap_reason=None
    ),

    # Case 7: Griseofulvin (BCS II, low dose, classic nanocrystal case)
    BenchmarkDrug(
        drug_name="Griseofulvin",
        smiles="COc1cc2c(c(c1Cl)OC)C(=O)CC3(C2=O)C=C(CC(C3)OC)C",
        molecular_weight=352.77,
        logp=2.18,
        logs=-4.0,
        bcs_class="II",
        dose=500.0,
        primary_challenge="Poor solubility despite moderate LogP",
        clinically_validated_strategies=[
            "Nanocrystal",
            "Solid dispersion"
        ],
        expected_top_strategy="Nanocrystal",
        context_constraints=[
            "High dose (500mg) challenges solid dispersion polymer amount",
            "Particle size reduction historically very effective",
            "Moderate LogP makes simple size reduction sufficient"
        ],
        mechanism_only_trap="Solid dispersion",
        trap_reason="High dose creates large polymer burden"
    ),

    # Case 8: Cyclosporine (BCS II/IV, very high MW, very lipophilic)
    BenchmarkDrug(
        drug_name="Cyclosporine",
        smiles="CCC1C(=O)N(CC(=O)N(C(C(=O)NC(C(=O)N(C(C(=O)NC(C(=O)NC(C(=O)N(C(C(=O)N(C(C(=O)N(C(C(=O)N(C(C(=O)N1)C(C(C)CC=CC)O)C)C(C)C)C)CC(C)C)C)CC(C)C)C)C)C)CC(C)C)C)C(C)C)CC(C)C)C)C",
        molecular_weight=1202.61,
        logp=3.0,
        logs=-6.8,
        bcs_class="II/IV",
        dose=300.0,
        primary_challenge="Very high MW + poor solubility + poor permeability",
        clinically_validated_strategies=[
            "Self-emulsifying (Neoral)",
            "Microemulsion"
        ],
        expected_top_strategy="Self-emulsifying",
        context_constraints=[
            "Very high MW (1203 Da) excludes most polymer-based strategies",
            "Lipophilic peptide benefits from lipid carriers",
            "Microemulsion formation enhances both solubility and permeability"
        ],
        mechanism_only_trap="Solid dispersion",
        trap_reason="MW too high for effective polymer dispersion"
    ),
]


def get_benchmark_case(drug_name: str) -> Optional[BenchmarkDrug]:
    """Retrieve a specific benchmark case by drug name"""
    for case in BENCHMARK_CASES:
        if case.drug_name.lower() == drug_name.lower():
            return case
    return None


def get_all_benchmark_drugs() -> List[str]:
    """Get list of all benchmark drug names"""
    return [case.drug_name for case in BENCHMARK_CASES]


def get_challenge_category_distribution() -> Dict[str, List[str]]:
    """Group drugs by challenge category"""
    categories = {
        "BCS II (moderate MW, moderate dose)": [],
        "BCS II (high dose burden)": [],
        "High MW (>700 Da)": [],
        "Extreme lipophilicity (LogP >5)": [],
        "Polymorphism/stability": []
    }

    for case in BENCHMARK_CASES:
        if case.molecular_weight > 700:
            categories["High MW (>700 Da)"].append(case.drug_name)
        if case.logp > 5.0:
            categories["Extreme lipophilicity (LogP >5)"].append(case.drug_name)
        if case.dose > 400:
            categories["BCS II (high dose burden)"].append(case.drug_name)
        if "polymorphism" in case.primary_challenge.lower():
            categories["Polymorphism/stability"].append(case.drug_name)

    return categories


if __name__ == "__main__":
    print("=" * 80)
    print("FormulationOS Benchmark Suite")
    print("=" * 80)
    print()

    print(f"Total Cases: {len(BENCHMARK_CASES)}")
    print()

    for i, case in enumerate(BENCHMARK_CASES, 1):
        print(f"{i}. {case.drug_name}")
        print(f"   BCS: {case.bcs_class} | MW: {case.molecular_weight:.1f} Da | LogP: {case.logp} | Dose: {case.dose}mg")
        print(f"   Challenge: {case.primary_challenge}")
        print(f"   Expected: {case.expected_top_strategy}")
        if case.mechanism_only_trap:
            print(f"   ⚠ Mechanism trap: {case.mechanism_only_trap}")
        print()

    print("=" * 80)
    print("Context Reasoning Test Cases:")
    print("=" * 80)
    traps = [c for c in BENCHMARK_CASES if c.mechanism_only_trap]
    print(f"Found {len(traps)} cases where mechanism-only reasoning may fail:")
    for case in traps:
        print(f"  • {case.drug_name}: {case.mechanism_only_trap}")
        print(f"    Reason: {case.trap_reason}")
    print()
