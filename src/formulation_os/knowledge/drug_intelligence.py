"""Multi-source drug intelligence aggregator.

This is the piece that turns FormulationOS's drug database from
"everything-from-one-database" into a **source-of-truth-per-category** system:

    category                primary source        supplement / cross-check
    ----------------------  --------------------  --------------------------------
    identity                PubChem               ChEMBL, (DrugBank)
    physicochemical         PubChem               ChEMBL, CompTox*, literature
    drug_forms              ChEMBL                PubChem, CSD*, DrugBank*
    approved_products       FDA (openFDA)         DailyMed, EMA*, NMPA/CDE*
    patents_exclusivity     FDA Orange Book       USPTO/Espacenet/WIPO/CNIPA*

(* = phase-2 stub; returns source_unavailable until wired up.)

For each category the aggregator queries the primary source first, then the
supplements, keeping **every** source's value (so disagreements are visible)
and flagging numeric conflicts for scalar fields.
"""

from __future__ import annotations

from typing import Optional

from .sources.base import SourceAdapter
from .sources.schema import (
    ALL_CATEGORIES,
    CATEGORY_APPROVED,
    CATEGORY_FORMS,
    CATEGORY_IDENTITY,
    CATEGORY_PATENTS,
    CATEGORY_PHYSCHEM,
    RECORD_CATEGORIES,
    SCALAR_CATEGORIES,
    STATUS_NO_RECORD,
    STATUS_RECORD_FOUND,
    STATUS_SOURCE_UNAVAILABLE,
    DrugIntelligence,
    Evidence,
    FieldValue,
    Provenance,
    SourceResult,
    SourceStatus,
)
from .drug_synonyms import DrugResolver
from .sources.pubchem import PubChemAdapter
from .sources.chembl import ChEMBLAdapter
from .sources.openfda import OpenFDAAdapter
from .sources.orange_book import OrangeBookAdapter
from .sources.drugbank_local import DrugBankLocalAdapter
from .sources import stubs


#: category -> (primary source name, [supplement source names])
PRIMARY_SOURCE = {
    CATEGORY_IDENTITY: ("PubChem", ["ChEMBL", "DrugBank"]),
    CATEGORY_PHYSCHEM: ("PubChem", ["ChEMBL", "DrugBank", "EPA CompTox"]),
    CATEGORY_FORMS: ("ChEMBL", ["CSD (CCDC)", "DrugBank"]),
    CATEGORY_APPROVED: ("openFDA (FDA)", ["FDA Orange Book", "EMA", "NMPA/CDE (China)"]),
    CATEGORY_PATENTS: ("FDA Orange Book", ["Patents (USPTO/Espacenet/WIPO/CNIPA)"]),
}

#: numeric fields where cross-source disagreement is worth flagging, with the
#: relative tolerance beyond which we record a conflict.
_CONFLICT_TOLERANCE = {
    "molecular_weight": 0.02,
}


def default_adapters() -> dict[str, SourceAdapter]:
    """Build the standard adapter set for the OFFLINE build step.

    These are the *ingestion* adapters used by
    ``scripts/build_drug_intelligence.py`` — several make live API calls and are
    never used at query time. The deployed runtime reads the pre-built local
    store instead (see ``knowledge.local_store``).
    """
    adapters: list[SourceAdapter] = [
        PubChemAdapter(),
        ChEMBLAdapter(),
        OpenFDAAdapter(),
        OrangeBookAdapter(),      # local OB DB — primary for patents/exclusivity
        DrugBankLocalAdapter(),   # local file, licence-restricted, optional
        stubs.CompToxAdapter(),
        stubs.EMAAdapter(),
        stubs.NmpaCdeAdapter(),
        stubs.PatentsAdapter(),
        stubs.CSDAdapter(),
    ]
    return {a.name: a for a in adapters}


class DrugIntelligenceAggregator:
    """Assemble a provenance-aware profile across sources."""

    def __init__(
        self,
        adapters: Optional[dict[str, SourceAdapter]] = None,
        resolver: Optional[DrugResolver] = None,
    ):
        self.adapters = adapters if adapters is not None else default_adapters()
        self.resolver = resolver if resolver is not None else DrugResolver()

    def build(
        self,
        drug_name: Optional[str] = None,
        smiles: Optional[str] = None,
        categories: Optional[list[str]] = None,
    ) -> DrugIntelligence:
        categories = categories or ALL_CATEGORIES
        profile = DrugIntelligence(query=drug_name or smiles or "unknown")

        # -- canonical name / synonym resolution (before any source lookup) ---
        candidates = [drug_name] if drug_name else []
        if drug_name:
            resolved = self.resolver.resolve(drug_name)
            candidates = resolved.candidates
            profile.preferred_name = resolved.preferred_name
            profile.resolution = {
                "query": resolved.query,
                "preferred_name": resolved.preferred_name,
                "candidates_tried": candidates,
                "aliases": resolved.aliases,
            }

        # Which source names are relevant for the requested categories?
        needed: list[str] = []
        for cat in categories:
            primary, supplements = PRIMARY_SOURCE[cat]
            for name in [primary, *supplements]:
                if name not in needed:
                    needed.append(name)

        # Query each needed source once. Try candidate names (synonyms) until a
        # hit, so a British-INN query still matches a US-USAN source vocabulary.
        results: dict[str, SourceResult] = {}
        for name in needed:
            adapter = self.adapters.get(name)
            if adapter is None:
                # Source not part of this build's adapter set (e.g. DrugBank
                # excluded from a public build) — config choice, skip silently.
                continue
            res = self._fetch_with_synonyms(adapter, candidates, smiles, categories)
            results[name] = res
            if res.status == SourceStatus.OK:
                if name not in profile.sources_used:
                    profile.sources_used.append(name)
            elif res.status == SourceStatus.SOURCE_UNAVAILABLE:
                profile.sources_unavailable.append(
                    {"source": name, "reason": res.message or "unavailable"}
                )

        # Merge per category, primary first then supplements.
        for cat in categories:
            primary, supplements = PRIMARY_SOURCE[cat]
            ordered = [primary, *supplements]
            if cat in SCALAR_CATEGORIES:
                self._merge_scalar(profile, cat, ordered, results)
            else:
                self._merge_records(profile, cat, ordered, results)
            profile.category_status[cat] = self._category_status(cat, primary, results)

        self._detect_entity_and_conflicts(profile, results)
        self._add_condition_warnings(profile, categories)
        return profile

    def _fetch_with_synonyms(self, adapter, candidates, smiles, categories) -> SourceResult:
        """Try each candidate name until a source returns data."""
        last: Optional[SourceResult] = None
        for cand in candidates or [None]:
            res = adapter.fetch(drug_name=cand, smiles=smiles, categories=categories)
            last = res
            if res.status == SourceStatus.OK:
                return res
            if res.status == SourceStatus.SOURCE_UNAVAILABLE:
                return res  # no point trying other names
        return last if last is not None else SourceResult(
            source=getattr(adapter, "name", "?"), status=SourceStatus.NOT_FOUND
        )

    def _category_status(self, category, primary_source, results) -> str:
        """Three-state status from the PRIMARY source's result for a category."""
        res = results.get(primary_source)
        if res is None or res.status == SourceStatus.SOURCE_UNAVAILABLE:
            return STATUS_SOURCE_UNAVAILABLE
        has_data = bool(res.fields.get(category)) or bool(res.records.get(category))
        return STATUS_RECORD_FOUND if has_data else STATUS_NO_RECORD

    # -- merging ---------------------------------------------------------------

    def _merge_scalar(self, profile, category, ordered_sources, results) -> None:
        bucket: dict[str, list] = getattr(profile, category)
        for src_name in ordered_sources:
            res = results.get(src_name)
            if not res or not res.ok:
                continue
            for fname, fv in res.fields.get(category, {}).items():
                bucket.setdefault(fname, []).append(fv)

    def _detect_entity_and_conflicts(self, profile, results) -> None:
        """Distinguish true value conflicts from chemical-entity/form mismatches.

        A raw MW disagreement between sources is only a real ``conflict`` when the
        sources describe the *same* chemical entity. We check each contributing
        source's entity signature (InChIKey, else molecular formula):

          * >1 distinct entity signature  -> ``entity_mismatch`` (e.g. free acid
            vs calcium salt); the distinct forms are also captured as drug_forms.
          * same entity, values differ    -> genuine ``conflict``.
        """
        for fname, tol in _CONFLICT_TOLERANCE.items():
            fvs = profile.physicochemical.get(fname, [])
            nums = [fv for fv in fvs if _is_number(fv.value) and fv.provenance]
            if len(nums) < 2:
                continue

            entries = []
            for fv in nums:
                src = fv.provenance.source
                sig_key, sig_val = _entity_signature(results, src)
                entries.append({"source": src, "value": fv.value,
                                "sig_key": sig_key, "sig_val": sig_val})

            distinct_sigs = {e["sig_val"] for e in entries if e["sig_val"]}
            values = [e["value"] for e in entries]
            lo, hi = min(values), max(values)
            differ = lo > 0 and (hi - lo) / lo > tol

            if not differ:
                continue

            if len(distinct_sigs) > 1:
                # different chemical entities / forms — not a value conflict
                profile.entity_mismatches.append({
                    "category": CATEGORY_PHYSCHEM,
                    "field": fname,
                    "reason": "different chemical entity/form across sources",
                    "forms": [
                        {"source": e["source"], "value": e["value"],
                         e["sig_key"] or "signature": e["sig_val"]}
                        for e in entries
                    ],
                })
                self._capture_forms_from_mismatch(profile, fname, entries, results)
            else:
                profile.conflicts.append({
                    "category": CATEGORY_PHYSCHEM,
                    "field": fname,
                    "values": [{"source": e["source"], "value": e["value"]} for e in entries],
                })

    def _capture_forms_from_mismatch(self, profile, fname, entries, results) -> None:
        """Record each distinct entity signature as a drug_form (so a salt seen
        only via a physchem mismatch still appears under drug_forms)."""
        seen = {
            _form_signature(rec) for rec in profile.drug_forms
        }
        for e in entries:
            if not e["sig_val"] or e["sig_val"] in seen:
                continue
            src = e["source"]
            ik, formula = _entity_pair(results, src)
            prov = Provenance(source=src)
            rec = {
                "form_source": FieldValue(src, None, Evidence.RECORDED, prov),
                fname: FieldValue(e["value"], "g/mol", Evidence.RECORDED, prov),
            }
            if ik:
                rec["inchikey"] = FieldValue(ik, None, Evidence.RECORDED, prov)
            if formula:
                rec["molecular_formula"] = FieldValue(formula, None, Evidence.RECORDED, prov)
            profile.drug_forms.append(rec)
            seen.add(e["sig_val"])

    def _merge_records(self, profile, category, ordered_sources, results) -> None:
        bucket: list = getattr(profile, category)
        for src_name in ordered_sources:
            res = results.get(src_name)
            if not res or not res.ok:
                continue
            for record in res.records.get(category, []):
                bucket.append(record)

    def _add_condition_warnings(self, profile, categories) -> None:
        """Nudge: solubility/pKa-type numbers without conditions are low-value."""
        if CATEGORY_PHYSCHEM not in categories:
            return
        needs_conditions = {"solubility", "intrinsic_solubility", "pka", "logd", "permeability"}
        for fname, fvs in profile.physicochemical.items():
            if fname.lower() in needs_conditions:
                for fv in fvs:
                    if fv.conditions is None or fv.conditions.is_empty():
                        profile.warnings.append(
                            f"'{fname}' reported without measurement conditions "
                            f"(pH/temp/medium/method) — interpret with caution."
                        )
                        break


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _entity_pair(results, source_name) -> tuple[Optional[str], Optional[str]]:
    """Return (inchikey, molecular_formula) as reported by a given source."""
    res = results.get(source_name)
    if not res:
        return None, None
    ident = res.fields.get(CATEGORY_IDENTITY, {})
    ik = ident.get("inchikey")
    formula = ident.get("molecular_formula")
    return (ik.value if ik else None, formula.value if formula else None)


def _entity_signature(results, source_name) -> tuple[Optional[str], Optional[str]]:
    """Best available entity signature for a source: InChIKey, else formula.

    Returns (key_name, value) so callers know which signature was used.
    """
    ik, formula = _entity_pair(results, source_name)
    if ik:
        return "inchikey", ik
    if formula:
        return "molecular_formula", formula
    return None, None


def _form_signature(record: dict) -> Optional[str]:
    for key in ("inchikey", "molecular_formula", "chembl_id"):
        fv = record.get(key)
        if fv is not None:
            return getattr(fv, "value", None)
    return None

