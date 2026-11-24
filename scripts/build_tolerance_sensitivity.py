#!/usr/bin/env python3
"""Tolerance sensitivity analysis for the three-source confidence tiers.

The confidence tiers use fixed tolerances (MW 2% rel, LogP 0.5 abs, TPSA 15%
rel). A reviewer's first question: "are those thresholds arbitrary?" This
recomputes tier distributions across a REASONABLE RANGE of each tolerance and
answers quantitatively: the ordering and the headline conclusions must be
stable across the whole range — robustness, not a cherry-picked threshold.

    python scripts/build_tolerance_sensitivity.py
"""

from __future__ import annotations

import re
import sqlite3


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().upper())


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def sweep(vals, rel_tol=None, abs_tol=None, label=""):
    total = a3 = a2 = conflict = 0
    for triple in vals:
        vs = [v for v in triple if v is not None]
        if not vs:
            continue
        total += 1

        def close(x, y):
            return abs(x - y) <= (abs_tol if abs_tol is not None else abs(x) * rel_tol)

        pairs_ok = all(close(vs[i], vs[j]) for i in range(len(vs)) for j in range(i + 1, len(vs)))
        if len(vs) >= 3:
            if pairs_ok:
                a3 += 1
            else:
                conflict += 1
        elif len(vs) == 2:
            if pairs_ok:
                a2 += 1
            else:
                conflict += 1
    print(f"{label:>22} {total:>9} {a3:>6} {a2:>6} {conflict:>9}")
    return total, a3, a2, conflict


def main() -> None:
    db = sqlite3.connect("data/master/master.db")
    chem = sqlite3.connect("data/drugbank/chembl_drugs.db")
    name_mw = {
        _norm(r[0]): _f(r[1])
        for r in chem.execute("SELECT name, molecular_weight FROM drugs")
    }
    name_mw = {k: v for k, v in name_mw.items() if v is not None}
    chem.close()

    rows = db.execute(
        """
        SELECT m.name, m.molecular_weight, m.logp, m.polar_surface_area,
               ch.alogp, ch.psa,
               p.molecular_weight, p.xlogp, p.tpsa
        FROM master_drug m
        LEFT JOIN x_chembl ch ON ch.drugbank_id = m.drugbank_id
        LEFT JOIN x_pubchem p  ON p.drugbank_id  = m.drugbank_id
        """
    ).fetchall()

    mw, lp, psa = [], [], []
    for (name, m_mw, m_lp, m_psa, c_lp, c_psa, p_mw, p_lp, p_psa) in rows:
        mw.append((_f(m_mw), name_mw.get(_norm(name)), _f(p_mw)))
        lp.append((_f(m_lp), _f(c_lp), _f(p_lp)))
        psa.append((_f(m_psa), _f(c_psa), _f(p_psa)))

    print(f"{'sweep':>22} {'compared':>9} {'A3':>6} {'A2':>6} {'CONFLICT':>9}")
    for tol in (0.01, 0.02, 0.05):
        sweep(mw, rel_tol=tol, label=f"MW rel_tol={tol}")
    for tol in (0.3, 0.5, 1.0):
        sweep(lp, abs_tol=tol, label=f"LogP abs_tol={tol}")
    for tol in (0.10, 0.15, 0.25):
        sweep(psa, rel_tol=tol, label=f"TPSA rel_tol={tol}")


if __name__ == "__main__":
    main()
