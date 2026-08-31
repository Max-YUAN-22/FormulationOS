"""Tests for the web drug-card provider (store hit + live fallback, mocked)."""

from __future__ import annotations

import pytest

from formulation_os.knowledge import web_drug_card as wdc
from formulation_os.knowledge.sources.schema import (
    CATEGORY_IDENTITY, Evidence, FieldValue, Provenance, SourceResult, SourceStatus,
    DrugIntelligence,
)
from formulation_os.knowledge.sources.base import SourceAdapter
from formulation_os.knowledge.drug_intelligence import DrugIntelligenceAggregator


@pytest.fixture(autouse=True)
def _clear_cache():
    wdc._CACHE.clear()
    wdc._agg = None
    yield
    wdc._CACHE.clear()
    wdc._agg = None


class _FakeStore:
    def __init__(self, profile):
        self._p = profile

    def get(self, name):
        return self._p


def test_store_hit_returns_prebuilt(monkeypatch):
    prof = {"query": "Aspirin", "identity": {"pubchem_cid": [{"value": 2244}]}, "_meta": {"sources_used": ["PubChem"]}}
    monkeypatch.setattr(wdc, "LocalDrugStore", lambda *a, **k: _FakeStore(prof))
    out = wdc.get_drug_card("Aspirin")
    assert out["identity"]["pubchem_cid"][0]["value"] == 2244
    assert wdc.is_prebuilt("Aspirin") is True


class _FakeAdapter(SourceAdapter):
    name = "PubChem"

    def fetch(self, drug_name=None, smiles=None, categories=None):
        r = SourceResult(source="PubChem", status=SourceStatus.OK)
        r.add_field(CATEGORY_IDENTITY, "pubchem_cid", FieldValue(999, None, Evidence.RECORDED, Provenance("PubChem")))
        return r


def test_live_fallback_uses_public_sources(monkeypatch):
    # store miss -> live fetch
    monkeypatch.setattr(wdc, "LocalDrugStore", lambda *a, **k: _FakeStore(None))
    # force the public aggregator to a fake adapter set (no DrugBank/CN)
    monkeypatch.setattr(
        wdc, "_public_aggregator",
        lambda: DrugIntelligenceAggregator(adapters={"PubChem": _FakeAdapter()}),
    )
    out = wdc.get_drug_card("Noveldrug")
    assert out is not None
    assert out["identity"]["pubchem_cid"][0]["value"] == 999
    assert "PubChem" in out["_meta"]["sources_used"]


def test_live_fallback_none_when_nothing_found(monkeypatch):
    monkeypatch.setattr(wdc, "LocalDrugStore", lambda *a, **k: _FakeStore(None))

    class _Empty(SourceAdapter):
        name = "PubChem"
        def fetch(self, drug_name=None, smiles=None, categories=None):
            return SourceResult(source="PubChem", status=SourceStatus.NOT_FOUND)

    monkeypatch.setattr(
        wdc, "_public_aggregator",
        lambda: DrugIntelligenceAggregator(adapters={"PubChem": _Empty()}),
    )
    assert wdc.get_drug_card("Nonexistol") is None


def test_public_aggregator_excludes_licence_restricted():
    agg = wdc._public_aggregator()
    assert "DrugBank" not in agg.adapters
    assert "NMPA/CDE (China)" not in agg.adapters
    assert "PubChem" in agg.adapters
