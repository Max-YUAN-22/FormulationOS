"""Real backend for PreformulationAI using local ML models.

Uses scikit-learn and PyTorch models from models/ directory
to predict preformulation properties like druglikeness, solubility, etc.
"""

from __future__ import annotations

import hashlib
from typing import Any

try:
    from .model_loader import (
        run_preformulation_suite,
        predict_druglikeness,
        predict_oral_bioavailability,
        predict_injectable_feasibility,
        predict_solubility_class,
        predict_hygroscopicity,
        check_models_available,
    )
    _MODELS_STATUS = check_models_available()
    _MODELS_AVAILABLE = any(_MODELS_STATUS.values())
except ImportError as e:
    _MODELS_AVAILABLE = False
    _IMPORT_ERROR = str(e)


def run(input_data: dict[str, Any]) -> dict[str, Any]:
    """Run preformulation prediction using real ML models.

    Args:
        input_data: Expected keys:
            - drug_name: str
            - smiles: str (required for model prediction)
            - assays: list[str] (optional, specific assays to run)

    Returns:
        Preformulation properties and predictions
    """
    drug_name = str(input_data.get("drug_name", "unknown")).strip() or "unknown"
    smiles = input_data.get("smiles", "").strip()
    requested_assays = input_data.get("assays")

    # Check if models are available
    if not _MODELS_AVAILABLE:
        return _mock_fallback(input_data, "Models not available")

    # Require SMILES for real prediction
    if not smiles:
        return _mock_fallback(input_data, "SMILES required for model prediction")

    try:
        # Run full preformulation suite
        results = run_preformulation_suite(smiles)

        if not results.get("success"):
            return _mock_fallback(input_data, results.get("error", "Unknown error"))

        # Format output
        output = {
            "drug_name": drug_name,
            "smiles": smiles,
            "druglikeness": results["druglikeness"],
            "oral_feasibility": results["oral_feasibility"],
            "injectable_feasibility": results["injectable_feasibility"],
            "solubility": results["solubility"],
            "hygroscopicity": results["hygroscopicity"],
            "summary": results["summary"],
            "warnings": results["warnings"],
            "models_used": _get_models_used(),
        }

        return output

    except Exception as e:
        return _mock_fallback(input_data, f"Prediction error: {str(e)}")


def _get_models_used() -> list[str]:
    """Return list of models that were successfully loaded."""
    if not _MODELS_AVAILABLE:
        return []

    available = []
    for model_name, is_available in _MODELS_STATUS.items():
        if is_available:
            available.append(model_name)

    return available


def _mock_fallback(input_data: dict[str, Any], reason: str) -> dict[str, Any]:
    """Fallback to mock output when models unavailable."""
    drug_name = str(input_data.get("drug_name", "unknown")).strip() or "unknown"
    requested = input_data.get("assays") or ["solubility", "logp", "permeability", "bcs_class", "stability"]

    # Use hash-based mock data for consistency
    _BCS_BY_HASH_BUCKET: list[tuple[float, float, float, str]] = [
        # (logP, solubility_mg_mL, perm_cm_s, bcs_class)
        (0.5, 25.0, 4.0e-4, "I"),
        (3.5, 21.0, 2.5e-4, "II"),
        (-0.3, 14.0, 8.0e-5, "III"),
        (4.2, 0.02, 1.5e-6, "IV"),
        (1.8, 5.0, 9.0e-5, "II"),
        (2.6, 8.0, 3.0e-5, "III"),
    ]

    def _bucket_for(name: str) -> tuple[float, float, float, str]:
        h = int(hashlib.sha256(name.encode("utf-8")).hexdigest(), 16)
        return _BCS_BY_HASH_BUCKET[h % len(_BCS_BY_HASH_BUCKET)]

    logp, solubility, perm, bcs = _bucket_for(drug_name)

    out: dict[str, Any] = {"drug_name": drug_name}

    if "solubility" in requested:
        out["solubility_mg_ml"] = solubility
    if "logp" in requested:
        out["logp"] = logp
    if "permeability" in requested:
        out["permeability_cm_s"] = perm
    if "bcs_class" in requested:
        out["bcs_class"] = bcs
    if "stability" in requested:
        out["stability_ph"] = {"1.0": 0.92, "4.0": 0.97, "6.8": 0.99, "9.0": 0.95}

    out["summary"] = (
        f"Mock preformulation for {drug_name}: "
        f"BCS {bcs}, logP {logp:.2f}, solubility {solubility:.2f} mg/mL."
    )
    out["warnings"] = [
        f"⚠️ Using mock backend: {reason}",
        "MOCK OUTPUT — real models not loaded"
    ]
    return out