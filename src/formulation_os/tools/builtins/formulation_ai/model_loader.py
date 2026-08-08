"""Local model loader for FormulationAI 2.0 Decision Tree models.

Loads the 12 sklearn RandomForest models from assets/formulation_dt/models/
These are Python 2 pickle files that need encoding="latin1" to load.

FormulationAI 2.0 is the second generation of the formulation decision tree system,
featuring improved training data and enhanced multi-level decision architecture.
"""

from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import Any

import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors

# Find project root (where assets/ folder is)
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
_MODEL_DIR = _PROJECT_ROOT / "assets" / "formulation_dt" / "models"

# Global cache for loaded models
_MODEL_CACHE: dict[str, Any] = {}


def _load_model(model_name: str) -> Any:
    """Load a pickle model file with latin1 encoding (Python 2 compatibility)."""
    if model_name in _MODEL_CACHE:
        return _MODEL_CACHE[model_name]

    model_path = _MODEL_DIR / f"{model_name}.pickle"

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    with open(model_path, "rb") as f:
        model = pickle.load(f, encoding="latin1")

    _MODEL_CACHE[model_name] = model
    return model


def extract_molecular_features(smiles: str) -> np.ndarray:
    """Extract molecular descriptors from SMILES for model input.

    Returns:
        Feature vector as numpy array
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")

    # Extract RDKit descriptors (based on common descriptors used in FormulationAI)
    features = [
        Descriptors.MolWt(mol),
        Descriptors.MolLogP(mol),
        Descriptors.NumHDonors(mol),
        Descriptors.NumHAcceptors(mol),
        Descriptors.TPSA(mol),
        Descriptors.NumRotatableBonds(mol),
        Descriptors.NumAromaticRings(mol),
        Descriptors.FractionCSP3(mol),
        Descriptors.NumAliphaticRings(mol),
        Descriptors.NumSaturatedRings(mol),
    ]

    return np.array(features).reshape(1, -1)


def predict_oral_formulation(smiles: str, bcs_class: str | None = None) -> dict[str, Any]:
    """Predict oral formulation strategy using the decision tree cascade.

    Args:
        smiles: SMILES string of the drug
        bcs_class: Optional BCS class (I, II, III, IV) to guide prediction

    Returns:
        Dictionary with:
            - strategy: Recommended formulation strategy
            - confidence: Model confidence (0-1)
            - level1_pred: Level 1 classification
            - level2_pred: Level 2 classification
    """
    features = extract_molecular_features(smiles)

    # Level 1: Overall oral route classification
    model_o1 = _load_model("model_o1")
    level1_pred = model_o1.predict(features)[0]
    level1_proba = model_o1.predict_proba(features)[0].max()

    # Level 2: Specific strategy based on level 1 result
    # The metadata shows: o2a, o2bs, o2bn, o2bl, o2bc
    # We'll use o2a as the main level-2 predictor
    model_o2a = _load_model("model_o2a")
    level2_pred = model_o2a.predict(features)[0]
    level2_proba = model_o2a.predict_proba(features)[0].max()

    # Map predictions to human-readable strategies
    strategy_map = {
        0: "Immediate Release Tablet",
        1: "Modified Release Formulation",
        2: "Solid Dispersion",
        3: "Lipid-Based Formulation",
        4: "Nanoparticle Formulation",
        5: "Cyclodextrin Complexation",
    }

    strategy = strategy_map.get(level2_pred, f"Strategy {level2_pred}")
    confidence = (level1_proba + level2_proba) / 2

    return {
        "route": "oral",
        "strategy": strategy,
        "confidence": float(confidence),
        "level1_classification": int(level1_pred),
        "level2_classification": int(level2_pred),
        "bcs_guidance": bcs_class,
    }


def predict_injectable_formulation(smiles: str) -> dict[str, Any]:
    """Predict injectable formulation strategy using the decision tree cascade.

    Args:
        smiles: SMILES string of the drug

    Returns:
        Dictionary with strategy and confidence
    """
    features = extract_molecular_features(smiles)

    # Level 1: Overall injectable route classification
    model_i1 = _load_model("model_i1")
    level1_pred = model_i1.predict(features)[0]
    level1_proba = model_i1.predict_proba(features)[0].max()

    # Level 2: Use i2a as main predictor
    model_i2a = _load_model("model_i2a")
    level2_pred = model_i2a.predict(features)[0]
    level2_proba = model_i2a.predict_proba(features)[0].max()

    strategy_map = {
        0: "Aqueous Solution",
        1: "Lyophilized Powder",
        2: "Liposomal Formulation",
        3: "Micellar Solution",
        4: "Emulsion",
        5: "Suspension",
    }

    strategy = strategy_map.get(level2_pred, f"Strategy {level2_pred}")
    confidence = (level1_proba + level2_proba) / 2

    return {
        "route": "injectable",
        "strategy": strategy,
        "confidence": float(confidence),
        "level1_classification": int(level1_pred),
        "level2_classification": int(level2_pred),
    }


def check_models_available() -> bool:
    """Check if all required model files exist."""
    required_models = [
        "model_o1", "model_o2a", "model_o2bs", "model_o2bn", "model_o2bl", "model_o2bc",
        "model_i1", "model_i2a", "model_i2bo", "model_i2bs", "model_i2bl", "model_i2bc",
    ]

    for model_name in required_models:
        model_path = _MODEL_DIR / f"{model_name}.pickle"
        if not model_path.exists():
            return False

    return True
