#!/usr/bin/env python3
"""Build x_pubchem v2 OFFLINE from the frozen backfill JSONL (no network).

Reads data/raw/pubchem_backfill/{cid_resolution,properties}.jsonl — the
verbatim frozen PubChem responses — and rebuilds the x_pubchem table for the
full spine. The DB build therefore never depends on the live API: anyone with
the committed JSONL snapshot reproduces this table byte-for-byte.

    python scripts/build_x_pubchem_v2.py
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

RAW = Path("data/raw/pubchem_backfill")


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    cid_of: dict[str, dict] = {}
    with (RAW / "cid_resolution.jsonl").open() as f:
        for line in f:
            r = json.loads(line)
            if r.get("cid"):
                cid_of[r["drugbank_id"]] = r

    props_by_cid: dict[str, dict] = {}
    with (RAW / "properties.jsonl").open() as f:
        for line in f:
            r = json.loads(line)
            for p in (r.get("response") or {}).get("PropertyTable", {}).get("Properties", []):
                props_by_cid[str(p["CID"])] = p

    db = sqlite3.connect("data/master/master.db")
    db.executescript(
        """
        DROP TABLE IF EXISTS x_pubchem;
        CREATE TABLE x_pubchem (
            drugbank_id TEXT PRIMARY KEY,
            match_name TEXT, match_type TEXT,
            pubchem_cid TEXT,
            molecular_weight REAL, xlogp REAL, tpsa REAL,
            hbd INTEGER, hba INTEGER,
            molecular_formula TEXT
        );
        """
    )

    ins = []
    for dbid, r in cid_of.items():
        p = props_by_cid.get(str(r["cid"]))
        if not p:
            continue
        ins.append((
            dbid, r["name"], r["status"], str(r["cid"]),
            _f(p.get("MolecularWeight")), _f(p.get("XLogP")), _f(p.get("TPSA")),
            p.get("HBondDonorCount"), p.get("HBondAcceptorCount"),
            p.get("MolecularFormula"),
        ))
    db.executemany("INSERT INTO x_pubchem VALUES (?,?,?,?,?,?,?,?,?,?)", ins)
    db.executescript(
        "CREATE INDEX IF NOT EXISTS idx_xpubchem_cid ON x_pubchem(pubchem_cid);"
    )

    for key, val in {
        "pubchem_fetched_at": datetime.now(timezone.utc).isoformat(),
        "pubchem_spine_drugs": 19857,
        "pubchem_cid_resolved": len(cid_of),
        "pubchem_props_rows": len(ins),
        "pubchem_cid_jsonl_sha256": _sha256(RAW / "cid_resolution.jsonl"),
        "pubchem_props_jsonl_sha256": _sha256(RAW / "properties.jsonl"),
    }.items():
        db.execute("INSERT OR REPLACE INTO manifest (key, value) VALUES (?,?)", (key, str(val)))
    db.commit()

    print(f"x_pubchem v2 rows: {len(ins)} (was 1368)")
    print(f"  CIDs resolved: {len(cid_of)} / 19857 ({100*len(cid_of)/19857:.1f}%)")
    print(f"  JSONL sha256s recorded in manifest")


if __name__ == "__main__":
    main()
