#!/usr/bin/env python3
"""Generate the human gold-audit worksheet (stratified random sample).

Reviewers ask: "who says your values are right?" The answer must be a HUMAN
verification exercise with documented error rate + confidence interval, not a
script asserting its own consistency. This generates the audit worksheet:

  * stratified sample, FIXED SEED (documented, re-runnable):
      20 A-tier, 20 B-tier, 20 CONFLICT, 20 with structured in-vivo values
  * one row per (drug, field): the master value NEXT TO every other source's
    value, so the human checks correspondence, not memory
  * blank verdict columns: human_verdict / correct_value / comment /
    verified_by / date — filled by hand, committed nowhere (verbatim content)

Precision of extraction + cross-source agreement is then reported as:
  n_checked, n_confirmed, precision, Wilson 95% CI.

    python scripts/generate_gold_audit_sample.py
"""

from __future__ import annotations

import csv
import random
import sqlite3
from pathlib import Path

SEED = 20261120          # frozen so the sample is reproducible
OUT = Path("data/processed/gold_audit_sample.csv")


def main() -> None:
    db = sqlite3.connect("data/master/master.db")
    db.row_factory = sqlite3.Row

    a_ids = [r[0] for r in db.execute(
        "SELECT drugbank_id FROM x_confidence WHERE overall_tier='A'")]
    b_ids = [r[0] for r in db.execute(
        "SELECT drugbank_id FROM x_confidence WHERE overall_tier='B'")]
    c_ids = [r[0] for r in db.execute(
        "SELECT drugbank_id FROM x_confidence WHERE overall_tier='CONFLICT'")]
    iv_ids = [r[0] for r in db.execute(
        "SELECT v.drugbank_id FROM x_in_vivo v JOIN x_confidence c "
        "ON c.drugbank_id = v.drugbank_id WHERE v.extracted_fields >= 2")]

    rng = random.Random(SEED)
    strata = {
        "A": rng.sample(a_ids, min(20, len(a_ids))),
        "B": rng.sample(b_ids, min(20, len(b_ids))),
        "CONFLICT": rng.sample(c_ids, min(20, len(c_ids))),
        "in_vivo": rng.sample(iv_ids, min(20, len(iv_ids))),
    }

    chem = sqlite3.connect("data/drugbank/chembl_drugs.db")
    chem_mw = {}
    for db_id, name in db.execute("SELECT drugbank_id, name FROM master_drug"):
        r = chem.execute(
            "SELECT molecular_weight FROM drugs WHERE UPPER(name)=UPPER(?)", (name,)
        ).fetchone()
        if r and r[0]:
            chem_mw[db_id] = r[0]
    chem.close()

    rows = []
    for stratum, ids in strata.items():
        for dbid in ids:
            m = db.execute(
                """SELECT name, molecular_weight, logp, polar_surface_area,
                          exp_melting_point, exp_water_solubility,
                          half_life, protein_binding
                   FROM master_drug WHERE drugbank_id=?""", (dbid,)
            ).fetchone()
            p = db.execute(
                "SELECT molecular_weight, xlogp, tpsa FROM x_pubchem WHERE drugbank_id=?",
                (dbid,)).fetchone()
            v = db.execute(
                """SELECT half_life_h_min, half_life_h_max, protein_binding_pct
                   FROM x_in_vivo WHERE drugbank_id=?""", (dbid,)).fetchone()
            cmw = chem_mw.get(dbid)

            fields = [
                ("molecular_weight", m["molecular_weight"],
                 f"pubchem={p['molecular_weight'] if p else None}; chembl={cmw}"),
                ("logp", m["logp"], f"pubchem_xlogp={p['xlogp'] if p else None}"),
                ("polar_surface_area", m["polar_surface_area"],
                 f"pubchem={p['tpsa'] if p else None}"),
                ("exp_melting_point", m["exp_melting_point"],
                 db.execute(
                     "SELECT pubchem_value FROM x_exp_crosscheck "
                     "WHERE drugbank_id=? AND field='mp'", (dbid,)).fetchone()),
                ("exp_water_solubility", m["exp_water_solubility"],
                 db.execute(
                     "SELECT pubchem_value FROM x_exp_crosscheck "
                     "WHERE drugbank_id=? AND field='ws'", (dbid,)).fetchone()),
                ("half_life",
                 f"{v['half_life_h_min']}..{v['half_life_h_max']} h" if v and v["half_life_h_min"] is not None else None,
                 f"prose={m['half_life']}"),
                ("protein_binding", v["protein_binding_pct"] if v else None,
                 f"prose={m['protein_binding']}"),
            ]
            for field, master_value, other_sources in fields:
                if master_value is None or master_value == "":
                    continue
                rows.append({
                    "stratum": stratum, "drugbank_id": dbid, "name": m["name"],
                    "field": field, "master_value": master_value,
                    "other_sources": str(other_sources) if other_sources else "",
                    "human_verdict": "", "correct_value": "",
                    "comment": "", "verified_by": "", "date": "",
                })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    per = {}
    for r in rows:
        per[r["stratum"]] = per.get(r["stratum"], 0) + 1
    print(f"worksheet -> {OUT} (stays local; verbatim content)")
    print(f"  rows: {len(rows)}  by stratum: {per}")
    print(f"  seed: {SEED} (frozen; re-run reproduces the exact sample)")
    print("  fill human_verdict/correct_value/verified_by, then report precision + Wilson CI")


if __name__ == "__main__":
    main()
