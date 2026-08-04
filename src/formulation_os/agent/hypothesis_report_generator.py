"""
Hypothesis Report Generator - Scientific Reasoning Documentation

Generates structured scientific reports that explain:
1. Why each hypothesis was selected or rejected
2. Complete reasoning chain from evidence to recommendation
3. Alternative analysis (critical for scientific credibility)
4. Formulation design details
5. Experimental validation plan

This is NOT a simple output formatter.
This is the scientific documentation layer that makes FormulationOS
transparent and scientifically defensible.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class FormulationHypothesis:
    """
    Complete formulation hypothesis with reasoning
    """
    # Core recommendation
    strategy_name: str
    confidence_score: float

    # Drug context
    drug_name: str
    drug_profile: Dict

    # Scientific reasoning
    supporting_evidence: List[str] = field(default_factory=list)
    mechanism_match: float = 0.0
    context_suitability: float = 0.0
    historical_precedent: float = 0.0

    # Formulation details
    excipients: List[Dict] = field(default_factory=list)  # [{name, function, rationale}]
    process_options: List[str] = field(default_factory=list)

    # Validation
    validation_plan: List[str] = field(default_factory=list)

    # Limitations
    practical_constraints: List[str] = field(default_factory=list)
    uncertainty_factors: List[str] = field(default_factory=list)


@dataclass
class RejectedAlternative:
    """
    Documentation of why an alternative strategy was not selected

    This is CRITICAL for scientific credibility.
    A good scientist explains why alternatives don't work.
    """
    strategy_name: str
    initial_plausibility: float  # Why it seemed reasonable initially
    rejection_reason: str  # Primary reason for rejection
    incompatibility_factors: List[str] = field(default_factory=list)
    context_mismatch: List[str] = field(default_factory=list)


class HypothesisReportGenerator:
    """
    Generate comprehensive scientific reports for formulation hypotheses

    Output format similar to AI Scientist research reports:
    - Executive summary
    - Drug understanding
    - Evidence collection
    - Hypothesis generation
    - Alternative analysis (why others rejected)
    - Recommended formulation design
    - Validation plan
    """

    def __init__(self):
        self.report_template = self._load_template()

    def generate_research_report(
        self,
        primary_hypothesis: FormulationHypothesis,
        rejected_alternatives: List[RejectedAlternative],
        evidence_pool: List,
        drug_profile: Dict
    ) -> str:
        """
        Generate complete scientific research report

        Args:
            primary_hypothesis: Selected formulation approach
            rejected_alternatives: Strategies that were considered but rejected
            evidence_pool: All collected evidence
            drug_profile: Complete drug context

        Returns:
            Markdown-formatted scientific report
        """

        report_sections = []

        # Header
        report_sections.append(self._generate_header(drug_profile))

        # Section 1: Drug Understanding
        report_sections.append(self._generate_drug_section(drug_profile))

        # Section 2: Evidence Collection
        report_sections.append(self._generate_evidence_section(evidence_pool))

        # Section 3: Mechanism Diagnosis
        report_sections.append(self._generate_mechanism_section(evidence_pool))

        # Section 4: Hypothesis Generation & Ranking
        report_sections.append(self._generate_hypothesis_section(
            primary_hypothesis, rejected_alternatives
        ))

        # Section 5: Alternative Analysis (CRITICAL)
        report_sections.append(self._generate_alternative_analysis(rejected_alternatives))

        # Section 6: Formulation Design
        report_sections.append(self._generate_formulation_design(primary_hypothesis))

        # Section 7: Validation Plan
        report_sections.append(self._generate_validation_plan(primary_hypothesis))

        # Section 8: Limitations & Uncertainties
        report_sections.append(self._generate_limitations(primary_hypothesis))

        return "\n\n".join(report_sections)

    def _generate_header(self, drug_profile: Dict) -> str:
        """Generate report header"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f"""# FormulationOS Scientific Report

**Drug:** {drug_profile.get('drug_name', 'Unknown')}
**Analysis Date:** {timestamp}
**System:** FormulationOS v1.0 - Knowledge-Grounded Formulation AI

---
"""

    def _generate_drug_section(self, drug_profile: Dict) -> str:
        """Section 1: Drug Understanding"""

        section = """## 1. Drug Understanding

**Source:** Drug Knowledge MCP (PubChem + ChEMBL)

**Physicochemical Properties:**
"""

        section += f"- **Molecular Weight:** {drug_profile.get('molecular_weight', 'N/A')} Da\n"
        section += f"- **LogP:** {drug_profile.get('logp', 'N/A')}\n"
        section += f"- **LogS:** {drug_profile.get('logs', 'N/A')}\n"
        section += f"- **BCS Class:** {drug_profile.get('bcs_class', 'N/A')}\n"

        if drug_profile.get('known_formulations'):
            section += "\n**Historical Formulations:**\n"
            for formulation in drug_profile['known_formulations'][:3]:
                section += f"- {formulation}\n"

        section += f"\n**Primary Challenge:** {self._identify_primary_challenge(drug_profile)}\n"

        return section

    def _generate_evidence_section(self, evidence_pool: List) -> str:
        """Section 2: Evidence Collection"""

        section = """## 2. Evidence Collection

**Evidence-Based Reasoning Chain:**

"""

        for i, evidence in enumerate(evidence_pool[:5], 1):
            section += f"""**Evidence E{i}**
- **Observation:** {getattr(evidence, 'observation', 'N/A')}
- **Interpretation:** {getattr(evidence, 'interpretation', 'N/A')}
- **Mechanism:** {getattr(evidence, 'mechanism', 'N/A').value if hasattr(getattr(evidence, 'mechanism', None), 'value') else 'N/A'}
- **Confidence:** {getattr(evidence, 'confidence', 0.0):.2f}
- **Source:** {getattr(evidence, 'source', 'N/A').value if hasattr(getattr(evidence, 'source', None), 'value') else 'N/A'}

"""

        return section

    def _generate_mechanism_section(self, evidence_pool: List) -> str:
        """Section 3: Mechanism Diagnosis"""

        section = """## 3. Mechanism Diagnosis

**Identified Problem Types:**

"""

        # Extract unique mechanisms
        mechanisms = set()
        for evidence in evidence_pool:
            if hasattr(evidence, 'mechanism'):
                mechanisms.add(evidence.mechanism)

        for mechanism in mechanisms:
            section += f"- **{mechanism.value if hasattr(mechanism, 'value') else mechanism}**\n"

            # Count supporting evidence
            count = sum(1 for e in evidence_pool if hasattr(e, 'mechanism') and e.mechanism == mechanism)
            section += f"  - Supporting evidence: {count} observations\n"

        return section

    def _generate_hypothesis_section(
        self,
        primary: FormulationHypothesis,
        alternatives: List[RejectedAlternative]
    ) -> str:
        """Section 4: Hypothesis Generation & Ranking"""

        section = """## 4. Hypothesis Generation & Ranking

**Candidate Strategies Evaluated:**

"""

        # Primary hypothesis
        section += f"""### Selected: {primary.strategy_name}

**Overall Confidence:** {primary.confidence_score:.2f}

**Component Scores:**
- Mechanism Match: {primary.mechanism_match:.2f}
- Drug Suitability: {primary.context_suitability:.2f}
- Historical Evidence: {primary.historical_precedent:.2f}

**Supporting Evidence:**
"""
        for evidence in primary.supporting_evidence:
            section += f"- {evidence}\n"

        # Alternatives (brief)
        if alternatives:
            section += "\n**Alternative Strategies:**\n"
            for alt in alternatives:
                section += f"- {alt.strategy_name}: Rejected (see Alternative Analysis)\n"

        return section

    def _generate_alternative_analysis(self, alternatives: List[RejectedAlternative]) -> str:
        """Section 5: Alternative Analysis - CRITICAL for scientific credibility"""

        section = """## 5. Alternative Analysis

**Why Other Strategies Were Not Selected:**

*This section demonstrates scientific rigor by explaining rejection rationale.*

"""

        for alt in alternatives:
            section += f"""### {alt.strategy_name}

**Initial Plausibility:** {alt.initial_plausibility:.2f}

**Rejection Rationale:**
{alt.rejection_reason}

"""
            if alt.incompatibility_factors:
                section += "**Incompatibility Factors:**\n"
                for factor in alt.incompatibility_factors:
                    section += f"- {factor}\n"
                section += "\n"

            if alt.context_mismatch:
                section += "**Context Mismatch:**\n"
                for mismatch in alt.context_mismatch:
                    section += f"- {mismatch}\n"
                section += "\n"

        return section

    def _generate_formulation_design(self, hypothesis: FormulationHypothesis) -> str:
        """Section 6: Formulation Design"""

        section = f"""## 6. Formulation Design Hypothesis

**Strategy:** {hypothesis.strategy_name}

"""

        if hypothesis.excipients:
            section += "**Excipient Selection:**\n\n"
            for excipient in hypothesis.excipients:
                section += f"**{excipient.get('name', 'Unknown')}**\n"
                section += f"- Function: {excipient.get('function', 'N/A')}\n"
                section += f"- Rationale: {excipient.get('rationale', 'N/A')}\n\n"

        if hypothesis.process_options:
            section += "**Process Options:**\n"
            for process in hypothesis.process_options:
                section += f"- {process}\n"

        return section

    def _generate_validation_plan(self, hypothesis: FormulationHypothesis) -> str:
        """Section 7: Experimental Validation Plan"""

        section = """## 7. Experimental Validation Plan

**Recommended Characterization:**

"""

        if hypothesis.validation_plan:
            for i, step in enumerate(hypothesis.validation_plan, 1):
                section += f"**Stage {i}:** {step}\n\n"
        else:
            # Default validation for solid dispersion
            section += """**Stage 1:** Solid-State Characterization
- DSC (glass transition, crystallinity)
- XRPD (amorphous confirmation)
- FT-IR (drug-polymer interaction)

**Stage 2:** Dissolution Testing
- Comparison vs. crystalline API
- pH-dependent profiles
- Supersaturation kinetics

**Stage 3:** Physical Stability
- Accelerated stability (40°C/75% RH)
- Recrystallization monitoring

**Stage 4:** Bioavailability Assessment
- *In vivo* PK study (if applicable)
"""

        return section

    def _generate_limitations(self, hypothesis: FormulationHypothesis) -> str:
        """Section 8: Limitations & Uncertainties"""

        section = """## 8. Limitations & Uncertainties

**Practical Constraints:**

"""

        if hypothesis.practical_constraints:
            for constraint in hypothesis.practical_constraints:
                section += f"- {constraint}\n"

        if hypothesis.uncertainty_factors:
            section += "\n**Uncertainty Factors:**\n"
            for factor in hypothesis.uncertainty_factors:
                section += f"- {factor}\n"

        section += """

**Recommended Next Steps:**
1. Polymer screening experiments
2. Process optimization
3. Stability validation
4. Scale-up feasibility assessment
"""

        return section

    def _identify_primary_challenge(self, drug_profile: Dict) -> str:
        """Identify primary formulation challenge from drug profile"""
        bcs = drug_profile.get('bcs_class', '')

        if 'II' in bcs or 'IV' in bcs:
            return "Poor aqueous solubility (dissolution-limited absorption)"
        elif 'III' in bcs:
            return "Low permeability (permeation-limited absorption)"
        else:
            return "General bioavailability optimization"

    def _load_template(self) -> Dict:
        """Load report template structure"""
        return {
            "sections": [
                "Drug Understanding",
                "Evidence Collection",
                "Mechanism Diagnosis",
                "Hypothesis Ranking",
                "Alternative Analysis",
                "Formulation Design",
                "Validation Plan",
                "Limitations"
            ]
        }


# Example usage
if __name__ == "__main__":
    # Mock data for testing
    from src.formulation_os.agent.context_reasoner import DrugContext

    drug_profile = {
        "drug_name": "Ibuprofen",
        "molecular_weight": 206.28,
        "logp": 3.5,
        "logs": -3.97,
        "bcs_class": "II",
        "known_formulations": ["tablet", "solid dispersion", "nanocrystal"]
    }

    primary_hyp = FormulationHypothesis(
        strategy_name="Amorphous Solid Dispersion",
        confidence_score=0.77,
        drug_name="Ibuprofen",
        drug_profile=drug_profile,
        mechanism_match=0.92,
        context_suitability=0.85,
        historical_precedent=0.80,
        excipients=[
            {
                "name": "HPMC-AS",
                "function": "Precipitation inhibitor",
                "rationale": "Hydrogen bonding with carboxylic acid group"
            },
            {
                "name": "Soluplus",
                "function": "Amorphous stabilization",
                "rationale": "Amphiphilic polymer for supersaturation maintenance"
            }
        ],
        process_options=["Hot melt extrusion", "Spray drying"],
        practical_constraints=["Physical stability validation required"],
        uncertainty_factors=["Optimal polymer ratio needs screening"]
    )

    rejected_alt = RejectedAlternative(
        strategy_name="Cyclodextrin Complex",
        initial_plausibility=0.64,
        rejection_reason="High dose (400mg) requires excessive cyclodextrin amount, limiting tablet feasibility",
        incompatibility_factors=[
            "MW=206 Da suitable for cavity, but dose is primary limitation",
            "Tablet weight would exceed 1000mg with required cyclodextrin"
        ],
        context_mismatch=[
            "Mechanism match adequate but practical constraints severe"
        ]
    )

    generator = HypothesisReportGenerator()
    report = generator.generate_research_report(
        primary_hypothesis=primary_hyp,
        rejected_alternatives=[rejected_alt],
        evidence_pool=[],
        drug_profile=drug_profile
    )

    print(report)
