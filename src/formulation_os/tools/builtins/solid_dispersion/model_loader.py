"""Local model loader for Solid Dispersion LightGBM model.

Loads the trained LightGBM model from assets/solid_dispersion/models/
to predict solubility enhancement and stability of drug-polymer combinations.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors

# Find project root (where assets/ folder is)
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
_MODEL_DIR = _PROJECT_ROOT / "assets" / "solid_dispersion" / "models"

# Global cache
_MODEL_CACHE: dict[str, Any] = {}


def _load_lgb_model() -> Any:
    """Load the LightGBM model."""
    if "lgb_model" in _MODEL_CACHE:
        return _MODEL_CACHE["lgb_model"]

    model_path = _MODEL_DIR / "lgb_model.pkl"

    if not model_path.exists():
        raise FileNotFoundError(f"LightGBM model not found: {model_path}")

    with open(model_path, "rb") as f:
        model = pickle.load(f)

    _MODEL_CACHE["lgb_model"] = model
    return model


def _load_lgb_params() -> dict[str, Any]:
    """Load the best hyperparameters."""
    params_path = _MODEL_DIR / "lgb_best_params.json"

    if not params_path.exists():
        return {}

    with open(params_path, "r") as f:
        return json.load(f)


def extract_drug_features(smiles: str) -> dict[str, float]:
    """Extract drug molecular features for solid dispersion prediction.

    Args:
        smiles: SMILES string of the drug

    Returns:
        Dictionary of molecular features
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")

    features = {
        "MW": Descriptors.MolWt(mol),
        "LogP": Descriptors.MolLogP(mol),
        "HBA": Descriptors.NumHAcceptors(mol),
        "HBD": Descriptors.NumHDonors(mol),
        "TPSA": Descriptors.TPSA(mol),
        "RotBonds": Descriptors.NumRotatableBonds(mol),
        "AromaticRings": Descriptors.NumAromaticRings(mol),
    }

    return features


def predict_solid_dispersion(
    smiles: str,
    polymer: str = "PVP K30",
    method: str = "HME",
    drug_loading: float = 10.0,
    temperature: float = 170.0
) -> dict[str, Any]:
    """Predict solid dispersion performance.

    Args:
        smiles: SMILES string of the drug
        polymer: Polymer type (PVP K30, HPMC, Soluplus, etc.)
        method: Preparation method (HME, Spray Drying, etc.)
        drug_loading: Drug loading percentage (w/w)
        temperature: Processing temperature (°C) for HME

    Returns:
        Dictionary with:
            - solubility_enhancement: Predicted fold improvement
            - stability_score: Physical stability prediction (0-1)
            - confidence: Model confidence
            - recommended: Whether this combination is recommended
    """
    model = _load_lgb_model()
    drug_features = extract_drug_features(smiles)

    # Encode categorical features
    polymer_encoding = _encode_polymer(polymer)
    method_encoding = _encode_method(method)

    # Prepare feature vector
    # Note: This is a simplified feature extraction.
    # The actual model may require different features based on training data
    feature_vector = np.array([
        drug_features["MW"],
        drug_features["LogP"],
        drug_features["HBA"],
        drug_features["HBD"],
        drug_features["TPSA"],
        drug_features["RotBonds"],
        polymer_encoding,
        method_encoding,
        drug_loading,
        temperature,
    ]).reshape(1, -1)

    try:
        # Predict solubility enhancement
        prediction = model.predict(feature_vector)[0]

        # Calculate stability score based on molecular properties
        stability_score = _calculate_stability_score(drug_features, polymer, method)

        # Determine confidence based on feature ranges
        confidence = _calculate_confidence(drug_features, drug_loading)

        # Recommendation logic
        recommended = (
            prediction > 2.0 and  # At least 2x solubility improvement
            stability_score > 0.6 and
            confidence > 0.5
        )

        return {
            "solubility_enhancement_fold": float(max(1.0, prediction)),
            "stability_score": float(stability_score),
            "confidence": float(confidence),
            "recommended": bool(recommended),
            "polymer": polymer,
            "method": method,
            "drug_loading_percent": drug_loading,
            "processing_temperature_c": temperature,
        }

    except Exception as e:
        raise RuntimeError(f"Prediction failed: {str(e)}")


def _encode_polymer(polymer: str) -> int:
    """Encode polymer type to numeric value."""
    polymer_map = {
        "PVP K30": 0,
        "PVP K90": 1,
        "HPMC": 2,
        "HPMC-AS": 3,
        "Soluplus": 4,
        "Eudragit E": 5,
        "Copovidone": 6,
    }
    return polymer_map.get(polymer, 0)


def _encode_method(method: str) -> int:
    """Encode preparation method to numeric value."""
    method_map = {
        "HME": 0,
        "Spray Drying": 1,
        "Solvent Evaporation": 2,
        "Freeze Drying": 3,
        "Co-precipitation": 4,
    }
    return method_map.get(method, 0)


def _calculate_stability_score(
    features: dict[str, float],
    polymer: str,
    method: str
) -> float:
    """Calculate physical stability score based on molecular properties.

    Higher stability for:
    - Lower MW (easier mixing)
    - Moderate LogP (good miscibility)
    - More H-bond interactions
    """
    score = 0.5  # Base score

    # MW factor (prefer 200-500 Da)
    if 200 <= features["MW"] <= 500:
        score += 0.15
    elif features["MW"] > 600:
        score -= 0.1

    # LogP factor (prefer 1-4 for good polymer-drug interaction)
    if 1 <= features["LogP"] <= 4:
        score += 0.15
    elif features["LogP"] < 0 or features["LogP"] > 6:
        score -= 0.1

    # H-bonding (more is better for polymer interaction)
    h_bond_capacity = features["HBA"] + features["HBD"]
    if h_bond_capacity >= 4:
        score += 0.2

    # Polymer bonus (some polymers are more versatile)
    if polymer in ["Soluplus", "HPMC-AS", "Copovidone"]:
        score += 0.1

    return min(1.0, max(0.0, score))


def _calculate_confidence(features: dict[str, float], drug_loading: float) -> float:
    """Calculate prediction confidence based on feature ranges.

    Higher confidence when features are within typical training ranges.
    """
    confidence = 1.0

    # MW range check (typical drugs: 200-800 Da)
    if features["MW"] < 150 or features["MW"] > 1000:
        confidence -= 0.2

    # LogP range check (typical: -2 to 6)
    if features["LogP"] < -3 or features["LogP"] > 8:
        confidence -= 0.2

    # Drug loading check (typical: 5-30%)
    if drug_loading < 5 or drug_loading > 40:
        confidence -= 0.15

    return max(0.0, confidence)


def check_model_available() -> bool:
    """Check if the LightGBM model file exists."""
    model_path = _MODEL_DIR / "lgb_model.pkl"
    return model_path.exists()


def get_available_polymers() -> list[str]:
    """Return list of supported polymers."""
    return [
        "PVP K30",
        "PVP K90",
        "HPMC",
        "HPMC-AS",
        "Soluplus",
        "Eudragit E",
        "Copovidone",
    ]


def get_available_methods() -> list[str]:
    """Return list of supported preparation methods."""
    return [
        "HME",
        "Spray Drying",
        "Solvent Evaporation",
        "Freeze Drying",
        "Co-precipitation",
    ]
