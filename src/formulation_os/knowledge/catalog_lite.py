"""Lightweight catalog profiles from the local ChEMBL table (zero network).

The 4,225-drug ChEMBL catalog (``chembl_drugs.db``) already holds MW / LogP /
PSA / HBD / HBA / SMILES / InChIKey / predicted BCS for every drug. This turns a
catalog row into a provenance-tagged (identity + physicochemical) profile — no
API calls — so every browsable drug has a *local* card and the web drill-down can
be fully offline. Curated drugs are separately enriched to full depth
(products/patents/CN) by the normal build.
"""

from __future__ import annotations

from typing import Any, Optional

from .sources.schema import (
    CATEGORY_IDENTITY,
    CATEGORY_PHYSCHEM,
    STATUS_RECORD_FOUND,
    Evidence,
    FieldValue,
    Provenance,
    DrugIntelligence,
)

_REF = "https://www.ebi.ac.uk/chembl/"


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return v


def build_lite_profile(row: dict[str, Any]) -> dict[str, Any]:
    """Build a lightweight identity+physicochemical profile from a ChEMBL row."""
    def prov() -> Provenance:
        cid = row.get("chembl_id")
        return Provenance(
            source="ChEMBL",
            reference=f"https://www.ebi.ac.uk/chembl/explore/compound/{cid}" if cid else _REF,
            source_type="local_catalog",
        )

    p = DrugIntelligence(query=row.get("name") or "unknown",
                         preferred_name=row.get("name"))

    ident = {
        "chembl_id": (row.get("chembl_id"), Evidence.RECORDED),
        "preferred_name": (row.get("name"), Evidence.RECORDED),
        "inchikey": (row.get("inchi_key"), Evidence.RECORDED),
        "smiles": (row.get("smiles"), Evidence.RECORDED),
    }
    for f, (v, ev) in ident.items():
        if v not in (None, ""):
            p.identity[f] = [FieldValue(v, None, ev, prov())]

    phys = [
        ("molecular_weight", row.get("molecular_weight"), "g/mol", Evidence.RECORDED),
        ("alogp", row.get("logp"), None, Evidence.PREDICTED),
        ("psa", row.get("psa"), "Å²", Evidence.PREDICTED),
        ("hbd", row.get("hbd"), None, Evidence.RECORDED),
        ("hba", row.get("hba"), None, Evidence.RECORDED),
        ("rotatable_bonds", row.get("rtb"), None, Evidence.RECORDED),
        ("ro5_violations", row.get("num_ro5_violations"), None, Evidence.PREDICTED),
        # predicted BCS (heuristic) — clearly labelled as predicted
        ("bcs_class_predicted", row.get("bcs_class"), None, Evidence.PREDICTED),
    ]
    for f, v, unit, ev in phys:
        if v not in (None, "") and not _isnan(v):
            p.physicochemical[f] = [FieldValue(_num(v) if f != "bcs_class_predicted" else v, unit, ev, prov())]

    p.sources_used = ["ChEMBL"]
    p.category_status = {
        CATEGORY_IDENTITY: STATUS_RECORD_FOUND,
        CATEGORY_PHYSCHEM: STATUS_RECORD_FOUND,
    }
    return p.to_dict()


def _isnan(v) -> bool:
    try:
        return v != v
    except Exception:
        return False
