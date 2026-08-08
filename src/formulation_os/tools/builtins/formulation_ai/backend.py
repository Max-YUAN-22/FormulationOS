"""Real backend for FormulationAI 2.0 using local Decision Tree models.

Uses 12 sklearn RandomForest models from assets/formulation_dt/models/
to predict optimal formulation strategies for oral and injectable routes.

FormulationAI 2.0 features:
- Enhanced training dataset with diverse formulation examples
- Improved multi-level decision architecture (input layer → output layer)
- Better accuracy for BCS Class II/IV compounds
- More precise polymer and excipient recommendations
"""

from __future__ import annotations

from typing import Any

try:
    from .model_loader import (
        predict_oral_formulation,
        predict_injectable_formulation,
        check_models_available,
    )
    MODELS_AVAILABLE = check_models_available()
except ImportError as e:
    MODELS_AVAILABLE = False
    _import_error = str(e)


def run(input_data: dict[str, Any]) -> dict[str, Any]:
    """Predict formulation strategy using real ML models.

    Args:
        input_data: Expected keys:
            - drug_name: str
            - smiles: str (required for model prediction)
            - dosage_form: str (oral/injectable/tablet/capsule/injection)
            - bcs_class: str (optional, for oral route guidance)

    Returns:
        Formulation strategy prediction with confidence score
    """
    drug_name = str(input_data.get("drug_name", "unknown"))
    smiles = input_data.get("smiles", "").strip()
    dosage_form = str(input_data.get("dosage_form", "tablet")).lower()
    bcs_class = input_data.get("bcs_class")

    # Check if models are available
    if not MODELS_AVAILABLE:
        return _mock_fallback(input_data, "Models not available")

    # Require SMILES for real prediction
    if not smiles:
        return _mock_fallback(input_data, "SMILES required for model prediction")

    try:
        # Determine route from dosage form
        route = _determine_route(dosage_form)

        if route == "oral":
            prediction = predict_oral_formulation(smiles, bcs_class)
        elif route == "injectable":
            prediction = predict_injectable_formulation(smiles)
        else:
            return _mock_fallback(input_data, f"Unsupported route: {route}")

        # Format output
        return {
            "drug_name": drug_name,
            "route": prediction["route"],
            "recommended_strategy": prediction["strategy"],
            "confidence": prediction["confidence"],
            "model_output": {
                "level1_classification": prediction["level1_classification"],
                "level2_classification": prediction["level2_classification"],
            },
            "excipients": _get_excipients_for_strategy(prediction["strategy"]),
            "summary": (
                f"FormulationAI prediction for {drug_name}: "
                f"{prediction['strategy']} "
                f"(confidence: {prediction['confidence']:.2%})"
            ),
            "warnings": _get_warnings(prediction["confidence"]),
        }

    except Exception as e:
        return _mock_fallback(input_data, f"Model error: {str(e)}")


def _determine_route(dosage_form: str) -> str:
    """Map dosage form to route (oral/injectable)."""
    oral_forms = ["oral", "tablet", "capsule", "suspension", "solution"]
    injectable_forms = ["injectable", "injection", "iv", "im", "sc"]

    if any(form in dosage_form for form in oral_forms):
        return "oral"
    elif any(form in dosage_form for form in injectable_forms):
        return "injectable"
    else:
        return "oral"  # Default to oral


def _get_excipients_for_strategy(strategy: str) -> list[dict[str, Any]]:
    """Return typical excipients for a given formulation strategy."""
    excipient_library = {
        "Immediate Release Tablet": [
            {"name": "Microcrystalline cellulose", "function": "diluent", "percent_w_w": 60.0},
            {"name": "Croscarmellose sodium", "function": "disintegrant", "percent_w_w": 5.0},
            {"name": "Magnesium stearate", "function": "lubricant", "percent_w_w": 1.0},
        ],
        "Solid Dispersion": [
            {"name": "PVP K30", "function": "carrier polymer", "percent_w_w": 70.0},
            {"name": "Crospovidone", "function": "disintegrant", "percent_w_w": 5.0},
        ],
        "Lipid-Based Formulation": [
            {"name": "Gelucire 44/14", "function": "lipid excipient", "percent_w_w": 50.0},
            {"name": "Labrasol", "function": "surfactant", "percent_w_w": 30.0},
        ],
        "Nanoparticle Formulation": [
            {"name": "PLGA", "function": "polymer matrix", "percent_w_w": 80.0},
            {"name": "Poloxamer 188", "function": "stabilizer", "percent_w_w": 5.0},
        ],
        "Aqueous Solution": [
            {"name": "Water for injection", "function": "vehicle", "percent_w_w": 95.0},
            {"name": "Sodium chloride", "function": "tonicity agent", "percent_w_w": 0.9},
        ],
        "Lyophilized Powder": [
            {"name": "Mannitol", "function": "bulking agent", "percent_w_w": 5.0},
            {"name": "Trehalose", "function": "cryoprotectant", "percent_w_w": 3.0},
        ],
        "Liposomal Formulation": [
            {"name": "DSPC", "function": "phospholipid", "percent_w_w": 10.0},
            {"name": "Cholesterol", "function": "membrane stabilizer", "percent_w_w": 5.0},
        ],
    }

    return excipient_library.get(strategy, [
        {"name": "Generic excipient", "function": "carrier", "percent_w_w": 90.0}
    ])


def _get_warnings(confidence: float) -> list[str]:
    """Generate warnings based on model confidence."""
    warnings = []

    if confidence < 0.6:
        warnings.append("⚠️ Low model confidence - consider expert review")
    elif confidence < 0.75:
        warnings.append("ℹ️ Moderate confidence - experimental validation recommended")

    return warnings


def _mock_fallback(input_data: dict[str, Any], reason: str) -> dict[str, Any]:
    """Fallback to mock output when models unavailable."""
    drug_name = str(input_data.get("drug_name", "unknown"))
    dosage_form = str(input_data.get("dosage_form", "tablet"))

    mock_excipients = [
        {"name": "Microcrystalline cellulose", "function": "diluent", "percent_w_w": 60.0},
        {"name": "Magnesium stearate", "function": "lubricant", "percent_w_w": 1.0},
    ]

    return {
        "drug_name": drug_name,
        "dosage_form": dosage_form,
        "recommended_strategy": "Generic Formulation",
        "confidence": 0.0,
        "excipients": mock_excipients,
        "summary": f"Mock formulation for {drug_name} ({dosage_form})",
        "warnings": [
            f"⚠️ Using mock backend: {reason}",
            "MOCK OUTPUT — real models not loaded"
        ],
    }