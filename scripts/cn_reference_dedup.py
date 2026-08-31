#!/usr/bin/env python3
"""Deduplicate the China reference_products table.

The same reference preparation can appear from both the official NMPA .doc
(source_type=official_file) and the drugfuture compilation
(source_type=third_party_compilation). This collapses exact duplicates —
matching on (drug_name_en, strength, dosage_form, holder) — keeping the OFFICIAL
row when present (higher provenance), otherwise keeping one third-party row.

Local-only maintenance script.

    python scripts/cn_reference_dedup.py
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

_DB = sys.argv[1] if len(sys.argv) > 1 else "data/nmpa_cde/nmpa_cde.db"


def _norm(s: str) -> str:
    return "".join((s or "").split()).lower()


def main() -> None:
    if not Path(_DB).exists():
        print(f"{_DB} not found")
        return
    conn = sqlite3.connect(_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT rowid, * FROM reference_products").fetchall()

    # group by content key; official rows rank first
    best: dict[tuple, int] = {}
    drop: list[int] = []
    for r in sorted(rows, key=lambda x: 0 if x["source_type"] == "official_file" else 1):
        key = (_norm(r["drug_name_en"]), _norm(r["strength"]),
               _norm(r["dosage_form"]), _norm(r["holder"]))
        if key in best:
            drop.append(r["rowid"])
        else:
            best[key] = r["rowid"]

    if drop:
        conn.executemany("DELETE FROM reference_products WHERE rowid=?", [(d,) for d in drop])
        conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM reference_products").fetchone()[0]
    off = conn.execute("SELECT COUNT(*) FROM reference_products WHERE source_type='official_file'").fetchone()[0]
    tp = conn.execute("SELECT COUNT(*) FROM reference_products WHERE source_type='third_party_compilation'").fetchone()[0]
    conn.close()
    print(f"Removed {len(drop)} duplicate rows.")
    print(f"reference_products now: {total}  (official={off}, third_party={tp})")


if __name__ == "__main__":
    main()
