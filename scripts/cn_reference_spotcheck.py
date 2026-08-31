#!/usr/bin/env python3
"""Spot-check the drugfuture compilation against the OFFICIAL NMPA .doc.

Random-samples records of a given batch from the drugfuture-compiled rows and
compares them field-by-field against the official NMPA .doc for the same batch —
the QA step after compiling third-party data.

Usage:
    python scripts/cn_reference_spotcheck.py --batch 10 --official /tmp/cankao10.doc --n 15
"""

from __future__ import annotations

import argparse
import random
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from formulation_os.knowledge.cn_reference_ingest import parse_reference_doc_text  # noqa: E402

_DB = "data/nmpa_cde/nmpa_cde.db"
_FIELDS = ["drug_name_en", "holder", "strength", "dosage_form"]


def _doc_to_text(path: str) -> str:
    p = Path(path)
    if p.suffix.lower() == ".txt":
        return p.read_text(encoding="utf-8", errors="ignore")
    out = Path(tempfile.gettempdir()) / (p.stem + "_sc.txt")
    subprocess.run(["textutil", "-convert", "txt", str(p), "-output", str(out)],
                   check=True, capture_output=True)
    return out.read_text(encoding="utf-8", errors="ignore")


def _norm(s):
    return "".join((s or "").split()).lower()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--batch", required=True)
    ap.add_argument("--official", required=True, help="official NMPA .doc/.txt for that batch")
    ap.add_argument("--n", type=int, default=15)
    ap.add_argument("--db", default=_DB)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    official = {r["seq"]: r for r in parse_reference_doc_text(_doc_to_text(args.official), args.batch)}

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    df_rows = conn.execute(
        "SELECT * FROM reference_products WHERE batch=? AND source_provider='drugfuture.com'",
        (args.batch,),
    ).fetchall()
    conn.close()
    df = {r["seq"]: r for r in df_rows}

    common = sorted(set(official) & set(df))
    if not common:
        print(f"No overlapping seqs for batch {args.batch} "
              f"(official={len(official)}, drugfuture={len(df)}). "
              f"Has the drugfuture crawl reached this batch yet?")
        return

    random.seed(args.seed)
    sample = random.sample(common, min(args.n, len(common)))
    print(f"Spot-check batch {args.batch}: {len(sample)} of {len(common)} overlapping records\n")

    field_ok = {f: 0 for f in _FIELDS}
    for seq in sample:
        o, d = official[seq], df[seq]
        diffs = []
        for f in _FIELDS:
            ov, dv = _norm(o.get(f)), _norm(d[f] if f in d.keys() else "")
            # drugfuture 英文名 sometimes carries the trade tail; compare prefix-tolerant
            match = ov == dv or (ov and dv and (ov in dv or dv in ov))
            if match:
                field_ok[f] += 1
            else:
                diffs.append(f"{f}: official={o.get(f)!r} vs df={d[f] if f in d.keys() else None!r}")
        status = "✓" if not diffs else "✗"
        print(f"  {status} {seq}  {o.get('drug_name_en')}")
        for diff in diffs:
            print(f"       {diff}")

    print("\n── field-level agreement ──")
    n = len(sample)
    for f in _FIELDS:
        print(f"  {f:14s} {field_ok[f]}/{n}  ({round(100*field_ok[f]/n)}%)")


if __name__ == "__main__":
    main()
