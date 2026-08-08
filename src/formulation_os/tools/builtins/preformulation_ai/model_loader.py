"""Local model loader for PreFormulationAI models.

Loads PyTorch (.ckpt) and scikit-learn (.pkl) models from models/ directory
to predict preformulation properties like pKa, LogP, solubility, etc.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import joblib
import numpy as np

# Find models directory
_MODELS_DIR = Path(__file__).parent / "models"

# Global cache for loaded models
_MODEL_CACHE: dict[str, Any] = {}


def _load_sklearn_model(model_name: str) -> Any:
    """Load a scikit-learn pickle model (using joblib for LightGBM compatibility)."""
    if model_name in _MODEL_CACHE:
        return _MODEL_CACHE[model_name]

    model_path = _MODELS_DIR / f"{model_name}.pkl"

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    # Use joblib for loading (handles LightGBM and scikit-learn models)
    model = joblib.load(model_path)

    _MODEL_CACHE[model_name] = model
    return model


def _load_pytorch_model(model_name: str) -> Any:
    """Load a PyTorch checkpoint model."""
    if model_name in _MODEL_CACHE:
        return _MODEL_CACHE[model_name]

    try:
        import torch
    except ImportError:
        raise ImportError("PyTorch not installed. Run: pip install torch")

    model_path = _MODELS_DIR / f"{model_name}.ckpt"

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    # Load checkpoint
    checkpoint = torch.load(model_path, map_location=torch.device('cpu'))

    _MODEL_CACHE[model_name] = checkpoint
    return checkpoint


def extract_molecular_descriptors(smiles: str) -> np.ndarray:
    """Extract complete 74 molecular features from SMILES.

    Uses the feature_extractor module to get all required features.

    Args:
        smiles: SMILES string

    Returns:
        Feature vector as numpy array (74 features)
    """
    try:
        from .feature_extractor import extract_74_features

        features_df = extract_74_features(smiles)
        return features_df.values

    except ImportError as e:
        raise ImportError(f"Feature extraction failed: {str(e)}")


def predict_druglikeness(smiles: str) -> dict[str, Any]:
    """Predict drug-likeness using the Random Forest model.

    Args:
        smiles: SMILES string

    Returns:
        Dictionary with druglike probability and category
    """
    model = _load_sklearn_model("druglikeness_model_final")

    # Extract all features and select the ones needed for druglikeness model
    from .feature_extractor import extract_74_features
    from .feature_selector import add_missing_features

    features_df = extract_74_features(smiles)
    features_df = add_missing_features(features_df, 'druglikeness')

    try:
        prediction = model.predict(features_df)[0]
        proba = model.predict_proba(features_df)[0]

        return {
            "is_druglike": bool(prediction == 1),
            "probability": float(proba[1]) if len(proba) > 1 else float(proba[0]),
            "category": "Drug-like" if prediction == 1 else "Non-drug-like",
        }
    except Exception as e:
        raise RuntimeError(f"Druglikeness prediction failed: {str(e)}")


def predict_oral_bioavailability(smiles: str) -> dict[str, Any]:
    """Predict oral bioavailability feasibility.

    Args:
        smiles: SMILES string

    Returns:
        Dictionary with oral feasibility prediction
    """
    model = _load_sklearn_model("oral_model_final")

    # Extract all features and select the 71 needed for oral model
    from .feature_extractor import extract_74_features
    from .feature_selector import add_missing_features

    features_df = extract_74_features(smiles)
    features_df = add_missing_features(features_df, 'oral')

    try:
        prediction = model.predict(features_df)[0]
        proba = model.predict_proba(features_df)[0]

        return {
            "oral_feasible": bool(prediction == 1),
            "probability": float(proba[1]) if len(proba) > 1 else float(proba[0]),
            "category": "Orally bioavailable" if prediction == 1 else "Poor oral absorption",
        }
    except Exception as e:
        raise RuntimeError(f"Oral prediction failed: {str(e)}")


def predict_injectable_feasibility(smiles: str) -> dict[str, Any]:
    """Predict injectable formulation feasibility.

    Args:
        smiles: SMILES string

    Returns:
        Dictionary with injectable feasibility prediction
    """
    model = _load_sklearn_model("injectable_model_final")

    # Extract all features and select the 66 needed for injectable model
    from .feature_extractor import extract_74_features
    from .feature_selector import add_missing_features

    features_df = extract_74_features(smiles)
    features_df = add_missing_features(features_df, 'injectable')

    try:
        prediction = model.predict(features_df)[0]
        proba = model.predict_proba(features_df)[0]

        return {
            "injectable_feasible": bool(prediction == 1),
            "probability": float(proba[1]) if len(proba) > 1 else float(proba[0]),
            "category": "Injectable suitable" if prediction == 1 else "Injectable challenging",
        }
    except Exception as e:
        raise RuntimeError(f"Injectable prediction failed: {str(e)}")


def predict_solubility_class(smiles: str) -> dict[str, Any]:
    """Predict solubility class (high/medium/low).

    Args:
        smiles: SMILES string

    Returns:
        Dictionary with solubility class
    """
    model = _load_sklearn_model("k_solubility_c")
    features = extract_molecular_descriptors(smiles).reshape(1, -1)

    try:
        prediction = model.predict(features)[0]
        proba = model.predict_proba(features)[0]

        class_map = {0: "Low", 1: "Medium", 2: "High"}

        return {
            "solubility_class": class_map.get(prediction, "Unknown"),
            "class_numeric": int(prediction),
            "probability": float(proba.max()),
        }
    except Exception as e:
        raise RuntimeError(f"Solubility classification failed: {str(e)}")


def predict_hygroscopicity(smiles: str) -> dict[str, Any]:
    """Predict hygroscopicity (moisture absorption tendency).

    Args:
        smiles: SMILES string

    Returns:
        Dictionary with hygroscopicity prediction
    """
    model = _load_sklearn_model("Hygroscopicity")
    features = extract_molecular_descriptors(smiles).reshape(1, -1)

    try:
        prediction = model.predict(features)[0]

        # Hygroscopicity classes: 0=Non-hygroscopic, 1=Slightly, 2=Moderately, 3=Very hygroscopic
        class_map = {
            0: "Non-hygroscopic",
            1: "Slightly hygroscopic",
            2: "Moderately hygroscopic",
            3: "Very hygroscopic",
        }

        return {
            "hygroscopicity_class": class_map.get(prediction, "Unknown"),
            "class_numeric": int(prediction),
            "warning": "Storage in dry conditions recommended" if prediction >= 2 else None,
        }
    except Exception as e:
        raise RuntimeError(f"Hygroscopicity prediction failed: {str(e)}")


def run_preformulation_suite(smiles: str) -> dict[str, Any]:
    """Run full preformulation prediction suite using all available models.

    Args:
        smiles: SMILES string

    Returns:
        Comprehensive preformulation assessment
    """
    results = {}

    try:
        # Drug-likeness assessment
        druglike = predict_druglikeness(smiles)
        results["druglikeness"] = druglike

        # Route feasibility
        oral = predict_oral_bioavailability(smiles)
        injectable = predict_injectable_feasibility(smiles)
        results["oral_feasibility"] = oral
        results["injectable_feasibility"] = injectable

        # Physicochemical properties
        solubility = predict_solubility_class(smiles)
        hygro = predict_hygroscopicity(smiles)
        results["solubility"] = solubility
        results["hygroscopicity"] = hygro

        # Generate summary
        results["summary"] = _generate_summary(druglike, oral, injectable, solubility, hygro)

        # Generate warnings
        results["warnings"] = _generate_warnings(druglike, oral, injectable, solubility, hygro)

        results["success"] = True

    except Exception as e:
        results["success"] = False
        results["error"] = str(e)
        results["warnings"] = [f"⚠️ Prediction failed: {str(e)}"]

    return results


def _generate_summary(
    druglike: dict,
    oral: dict,
    injectable: dict,
    solubility: dict,
    hygro: dict
) -> str:
    """Generate human-readable summary."""
    lines = []

    if druglike["is_druglike"]:
        lines.append(f"✓ Drug-like compound ({druglike['probability']:.1%} confidence)")
    else:
        lines.append(f"⚠ Non-drug-like compound ({1-druglike['probability']:.1%} confidence)")

    lines.append(f"• Oral bioavailability: {oral['category']} ({oral['probability']:.1%})")
    lines.append(f"• Injectable feasibility: {injectable['category']} ({injectable['probability']:.1%})")
    lines.append(f"• Solubility class: {solubility['solubility_class']}")
    lines.append(f"• Hygroscopicity: {hygro['hygroscopicity_class']}")

    return "\n".join(lines)


def _generate_warnings(
    druglike: dict,
    oral: dict,
    injectable: dict,
    solubility: dict,
    hygro: dict
) -> list[str]:
    """Generate warning messages."""
    warnings = []

    if not druglike["is_druglike"]:
        warnings.append("⚠️ Poor drug-likeness - consider structural modifications")

    if not oral["oral_feasible"]:
        warnings.append("⚠️ Poor oral absorption predicted - consider formulation strategies")

    if solubility["solubility_class"] == "Low":
        warnings.append("⚠️ Low solubility - solubility enhancement strategies recommended")

    if hygro["class_numeric"] >= 2:
        warnings.append("ℹ️ Hygroscopic compound - moisture-protective packaging required")

    if not warnings:
        warnings.append("✓ No major formulation concerns identified")

    return warnings


def check_models_available() -> dict[str, bool]:
    """Check which models are available."""
    sklearn_models = [
        "druglikeness_model_final",
        "oral_model_final",
        "injectable_model_final",
        "k_solubility_c",
        "Hygroscopicity",
    ]

    pytorch_models = [
        "A_pKa",
        "B_pKa",
        "MP",
        "Tg",
        "density",
        "logP",
        "logS",
        "logD",
        "logPapp",
        "kinetic_solubility",
    ]

    availability = {}

    for model in sklearn_models:
        availability[model] = (_MODELS_DIR / f"{model}.pkl").exists()

    for model in pytorch_models:
        availability[model] = (_MODELS_DIR / f"{model}.ckpt").exists()

    return availability
