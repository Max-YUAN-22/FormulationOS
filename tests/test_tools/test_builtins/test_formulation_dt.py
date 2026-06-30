"""Tests for the FormulationDT mock tool."""

from __future__ import annotations

from formulation_os.tools.loader import load_tool
from tests.conftest import BUILTINS_DIR


def test_load_and_execute_default() -> None:
    tool = load_tool(BUILTINS_DIR / "formulation_dt")
    out = tool.execute({"drug_name": "Ibuprofen"})
    assert out["drug_name"] == "Ibuprofen"
    assert out["medium"] == "pH_6_8"
    assert isinstance(out["dissolution_curve"], list)
    assert all({"t_min", "pct_dissolved"} <= p.keys() for p in out["dissolution_curve"])
    pcts = [p["pct_dissolved"] for p in out["dissolution_curve"]]
    assert pcts == sorted(pcts)
    assert any("MOCK" in w for w in out["warnings"])


def test_execute_short_duration() -> None:
    tool = load_tool(BUILTINS_DIR / "formulation_dt")
    out = tool.execute({"drug_name": "DrugY", "duration_min": 30})
    assert all(p["t_min"] <= 30 for p in out["dissolution_curve"])


def test_execute_deterministic_per_drug() -> None:
    tool = load_tool(BUILTINS_DIR / "formulation_dt")
    a = tool.execute({"drug_name": "DrugZ"})
    b = tool.execute({"drug_name": "DrugZ"})
    assert a["dissolution_curve"] == b["dissolution_curve"]