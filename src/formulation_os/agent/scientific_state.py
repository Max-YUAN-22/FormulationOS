"""Scientific State Management for FormulationOS

Maintains the ongoing scientific context across the conversation:
- Compound information (drug name, SMILES)
- Physicochemical properties (logP, logS, BCS classification)
- Research challenges
- Generated hypotheses with evidence
- Experimental validation plans

This is shared across all agents to maintain scientific continuity.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Hypothesis:
    """Scientific hypothesis with evidence and validation plan"""

    id: str
    name: str  # e.g., "Amorphous Solid Dispersion"
    mechanism: str  # Scientific mechanism explanation
    evidence: List[str]  # List of supporting evidence
    uncertainty: List[str]  # Known uncertainties/risks
    validation_methods: List[str]  # Suggested experimental methods
    confidence_score: Optional[float] = None  # 0-1 if available
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class CompoundProfile:
    """Drug compound information"""

    drug_name: str
    smiles: Optional[str] = None
    molecular_weight: Optional[float] = None
    formula: Optional[str] = None
    structure_image_path: Optional[str] = None


@dataclass
class PhysicochemicalProperties:
    """Predicted/measured drug properties"""

    logP: Optional[float] = None
    logS: Optional[float] = None
    logD: Optional[float] = None
    pKa_acidic: Optional[float] = None
    pKa_basic: Optional[float] = None
    melting_point: Optional[float] = None
    glass_transition_temp: Optional[float] = None
    aqueous_solubility: Optional[float] = None
    permeability: Optional[float] = None

    # Derived classifications
    bcs_class: Optional[str] = None  # I, II, III, IV
    developability_score: Optional[float] = None


@dataclass
class ResearchChallenge:
    """Primary formulation challenge"""

    primary: str  # e.g., "Low aqueous solubility"
    mechanism: str  # Why this is a problem
    impact: str  # e.g., "Dissolution-limited absorption"
    severity: str = "medium"  # low, medium, high


class ScientificState:
    """
    Central scientific state manager for FormulationOS

    Maintains all scientific context throughout the research conversation.
    Enables the AI Scientist to:
    - Remember what compound is being studied
    - Track what properties have been analyzed
    - Maintain generated hypotheses
    - Build upon previous insights
    """

    def __init__(self):
        self.compound: Optional[CompoundProfile] = None
        self.properties: Optional[PhysicochemicalProperties] = None
        self.challenge: Optional[ResearchChallenge] = None
        self.hypotheses: List[Hypothesis] = []
        self.research_objective: Optional[str] = None
        self.analysis_history: List[Dict[str, Any]] = []

    def set_compound(self, drug_name: str, smiles: Optional[str] = None):
        """Set the compound being studied"""
        self.compound = CompoundProfile(
            drug_name=drug_name,
            smiles=smiles
        )
        self._log_event("compound_set", {"drug_name": drug_name})

    def update_properties(self, **properties):
        """Update physicochemical properties"""
        if not self.properties:
            self.properties = PhysicochemicalProperties()

        for key, value in properties.items():
            if hasattr(self.properties, key):
                setattr(self.properties, key, value)

        self._log_event("properties_updated", properties)

    def set_challenge(self, primary: str, mechanism: str, impact: str, severity: str = "medium"):
        """Define the primary research challenge"""
        self.challenge = ResearchChallenge(
            primary=primary,
            mechanism=mechanism,
            impact=impact,
            severity=severity
        )
        self._log_event("challenge_identified", {
            "primary": primary,
            "severity": severity
        })

    def add_hypothesis(
        self,
        name: str,
        mechanism: str,
        evidence: List[str],
        uncertainty: List[str],
        validation_methods: List[str],
        confidence_score: Optional[float] = None
    ) -> Hypothesis:
        """Add a new scientific hypothesis"""
        hypothesis = Hypothesis(
            id=f"H{len(self.hypotheses) + 1}",
            name=name,
            mechanism=mechanism,
            evidence=evidence,
            uncertainty=uncertainty,
            validation_methods=validation_methods,
            confidence_score=confidence_score
        )

        self.hypotheses.append(hypothesis)
        self._log_event("hypothesis_generated", {
            "id": hypothesis.id,
            "name": name,
            "confidence": confidence_score
        })

        return hypothesis

    def get_context_summary(self) -> str:
        """Get a summary of the current scientific context"""
        if not self.compound:
            return "No compound currently under investigation."

        summary_parts = []

        # Compound
        summary_parts.append(f"**Compound**: {self.compound.drug_name}")
        if self.compound.smiles:
            summary_parts.append(f"**SMILES**: {self.compound.smiles}")

        # Properties
        if self.properties:
            props = []
            if self.properties.logP is not None:
                props.append(f"LogP: {self.properties.logP:.2f}")
            if self.properties.logS is not None:
                props.append(f"LogS: {self.properties.logS:.2f}")
            if self.properties.bcs_class:
                props.append(f"BCS: Class {self.properties.bcs_class}")

            if props:
                summary_parts.append(f"**Properties**: {', '.join(props)}")

        # Challenge
        if self.challenge:
            summary_parts.append(f"**Challenge**: {self.challenge.primary}")
            summary_parts.append(f"**Impact**: {self.challenge.impact}")

        # Hypotheses
        if self.hypotheses:
            summary_parts.append(f"\n**Hypotheses Generated**: {len(self.hypotheses)}")
            for h in self.hypotheses:
                conf_str = f" (confidence: {h.confidence_score:.2f})" if h.confidence_score else ""
                summary_parts.append(f"- {h.id}: {h.name}{conf_str}")

        return "\n".join(summary_parts)

    def _log_event(self, event_type: str, data: Dict[str, Any]):
        """Log an analysis event"""
        self.analysis_history.append({
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "data": data
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization"""
        return {
            "compound": {
                "drug_name": self.compound.drug_name,
                "smiles": self.compound.smiles
            } if self.compound else None,

            "properties": {
                "logP": self.properties.logP,
                "logS": self.properties.logS,
                "bcs_class": self.properties.bcs_class,
                # Add more as needed
            } if self.properties else None,

            "challenge": {
                "primary": self.challenge.primary,
                "impact": self.challenge.impact,
                "severity": self.challenge.severity
            } if self.challenge else None,

            "hypotheses": [
                {
                    "id": h.id,
                    "name": h.name,
                    "mechanism": h.mechanism,
                    "evidence": h.evidence,
                    "uncertainty": h.uncertainty,
                    "validation_methods": h.validation_methods,
                    "confidence_score": h.confidence_score
                }
                for h in self.hypotheses
            ],

            "research_objective": self.research_objective,
            "analysis_history": self.analysis_history
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScientificState':
        """Restore state from dictionary"""
        state = cls()

        if data.get("compound"):
            state.set_compound(
                drug_name=data["compound"]["drug_name"],
                smiles=data["compound"].get("smiles")
            )

        if data.get("properties"):
            state.update_properties(**data["properties"])

        if data.get("challenge"):
            ch = data["challenge"]
            state.set_challenge(
                primary=ch["primary"],
                mechanism=ch.get("mechanism", ""),
                impact=ch["impact"],
                severity=ch.get("severity", "medium")
            )

        # Restore hypotheses
        for h_data in data.get("hypotheses", []):
            state.add_hypothesis(
                name=h_data["name"],
                mechanism=h_data["mechanism"],
                evidence=h_data["evidence"],
                uncertainty=h_data["uncertainty"],
                validation_methods=h_data["validation_methods"],
                confidence_score=h_data.get("confidence_score")
            )

        state.research_objective = data.get("research_objective")
        state.analysis_history = data.get("analysis_history", [])

        return state
