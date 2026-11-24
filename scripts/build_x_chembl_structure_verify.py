#!/usr/bin/env python3
"""Verify the ChEMBL drugbank_id <-> chembl_id mapping at the STRUCTURE level.

The ChEMBL enrichment was joined BY NAME (the same weakness the PubChem side
had). The local ChEMBL snapshot carries inchi_key per molecule, so this check
runs fully offline: compare master_drug.inchikey against the ChEMBL molecule's
inchi_key for every mapped pair, using the same four levels as the PubChem
side (exact_match / skeleton_match / mismatch / unverifiable).

    python scripts/build_x_chembl_structure_verify.py
"""

from __future__ import annotations

import sqlite3
from collections import Counter
from datetime import datetime, timezone


def main() -> None:
    db = sqlite3.connect("data/master/master.db")
    chem = sqlite3.connect("data/drugbank/chembl_drugs.db")

    chem_ik = dict(chem.execute(
        "SELECT chembl_id, inchi_key FROM drugs WHERE inchi_key IS NOT NULL AND inchi_key!=''"))
    mapped = db.execute("SELECT drugbank_id, chembl_id FROM x_chembl").fetchall()
    master_ik = dict(db.execute("SELECT drugbank_id, COALESCE(inchikey,'') FROM master_drug"))
    names = dict(db.execute("SELECT drugbank_id, name FROM master_drug"))

    db.executescript(
        """
        DROP TABLE IF EXISTS x_chembl_structure_verify;
        CREATE TABLE x_chembl_structure_verify (
            drugbank_id TEXT PRIMARY KEY, name TEXT, chembl_id TEXT,
            match_level TEXT, master_inchikey TEXT, chembl_inchikey TEXT
        );
        """
    )

    levels = Counter()
    ins = []
    for dbid, chid in mapped:
        m_ik = master_ik.get(dbid, "")
        c_ik = chem_ik.get(chid, "")
        if not m_ik or not c_ik:
            level = "unverifiable"
        elif m_ik == c_ik:
            level = "exact_match"
        elif m_ik.split("-")[0] == c_ik.split("-")[0]:
            level = "skeleton_match"
        else:
            level = "mismatch"
        levels[level] += 1
        ins.append((dbid, names.get(dbid), chid, level, m_ik, c_ik))

    db.executemany("INSERT OR REPLACE INTO x_chembl_structure_verify VALUES (?,?,?,?,?,?)", ins)
    db.execute("INSERT OR REPLACE INTO manifest (key, value) VALUES (?,?)",
               ("chembl_structure_verify_built_at", datetime.now(timezone.utc).isoformat()))
    db.commit()
    chem.close()

    print(f"x_chembl_structure_verify rows: {len(ins)}")
    for k, v in levels.most_common():
        print(f"  {k:14s} {v:>5} ({100*v/len(ins):.1f}%)")


if __name__ == "__main__":
    main()
