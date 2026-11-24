#!/usr/bin/env python3
"""Quantify the LogP cross-method spread (DrugBank vs ChEMBL alogp vs PubChem xlogp).

The three sources do not measure LogP — they PREDICT it with different models.
The x_confidence CONFLICT tier records that they disagree; this analysis makes
the disagreement quantitative and interpretable:

  * pairwise signed differences per drug -> x_logp_analysis table
  * aggregate: mean/median signed difference, MAE, % within +/-0.5 / +/-1.0
  * verdict: is the spread random noise, or systematic method bias?

    python scripts/build_logp_analysis.py
"""

from __future__ import annotations

import sqlite3
import statistics as st
from datetime import datetime, timezone


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main() -> None:
    db = sqlite3.connect("data/master/master.db")
    db.row_factory = sqlite3.Row

    db.executescript(
        """
        DROP TABLE IF EXISTS x_logp_analysis;
        CREATE TABLE x_logp_analysis (
            drugbank_id TEXT PRIMARY KEY, name TEXT,
            db_logp REAL, chembl_alogp REAL, pubchem_xlogp REAL,
            db_minus_chembl REAL, db_minus_pubchem REAL, chembl_minus_pubchem REAL
        );
        """
    )

    rows = db.execute(
        """
        SELECT m.drugbank_id, m.name, m.logp,
               ch.alogp, p.xlogp
        FROM master_drug m
        LEFT JOIN x_chembl ch ON ch.drugbank_id = m.drugbank_id
        LEFT JOIN x_pubchem p ON p.drugbank_id = m.drugbank_id
        WHERE m.logp IS NOT NULL OR ch.alogp IS NOT NULL OR p.xlogp IS NOT NULL
        """
    ).fetchall()

    pairs = {"db_minus_chembl": [], "db_minus_pubchem": [], "chembl_minus_pubchem": []}
    ins = []
    for r in rows:
        a, b, c = _f(r["logp"]), _f(r["alogp"]), _f(r["xlogp"])
        d_ab = a - b if a is not None and b is not None else None
        d_ac = a - c if a is not None and c is not None else None
        d_bc = b - c if b is not None and c is not None else None
        if d_ab is not None:
            pairs["db_minus_chembl"].append(d_ab)
        if d_ac is not None:
            pairs["db_minus_pubchem"].append(d_ac)
        if d_bc is not None:
            pairs["chembl_minus_pubchem"].append(d_bc)
        if any(v is not None for v in (d_ab, d_ac, d_bc)):
            ins.append((r["drugbank_id"], r["name"], a, b, c, d_ab, d_ac, d_bc))

    db.executemany("INSERT OR REPLACE INTO x_logp_analysis VALUES (?,?,?,?,?,?,?,?)", ins)
    db.execute("INSERT OR REPLACE INTO manifest (key, value) VALUES (?,?)",
               ("logp_analysis_built_at", datetime.now(timezone.utc).isoformat()))
    db.commit()

    print(f"x_logp_analysis rows: {len(ins)}")
    print(f"{'pair':26s} {'n':>6} {'mean':>7} {'median':>7} {'MAE':>6} {'±0.5':>6} {'±1.0':>6}")
    for k, v in pairs.items():
        n = len(v)
        mae = sum(abs(x) for x in v) / n
        w05 = 100 * sum(1 for x in v if abs(x) <= 0.5) / n
        w10 = 100 * sum(1 for x in v if abs(x) <= 1.0) / n
        print(f"{k:26s} {n:>6} {st.mean(v):>7.2f} {st.median(v):>7.2f} "
              f"{mae:>6.2f} {w05:>5.1f}% {w10:>5.1f}%")


if __name__ == "__main__":
    main()
