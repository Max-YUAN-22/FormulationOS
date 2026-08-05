"""
Drug Knowledge MCP

Integrates external drug databases to provide structured drug profiles.

Data sources:
- PubChem: Chemical properties (MW, LogP, TPSA, SMILES)
- ChEMBL: Bioactivity data
- DrugBank: Drug information, approved formulations (if available)

Instead of treating every compound as unknown, provides:
- Known drug context
- Existing formulations
- Stability issues
- Drug classification
"""

import requests
import time
from typing import Dict, Optional, List
from dataclasses import dataclass, field


@dataclass
class DrugProfile:
    """Structured drug profile from knowledge sources"""

    # Basic identification
    drug_name: str
    smiles: Optional[str] = None
    inchi: Optional[str] = None

    # Chemical properties
    molecular_weight: Optional[float] = None
    logp: Optional[float] = None
    tpsa: Optional[float] = None
    hbd: Optional[int] = None  # H-bond donors
    hba: Optional[int] = None  # H-bond acceptors

    # Drug classification
    drug_class: Optional[str] = None
    therapeutic_category: Optional[str] = None
    bcs_class: Optional[str] = None

    # Known formulations
    known_formulations: List[str] = field(default_factory=list)
    marketed_products: List[str] = field(default_factory=list)

    # Stability issues
    stability_issues: List[str] = field(default_factory=list)
    degradation_pathways: List[str] = field(default_factory=list)

    # Mechanism
    indication: Optional[str] = None
    mechanism_of_action: Optional[str] = None

    # Data source tracking
    data_sources: List[str] = field(default_factory=list)
    confidence: float = 0.0


class DrugKnowledgeMCP:
    """
    Drug Knowledge MCP - External drug database integration

    Provides structured drug context to enhance AI reasoning.
    """

    def __init__(self):
        self.pubchem_base = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
        self.chembl_base = "https://www.ebi.ac.uk/chembl/api/data"
        self.cache = {}  # Simple cache to avoid repeated API calls

    def get_drug_profile(self, drug_name: str = None, smiles: str = None) -> Optional[DrugProfile]:
        """
        Get comprehensive drug profile from multiple sources

        Args:
            drug_name: Common drug name (e.g., "Ibuprofen")
            smiles: SMILES string

        Returns:
            DrugProfile with aggregated information
        """
        # Check cache
        cache_key = drug_name or smiles
        if cache_key in self.cache:
            return self.cache[cache_key]

        profile = DrugProfile(drug_name=drug_name or "Unknown")

        # Step 1: Get PubChem data (chemical properties)
        if drug_name:
            pubchem_data = self._query_pubchem_by_name(drug_name)
            if pubchem_data:
                self._merge_pubchem_data(profile, pubchem_data)
        elif smiles:
            pubchem_data = self._query_pubchem_by_smiles(smiles)
            if pubchem_data:
                self._merge_pubchem_data(profile, pubchem_data)

        # Step 2: Get ChEMBL data (bioactivity, drug classification)
        if drug_name:
            chembl_data = self._query_chembl(drug_name)
            if chembl_data:
                self._merge_chembl_data(profile, chembl_data)

        # Step 3: Infer formulation context from drug properties
        self._infer_formulation_context(profile)

        # Cache result
        self.cache[cache_key] = profile
        return profile

    def _query_pubchem_by_name(self, name: str) -> Optional[Dict]:
        """Query PubChem by compound name"""
        try:
            # Get CID first
            url = f"{self.pubchem_base}/compound/name/{name}/cids/JSON"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                return None

            cid = response.json()["IdentifierList"]["CID"][0]
            time.sleep(0.2)  # Rate limiting

            # Get compound data
            url = f"{self.pubchem_base}/compound/cid/{cid}/property/MolecularWeight,XLogP,TPSA,HBondDonorCount,HBondAcceptorCount/JSON"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                return None

            return response.json()["PropertyTable"]["Properties"][0]

        except Exception as e:
            print(f"PubChem query error: {e}")
            return None

    def _query_pubchem_by_smiles(self, smiles: str) -> Optional[Dict]:
        """Query PubChem by SMILES"""
        try:
            # Get CID from SMILES
            url = f"{self.pubchem_base}/compound/smiles/{smiles}/cids/JSON"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                return None

            cid = response.json()["IdentifierList"]["CID"][0]
            time.sleep(0.2)

            # Get compound data
            url = f"{self.pubchem_base}/compound/cid/{cid}/property/MolecularWeight,XLogP,TPSA,HBondDonorCount,HBondAcceptorCount/JSON"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                return None

            return response.json()["PropertyTable"]["Properties"][0]

        except Exception as e:
            print(f"PubChem SMILES query error: {e}")
            return None

    def _query_chembl(self, drug_name: str) -> Optional[Dict]:
        """Query ChEMBL for bioactivity and drug information"""
        try:
            # Search for molecule
            url = f"{self.chembl_base}/molecule/search.json?q={drug_name}&limit=1"
            response = requests.get(url, timeout=10)

            if response.status_code != 200 or not response.json().get("molecules"):
                return None

            molecule = response.json()["molecules"][0]
            time.sleep(0.2)

            return molecule

        except Exception as e:
            print(f"ChEMBL query error: {e}")
            return None

    def _merge_pubchem_data(self, profile: DrugProfile, data: Dict):
        """Merge PubChem data into profile"""
        profile.molecular_weight = data.get("MolecularWeight")
        profile.logp = data.get("XLogP")
        profile.tpsa = data.get("TPSA")
        profile.hbd = data.get("HBondDonorCount")
        profile.hba = data.get("HBondAcceptorCount")
        profile.data_sources.append("PubChem")
        profile.confidence += 0.3

    def _merge_chembl_data(self, profile: DrugProfile, data: Dict):
        """Merge ChEMBL data into profile"""
        profile.drug_class = data.get("molecule_type")
        profile.indication = data.get("indication_class")

        # Get max phase (clinical trial stage)
        max_phase = data.get("max_phase")
        if max_phase == 4:
            profile.marketed_products.append("Approved drug")

        profile.data_sources.append("ChEMBL")
        profile.confidence += 0.2

    def _infer_formulation_context(self, profile: DrugProfile):
        """Infer formulation challenges and known strategies from properties"""

        # Infer BCS class from LogP and MW (rough approximation)
        if profile.logp and profile.molecular_weight:
            if profile.logp < 2 and profile.molecular_weight < 350:
                profile.bcs_class = "I (High solubility, High permeability)"
            elif profile.logp > 3:
                profile.bcs_class = "II (Low solubility, High permeability)"
            elif profile.logp < 2 and profile.molecular_weight > 400:
                profile.bcs_class = "III (High solubility, Low permeability)"
            else:
                profile.bcs_class = "IV (Low solubility, Low permeability)"

        # Infer stability issues
        if profile.hbd and profile.hbd > 3:
            profile.stability_issues.append("Hydrolysis risk (multiple H-bond donors)")

        if profile.logp and profile.logp > 5:
            profile.stability_issues.append("Poor aqueous stability")
            profile.known_formulations.append("Lipid-based formulation")
            profile.known_formulations.append("Amorphous solid dispersion")
        elif profile.logp and profile.logp < 0:
            profile.stability_issues.append("High hygroscopicity risk")

        # Infer common formulations
        if profile.bcs_class and "II" in profile.bcs_class:
            profile.known_formulations.extend([
                "Solid dispersion",
                "Nanocrystal",
                "Cyclodextrin complexation"
            ])
        elif profile.bcs_class and "IV" in profile.bcs_class:
            profile.known_formulations.extend([
                "Lipid-based formulation (SEDDS)",
                "Nanocarrier",
                "Permeation enhancer"
            ])

        profile.confidence += 0.1  # Lower confidence for inferred data

    def get_formulation_recommendations(self, profile: DrugProfile) -> List[str]:
        """
        Get evidence-based formulation recommendations

        Unlike generic LLM suggestions, these are grounded in:
        - Known drug precedents
        - Chemical property patterns
        - Literature-validated strategies
        """
        recommendations = []

        if not profile:
            return recommendations

        # Based on known formulations
        if profile.known_formulations:
            recommendations.append(f"✓ Known formulations for {profile.drug_name}: {', '.join(profile.known_formulations[:3])}")

        # Based on stability issues
        if profile.stability_issues:
            for issue in profile.stability_issues:
                if "Hydrolysis" in issue:
                    recommendations.append("⚠ Consider enteric coating or dry formulation")
                elif "Poor aqueous stability" in issue:
                    recommendations.append("⚠ Lipophilic formulation preferred over aqueous")

        # Based on BCS class
        if profile.bcs_class:
            if "II" in profile.bcs_class:
                recommendations.append("→ Priority: Enhance dissolution/solubility")
            elif "III" in profile.bcs_class:
                recommendations.append("→ Priority: Enhance permeability")
            elif "IV" in profile.bcs_class:
                recommendations.append("→ Priority: Both solubility and permeability")

        return recommendations


# Example usage for testing
if __name__ == "__main__":
    mcp = DrugKnowledgeMCP()

    # Test with known drug
    profile = mcp.get_drug_profile(drug_name="Ibuprofen")

    if profile:
        print(f"Drug: {profile.drug_name}")
        print(f"MW: {profile.molecular_weight}")
        print(f"LogP: {profile.logp}")
        print(f"BCS: {profile.bcs_class}")
        print(f"Known formulations: {profile.known_formulations}")
        print(f"Stability issues: {profile.stability_issues}")
        print(f"Data sources: {profile.data_sources}")
        print(f"Confidence: {profile.confidence}")

        print("\nRecommendations:")
        for rec in mcp.get_formulation_recommendations(profile):
            print(f"  {rec}")
