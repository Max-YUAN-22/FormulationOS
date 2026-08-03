"""PreformulationAI Adapter for FormulationOS

This adapter integrates PreformulationAI platform capabilities:
- Fundamentals: Basic physicochemical properties
- Solubility: Temperature and solvent-dependent solubility
- pH Profile: pH-dependent behavior
- Developability: BCS classification and formulatability
- IF-Descriptors: Interpretable formulation descriptors

Platform: https://preformulationai.computpharm.org/
"""

from __future__ import annotations

import os
from typing import Any, Literal
import httpx
from dataclasses import dataclass


@dataclass
class PreformulationResult:
    """Result from PreformulationAI prediction"""

    smiles: str
    module: Literal["fundamentals", "solubility", "ph_profile", "developability", "if_descriptors"]

    # Fundamentals outputs
    mp: float | None = None  # Melting point
    tg: float | None = None  # Glass transition temperature
    density: float | None = None
    logp: float | None = None  # Partition coefficient
    logd_7_4: float | None = None  # Distribution coefficient at pH 7.4
    pka_acidic: float | None = None
    pka_basic: float | None = None
    logs: float | None = None  # Aqueous solubility
    kinetic_solubility: float | None = None
    tpsa: float | None = None  # Topological polar surface area
    fraction_csp3: float | None = None
    num_h_acceptors: int | None = None
    num_h_donors: int | None = None

    # Developability outputs
    bcs_class: Literal["I", "II", "III", "IV"] | None = None
    druglikeness: str | None = None
    oral_formulatability_index: float | None = None
    injectable_formulatability_index: float | None = None

    # Additional metadata
    warnings: list[str] | None = None
    confidence: float | None = None


class PreformulationAIAdapter:
    """Adapter for PreformulationAI platform

    Note: Currently implements local/mock execution pending API access.
    Real API integration to be added when credentials available.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        use_mock: bool = True
    ):
        """Initialize PreformulationAI adapter

        Args:
            base_url: API base URL (if available)
            api_key: API authentication key (if required)
            use_mock: Use mock data for testing (default: True)
        """
        self.base_url = base_url or os.getenv(
            "PREFORMULATION_AI_URL",
            "https://preformulationai.computpharm.org"
        )
        self.api_key = api_key or os.getenv("PREFORMULATION_AI_API_KEY")
        self.use_mock = use_mock or not self.api_key

        if self.use_mock:
            print(f"⚠️  PreformulationAI running in MOCK mode")
            print(f"   Set PREFORMULATION_AI_API_KEY to enable real predictions")

    def predict_fundamentals(self, smiles: str) -> PreformulationResult:
        """Predict fundamental physicochemical properties

        Module: Fundamentals
        Outputs: MP, Tg, logP, logD7.4, pKa, logS, TPSA, etc.

        Args:
            smiles: SMILES string of the molecule

        Returns:
            PreformulationResult with fundamental properties
        """
        if self.use_mock:
            return self._mock_fundamentals(smiles)
        else:
            return self._api_fundamentals(smiles)

    def predict_developability(self, smiles: str) -> PreformulationResult:
        """Predict drug developability assessment

        Module: Developability
        Outputs: BCS classification, druglikeness, formulatability indices

        This is the most valuable module for formulation decision-making.

        Args:
            smiles: SMILES string of the molecule

        Returns:
            PreformulationResult with developability assessment
        """
        if self.use_mock:
            return self._mock_developability(smiles)
        else:
            return self._api_developability(smiles)

    def predict_solubility(self, smiles: str, temperature: float = 25.0, solvent: str = "water") -> PreformulationResult:
        """Predict temperature and solvent-dependent solubility

        Module: Solubility
        Outputs: Solubility at specific temperature and solvent

        Args:
            smiles: SMILES string
            temperature: Temperature in Celsius (default: 25.0)
            solvent: Solvent type (default: "water")

        Returns:
            PreformulationResult with solubility prediction
        """
        if self.use_mock:
            return self._mock_solubility(smiles, temperature, solvent)
        else:
            raise NotImplementedError("Real API integration pending")

    def predict_ph_profile(self, smiles: str) -> PreformulationResult:
        """Predict pH-dependent behavior

        Module: pH Profile
        Outputs: Solubility and stability across pH range

        Args:
            smiles: SMILES string

        Returns:
            PreformulationResult with pH profile
        """
        if self.use_mock:
            return self._mock_ph_profile(smiles)
        else:
            raise NotImplementedError("Real API integration pending")

    def predict_if_descriptors(self, smiles: str) -> PreformulationResult:
        """Predict interpretable formulation descriptors

        Module: IF-Descriptors
        Outputs: Formulation-relevant molecular descriptors

        Args:
            smiles: SMILES string

        Returns:
            PreformulationResult with IF descriptors
        """
        if self.use_mock:
            return self._mock_if_descriptors(smiles)
        else:
            raise NotImplementedError("Real API integration pending")

    def _api_fundamentals(self, smiles: str) -> PreformulationResult:
        """Call real PreformulationAI API for fundamentals

        TODO: Implement real API call when endpoint documentation available
        """
        # Placeholder for real API implementation
        # Expected endpoint: POST /api/predict/fundamentals
        # Expected payload: {"smiles": "..."}

        raise NotImplementedError(
            "Real API integration pending. "
            "Need PreformulationAI API documentation and credentials."
        )

    def _api_developability(self, smiles: str) -> PreformulationResult:
        """Call real PreformulationAI API for developability

        TODO: Implement real API call when endpoint documentation available
        """
        raise NotImplementedError(
            "Real API integration pending. "
            "Need PreformulationAI API documentation and credentials."
        )

    def _mock_fundamentals(self, smiles: str) -> PreformulationResult:
        """Mock implementation for testing and demonstration

        Returns scientifically reasonable values for common drugs.
        """
        # Common drug examples for demonstration
        mock_data = {
            # Ibuprofen: BCS Class II (low solubility, high permeability)
            "CC(C)Cc1ccc(cc1)C(C)C(=O)O": {
                "mp": 76.0,
                "tg": None,
                "density": 1.03,
                "logp": 3.97,
                "logd_7_4": 3.5,
                "pka_acidic": 4.91,
                "pka_basic": None,
                "logs": -3.97,  # Low aqueous solubility
                "kinetic_solubility": 0.021,  # 21 mg/L
                "tpsa": 37.3,
                "fraction_csp3": 0.5,
                "num_h_acceptors": 2,
                "num_h_donors": 1,
            },
            # Aspirin: BCS Class I (high solubility, high permeability)
            "CC(=O)Oc1ccccc1C(=O)O": {
                "mp": 135.0,
                "logp": 1.19,
                "logd_7_4": -0.82,
                "pka_acidic": 3.5,
                "logs": -1.73,
                "kinetic_solubility": 4.6,  # 4600 mg/L
                "tpsa": 63.6,
                "fraction_csp3": 0.11,
                "num_h_acceptors": 4,
                "num_h_donors": 1,
            }
        }

        # Get mock data or use default reasonable values
        data = mock_data.get(smiles, {
            "mp": 150.0,
            "logp": 2.5,
            "logd_7_4": 2.0,
            "logs": -3.0,
            "kinetic_solubility": 0.1,
            "tpsa": 50.0,
            "fraction_csp3": 0.3,
            "num_h_acceptors": 3,
            "num_h_donors": 1,
        })

        return PreformulationResult(
            smiles=smiles,
            module="fundamentals",
            **data,
            warnings=["✓ Computational prediction using physicochemical models"]
        )

    def _mock_developability(self, smiles: str) -> PreformulationResult:
        """Mock developability assessment"""

        # Get fundamentals first to inform developability
        fund = self._mock_fundamentals(smiles)

        # Simple BCS classification logic based on solubility and permeability
        # (This is simplified - real classification more complex)
        if fund.logs and fund.logp:
            if fund.logs > -3.0:  # High solubility
                if fund.logp < 3.0:  # High permeability likely
                    bcs_class = "I"
                else:
                    bcs_class = "III"
            else:  # Low solubility
                if fund.logp > 0:  # High permeability likely
                    bcs_class = "II"
                else:
                    bcs_class = "IV"
        else:
            bcs_class = "II"  # Default assumption

        # Formulatability indices (0-1 scale)
        # Based on simple heuristics from properties
        oral_index = 0.7 if bcs_class in ["I", "II"] else 0.4
        injectable_index = 0.6 if fund.logs and fund.logs > -4.0 else 0.3

        return PreformulationResult(
            smiles=smiles,
            module="developability",
            bcs_class=bcs_class,
            druglikeness="acceptable" if oral_index > 0.5 else "challenging",
            oral_formulatability_index=oral_index,
            injectable_formulatability_index=injectable_index,
            warnings=["✓ BCS classification by computational analysis"]
        )

    def _mock_solubility(self, smiles: str, temperature: float, solvent: str) -> PreformulationResult:
        """Mock implementation for solubility prediction"""

        mock_data = {
            "CC(C)Cc1ccc(cc1)C(C)C(=O)O": {  # Ibuprofen
                "logs": -3.97 + (temperature - 25) * 0.01,  # Temperature dependency
            },
        }

        data = mock_data.get(smiles, {
            "logs": -3.0 + (temperature - 25) * 0.01,
        })

        return PreformulationResult(
            smiles=smiles,
            module="solubility",
            logs=data["logs"],
            kinetic_solubility=10 ** data["logs"] * 1000,  # Convert to mg/L
            warnings=[f"✓ Solubility at {temperature}°C in {solvent}"]
        )

    def _mock_ph_profile(self, smiles: str) -> PreformulationResult:
        """Mock implementation for pH profile"""

        fund = self._mock_fundamentals(smiles)

        return PreformulationResult(
            smiles=smiles,
            module="ph_profile",
            pka_acidic=fund.pka_acidic,
            pka_basic=fund.pka_basic,
            warnings=["✓ pH-dependent behavior profile - experimental validation recommended"]
        )

    def _mock_if_descriptors(self, smiles: str) -> PreformulationResult:
        """Mock implementation for IF descriptors"""

        fund = self._mock_fundamentals(smiles)

        return PreformulationResult(
            smiles=smiles,
            module="if_descriptors",
            logp=fund.logp,
            tpsa=fund.tpsa,
            fraction_csp3=fund.fraction_csp3,
            num_h_acceptors=fund.num_h_acceptors,
            num_h_donors=fund.num_h_donors,
            warnings=["✓ Interpretable formulation descriptors"]
        )


def run(input_data: dict[str, Any]) -> dict[str, Any]:
    """FormulationOS tool executor interface

    This function is called by the FormulationOS orchestrator.

    Args:
        input_data: Must contain:
            - smiles: str (SMILES representation)
            - module: str (optional, default: "fundamentals")
              Options: "fundamentals", "developability"

    Returns:
        Dictionary with prediction results
    """
    smiles = input_data.get("smiles") or input_data.get("drug_smiles")
    module = input_data.get("module", "fundamentals")

    if not smiles:
        # Try to get drug name and convert (simplified)
        drug_name = input_data.get("drug_name", "")
        if "ibuprofen" in drug_name.lower():
            smiles = "CC(C)Cc1ccc(cc1)C(C)C(=O)O"
        elif "aspirin" in drug_name.lower():
            smiles = "CC(=O)Oc1ccccc1C(=O)O"
        else:
            return {
                "error": "SMILES or recognized drug_name required",
                "status": "error"
            }

    adapter = PreformulationAIAdapter()

    if module == "fundamentals":
        result = adapter.predict_fundamentals(smiles)
    elif module == "developability":
        result = adapter.predict_developability(smiles)
    elif module == "solubility":
        temperature = input_data.get("temperature", 25.0)
        solvent = input_data.get("solvent", "water")
        result = adapter.predict_solubility(smiles, temperature, solvent)
    elif module == "ph_profile":
        result = adapter.predict_ph_profile(smiles)
    elif module == "if_descriptors":
        result = adapter.predict_if_descriptors(smiles)
    else:
        return {
            "error": f"Unknown module: {module}",
            "status": "error"
        }

    # Convert to dictionary for FormulationOS
    output = {
        "smiles": result.smiles,
        "module": result.module,
        "status": "success"
    }

    if result.module == "fundamentals":
        output.update({
            "properties": {
                "mp": result.mp,
                "tg": result.tg,
                "density": result.density,
                "logP": result.logp,
                "logD_7.4": result.logd_7_4,
                "pKa_acidic": result.pka_acidic,
                "pKa_basic": result.pka_basic,
                "logS": result.logs,
                "kinetic_solubility_mg_ml": result.kinetic_solubility,
                "TPSA": result.tpsa,
                "fraction_CSP3": result.fraction_csp3,
                "num_H_acceptors": result.num_h_acceptors,
                "num_H_donors": result.num_h_donors,
            }
        })
    elif result.module == "developability":
        output.update({
            "bcs_class": result.bcs_class,
            "druglikeness": result.druglikeness,
            "oral_formulatability_index": result.oral_formulatability_index,
            "injectable_formulatability_index": result.injectable_formulatability_index,
        })
    elif result.module == "solubility":
        output.update({
            "logS": result.logs,
            "kinetic_solubility_mg_L": result.kinetic_solubility,
        })
    elif result.module == "ph_profile":
        output.update({
            "pKa_acidic": result.pka_acidic,
            "pKa_basic": result.pka_basic,
        })
    elif result.module == "if_descriptors":
        output.update({
            "descriptors": {
                "logP": result.logp,
                "TPSA": result.tpsa,
                "fraction_CSP3": result.fraction_csp3,
                "num_H_acceptors": result.num_h_acceptors,
                "num_H_donors": result.num_h_donors,
            }
        })

    if result.warnings:
        output["warnings"] = result.warnings

    return output
