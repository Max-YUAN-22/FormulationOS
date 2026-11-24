#!/usr/bin/env python3
"""Audit the melting-point disagreements between DrugBank and PubChem.

Each disagree row in x_exp_crosscheck is classified by likely cause so the
1,54+ cases become a REVIEWABLE error list, not a shrug:

  decomp_marker      one side mentions decomposition (dec./decomp) — MP vs
                     decomposition temperature of a DIFFERENT solid form
  interval_vs_point  db range vs pc point (or vice versa) — may be polymorphs
  unit_clash         underlying units differ (K vs °C) — parser artefact
  polymorph_suspect  both point values, no markers — genuine candidate error,
                     needs literature review
Writes data/processed/mp_disagreement_audit.csv (stays local: DrugBank
verbatim embedded; git only sees counts via the fingerprint).

    python scripts/audit_mp_disagreements.py
"""

from __future__ import annotations

import csv
import re
import sqlite3
from collections import Counter
from pathlib import Path

OUT = Path("data/processed/mp_disagreement_audit.csv")

_DEC = re.compile(r"dec(?:omp|\.)?\b", re.I)
_SALT = re.compile(r"hydrochloride|sulfate|sodium|salt|hydrate|monohydrate|dihydrate|maleate", re.I)


def main() -> None:
    db = sqlite3.connect("data/master/master.db")
    db.row_factory = sqlite3.Row
    rows = db.execute(
        """SELECT drugbank_id, name, drugbank_value, drugbank_lo, drugbank_hi,
                  drugbank_unit_known, pubchem_value, pubchem_lo, pubchem_hi
           FROM x_exp_crosscheck WHERE field='mp' AND relation='disagree'"""
    ).fetchall()

    audit = []
    for r in rows:
        db_txt = r["drugbank_value"] or ""
        cause = "polymorph_suspect"
        db_span = abs((r["drugbank_hi"] or 0) - (r["drugbank_lo"] or 0))
        pc_span = abs((r["pubchem_hi"] or 0) - (r["pubchem_lo"] or 0))
        if _DEC.search(db_txt) or _DEC.search(str(r["pubchem_value"])):
            cause = "decomp_marker"
        elif (db_span > 1) != (pc_span > 1):
            cause = "interval_vs_point"
        elif not r["drugbank_unit_known"]:
            cause = "unit_clash"
        elif _SALT.search(db_txt):
            cause = "salt_form_mentioned"
        audit.append({
            "drugbank_id": r["drugbank_id"], "name": r["name"], "cause": cause,
            "db_verbatim": db_txt, "db_lo": r["drugbank_lo"], "db_hi": r["drugbank_hi"],
            "pc_value": r["pubchem_value"], "pc_lo": r["pubchem_lo"], "pc_hi": r["pubchem_hi"],
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(audit[0].keys()))
        w.writeheader()
        w.writerows(audit)

    c = Counter(a["cause"] for a in audit)
    print(f"audited {len(audit)} MP disagreements -> {OUT} (stays local)")
    for k, v in c.most_common():
        print(f"  {k:18s} {v}")


if __name__ == "__main__":
    main()
