"""Tests for the web drug-card provider (local-only, no network)."""

from __future__ import annotations

import pytest

from formulation_os.knowledge import web_drug_card as wdc


@pytest.fixture(autouse=True)
def _clear_cache():
    wdc._CACHE.clear()
    yield
    wdc._CACHE.clear()


class _FakeStore:
    def __init__(self, profile):
        self._p = profile

    def get(self, name):
        return self._p


def test_store_hit_returns_profile(monkeypatch):
    prof = {"query": "Aspirin", "identity": {"pubchem_cid": [{"value": 2244}]},
            "_meta": {"sources_used": ["PubChem"]}}
    monkeypatch.setattr(wdc, "LocalDrugStore", lambda *a, **k: _FakeStore(prof))
    out = wdc.get_drug_card("Aspirin")
    assert out["identity"]["pubchem_cid"][0]["value"] == 2244
    assert wdc.is_prebuilt("Aspirin") is True


def test_miss_returns_none_no_network(monkeypatch):
    monkeypatch.setattr(wdc, "LocalDrugStore", lambda *a, **k: _FakeStore(None))
    assert wdc.get_drug_card("Nonexistol") is None
    assert wdc.is_prebuilt("Nonexistol") is False


def test_has_full_depth():
    assert wdc.has_full_depth({"approved_products": [{"x": 1}]}) is True
    assert wdc.has_full_depth({"patents_exclusivity": [{"x": 1}]}) is True
    assert wdc.has_full_depth({"identity": {"a": [1]}, "approved_products": [],
                               "patents_exclusivity": [], "drug_forms": []}) is False
    assert wdc.has_full_depth(None) is False


def test_web_card_module_has_no_network_imports():
    # local-only: must not pull in the live aggregator
    import inspect
    src = inspect.getsource(wdc)
    assert "DrugIntelligenceAggregator" not in src
    assert "requests" not in src
