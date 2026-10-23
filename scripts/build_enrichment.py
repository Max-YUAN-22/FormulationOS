#!/usr/bin/env python3
"""Build enrichment tables in the master spine DB (local sources only).

Adds to data/master/master.db:
  x_chembl       — ChEMBL IDs/properties/BCS/first-approval  (join: inchikey → name)
  x_orange_book  — aggregated OB products/patents per ingredient (join: name)
  x_nmpa         — aggregated CN reference preparations per drug  (join: name)
  x_confidence   — per-field multi-source agreement tiers (A/B/conflict)

Every table records how the join was made (match_type) — auditable, reproducible.

    python scripts/build_enrichment.py
"""

from __future__ import annotations

import re
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

MASTER = "data/master/master.db"
CHEMBL = "data/drugbank/chembl_drugs.db"
OB = "data/orange_book/orange_book.db"
CN = "data/nmpa_cde/nmpa_cde.db"


def _norm_name(s: str | None) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().upper())


def main() -> None:
    if not Path(MASTER).exists():
        print("❌ master.db not found — run scripts/build_master_spine.py first")
        sys.exit(1)
    out = sqlite3.connect(MASTER)
    out.row_factory = sqlite3.Row
    now = datetime.now(timezone.utc).isoformat()

    masters = out.execute(
        "SELECT drugbank_id, name, inchikey, molecular_weight, polar_surface_area, "
        "h_bond_donor_count, h_bond_acceptor_count FROM master_drug"
    ).fetchall()

    # ------------------------------------------------------------------ #
    # x_chembl                                                            #
    # ------------------------------------------------------------------ #
    out.executescript(
        """
        DROP TABLE IF EXISTS x_chembl;
        CREATE TABLE x_chembl (
            drugbank_id TEXT PRIMARY KEY,
            chembl_id TEXT, chembl_name TEXT, match_type TEXT,
            first_approval TEXT, bcs_class TEXT,
            alogp REAL, psa REAL, hbd INTEGER, hba INTEGER, rtb INTEGER,
            oral INTEGER, parenteral INTEGER, topical INTEGER, black_box INTEGER
        );
        """
    )
    chem = sqlite3.connect(CHEMBL)
    chem.row_factory = sqlite3.Row
    chem_by_ik, chem_by_name = {}, {}
    for r in chem.execute("SELECT * FROM drugs"):
        if r["inchi_key"]:
            chem_by_ik[r["inchi_key"].strip()] = r
        chem_by_name[_norm_name(r["name"])] = r
    stats = {"inchikey": 0, "name": 0, "none": 0}
    for m in masters:
        r = None
        mt = "none"
        if m["inchikey"] and m["inchikey"].strip() in chem_by_ik:
            r, mt = chem_by_ik[m["inchikey"].strip()], "inchikey"
        elif _norm_name(m["name"]) in chem_by_name:
            r, mt = chem_by_name[_norm_name(m["name"])], "name"
        stats[mt] += 1
        if r is None:
            continue
        out.execute(
            "INSERT OR REPLACE INTO x_chembl VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                m["drugbank_id"], r["chembl_id"], r["name"], mt,
                r["first_approval"], r["bcs_class"], r["logp"], r["psa"],
                r["hbd"], r["hba"], r["rtb"],
                r["oral"], r["parenteral"], r["topical"], r["black_box"],
            ),
        )
    chem.close()

    # ------------------------------------------------------------------ #
    # x_orange_book (aggregate products per ingredient)                    #
    # ------------------------------------------------------------------ #
    out.executescript(
        """
        DROP TABLE IF EXISTS x_orange_book;
        CREATE TABLE x_orange_book (
            drugbank_id TEXT PRIMARY KEY,
            match_name TEXT, match_type TEXT,
            n_products INTEGER, n_rld INTEGER, n_rs INTEGER,
            n_patents INTEGER, n_exclusivity INTEGER,
            sample_trade_name TEXT, sample_appl_no TEXT
        );
        """
    )
    ob_stats: dict[str, int] = defaultdict(int)
    try:
        ob = sqlite3.connect(OB)
        ob.row_factory = sqlite3.Row
        agg: dict[str, dict] = {}
        for p in ob.execute("SELECT * FROM products"):
            key = _norm_name(p["ingredient"])
            a = agg.setdefault(key, {
                "n": 0, "rld": 0, "rs": 0, "trades": set(), "appls": set()})
            a["n"] += 1
            a["rld"] += 1 if (p["rld"] or "").strip().lower() == "yes" else 0
            a["rs"] += 1 if (p["rs"] or "").strip().lower() == "yes" else 0
            if p["trade_name"]:
                a["trades"].add(p["trade_name"])
            if p["appl_no"]:
                a["appls"].add(p["appl_no"])
        # patents/exclusivity 无 ingredient 列 → 经 appl_no 归属到产品成分
        appl2ing: dict[str, str] = {}
        for p in ob.execute("SELECT appl_no, ingredient FROM products"):
            k = (p["appl_no"] or "").strip()
            if k:
                appl2ing.setdefault(k, _norm_name(p["ingredient"]))
        pat_counts: dict[str, int] = defaultdict(int)
        exc_counts: dict[str, int] = defaultdict(int)
        for r in ob.execute("SELECT appl_no, COUNT(*) c FROM patents GROUP BY appl_no"):
            ing = appl2ing.get((r["appl_no"] or "").strip())
            if ing:
                pat_counts[ing] += r["c"]
        for r in ob.execute("SELECT appl_no, COUNT(*) c FROM exclusivity GROUP BY appl_no"):
            ing = appl2ing.get((r["appl_no"] or "").strip())
            if ing:
                exc_counts[ing] += r["c"]
        ob.close()

        for m in masters:
            nm = _norm_name(m["name"])
            a = agg.get(nm)
            mt = "exact"
            hit_key = nm
            if a is None and nm:
                # word-level containment (ATORVASTATIN -> ATORVASTATIN CALCIUM)
                hits = [k for k in agg if nm in re.split(r"[;]", k)]
                if not hits:
                    hits = [k for k in agg if re.search(r"(?:^|[; ])"+re.escape(nm)+r"(?:$|[ (])", k)]
                if hits:
                    hit_key = min(hits, key=len)   # 最短命中=最特异
                    a, mt = agg[hit_key], "word_contains"
            if a is None:
                ob_stats["none"] += 1
                continue
            ob_stats[mt] += 1
            out.execute(
                "INSERT OR REPLACE INTO x_orange_book VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    m["drugbank_id"], hit_key, mt,
                    a["n"], a["rld"], a["rs"],
                    pat_counts.get(nm, 0), exc_counts.get(nm, 0),
                    (sorted(a["trades"])[0][:60] if a["trades"] else None),
                    (sorted(a["appls"])[0] if a["appls"] else None),
                ),
            )
    except Exception as e:
        print(f"⚠ Orange Book enrichment skipped: {type(e).__name__}: {e}")

    # ------------------------------------------------------------------ #
    # x_nmpa (CN reference preparations, aggregated per drug)              #
    # ------------------------------------------------------------------ #
    out.executescript(
        """
        DROP TABLE IF EXISTS x_nmpa;
        CREATE TABLE x_nmpa (
            drugbank_id TEXT PRIMARY KEY,
            match_name TEXT, match_type TEXT,
            n_cn_references INTEGER, n_originator INTEGER,
            sample_holder TEXT, latest_batch TEXT
        );
        """
    )
    cn_stats: dict[str, int] = defaultdict(int)
    try:
        cn = sqlite3.connect(CN)
        cn.row_factory = sqlite3.Row
        cagg = {}
        for r in cn.execute("SELECT drug_name_en, holder, reference_status, batch FROM reference_products"):
            key = _norm_name(r["drug_name_en"])
            a = cagg.setdefault(key, {"n": 0, "orig": 0, "holders": set(), "batches": []})
            a["n"] += 1
            a["orig"] += 1 if "originator" in (r["reference_status"] or "") else 0
            if r["holder"]:
                a["holders"].add(r["holder"])
            if r["batch"]:
                a["batches"].append(r["batch"])
        cn.close()

        inserted = 0
        for m in masters:
            nm = _norm_name(m["name"])
            a = None
            mt = "none"
            if nm in cagg:
                a, mt = cagg[nm], "name"
            else:
                hits = [k for k in cagg if nm and k.startswith(nm)]
                if not hits:
                    hits = [k for k in cagg if nm and (nm in k or k in nm)]
                if hits:
                    hit = min(hits, key=len)
                    a, mt = cagg[hit], "name_fuzzy"
            if a is None:
                cn_stats["none"] += 1
                continue
            cn_stats[mt] += 1
            out.execute(
                "INSERT OR REPLACE INTO x_nmpa VALUES (?,?,?,?,?,?,?)",
                (
                    m["drugbank_id"], nm, mt, a["n"], a["orig"],
                    (sorted(a["holders"])[0][:60] if a["holders"] else None),
                    max(a["batches"]) if a["batches"] else None,
                ),
            )
            inserted += 1
        print(f"   x_nmpa: {inserted} matched ({dict(cn_stats)})")
    except Exception as e:
        print(f"⚠ NMPA enrichment skipped: {type(e).__name__}: {e}")

    # ------------------------------------------------------------------ #
    # x_confidence (per-field multi-source agreement tiers)                #
    # ------------------------------------------------------------------ #
    # x_confidence 由 _build_confidence() 单独构建(需 ChEMBL MW 列)


def _build_confidence() -> None:
    out = sqlite3.connect(MASTER)
    out.row_factory = sqlite3.Row
    ch = sqlite3.connect(CHEMBL)
    ch.row_factory = sqlite3.Row
    chem_mw = {}
    for r in ch.execute("SELECT name, molecular_weight, logp, psa, hbd, hba FROM drugs"):
        chem_mw[_norm_name(r["name"])] = r
    ch.close()

    out.executescript(
        """
        DROP TABLE IF EXISTS x_confidence;
        CREATE TABLE x_confidence (
            drugbank_id TEXT PRIMARY KEY, name TEXT,
            mw_sources INTEGER, mw_agree INTEGER, mw_tier TEXT,
            logp_sources INTEGER, logp_agree INTEGER, logp_tier TEXT,
            psa_sources INTEGER, psa_agree INTEGER, psa_tier TEXT,
            overall_tier TEXT
        );
        """
    )

    def _f(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def cmp_tier(v1, v2, tol):
        v1, v2 = _f(v1), _f(v2)
        s = [v for v in (v1, v2) if v is not None]
        if len(s) < 2:
            return len(s), True, "B" if s else ""
        agree = abs(v1 - v2) / max(abs(v1), 1e-9) <= tol
        return 2, agree, ("A" if agree else "CONFLICT")

    rows = out.execute(
        "SELECT drugbank_id, name, molecular_weight, logp, polar_surface_area,"
        " h_bond_donor_count, h_bond_acceptor_count FROM master_drug"
    ).fetchall()
    overall = {"A": 0, "B": 0, "CONFLICT": 0}
    ins = []
    for m in rows:
        c = chem_mw.get(_norm_name(m["name"]))
        r = {"drugbank_id": m["drugbank_id"], "name": m["name"]}
        tiers = []
        for field, mcol, ccol, tol in (
            ("mw", "molecular_weight", "molecular_weight", 0.02),
            ("logp", "logp", "logp", 0.15),
            ("psa", "polar_surface_area", "psa", 0.15),
        ):
            cv = c[ccol] if c else None
            n, agree, t = cmp_tier(m[mcol], cv, tol)
            r[f"{field}_sources"], r[f"{field}_agree"], r[f"{field}_tier"] = n, int(agree), t
            if t:
                tiers.append(t)
        r["overall_tier"] = (
            "A" if tiers and all(t == "A" for t in tiers)
            else "CONFLICT" if "CONFLICT" in tiers else "B"
        )
        if r["overall_tier"] in overall:
            overall[r["overall_tier"]] += 1
        ins.append(tuple(r.values()))

    out.executemany(
        f"INSERT OR REPLACE INTO x_confidence VALUES ({','.join('?' for _ in ins[0])})", ins
    )
    out.commit()
    out.close()
    print(f"✅ x_confidence: A={overall['A']}  B={overall['B']}  CONFLICT={overall['CONFLICT']}")


if __name__ == "__main__":
    main()
    _build_confidence()
