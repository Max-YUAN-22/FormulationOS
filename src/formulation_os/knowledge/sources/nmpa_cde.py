"""NMPA/CDE adapter — China marketed products (local DB, no network).

Reads the local ``data/nmpa_cde/nmpa_cde.db`` built offline by
``scripts/import_cn_drug_catalog.py`` from a third-party compilation of the CDE
《中国上市药品目录集》 / 参比制剂目录.

Licence: third-party compilation, treated as non-redistributable -> the DB is
local-only (git-ignored) and only included in the ``local`` build profile, never
the public/deployed one. If the DB is absent -> source_unavailable.

Provides:
  - approved_products (④, region=CN): drug/API names, dosage form, route,
    strength, approval number, MAH, manufacturer, marketing status, catalog
    category, consistency-evaluation status, and reference-product info under the
    unified reference model (region/authority/reference_role).

Matching to the existing (English-keyed) profiles is done on the English active
ingredient / drug name via candidate names passed by the aggregator (which has
already run DrugResolver). Salt/form-specific Chinese names are NOT collapsed
into the parent — a hydrochloride row stays a hydrochloride row.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from .base import SourceAdapter
from .schema import (
    CATEGORY_APPROVED,
    REF_ROLE_CN_REFERENCE_PREPARATION,
    Evidence,
    FieldValue,
    Provenance,
    SourceResult,
)

_DEFAULT_DB = "data/nmpa_cde/nmpa_cde.db"
_OFFICIAL_REF = "https://www.cde.org.cn/hymlj/"

# Fields copied straight through onto each CN product record.
_PASSTHROUGH = [
    "drug_name", "drug_name_en", "trade_name", "trade_name_en",
    "active_ingredient", "active_ingredient_en", "dosage_form", "route",
    "strength", "approval_number", "mah", "manufacturer",
    "first_approval_date", "marketing_status", "catalog_category",
    "consistency_evaluation_status", "te_code", "atc_code",
]


class NmpaCdeAdapter(SourceAdapter):
    name = "NMPA/CDE (China)"
    provides = (CATEGORY_APPROVED,)

    def __init__(self, db_path: str = _DEFAULT_DB, max_products: int = 50):
        self.db_path = db_path
        self.max_products = max_products

    def fetch(self, drug_name=None, smiles=None, categories=None) -> SourceResult:
        if not Path(self.db_path).exists():
            return self._unavailable(
                f"China catalog DB not found at {self.db_path}. Run "
                f"scripts/import_cn_drug_catalog.py / import_cn_reference_products.py "
                f"(local, non-redistributable)."
            )
        if not drug_name:
            return self._not_found("NMPA/CDE adapter requires drug_name")

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            result = self._ok()
            found = False
            found |= self._marketed(conn, drug_name, result)
            found |= self._reference(conn, drug_name, result)
            conn.close()
        except Exception as exc:
            return self._error(str(exc))

        return result if found else self._not_found()

    def _marketed(self, conn, drug_name, result) -> bool:
        """Registration base records (marketed_products), if that table exists."""
        if not _table_exists(conn, "marketed_products"):
            return False
        cur = conn.cursor()
        rows = cur.execute(
            """
            SELECT * FROM marketed_products
            WHERE active_ingredient_en = ? COLLATE NOCASE
               OR drug_name_en = ? COLLATE NOCASE
            LIMIT ?
            """,
            (drug_name, drug_name, self.max_products),
        ).fetchall()
        if not rows:
            rows = cur.execute(
                "SELECT * FROM marketed_products WHERE active_ingredient_en LIKE ? COLLATE NOCASE LIMIT ?",
                (f"%{drug_name}%", self.max_products),
            ).fetchall()
        for row in rows:
            prov = self._provenance(row)
            rec: dict[str, FieldValue] = {"region": FieldValue("CN", None, Evidence.RECORDED, prov)}
            for f in _PASSTHROUGH:
                val = _get(row, f)
                if val not in (None, ""):
                    rec[f] = FieldValue(val, None, Evidence.RECORDED, prov)
            if _get(row, "reference_preparation"):
                rec["reference_preparation"] = FieldValue(
                    _get(row, "reference_preparation"), None, Evidence.RECORDED, prov)
            result.add_record(CATEGORY_APPROVED, rec)
        return bool(rows)

    def _reference(self, conn, drug_name, result) -> bool:
        """Reference-preparation records (参比制剂), if that table exists.

        Matched on the English product name containing the drug (a reference
        product 'Atorvastatin Calcium Tablets' is a legitimate CN reference for
        Atorvastatin — it is recorded as its own product, not merged to parent).
        """
        if not _table_exists(conn, "reference_products"):
            return False
        rows = conn.execute(
            "SELECT * FROM reference_products WHERE drug_name_en LIKE ? COLLATE NOCASE LIMIT ?",
            (f"%{drug_name}%", self.max_products),
        ).fetchall()
        for row in rows:
            prov = self._provenance(row)
            rec: dict[str, FieldValue] = {
                "region": FieldValue("CN", None, Evidence.RECORDED, prov),
                "is_reference_preparation": FieldValue(True, None, Evidence.RECORDED, prov),
                "reference_role": FieldValue(REF_ROLE_CN_REFERENCE_PREPARATION, None, Evidence.RECORDED, prov),
                "reference_region": FieldValue("CN", None, Evidence.RECORDED, prov),
                "reference_authority": FieldValue("CDE", None, Evidence.RECORDED, prov),
            }
            for src_field, dst in (
                ("drug_name", "drug_name"), ("drug_name_en", "drug_name_en"),
                ("trade_name", "trade_name"), ("strength", "strength"),
                ("dosage_form", "dosage_form"), ("holder", "mah"),
                ("reference_status", "reference_status"), ("note", "note"),
                ("batch", "reference_batch"), ("seq", "reference_seq"),
            ):
                val = _get(row, src_field)
                if val not in (None, ""):
                    rec[dst] = FieldValue(val, None, Evidence.RECORDED, prov)
            result.add_record(CATEGORY_APPROVED, rec)
        return bool(rows)

    def _provenance(self, row) -> Provenance:
        return Provenance(
            source=self.name,
            authority=_get(row, "authority") or "NMPA/CDE",
            source_type=_get(row, "source_type") or "third_party_compilation",
            source_provider=_get(row, "source_provider"),
            source_file=_get(row, "source_file"),
            snapshot_date=_get(row, "snapshot_date"),
            official_reference=_get(row, "official_reference") or _OFFICIAL_REF,
            ingested_at=_get(row, "ingested_at"),
        )


def _get(row, key):
    try:
        return row[key]
    except (IndexError, KeyError):
        return None


def _table_exists(conn, name: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None
