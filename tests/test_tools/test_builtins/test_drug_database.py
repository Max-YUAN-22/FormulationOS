"""Tests for the DrugDatabase tool backend — local-only, no network."""

from __future__ import annotations

import pytest

from formulation_os.tools.builtins.drug_database import backend
from formulation_os.knowledge.local_store import LocalDrugStore
from formulation_os.knowledge.drug_intelligence import DrugIntelligenceAggregator
from formulation_os.knowledge.sources.base import SourceAdapter
from formulation_os.knowledge.sources.schema import (
    CATEGORY_APPROVED,
    CATEGORY_IDENTITY,
    CATEGORY_PATENTS,
    CATEGORY_PHYSCHEM,
    Evidence,
    FieldValue,
    Provenance,
    SourceResult,
    SourceStatus,
)


class _FakeSource(SourceAdapter):
    def __init__(self, name, result):
        self.name = name
        self._result = result

    def fetch(self, drug_name=None, smiles=None, categories=None):
        return self._result


def _build_profile_dict():
    """Assemble one profile via the aggregator using fake (offline) adapters."""
    r = SourceResult(source="PubChem", status=SourceStatus.OK)
    prov = Provenance(source="PubChem", reference="http://example/cid/3672")
    r.add_field(CATEGORY_IDENTITY, "pubchem_cid", FieldValue(3672, None, Evidence.RECORDED, prov))
    r.add_field(CATEGORY_PHYSCHEM, "molecular_weight", FieldValue(206.28, "g/mol", Evidence.RECORDED, prov))
    r.add_field(CATEGORY_PHYSCHEM, "xlogp", FieldValue(3.5, None, Evidence.PREDICTED, prov))

    fda = SourceResult(source="openFDA (FDA)", status=SourceStatus.OK)
    fprov = Provenance(source="openFDA (FDA)")
    fda.add_record(CATEGORY_APPROVED, {"brand_name": FieldValue("MOTRIN", None, Evidence.RECORDED, fprov)})

    ob = SourceResult(source="FDA Orange Book", status=SourceStatus.OK)
    obprov = Provenance(source="FDA Orange Book")
    ob.add_record(CATEGORY_PATENTS, {
        "type": FieldValue("patent", None, Evidence.RECORDED, obprov),
        "patent_expire_date": FieldValue("2031-01-01", None, Evidence.RECORDED, obprov),
    })

    adapters = {
        "PubChem": _FakeSource("PubChem", r),
        "ChEMBL": _FakeSource("ChEMBL", SourceResult(source="ChEMBL", status=SourceStatus.NOT_FOUND)),
        "openFDA (FDA)": _FakeSource("openFDA (FDA)", fda),
        "FDA Orange Book": _FakeSource("FDA Orange Book", ob),
    }
    agg = DrugIntelligenceAggregator(adapters=adapters)
    return agg.build(drug_name="Ibuprofen").to_dict()


@pytest.fixture()
def local_backend(tmp_path, monkeypatch):
    """Point the backend at a temp local store pre-populated with Ibuprofen."""
    db = tmp_path / "drug_intelligence.db"
    store = LocalDrugStore(str(db), for_write=True)
    store.init_schema()
    store.write("Ibuprofen", _build_profile_dict(), built_at="2026-01-01")

    read_store = LocalDrugStore(str(db))
    monkeypatch.setattr(backend, "_store", read_store)
    return read_store


def test_properties_query_reads_local_store(local_backend):
    out = backend.run({"drug_name": "Ibuprofen", "query_type": "properties"})
    assert out["identity"]["pubchem_cid"][0]["value"] == 3672
    assert out["identity"]["pubchem_cid"][0]["source"] == "PubChem"
    mw = out["physicochemical"]["molecular_weight"][0]
    assert mw["value"] == 206.28 and mw["evidence"] == "recorded"
    assert out["physicochemical"]["xlogp"][0]["evidence"] == "predicted"
    assert "PubChem" in out["_meta"]["sources_used"]


def test_patents_and_exclusivity_separate(local_backend):
    out = backend.run({"drug_name": "Ibuprofen", "query_type": "patents"})
    patents = out["patents_exclusivity"]
    assert patents and patents[0]["type"]["value"] == "patent"
    assert patents[0]["patent_expire_date"]["value"] == "2031-01-01"


def test_approved_products_query(local_backend):
    out = backend.run({"drug_name": "Ibuprofen", "query_type": "approved_products"})
    assert any(p.get("brand_name", {}).get("value") == "MOTRIN" for p in out["approved_products"])


def test_case_insensitive_lookup(local_backend):
    out = backend.run({"drug_name": "ibuprofen", "query_type": "identity"})
    assert out["identity"]["pubchem_cid"][0]["value"] == 3672


def test_unknown_drug_returns_not_found(local_backend):
    out = backend.run({"drug_name": "Nonexistol", "query_type": "properties"})
    assert out["error"] == "not_found"
    assert any("rebuild" in w.lower() or "curated" in w.lower() for w in out["warnings"])


def test_missing_store_reports_build_hint(tmp_path, monkeypatch):
    empty = LocalDrugStore(str(tmp_path / "absent.db"))  # file does not exist
    monkeypatch.setattr(backend, "_store", empty)
    out = backend.run({"drug_name": "Ibuprofen"})
    assert out["error"] == "local_store_missing"


def test_missing_target_errors():
    out = backend.run({"query_type": "properties"})
    assert "error" in out


def test_legacy_query_type_flagged(local_backend):
    out = backend.run({"drug_name": "Ibuprofen", "query_type": "interactions"})
    assert out["results"] == []
    assert any("not served" in w for w in out["warnings"])


def test_tool_loads_via_loader():
    from formulation_os.tools.loader import load_tool
    from tests.conftest import BUILTINS_DIR

    tool = load_tool(BUILTINS_DIR / "drug_database")
    assert tool is not None
