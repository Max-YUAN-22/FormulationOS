"""
Hypothesis Ranking System for FormulationOS

REFACTORED ARCHITECTURE (Phase 32 + Context Reasoning):
    Evidence → Mechanism → Hypothesis → Context Reasoning → Validation

This module implements evidence-grounded hypothesis generation and ranking:
1. Consumes Evidence objects from EvidenceManager (not LLM generation)
2. Matches evidence mechanisms to formulation strategies
3. Assesses drug-strategy compatibility via Context Reasoning
4. Calculates confidence = Evidence strength × Mechanism relevance × Context compatibility - Uncertainty
5. Outputs ranked hypotheses with transparent reasoning trace

Key transformation:
    OLD: LLM generates hypotheses → score them
    NEW: Evidence → Mechanism → Candidates → Context Reasoning → Ranking

Example workflow:
    Evidence: LogS=-3.97, BCS II, MW=206, LogP=3.8
    → Mechanism: DISSOLUTION_LIMITATION, SOLUBILITY_LIMITATION
    → Candidates: [solid_dispersion, nanocrystal, cyclodextrin, SEDDS]
    → Context Assessment: cyclodextrin (MW suitable, LogP moderate) = 0.85
    → Ranked by evidence × mechanism × context compatibility
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

# Import the Evidence system
from .evidence_manager import (
    Evidence,
    EvidenceManager,
    ScientificMechanism,
    MechanismKnowledgeBase
)

# Import Context Reasoning
from .context_reasoner import (
    DrugContext,
    ContextReasoner,
    CompatibilityAssessment
)


@dataclass
class UncertaintyFactor:
    """
    Unresolved uncertainty that reduces hypothesis confidence

    Example:
        UncertaintyFactor(
            description="Polymer compatibility unknown",
            impact=0.2,  # -20% confidence penalty
            resolution="In vitro compatibility screening"
        )
    """
    description: str
    impact: float  # 0-1, penalty to confidence
    resolution: str  # How to resolve this uncertainty


@dataclass
class Hypothesis:
    """
    Scientific hypothesis for formulation strategy

    NEW ARCHITECTURE (with Context Reasoning):
    - Generated FROM evidence and mechanisms (not by LLM)
    - Confidence calculated from evidence × mechanism × context compatibility
    - Includes reasoning trace (WHY this hypothesis)
    - Links to validation experiments
    """
    strategy_name: str
    description: str

    # Evidence-based scoring
    supporting_mechanisms: List[ScientificMechanism] = field(default_factory=list)
    supporting_evidence: List[Evidence] = field(default_factory=list)
    uncertainties: List[UncertaintyFactor] = field(default_factory=list)

    # Context compatibility (NEW)
    context_assessment: Optional[CompatibilityAssessment] = None

    # Calculated scores
    evidence_strength: float = 0.0  # Raw evidence support (0-1)
    mechanism_compatibility: float = 0.0  # How well strategy matches mechanisms (0-1)
    context_compatibility: float = 1.0  # Drug-strategy fit (0-1) - NEW
    uncertainty_penalty: float = 0.0  # Reduction from unresolved questions (0-1)
    final_confidence: float = 0.0  # Final score after all factors

    # Validation
    validation_methods: List[str] = field(default_factory=list)
    validation_rationale: str = ""

    # Reasoning transparency
    reasoning_trace: str = ""  # WHY this hypothesis was generated and ranked

    created_at: datetime = field(default_factory=datetime.now)

    def calculate_confidence(self) -> float:
        """
        Calculate final confidence score with context reasoning

        REFACTORED Formula:
            confidence = evidence_strength × mechanism_compatibility × context_compatibility - weighted_uncertainty

        Components:
        - Evidence strength: Quality and quantity of supporting evidence
        - Mechanism compatibility: How well strategy addresses identified mechanisms
        - Context compatibility: Drug-strategy fit based on molecular properties (NEW)
        - Weighted uncertainty: Typical vs critical uncertainties

        Returns:
            Final confidence score (0-1)
        """
        if not self.supporting_evidence:
            return 0.2  # No evidence = very low confidence

        # 1. Evidence strength (average confidence + count bonus)
        base_strength = sum(e.confidence for e in self.supporting_evidence) / len(self.supporting_evidence)
        evidence_count = len(self.supporting_evidence)
        evidence_count_bonus = min(0.2, (evidence_count - 1) * 0.08)
        self.evidence_strength = min(1.0, base_strength + evidence_count_bonus)

        # 2. Mechanism compatibility
        total_mechanisms = len(self.supporting_mechanisms)
        if total_mechanisms >= 2:
            self.mechanism_compatibility = 1.0
        elif total_mechanisms == 1:
            self.mechanism_compatibility = 0.75
        else:
            self.mechanism_compatibility = 0.5

        # 3. Context compatibility (NEW - from ContextReasoner)
        if self.context_assessment:
            self.context_compatibility = self.context_assessment.compatibility_score
        else:
            self.context_compatibility = 0.8  # Default if no context assessment

        # 4. Weighted uncertainty penalty
        typical_uncertainty_keywords = ["polymer", "stability", "scalability"]
        weighted_penalty = 0.0

        for uncertainty in self.uncertainties:
            is_typical = any(keyword in uncertainty.description.lower()
                           for keyword in typical_uncertainty_keywords)
            if is_typical:
                weighted_penalty += uncertainty.impact * 0.5
            else:
                weighted_penalty += uncertainty.impact

        self.uncertainty_penalty = min(0.4, weighted_penalty)

        # Final calculation: multiplicative for factors, subtractive for uncertainty
        base_confidence = self.evidence_strength * self.mechanism_compatibility * self.context_compatibility
        self.final_confidence = max(0.0, base_confidence * (1 - self.uncertainty_penalty))

        return self.final_confidence

    def generate_reasoning_trace(self) -> str:
        """
        Generate transparent reasoning explanation with context assessment

        Format:
            WHY this hypothesis:
            - Mechanism: DISSOLUTION_LIMITATION (2 evidence)
            - Evidence strength: 0.85
            - Context compatibility: 0.72 (from drug properties)
            - Uncertainties: 1 unresolved

            Evidence:
            - LogS=-3.97 (poor solubility) [0.9]
            - BCS II [0.95]

            Context Assessment:
            [Drug-strategy compatibility reasoning]

            Validation needed:
            - DSC (detect amorphous conversion)
            - XRPD (confirm crystallinity reduction)
        """
        lines = ["**WHY this hypothesis:**\n"]

        # Mechanisms
        for mechanism in self.supporting_mechanisms:
            evidence_count = sum(1 for e in self.supporting_evidence if e.mechanism == mechanism)
            lines.append(f"- Mechanism: {mechanism.value} ({evidence_count} evidence)")

        # Scores
        lines.append(f"- Evidence strength: {self.evidence_strength:.2f}")
        lines.append(f"- Mechanism compatibility: {self.mechanism_compatibility:.2f}")
        lines.append(f"- Context compatibility: {self.context_compatibility:.2f}")
        if self.uncertainties:
            lines.append(f"- Uncertainties: {len(self.uncertainties)} unresolved")

        # Evidence details
        lines.append("\n**Supporting Evidence:**")
        for evidence in self.supporting_evidence:
            lines.append(f"- {evidence.observation} ({evidence.interpretation}) [{evidence.confidence:.2f}]")

        # Context Assessment (NEW)
        if self.context_assessment:
            lines.append("\n**Context Assessment:**")
            lines.append(self.context_assessment.reasoning_summary)

        # Uncertainties
        if self.uncertainties:
            lines.append("\n**Unresolved Uncertainties:**")
            for unc in self.uncertainties:
                lines.append(f"- {unc.description} (impact: -{unc.impact*100:.0f}%)")
                lines.append(f"  Resolution: {unc.resolution}")

        # Validation
        if self.validation_methods:
            lines.append("\n**Validation Required:**")
            for method in self.validation_methods:
                lines.append(f"- {method}")
            if self.validation_rationale:
                lines.append(f"\n{self.validation_rationale}")

        self.reasoning_trace = "\n".join(lines)
        return self.reasoning_trace


class HypothesisRanker:
    """
    Evidence-grounded hypothesis generation and ranking system with context reasoning

    NEW WORKFLOW (Phase 32 + Context):
    1. Consume Evidence from EvidenceManager
    2. Identify mechanisms from evidence
    3. Generate candidate strategies for each mechanism
    4. Assess drug-strategy compatibility via ContextReasoner (NEW)
    5. Calculate confidence from evidence × mechanism × context
    6. Rank hypotheses
    7. Generate reasoning trace for transparency

    This is NOT a scoring system for pre-generated hypotheses.
    This GENERATES hypotheses from evidence and reasons about their suitability.
    """

    def __init__(self, evidence_manager: EvidenceManager, drug_context: Optional[DrugContext] = None):
        self.evidence_manager = evidence_manager
        self.mechanism_kb = MechanismKnowledgeBase()
        self.context_reasoner = ContextReasoner()
        self.drug_context = drug_context
        self.hypotheses: List[Hypothesis] = []

    def generate_hypotheses_from_evidence(self) -> List[Hypothesis]:
        """
        Generate hypotheses directly from collected evidence with context reasoning

        This is the core method that implements:
            Evidence → Mechanism → Strategy Candidates → Context Assessment → Hypotheses

        Returns:
            List of Hypothesis objects with context compatibility assessed
        """
        self.hypotheses.clear()

        # Get all mechanisms identified from evidence
        mechanisms = self.evidence_manager.get_all_mechanisms()

        if not mechanisms:
            return []

        # For each mechanism, generate candidate strategies
        strategy_to_mechanisms = {}  # Group mechanisms by strategy

        for mechanism in mechanisms:
            # Skip mechanisms that don't indicate a problem
            if mechanism == ScientificMechanism.BIOAVAILABILITY_LOSS:
                continue

            strategies = self.mechanism_kb.get_strategies_for_mechanism(mechanism)
            for strategy in strategies:
                if strategy not in strategy_to_mechanisms:
                    strategy_to_mechanisms[strategy] = []
                strategy_to_mechanisms[strategy].append(mechanism)

        # Create Hypothesis objects with context assessment
        for strategy_name, mechanisms_list in strategy_to_mechanisms.items():
            # Get all evidence supporting these mechanisms
            supporting_evidence = []
            for mechanism in mechanisms_list:
                supporting_evidence.extend(self.evidence_manager.get_evidence_by_mechanism(mechanism))

            # Remove duplicates manually
            seen = []
            unique_evidence = []
            for evidence in supporting_evidence:
                key = (evidence.observation, evidence.source.value)
                if key not in seen:
                    seen.append(key)
                    unique_evidence.append(evidence)
            supporting_evidence = unique_evidence

            # Create hypothesis
            hypothesis = Hypothesis(
                strategy_name=strategy_name,
                description=self._generate_strategy_description(strategy_name),
                supporting_mechanisms=mechanisms_list,
                supporting_evidence=supporting_evidence,
                validation_methods=self._get_validation_methods(strategy_name)
            )

            # Context compatibility assessment (NEW)
            if self.drug_context:
                context_assessment = self.context_reasoner.assess_compatibility(
                    strategy_name,
                    self.drug_context
                )
                hypothesis.context_assessment = context_assessment

            # Add uncertainties
            hypothesis.uncertainties = self._identify_uncertainties(strategy_name, supporting_evidence)

            # Calculate confidence (now includes context compatibility)
            hypothesis.calculate_confidence()

            # Generate reasoning
            hypothesis.generate_reasoning_trace()

            self.hypotheses.append(hypothesis)

        return self.hypotheses

    def rank_hypotheses(self) -> List[Hypothesis]:
        """
        Rank hypotheses by final confidence score

        Returns:
            Hypotheses sorted by confidence (highest first)
        """
        return sorted(self.hypotheses, key=lambda h: h.final_confidence, reverse=True)

    def generate_ranking_report(self) -> str:
        """
        Generate comprehensive ranking report with reasoning

        Format:
            HYPOTHESIS RANKING (Evidence-Based)

            H1: Solid Dispersion [Confidence: 0.78]
            Supporting Mechanisms: DISSOLUTION_LIMITATION, SOLUBILITY_LIMITATION
            Evidence: 3 items
            [Detailed reasoning trace]

            H2: Nanocrystal [Confidence: 0.71]
            ...

            RECOMMENDATION:
            Prioritize H1 (Solid Dispersion) based on strongest evidence.
            Alternative: H2 if manufacturing constraints arise.
        """
        ranked = self.rank_hypotheses()

        lines = ["# HYPOTHESIS RANKING (Evidence-Based)\n"]
        lines.append(f"*Generated from {len(self.evidence_manager.get_all_evidence())} pieces of evidence*\n")

        # Add each hypothesis
        for idx, hypothesis in enumerate(ranked, 1):
            lines.append(f"## H{idx}: {hypothesis.strategy_name} [Confidence: {hypothesis.final_confidence:.2f}]\n")
            lines.append(f"**Mechanisms addressed:** {', '.join(m.value for m in hypothesis.supporting_mechanisms)}")
            lines.append(f"**Evidence items:** {len(hypothesis.supporting_evidence)}\n")
            lines.append(hypothesis.reasoning_trace)
            lines.append("\n---\n")

        # Add recommendation
        if ranked:
            lines.append("## RECOMMENDATION\n")
            top_hypothesis = ranked[0]
            lines.append(f"**Prioritize H1 ({top_hypothesis.strategy_name})** based on strongest evidence (confidence: {top_hypothesis.final_confidence:.2f}).\n")

            if len(ranked) > 1:
                second_hypothesis = ranked[1]
                lines.append(f"**Alternative:** H2 ({second_hypothesis.strategy_name}) if H1 faces constraints.\n")

            lines.append(f"\n**Next Steps:**")
            lines.append(f"1. Validate H1 with: {', '.join(top_hypothesis.validation_methods)}")
            if top_hypothesis.uncertainties:
                lines.append(f"2. Resolve uncertainties: {', '.join(u.description for u in top_hypothesis.uncertainties)}")
            lines.append(f"3. If validated, proceed to formulation optimization")

        return "\n".join(lines)

    def _generate_strategy_description(self, strategy_name: str) -> str:
        """Generate human-readable description for strategy"""
        descriptions = {
            "solid_dispersion": "Disperse drug in polymer matrix to achieve amorphous state",
            "nanocrystal": "Reduce particle size to nanoscale for enhanced dissolution",
            "cyclodextrin_complex": "Form inclusion complex with cyclodextrin for solubility enhancement",
            "SEDDS": "Self-emulsifying drug delivery system for lipophilic drugs",
            "salt_formation": "Convert to salt form for improved solubility",
            "cocrystal": "Form cocrystal with coformer for enhanced properties",
            "permeation_enhancer": "Add excipients to improve intestinal permeability",
            "nanoparticle": "Formulate as nanoparticles for enhanced absorption",
            "lipid_formulation": "Lipid-based formulation for lipophilic drug solubilization"
        }
        return descriptions.get(strategy_name, f"{strategy_name} formulation approach")

    def _get_validation_methods(self, strategy_name: str) -> List[str]:
        """Return validation methods for each strategy"""
        validation_map = {
            "solid_dispersion": ["DSC (amorphous state)", "XRPD (crystallinity)", "Dissolution test"],
            "nanocrystal": ["DLS (particle size)", "SEM/TEM (morphology)", "Dissolution test"],
            "cyclodextrin_complex": ["Phase solubility", "DSC", "NMR (complex formation)"],
            "SEDDS": ["Droplet size", "Self-emulsification time", "In vitro lipolysis"],
            "salt_formation": ["pKa measurement", "Solubility test", "Stability study"],
            "cocrystal": ["XRPD", "DSC", "FTIR (cocrystal confirmation)"],
            "permeation_enhancer": ["Caco-2 permeability", "TEER measurement", "In vivo PK"],
            "nanoparticle": ["DLS", "Zeta potential", "TEM", "Drug loading"],
            "lipid_formulation": ["Lipid solubility", "Emulsion stability", "In vitro lipolysis"]
        }
        return validation_map.get(strategy_name, ["Characterization required"])

    def _identify_uncertainties(self, strategy_name: str, evidence: List[Evidence]) -> List[UncertaintyFactor]:
        """Identify unresolved uncertainties for each strategy"""
        uncertainties = []

        # Generic uncertainties for strategies
        if strategy_name == "solid_dispersion":
            # Check if we have stability evidence
            has_stability_evidence = any("stability" in e.interpretation.lower() for e in evidence)
            if not has_stability_evidence:
                uncertainties.append(UncertaintyFactor(
                    description="Physical stability unknown (recrystallization risk)",
                    impact=0.15,
                    resolution="Accelerated stability study (40°C, 75% RH)"
                ))

            # Check polymer compatibility
            uncertainties.append(UncertaintyFactor(
                description="Optimal polymer type not determined",
                impact=0.10,
                resolution="Polymer screening (HPMC-AS, PVP-VA, Soluplus)"
            ))

        elif strategy_name == "nanocrystal":
            uncertainties.append(UncertaintyFactor(
                description="Manufacturing scalability unknown",
                impact=0.12,
                resolution="Pilot scale wet milling study"
            ))

        elif strategy_name == "SEDDS":
            uncertainties.append(UncertaintyFactor(
                description="Lipid excipient compatibility not tested",
                impact=0.15,
                resolution="Lipid solubility screening and formulation optimization"
            ))

        return uncertainties


def create_hypothesis_ranker_from_evidence(
    evidence_manager: EvidenceManager,
    drug_context: Optional[DrugContext] = None
) -> HypothesisRanker:
    """
    Convenience function to create ranker and generate hypotheses

    Usage:
        evidence_mgr = EvidenceManager()
        evidence_mgr.capture_from_tool_call("preformulation_fundamentals", tool_result)

        # Create drug context from tool results
        drug_context = DrugContext(
            molecular_weight=tool_result["molecular_weight"],
            logP=tool_result["LogP"],
            logS=tool_result["LogS"],
            bcs_class=tool_result["bcs_class"]
        )

        ranker = create_hypothesis_ranker_from_evidence(evidence_mgr, drug_context)
        ranked_hypotheses = ranker.rank_hypotheses()
        report = ranker.generate_ranking_report()
    """
    ranker = HypothesisRanker(evidence_manager, drug_context)
    ranker.generate_hypotheses_from_evidence()
    return ranker
