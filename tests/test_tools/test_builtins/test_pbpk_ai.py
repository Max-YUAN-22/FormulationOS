"""Tests for the PBPK-AI mock tool."""

from __future__ import annotations

from formulation_os.tools.loader import load_tool
from tests.conftest import BUILTINS_DIR


def test_load_and_execute_oral_human() -> None:
    tool = load_tool(BUILTINS_DIR / "pbpk_ai")
    out = tool.execute({"drug_name": "Ibuprofen", "dose_mg": 200, "route": "oral"})
    assert out["drug_name"] == "Ibuprofen"
    assert out["route"] == "oral"
    assert out["species"] == "human"
    assert out["confidence"] == 0.42
    params = out["parameters"]
    for k in ("cmax_ng_ml", "auc_ng_h_ml", "t_half_h", "clearance_L_h", "vd_L"):
        assert k in params
        assert params[k] >= 0
    assert any("MOCK" in w for w in out["warnings"])


def test_iv_bioavailability_higher_than_oral() -> None:
    tool = load_tool(BUILTINS_DIR / "pbpk_ai")
    iv = tool.execute({"drug_name": "DrugX", "dose_mg": 100, "route": "iv"})
    oral = tool.execute({"drug_name": "DrugX", "dose_mg": 100, "route": "oral"})
    assert iv["parameters"]["auc_ng_h_ml"] >= oral["parameters"]["auc_ng_h_ml"]


def test_rat_faster_clearance_than_human() -> None:
    tool = load_tool(BUILTINS_DIR / "pbpk_ai")
    human = tool.execute({"drug_name": "DrugX", "dose_mg": 100, "route": "iv", "species": "human"})
    rat = tool.execute({"drug_name": "DrugX", "dose_mg": 100, "route": "iv", "species": "rat"})
    assert rat["parameters"]["clearance_L_h"] < human["parameters"]["clearance_L_h"]


def test_unknown_route_defaults_to_oral() -> None:
    tool = load_tool(BUILTINS_DIR / "pbpk_ai")
    out = tool.execute({"drug_name": "DrugX", "dose_mg": 100, "route": "intranasal"})
    assert out["route"] == "oral"