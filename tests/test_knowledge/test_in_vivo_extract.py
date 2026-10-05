"""Structured ADME extraction — real DrugBank prose fixtures."""

from __future__ import annotations

from formulation_os.knowledge.in_vivo_extract import (
    extract_clearance,
    extract_half_life,
    extract_protein_binding,
    extract_structured,
    extract_volume_of_distribution,
)


def test_half_life_ranges_and_units():
    r = extract_half_life("The terminal elimination half-life of about 30–50 hours [FDA label].")
    assert (r["min"], r["max"], r["unit"]) == (30.0, 50.0, "h")
    r = extract_half_life("serum half-life is 1.2-2 hours.")
    assert (r["min"], r["max"]) == (1.2, 2.0)
    r = extract_half_life("half-life is 14 hours")
    assert (r["min"], r["max"]) == (14.0, 14.0)
    r = extract_half_life("initial half-life of approximately 10 minutes")
    assert abs(r["min"] - 10 / 60) < 0.01 and r["unit"] == "h"


def test_protein_binding():
    assert extract_protein_binding("About 98% [A175327].")["value"] == 98.0
    assert extract_protein_binding("99% bound primarily to albumin")["value"] == 99.0
    assert extract_protein_binding("negligibly bound to plasma proteins")["value"] == 0.0
    assert extract_protein_binding("no percentage here") is None


def test_vd_and_clearance():
    assert extract_volume_of_distribution("21 L/kg [A175327].")["unit"] == "L/kg"
    assert extract_volume_of_distribution("volume of distribution is of 380 L.")["value"] == 380.0
    c = extract_clearance("7 ± 1.3 ml/min/kg")
    assert (c["min"], c["max"], c["unit"]) == (5.7, 8.3, "ml/min/kg")
    c = extract_clearance("ranges between 3-13 L/h")
    assert (c["min"], c["max"]) == (3.0, 13.0)
    assert extract_clearance("625 ml/min")["min"] == 625.0


def test_extract_structured_bucket():
    iv = {
        "half_life": [{"value": "half-life is 6.2 hours"}],
        "protein_binding": [{"value": "negligibly bound"}],
        "clearance": [{"value": "625 ml/min"}],
    }
    out = extract_structured(iv)
    assert out["half_life_h"]["min"] == 6.2
    assert out["protein_binding_pct"]["value"] == 0.0
    assert out["clearance_structured"]["min"] == 625.0
    assert "vd" not in out  # no Vd prose -> no guess
