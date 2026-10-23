#!/usr/bin/env python3
"""Build x_pubchem enrichment table from ALREADY-FETCHED profile data (offline).

The drug-intelligence profiles (4,230 rows) already carry PubChem identity +
physicochemical values collected during earlier builds. This extracts them into
the master spine as the THIRD source for cross-validation — zero network.

Join key: normalized preferred_name → master_drug.name (exact → startswith).
    python scripts/build_x_pubchem.py
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().upper())


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main() -> None:
    prof = sqlite3.connect("data/drug_intelligence.local.db")
    prof.row_factory = sqlite3.Row

    out = sqlite3.connect("data/master/master.db")
    out.row_factory = sqlite3.Row
    out.executescript(
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

    masters = out.execute("SELECT drugbank_id, name FROM master_drug").fetchall()
    by_exact, keys = {}, []
    seen = {}
    for r in prof.execute("SELECT name, profile_json FROM drug_profiles"):
        try:
            p = json.loads(r["profile_json"])
        except Exception:
            continue
        ident = p.get("identity", {})
        cid = ident.get("pubchem_cid", [{}])[0].get("value")
        if cid is None:
            continue
        ph = p.get("physicochemical", {})

        def first(cat, f):
            vs = ph.get(f) or ident.get(f)
            return _num(vs[0].get("value")) if vs else None

        rec = {
            "cid": str(cid),
            "mw": first(0, "molecular_weight"),
            "xlogp": first(0, "xlogp"),
            "tpsa": first(0, "tpsa") or first(0, "psa"),
            "hbd": first(0, "hbd"),
            "hba": first(0, "hba"),
            "formula": (ident.get("molecular_formula") or [{}])[0].get("value"),
        }
        # 只要有任一 PubChem 数值就算有效行
        if rec["mw"] is None and rec["xlogp"] is None and rec["tpsa"] is None:
            continue
        key = _norm(r["name"])
        if key not in seen:  # 首见优先
            seen[key] = rec
            by_exact[key] = rec
            keys.append(key)

    stats = {"exact": 0, "prefix": 0, "none": 0}
    inserted = 0
    for m in masters:
        nm = _norm(m["name"])
        rec, mt = by_exact.get(nm), "exact"
        if rec is None and nm:
            hits = [k for k in keys if k.startswith(nm)]
            if hits:
                rec, mt = by_exact[min(hits, key=len)], "prefix"
        if rec is None:
            stats["none"] += 1
            continue
        stats[mt] += 1
        out.execute(
            "INSERT OR REPLACE INTO x_pubchem VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                m["drugbank_id"], nm, mt, rec["cid"],
                rec["mw"], rec["xlogp"], rec["tpsa"], rec["hbd"], rec["hba"],
                rec["formula"],
            ),
        )
        inserted += 1
    out.commit()
    print(f"✅ x_pubchem: {inserted} 行 (exact={stats['exact']}, prefix={stats['prefix']}, none={stats['none']})")
    out.close(); prof.close()


if __name__ == "__main__":
    main()
