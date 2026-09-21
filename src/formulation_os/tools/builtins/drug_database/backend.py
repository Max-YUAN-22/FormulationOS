"""Drug Database Query Tool — local-only runtime.

Queries a pre-built, offline drug-intelligence store (SQLite). **No network
access happens at query time** — live API calls would make the service slow and
unreliable, so all data is ingested offline by
``scripts/build_drug_intelligence.py`` and only read from here.

Each category of information keeps its designated primary source + supplements
(recorded as provenance inside the stored profile):

    identity/physicochemical -> PubChem (primary) + ChEMBL (+ DrugBank, local only)
    drug_forms               -> ChEMBL (primary) + DrugBank (local only) + CSD*
    approved_products        -> FDA openFDA + DailyMed (+ EMA*, NMPA/CDE*)
    patents_exclusivity      -> FDA Orange Book (+ USPTO/EPO/WIPO/CNIPA*)

(* = phase-2, not yet ingested.)
"""

from __future__ import annotations

from typing import Any

from formulation_os.knowledge.local_store import LocalDrugStore
from formulation_os.knowledge.sources.schema import (
    ALL_CATEGORIES,
    CATEGORY_APPROVED,
    CATEGORY_FORMS,
    CATEGORY_IDENTITY,
    CATEGORY_IN_VIVO,
    CATEGORY_PATENTS,
    CATEGORY_PHYSCHEM,
    CATEGORY_SOLID_STATE,
    SCALAR_CATEGORIES,
)

# Map the tool's query_type values to profile categories.
_QUERY_MAP = {
    "identity": [CATEGORY_IDENTITY],
    "properties": [CATEGORY_IDENTITY, CATEGORY_PHYSCHEM],
    "physicochemical": [CATEGORY_PHYSCHEM],
    "forms": [CATEGORY_FORMS],
    "approved_products": [CATEGORY_APPROVED],
    "patents": [CATEGORY_PATENTS],
    "in_vivo": [CATEGORY_IN_VIVO],
    "solid_state": [CATEGORY_SOLID_STATE],
    "all": ALL_CATEGORIES,
}

# Legacy query types kept for backwards compatibility (previously mock-only).
_LEGACY = {"targets", "indications", "interactions"}

_store: LocalDrugStore | None = None


def _get_store() -> LocalDrugStore:
    global _store
    if _store is None:
        _store = LocalDrugStore()
    return _store


def run(input_data: dict[str, Any]) -> dict[str, Any]:
    """Query the local drug-intelligence store (offline).

    Args:
        input_data:
            - drug_name: str   (required)
            - query_type: str  identity | properties | physicochemical | forms |
                               approved_products | patents | all
                               (default: properties)

    Returns:
        Provenance-aware drug intelligence for the requested categories, filtered
        from the pre-built local profile. Every value carries its source and
        whether it is experimental / predicted / recorded.
    """
    drug_name = input_data.get("drug_name")
    query_type = input_data.get("query_type", "properties")

    if not drug_name:
        return {"error": "drug_name is required", "warnings": ["No query target provided."]}

    if query_type in _LEGACY:
        return {
            "drug_name": drug_name,
            "query_type": query_type,
            "results": [],
            "warnings": [
                f"'{query_type}' is not served by the drug database "
                f"(it covers identity/properties/forms/approved_products/patents)."
            ],
        }

    categories = _QUERY_MAP.get(query_type, _QUERY_MAP["properties"])

    store = _get_store()
    if not store.available:
        return {
            "drug_name": drug_name,
            "error": "local_store_missing",
            "warnings": [
                "Local drug-intelligence database not found. Build it offline: "
                "`python scripts/build_drug_intelligence.py`."
            ],
        }

    profile = store.get(drug_name)
    if profile is None:
        return {
            "drug_name": drug_name,
            "error": "not_found",
            "warnings": [
                f"'{drug_name}' is not in the local database yet. Add it to the "
                f"curated list and rebuild: `python scripts/build_drug_intelligence.py`.",
                f"Currently {store.stats().get('count', 0)} drugs are available.",
            ],
        }

    # Filter the stored profile down to the requested categories.
    out: dict[str, Any] = {"query": profile.get("query", drug_name)}
    for cat in categories:
        out[cat] = profile.get(cat, {} if cat in SCALAR_CATEGORIES else [])
    out["_meta"] = profile.get("_meta", {})

    meta = out["_meta"]
    used = meta.get("sources_used", [])
    unavailable = [s.get("source") for s in meta.get("sources_unavailable", [])]
    bits = [f"Sources: {', '.join(used) or 'none'}"]
    if unavailable:
        bits.append(f"Not yet ingested: {', '.join(unavailable)}")
    if meta.get("conflicts"):
        bits.append(f"{len(meta['conflicts'])} cross-source conflict(s) flagged")
    out["summary"] = " | ".join(bits)
    return out
