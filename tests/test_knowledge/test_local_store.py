"""Tests for the offline LocalDrugStore (SQLite, no network)."""

from __future__ import annotations

from formulation_os.knowledge.local_store import LocalDrugStore, resolve_db_path


def _profile():
    return {
        "query": "Ibuprofen",
        "identity": {
            "iupac_name": [{"value": "2-[4-(2-methylpropyl)phenyl]propanoic acid", "evidence": "recorded", "source": "PubChem"}],
            "inchikey": [{"value": "HEFNNWSXXWATRW-UHFFFAOYSA-N", "evidence": "recorded", "source": "PubChem"}],
        },
        "physicochemical": {
            "molecular_weight": [{"value": 206.28, "unit": "g/mol", "evidence": "recorded", "source": "PubChem"}],
        },
        "drug_forms": [],
        "approved_products": [],
        "patents_exclusivity": [],
        "_meta": {"sources_used": ["PubChem"], "sources_unavailable": [], "conflicts": [], "warnings": []},
    }


def test_write_then_get_roundtrip(tmp_path):
    db = tmp_path / "di.db"
    w = LocalDrugStore(str(db), for_write=True)
    w.init_schema()
    w.write("Ibuprofen", _profile(), built_at="2026-01-01")

    r = LocalDrugStore(str(db))
    assert r.available
    got = r.get("Ibuprofen")
    assert got["identity"]["inchikey"][0]["value"] == "HEFNNWSXXWATRW-UHFFFAOYSA-N"
    assert r.stats()["count"] == 1


def test_case_insensitive_and_canonical_lookup(tmp_path):
    db = tmp_path / "di.db"
    w = LocalDrugStore(str(db), for_write=True)
    w.init_schema()
    w.write("Ibuprofen", _profile(), built_at="")

    r = LocalDrugStore(str(db))
    assert r.get("ibuprofen") is not None            # case-insensitive
    assert r.get("Nonexistol") is None


def test_absent_db_is_unavailable(tmp_path):
    r = LocalDrugStore(str(tmp_path / "missing.db"))
    assert not r.available
    assert r.get("Ibuprofen") is None
    assert r.list_drugs() == []


def test_resolve_prefers_local_over_public(tmp_path, monkeypatch):
    import formulation_os.knowledge.local_store as ls

    localdb = tmp_path / "drug_intelligence.local.db"
    publicdb = tmp_path / "drug_intelligence.db"
    localdb.write_text("x")
    publicdb.write_text("y")
    monkeypatch.setattr(
        ls, "_DEFAULT_CANDIDATES", (str(localdb), str(publicdb))
    )
    assert resolve_db_path() == str(localdb)
