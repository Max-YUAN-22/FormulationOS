"""Multi-source drug data adapters.

Each adapter implements :class:`SourceAdapter` and returns a
:class:`SourceResult`. The aggregator in
``formulation_os.knowledge.drug_intelligence`` decides which source is the
*primary* one for each category of information and which sources are used for
supplementary lookup / cross-validation.

Design principle: **no single database is the required backbone.** DrugBank in
particular is an optional supplement only (its bulk data is licence-restricted),
so its adapter degrades gracefully to ``source_unavailable`` when data/licence
is absent.
"""

from .schema import (
    Provenance,
    FieldValue,
    Conditions,
    Evidence,
    SourceResult,
    SourceStatus,
    DrugIntelligence,
)
from .base import SourceAdapter

__all__ = [
    "Provenance",
    "FieldValue",
    "Conditions",
    "Evidence",
    "SourceResult",
    "SourceStatus",
    "DrugIntelligence",
    "SourceAdapter",
]
