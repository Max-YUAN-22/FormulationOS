"""Tests for the LLM digest formatter and the lookup_drug_intelligence dispatch."""

from __future__ import annotations

from formulation_os.knowledge.llm_digest import digest_profile


def _profile():
    return {
        "query": "Atorvastatin",
        "preferred_name": "Atorvastatin",
        "identity": {
            "chembl_id": [{"value": "CHEMBL393220", "source": "ChEMBL"}],
            "drugbank_id": [{"value": "DB01076", "source": "DrugBank"}],
            "molecular_formula": [{"value": "C33H35FN2O5", "source": "PubChem"}],
        },
        "physicochemical": {
            "molecular_weight": [{"value": 558.6, "unit": "g/mol", "source": "PubChem"}],
            "pka_strongest_acidic": [{"value": 4.31, "source": "DrugBank"}],
        },
        "drug_forms": [{"a": {"value": 1}}],
        "approved_products": [
            {"region": {"value": "US"}, "brand_name": {"value": "LIPITOR"},
             "dosage_form": {"value": "TABLET"}},
            {"region": {"value": "CN"}, "drug_name": {"value": "阿托伐他汀钙片"},
             "mah": {"value": "Pfizer"}},
        ],
        "patents_exclusivity": [
            {"type": {"value": "patent"}, "patent_number": {"value": "11654106"},
             "patent_expire_date": {"value": "Jun 7, 2037"}},
            {"type": {"value": "patent"}, "patent_number": {"value": "11654106"},
             "patent_expire_date": {"value": "Jun 7, 2037"}},  # duplicate row
            {"type": {"value": "regulatory_exclusivity"}, "exclusivity_code": {"value": "NCE"},
             "exclusivity_expiration_date": {"value": "2029-01-01"}},
        ],
        "_meta": {
            "sources_used": ["PubChem", "DrugBank", "openFDA (FDA)"],
            "category_status": {"identity": "record_found"},
            "entity_mismatches": [{
                "field": "molecular_weight",
                "forms": [{"value": 558.6, "source": "PubChem"},
                          {"value": 1155.36, "source": "ChEMBL"}],
            }],
        },
    }


def test_digest_contains_key_sections():
    d = digest_profile(_profile())
    assert "DRUG INTELLIGENCE — Atorvastatin" in d
    assert "IDENTITY:" in d and "CHEMBL393220" in d
    assert "PHYSICOCHEMICAL:" in d and "558.6 g/mol" in d and "pka_strongest_acidic=4.31" in d
    assert "US MARKETED: 1" in d and "LIPITOR" in d
    assert "CN REFERENCE" in d and "阿托伐他汀钙片" in d
    assert "PATENTS: 1 unique" in d            # duplicates collapsed
    assert "latest expiry Jun 7, 2037" in d
    assert "EXCLUSIVITY: NCE" in d
    assert "FORM NOTE" in d and "558.6" in d and "1155.36" in d
    assert "SOURCES: PubChem" in d


def test_digest_empty_profile():
    assert digest_profile(None) == "No drug-intelligence record found."
    assert "record" in digest_profile({}).lower()


def test_dispatch_lookup_drug_intelligence(monkeypatch, tmp_path):
    from formulation_os.agent.unified_llm_manager import UnifiedLLMManager

    class _Store:
        def __init__(self, p):
            self._p = p
        def get(self, name):
            return self._p

    prof = _profile()
    import formulation_os.knowledge.local_store as ls
    monkeypatch.setattr(ls, "LocalDrugStore", lambda *a, **k: _Store(prof))

    mgr = UnifiedLLMManager.__new__(UnifiedLLMManager)  # skip __init__ (LLM keys)
    out = mgr.execute_tool_call("lookup_drug_intelligence", {"drug_name": "Atorvastatin"})
    assert "digest" in out
    assert "Atorvastatin" in out["digest"]


def test_dispatch_not_found(monkeypatch):
    from formulation_os.agent.unified_llm_manager import UnifiedLLMManager

    class _Store:
        def __init__(self, p):
            self._p = p
        def get(self, name):
            return self._p

    import formulation_os.knowledge.local_store as ls
    monkeypatch.setattr(ls, "LocalDrugStore", lambda *a, **k: _Store(None))

    mgr = UnifiedLLMManager.__new__(UnifiedLLMManager)
    out = mgr.execute_tool_call("lookup_drug_intelligence", {"drug_name": "Nonexistol"})
    assert out.get("error") == "not_found"
