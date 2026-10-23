#!/usr/bin/env python3
"""Build the FormulationBench master spine from the parsed DrugBank DB.

The spine is the FULL DrugBank dataset as the master table (one row per drug),
with per-source enrichment tables LEFT-JOINed later by InChIKey/name:
  master_drug (spine, from drugbank.db 5.1.x)
  + x_chembl, x_orange_book, x_nmpa ... (enrichment, added by later scripts)

Local-only file (DrugBank licence): data/master/master.db — never committed.

    python scripts/build_master_spine.py [--source data/drugbank/drugbank.db]
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

DDL = """
CREATE TABLE IF NOT EXISTS master_drug (
    drugbank_id      TEXT PRIMARY KEY,
    name             TEXT,
    cas_number       TEXT,
    unii             TEXT,
    type             TEXT,
    state            TEXT,
    inchikey         TEXT,
    smiles           TEXT,
    molecular_formula TEXT,
    molecular_weight REAL,
    -- calculated (DrugBank, predicted)
    logp REAL, logs REAL,
    pka_strongest_acidic REAL, pka_strongest_basic REAL,
    polar_surface_area REAL,
    h_bond_donor_count INTEGER, h_bond_acceptor_count INTEGER,
    rotatable_bond_count INTEGER,
    -- in-vivo (DrugBank curated text)
    absorption TEXT, half_life TEXT, protein_binding TEXT,
    route_of_elimination TEXT, volume_of_distribution TEXT, clearance TEXT,
    -- experimental (solid-state / solubility, with literature source)
    exp_melting_point TEXT,
    exp_water_solubility TEXT, exp_water_solubility_source TEXT,
    exp_isoelectric_point TEXT,
    -- classification
    superclass TEXT, class TEXT,
    -- pipeline metadata
    source_version TEXT,
    built_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_spine_inchikey ON master_drug(inchikey);
CREATE INDEX IF NOT EXISTS idx_spine_name ON master_drug(name COLLATE NOCASE);
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default="data/drugbank/drugbank.db")
    ap.add_argument("--out", default="data/master/master.db")
    ap.add_argument("--version", default="5.1.19")
    args = ap.parse_args()

    if not Path(args.source).exists():
        print(f"❌ source DB not found: {args.source}")
        sys.exit(1)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out = sqlite3.connect(args.out)
    out.executescript(DDL)

    src = sqlite3.connect(args.source)
    src.row_factory = sqlite3.Row
    rows = src.execute(
        """
        SELECT drugbank_id, name, cas_number, unii, type, state,
               inchikey, smiles, molecular_formula, molecular_weight,
               logp, logs, pka_strongest_acidic, pka_strongest_basic,
               polar_surface_area, h_bond_donor_count, h_bond_acceptor_count,
               rotatable_bond_count,
               absorption, half_life, protein_binding,
               route_of_elimination, volume_of_distribution, clearance,
               exp_melting_point, exp_water_solubility,
               exp_water_solubility_source, exp_isoelectric_point,
               classification_superclass, classification_class
        FROM drugs
        """
    ).fetchall()

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    out.execute("DELETE FROM master_drug")
    out.executemany(
        """
        INSERT INTO master_drug VALUES (
            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
        )
        """.replace("?", "?", 1),
        [
            (
                r["drugbank_id"], r["name"], r["cas_number"], r["unii"],
                r["type"], r["state"], r["inchikey"], r["smiles"],
                r["molecular_formula"], r["molecular_weight"],
                r["logp"], r["logs"], r["pka_strongest_acidic"], r["pka_strongest_basic"],
                r["polar_surface_area"], r["h_bond_donor_count"], r["h_bond_acceptor_count"],
                r["rotatable_bond_count"],
                r["absorption"], r["half_life"], r["protein_binding"],
                r["route_of_elimination"], r["volume_of_distribution"], r["clearance"],
                r["exp_melting_point"], r["exp_water_solubility"],
                r["exp_water_solubility_source"], r["exp_isoelectric_point"],
                r["classification_superclass"], r["classification_class"],
                args.version, now,
            )
            for r in rows
        ],
    )
    out.commit()

    total = out.execute("SELECT COUNT(*) FROM master_drug").fetchone()[0]
    iv = out.execute("SELECT COUNT(*) FROM master_drug WHERE half_life IS NOT NULL").fetchone()[0]
    ss = out.execute("SELECT COUNT(*) FROM master_drug WHERE exp_melting_point IS NOT NULL").fetchone()[0]
    out.close(); src.close()
    print(f"✅ Spine built: {args.out}")
    print(f"   master_drug: {total} rows (DrugBank {args.version})")
    print(f"   体内半衰期非空: {iv} | 实验熔点非空: {ss}")


if __name__ == "__main__":
    main()
