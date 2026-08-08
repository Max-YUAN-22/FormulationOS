"""Feature selector for different PreFormulationAI models.

Each model was trained on a different subset of features.
This module ensures we provide the correct features to each model.
"""

from __future__ import annotations

import pandas as pd

# Feature names for each model (excluding 'target' column)
# These are extracted from the training data CSV headers

DRUGLIKENESS_FEATURES = [
    'Density', 'MP', 'Tg', 'logP', 'logD', 'A_pKa', 'B_pKa', 'logS', 'logPapp',
    'Kinetic_Solubility_Pred', 'Soubility_ethanol', 'Soubility_methanol',
    'Soubility_isopropanol', 'Soubility_DMF', 'Max_organic_solubility',
    'Min_organic_solubility', 'MaxAbsEStateIndex', 'MinAbsEStateIndex',
    'MinEStateIndex', 'qed', 'SPS', 'MolWt', 'NumRadicalElectrons',
    'MaxPartialCharge', 'MinPartialCharge', 'BalabanJ', 'TPSA', 'FractionCSP3',
    'NumAliphaticCarbocycles', 'NumAliphaticHeterocycles', 'NumAliphaticRings',
    'NumAmideBonds', 'NumAromaticCarbocycles', 'NumAromaticHeterocycles',
    'NumAromaticRings', 'NumAtomStereoCenters', 'NumBridgeheadAtoms',
    'NumHAcceptors', 'NumHDonors', 'NumHeteroatoms', 'NumHeterocycles',
    'NumRotatableBonds', 'NumSaturatedHeterocycles', 'NumSaturatedRings',
    'NumSpiroAtoms', 'Phi', 'RingCount', 'fr_Al_COO', 'fr_Al_OH', 'fr_ArN',
    'fr_Ar_COO', 'fr_Ar_NH', 'fr_Ar_OH', 'fr_C_S', 'fr_NH0', 'fr_NH1', 'fr_NH2',
    'fr_N_O', 'fr_amidine', 'fr_aniline', 'fr_azide', 'fr_bicyclic', 'fr_halogen',
    'fr_ketone', 'fr_lactam', 'fr_lactone', 'fr_nitro', 'fr_nitro_arom',
    'fr_phos_acid', 'fr_quatN', 'fr_sulfide', 'fr_sulfonamd', 'fr_sulfone',
    'fr_unbrch_alkane'
]  # Total: 74 features

ORAL_FEATURES = [
    'Density', 'MP', 'Tg', 'logP', 'logD', 'A_pKa', 'B_pKa', 'logS', 'logPapp',
    'Kinetic_Solubility_Pred', 'Soubility_ethanol', 'Soubility_methanol',
    'Soubility_DMF', 'Max_organic_solubility', 'Min_organic_solubility',
    'MaxAbsEStateIndex', 'MinAbsEStateIndex', 'MinEStateIndex', 'qed', 'SPS',
    'MolWt', 'MaxPartialCharge', 'MinPartialCharge', 'BalabanJ', 'TPSA',
    'FractionCSP3', 'NumAliphaticCarbocycles', 'NumAliphaticHeterocycles',
    'NumAliphaticRings', 'NumAmideBonds', 'NumAromaticCarbocycles',
    'NumAromaticHeterocycles', 'NumAromaticRings', 'NumAtomStereoCenters',
    'NumBridgeheadAtoms', 'NumHAcceptors', 'NumHeterocycles', 'NumRotatableBonds',
    'NumSaturatedHeterocycles', 'NumSaturatedRings', 'NumSpiroAtoms',
    'NumUnspecifiedAtomStereoCenters', 'RingCount', 'MolLogP', 'fr_Al_COO',
    'fr_Al_OH', 'fr_ArN', 'fr_Ar_COO', 'fr_Ar_NH', 'fr_Ar_OH', 'fr_C_S', 'fr_NH0',
    'fr_NH1', 'fr_NH2', 'fr_N_O', 'fr_amidine', 'fr_aniline', 'fr_azide',
    'fr_bicyclic', 'fr_halogen', 'fr_ketone', 'fr_lactam', 'fr_lactone', 'fr_nitro',
    'fr_nitro_arom', 'fr_phos_acid', 'fr_quatN', 'fr_sulfide', 'fr_sulfonamd',
    'fr_sulfone', 'fr_unbrch_alkane'
]  # Total: 71 features

INJECTABLE_FEATURES = [
    'Density', 'MP', 'Tg', 'logP', 'logD', 'A_pKa', 'B_pKa', 'logS', 'logPapp',
    'Kinetic_Solubility_Pred', 'Soubility_ethanol', 'Soubility_methanol',
    'Max_organic_solubility', 'Min_organic_solubility', 'MaxAbsEStateIndex',
    'MinAbsEStateIndex', 'MinEStateIndex', 'qed', 'SPS', 'MolWt', 'NumRadicalElectrons',
    'MaxPartialCharge', 'MinPartialCharge', 'MinAbsPartialCharge', 'BalabanJ',
    'FractionCSP3', 'NumAliphaticCarbocycles', 'NumAliphaticHeterocycles',
    'NumAmideBonds', 'NumAromaticCarbocycles', 'NumAromaticHeterocycles',
    'NumAromaticRings', 'NumAtomStereoCenters', 'NumBridgeheadAtoms', 'NumHDonors',
    'NumSaturatedCarbocycles', 'NumSaturatedRings', 'NumSpiroAtoms',
    'NumUnspecifiedAtomStereoCenters', 'RingCount', 'MolLogP', 'fr_Al_COO',
    'fr_Al_OH', 'fr_ArN', 'fr_Ar_COO', 'fr_Ar_NH', 'fr_Ar_OH', 'fr_C_S', 'fr_NH2',
    'fr_N_O', 'fr_amidine', 'fr_aniline', 'fr_azide', 'fr_bicyclic', 'fr_halogen',
    'fr_ketone', 'fr_lactam', 'fr_lactone', 'fr_nitro', 'fr_phos_acid',
    'fr_phos_ester', 'fr_quatN', 'fr_sulfide', 'fr_sulfonamd', 'fr_sulfone',
    'fr_unbrch_alkane'
]  # Total: 66 features


def select_features_for_model(features_df: pd.DataFrame, model_type: str) -> pd.DataFrame:
    """Select the correct feature subset for a specific model.

    Args:
        features_df: DataFrame with all available features (74 columns)
        model_type: One of 'druglikeness', 'oral', 'injectable'

    Returns:
        DataFrame with only the features needed for the specified model
    """
    if model_type == 'druglikeness':
        feature_list = DRUGLIKENESS_FEATURES
    elif model_type == 'oral':
        feature_list = ORAL_FEATURES
    elif model_type == 'injectable':
        feature_list = INJECTABLE_FEATURES
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    # Select only the features present in the input DataFrame
    available_features = [f for f in feature_list if f in features_df.columns]

    # Check if we have enough features
    if len(available_features) < len(feature_list):
        missing = set(feature_list) - set(available_features)
        print(f"Warning: Missing {len(missing)} features for {model_type}: {missing}")

    return features_df[available_features]


def add_missing_features(features_df: pd.DataFrame, model_type: str) -> pd.DataFrame:
    """Add missing features with default values if they don't exist.

    Args:
        features_df: DataFrame with current features
        model_type: One of 'druglikeness', 'oral', 'injectable'

    Returns:
        DataFrame with all required features (missing ones filled with defaults)
    """
    if model_type == 'druglikeness':
        required_features = DRUGLIKENESS_FEATURES
    elif model_type == 'oral':
        required_features = ORAL_FEATURES
    elif model_type == 'injectable':
        required_features = INJECTABLE_FEATURES
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    # Add missing features with default values
    for feature in required_features:
        if feature not in features_df.columns:
            # Add with default value based on feature type
            if feature.startswith('fr_') or feature.startswith('Num'):
                features_df[feature] = 0  # Counts default to 0
            elif feature in ['MolLogP', 'logP']:
                features_df[feature] = 2.0  # Neutral lipophilicity
            elif feature == 'NumUnspecifiedAtomStereoCenters':
                features_df[feature] = 0
            else:
                features_df[feature] = 0.0

    # Return features in the correct order
    return features_df[required_features]
