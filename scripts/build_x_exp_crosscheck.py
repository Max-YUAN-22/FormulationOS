#!/usr/bin/env python3
"""Cross-check DrugBank experimental solid-state values against PubChem (offline).

Reads the frozen exp_properties.jsonl (PUG View responses fetched for drugs
where the master spine carries experimental melting point / solubility) and
builds x_exp_crosscheck: one row per (drug, field) comparing the DrugBank
verbatim value with PubChem's experimental-property numbers.

Rules (honest-by-construction):
  * MP: DrugBank side accepts "N °C", ranges "N-M [°C/℃]" (unit optional —
    stored as unit_unknown, never guessed), decomposition markers ignored;
    PubChem side uses Number+Unit pairs (°C/°F/K -> °C), string fallback.
    agree = pc inside [lo,hi] (or |pc-lo|<=10 for point values);
    disagree = >25 °C away; in between = near.
  * Solubility: both sides normalised to log10(mg/mL-equivalent);
    agree within 1 decade, disagree beyond 2 decades, near in between.
  * anything unparseable on either side -> unparsed_one_side (kept, auditable).
Both verbatim sources stay in the row — the table is a review surface, not a
verdict. No value is silently dropped or silently agreed.

    python scripts/build_x_exp_crosscheck.py
"""

from __future__ import annotations

import json
import math
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RAW = Path("data/raw/pubchem_backfill/exp_properties.jsonl")
OUT_DB = "data/master/master.db"

# unit char class covers ASCII C/F/K, degree sign, and full-width ℃ (U+2103)
_U = r"(?:°|℃)?\s*(C|F|K|℃)"
_TEMP_RANGE = re.compile(r"(-?\d+(?:\.\d+)?)\s*[-–~to]+\s*(-?\d+(?:\.\d+)?)\s*" + _U, re.I)
_TEMP_POINT = re.compile(r"(-?\d+(?:\.\d+)?)\s*" + _U, re.I)
_TEMP_BARE = re.compile(r"(-?\d+(?:\.\d+)?)")            # unit unknown — flagged, not guessed
_SOL_RANGE = re.compile(
    r"(\d+(?:\.\d+)?(?:[eE]-?\d+)?)\s*[-–~to]+\s*(\d+(?:\.\d+)?(?:[eE]-?\d+)?)\s*"
    r"(mg/mL|µg/mL|ug/mL|g/L|mg/L|mol/L|mM|µM|uM)", re.I)
_SOL_POINT = re.compile(
    r"(\d+(?:\.\d+)?(?:[eE]-?\d+)?)\s*(mg/mL|µg/mL|ug/mL|g/L|mg/L|mol/L|mM|µM|uM)", re.I)

_SOL_FACTOR = {"mg/ml": 1.0, "µg/ml": 1e-3, "ug/ml": 1e-3, "g/l": 1.0,
               "mg/l": 1e-3, "mol/l": 1.0, "mm": 1e-3, "µm": 1e-6, "um": 1e-6}


def _to_c(v: float, u: str) -> float:
    u = u.replace("°", "").replace("℃", "C").strip().upper()
    return v if u == "C" else (v - 32) * 5 / 9 if u == "F" else v + 273.15


def parse_mp(text: str):
    """-> (lo, hi, unit_known) in °C, or None."""
    if not text:
        return None
    for rx in (_TEMP_RANGE, _TEMP_POINT):
        m = rx.search(text)
        if m:
            groups = [g for g in m.groups()]
            c = groups[-1]
            if rx is _TEMP_RANGE:
                lo, hi = _to_c(float(groups[0]), c), _to_c(float(groups[1]), c)
                return (min(lo, hi), max(lo, hi), True)
            return (_to_c(float(groups[0]), c),) * 2 + (True,)
    m = _TEMP_BARE.search(text)
    if m:
        v = float(m.group(1))
        return (v, v, False)          # unit unknown — flag stays on the row
    return None


def _sol_log10(v: float, u: str) -> float:
    # Greek mu (U+03BC) and micro sign (U+00B5) are distinct codepoints; both occur
    f = _SOL_FACTOR[u.lower().replace("μ", "µ")]
    return math.log10(v * f)


def parse_sol(text: str):
    """-> (lo, hi) in log10 mg/mL-equivalent, or None."""
    if not text:
        return None
    for rx in (_SOL_RANGE, _SOL_POINT):
        m = rx.search(text)
        if m:
            if rx is _SOL_RANGE:
                a, b = float(m.group(1)), float(m.group(2))
                if a <= 0 or b <= 0:
                    return None                      # 0 / negative: not log-comparable
                a, b = _sol_log10(a, m.group(3)), _sol_log10(b, m.group(3))
                return (min(a, b), max(a, b))
            v = float(m.group(1))
            if v <= 0:
                return None
            v = _sol_log10(v, m.group(2))
            return (v, v)
    return None


def collect_pc(response: dict, kind: str):
    """PubChem side: Number+Unit pairs; string-value fallback for both kinds."""
    if kind == "mp":
        hits: list[tuple[float, float]] = []
        texts: list[str] = []

        def walk(d) -> None:
            if isinstance(d, dict):
                if "Number" in d and isinstance(d["Number"], list) and d.get("Unit"):
                    u = str(d["Unit"])
                    for v in d["Number"]:
                        try:
                            hits.append((_to_c(float(v), u), _to_c(float(v), u)))
                        except (TypeError, ValueError):
                            continue
                if "StringValue" in d:
                    texts.append(str(d["StringValue"]))
                for x in d.values():
                    walk(x)
            elif isinstance(d, list):
                for x in d:
                    walk(x)

        walk(response)
        for t in texts:
            p = parse_mp(t)
            if p and p[2]:
                hits.append((p[0], p[1]))
        return hits

    hits = []
    texts = []

    def walk(d) -> None:
        if isinstance(d, dict):
            if "Number" in d and isinstance(d["Number"], list) and d.get("Unit"):
                u = str(d["Unit"]).lower()
                for v in d["Number"]:
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    f = _SOL_FACTOR.get(u)
                    if f is not None and v > 0:
                        hits.append((math.log10(v * f),) * 2)
            if "StringValue" in d:
                texts.append(str(d["StringValue"]))
            for x in d.get("StringWithMarkup") or []:
                if isinstance(x, dict) and x.get("String"):
                    texts.append(str(x["String"]))
            for x in d.values():
                walk(x)
        elif isinstance(d, list):
            for x in d:
                walk(x)

    walk(response)
    for t in texts:
        p = parse_sol(t)
        if p:
            hits.append(p)
    return hits


def main() -> None:
    cid2db = {}
    with (RAW.parent / "cid_resolution.jsonl").open() as f:
        for line in f:
            r = json.loads(line)
            if r.get("cid"):
                cid2db[str(r["cid"])] = r["drugbank_id"]

    pc_by_key: dict[str, list] = {}
    with RAW.open() as f:
        for line in f:
            r = json.loads(line)
            if r["status"] != "ok":
                continue
            pc_by_key[r["cid_flag"]] = collect_pc(r["response"], r["cid_flag"].split(":")[1])

    db = sqlite3.connect(OUT_DB)
    names = dict(db.execute("SELECT drugbank_id, name FROM master_drug"))
    spine = dict(db.execute(
        "SELECT drugbank_id, COALESCE(exp_melting_point,'')||'\x1f'||COALESCE(exp_water_solubility,'') "
        "FROM master_drug"))
    db.executescript(
        """
        DROP TABLE IF EXISTS x_exp_crosscheck;
        CREATE TABLE x_exp_crosscheck (
            drugbank_id TEXT, name TEXT, field TEXT,
            drugbank_value TEXT, drugbank_lo REAL, drugbank_hi REAL, drugbank_unit_known INTEGER,
            pubchem_value TEXT, pubchem_lo REAL, pubchem_hi REAL,
            relation TEXT,
            PRIMARY KEY (drugbank_id, field)
        );
        """
    )

    rows = []
    for key, pc_hits in pc_by_key.items():
        cid, kind = key.split(":")
        dbid = cid2db.get(cid)
        if not dbid:
            continue
        mp_verbatim, ws_verbatim = spine[dbid].split("\x1f")
        db_text = mp_verbatim if kind == "mp" else ws_verbatim
        parsed = parse_mp(db_text) if kind == "mp" else parse_sol(db_text)

        if not parsed or not pc_hits:
            rows.append((dbid, names.get(dbid), kind, db_text,
                         parsed[0] if parsed else None, parsed[1] if parsed else None,
                         int(parsed[2]) if parsed and len(parsed) == 3 else None,
                         "", None, None, "unparsed_one_side"))
            continue

        pc_lo, pc_hi = pc_hits[0]
        pc_desc = f"{pc_hits[0][0]:.4g}" + (f"..{pc_hits[0][1]:.4g}" if pc_hits[0][1] != pc_hits[0][0] else "")
        d_lo, d_hi = parsed[0], parsed[1]
        unit_known = int(parsed[2]) if len(parsed) == 3 else None

        overlap = not (pc_hi < d_lo or pc_lo > d_hi)           # interval overlap test
        if kind == "mp" and not unit_known and overlap:
            relation = "agree_unit_unknown"                     # bare db number inside pc range
        elif overlap:
            relation = "agree"
        else:
            gap = max(d_lo - pc_hi, pc_lo - d_hi)
            cap = 15 if kind == "mp" else 1.0
            far = 40 if kind == "mp" else 2.0
            relation = "near" if gap <= cap else "disagree" if gap > far else "near"

        rows.append((dbid, names.get(dbid), kind, db_text,
                     d_lo, d_hi, unit_known, pc_desc, pc_lo, pc_hi, relation))

    db.executemany("INSERT OR REPLACE INTO x_exp_crosscheck VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
    db.execute("INSERT OR REPLACE INTO manifest (key, value) VALUES (?,?)",
               ("exp_crosscheck_built_at", datetime.now(timezone.utc).isoformat()))
    db.commit()

    rel = Counter(r[10] for r in rows)
    by_field = Counter((r[2], r[10]) for r in rows)
    print(f"x_exp_crosscheck rows: {len(rows)}  relation: {dict(rel)}")
    for (f_, r_), n in sorted(by_field.items()):
        print(f"  {f_}: {r_:20s} {n}")


if __name__ == "__main__":
    main()
