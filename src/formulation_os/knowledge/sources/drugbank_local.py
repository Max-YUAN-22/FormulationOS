"""DrugBank adapter — LOCAL file only, optional supplement / cross-validation.

Reads the DrugBank full database that has been parsed into SQLite by
``scripts/parse_drugbank_xml.py`` (table ``drugs``). This is a **local file
read**, never a network call, so it fits the offline architecture.

Licence note: the DrugBank full database is licence-restricted and must not be
redistributed. Therefore:
  * this adapter is used at BUILD time only, on your machine;
  * its data goes into ``data/drug_intelligence.local.db`` (git-ignored), never
    into the committed / deployed ``data/drug_intelligence.db``;
  * if the parsed DrugBank DB is absent, it degrades to ``source_unavailable``.

High-value contribution vs the free sources: **pKa (acidic/basic)** and
**logS** — computed physicochemical values that PubChem/ChEMBL do not expose
cleanly, and which matter a lot for formulation. All DrugBank calculated
properties are model-derived, so they are tagged ``PREDICTED``.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from .base import SourceAdapter
from .schema import (
    CATEGORY_IDENTITY,
    CATEGORY_PHYSCHEM,
    Evidence,
    FieldValue,
    Provenance,
    SourceResult,
)

_DEFAULT_DB = "data/drugbank/drugbank.db"


class DrugBankLocalAdapter(SourceAdapter):
    name = "DrugBank"
    provides = (CATEGORY_IDENTITY, CATEGORY_PHYSCHEM)

    def __init__(self, db_path: str = _DEFAULT_DB):
        self.db_path = db_path

    def fetch(self, drug_name=None, smiles=None, categories=None) -> SourceResult:
        if not Path(self.db_path).exists():
            return self._unavailable(
                f"Parsed DrugBank DB not found at {self.db_path}. Run "
                f"scripts/parse_drugbank_xml.py (local, licence-restricted)."
            )
        if not drug_name:
            return self._not_found("DrugBank adapter requires drug_name")

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM drugs WHERE name = ? COLLATE NOCASE", (drug_name,))
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    "SELECT * FROM drugs WHERE name LIKE ? COLLATE NOCASE LIMIT 1",
                    (f"%{drug_name}%",),
                )
                row = cur.fetchone()
            conn.close()
        except Exception as exc:
            return self._error(str(exc))

        if row is None:
            return self._not_found()

        dbid = _get(row, "drugbank_id")
        ref = f"https://go.drugbank.com/drugs/{dbid}" if dbid else None
        prov = Provenance(source=self.name, reference=ref)
        result = self._ok()

        # -- identity (RECORDED) ---------------------------------------------
        identity = {
            "drugbank_id": dbid,
            "cas_number": _get(row, "cas_number"),
            "unii": _get(row, "unii"),
            "inchikey": _get(row, "inchikey"),
            "smiles": _get(row, "smiles"),
            "molecular_formula": _get(row, "molecular_formula"),
        }
        for fname, val in identity.items():
            if val not in (None, ""):
                result.add_field(CATEGORY_IDENTITY, fname, FieldValue(val, None, Evidence.RECORDED, prov))

        # -- physicochemical -------------------------------------------------
        # MW recorded; the rest are ChemAxon calculated => PREDICTED. pKa & logS
        # are DrugBank's headline contribution here.
        phys = [
            ("molecular_weight", _get(row, "molecular_weight"), "g/mol", Evidence.RECORDED),
            ("logp", _get(row, "logp"), None, Evidence.PREDICTED),
            ("logs", _get(row, "logs"), None, Evidence.PREDICTED),
            ("pka_strongest_acidic", _get(row, "pka_strongest_acidic"), None, Evidence.PREDICTED),
            ("pka_strongest_basic", _get(row, "pka_strongest_basic"), None, Evidence.PREDICTED),
            ("psa", _get(row, "polar_surface_area"), "Å²", Evidence.PREDICTED),
            ("hbd", _get(row, "h_bond_donor_count"), None, Evidence.RECORDED),
            ("hba", _get(row, "h_bond_acceptor_count"), None, Evidence.RECORDED),
            ("rotatable_bonds", _get(row, "rotatable_bond_count"), None, Evidence.RECORDED),
        ]
        for fname, val, unit, ev in phys:
            if val not in (None, ""):
                result.add_field(CATEGORY_PHYSCHEM, fname, FieldValue(_num(val), unit, ev, prov))

        return result


def _get(row, key):
    try:
        return row[key]
    except (IndexError, KeyError):
        return None


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return v
