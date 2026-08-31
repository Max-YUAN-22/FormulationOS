"""Web drill-down data provider for the Drug Intelligence card.

Bridges the deployed Streamlit UI to the multi-source Drug Intelligence Database:

  1. try the pre-built LocalDrugStore  (instant; local .local.db has DrugBank+CN,
     public .db has US public data)
  2. on a miss, LIVE-fetch via the aggregator using PUBLIC sources only
     (PubChem / ChEMBL / openFDA / Orange Book) — never DrugBank/CN, so nothing
     licence-restricted is ever produced for a public deployment. Cached
     in-process for the session.

This gives breadth (any of the 4,225 catalog drugs works) without pre-building
all of them, while keeping the deployed public site licence-clean.
"""

from __future__ import annotations

from typing import Any, Optional

from .local_store import LocalDrugStore
from .drug_intelligence import DrugIntelligenceAggregator, default_adapters

# sources excluded from the public live-fallback (licence-restricted, local-only)
_PUBLIC_EXCLUDE = {"DrugBank", "NMPA/CDE (China)"}

_CACHE: dict[str, Optional[dict[str, Any]]] = {}
_agg: Optional[DrugIntelligenceAggregator] = None


def _public_aggregator() -> DrugIntelligenceAggregator:
    global _agg
    if _agg is None:
        adapters = {k: v for k, v in default_adapters().items() if k not in _PUBLIC_EXCLUDE}
        _agg = DrugIntelligenceAggregator(adapters=adapters)
    return _agg


def get_drug_card(name: str, allow_live: bool = True) -> Optional[dict[str, Any]]:
    """Return a drug-intelligence profile dict for the web card, or None.

    Order: in-process cache -> pre-built local store -> live public fallback.
    """
    if not name:
        return None
    key = name.strip().lower()
    if key in _CACHE:
        return _CACHE[key]

    profile = LocalDrugStore().get(name)
    if profile is not None:
        _CACHE[key] = profile
        return profile

    if not allow_live:
        return None

    try:
        built = _public_aggregator().build(drug_name=name)
        profile = built.to_dict() if built.sources_used else None
    except Exception:
        profile = None
    _CACHE[key] = profile
    return profile


def is_prebuilt(name: str) -> bool:
    return LocalDrugStore().get(name) is not None
