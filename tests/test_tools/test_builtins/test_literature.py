"""Tests for the Literature mock tool."""

from __future__ import annotations

from formulation_os.tools.loader import load_tool
from tests.conftest import BUILTINS_DIR


def test_load_and_execute_returns_papers() -> None:
    tool = load_tool(BUILTINS_DIR / "literature")
    out = tool.execute({"query": "ibuprofen tablet formulation"})
    assert out["query"] == "ibuprofen tablet formulation"
    assert 1 <= out["total_found"] <= 5
    for paper in out["papers"]:
        assert {"title", "authors", "year", "abstract", "source"} <= paper.keys()
        assert isinstance(paper["authors"], list)
        assert paper["year"] >= 2018
    assert any("MOCK" in w for w in out["warnings"])


def test_max_results_respected() -> None:
    tool = load_tool(BUILTINS_DIR / "literature")
    out = tool.execute({"query": "excipient design", "max_results": 2})
    assert out["total_found"] <= 2
    assert len(out["papers"]) <= 2


def test_empty_query_returns_empty_list() -> None:
    tool = load_tool(BUILTINS_DIR / "literature")
    out = tool.execute({"query": ""})
    assert out["papers"] == []
    assert out["total_found"] == 0


def test_deterministic_per_query() -> None:
    tool = load_tool(BUILTINS_DIR / "literature")
    a = tool.execute({"query": "BCS classification"})
    b = tool.execute({"query": "BCS classification"})
    assert a["papers"] == b["papers"]