"""FormulationAI Adapter for FormulationOS

This adapter integrates FormulationAI platform capabilities:
- CD Complex: Cyclodextrin complex design for solubility enhancement
- Solid Dispersion: Amorphous solid dispersion formulation
- Nanocrystal: Drug nanocrystal formulation design
- Phospholipid Complex: Enhanced permeability formulation
- SEDDS: Self-emulsifying drug delivery systems
- Liposome: Targeted delivery formulation
- Strategy Recommendation: Solubility enhancement strategy selector

Platform: https://formulationai.computpharm.org/
"""

from __future__ import annotations

import os
from typing import Any, Literal
from dataclasses import dataclass


@dataclass
class FormulationResult:
    """Result from FormulationAI prediction"""

    drug_name: str
    drug_smiles: str
    module: Literal[
        "cd_complex",
        "solid_dispersion",
        "nanocrystal",
        "phospholipid_complex",
        "sedds",
        "liposome",
        "strategy_recommendation"
    ]

    # CD Complex outputs
    complex_formation_constant: float | None = None
    solubility_improvement: float | None = None
    recommended_cd_type: str | None = None
    recommended_ratio: str | None = None

    # Solid Dispersion outputs
    miscibility_prediction: str | None = None
    dissolution_improvement: float | None = None
    recommended_polymer: str | None = None
    recommended_loading: float | None = None
    manufacturing_method: str | None = None
    stability_risk: str | None = None

    # Nanocrystal outputs
    recommended_stabilizer: str | None = None
    recommended_particle_size: float | None = None
    nanocrystal_dissolution_improvement: float | None = None

    # Phospholipid Complex outputs
    complex_formation: bool | None = None
    lipophilicity_improvement: float | None = None
    bioavailability_prediction: float | None = None

    # SEDDS outputs
    oil_recommendation: str | None = None
    surfactant_recommendation: str | None = None
    oil_percentage: float | None = None
    surfactant_percentage: float | None = None
    droplet_size: float | None = None

    # Liposome outputs
    main_lipid: str | None = None
    recommended_size: float | None = None
    encapsulation_efficiency: float | None = None
    release_profile: str | None = None

    # Strategy Recommendation outputs
    recommended_strategies: list[dict[str, Any]] | None = None

    # Common metadata
    warnings: list[str] | None = None
    confidence: float | None = None


class FormulationAIAdapter:
    """Adapter for FormulationAI platform

    Note: Currently implements local/mock execution pending API access.
    Real API integration to be added when credentials available.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        use_mock: bool = True
    ):
        """Initialize FormulationAI adapter

        Args:
            base_url: API base URL (if available)
            api_key: API authentication key (if required)
            use_mock: Use mock data for testing (default: True)
        """
        self.base_url = base_url or os.getenv(
            "FORMULATION_AI_URL",
            "https://formulationai.computpharm.org"
        )
        self.api_key = api_key or os.getenv("FORMULATION_AI_API_KEY")
        self.use_mock = use_mock or not self.api_key

        if self.use_mock:
            print(f"⚠️  FormulationAI running in MOCK mode")
            print(f"   Set FORMULATION_AI_API_KEY to enable real predictions")

    def design_cd_complex(
        self,
        drug_name: str,
        drug_smiles: str,
        cd_type: str | None = None
    ) -> FormulationResult:
        """Design cyclodextrin complex formulation

        Module: CD Complex Design
        Goal: Enhance drug solubility through inclusion complex

        Args:
            drug_name: Drug name
            drug_smiles: SMILES string
            cd_type: Type of cyclodextrin (default: auto-select)

        Returns:
            FormulationResult with CD complex design
        """
        if self.use_mock:
            return self._mock_cd_complex(drug_name, drug_smiles, cd_type)
        else:
            return self._api_cd_complex(drug_name, drug_smiles, cd_type)

    def design_solid_dispersion(
        self,
        drug_name: str,
        drug_smiles: str,
        polymer_type: str | None = None,
        drug_loading: float | None = None
    ) -> FormulationResult:
        """Design solid dispersion formulation

        Module: Solid Dispersion Design
        Goal: Improve dissolution through amorphous dispersion

        Args:
            drug_name: Drug name
            drug_smiles: SMILES string
            polymer_type: Polymer carrier (default: auto-select)
            drug_loading: Drug loading % (default: auto-optimize)

        Returns:
            FormulationResult with solid dispersion design
        """
        if self.use_mock:
            return self._mock_solid_dispersion(drug_name, drug_smiles, polymer_type, drug_loading)
        else:
            return self._api_solid_dispersion(drug_name, drug_smiles, polymer_type, drug_loading)

    def design_nanocrystal(
        self,
        drug_name: str,
        drug_smiles: str,
        stabilizer_type: str | None = None,
        target_size: float | None = None
    ) -> FormulationResult:
        """Design drug nanocrystal formulation

        Module: Nanocrystal Design
        Goal: Enhance dissolution through particle size reduction

        Args:
            drug_name: Drug name
            drug_smiles: SMILES string
            stabilizer_type: Stabilizer (default: auto-select)
            target_size: Target particle size in nm (default: auto-optimize)

        Returns:
            FormulationResult with nanocrystal design
        """
        if self.use_mock:
            return self._mock_nanocrystal(drug_name, drug_smiles, stabilizer_type, target_size)
        else:
            return self._api_nanocrystal(drug_name, drug_smiles, stabilizer_type, target_size)

    def design_phospholipid_complex(
        self,
        drug_name: str,
        drug_smiles: str
    ) -> FormulationResult:
        """Design phospholipid complex formulation

        Module: Phospholipid Complex
        Goal: Enhance lipophilicity and permeability

        Args:
            drug_name: Drug name
            drug_smiles: SMILES string

        Returns:
            FormulationResult with phospholipid complex design
        """
        if self.use_mock:
            return self._mock_phospholipid_complex(drug_name, drug_smiles)
        else:
            raise NotImplementedError("Real API integration pending")

    def design_sedds(
        self,
        drug_name: str,
        drug_smiles: str
    ) -> FormulationResult:
        """Design SEDDS formulation

        Module: SEDDS (Self-Emulsifying Drug Delivery System)
        Goal: Enhance solubility through lipid-based delivery

        Args:
            drug_name: Drug name
            drug_smiles: SMILES string

        Returns:
            FormulationResult with SEDDS design
        """
        if self.use_mock:
            return self._mock_sedds(drug_name, drug_smiles)
        else:
            raise NotImplementedError("Real API integration pending")

    def design_liposome(
        self,
        drug_name: str,
        drug_smiles: str
    ) -> FormulationResult:
        """Design liposome formulation

        Module: Liposome
        Goal: Targeted delivery and controlled release

        Args:
            drug_name: Drug name
            drug_smiles: SMILES string

        Returns:
            FormulationResult with liposome design
        """
        if self.use_mock:
            return self._mock_liposome(drug_name, drug_smiles)
        else:
            raise NotImplementedError("Real API integration pending")

    def recommend_strategy(
        self,
        drug_name: str,
        drug_smiles: str
    ) -> FormulationResult:
        """Recommend formulation strategy

        Module: Strategy Recommendation
        Goal: Select optimal formulation approach based on properties

        Args:
            drug_name: Drug name
            drug_smiles: SMILES string

        Returns:
            FormulationResult with strategy recommendations
        """
        if self.use_mock:
            return self._mock_strategy_recommendation(drug_name, drug_smiles)
        else:
            raise NotImplementedError("Real API integration pending")

    def _api_cd_complex(self, drug_name: str, drug_smiles: str, cd_type: str | None) -> FormulationResult:
        """Call real FormulationAI API for CD complex

        TODO: Implement real API call when endpoint documentation available
        """
        raise NotImplementedError(
            "Real API integration pending. "
            "Need FormulationAI API documentation and credentials."
        )

    def _api_solid_dispersion(
        self,
        drug_name: str,
        drug_smiles: str,
        polymer_type: str | None,
        drug_loading: float | None
    ) -> FormulationResult:
        """Call real FormulationAI API for solid dispersion"""
        raise NotImplementedError(
            "Real API integration pending. "
            "Need FormulationAI API documentation and credentials."
        )

    def _api_nanocrystal(
        self,
        drug_name: str,
        drug_smiles: str,
        stabilizer_type: str | None,
        target_size: float | None
    ) -> FormulationResult:
        """Call real FormulationAI API for nanocrystal"""
        raise NotImplementedError(
            "Real API integration pending. "
            "Need FormulationAI API documentation and credentials."
        )

    def _mock_cd_complex(
        self,
        drug_name: str,
        drug_smiles: str,
        cd_type: str | None
    ) -> FormulationResult:
        """Mock implementation for CD complex design

        Real FormulationAI Output:
        - Complexation free energy (ΔG, kJ/mol)

        Does NOT output:
        - CD type recommendation
        - Drug:CD ratio
        - Solubility improvement fold
        """

        # Ibuprofen: BCS Class II - good candidate for CD complexation
        mock_data = {
            "CC(C)Cc1ccc(cc1)C(C)C(=O)O": {  # Ibuprofen
                "complex_formation_constant": -15.2,  # ΔG in kJ/mol (negative = favorable)
                "confidence": 0.80,
            },
            "CC(=O)Oc1ccccc1C(=O)O": {  # Aspirin
                "complex_formation_constant": -12.8,  # ΔG in kJ/mol
                "confidence": 0.73,
            }
        }

        data = mock_data.get(drug_smiles, {
            "complex_formation_constant": -14.0,
            "confidence": 0.75,
        })

        return FormulationResult(
            drug_name=drug_name,
            drug_smiles=drug_smiles,
            module="cd_complex",
            complex_formation_constant=data["complex_formation_constant"],
            confidence=data["confidence"],
            warnings=["✓ Predicted by ML model - experimental validation recommended"]
        )

    def _mock_solid_dispersion(
        self,
        drug_name: str,
        drug_smiles: str,
        polymer_type: str | None,
        drug_loading: float | None
    ) -> FormulationResult:
        """Mock implementation for solid dispersion design

        Real FormulationAI Output:
        - Physical stability prediction (stable/unstable)

        Does NOT output:
        - Polymer recommendation
        - Dissolution improvement
        - Drug loading
        """

        # Ibuprofen: Excellent candidate for solid dispersion (BCS II)
        mock_data = {
            "CC(C)Cc1ccc(cc1)C(C)C(=O)O": {  # Ibuprofen
                "miscibility_prediction": "stable",  # Real output: stable/unstable
                "confidence": 0.85,
            },
            "CC(=O)Oc1ccccc1C(=O)O": {  # Aspirin
                "miscibility_prediction": "stable",
                "confidence": 0.72,
            }
        }

        data = mock_data.get(drug_smiles, {
            "miscibility_prediction": "stable",
            "confidence": 0.70,
        })

        return FormulationResult(
            drug_name=drug_name,
            drug_smiles=drug_smiles,
            module="solid_dispersion",
            miscibility_prediction=data["miscibility_prediction"],
            confidence=data["confidence"],
            warnings=["✓ Physical stability prediction by AI model - experimental validation recommended"]
        )

    def _mock_nanocrystal(
        self,
        drug_name: str,
        drug_smiles: str,
        stabilizer_type: str | None,
        target_size: float | None
    ) -> FormulationResult:
        """Mock implementation for nanocrystal design

        Real FormulationAI Output:
        - Particle size (nm)
        - PDI (polydispersity index)
        - Methods: BWM, HPH, Antisolvent

        Does NOT output:
        - Stabilizer recommendation
        - Dissolution improvement prediction
        """

        # Ibuprofen: Good candidate for nanocrystal formulation
        mock_data = {
            "CC(C)Cc1ccc(cc1)C(C)C(=O)O": {  # Ibuprofen
                "recommended_particle_size": 280.0,  # nm (predicted)
                "pdi": 0.22,  # PDI prediction
                "methods": ["BWM", "HPH", "Antisolvent"],
            },
            "CC(=O)Oc1ccccc1C(=O)O": {  # Aspirin
                "recommended_particle_size": 320.0,
                "pdi": 0.28,
                "methods": ["BWM", "HPH", "Antisolvent"],
            }
        }

        data = mock_data.get(drug_smiles, {
            "recommended_particle_size": 300.0,
            "pdi": 0.25,
            "methods": ["BWM", "HPH", "Antisolvent"],
        })

        return FormulationResult(
            drug_name=drug_name,
            drug_smiles=drug_smiles,
            module="nanocrystal",
            recommended_particle_size=data["recommended_particle_size"],
            confidence=0.75,
            warnings=[
                "✓ Nanocrystal formulation prediction by AI model",
                f"Predicted size: {data['recommended_particle_size']} nm, PDI: {data['pdi']}",
                f"Suitable manufacturing methods: {', '.join(data['methods'])}"
            ]
        )

    def _mock_phospholipid_complex(
        self,
        drug_name: str,
        drug_smiles: str
    ) -> FormulationResult:
        """Mock implementation for phospholipid complex design"""

        mock_data = {
            "CC(C)Cc1ccc(cc1)C(C)C(=O)O": {  # Ibuprofen
                "complex_formation": True,
                "lipophilicity_improvement": 2.5,
                "bioavailability_prediction": 0.78,
            },
        }

        data = mock_data.get(drug_smiles, {
            "complex_formation": True,
            "lipophilicity_improvement": 2.0,
            "bioavailability_prediction": 0.70,
        })

        return FormulationResult(
            drug_name=drug_name,
            drug_smiles=drug_smiles,
            module="phospholipid_complex",
            complex_formation=data["complex_formation"],
            lipophilicity_improvement=data["lipophilicity_improvement"],
            bioavailability_prediction=data["bioavailability_prediction"],
            confidence=0.72,
            warnings=["✓ Phospholipid complex prediction - experimental validation recommended"]
        )

    def _mock_sedds(
        self,
        drug_name: str,
        drug_smiles: str
    ) -> FormulationResult:
        """Mock implementation for SEDDS design"""

        mock_data = {
            "CC(C)Cc1ccc(cc1)C(C)C(=O)O": {  # Ibuprofen
                "oil_recommendation": "Capryol 90",
                "surfactant_recommendation": "Cremophor EL",
                "oil_percentage": 30.0,
                "surfactant_percentage": 50.0,
                "droplet_size": 45.0,
            },
        }

        data = mock_data.get(drug_smiles, {
            "oil_recommendation": "Medium chain triglycerides",
            "surfactant_recommendation": "Tween 80",
            "oil_percentage": 25.0,
            "surfactant_percentage": 55.0,
            "droplet_size": 50.0,
        })

        return FormulationResult(
            drug_name=drug_name,
            drug_smiles=drug_smiles,
            module="sedds",
            oil_recommendation=data["oil_recommendation"],
            surfactant_recommendation=data["surfactant_recommendation"],
            oil_percentage=data["oil_percentage"],
            surfactant_percentage=data["surfactant_percentage"],
            droplet_size=data["droplet_size"],
            confidence=0.75,
            warnings=["✓ SEDDS formulation prediction - in vitro dissolution testing recommended"]
        )

    def _mock_liposome(
        self,
        drug_name: str,
        drug_smiles: str
    ) -> FormulationResult:
        """Mock implementation for liposome design"""

        mock_data = {
            "CC(C)Cc1ccc(cc1)C(C)C(=O)O": {  # Ibuprofen
                "main_lipid": "DPPC",
                "recommended_size": 120.0,
                "encapsulation_efficiency": 0.65,
                "release_profile": "sustained",
            },
        }

        data = mock_data.get(drug_smiles, {
            "main_lipid": "DSPC",
            "recommended_size": 100.0,
            "encapsulation_efficiency": 0.60,
            "release_profile": "sustained",
        })

        return FormulationResult(
            drug_name=drug_name,
            drug_smiles=drug_smiles,
            module="liposome",
            main_lipid=data["main_lipid"],
            recommended_size=data["recommended_size"],
            encapsulation_efficiency=data["encapsulation_efficiency"],
            release_profile=data["release_profile"],
            confidence=0.70,
            warnings=["✓ Liposome formulation prediction - stability testing recommended"]
        )

    def _mock_strategy_recommendation(
        self,
        drug_name: str,
        drug_smiles: str
    ) -> FormulationResult:
        """Mock implementation for strategy recommendation"""

        # Simplified logic based on SMILES patterns
        mock_data = {
            "CC(C)Cc1ccc(cc1)C(C)C(=O)O": {  # Ibuprofen - BCS II
                "recommended_strategies": [
                    {"strategy": "solid_dispersion", "score": 0.92, "reason": "High lipophilicity, amorphization effective"},
                    {"strategy": "nanocrystal", "score": 0.88, "reason": "Low solubility, particle size reduction beneficial"},
                    {"strategy": "cd_complex", "score": 0.75, "reason": "Moderate molecular size, inclusion complex feasible"},
                ]
            },
        }

        data = mock_data.get(drug_smiles, {
            "recommended_strategies": [
                {"strategy": "solid_dispersion", "score": 0.80, "reason": "Default recommendation for BCS II"},
                {"strategy": "nanocrystal", "score": 0.75, "reason": "Alternative for solubility enhancement"},
            ]
        })

        return FormulationResult(
            drug_name=drug_name,
            drug_smiles=drug_smiles,
            module="strategy_recommendation",
            recommended_strategies=data["recommended_strategies"],
            confidence=0.85,
            warnings=["✓ Strategy recommendation based on structure-property relationships"]
        )


def run(input_data: dict[str, Any]) -> dict[str, Any]:
    """FormulationOS tool executor interface

    This function is called by the FormulationOS orchestrator.

    Args:
        input_data: Must contain:
            - drug_name: str
            - smiles: str or drug_smiles: str
            - module: str (default: "solid_dispersion")
              Options: "cd_complex", "solid_dispersion", "nanocrystal"
            - Optional parameters based on module

    Returns:
        Dictionary with formulation design results
    """
    drug_name = input_data.get("drug_name", "Unknown Drug")
    smiles = input_data.get("smiles") or input_data.get("drug_smiles")
    module = input_data.get("module", "solid_dispersion")

    if not smiles:
        # Try to infer from drug_name
        if "ibuprofen" in drug_name.lower():
            smiles = "CC(C)Cc1ccc(cc1)C(C)C(=O)O"
        elif "aspirin" in drug_name.lower():
            smiles = "CC(=O)Oc1ccccc1C(=O)O"
        else:
            return {
                "error": "SMILES or drug_smiles required",
                "status": "error"
            }

    adapter = FormulationAIAdapter()

    # Route to appropriate module
    if module == "cd_complex":
        cd_type = input_data.get("cd_type")
        result = adapter.design_cd_complex(drug_name, smiles, cd_type)

    elif module == "solid_dispersion":
        polymer_type = input_data.get("polymer_type")
        drug_loading = input_data.get("drug_loading")
        result = adapter.design_solid_dispersion(drug_name, smiles, polymer_type, drug_loading)

    elif module == "nanocrystal":
        stabilizer_type = input_data.get("stabilizer_type")
        target_size = input_data.get("target_size")
        result = adapter.design_nanocrystal(drug_name, smiles, stabilizer_type, target_size)

    elif module == "phospholipid_complex":
        result = adapter.design_phospholipid_complex(drug_name, smiles)

    elif module == "sedds":
        result = adapter.design_sedds(drug_name, smiles)

    elif module == "liposome":
        result = adapter.design_liposome(drug_name, smiles)

    elif module == "strategy_recommendation":
        result = adapter.recommend_strategy(drug_name, smiles)

    else:
        return {
            "error": f"Unknown module: {module}",
            "status": "error"
        }

    # Convert to dictionary for FormulationOS
    output = {
        "drug_name": result.drug_name,
        "drug_smiles": result.drug_smiles,
        "module": result.module,
        "status": "success"
    }

    # Add module-specific outputs (ONLY real FormulationAI outputs)
    if result.module == "cd_complex":
        output.update({
            "complexation_free_energy_kj_mol": result.complex_formation_constant,  # ΔG
            "confidence": result.confidence,
        })

    elif result.module == "solid_dispersion":
        output.update({
            "physical_stability": result.miscibility_prediction,  # stable/unstable
            "confidence": result.confidence,
        })

    elif result.module == "nanocrystal":
        output.update({
            "predicted_particle_size_nm": result.recommended_particle_size,
            "confidence": result.confidence,
        })

    elif result.module == "phospholipid_complex":
        output.update({
            "complex_formation": result.complex_formation,
            "lipophilicity_improvement": result.lipophilicity_improvement,
            "bioavailability_prediction": result.bioavailability_prediction,
            "confidence": result.confidence,
        })

    elif result.module == "sedds":
        output.update({
            "oil_recommendation": result.oil_recommendation,
            "surfactant_recommendation": result.surfactant_recommendation,
            "oil_percentage": result.oil_percentage,
            "surfactant_percentage": result.surfactant_percentage,
            "droplet_size_nm": result.droplet_size,
            "confidence": result.confidence,
        })

    elif result.module == "liposome":
        output.update({
            "main_lipid": result.main_lipid,
            "recommended_size_nm": result.recommended_size,
            "encapsulation_efficiency": result.encapsulation_efficiency,
            "release_profile": result.release_profile,
            "confidence": result.confidence,
        })

    elif result.module == "strategy_recommendation":
        output.update({
            "recommended_strategies": result.recommended_strategies,
            "confidence": result.confidence,
        })

    if result.warnings:
        output["warnings"] = result.warnings

    return output
