"""Tests for the PreformulationAI mock tool."""

from __future__ import annotations

from formulation_os.tools.loader import load_tool
from tests.conftest import BUILTINS_DIR


def test_load_and_execute_full() -> None:
    tool = load_tool(BUILTINS_DIR / "preformulation_ai")
    out = tool.execute({"drug_name": "Ibuprofen"})
    for key in ("solubility_mg_ml", "logp", "permeability_cm_s", "bcs_class", "stability_ph", "summary"):
        assert key in out
    assert out["bcs_class"] in ("I", "II", "III", "IV")
    assert any("MOCK" in w for w in out["warnings"])


def test_execute_with_assays_subset() -> None:
    tool = load_tool(BUILTINS_DIR / "preformulation_ai")
    out = tool.execute({"drug_name": "Acetaminophen", "assays": ["solubility", "logp"]})
    assert "solubility_mg_ml" in out
    assert "logp" in out
    assert "bcs_class" not in out


def test_execute_is_deterministic_per_drug() -> None:
    tool = load_tool(BUILTINS_DIR / "preformulation_ai")
    a = tool.execute({"drug_name": "Caffeine"})
    b = tool.execute({"drug_name": "Caffeine"})
    assert a["solubility_mg_ml"] == b["solubility_mg_ml"]
    assert a["bcs_class"] == b["bcs_class"]


def test_execute_empty_query_returns_known_shape() -> None:
    tool = load_tool(BUILTINS_DIR / "preformulation_ai")
    out = tool.execute({"drug_name": ""})
    assert "drug_name" in out
    assert out["drug_name"] == "unknown"