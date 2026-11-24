#!/usr/bin/env python3
"""Verify the name-based PubChem match at the STRUCTURE level (offline).

Reads frozen inchikey_verify.jsonl and builds x_structure_verify:

  exact_match      full InChIKey equal           -> same compound; MW/TPSA/
                                                  XLogP comparison is clean
  skeleton_match   first InChIKey block equal    -> same covalent skeleton
                                                  (salt/protonation/stereo
                                                  difference); numeric
                                                  comparison must be FLAGGED
  mismatch         different structure           -> name match was WRONG
  unverifiable     master has no InChIKey        -> stays name-matched only
                                                  (biologics mostly)

    python scripts/build_x_structure_verify.py
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RAW = Path("data/raw/pubchem_backfill")


def main() -> None:
    pc_ik: dict[str, str] = {}
    with (RAW / "inchikey_verify.jsonl").open() as f:
        for line in f:
            r = json.loads(line)
            props = (r.get("response") or {}).get("PropertyTable", {}).get("Properties", [])
            for p in props:
                if p.get("InChIKey"):
                    pc_ik[str(p["CID"])] = p["InChIKey"]

    db = sqlite3.connect("data/master/master.db")
    spine = dict(db.execute(
        "SELECT drugbank_id, COALESCE(inchikey,'') FROM master_drug"))

    cid2db = {}
    with (RAW / "cid_resolution.jsonl").open() as f:
        for line in f:
            r = json.loads(line)
            if r.get("cid"):
                cid2db[str(r["cid"])] = r["drugbank_id"]

    db.executescript(
        """
        DROP TABLE IF EXISTS x_structure_verify;
        CREATE TABLE x_structure_verify (
            drugbank_id TEXT PRIMARY KEY, name TEXT,
            match_level TEXT, master_inchikey TEXT, pubchem_inchikey TEXT
        );
        """
    )

    names = dict(db.execute("SELECT drugbank_id, name FROM master_drug"))
    levels = Counter()
    ins = []
    for cid, dbid in cid2db.items():
        m_ik = spine.get(dbid, "")
        p_ik = pc_ik.get(cid, "")
        if not m_ik or not p_ik:
            level = "unverifiable"
        elif m_ik == p_ik:
            level = "exact_match"
        elif m_ik.split("-")[0] == p_ik.split("-")[0]:
            level = "skeleton_match"
        else:
            level = "mismatch"
        levels[level] += 1
        ins.append((dbid, names.get(dbid), level, m_ik, p_ik))

    db.executemany("INSERT OR REPLACE INTO x_structure_verify VALUES (?,?,?,?,?)", ins)
    db.execute("INSERT OR REPLACE INTO manifest (key, value) VALUES (?,?)",
               ("structure_verify_built_at", datetime.now(timezone.utc).isoformat()))
    db.commit()

    print(f"x_structure_verify rows: {len(ins)}")
    for k, v in levels.most_common():
        print(f"  {k:14s} {v:>6} ({100*v/len(ins):.1f}%)")


if __name__ == "__main__":
    main()
