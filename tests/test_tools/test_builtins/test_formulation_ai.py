"""Tests for the FormulationAI mock tool."""

from __future__ import annotations

from formulation_os.tools.loader import load_tool
from tests.conftest import BUILTINS_DIR


def test_load_and_execute_tablet() -> None:
    tool = load_tool(BUILTINS_DIR / "formulation_ai")
    out = tool.execute(
        {"drug_name": "Ibuprofen", "target_dose_mg": 200, "dosage_form": "tablet"}
    )
    assert out["drug_name"] == "Ibuprofen"
    assert out["dosage_form"] == "tablet"
    assert isinstance(out["excipients"], list) and len(out["excipients"]) > 0
    for ex in out["excipients"]:
        assert {"name", "function", "percent_w_w"} <= ex.keys()
    assert any("MOCK" in w for w in out["warnings"])


def test_execute_capsule_recipe() -> None:
    tool = load_tool(BUILTINS_DIR / "formulation_ai")
    out = tool.execute(
        {"drug_name": "Aspirin", "target_dose_mg": 100, "dosage_form": "capsule"}
    )
    assert out["dosage_form"] == "capsule"
    assert len(out["excipients"]) > 0


def test_execute_unknown_form_falls_back_to_tablet() -> None:
    tool = load_tool(BUILTINS_DIR / "formulation_ai")
    out = tool.execute(
        {"drug_name": "X", "target_dose_mg": 50, "dosage_form": "nonexistent"}
    )
    assert out["dosage_form"] == "nonexistent"
    assert any("Microcrystalline" in e["name"] for e in out["excipients"])