#!/usr/bin/env python3
"""Compile China reference preparations from drugfuture.com by PER-DRUG search.

drugfuture.com/refdrug consolidates the official NMPA/CDE 参比制剂目录. Its browse
pagination clamps after ~100 pages (returns a fixed page), so the reliable path
is its POST search: for each curated drug we POST a BasicSearch by English name
and parse the result rows. Targeted, clean, and covers exactly our drug set.

Provenance is honest: authority=NMPA/CDE, source_type=third_party_compilation,
source_provider=drugfuture.com — NOT tagged official. Local-only (git-ignored).
Spot-check against the official NMPA .doc afterwards.

Usage:
    python scripts/import_cn_reference_drugfuture.py            # curated 25 drugs
    python scripts/import_cn_reference_drugfuture.py --drugs Ibuprofen,Aspirin
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import requests  # noqa: E402

from formulation_os.knowledge.cn_reference_ingest import (  # noqa: E402
    parse_drugfuture_page,
    write_reference_records,
)
from formulation_os.knowledge.curated_drugs_list import CURATED_DRUGS  # noqa: E402

_BASE = "https://www.drugfuture.com/refdrug/index.aspx"
_OUT_DB = "data/nmpa_cde/nmpa_cde.db"
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def _hidden(html: str, name: str) -> str:
    m = re.search(rf'name="{name}"[^>]*value="([^"]*)"', html) or \
        re.search(rf'value="([^"]*)"[^>]*name="{name}"', html)
    return m.group(1) if m else ""


def search_drug(session: requests.Session, term: str) -> list[dict]:
    """POST BasicSearch for a drug's English name; return parsed reference rows."""
    g = session.get(_BASE, timeout=30)
    g.encoding = g.apparent_encoding
    data = {
        "__VIEWSTATE": _hidden(g.text, "__VIEWSTATE"),
        "__VIEWSTATEGENERATOR": _hidden(g.text, "__VIEWSTATEGENERATOR"),
        "__EVENTVALIDATION": _hidden(g.text, "__EVENTVALIDATION"),
        "SearchTerm": term,
        "SearchType": "BasicSearch",
        "submit": "查询",
    }
    r = session.post(_BASE, data=data, timeout=30)
    r.encoding = r.apparent_encoding
    recs = parse_drugfuture_page(r.text)
    # keep only rows whose English name actually contains the search term
    tl = term.lower()
    return [x for x in recs if tl in (x.get("drug_name_en") or "").lower()]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--drugs", help="comma-separated names (default: curated 25)")
    ap.add_argument("--delay", type=float, default=0.4)
    ap.add_argument("--out", default=_OUT_DB)
    args = ap.parse_args()

    drugs = [d.strip() for d in args.drugs.split(",")] if args.drugs else CURATED_DRUGS
    s = requests.Session()
    s.headers.update({"User-Agent": _UA})
    now = datetime.now(timezone.utc).isoformat()
    prov = {
        "authority": "NMPA/CDE",
        "source_type": "third_party_compilation",
        "source_provider": "drugfuture.com",
        "source_file": "drugfuture refdrug BasicSearch",
        "snapshot_date": "",
        "official_reference": "https://www.nmpa.gov.cn/ (仿制药参比制剂目录)",
        "ingested_at": now,
    }

    total = 0
    for i, drug in enumerate(drugs, 1):
        try:
            recs = search_drug(s, drug)
            if recs:
                write_reference_records(args.out, recs, prov)
            total += len(recs)
            print(f"  [{i}/{len(drugs)}] {drug:16s} +{len(recs)} reference products")
        except Exception as e:
            print(f"  [{i}/{len(drugs)}] {drug:16s} ERROR {e}")
        time.sleep(args.delay)

    print(f"\n✅ Compiled {total} reference products (curated drugs) into {args.out}")


if __name__ == "__main__":
    main()
