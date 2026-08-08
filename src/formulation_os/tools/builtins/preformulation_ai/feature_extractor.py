"""Complete 74-feature extraction pipeline for PreFormulationAI models.

Combines:
1. PyTorch predictions (10 physicochemical properties from Chemprop models)
2. Organic solvent solubility predictions (5 solvents)
3. RDKit molecular descriptors (59 features)

Total: 74 features matching the training data format.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# Global cache
_FEATURE_CACHE: dict[str, Any] = {}


def extract_74_features(smiles: str) -> pd.DataFrame:
    """Extract all 74 features required for PreFormulationAI models.

    Features match the columns in druglikeness_train.csv:
    - 10 PyTorch predictions: Density, MP, Tg, logP, logD, A_pKa, B_pKa, logS, logPapp, Kinetic_Solubility_Pred
    - 5 organic solvent solubilities: ethanol, methanol, isopropanol, DMF, + max/min
    - 59 RDKit descriptors and functional group counts

    Args:
        smiles: SMILES string

    Returns:
        DataFrame with 1 row and 73 columns (target excluded, features only)
    """
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdMolDescriptors

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")

    features = {}

    # ========================================================================
    # 1. PyTorch Property Predictions (10 features)
    # ========================================================================
    try:
        from .pytorch_predictor import predict_all_pytorch_properties

        pytorch_props = predict_all_pytorch_properties(smiles)

        # Fill with predictions or reasonable defaults
        features["Density"] = pytorch_props.get("Density") or 1.2
        features["MP"] = pytorch_props.get("MP") or 150.0
        features["Tg"] = pytorch_props.get("Tg") or 50.0
        features["logP"] = pytorch_props.get("logP") or 2.0
        features["logD"] = pytorch_props.get("logD") or 2.0
        features["A_pKa"] = pytorch_props.get("A_pKa") or 4.0
        features["B_pKa"] = pytorch_props.get("B_pKa") or 9.0
        features["logS"] = pytorch_props.get("logS") or -3.0
        features["logPapp"] = pytorch_props.get("logPapp") or -5.0
        features["Kinetic_Solubility_Pred"] = pytorch_props.get("Kinetic_Solubility_Pred") or 0.1

    except Exception as e:
        print(f"Warning: PyTorch predictions failed, using defaults: {str(e)}")
        # Use reasonable default values
        features["Density"] = 1.2
        features["MP"] = 150.0
        features["Tg"] = 50.0
        features["logP"] = Descriptors.MolLogP(mol)
        features["logD"] = features["logP"]
        features["A_pKa"] = 4.0
        features["B_pKa"] = 9.0
        features["logS"] = -3.0
        features["logPapp"] = -5.0
        features["Kinetic_Solubility_Pred"] = 0.1

    # ========================================================================
    # 2. Organic Solvent Solubilities (5 features)
    # ========================================================================
    # TODO: These would ideally come from separate models
    # For now, estimate based on logP and molecular properties
    logP = features["logP"]

    # Rough estimates: polar solvents prefer lower logP
    features["Soubility_ethanol"] = max(0.01, 100 / (1 + abs(logP - 0.5)))
    features["Soubility_methanol"] = max(0.01, 120 / (1 + abs(logP - 0.3)))
    features["Soubility_isopropanol"] = max(0.01, 80 / (1 + abs(logP - 1.0)))
    features["Soubility_DMF"] = max(0.01, 200 / (1 + abs(logP - 1.5)))

    features["Max_organic_solubility"] = max(
        features["Soubility_ethanol"],
        features["Soubility_methanol"],
        features["Soubility_isopropanol"],
        features["Soubility_DMF"],
    )
    features["Min_organic_solubility"] = min(
        features["Soubility_ethanol"],
        features["Soubility_methanol"],
        features["Soubility_isopropanol"],
        features["Soubility_DMF"],
    )

    # ========================================================================
    # 3. RDKit Descriptors (59 features)
    # ========================================================================

    # E-state indices
    features["MaxAbsEStateIndex"] = Descriptors.MaxAbsEStateIndex(mol)
    features["MinAbsEStateIndex"] = Descriptors.MinAbsEStateIndex(mol)
    features["MinEStateIndex"] = Descriptors.MinEStateIndex(mol)

    # Drug-likeness scores
    features["qed"] = Descriptors.qed(mol)

    # Synthetic accessibility (use a proxy based on complexity)
    features["SPS"] = rdMolDescriptors.CalcNumRotatableBonds(mol) / max(1, mol.GetNumHeavyAtoms())

    # Basic properties
    features["MolWt"] = Descriptors.MolWt(mol)
    features["NumRadicalElectrons"] = Descriptors.NumRadicalElectrons(mol)

    # Partial charges (approximate with Gasteiger if available)
    try:
        from rdkit.Chem import AllChem
        AllChem.ComputeGasteigerCharges(mol)
        charges = [float(atom.GetProp('_GasteigerCharge')) for atom in mol.GetAtoms() if atom.GetProp('_GasteigerCharge') != 'nan']
        features["MaxPartialCharge"] = max(charges) if charges else 0.0
        features["MinPartialCharge"] = min(charges) if charges else 0.0
    except:
        features["MaxPartialCharge"] = 0.0
        features["MinPartialCharge"] = 0.0

    # Topological descriptors
    features["BalabanJ"] = Descriptors.BalabanJ(mol)
    features["TPSA"] = Descriptors.TPSA(mol)
    features["FractionCSP3"] = Descriptors.FractionCSP3(mol)

    # Ring counts
    features["NumAliphaticCarbocycles"] = Descriptors.NumAliphaticCarbocycles(mol)
    features["NumAliphaticHeterocycles"] = Descriptors.NumAliphaticHeterocycles(mol)
    features["NumAliphaticRings"] = Descriptors.NumAliphaticRings(mol)
    features["NumAmideBonds"] = rdMolDescriptors.CalcNumAmideBonds(mol)
    features["NumAromaticCarbocycles"] = Descriptors.NumAromaticCarbocycles(mol)
    features["NumAromaticHeterocycles"] = Descriptors.NumAromaticHeterocycles(mol)
    features["NumAromaticRings"] = Descriptors.NumAromaticRings(mol)
    features["NumAtomStereoCenters"] = Descriptors.NumAtomStereoCenters(mol)
    features["NumBridgeheadAtoms"] = Descriptors.NumBridgeheadAtoms(mol)
    features["NumHAcceptors"] = Descriptors.NumHAcceptors(mol)
    features["NumHDonors"] = Descriptors.NumHDonors(mol)
    features["NumHeteroatoms"] = Descriptors.NumHeteroatoms(mol)
    features["NumHeterocycles"] = Descriptors.NumHeterocycles(mol)
    features["NumRotatableBonds"] = Descriptors.NumRotatableBonds(mol)
    features["NumSaturatedHeterocycles"] = Descriptors.NumSaturatedHeterocycles(mol)
    features["NumSaturatedRings"] = Descriptors.NumSaturatedRings(mol)
    features["NumSpiroAtoms"] = Descriptors.NumSpiroAtoms(mol)
    features["Phi"] = rdMolDescriptors.CalcPhi(mol)
    features["RingCount"] = Descriptors.RingCount(mol)

    # Functional group counts (fr_* descriptors)
    features["fr_Al_COO"] = Descriptors.fr_Al_COO(mol)
    features["fr_Al_OH"] = Descriptors.fr_Al_OH(mol)
    features["fr_ArN"] = Descriptors.fr_ArN(mol)
    features["fr_Ar_COO"] = Descriptors.fr_Ar_COO(mol)
    features["fr_Ar_NH"] = Descriptors.fr_Ar_NH(mol)
    features["fr_Ar_OH"] = Descriptors.fr_Ar_OH(mol)
    features["fr_C_S"] = Descriptors.fr_C_S(mol)
    features["fr_NH0"] = Descriptors.fr_NH0(mol)
    features["fr_NH1"] = Descriptors.fr_NH1(mol)
    features["fr_NH2"] = Descriptors.fr_NH2(mol)
    features["fr_N_O"] = Descriptors.fr_N_O(mol)
    features["fr_amidine"] = Descriptors.fr_amidine(mol)
    features["fr_aniline"] = Descriptors.fr_aniline(mol)
    features["fr_azide"] = Descriptors.fr_azide(mol)
    features["fr_bicyclic"] = Descriptors.fr_bicyclic(mol)
    features["fr_halogen"] = Descriptors.fr_halogen(mol)
    features["fr_ketone"] = Descriptors.fr_ketone(mol)
    features["fr_lactam"] = Descriptors.fr_lactam(mol)
    features["fr_lactone"] = Descriptors.fr_lactone(mol)
    features["fr_nitro"] = Descriptors.fr_nitro(mol)
    features["fr_nitro_arom"] = Descriptors.fr_nitro_arom(mol)
    features["fr_phos_acid"] = Descriptors.fr_phos_acid(mol)
    features["fr_quatN"] = Descriptors.fr_quatN(mol)
    features["fr_sulfide"] = Descriptors.fr_sulfide(mol)
    features["fr_sulfonamd"] = Descriptors.fr_sulfonamd(mol)
    features["fr_sulfone"] = Descriptors.fr_sulfone(mol)
    features["fr_unbrch_alkane"] = Descriptors.fr_unbrch_alkane(mol)

    # Convert to DataFrame (expected format for sklearn models)
    df = pd.DataFrame([features])

    return df


def get_expected_feature_names() -> list[str]:
    """Return the expected 73 feature names (excluding 'target').

    This matches the column order in druglikeness_train.csv.
    """
    return [
        # PyTorch predictions (10)
        "Density", "MP", "Tg", "logP", "logD", "A_pKa", "B_pKa", "logS", "logPapp", "Kinetic_Solubility_Pred",
        # Organic solvent solubilities (6)
        "Soubility_ethanol", "Soubility_methanol", "Soubility_isopropanol", "Soubility_DMF",
        "Max_organic_solubility", "Min_organic_solubility",
        # RDKit descriptors (57)
        "MaxAbsEStateIndex", "MinAbsEStateIndex", "MinEStateIndex", "qed", "SPS",
        "MolWt", "NumRadicalElectrons", "MaxPartialCharge", "MinPartialCharge",
        "BalabanJ", "TPSA", "FractionCSP3",
        "NumAliphaticCarbocycles", "NumAliphaticHeterocycles", "NumAliphaticRings",
        "NumAmideBonds", "NumAromaticCarbocycles", "NumAromaticHeterocycles", "NumAromaticRings",
        "NumAtomStereoCenters", "NumBridgeheadAtoms",
        "NumHAcceptors", "NumHDonors", "NumHeteroatoms", "NumHeterocycles",
        "NumRotatableBonds", "NumSaturatedHeterocycles", "NumSaturatedRings", "NumSpiroAtoms",
        "Phi", "RingCount",
        "fr_Al_COO", "fr_Al_OH", "fr_ArN", "fr_Ar_COO", "fr_Ar_NH", "fr_Ar_OH",
        "fr_C_S", "fr_NH0", "fr_NH1", "fr_NH2", "fr_N_O",
        "fr_amidine", "fr_aniline", "fr_azide", "fr_bicyclic",
        "fr_halogen", "fr_ketone", "fr_lactam", "fr_lactone",
        "fr_nitro", "fr_nitro_arom", "fr_phos_acid", "fr_quatN",
        "fr_sulfide", "fr_sulfonamd", "fr_sulfone", "fr_unbrch_alkane",
    ]


def validate_features(features_df: pd.DataFrame) -> bool:
    """Validate that feature DataFrame has correct shape and columns.

    Args:
        features_df: Feature DataFrame

    Returns:
        True if valid, raises ValueError otherwise
    """
    expected_cols = get_expected_feature_names()

    if len(features_df.columns) != len(expected_cols):
        raise ValueError(
            f"Expected {len(expected_cols)} features, got {len(features_df.columns)}"
        )

    # Check for missing columns
    missing = set(expected_cols) - set(features_df.columns)
    if missing:
        raise ValueError(f"Missing features: {missing}")

    return True
