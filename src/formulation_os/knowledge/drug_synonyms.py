"""Drug name standardisation — canonical-name / synonym resolution.

Real data immediately exposed that a drug is known by different names across
sources (British INN vs US USAN): a query for *Paracetamol* misses openFDA and
DrugBank because they file it under *Acetaminophen*; *Glibenclamide* is
*Glyburide* in the US, etc.

Rather than hard-code per-drug patches, this module provides a proper resolution
layer used **before** any source lookup:

    user input -> canonical (preferred) name -> ordered candidate names
                -> each source is tried against the candidates until a hit

The seed table below covers the common INN/USAN/BAN divergences; it can be
extended freely, and is also persisted into the local DB as a ``drug_synonym``
table for queryability.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# (preferred_name, [synonyms], synonym_type)
SYNONYM_GROUPS: list[tuple[str, list[str], str]] = [
    ("Acetaminophen", ["Paracetamol", "APAP"], "USAN/INN"),
    ("Glyburide", ["Glibenclamide"], "USAN/INN"),
    ("Epinephrine", ["Adrenaline"], "USAN/INN"),
    ("Lidocaine", ["Lignocaine"], "USAN/INN"),
    ("Albuterol", ["Salbutamol"], "USAN/INN"),
    ("Furosemide", ["Frusemide"], "USAN/INN"),
    ("Rifampin", ["Rifampicin"], "USAN/INN"),
    ("Cyclosporine", ["Ciclosporin", "Cyclosporin"], "USAN/INN"),
    ("Acetylsalicylic acid", ["Aspirin"], "INN/brand"),
    ("Meperidine", ["Pethidine"], "USAN/INN"),
    ("Isoproterenol", ["Isoprenaline"], "USAN/INN"),
    ("Dextroamphetamine", ["Dexamfetamine"], "USAN/INN"),
    ("Trimethoprim", ["Trimethoprim"], "INN"),
]


@dataclass
class ResolvedDrug:
    """Result of resolving a raw query name."""

    query: str
    preferred_name: str
    #: ordered names to try against sources (preferred first, then synonyms)
    candidates: list[str] = field(default_factory=list)
    #: all alternative names (for storage / alias matching)
    aliases: list[str] = field(default_factory=list)


class DrugResolver:
    """Canonical-name / synonym resolver."""

    def __init__(self, groups: list[tuple[str, list[str], str]] | None = None):
        groups = groups if groups is not None else SYNONYM_GROUPS
        self._preferred_of: dict[str, str] = {}   # lower(any name) -> preferred
        self._aliases_of: dict[str, list[str]] = {}  # lower(preferred) -> [all names]
        self._types: dict[str, str] = {}
        for preferred, syns, stype in groups:
            names = [preferred, *syns]
            self._aliases_of[preferred.lower()] = names
            self._types[preferred.lower()] = stype
            for n in names:
                self._preferred_of[n.lower()] = preferred

    def resolve(self, name: str) -> ResolvedDrug:
        key = name.strip().lower()
        preferred = self._preferred_of.get(key, name)
        group = self._aliases_of.get(preferred.lower(), [preferred])
        # candidate order: the queried name first (most likely to match its own
        # source vocabulary), then preferred, then the rest — de-duplicated.
        candidates: list[str] = []
        for cand in [name, preferred, *group]:
            if cand and cand not in candidates:
                candidates.append(cand)
        aliases = [n for n in group if n.lower() != name.strip().lower()]
        return ResolvedDrug(
            query=name,
            preferred_name=preferred,
            candidates=candidates,
            aliases=aliases,
        )

    def as_rows(self) -> list[tuple[str, str, str]]:
        """Rows for the drug_synonym table: (preferred_name, synonym, type)."""
        rows: list[tuple[str, str, str]] = []
        for pref_lower, names in self._aliases_of.items():
            preferred = names[0]
            stype = self._types.get(pref_lower, "")
            for syn in names[1:]:
                rows.append((preferred, syn, stype))
        return rows
