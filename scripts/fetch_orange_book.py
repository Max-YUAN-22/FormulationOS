#!/usr/bin/env python3
"""Fetch and parse the FDA Orange Book data files into a local SQLite DB.

The openFDA drugsfda JSON API does NOT carry Orange Book patent/exclusivity
data — those live only in the downloadable Orange Book data files. This script
downloads them once (build time) and parses into a local, offline DB that the
runtime reads with no network.

Orange Book zip -> products.txt / patent.txt / exclusivity.txt (~-delimited)
              -> data/orange_book/orange_book.db  (tables: products, patents, exclusivity)

Keeps patent and exclusivity in SEPARATE tables, keyed by (appl_no, product_no),
preserving the Drug -> Product -> Application -> Patent / Exclusivity chain.

Usage:
    python scripts/fetch_orange_book.py                 # download + parse
    python scripts/fetch_orange_book.py --zip local.zip # parse an existing zip
"""

from __future__ import annotations

import argparse
import io
import sqlite3
import sys
import zipfile
from pathlib import Path

import requests

# FDA "Orange Book Data Files" (updated monthly).
_OB_URL = "https://www.fda.gov/media/76860/download"
_OUT_DB = "data/orange_book/orange_book.db"


def _read_delimited(zf: zipfile.ZipFile, filename: str) -> tuple[list[str], list[list[str]]]:
    """Read a ~-delimited Orange Book file: returns (header, rows)."""
    name = next((n for n in zf.namelist() if n.lower() == filename.lower()), None)
    if name is None:
        name = next((n for n in zf.namelist() if n.lower().endswith(filename.lower())), None)
    if name is None:
        raise FileNotFoundError(f"{filename} not found in zip ({zf.namelist()})")
    text = zf.read(name).decode("latin-1")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    header = [h.strip().lower() for h in lines[0].split("~")]
    rows = [ln.split("~") for ln in lines[1:]]
    return header, rows


def _create(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS patents;
        DROP TABLE IF EXISTS exclusivity;

        CREATE TABLE products (
            ingredient TEXT, df_route TEXT, trade_name TEXT, applicant TEXT,
            strength TEXT, appl_type TEXT, appl_no TEXT, product_no TEXT,
            te_code TEXT, approval_date TEXT, rld TEXT, rs TEXT,
            type TEXT, applicant_full_name TEXT
        );
        CREATE TABLE patents (
            appl_type TEXT, appl_no TEXT, product_no TEXT, patent_no TEXT,
            patent_expire_date TEXT, drug_substance_flag TEXT,
            drug_product_flag TEXT, patent_use_code TEXT, delist_flag TEXT,
            submission_date TEXT
        );
        CREATE TABLE exclusivity (
            appl_type TEXT, appl_no TEXT, product_no TEXT,
            exclusivity_code TEXT, exclusivity_date TEXT
        );
        CREATE INDEX idx_prod_ingredient ON products(ingredient);
        CREATE INDEX idx_prod_appl ON products(appl_no, product_no);
        CREATE INDEX idx_pat_appl ON patents(appl_no, product_no);
        CREATE INDEX idx_exc_appl ON exclusivity(appl_no, product_no);
        """
    )


def _col(header: list[str], row: list[str], *names: str):
    for n in names:
        if n in header:
            i = header.index(n)
            return row[i].strip() if i < len(row) else None
    return None


def parse_zip(zip_bytes: bytes, out_db: str) -> dict[str, int]:
    Path(out_db).parent.mkdir(parents=True, exist_ok=True)
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    conn = sqlite3.connect(out_db)
    _create(conn)
    counts = {}

    ph, prows = _read_delimited(zf, "products.txt")
    conn.executemany(
        "INSERT INTO products VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [(
            _col(ph, r, "ingredient"), _col(ph, r, "df;route", "df_route"),
            _col(ph, r, "trade_name"), _col(ph, r, "applicant"),
            _col(ph, r, "strength"), _col(ph, r, "appl_type"),
            _col(ph, r, "appl_no"), _col(ph, r, "product_no"),
            _col(ph, r, "te_code"), _col(ph, r, "approval_date"),
            _col(ph, r, "rld"), _col(ph, r, "rs"),
            _col(ph, r, "type"), _col(ph, r, "applicant_full_name"),
        ) for r in prows],
    )
    counts["products"] = len(prows)

    th, trows = _read_delimited(zf, "patent.txt")
    conn.executemany(
        "INSERT INTO patents VALUES (?,?,?,?,?,?,?,?,?,?)",
        [(
            _col(th, r, "appl_type"), _col(th, r, "appl_no"), _col(th, r, "product_no"),
            _col(th, r, "patent_no"), _col(th, r, "patent_expire_date_text", "patent_expire_date"),
            _col(th, r, "drug_substance_flag"), _col(th, r, "drug_product_flag"),
            _col(th, r, "patent_use_code"), _col(th, r, "delist_flag"),
            _col(th, r, "submission_date"),
        ) for r in trows],
    )
    counts["patents"] = len(trows)

    eh, erows = _read_delimited(zf, "exclusivity.txt")
    conn.executemany(
        "INSERT INTO exclusivity VALUES (?,?,?,?,?)",
        [(
            _col(eh, r, "appl_type"), _col(eh, r, "appl_no"), _col(eh, r, "product_no"),
            _col(eh, r, "exclusivity_code"), _col(eh, r, "exclusivity_date"),
        ) for r in erows],
    )
    counts["exclusivity"] = len(erows)

    conn.commit()
    conn.close()
    return counts


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--zip", help="path to an already-downloaded Orange Book zip")
    ap.add_argument("--out", default=_OUT_DB)
    args = ap.parse_args()

    if args.zip:
        print(f"📦 Parsing local zip: {args.zip}")
        data = Path(args.zip).read_bytes()
    else:
        print(f"⬇️  Downloading Orange Book data files from {_OB_URL}")
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            "Accept": "application/zip,application/octet-stream,*/*",
        }
        resp = requests.get(_OB_URL, timeout=120, headers=headers, allow_redirects=True)
        resp.raise_for_status()
        data = resp.content
        print(f"    {len(data)/1e6:.1f} MB downloaded")

    counts = parse_zip(data, args.out)
    print(f"✅ Parsed into {args.out}: {counts}")
    print("   Now rebuild: python scripts/build_drug_intelligence.py")


if __name__ == "__main__":
    main()
