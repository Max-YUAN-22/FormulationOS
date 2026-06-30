"""Mock backend for FormulationDT.

Generates a deterministic Weibull-like dissolution curve parameterized
by a hash of ``drug_name``. Same input always yields the same curve.
"""

from __future__ import annotations

import hashlib
from typing import Any

_DEFAULT_SAMPLE_TIMES = (0, 5, 10, 15, 30, 45, 60, 90, 120)


def _weibull(t: float, t50: float, beta: float = 1.2) -> float:
    """Return percent dissolved at time ``t`` for Weibull params (t50, beta)."""
    if t <= 0:
        return 0.0
    return 100.0 * (1.0 - 2.71828 ** (-((t / t50) ** beta)))


def run(input_data: dict[str, Any]) -> dict[str, Any]:
    """Return a mock dissolution profile for the given drug + medium."""
    drug_name = str(input_data.get("drug_name", "unknown")).strip() or "unknown"
    medium = str(input_data.get("medium", "pH_6_8"))
    duration_min = float(input_data.get("duration_min", 120))

    seed = int(hashlib.sha256(drug_name.encode("utf-8")).hexdigest()[:8], 16)
    # T50 between 5 and 60 minutes
    t50 = 5.0 + (seed % 55)

    sample_times = [t for t in _DEFAULT_SAMPLE_TIMES if t <= duration_min]
    if duration_min not in sample_times:
        sample_times.append(duration_min)

    curve = [
        {"t_min": t, "pct_dissolved": round(_weibull(t, t50), 2)}
        for t in sample_times
    ]

    return {
        "drug_name": drug_name,
        "medium": medium,
        "dissolution_curve": curve,
        "f2_similarity": round(50.0 + (seed % 30), 2),
        "summary": (
            f"Mock dissolution for {drug_name} in {medium}: "
            f"T50 ~{t50:.1f} min, sampled at {len(curve)} timepoints."
        ),
        "warnings": [
            "MOCK OUTPUT — replace FormulationDT backend with a real digital-twin model."
        ],
    }