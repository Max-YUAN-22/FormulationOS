"""Base class for all drug-data source adapters."""

from __future__ import annotations

from typing import Optional

from .schema import SourceResult, SourceStatus


class SourceAdapter:
    """Common interface for every data source.

    Subclasses implement :meth:`fetch`. They must **never raise** for expected
    conditions (drug not found, network error, missing licence/key) — instead
    return a :class:`SourceResult` with the appropriate status, so the
    aggregator can degrade gracefully.
    """

    #: Human-readable source name, e.g. "PubChem".
    name: str = "UnnamedSource"

    #: Categories (see schema.CATEGORY_*) this source can primarily serve.
    provides: tuple[str, ...] = ()

    def fetch(
        self,
        drug_name: Optional[str] = None,
        smiles: Optional[str] = None,
        categories: Optional[list[str]] = None,
    ) -> SourceResult:
        raise NotImplementedError

    # -- helpers for subclasses ------------------------------------------------

    def _unavailable(self, message: str) -> SourceResult:
        return SourceResult(
            source=self.name,
            status=SourceStatus.SOURCE_UNAVAILABLE,
            message=message,
        )

    def _not_found(self, message: str = "") -> SourceResult:
        return SourceResult(
            source=self.name,
            status=SourceStatus.NOT_FOUND,
            message=message or f"{self.name}: no record found",
        )

    def _error(self, message: str) -> SourceResult:
        return SourceResult(
            source=self.name,
            status=SourceStatus.ERROR,
            message=f"{self.name}: {message}",
        )

    def _ok(self) -> SourceResult:
        return SourceResult(source=self.name, status=SourceStatus.OK)
