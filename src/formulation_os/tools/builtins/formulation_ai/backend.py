"""Mock backend for FormulationAI.

Returns deterministic excipient recipes keyed by ``dosage_form``. The
output is clearly labeled with a ``MOCK OUTPUT`` warning so downstream
consumers cannot mistake it for a real prediction.
"""

from __future__ import annotations

from typing import Any

_MOCK_RECIPES: dict[str, list[dict[str, Any]]] = {
    "tablet": [
        {"name": "Microcrystalline cellulose", "function": "diluent", "percent_w_w": 60.0},
        {"name": "Lactose monohydrate", "function": "diluent", "percent_w_w": 30.5},
        {"name": "Magnesium stearate", "function": "lubricant", "percent_w_w": 1.0},
    ],
    "capsule": [
        {"name": "Mannitol", "function": "diluent", "percent_w_w": 70.0},
        {"name": "Croscarmellose sodium", "function": "disintegrant", "percent_w_w": 5.0},
        {"name": "Magnesium stearate", "function": "lubricant", "percent_w_w": 1.0},
    ],
    "injection": [
        {"name": "Water for injection", "function": "vehicle", "percent_w_w": 100.0},
    ],
    "cream": [
        {"name": "Petrolatum", "function": "oleaginous base", "percent_w_w": 60.0},
        {"name": "Glycerin", "function": "humectant", "percent_w_w": 5.0},
        {"name": "Purified water", "function": "vehicle", "percent_w_w": 35.0},
    ],
    "patch": [
        {"name": "Ethylene-vinyl acetate", "function": "backing matrix", "percent_w_w": 70.0},
        {"name": "Isopropyl myristate", "function": "penetration enhancer", "percent_w_w": 15.0},
    ],
}


def run(input_data: dict[str, Any]) -> dict[str, Any]:
    """Return a mock formulation recipe for the given dosage form."""
    drug_name = str(input_data.get("drug_name", "unknown"))
    target_dose_mg = float(input_data.get("target_dose_mg", 0))
    dosage_form = str(input_data.get("dosage_form", "tablet"))

    excipients = list(_MOCK_RECIPES.get(dosage_form, _MOCK_RECIPES["tablet"]))

    return {
        "drug_name": drug_name,
        "dosage_form": dosage_form,
        "excipients": excipients,
        "summary": (
            f"Mock formulation for {drug_name} "
            f"({dosage_form}, {target_dose_mg} mg)."
        ),
        "warnings": [
            "MOCK OUTPUT — replace FormulationAI backend with the real model before scientific use."
        ],
    }