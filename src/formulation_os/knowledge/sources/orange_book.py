"""FDA Orange Book adapter — primary source for US patents & exclusivity.

Reads the LOCAL Orange Book DB built by ``scripts/fetch_orange_book.py`` (no
network at query time). Provides:

  - patents_exclusivity (⑤, primary): patent and exclusivity records, kept
    SEPARATE, joined to products by (appl_no, product_no).
  - approved_products (④, supplement): OB product rows carry RLD / Reference
    Standard / TE code that Drugs@FDA does not.

Three-state semantics: if the OB DB is missing -> source_unavailable; if present
but the drug has no OB entry -> not_found (=> no_record); otherwise ok.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .base import SourceAdapter
from .schema import (
    CATEGORY_APPROVED,
    CATEGORY_PATENTS,
    Evidence,
    FieldValue,
    Provenance,
    SourceResult,
)

_DEFAULT_DB = "data/orange_book/orange_book.db"
_REF = "https://www.accessdata.fda.gov/scripts/cder/ob/"


class OrangeBookAdapter(SourceAdapter):
    name = "FDA Orange Book"
    provides = (CATEGORY_PATENTS, CATEGORY_APPROVED)

    def __init__(self, db_path: str = _DEFAULT_DB, max_products: int = 25):
        self.db_path = db_path
        self.max_products = max_products

    def fetch(self, drug_name=None, smiles=None, categories=None) -> SourceResult:
        if not Path(self.db_path).exists():
            return self._unavailable(
                f"Orange Book DB not found at {self.db_path}. Run "
                f"scripts/fetch_orange_book.py."
            )
        if not drug_name:
            return self._not_found("Orange Book adapter requires drug_name")

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            # Match by active ingredient (OB stores UPPERCASE, may be combos).
            cur.execute(
                "SELECT * FROM products WHERE UPPER(ingredient) LIKE ? LIMIT ?",
                (f"%{drug_name.upper()}%", self.max_products),
            )
            products = cur.fetchall()
            if not products:
                conn.close()
                return self._not_found()

            result = self._ok()
            prov = Provenance(source=self.name, reference=_REF)
            appl_keys: set[tuple[str, str]] = set()

            # -- approved products (④ supplement: adds RLD/RS/TE) -------------
            for p in products:
                appl_no = p["appl_no"]
                product_no = p["product_no"]
                appl_keys.add((appl_no, product_no))
                rec = {}
                _put(rec, "trade_name", p["trade_name"], prov)
                _put(rec, "ingredient", p["ingredient"], prov)
                _put(rec, "dosage_form_route", p["df_route"], prov)
                _put(rec, "strength", p["strength"], prov)
                _put(rec, "applicant", p["applicant_full_name"] or p["applicant"], prov)
                _put(rec, "application_number", f"{p['appl_type']}{appl_no}", prov)
                _put(rec, "product_number", product_no, prov)
                _put(rec, "te_code", p["te_code"], prov)
                _put(rec, "reference_listed_drug", p["rld"], prov)
                _put(rec, "reference_standard", p["rs"], prov)
                _put(rec, "approval_date", p["approval_date"], prov)
                if rec:
                    result.add_record(CATEGORY_APPROVED, rec)

            # -- patents (⑤) — separate records --------------------------------
            for (appl_no, product_no) in appl_keys:
                cur.execute(
                    "SELECT * FROM patents WHERE appl_no = ? AND product_no = ?",
                    (appl_no, product_no),
                )
                for pat in cur.fetchall():
                    rec = {}
                    _put(rec, "type", "patent", prov)
                    _put(rec, "application_number", f"{pat['appl_type']}{appl_no}", prov)
                    _put(rec, "product_number", product_no, prov)
                    _put(rec, "patent_number", pat["patent_no"], prov)
                    _put(rec, "patent_expire_date", pat["patent_expire_date"], prov)
                    _put(rec, "drug_substance_flag", pat["drug_substance_flag"], prov)
                    _put(rec, "drug_product_flag", pat["drug_product_flag"], prov)
                    _put(rec, "patent_use_code", pat["patent_use_code"], prov)
                    if rec:
                        result.add_record(CATEGORY_PATENTS, rec)

            # -- exclusivity (⑤) — SEPARATE from patents -----------------------
            for (appl_no, product_no) in appl_keys:
                cur.execute(
                    "SELECT * FROM exclusivity WHERE appl_no = ? AND product_no = ?",
                    (appl_no, product_no),
                )
                for exc in cur.fetchall():
                    rec = {}
                    _put(rec, "type", "regulatory_exclusivity", prov)
                    _put(rec, "application_number", f"{exc['appl_type']}{appl_no}", prov)
                    _put(rec, "product_number", product_no, prov)
                    _put(rec, "exclusivity_code", exc["exclusivity_code"], prov)
                    _put(rec, "exclusivity_expiration_date", exc["exclusivity_date"], prov)
                    if rec:
                        result.add_record(CATEGORY_PATENTS, rec)

            conn.close()
            return result
        except Exception as exc:
            return self._error(str(exc))


def _put(rec: dict, name: str, value, prov: Provenance) -> None:
    if value not in (None, ""):
        rec[name] = FieldValue(value, None, Evidence.RECORDED, prov)
