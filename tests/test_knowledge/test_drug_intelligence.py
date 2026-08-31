"""Tests for the multi-source drug intelligence layer (network mocked)."""

from __future__ import annotations

from formulation_os.knowledge.drug_intelligence import (
    DrugIntelligenceAggregator,
    PRIMARY_SOURCE,
)
from formulation_os.knowledge.sources.base import SourceAdapter
from formulation_os.knowledge.sources.pubchem import PubChemAdapter
from formulation_os.knowledge.sources.openfda import OpenFDAAdapter
from formulation_os.knowledge.sources import stubs
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


# --------------------------------------------------------------------------- #
# Fake HTTP layer                                                             #
# --------------------------------------------------------------------------- #
class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


class FakeSession:
    """Returns a queued/keyed response based on URL substring match."""

    def __init__(self, routes):
        self.routes = routes  # list of (substring, FakeResponse)

    def get(self, url, params=None, timeout=None):
        for sub, resp in self.routes:
            if sub in url:
                return resp
        return FakeResponse({}, status_code=404)


# --------------------------------------------------------------------------- #
# PubChem adapter                                                             #
# --------------------------------------------------------------------------- #
_PUBCHEM_PAYLOAD = {
    "PropertyTable": {
        "Properties": [
            {
                "CID": 3672,
                "IUPACName": "2-[4-(2-methylpropyl)phenyl]propanoic acid",
                "MolecularFormula": "C13H18O2",
                "MolecularWeight": "206.28",
                "CanonicalSMILES": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
                "IsomericSMILES": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
                "InChIKey": "HEFNNWSXXWATRW-UHFFFAOYSA-N",
                "InChI": "InChI=1S/C13H18O2/...",
                "XLogP": 3.5,
                "TPSA": 37.3,
                "HBondDonorCount": 1,
                "HBondAcceptorCount": 2,
                "RotatableBondCount": 4,
            }
        ]
    }
}


def test_pubchem_adapter_parses_identity_and_physchem():
    session = FakeSession([("pubchem", FakeResponse(_PUBCHEM_PAYLOAD))])
    adapter = PubChemAdapter(session=session)
    res = adapter.fetch(drug_name="Ibuprofen")

    assert res.status == SourceStatus.OK
    ident = res.fields[CATEGORY_IDENTITY]
    assert ident["pubchem_cid"].value == 3672
    assert ident["molecular_formula"].value == "C13H18O2"
    assert ident["pubchem_cid"].evidence == Evidence.RECORDED

    phys = res.fields[CATEGORY_PHYSCHEM]
    assert phys["molecular_weight"].value == 206.28
    assert phys["molecular_weight"].unit == "g/mol"
    # XLogP is a computed descriptor -> predicted
    assert phys["xlogp"].evidence == Evidence.PREDICTED


def test_pubchem_adapter_not_found():
    session = FakeSession([("pubchem", FakeResponse({}, status_code=404))])
    res = PubChemAdapter(session=session).fetch(drug_name="Nonexistol")
    assert res.status == SourceStatus.NOT_FOUND


def test_pubchem_adapter_network_error_degrades():
    class BoomSession:
        def get(self, *a, **k):
            raise ConnectionError("no network")

    res = PubChemAdapter(session=BoomSession()).fetch(drug_name="Ibuprofen")
    assert res.status == SourceStatus.ERROR


# --------------------------------------------------------------------------- #
# openFDA adapter                                                             #
# --------------------------------------------------------------------------- #
_DRUGSFDA_PAYLOAD = {
    "results": [
        {
            "application_number": "NDA018989",
            "sponsor_name": "Pharma Co",
            "openfda": {"generic_name": ["IBUPROFEN"]},
            "products": [
                {
                    "brand_name": "MOTRIN",
                    "product_number": "001",
                    "dosage_form": "TABLET",
                    "route": "ORAL",
                    "marketing_status": "Prescription",
                    "active_ingredients": [{"name": "IBUPROFEN", "strength": "600MG"}],
                }
            ],
        }
    ]
}


def test_openfda_adapter_products():
    session = FakeSession([
        ("drugsfda", FakeResponse(_DRUGSFDA_PAYLOAD)),
        ("label", FakeResponse({"results": []})),
    ])
    res = OpenFDAAdapter(session=session).fetch(drug_name="Ibuprofen")

    assert res.status == SourceStatus.OK
    products = res.records[CATEGORY_APPROVED]
    assert any(p.get("brand_name") and p["brand_name"].value == "MOTRIN" for p in products)
    # openFDA no longer emits patents — that's the Orange Book adapter's job
    assert CATEGORY_PATENTS not in res.records


# --------------------------------------------------------------------------- #
# Stubs                                                                       #
# --------------------------------------------------------------------------- #
def test_phase2_stubs_report_unavailable():
    for adapter in (
        stubs.CompToxAdapter(),
        stubs.EMAAdapter(),
        stubs.NmpaCdeAdapter(),
        stubs.PatentsAdapter(),
        stubs.CSDAdapter(),
    ):
        res = adapter.fetch(drug_name="Ibuprofen")
        assert res.status == SourceStatus.SOURCE_UNAVAILABLE
        assert res.message


def test_drugbank_local_adapter_unavailable_without_file():
    from formulation_os.knowledge.sources.drugbank_local import DrugBankLocalAdapter

    res = DrugBankLocalAdapter(db_path="/nonexistent/drugbank.db").fetch(drug_name="Ibuprofen")
    assert res.status == SourceStatus.SOURCE_UNAVAILABLE


# --------------------------------------------------------------------------- #
# Aggregator                                                                  #
# --------------------------------------------------------------------------- #
class _FakeSource(SourceAdapter):
    def __init__(self, name, result):
        self.name = name
        self._result = result

    def fetch(self, drug_name=None, smiles=None, categories=None):
        return self._result


def _pubchem_result():
    r = SourceResult(source="PubChem", status=SourceStatus.OK)
    prov = Provenance(source="PubChem")
    r.add_field(CATEGORY_IDENTITY, "pubchem_cid", FieldValue(3672, None, Evidence.RECORDED, prov))
    r.add_field(CATEGORY_PHYSCHEM, "molecular_weight", FieldValue(206.28, "g/mol", Evidence.RECORDED, prov))
    return r


def _chembl_result_conflict():
    r = SourceResult(source="ChEMBL", status=SourceStatus.OK)
    prov = Provenance(source="ChEMBL")
    # deliberately different MW to trigger a conflict flag
    r.add_field(CATEGORY_PHYSCHEM, "molecular_weight", FieldValue(250.0, "g/mol", Evidence.RECORDED, prov))
    return r


def test_aggregator_merges_and_flags_conflict():
    adapters = {
        "PubChem": _FakeSource("PubChem", _pubchem_result()),
        "ChEMBL": _FakeSource("ChEMBL", _chembl_result_conflict()),
        "EPA CompTox": stubs.CompToxAdapter(),
    }
    agg = DrugIntelligenceAggregator(adapters=adapters)
    profile = agg.build(drug_name="Ibuprofen", categories=[CATEGORY_IDENTITY, CATEGORY_PHYSCHEM])

    # both sources contributed MW -> two FieldValues preserved
    mw = profile.physicochemical["molecular_weight"]
    assert len(mw) == 2
    # conflict flagged (206.28 vs 250)
    assert any(c["field"] == "molecular_weight" for c in profile.conflicts)
    # CompTox stub recorded as unavailable, not crashing
    assert any(s["source"] == "EPA CompTox" for s in profile.sources_unavailable)
    assert "PubChem" in profile.sources_used


def test_unregistered_source_skipped_silently():
    # DrugBank not in adapter set (e.g. public build) -> not reported as unavailable
    adapters = {"PubChem": _FakeSource("PubChem", _pubchem_result())}
    agg = DrugIntelligenceAggregator(adapters=adapters)
    profile = agg.build(drug_name="Ibuprofen", categories=[CATEGORY_IDENTITY])
    assert not any(s["source"] == "DrugBank" for s in profile.sources_unavailable)
    assert "PubChem" in profile.sources_used


def test_primary_source_table_covers_all_categories():
    # routing table must define a primary for every category the tool exposes
    for cat in (CATEGORY_IDENTITY, CATEGORY_PHYSCHEM, CATEGORY_APPROVED, CATEGORY_PATENTS):
        assert cat in PRIMARY_SOURCE
        primary, supplements = PRIMARY_SOURCE[cat]
        assert isinstance(primary, str) and primary
        assert isinstance(supplements, list)
