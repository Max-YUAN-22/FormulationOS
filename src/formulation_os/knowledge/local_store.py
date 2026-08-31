"""Local, offline drug-intelligence store.

The deployed service must answer queries **without any network access** — live
API calls per request are slow, rate-limited and unreliable. So all data is
pre-built offline (see ``scripts/build_drug_intelligence.py``) into a local
SQLite store, and the runtime only ever reads from here.

Store layout — one row per drug, holding:
  * a few indexed columns for fast lookup / filtering
  * the full provenance-aware profile as a JSON blob (already in output shape)

Two physical files are supported, checked in priority order:
  1. ``data/drug_intelligence.local.db``  — dev machine, may include
     licence-restricted sources (DrugBank). Never committed / deployed.
  2. ``data/drug_intelligence.db``        — redistributable sources only
     (PubChem / ChEMBL / openFDA). Committed and shipped to the service.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

_DEFAULT_CANDIDATES = (
    "data/drug_intelligence.local.db",
    "data/drug_intelligence.db",
)


def resolve_db_path(explicit: Optional[str] = None) -> Optional[str]:
    """Pick the local DB to read: explicit > .local.db > .db. None if absent."""
    if explicit:
        return explicit if Path(explicit).exists() else None
    for cand in _DEFAULT_CANDIDATES:
        if Path(cand).exists():
            return cand
    return None


class LocalDrugStore:
    """Read/write access to the offline drug-intelligence SQLite store."""

    def __init__(self, db_path: Optional[str] = None, *, for_write: bool = False):
        if for_write:
            # writing: use the given path (or the default local build target)
            self.db_path = db_path or "data/drug_intelligence.db"
        else:
            self.db_path = resolve_db_path(db_path)
        self._for_write = for_write

    # -- schema ---------------------------------------------------------------

    def init_schema(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS drug_profiles (
                name          TEXT PRIMARY KEY COLLATE NOCASE,
                canonical_name TEXT,
                aliases       TEXT,          -- JSON list of alternative names
                inchikey      TEXT,
                profile_json  TEXT NOT NULL, -- full DrugIntelligence.to_dict()
                sources       TEXT,          -- JSON list of sources used
                built_at      TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_dp_inchikey ON drug_profiles(inchikey)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_dp_canonical ON drug_profiles(canonical_name COLLATE NOCASE)")
        conn.commit()
        conn.close()

    # -- write (build time) ---------------------------------------------------

    def write(
        self,
        name: str,
        profile_dict: dict[str, Any],
        *,
        aliases: Optional[list[str]] = None,
        built_at: str = "",
    ) -> None:
        canonical = _first_identity(profile_dict, "iupac_name") or name
        inchikey = _first_identity(profile_dict, "inchikey")
        sources = (profile_dict.get("_meta", {}) or {}).get("sources_used", [])
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT OR REPLACE INTO drug_profiles
                (name, canonical_name, aliases, inchikey, profile_json, sources, built_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                canonical,
                json.dumps(aliases or [], ensure_ascii=False),
                inchikey,
                json.dumps(profile_dict, ensure_ascii=False),
                json.dumps(sources, ensure_ascii=False),
                built_at,
            ),
        )
        conn.commit()
        conn.close()

    # -- read (runtime) -------------------------------------------------------

    @property
    def available(self) -> bool:
        return bool(self.db_path) and Path(self.db_path).exists()

    def get(self, name: str) -> Optional[dict[str, Any]]:
        """Return the stored profile dict for a drug, or None. No network."""
        if not self.available:
            return None
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # exact (case-insensitive) match first
        cur.execute("SELECT profile_json FROM drug_profiles WHERE name = ?", (name,))
        row = cur.fetchone()
        if row is None:
            # try alias / canonical / substring
            cur.execute(
                """
                SELECT profile_json FROM drug_profiles
                WHERE canonical_name = ? OR aliases LIKE ? OR name LIKE ?
                LIMIT 1
                """,
                (name, f'%"{name}"%', f"%{name}%"),
            )
            row = cur.fetchone()
        conn.close()
        if row is None:
            return None
        return json.loads(row["profile_json"])

    def list_drugs(self) -> list[str]:
        if not self.available:
            return []
        conn = sqlite3.connect(self.db_path)
        names = [r[0] for r in conn.execute("SELECT name FROM drug_profiles ORDER BY name")]
        conn.close()
        return names

    def stats(self) -> dict[str, Any]:
        if not self.available:
            return {"db_path": self.db_path, "available": False, "count": 0}
        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM drug_profiles").fetchone()[0]
        conn.close()
        return {"db_path": self.db_path, "available": True, "count": count}


def _first_identity(profile_dict: dict[str, Any], field: str) -> Optional[str]:
    vals = (profile_dict.get("identity", {}) or {}).get(field)
    if vals and isinstance(vals, list) and vals:
        return vals[0].get("value")
    return None
