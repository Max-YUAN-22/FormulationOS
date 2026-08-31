"""Tests for synonym resolution and entity/form-mismatch detection."""

from __future__ import annotations

from formulation_os.knowledge.drug_synonyms import DrugResolver
from formulation_os.knowledge.drug_intelligence import DrugIntelligenceAggregator
from formulation_os.knowledge.sources.base import SourceAdapter
from formulation_os.knowledge.sources.schema import (
    CATEGORY_IDENTITY,
    CATEGORY_PATENTS,
    CATEGORY_PHYSCHEM,
    STATUS_NO_RECORD,
    STATUS_RECORD_FOUND,
    STATUS_SOURCE_UNAVAILABLE,
    Evidence,
    FieldValue,
    Provenance,
    SourceResult,
    SourceStatus,
)


# --------------------------------------------------------------------------- #
# Synonym resolution                                                          #
# --------------------------------------------------------------------------- #
def test_resolver_maps_inn_to_usan():
    r = DrugResolver()
    res = r.resolve("Paracetamol")
    assert res.preferred_name == "Acetaminophen"
    assert "Acetaminophen" in res.candidates
    assert "Paracetamol" in res.candidates  # queried name tried first

    res2 = r.resolve("Glibenclamide")
    assert res2.preferred_name == "Glyburide"


def test_resolver_unknown_name_passthrough():
    r = DrugResolver()
    res = r.resolve("Ibuprofen")
    assert res.preferred_name == "Ibuprofen"
    assert res.candidates == ["Ibuprofen"]


class _NameGatedSource(SourceAdapter):
    """OK only when queried with a specific (US) name — models openFDA/DrugBank."""

    def __init__(self, name, accepts, result):
        self.name = name
        self._accepts = accepts
        self._result = result

    def fetch(self, drug_name=None, smiles=None, categories=None):
        if drug_name == self._accepts:
            return self._result
        return SourceResult(source=self.name, status=SourceStatus.NOT_FOUND)


def test_aggregator_uses_synonyms_to_hit_us_only_source():
    ok = SourceResult(source="PubChem", status=SourceStatus.OK)
    ok.add_field(CATEGORY_IDENTITY, "pubchem_cid", FieldValue(1983, None, Evidence.RECORDED, Provenance("PubChem")))
    # source only answers to "Acetaminophen", user queries "Paracetamol"
    adapters = {"PubChem": _NameGatedSource("PubChem", "Acetaminophen", ok)}
    agg = DrugIntelligenceAggregator(adapters=adapters)
    profile = agg.build(drug_name="Paracetamol", categories=[CATEGORY_IDENTITY])
    assert "PubChem" in profile.sources_used
    assert profile.preferred_name == "Acetaminophen"


# --------------------------------------------------------------------------- #
# Entity / form mismatch vs true conflict                                     #
# --------------------------------------------------------------------------- #
class _Fake(SourceAdapter):
    def __init__(self, name, result):
        self.name = name
        self._result = result

    def fetch(self, drug_name=None, smiles=None, categories=None):
        return self._result


def _src(name, inchikey, mw):
    r = SourceResult(source=name, status=SourceStatus.OK)
    prov = Provenance(source=name)
    r.add_field(CATEGORY_IDENTITY, "inchikey", FieldValue(inchikey, None, Evidence.RECORDED, prov))
    r.add_field(CATEGORY_PHYSCHEM, "molecular_weight", FieldValue(mw, "g/mol", Evidence.RECORDED, prov))
    return r


def test_different_entity_is_form_mismatch_not_conflict():
    # free acid (558.6) vs calcium salt (1155) with different InChIKeys
    adapters = {
        "PubChem": _Fake("PubChem", _src("PubChem", "XUKUURHRXDUEBC-KAYWLYCHSA-N", 558.6)),
        "ChEMBL": _Fake("ChEMBL", _src("ChEMBL", "MECIMKYWSBFRDS-NALSBCIISA-L", 1155.36)),
    }
    agg = DrugIntelligenceAggregator(adapters=adapters)
    profile = agg.build(drug_name="Atorvastatin", categories=[CATEGORY_IDENTITY, CATEGORY_PHYSCHEM])
    assert profile.entity_mismatches, "should flag entity/form mismatch"
    assert not profile.conflicts, "should NOT be a plain conflict"
    # both forms captured under drug_forms
    assert len(profile.drug_forms) >= 2


def test_same_entity_value_difference_is_conflict():
    # same InChIKey, MW differs beyond tolerance -> genuine conflict
    adapters = {
        "PubChem": _Fake("PubChem", _src("PubChem", "SAMEKEY-AAAAAAAAAA-N", 300.0)),
        "ChEMBL": _Fake("ChEMBL", _src("ChEMBL", "SAMEKEY-AAAAAAAAAA-N", 360.0)),
    }
    agg = DrugIntelligenceAggregator(adapters=adapters)
    profile = agg.build(drug_name="X", categories=[CATEGORY_IDENTITY, CATEGORY_PHYSCHEM])
    assert profile.conflicts
    assert not profile.entity_mismatches


# --------------------------------------------------------------------------- #
# Three-state category status                                                 #
# --------------------------------------------------------------------------- #
def test_three_state_category_status():
    # PubChem OK for identity/physchem.
    ok = SourceResult(source="PubChem", status=SourceStatus.OK)
    ok.add_field(CATEGORY_IDENTITY, "pubchem_cid", FieldValue(1, None, Evidence.RECORDED, Provenance("PubChem")))
    # openFDA reachable but nothing for this drug -> approved_products no_record
    fda_empty = SourceResult(source="openFDA (FDA)", status=SourceStatus.NOT_FOUND)
    # Orange Book reachable but no OB entry -> patents no_record
    ob_empty = SourceResult(source="FDA Orange Book", status=SourceStatus.NOT_FOUND)
    adapters = {
        "PubChem": _Fake("PubChem", ok),
        "openFDA (FDA)": _Fake("openFDA (FDA)", fda_empty),
        "FDA Orange Book": _Fake("FDA Orange Book", ob_empty),
    }
    agg = DrugIntelligenceAggregator(adapters=adapters)
    profile = agg.build(drug_name="X")
    assert profile.category_status[CATEGORY_IDENTITY] == STATUS_RECORD_FOUND
    assert profile.category_status["approved_products"] == STATUS_NO_RECORD
    assert profile.category_status[CATEGORY_PATENTS] == STATUS_NO_RECORD


def test_patents_source_unavailable_when_orange_book_absent():
    ok = SourceResult(source="PubChem", status=SourceStatus.OK)
    ok.add_field(CATEGORY_IDENTITY, "pubchem_cid", FieldValue(1, None, Evidence.RECORDED, Provenance("PubChem")))
    # Orange Book adapter not registered at all -> patents source_unavailable
    agg = DrugIntelligenceAggregator(adapters={"PubChem": _Fake("PubChem", ok)})
    profile = agg.build(drug_name="X", categories=[CATEGORY_PATENTS])
    assert profile.category_status[CATEGORY_PATENTS] == STATUS_SOURCE_UNAVAILABLE
