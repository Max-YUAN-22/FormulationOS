"""Provenance-aware data model for the multi-source drug database.

The core idea the FormulationOS drug database is built on: every piece of
information carries **where it came from** and **whether it is measured or
predicted**, and physicochemical measurements additionally carry the
**conditions** under which they were obtained (pH, temperature, medium,
method). A number like ``Solubility = 3 mg/mL`` is nearly meaningless without
that context, so the schema forces it to travel together.

Two category shapes exist:

* **scalar** categories (identity, physicochemical) — a fixed set of named
  fields; each field may have several :class:`FieldValue` entries, one per
  contributing source, so cross-validation is preserved.
* **record-list** categories (drug_forms, approved_products,
  patents_exclusivity) — an open-ended list of records, each record being a
  ``{field_name: FieldValue}`` dict (e.g. one marketed product, one patent).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional


class SourceStatus(str, Enum):
    """Outcome of a single source lookup."""

    OK = "ok"
    NOT_FOUND = "not_found"
    #: Source exists in the architecture but is not wired up yet (phase 2),
    #: or requires a licence/API key that is not configured.
    SOURCE_UNAVAILABLE = "source_unavailable"
    ERROR = "error"


class Evidence(str, Enum):
    """Whether a value is experimentally measured or model-predicted."""

    EXPERIMENTAL = "experimental"
    PREDICTED = "predicted"
    #: e.g. a database identifier / structure — not a measurement at all.
    RECORDED = "recorded"
    UNKNOWN = "unknown"


@dataclass
class Conditions:
    """Measurement conditions for a physicochemical property.

    All optional — but strongly encouraged for solubility/pKa/logD/permeability
    where an unconditioned number is not scientifically usable.
    """

    ph: Optional[float] = None
    temperature_c: Optional[float] = None
    medium: Optional[str] = None          # e.g. "phosphate buffer", "water", "FaSSIF"
    method: Optional[str] = None          # e.g. "shake-flask", "potentiometric"
    solid_form: Optional[str] = None      # e.g. "crystalline Form I", "amorphous"

    def is_empty(self) -> bool:
        return all(v is None for v in asdict(self).values())


@dataclass
class Provenance:
    """Where a value came from."""

    source: str                            # e.g. "PubChem", "ChEMBL", "FDA Orange Book"
    reference: Optional[str] = None        # URL / accession / citation
    retrieved_from_cache: bool = False


@dataclass
class FieldValue:
    """A single value plus full provenance and (optional) conditions."""

    value: Any
    unit: Optional[str] = None
    evidence: Evidence = Evidence.UNKNOWN
    provenance: Optional[Provenance] = None
    conditions: Optional[Conditions] = None
    confidence: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"value": self.value}
        if self.unit is not None:
            d["unit"] = self.unit
        d["evidence"] = self.evidence.value if isinstance(self.evidence, Evidence) else self.evidence
        if self.provenance is not None:
            d["source"] = self.provenance.source
            if self.provenance.reference:
                d["reference"] = self.provenance.reference
            if self.provenance.retrieved_from_cache:
                d["cached"] = True
        if self.conditions is not None and not self.conditions.is_empty():
            d["conditions"] = {k: v for k, v in asdict(self.conditions).items() if v is not None}
        if self.confidence is not None:
            d["confidence"] = self.confidence
        return d


# ---------------------------------------------------------------------------
# The five information modules the drug database is organised around.
# ---------------------------------------------------------------------------

CATEGORY_IDENTITY = "identity"                    # (1) who is this drug   [scalar]
CATEGORY_PHYSCHEM = "physicochemical"             # (2) molecular/physchem [scalar]
CATEGORY_FORMS = "drug_forms"                     # (3) salt/crystal/hydrate [records]
CATEGORY_APPROVED = "approved_products"           # (4) marketed products    [records]
CATEGORY_PATENTS = "patents_exclusivity"          # (5) patent & exclusivity [records]

SCALAR_CATEGORIES = (CATEGORY_IDENTITY, CATEGORY_PHYSCHEM)
RECORD_CATEGORIES = (CATEGORY_FORMS, CATEGORY_APPROVED, CATEGORY_PATENTS)
ALL_CATEGORIES = list(SCALAR_CATEGORIES) + list(RECORD_CATEGORIES)

# Per-category resolution status (distinct from a source's raw SourceStatus).
STATUS_RECORD_FOUND = "record_found"          # primary source has data for this drug
STATUS_NO_RECORD = "no_record"                # primary source reachable but no record
STATUS_SOURCE_UNAVAILABLE = "source_unavailable"  # primary source not ingested yet


@dataclass
class SourceResult:
    """Raw payload returned by one source adapter for one drug."""

    source: str
    status: SourceStatus
    #: scalar categories: category -> {field_name: FieldValue}
    fields: dict[str, dict[str, FieldValue]] = field(default_factory=dict)
    #: record categories: category -> list of {field_name: FieldValue}
    records: dict[str, list[dict[str, FieldValue]]] = field(default_factory=dict)
    message: Optional[str] = None

    def add_field(self, category: str, name: str, fv: FieldValue) -> None:
        self.fields.setdefault(category, {})[name] = fv

    def add_record(self, category: str, record: dict[str, FieldValue]) -> None:
        self.records.setdefault(category, []).append(record)

    @property
    def ok(self) -> bool:
        return self.status == SourceStatus.OK


@dataclass
class DrugIntelligence:
    """Aggregated, provenance-aware profile assembled from many sources."""

    query: str
    preferred_name: Optional[str] = None
    # scalar categories: field name -> list of FieldValue (one per source)
    identity: dict[str, list[FieldValue]] = field(default_factory=dict)
    physicochemical: dict[str, list[FieldValue]] = field(default_factory=dict)
    # record categories: list of records
    drug_forms: list[dict[str, FieldValue]] = field(default_factory=list)
    approved_products: list[dict[str, FieldValue]] = field(default_factory=list)
    patents_exclusivity: list[dict[str, FieldValue]] = field(default_factory=list)

    #: bookkeeping
    sources_used: list[str] = field(default_factory=list)
    sources_unavailable: list[dict[str, str]] = field(default_factory=list)
    #: category -> "record_found" | "no_record" | "source_unavailable"
    category_status: dict[str, str] = field(default_factory=dict)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    #: differences that are NOT true conflicts but different chemical entities
    #: / forms (e.g. free acid vs calcium salt).
    entity_mismatches: list[dict[str, Any]] = field(default_factory=list)
    resolution: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"query": self.query}
        if self.preferred_name:
            out["preferred_name"] = self.preferred_name
        for cat in SCALAR_CATEGORIES:
            bucket: dict[str, list[FieldValue]] = getattr(self, cat)
            out[cat] = {
                fname: [fv.to_dict() for fv in fvs]
                for fname, fvs in bucket.items()
            }
        for cat in RECORD_CATEGORIES:
            records: list[dict[str, FieldValue]] = getattr(self, cat)
            out[cat] = [
                {fname: fv.to_dict() for fname, fv in rec.items()}
                for rec in records
            ]
        out["_meta"] = {
            "sources_used": self.sources_used,
            "sources_unavailable": self.sources_unavailable,
            "category_status": self.category_status,
            "conflicts": self.conflicts,
            "entity_mismatches": self.entity_mismatches,
            "resolution": self.resolution,
            "warnings": self.warnings,
        }
        return out
