"""Mock backend for Literature search.

Returns deterministic synthetic paper entries derived from a hash of
the query string. Same query always yields the same papers, which is
useful for testing but obviously not real literature.
"""

from __future__ import annotations

import hashlib
from typing import Any

_SOURCES = ("PubMed", "CrossRef", "OpenAlex")
_AUTHOR_POOL = (
    "Smith J.", "Lee K.", "Doe J.", "Garcia M.", "Patel R.",
    "Wang X.", "Brown A.", "Liu Y.", "Tanaka H.", "Khan S.",
)


def _author_list(seed: int, k: int = 2) -> list[str]:
    return [_AUTHOR_POOL[(seed + i * 7) % len(_AUTHOR_POOL)] for i in range(k)]


def run(input_data: dict[str, Any]) -> dict[str, Any]:
    """Return mock paper entries for the given query."""
    query = str(input_data.get("query", "")).strip()
    if not query:
        return {
            "query": query,
            "papers": [],
            "total_found": 0,
            "warnings": ["MOCK OUTPUT — empty query."],
        }

    max_results = int(input_data.get("max_results", 5))
    year_from = input_data.get("year_from")
    year_to = input_data.get("year_to")

    base_seed = int(hashlib.sha256(query.encode("utf-8")).hexdigest()[:8], 16)
    n_papers = min(max_results, 5)

    papers: list[dict[str, Any]] = []
    for i in range(n_papers):
        seed = (base_seed + i * 1009) & 0xFFFFFFFF
        year = 2018 + (seed % 8)              # 2018–2025
        if year_from and year < int(year_from):
            year = int(year_from)
        if year_to and year > int(year_to):
            year = int(year_to)

        papers.append({
            "title": f"Mock study on {query} ({i + 1})",
            "authors": _author_list(seed, k=2 + (seed % 2)),
            "year": year,
            "abstract": (
                f"This is a mock abstract for testing the Literature tool. "
                f"Query: '{query}'."
            ),
            "doi": f"10.MOCK/{seed:08x}" if seed % 3 == 0 else None,
            "source": _SOURCES[seed % len(_SOURCES)],
        })

    return {
        "query": query,
        "papers": papers,
        "total_found": n_papers,
        "warnings": [
            "MOCK OUTPUT — replace Literature backend with a real PubMed/CrossRef/OpenAlex client."
        ],
    }