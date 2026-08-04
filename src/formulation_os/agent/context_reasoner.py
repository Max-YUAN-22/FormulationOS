"""
Drug Context Reasoning Layer for FormulationOS

This module implements context-aware scientific reasoning for strategy selection.

KEY PRINCIPLE:
    This is NOT a rule-based filter.
    This is a REASONING system that assesses drug-strategy compatibility
    based on pharmaceutical science principles.

Architecture:
    Strategy Candidate → Drug Context → Compatibility Assessment → Reasoning Trace

Difference from Rule System:
    Rule System: "if MW > 500: reject cyclodextrin"
    Reasoning System: "Large MW (853 Da) reduces cyclodextrin inclusion efficiency.
                       Typical cavity accommodates <400 Da. Compatibility: 0.35"

Output:
    Not binary accept/reject, but compatibility score + scientific rationale
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum


@dataclass
class DrugContext:
    """
    Drug-specific context for formulation reasoning

    This captures the complete drug profile that influences strategy selection
    beyond just mechanisms.
    """
    # Physicochemical properties
    molecular_weight: float
    logP: float
    logS: float
    bcs_class: str

    # Formulation requirements
    dose: Optional[float] = None  # mg
    route: str = "oral"
    target_release: str = "immediate"  # immediate | sustained | controlled

    # Chemical characteristics
    ionizable: Optional[bool] = None
    pka: Optional[float] = None
    polymorphism: Optional[bool] = None

    # Manufacturing constraints
    target_dosage_form: str = "tablet"  # tablet | capsule | suspension | injectable

    def get_property(self, key: str) -> Optional[float]:
        """Safely get a property value"""
        return getattr(self, key, None)


@dataclass
class CompatibilityAssessment:
    """
    Scientific assessment of drug-strategy compatibility

    This is the output of context reasoning, not a binary filter.
    """
    strategy_name: str
    drug_context: DrugContext

    # Compatibility scoring
    compatibility_score: float = 0.7  # 0-1, how well this strategy fits the drug context (default moderate)

    # Scientific reasoning
    advantages: List[str] = field(default_factory=list)  # Why this strategy is suitable
    limitations: List[str] = field(default_factory=list)  # Contextual challenges
    contraindications: List[str] = field(default_factory=list)  # Strong incompatibilities

    # Reasoning trace
    reasoning_summary: str = ""

    def generate_reasoning_trace(self) -> str:
        """
        Generate human-readable reasoning explanation

        Format:
            Strategy: Cyclodextrin Complex
            Drug: MW=853 Da, LogP=5.6

            Advantages:
            + Addresses solubility limitation

            Limitations:
            - Large molecular size (853 Da) exceeds typical cavity capacity (<400 Da)
            - High lipophilicity (LogP=5.6) reduces aqueous complexation efficiency

            Overall Compatibility: 0.35 (Low)
            Recommendation: Consider alternative strategies for large lipophilic molecules
        """
        lines = [f"**Context-Aware Assessment: {self.strategy_name}**\n"]
        lines.append(f"Drug: MW={self.drug_context.molecular_weight:.1f} Da, "
                    f"LogP={self.drug_context.logP:.1f}, "
                    f"LogS={self.drug_context.logS:.1f}\n")

        if self.advantages:
            lines.append("**Advantages:**")
            for adv in self.advantages:
                lines.append(f"  + {adv}")
            lines.append("")

        if self.limitations:
            lines.append("**Limitations:**")
            for lim in self.limitations:
                lines.append(f"  - {lim}")
            lines.append("")

        if self.contraindications:
            lines.append("**Contraindications:**")
            for contra in self.contraindications:
                lines.append(f"  ⚠️ {contra}")
            lines.append("")

        # Compatibility interpretation
        compat_label = "High" if self.compatibility_score > 0.7 else \
                      "Moderate" if self.compatibility_score > 0.5 else "Low"

        lines.append(f"**Overall Compatibility:** {self.compatibility_score:.2f} ({compat_label})")

        if self.compatibility_score < 0.5:
            lines.append("*Recommendation: Consider alternative strategies with higher compatibility*")

        self.reasoning_summary = "\n".join(lines)
        return self.reasoning_summary


class ContextReasoner:
    """
    Context-aware scientific reasoning for drug-strategy compatibility

    This is NOT a rule-based filter. This implements pharmaceutical science
    reasoning about why certain strategies are more or less suitable for
    specific drug properties.

    Core Methods:
    - assess_compatibility(): Generate CompatibilityAssessment with reasoning
    - _assess_cyclodextrin_compatibility(): Strategy-specific reasoning
    - _assess_solid_dispersion_compatibility(): ...
    """

    def __init__(self):
        # Strategy-specific reasoning methods
        self.strategy_assessors = {
            "cyclodextrin_complex": self._assess_cyclodextrin_compatibility,
            "solid_dispersion": self._assess_solid_dispersion_compatibility,
            "nanocrystal": self._assess_nanocrystal_compatibility,
            "SEDDS": self._assess_sedds_compatibility,
            "salt_formation": self._assess_salt_compatibility,
            "cocrystal": self._assess_cocrystal_compatibility,
        }

    def assess_compatibility(self, strategy_name: str, drug_context: DrugContext) -> CompatibilityAssessment:
        """
        Assess drug-strategy compatibility with scientific reasoning

        This generates a compatibility score and reasoning trace explaining
        WHY this strategy is suitable or unsuitable for this drug.

        Args:
            strategy_name: Formulation strategy
            drug_context: Complete drug profile

        Returns:
            CompatibilityAssessment with score and reasoning
        """
        assessor = self.strategy_assessors.get(strategy_name, self._default_assessment)
        return assessor(drug_context)

    def _assess_cyclodextrin_compatibility(self, drug_context: DrugContext) -> CompatibilityAssessment:
        """
        Cyclodextrin compatibility reasoning

        Pharmaceutical science principles:
        - Optimal for MW < 400 Da (cavity size limitation)
        - Suitable for LogP 1-4 (moderate lipophilicity)
        - Effective for ionizable compounds
        - Dose limitation due to cyclodextrin amount
        """
        assessment = CompatibilityAssessment(
            strategy_name="cyclodextrin_complex",
            drug_context=drug_context
        )

        base_score = 0.8  # Start with moderate-high baseline

        # Molecular weight reasoning
        mw = drug_context.molecular_weight
        if mw < 300:
            assessment.advantages.append(f"Small molecular size (MW={mw:.0f} Da) suitable for cyclodextrin cavity")
            mw_factor = 1.0
        elif mw < 400:
            assessment.advantages.append(f"Molecular size (MW={mw:.0f} Da) within typical cavity capacity")
            mw_factor = 0.9
        elif mw < 500:
            assessment.limitations.append(f"Moderate molecular size (MW={mw:.0f} Da) may reduce complexation efficiency")
            mw_factor = 0.6
        else:
            assessment.limitations.append(
                f"Large molecular size (MW={mw:.0f} Da) significantly exceeds typical cyclodextrin "
                f"cavity capacity (<400 Da)"
            )
            mw_factor = 0.3
            if mw > 700:
                assessment.contraindications.append(
                    "Molecular size incompatible with cyclodextrin inclusion complex formation"
                )
                mw_factor = 0.1

        # LogP reasoning
        logp = drug_context.logP
        if 1 < logp < 4:
            assessment.advantages.append(f"Moderate lipophilicity (LogP={logp:.1f}) favorable for cyclodextrin complexation")
            logp_factor = 1.0
        elif logp <= 1:
            assessment.limitations.append(f"Low lipophilicity (LogP={logp:.1f}) suggests limited benefit from cyclodextrin")
            logp_factor = 0.7
        elif logp < 5:
            assessment.limitations.append(f"High lipophilicity (LogP={logp:.1f}) may reduce aqueous complexation efficiency")
            logp_factor = 0.6
        else:
            assessment.limitations.append(
                f"Very high lipophilicity (LogP={logp:.1f}) strongly incompatible with "
                f"cyclodextrin's aqueous complexation mechanism"
            )
            logp_factor = 0.3
            assessment.contraindications.append("Extreme lipophilicity unsuitable for cyclodextrin approach")

        # Dose reasoning
        if drug_context.dose and drug_context.dose > 200:
            assessment.limitations.append(
                f"High dose ({drug_context.dose}mg) requires large cyclodextrin amount, "
                f"may limit tablet formulation feasibility"
            )
            dose_factor = 0.8
        else:
            dose_factor = 1.0

        # Calculate final compatibility
        assessment.compatibility_score = base_score * mw_factor * logp_factor * dose_factor
        assessment.generate_reasoning_trace()

        return assessment

    def _assess_solid_dispersion_compatibility(self, drug_context: DrugContext) -> CompatibilityAssessment:
        """
        Solid dispersion compatibility reasoning

        Principles:
        - Highly versatile strategy
        - Suitable for wide MW range
        - Most effective for BCS II/IV
        - Manufacturing scalability good
        """
        assessment = CompatibilityAssessment(
            strategy_name="solid_dispersion",
            drug_context=drug_context
        )

        base_score = 0.9  # Solid dispersion is highly versatile

        # BCS reasoning
        if drug_context.bcs_class in ["II", "IV"]:
            assessment.advantages.append(f"BCS {drug_context.bcs_class} drug - solid dispersion addresses solubility limitation")
            bcs_factor = 1.0
        else:
            assessment.limitations.append(f"BCS {drug_context.bcs_class} - solubility may not be primary limitation")
            bcs_factor = 0.7

        # MW reasoning
        mw = drug_context.molecular_weight
        if mw < 600:
            assessment.advantages.append(f"Molecular size (MW={mw:.0f} Da) suitable for polymer matrix dispersion")
            mw_factor = 1.0
        else:
            assessment.limitations.append(f"Large molecule (MW={mw:.0f} Da) may require higher polymer ratio")
            mw_factor = 0.85

        # Stability consideration
        assessment.limitations.append("Physical stability requires validation (recrystallization risk)")
        assessment.limitations.append("Optimal polymer selection needs screening")

        stability_factor = 0.85  # Generic stability uncertainty

        assessment.compatibility_score = base_score * bcs_factor * mw_factor * stability_factor
        assessment.generate_reasoning_trace()

        return assessment

    def _assess_nanocrystal_compatibility(self, drug_context: DrugContext) -> CompatibilityAssessment:
        """Nanocrystal compatibility reasoning"""
        assessment = CompatibilityAssessment(
            strategy_name="nanocrystal",
            drug_context=drug_context
        )

        base_score = 0.85

        # Solubility reasoning
        if drug_context.logS < -4:
            assessment.advantages.append(f"Very poor solubility (LogS={drug_context.logS:.1f}) - nanocrystal highly effective")
            solubility_factor = 1.0
        elif drug_context.logS < -3:
            assessment.advantages.append(f"Poor solubility (LogS={drug_context.logS:.1f}) benefits from particle size reduction")
            solubility_factor = 0.9
        else:
            assessment.limitations.append("Moderate solubility - limited benefit from nanocrystal approach")
            solubility_factor = 0.6

        # Manufacturing
        assessment.limitations.append("Manufacturing scalability requires validation (wet milling process)")

        assessment.compatibility_score = base_score * solubility_factor * 0.9
        assessment.generate_reasoning_trace()

        return assessment

    def _assess_sedds_compatibility(self, drug_context: DrugContext) -> CompatibilityAssessment:
        """SEDDS compatibility reasoning"""
        assessment = CompatibilityAssessment(
            strategy_name="SEDDS",
            drug_context=drug_context
        )

        base_score = 0.8

        # LogP reasoning - SEDDS best for lipophilic drugs
        logp = drug_context.logP
        if logp > 4:
            assessment.advantages.append(f"High lipophilicity (LogP={logp:.1f}) - ideal for lipid-based formulation")
            logp_factor = 1.0
        elif logp > 2:
            assessment.advantages.append(f"Moderate lipophilicity (LogP={logp:.1f}) suitable for SEDDS")
            logp_factor = 0.85
        else:
            assessment.limitations.append(f"Low lipophilicity (LogP={logp:.1f}) reduces lipid solubilization efficiency")
            logp_factor = 0.5
            assessment.contraindications.append("Hydrophilic drugs poorly suited for lipid-based delivery")

        # Dose reasoning
        if drug_context.dose and drug_context.dose > 250:
            assessment.limitations.append(f"High dose ({drug_context.dose}mg) may require large capsule size")
            dose_factor = 0.8
        else:
            dose_factor = 1.0

        assessment.compatibility_score = base_score * logp_factor * dose_factor
        assessment.generate_reasoning_trace()

        return assessment

    def _assess_salt_compatibility(self, drug_context: DrugContext) -> CompatibilityAssessment:
        """Salt formation compatibility reasoning"""
        assessment = CompatibilityAssessment(
            strategy_name="salt_formation",
            drug_context=drug_context
        )

        base_score = 0.75

        # Ionizability requirement
        if drug_context.ionizable is True:
            assessment.advantages.append("Ionizable drug - salt formation feasible")
            ion_factor = 1.0
        elif drug_context.ionizable is False:
            assessment.contraindications.append("Non-ionizable drug - salt formation not applicable")
            ion_factor = 0.1
        else:
            assessment.limitations.append("Ionizability unknown - requires pKa determination")
            ion_factor = 0.6

        assessment.compatibility_score = base_score * ion_factor
        assessment.generate_reasoning_trace()

        return assessment

    def _assess_cocrystal_compatibility(self, drug_context: DrugContext) -> CompatibilityAssessment:
        """Cocrystal compatibility reasoning"""
        assessment = CompatibilityAssessment(
            strategy_name="cocrystal",
            drug_context=drug_context
        )

        base_score = 0.7

        # Cocrystal generally applicable but requires coformer screening
        assessment.advantages.append("Cocrystal can improve solubility and stability")
        assessment.limitations.append("Requires coformer screening and regulatory consideration")
        assessment.limitations.append("Intellectual property landscape complex")

        assessment.compatibility_score = base_score
        assessment.generate_reasoning_trace()

        return assessment

    def _default_assessment(self, drug_context: DrugContext) -> CompatibilityAssessment:
        """Default assessment for strategies without specific reasoning"""
        return CompatibilityAssessment(
            strategy_name="unknown",
            drug_context=drug_context,
            compatibility_score=0.7,
            reasoning_summary="No specific context reasoning available"
        )
