"""ChEMBL adapter.

Two layers, both no-key:

* **Local SQLite** (``data/drugbank/chembl_drugs.db``, ~approved drugs) reused
  via the existing :class:`ChEMBLDrugDatabase` — fast, offline, primary path.
* **Live ChEMBL REST** (https://www.ebi.ac.uk/chembl/api/data) for
  ``molecule_form`` (parent / salt relationships) which the local table does
  not store — this makes ChEMBL the primary source for **drug forms**.

Primary for:
  - drug_forms      (parent molecule, salts / alternative forms)
Supplements:
  - identity        (ChEMBL ID, preferred name, InChIKey)
  - physicochemical (alogP, PSA, HBD/HBA, RO5 violations) — computed => PREDICTED
"""

from __future__ import annotations

from typing import Optional

import requests

from .base import SourceAdapter
from .schema import (
    CATEGORY_FORMS,
    CATEGORY_IDENTITY,
    CATEGORY_PHYSCHEM,
    Evidence,
    FieldValue,
    Provenance,
    SourceResult,
)

_LIVE_BASE = "https://www.ebi.ac.uk/chembl/api/data"


class ChEMBLAdapter(SourceAdapter):
    name = "ChEMBL"
    provides = (CATEGORY_FORMS, CATEGORY_IDENTITY, CATEGORY_PHYSCHEM)

    def __init__(
        self,
        db_path: str = "data/drugbank/chembl_drugs.db",
        use_live_forms: bool = True,
        timeout: int = 10,
        session: Optional[requests.Session] = None,
    ):
        self.db_path = db_path
        self.use_live_forms = use_live_forms
        self.timeout = timeout
        self.session = session or requests

    def _local(self, drug_name: str) -> Optional[dict]:
        try:
            from formulation_os.knowledge.chembl_database import ChEMBLDrugDatabase
        except Exception:
            return None
        try:
            db = ChEMBLDrugDatabase(self.db_path)
            row = db.get_drug_by_name(drug_name)
            if row:
                return row
            df = db.search_drugs(drug_name, limit=1)
            if not df.empty:
                return df.iloc[0].to_dict()
        except Exception:
            return None
        return None

    def fetch(self, drug_name=None, smiles=None, categories=None) -> SourceResult:
        if not drug_name:
            return self._not_found("ChEMBL adapter requires drug_name")

        row = self._local(drug_name)
        if row is None:
            # Local miss is not fatal — forms may still come from live API.
            result = self._ok()
            found_any = False
        else:
            result = self._ok()
            found_any = True
            chembl_id = row.get("chembl_id")
            ref = (
                f"https://www.ebi.ac.uk/chembl/explore/compound/{chembl_id}"
                if chembl_id else None
            )
            prov = Provenance(source=self.name, reference=ref)

            ident = {
                "chembl_id": (row.get("chembl_id"), Evidence.RECORDED),
                "preferred_name": (row.get("name"), Evidence.RECORDED),
                "inchikey": (row.get("inchi_key"), Evidence.RECORDED),
                "smiles": (row.get("smiles"), Evidence.RECORDED),
            }
            for fname, (val, ev) in ident.items():
                if val is not None:
                    result.add_field(CATEGORY_IDENTITY, fname, FieldValue(val, None, ev, prov))

            phys = [
                ("molecular_weight", row.get("molecular_weight"), "g/mol", Evidence.RECORDED),
                ("alogp", row.get("logp"), None, Evidence.PREDICTED),
                ("psa", row.get("psa"), "Å²", Evidence.PREDICTED),
                ("hbd", row.get("hbd"), None, Evidence.RECORDED),
                ("hba", row.get("hba"), None, Evidence.RECORDED),
                ("ro5_violations", row.get("num_ro5_violations"), None, Evidence.PREDICTED),
            ]
            for fname, val, unit, ev in phys:
                if val is not None and not _isnan(val):
                    result.add_field(CATEGORY_PHYSCHEM, fname, FieldValue(_num(val), unit, ev, prov))

        # -- drug forms via live API (parent / salt relationships) ------------
        if self.use_live_forms:
            self._fetch_forms(drug_name, result)
            found_any = found_any or bool(result.records.get(CATEGORY_FORMS))

        if not found_any:
            return self._not_found()
        return result

    def _fetch_forms(self, drug_name: str, result: SourceResult) -> None:
        """Look up molecule_form (parent + salts) from live ChEMBL."""
        try:
            url = f"{_LIVE_BASE}/molecule/search"
            resp = self.session.get(
                url, params={"q": drug_name, "format": "json"}, timeout=self.timeout
            )
            if resp.status_code != 200:
                return
            molecules = resp.json().get("molecules", [])
            if not molecules:
                return
            chembl_id = molecules[0].get("molecule_chembl_id")
            if not chembl_id:
                return

            form_url = f"{_LIVE_BASE}/molecule_form/{chembl_id}"
            fresp = self.session.get(form_url, params={"format": "json"}, timeout=self.timeout)
            if fresp.status_code != 200:
                return
            forms = fresp.json().get("molecule_forms", [])
            for f in forms:
                fid = f.get("molecule_chembl_id")
                ref = f"https://www.ebi.ac.uk/chembl/explore/compound/{fid}" if fid else None
                prov = Provenance(source=self.name, reference=ref)
                record = {
                    "chembl_id": FieldValue(fid, None, Evidence.RECORDED, prov),
                    "is_parent": FieldValue(
                        f.get("is_parent"), None, Evidence.RECORDED, prov
                    ),
                }
                result.add_record(CATEGORY_FORMS, record)
        except Exception:
            return  # forms are best-effort


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return v


def _isnan(v) -> bool:
    try:
        return v != v  # NaN check without importing math
    except Exception:
        return False
