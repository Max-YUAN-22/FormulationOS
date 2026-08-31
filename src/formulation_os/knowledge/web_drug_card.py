"""Web drill-down data provider for the Drug Intelligence card.

Reads the pre-built LocalDrugStore ONLY — **zero network at runtime**. The whole
ChEMBL catalog is pre-built offline: every drug has at least a lightweight
identity+physicochemical profile (from the local ChEMBL table), and curated
drugs additionally carry full depth (US/CN products, patents; DrugBank/CN only
in the local build). See scripts/prebuild_catalog_lite.py + build_drug_intelligence.py.
"""

from __future__ import annotations

from typing import Any, Optional

from .local_store import LocalDrugStore

_CACHE: dict[str, Optional[dict[str, Any]]] = {}


def get_drug_card(name: str, allow_live: bool = False) -> Optional[dict[str, Any]]:
    """Return a pre-built drug-intelligence profile for the web card, or None.

    Local store only (no network). ``allow_live`` is retained for API
    compatibility but ignored — the catalog is pre-built offline.
    """
    if not name:
        return None
    key = name.strip().lower()
    if key in _CACHE:
        return _CACHE[key]
    profile = LocalDrugStore().get(name)
    _CACHE[key] = profile
    return profile


def has_full_depth(profile: Optional[dict[str, Any]]) -> bool:
    """True if the profile carries products/patents/forms (not just lightweight)."""
    if not profile:
        return False
    return bool(profile.get("approved_products") or profile.get("patents_exclusivity")
                or profile.get("drug_forms"))


def is_prebuilt(name: str) -> bool:
    return LocalDrugStore().get(name) is not None

