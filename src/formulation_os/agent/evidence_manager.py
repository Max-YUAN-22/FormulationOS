"""
Evidence Manager - Foundation for Evidence-Grounded Hypothesis Generation

This module implements the scientific reasoning chain:
    Observation → Interpretation → Mechanism → Hypothesis

Key principle:
    Evidence identifies MECHANISMS, not directly STRATEGIES.
    Strategies are matched to mechanisms through scientific knowledge.

Architecture:
    Layer 1: Observation (raw tool output)
    Layer 2: Scientific Interpretation (what does this mean?)
    Layer 3: Mechanism (what problem type?)
    Layer 4: Hypothesis (which strategies address this mechanism?)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import json


class EvidenceType(Enum):
    """Types of evidence sources"""
    COMPUTATIONAL_PREDICTION = "computational_prediction"
    LITERATURE = "literature"
    PHYSICOCHEMICAL = "physicochemical_property"
    MANUFACTURING = "manufacturing_constraint"
    REGULATORY = "regulatory_guideline"
    EXPERIMENTAL = "experimental_data"


class EvidenceSource(Enum):
    """Tool sources that generate evidence"""
    PREFORMULATION_AI = "PreformulationAI"
    FORMULATION_AI = "FormulationAI"
    LITERATURE_SEARCH = "LiteratureSearch"
    USER_INPUT = "UserInput"
    KNOWLEDGE_BASE = "KnowledgeBase"


class ScientificMechanism(Enum):
    """
    Scientific problem types (mechanisms) that evidence points to

    This is the bridge between evidence and strategies:
    Evidence → Mechanism → Strategy

    Example:
        LogS=-3.97 → DISSOLUTION_LIMITATION → [solid_dispersion, nanocrystal]
    """
    DISSOLUTION_LIMITATION = "dissolution_limitation"
    PERMEABILITY_BARRIER = "permeability_barrier"
    SOLUBILITY_LIMITATION = "solubility_limitation"
    STABILITY_ISSUE = "stability_issue"
    BIOAVAILABILITY_LOSS = "bioavailability_loss"
    CRYSTALLINITY_ISSUE = "crystallinity_issue"
    LIPID_SOLUBILIZATION = "lipid_solubilization"

    # Manufacturing-related
    POOR_FLOWABILITY = "poor_flowability"
    COMPRESSIBILITY_ISSUE = "compressibility_issue"


@dataclass
class Evidence:
    """
    Single piece of evidence with scientific reasoning chain

    Refactored design:
    - observation: Raw measurement (e.g., "LogS=-3.97")
    - interpretation: Scientific meaning (e.g., "poor aqueous solubility")
    - mechanism: Problem type (e.g., ScientificMechanism.DISSOLUTION_LIMITATION)
    - implications: What this means for formulation

    Example:
        Evidence(
            source=EvidenceSource.PREFORMULATION_AI,
            type=EvidenceType.PHYSICOCHEMICAL,
            observation="LogS=-3.97",
            interpretation="poor aqueous solubility",
            mechanism=ScientificMechanism.DISSOLUTION_LIMITATION,
            confidence=0.9,
            raw_data={"LogS": -3.97, "unit": "mol/L"},
            implications="Drug dissolution will be rate-limiting for absorption"
        )
    """
    # Core fields
    source: EvidenceSource
    type: EvidenceType
    observation: str  # Raw measurement (e.g., "LogS=-3.97")
    interpretation: str  # Scientific meaning (e.g., "poor aqueous solubility")
    mechanism: ScientificMechanism  # Problem type this evidence points to
    confidence: float  # 0-1
    raw_data: Dict[str, Any]  # Original tool output

    # Additional context
    implications: str = ""  # What this means for formulation
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict:
        """Serialize for storage"""
        return {
            "source": self.source.value,
            "type": self.type.value,
            "observation": self.observation,
            "interpretation": self.interpretation,
            "mechanism": self.mechanism.value,
            "confidence": self.confidence,
            "raw_data": self.raw_data,
            "implications": self.implications,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Evidence':
        """Deserialize from storage"""
        return cls(
            source=EvidenceSource(data["source"]),
            type=EvidenceType(data["type"]),
            observation=data["observation"],
            interpretation=data["interpretation"],
            mechanism=ScientificMechanism(data["mechanism"]),
            confidence=data["confidence"],
            raw_data=data["raw_data"],
            implications=data.get("implications", ""),
            timestamp=data.get("timestamp")
        )


class MechanismKnowledgeBase:
    """
    Scientific knowledge: Mechanism → Strategy mapping

    This encodes pharmaceutical science knowledge about which strategies
    address which problem types.

    Example:
        DISSOLUTION_LIMITATION → [solid_dispersion, nanocrystal, SEDDS, cyclodextrin]
    """

    MECHANISM_TO_STRATEGIES = {
        ScientificMechanism.DISSOLUTION_LIMITATION: [
            "solid_dispersion",
            "nanocrystal",
            "cyclodextrin_complex",
            "salt_formation"
        ],
        ScientificMechanism.SOLUBILITY_LIMITATION: [
            "solid_dispersion",
            "nanocrystal",
            "cyclodextrin_complex",
            "cocrystal",
            "SEDDS",
            "liposomal_formulation"
        ],
        ScientificMechanism.LIPID_SOLUBILIZATION: [
            "SEDDS",
            "lipid_formulation",
            "solid_lipid_nanoparticle"
        ],
        ScientificMechanism.PERMEABILITY_BARRIER: [
            "permeation_enhancer",
            "nanoparticle",
            "lipid_formulation"
        ],
        ScientificMechanism.STABILITY_ISSUE: [
            "solid_dispersion",
            "stabilizer_addition",
            "protective_coating"
        ],
        ScientificMechanism.CRYSTALLINITY_ISSUE: [
            "solid_dispersion",
            "cocrystal",
            "salt_formation"
        ]
    }

    @staticmethod
    def get_strategies_for_mechanism(mechanism: ScientificMechanism) -> List[str]:
        """Return formulation strategies that address a given mechanism"""
        return MechanismKnowledgeBase.MECHANISM_TO_STRATEGIES.get(mechanism, [])


class EvidenceManager:
    """
    Central evidence collection and retrieval system

    Implements scientific reasoning chain:
        Tool Output → Evidence (Observation + Interpretation + Mechanism)

    Responsibilities:
    1. Capture evidence from all tool calls
    2. Interpret observations into scientific mechanisms
    3. Store evidence with full reasoning chain
    4. Provide mechanism-based evidence retrieval
    """

    def __init__(self):
        self.evidence_pool: List[Evidence] = []
        self.mechanism_kb = MechanismKnowledgeBase()

    def capture_from_tool_call(self, tool_name: str, tool_result: Dict[str, Any]) -> List[Evidence]:
        """
        Extract evidence from tool outputs

        This is the critical bridge: Tool Output → Evidence Object
        Now includes scientific interpretation and mechanism identification

        Args:
            tool_name: Name of the tool that was called
            tool_result: Raw tool output

        Returns:
            List of Evidence objects with reasoning chain
        """
        evidence_list = []

        # Match tool names with or without _ai prefix
        if "preformulation" in tool_name and ("fundamentals" in tool_name or "developability" in tool_name):
            evidence_list.extend(self._extract_preformulation_evidence(tool_result))
        elif "formulation" in tool_name and tool_name != "preformulation_ai_developability":
            evidence_list.extend(self._extract_formulation_evidence(tool_result))
        elif "literature" in tool_name:
            evidence_list.extend(self._extract_literature_evidence(tool_result))

        # Add to pool
        self.evidence_pool.extend(evidence_list)

        return evidence_list

    def _extract_preformulation_evidence(self, result: Dict) -> List[Evidence]:
        """
        Extract evidence from PreformulationAI tool

        New architecture: Observation → Interpretation → Mechanism
        """
        evidence_list = []

        # Handle nested properties structure from real tools
        if 'properties' in result and isinstance(result['properties'], dict):
            properties = result['properties']
        else:
            properties = result

        # Normalize keys to handle case variations (BCS_class vs bcs_class)
        normalized_result = {k.lower(): v for k, v in properties.items()}

        # BCS Classification (can be in top-level result or properties)
        bcs_normalized = {k.lower(): v for k, v in result.items()}
        if "bcs_class" in bcs_normalized:
            bcs_class = bcs_normalized["bcs_class"]

            # Determine mechanism based on BCS class
            if bcs_class in ["II", "IV"]:
                mechanism = ScientificMechanism.DISSOLUTION_LIMITATION
                interpretation = "Low solubility drug - dissolution-limited absorption"
                implications = "Bioavailability enhancement requires solubility/dissolution improvement"
            elif bcs_class == "III":
                mechanism = ScientificMechanism.PERMEABILITY_BARRIER
                interpretation = "Permeability-limited absorption"
                implications = "Bioavailability enhancement requires permeation enhancement"
            else:
                mechanism = ScientificMechanism.BIOAVAILABILITY_LOSS
                interpretation = "BCS Class I - high solubility and permeability"
                implications = "No major bioavailability challenge"

            evidence_list.append(Evidence(
                source=EvidenceSource.PREFORMULATION_AI,
                type=EvidenceType.COMPUTATIONAL_PREDICTION,
                observation=f"BCS Class {bcs_class}",
                interpretation=interpretation,
                mechanism=mechanism,
                confidence=0.95,
                raw_data={"bcs_class": bcs_class},
                implications=implications
            ))

        # Solubility
        if "logs" in normalized_result:
            log_s = float(normalized_result["logs"])

            observation = f"LogS={log_s}"

            if log_s < -3.5:
                interpretation = "poor aqueous solubility"
                mechanism = ScientificMechanism.SOLUBILITY_LIMITATION
                implications = "Drug dissolution will be rate-limiting for absorption. Solubility enhancement is critical."
                confidence = 0.9
            elif log_s < -2:
                interpretation = "moderate aqueous solubility"
                mechanism = ScientificMechanism.DISSOLUTION_LIMITATION
                implications = "Dissolution may be limiting at higher doses. Consider enhancement strategies."
                confidence = 0.75
            else:
                interpretation = "good aqueous solubility"
                mechanism = ScientificMechanism.BIOAVAILABILITY_LOSS
                implications = "Solubility is not a major barrier."
                confidence = 0.9

            evidence_list.append(Evidence(
                source=EvidenceSource.PREFORMULATION_AI,
                type=EvidenceType.PHYSICOCHEMICAL,
                observation=observation,
                interpretation=interpretation,
                mechanism=mechanism,
                confidence=confidence,
                raw_data={"LogS": log_s, "unit": "mol/L"},
                implications=implications
            ))

        # Lipophilicity
        if "logp" in normalized_result:
            log_p = float(normalized_result["logp"])

            observation = f"LogP={log_p}"

            if log_p > 3:
                interpretation = "high lipophilicity"
                mechanism = ScientificMechanism.LIPID_SOLUBILIZATION
                implications = "Lipid-based formulations may enhance solubilization and absorption"
                confidence = 0.85
            elif log_p > 1:
                interpretation = "moderate lipophilicity"
                mechanism = ScientificMechanism.BIOAVAILABILITY_LOSS
                implications = "Balanced lipophilicity - multiple formulation approaches viable"
                confidence = 0.7
            else:
                interpretation = "low lipophilicity"
                mechanism = ScientificMechanism.BIOAVAILABILITY_LOSS
                implications = "Hydrophilic drug - lipid formulations less suitable"
                confidence = 0.8

            evidence_list.append(Evidence(
                source=EvidenceSource.PREFORMULATION_AI,
                type=EvidenceType.PHYSICOCHEMICAL,
                observation=observation,
                interpretation=interpretation,
                mechanism=mechanism,
                confidence=confidence,
                raw_data={"LogP": log_p},
                implications=implications
            ))

        # Molecular Weight
        if "molecular_weight" in result:
            mw = float(result["molecular_weight"])
            observation = f"Molecular weight={mw} Da"

            if mw > 500:
                interpretation = "large molecular size"
                mechanism = ScientificMechanism.PERMEABILITY_BARRIER
                implications = "Large molecules may have permeability limitations"
                confidence = 0.7
            else:
                interpretation = "small molecule"
                mechanism = ScientificMechanism.BIOAVAILABILITY_LOSS
                implications = "Molecular size is not a major barrier"
                confidence = 0.8

            evidence_list.append(Evidence(
                source=EvidenceSource.PREFORMULATION_AI,
                type=EvidenceType.PHYSICOCHEMICAL,
                observation=observation,
                interpretation=interpretation,
                mechanism=mechanism,
                confidence=confidence,
                raw_data={"MW": mw, "unit": "Da"},
                implications=implications
            ))

        return evidence_list

    def _extract_formulation_evidence(self, result: Dict) -> List[Evidence]:
        """Extract evidence from FormulationAI tool"""
        evidence_list = []

        # Handle solid dispersion predictions
        if "physical_stability" in result:
            stability = result["physical_stability"]
            confidence = result.get("confidence", 0.7)

            evidence_list.append(Evidence(
                source=EvidenceSource.FORMULATION_AI,
                type=EvidenceType.COMPUTATIONAL_PREDICTION,
                observation=f"Solid dispersion stability: {stability}",
                interpretation="Physical stability prediction for amorphous solid dispersion",
                mechanism=ScientificMechanism.DISSOLUTION_LIMITATION,
                confidence=confidence,
                raw_data=result,
                implications="Solid dispersion approach may improve dissolution rate"
            ))

        # Handle nanocrystal predictions
        if "predicted_particle_size_nm" in result:
            particle_size = result["predicted_particle_size_nm"]
            confidence = result.get("confidence", 0.7)

            evidence_list.append(Evidence(
                source=EvidenceSource.FORMULATION_AI,
                type=EvidenceType.COMPUTATIONAL_PREDICTION,
                observation=f"Predicted nanocrystal size: {particle_size} nm",
                interpretation="Nanocrystallization can increase surface area for dissolution",
                mechanism=ScientificMechanism.DISSOLUTION_LIMITATION,
                confidence=confidence,
                raw_data=result,
                implications="Nanocrystal formulation may enhance dissolution and bioavailability"
            ))

        # Handle cyclodextrin predictions
        if "complexation_free_energy_kj_mol" in result:
            free_energy = result["complexation_free_energy_kj_mol"]
            confidence = result.get("confidence", 0.7)

            mechanism = ScientificMechanism.SOLUBILITY_LIMITATION if free_energy < -10 else ScientificMechanism.BIOAVAILABILITY_LOSS

            evidence_list.append(Evidence(
                source=EvidenceSource.FORMULATION_AI,
                type=EvidenceType.COMPUTATIONAL_PREDICTION,
                observation=f"Cyclodextrin complexation ΔG: {free_energy} kJ/mol",
                interpretation="Favorable host-guest interaction" if free_energy < -10 else "Weak complexation",
                mechanism=mechanism,
                confidence=confidence,
                raw_data=result,
                implications="Cyclodextrin inclusion may improve solubility" if free_energy < -10 else "Cyclodextrin complexation less favorable"
            ))

        # Legacy: Handle old format if present
        if "recommended_strategy" in result:
            strategy = result["recommended_strategy"]
            confidence = result.get("confidence", 0.7)
            reasoning = result.get("reasoning", "")

            mechanism = ScientificMechanism.DISSOLUTION_LIMITATION

            evidence_list.append(Evidence(
                source=EvidenceSource.FORMULATION_AI,
                type=EvidenceType.COMPUTATIONAL_PREDICTION,
                observation=f"AI-recommended strategy: {strategy}",
                interpretation=reasoning if reasoning else f"{strategy} predicted as suitable",
                mechanism=mechanism,
                confidence=confidence,
                raw_data=result,
                implications=f"FormulationAI suggests {strategy} based on drug properties"
            ))

        return evidence_list

    def _extract_literature_evidence(self, result: Dict) -> List[Evidence]:
        """Extract evidence from literature search results"""
        evidence_list = []

        # This will be implemented when literature search tool is added
        # For now, placeholder

        return evidence_list

    def get_evidence_by_mechanism(self, mechanism: ScientificMechanism) -> List[Evidence]:
        """
        Retrieve all evidence pointing to a specific mechanism

        This is the key retrieval method for hypothesis generation:
        Mechanism → Evidence → Confidence calculation
        """
        return [e for e in self.evidence_pool if e.mechanism == mechanism]

    def get_all_mechanisms(self) -> List[ScientificMechanism]:
        """Return all unique mechanisms identified from evidence"""
        return list(set(e.mechanism for e in self.evidence_pool))

    def get_strategies_for_evidence(self) -> Dict[str, float]:
        """
        Generate strategy candidates based on collected evidence

        Returns:
            Dict mapping strategy names to evidence-based confidence scores

        Example:
            {
                "solid_dispersion": 0.85,
                "nanocrystal": 0.78,
                "SEDDS": 0.65
            }
        """
        strategy_evidence_map = {}

        # For each identified mechanism, get candidate strategies
        for mechanism in self.get_all_mechanisms():
            strategies = self.mechanism_kb.get_strategies_for_mechanism(mechanism)
            evidence_list = self.get_evidence_by_mechanism(mechanism)

            # Calculate evidence strength for this mechanism
            mechanism_confidence = sum(e.confidence for e in evidence_list) / len(evidence_list) if evidence_list else 0

            # Assign confidence to each strategy
            for strategy in strategies:
                if strategy not in strategy_evidence_map:
                    strategy_evidence_map[strategy] = []
                strategy_evidence_map[strategy].append(mechanism_confidence)

        # Average confidence across all supporting mechanisms
        strategy_scores = {
            strategy: sum(confidences) / len(confidences)
            for strategy, confidences in strategy_evidence_map.items()
        }

        return strategy_scores

    def get_evidence_for_strategy(self, strategy_name: str) -> Dict[str, Any]:
        """
        Retrieve all evidence supporting a specific strategy

        Returns:
            {
                "supporting_mechanisms": [ScientificMechanism, ...],
                "evidence": [Evidence, ...],
                "confidence": float,
                "reasoning": str
            }
        """
        supporting_mechanisms = []
        supporting_evidence = []

        # Find all mechanisms that this strategy addresses
        for mechanism, strategies in self.mechanism_kb.MECHANISM_TO_STRATEGIES.items():
            if strategy_name in strategies:
                supporting_mechanisms.append(mechanism)
                supporting_evidence.extend(self.get_evidence_by_mechanism(mechanism))

        # Calculate confidence
        if supporting_evidence:
            confidence = sum(e.confidence for e in supporting_evidence) / len(supporting_evidence)
        else:
            confidence = 0.0

        # Generate reasoning
        reasoning_parts = []
        for mechanism in supporting_mechanisms:
            evidence_for_mechanism = self.get_evidence_by_mechanism(mechanism)
            if evidence_for_mechanism:
                reasoning_parts.append(
                    f"Addresses {mechanism.value}: {len(evidence_for_mechanism)} supporting evidence"
                )

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "No supporting evidence"

        return {
            "supporting_mechanisms": supporting_mechanisms,
            "evidence": supporting_evidence,
            "confidence": confidence,
            "reasoning": reasoning
        }

    def generate_evidence_summary(self) -> str:
        """
        Generate human-readable evidence summary

        Format:
            Evidence Collected (N items):

            Mechanism: DISSOLUTION_LIMITATION
            - LogS=-3.97 (poor aqueous solubility) [0.9]
            - BCS Class II [0.95]
        """
        summary_lines = [f"Evidence Collected ({len(self.evidence_pool)} items):\n"]

        mechanisms = self.get_all_mechanisms()
        for mechanism in mechanisms:
            evidence_list = self.get_evidence_by_mechanism(mechanism)
            summary_lines.append(f"\n**{mechanism.value.upper()}**")

            for evidence in evidence_list:
                summary_lines.append(
                    f"  - {evidence.observation} ({evidence.interpretation}) [{evidence.confidence:.2f}]"
                )
                if evidence.implications:
                    summary_lines.append(f"    → {evidence.implications}")

        return "\n".join(summary_lines)

    def get_all_evidence(self) -> List[Evidence]:
        """Return all collected evidence"""
        return self.evidence_pool

    def clear(self):
        """Clear evidence pool (for new session)"""
        self.evidence_pool.clear()

    def export_to_dict(self) -> List[Dict]:
        """Export all evidence for storage"""
        return [e.to_dict() for e in self.evidence_pool]

    def import_from_dict(self, data: List[Dict]):
        """Import evidence from storage"""
        self.evidence_pool = [Evidence.from_dict(d) for d in data]
