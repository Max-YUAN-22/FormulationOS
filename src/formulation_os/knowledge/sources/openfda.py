"""openFDA Drugs@FDA adapter — US approved products.

Free JSON API (a key raises rate limits but isn't required):
https://open.fda.gov/apis/

Primary for:
  - approved_products (④)  via Drugs@FDA + DailyMed labelling

NOTE: the drugsfda JSON does **not** carry Orange Book patent/exclusivity data
(those keys don't exist in the API payload). Patents & exclusivity (⑤) are
handled by the dedicated Orange Book adapter reading the OB data files.
"""

from __future__ import annotations

from typing import Optional

import requests

from .base import SourceAdapter
from .schema import (
    CATEGORY_APPROVED,
    Evidence,
    FieldValue,
    Provenance,
    SourceResult,
)

_DRUGSFDA = "https://api.fda.gov/drug/drugsfda.json"
_LABEL = "https://api.fda.gov/drug/label.json"


class OpenFDAAdapter(SourceAdapter):
    name = "openFDA (FDA)"
    provides = (CATEGORY_APPROVED,)

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 12,
        max_products: int = 10,
        session: Optional[requests.Session] = None,
    ):
        self.api_key = api_key
        self.timeout = timeout
        self.max_products = max_products
        self.session = session or requests

    def _get(self, url: str, params: dict) -> Optional[dict]:
        if self.api_key:
            params = {**params, "api_key": self.api_key}
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
        except Exception:
            return None
        if resp.status_code == 404:
            return {"results": []}
        if resp.status_code != 200:
            return None
        try:
            return resp.json()
        except ValueError:
            return None

    def fetch(self, drug_name=None, smiles=None, categories=None) -> SourceResult:
        if not drug_name:
            return self._not_found("openFDA adapter requires drug_name")

        search = (
            f'openfda.brand_name:"{drug_name}"+'
            f'openfda.generic_name:"{drug_name}"+'
            f'openfda.substance_name:"{drug_name}"'
        )
        payload = self._get(_DRUGSFDA, {"search": search, "limit": self.max_products})
        if payload is None:
            return self._error("Drugs@FDA request failed")

        results = payload.get("results", [])
        if not results:
            return self._not_found()

        result = self._ok()
        ref = "https://www.accessdata.fda.gov/scripts/cder/daf/"
        prov = Provenance(source=self.name, reference=ref)

        for app in results:
            app_no = app.get("application_number")
            sponsor = app.get("sponsor_name")
            openfda = app.get("openfda", {}) or {}
            products = app.get("products", []) or []

            for prod in products:
                rec: dict[str, FieldValue] = {}
                _put(rec, "application_number", app_no, prov)
                _put(rec, "sponsor", sponsor, prov)
                _put(rec, "brand_name", prod.get("brand_name"), prov)
                _put(rec, "product_number", prod.get("product_number"), prov)
                _put(rec, "dosage_form", prod.get("dosage_form"), prov)
                _put(rec, "route", prod.get("route"), prov)
                _put(rec, "marketing_status", prod.get("marketing_status"), prov)
                _put(rec, "reference_drug", prod.get("reference_drug"), prov)
                actives = prod.get("active_ingredients", []) or []
                if actives:
                    strengths = "; ".join(
                        f"{a.get('name')} {a.get('strength')}" for a in actives
                    )
                    _put(rec, "active_ingredients", strengths, prov)
                gen = (openfda.get("generic_name") or [None])[0]
                _put(rec, "generic_name", gen, prov)
                if rec:
                    result.add_record(CATEGORY_APPROVED, rec)

        # -- DailyMed / SPL label: inactive ingredients ----------------------
        self._fetch_label(drug_name, result)

        if not result.records.get(CATEGORY_APPROVED):
            return self._not_found()
        return result

    def _fetch_label(self, drug_name: str, result: SourceResult) -> None:
        payload = self._get(
            _LABEL,
            {"search": f'openfda.generic_name:"{drug_name}"', "limit": 1},
        )
        if not payload:
            return
        results = payload.get("results", [])
        if not results:
            return
        label = results[0]
        prov = Provenance(
            source="DailyMed/SPL (via openFDA)",
            reference="https://dailymed.nlm.nih.gov/",
        )
        inactive = label.get("inactive_ingredient")
        if inactive:
            text = inactive[0] if isinstance(inactive, list) else inactive
            rec = {"inactive_ingredients": FieldValue(text, None, Evidence.RECORDED, prov)}
            result.add_record(CATEGORY_APPROVED, rec)


def _put(rec: dict, name: str, value, prov: Provenance) -> None:
    if value is not None and value != "":
        rec[name] = FieldValue(value, None, Evidence.RECORDED, prov)

