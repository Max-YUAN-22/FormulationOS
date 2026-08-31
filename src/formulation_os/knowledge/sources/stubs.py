"""Phase-2 source adapters (framework stubs).

These sources are part of the target architecture but are **not automatable
with a simple free JSON API today** — they need an API key, a licence, or web
scraping. Each is implemented as a proper :class:`SourceAdapter` that returns
``SOURCE_UNAVAILABLE`` with a precise note on what it will provide and how it
will be wired up. This keeps the aggregator's routing table complete so filling
one in later is a drop-in change — no architectural rework.

Roadmap per source:

* CompTox (EPA)   — experimental *and* predicted physchem (melting point, water
                    solubility, ...). Needs a free CTX API key. Primary
                    supplement for physicochemical, clearly separating
                    experimental vs predicted values.
* EMA             — EU authorisations / EPAR. Downloadable medicine data tables
                    (parse + refresh), no per-drug JSON API.
* NMPA / CDE      — China marketed products + 参比制剂 (reference listed drug).
                    No clean public JSON API -> requires scraping the NMPA data
                    query portal and the CDE 上市药品目录集.
* Patents         — deep patent landscape beyond Orange Book: USPTO
                    (PatentsView API), EPO Espacenet (OPS API, needs
                    registration), WIPO PATENTSCOPE, CNIPA. Supplements ⑤.
* CSD (CCDC)      — crystal structures / polymorphs. Licensed; no free bulk
                    export. Cross-validate crystal forms.
* DrugBank        — optional supplement / cross-validation only. Bulk data is
                    licence-restricted and academic download is currently
                    paused, so this must never be a hard dependency.
"""

from __future__ import annotations

from typing import Optional

from .base import SourceAdapter
from .schema import (
    CATEGORY_APPROVED,
    CATEGORY_FORMS,
    CATEGORY_PATENTS,
    CATEGORY_PHYSCHEM,
)


class _StubAdapter(SourceAdapter):
    _note = "not yet integrated"

    def fetch(self, drug_name=None, smiles=None, categories=None):
        return self._unavailable(self._note)


class CompToxAdapter(_StubAdapter):
    name = "EPA CompTox"
    provides = (CATEGORY_PHYSCHEM,)
    _note = (
        "Phase 2: needs a free EPA CTX API key. Will supply experimental AND "
        "predicted physchem (melting point, water solubility, etc.), labelled "
        "separately."
    )

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key


class EMAAdapter(_StubAdapter):
    name = "EMA"
    provides = (CATEGORY_APPROVED,)
    _note = "Phase 2: parse EMA downloadable medicine data tables (EU authorisations / EPAR)."


class PatentsAdapter(_StubAdapter):
    name = "Patents (USPTO/Espacenet/WIPO/CNIPA)"
    provides = (CATEGORY_PATENTS,)
    _note = (
        "Phase 2: deep patent landscape beyond Orange Book. USPTO PatentsView "
        "API + EPO Espacenet OPS (registration) + WIPO PATENTSCOPE + CNIPA."
    )


class CSDAdapter(_StubAdapter):
    name = "CSD (CCDC)"
    provides = (CATEGORY_FORMS,)
    _note = "Phase 2: crystal structures / polymorphs. Licensed database, no free bulk export."
