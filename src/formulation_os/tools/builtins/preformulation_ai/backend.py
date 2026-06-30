"""Mock backend for PreformulationAI.

Returns deterministic preformulation property values derived from a
hash of ``drug_name``. The same drug name always produces the same
output, which is convenient for unit testing.
"""

from __future__ import annotations

import hashlib
from typing import Any

_BCS_BY_HASH_BUCKET: list[tuple[float, float, float, str]] = [
    # (logP, solubility_mg_mL, perm_cm_s, bcs_class)
    (0.5, 25.0, 4.0e-4, "I"),
    (3.5, 21.0, 2.5e-4, "II"),
    (-0.3, 14.0, 8.0e-5, "III"),
    (4.2, 0.02, 1.5e-6, "IV"),
    (1.8, 5.0, 9.0e-5, "II"),
    (2.6, 8.0, 3.0e-5, "III"),
]


def _bucket_for(drug_name: str) -> tuple[float, float, float, str]:
    h = int(hashlib.sha256(drug_name.encode("utf-8")).hexdigest(), 16)
    return _BCS_BY_HASH_BUCKET[h % len(_BCS_BY_HASH_BUCKET)]


def run(input_data: dict[str, Any]) -> dict[str, Any]:
    """Return mock preformulation properties for the given drug."""
    drug_name = str(input_data.get("drug_name", "unknown")).strip() or "unknown"
    requested = input_data.get("assays") or ["solubility", "logp", "permeability", "bcs_class", "stability"]
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
        "MOCK OUTPUT — replace PreformulationAI backend with the real model."
    ]
    return out