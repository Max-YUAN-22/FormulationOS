"""Mock backend for PBPK-AI.

Returns deterministic PK parameter estimates derived from a hash of
``drug_name``. Confidence is fixed at 0.42 to make the mock nature
of the data unambiguous.
"""

from __future__ import annotations

import hashlib
from typing import Any

_ROUTE_FACTORS: dict[str, dict[str, float]] = {
    "oral":  {"bioavailability": 0.85, "ka_factor": 1.0},
    "iv":    {"bioavailability": 1.00, "ka_factor": 0.0},
    "sc":    {"bioavailability": 0.95, "ka_factor": 0.4},
    "im":    {"bioavailability": 0.98, "ka_factor": 0.5},
}

_SPECIES_FACTORS: dict[str, float] = {
    "human": 1.0,
    "rat":   0.18,   # much faster clearance than humans
    "mouse": 0.05,
}


def run(input_data: dict[str, Any]) -> dict[str, Any]:
    """Return mock PK parameters for the given drug, dose, route, species."""
    drug_name = str(input_data.get("drug_name", "unknown")).strip() or "unknown"
    dose_mg = float(input_data.get("dose_mg", 0))
    route = str(input_data.get("route", "oral"))
    species = str(input_data.get("species", "human"))

    if route not in _ROUTE_FACTORS:
        route = "oral"
    if species not in _SPECIES_FACTORS:
        species = "human"

    # Deterministic seed from drug name
    seed = int(hashlib.sha256(drug_name.encode("utf-8")).hexdigest()[:8], 16)
    base_cmax = 50 + (seed % 100)            # 50–150 ng/mL per mg (rough)
    base_auc = 400 + (seed % 600)            # 400–1000 ng·h/mL per mg
    base_half = 1.0 + (seed % 24) / 2.0      # 1–13 h
    base_cl = 5 + (seed % 30)                # 5–35 L/h
    base_vd = 30 + (seed % 100)              # 30–130 L

    f = _ROUTE_FACTORS[route]
    sf = _SPECIES_FACTORS[species]

    cmax = base_cmax * dose_mg * f["bioavailability"] * f["ka_factor"]
    auc = base_auc * dose_mg * f["bioavailability"]
    t_half = base_half / sf
    clearance = base_cl * sf
    vd = base_vd

    return {
        "drug_name": drug_name,
        "route": route,
        "species": species,
        "parameters": {
            "cmax_ng_ml": round(cmax, 2),
            "auc_ng_h_ml": round(auc, 2),
            "t_half_h": round(t_half, 2),
            "clearance_L_h": round(clearance, 2),
            "vd_L": round(vd, 2),
        },
        "confidence": 0.42,
        "notes": (
            f"Mock PK for {drug_name} at {dose_mg} mg via {route} in {species}. "
            f"All values are deterministic placeholders."
        ),
        "warnings": [
            "MOCK OUTPUT — replace PBPK-AI backend with a real PBPK model."
        ],
    }