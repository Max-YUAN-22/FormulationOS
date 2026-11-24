#!/usr/bin/env python3
"""Build x_coverage: per-field non-null counts across the full spine.

The database paper's Table 1 — one view answering "how many drugs carry each
field, from which source". Pure SQL over existing tables, regenerated on every
build so it can never drift from the data.

    python scripts/build_coverage_matrix.py
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

N_FIELDS = [
    ("master_drug", "cas_number", "DrugBank", "identity"),
    ("master_drug", "unii", "DrugBank", "identity"),
    ("master_drug", "inchikey", "DrugBank", "identity"),
    ("master_drug", "smiles", "DrugBank", "identity"),
    ("master_drug", "molecular_weight", "DrugBank", "calculated"),
    ("master_drug", "logp", "DrugBank", "calculated"),
    ("master_drug", "pka_strongest_acidic", "DrugBank", "calculated"),
    ("master_drug", "pka_strongest_basic", "DrugBank", "calculated"),
    ("master_drug", "polar_surface_area", "DrugBank", "calculated"),
    ("master_drug", "h_bond_donor_count", "DrugBank", "calculated"),
    ("master_drug", "rotatable_bond_count", "DrugBank", "calculated"),
    ("master_drug", "exp_melting_point", "DrugBank(exp,lit)", "solid_state"),
    ("master_drug", "exp_water_solubility", "DrugBank(exp,lit)", "solid_state"),
    ("master_drug", "exp_isoelectric_point", "DrugBank(exp,lit)", "solid_state"),
    ("master_drug", "half_life", "DrugBank", "in_vivo_prose"),
    ("master_drug", "protein_binding", "DrugBank", "in_vivo_prose"),
    ("master_drug", "volume_of_distribution", "DrugBank", "in_vivo_prose"),
    ("master_drug", "clearance", "DrugBank", "in_vivo_prose"),
    ("master_drug", "absorption", "DrugBank", "in_vivo_prose"),
    ("master_drug", "route_of_elimination", "DrugBank", "in_vivo_prose"),
    ("master_drug", "superclass", "DrugBank", "classification"),
    ("master_drug", "class", "DrugBank", "classification"),
    ("x_pubchem", "pubchem_cid", "PubChem", "cross_source"),
    ("x_pubchem", "molecular_weight", "PubChem", "calculated"),
    ("x_pubchem", "xlogp", "PubChem", "calculated"),
    ("x_pubchem", "tpsa", "PubChem", "calculated"),
    ("x_chembl", "drugbank_id", "ChEMBL", "cross_source"),
    ("x_orange_book", "drugbank_id", "OrangeBook", "cross_source"),
    ("x_nmpa", "drugbank_id", "NMPA", "cross_source"),
    ("x_in_vivo", "half_life_h_min", "extracted", "in_vivo_structured"),
    ("x_in_vivo", "protein_binding_pct", "extracted", "in_vivo_structured"),
    ("x_in_vivo", "vd_value", "extracted", "in_vivo_structured"),
    ("x_in_vivo", "clearance_min", "extracted", "in_vivo_structured"),
    ("x_exp_crosscheck", "drugbank_id", "crosscheck", "cross_source"),
    ("x_logp_analysis", "drugbank_id", "analysis", "cross_source"),
]


def main() -> None:
    db = sqlite3.connect("data/master/master.db")
    total = db.execute("SELECT COUNT(*) FROM master_drug").fetchone()[0]

    db.executescript(
        """
        DROP TABLE IF EXISTS x_coverage;
        CREATE TABLE x_coverage (
            layer TEXT, field TEXT, source TEXT,
            drugs_with_field INTEGER, pct_of_spine REAL
        );
        """
    )

    out = []
    for table, col, source, layer in N_FIELDS:
        try:
            n = db.execute(
                f"SELECT COUNT(*) FROM {table} "
                f"WHERE {col} IS NOT NULL AND TRIM(CAST({col} AS TEXT))!=''"
            ).fetchone()[0]
        except sqlite3.OperationalError:
            n = 0
        out.append((layer, col, source, n, round(100.0 * n / total, 1)))

    db.executemany("INSERT INTO x_coverage VALUES (?,?,?,?,?)", out)
    db.execute("INSERT OR REPLACE INTO manifest (key, value) VALUES (?,?)",
               ("coverage_built_at", datetime.now(timezone.utc).isoformat()))
    db.commit()

    print(f"spine: {total} drugs\n")
    cur_layer = None
    for layer, col, source, n, pct in out:
        if layer != cur_layer:
            print(f"-- {layer} --")
            cur_layer = layer
        print(f"  {col:26s} {source:18s} {n:>6} ({pct:.1f}%)")


if __name__ == "__main__":
    main()
