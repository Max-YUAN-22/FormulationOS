#!/usr/bin/env python3
"""Three-source field confidence: DrugBank spine vs ChEMBL vs PubChem.

Tiers per numeric field (MW / LogP / TPSA):
  A3        three sources, all pairwise within tolerance
  A2        two sources, within tolerance
  B1        single source
  CONFLICT  multiple sources, disagreement
Overall: A (all fields A3) / CONFLICT (any) / B.

    python scripts/build_confidence3.py
"""

from __future__ import annotations

import re
import sqlite3
from collections import Counter
from pathlib import Path


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().upper())


def tier3(v1, v2, v3, rel_tol, abs_tol=None):
    vs = [v for v in map(_f, (v1, v2, v3)) if v is not None]
    n = len(vs)
    if n == 0:
        return 0, False, ""
    if n == 1:
        return 1, False, "B1"
    ok = lambda a, b: abs(a - b) <= (abs_tol if abs_tol is not None else abs(a) * rel_tol)
    pairs = [ok(vs[i], vs[j]) for i in range(n) for j in range(i + 1, n)]
    if n >= 3 and all(pairs):
        return 3, True, "A3"
    if all(pairs):
        return 2, True, "A2"
    return n, False, "CONFLICT"


def main() -> None:
    m = sqlite3.connect("data/master/master.db")
    m.row_factory = sqlite3.Row

    ch = sqlite3.connect("data/drugbank/chembl_drugs.db")
    ch.row_factory = sqlite3.Row
    cmw = {_norm(r["name"]): r["molecular_weight"] for r in
           ch.execute("SELECT name, molecular_weight FROM drugs")}
    ch.close()

    rows = m.execute(
        """
        SELECT m.drugbank_id, m.name,
               m.molecular_weight mw, m.logp, m.polar_surface_area psa,
               ch.alogp clogp, ch.psa cpsa,
               p.molecular_weight pmw, p.xlogp plogp, p.tpsa ptpsa,
               sv.match_level
        FROM master_drug m
        LEFT JOIN x_chembl ch ON ch.drugbank_id = m.drugbank_id
        LEFT JOIN x_pubchem p ON p.drugbank_id = m.drugbank_id
        LEFT JOIN x_structure_verify sv ON sv.drugbank_id = m.drugbank_id
        """
    ).fetchall()

    t_mw, t_lp, t_psa, overall = Counter(), Counter(), Counter(), Counter()
    exact_overall = Counter()
    ins = []
    for r in rows:
        nm, ag, tt = tier3(r["mw"], cmw.get(_norm(r["name"])), r["pmw"], 0.02)
        lp, lag, lt = tier3(r["logp"], r["clogp"], r["plogp"], None, abs_tol=0.5)
        ps, pag, pt = tier3(r["psa"], r["cpsa"], r["ptpsa"], 0.15)
        t_mw[tt] += 1; t_lp[lt] += 1; t_psa[pt] += 1
        tiers = [t for t in (tt, lt, pt) if t]
        ov = ("A" if tiers and all(t.startswith("A") for t in tiers) and "A3" in tiers
              else "CONFLICT" if "CONFLICT" in tiers
              else "B" if tiers else "")
        overall[ov] += 1
        if r["match_level"] == "exact_match":
            exact_overall[ov] += 1
        ins.append((r["drugbank_id"], r["name"], nm, ag, tt,
                    lp, lag, lt, ps, pag, pt, ov, r["match_level"]))

    m.executescript(
        """
        DROP TABLE IF EXISTS x_confidence;
        CREATE TABLE x_confidence (
            drugbank_id TEXT PRIMARY KEY, name TEXT,
            mw_n INTEGER, mw_agree INTEGER, mw_tier TEXT,
            logp_n INTEGER, logp_agree INTEGER, logp_tier TEXT,
            psa_n INTEGER, psa_agree INTEGER, psa_tier TEXT,
            overall_tier TEXT, match_level TEXT
        );
        """
    )
    m.executemany("INSERT INTO x_confidence VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", ins)
    m.commit()
    m.close()

    print("=== 三源置信度 v3(DrugBank + ChEMBL + PubChem, 结构验证标注)===")
    print("MW:  ", dict(t_mw))
    print("LogP:", dict(t_lp))
    print("TPSA:", dict(t_psa))
    print("总体(全部):", dict(overall))
    print("总体(仅结构验证 exact_match):", dict(exact_overall))


if __name__ == "__main__":
    main()
