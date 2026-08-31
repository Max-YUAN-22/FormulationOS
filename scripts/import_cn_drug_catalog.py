#!/usr/bin/env python3
"""Import a third-party compilation of the CDE 中国上市药品目录集 into a local DB.

NOT a fetch of official NMPA/CDE data — it imports a third-party Excel the user
supplies. Because that compilation's redistribution rights are unclear, the
output DB is local-only (git-ignored) and only ever merged into the ``local``
build profile, never the public/deployed one.

    third-party Excel  ->  data/nmpa_cde/nmpa_cde.db  (table: marketed_products)

Provenance records the authority (NMPA/CDE) separately from the channel
(third-party compilation): --provider / --snapshot / the file name are stored on
every row.

Usage:
    python scripts/import_cn_drug_catalog.py path/to/catalog.xlsx \
        --provider "rjpharma" --snapshot 2026-06
    python scripts/import_cn_drug_catalog.py catalog.xlsx --sheet 0
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from formulation_os.knowledge.cn_catalog_ingest import (  # noqa: E402
    normalize_row,
    resolve_headers,
    write_records,
)

_OUT_DB = "data/nmpa_cde/nmpa_cde.db"
_OFFICIAL_REF = "https://www.cde.org.cn/hymlj/"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("excel", help="path to the third-party catalog .xlsx/.csv")
    ap.add_argument("--sheet", default=0, help="sheet name or index (Excel only)")
    ap.add_argument("--out", default=_OUT_DB)
    ap.add_argument("--provider", default="third_party", help="who compiled the file")
    ap.add_argument("--snapshot", default="", help="edition/version date of the source")
    ap.add_argument("--official-reference", default=_OFFICIAL_REF)
    args = ap.parse_args()

    try:
        import pandas as pd
    except ImportError:
        print("pandas required: pip install pandas openpyxl")
        sys.exit(1)

    path = args.excel
    if path.lower().endswith(".csv"):
        df = pd.read_csv(path, dtype=str)
    else:
        df = pd.read_excel(path, sheet_name=args.sheet, dtype=str)

    columns = list(df.columns)
    mapping = resolve_headers(columns)
    print(f"📖 {len(df)} rows, {len(columns)} columns")
    print(f"🔗 Resolved {len(mapping)} logical fields:")
    for field, col in sorted(mapping.items()):
        print(f"     {field:24s} <- {col!r}")
    unresolved = [f for f in ("active_ingredient_en", "approval_number", "drug_name") if f not in mapping]
    if unresolved:
        print(f"⚠️  Could NOT map key fields: {unresolved}")
        print(f"    Available columns: {columns}")
        print("    Add the real header(s) to HEADER_ALIASES and re-run.")

    now = datetime.now(timezone.utc).isoformat()
    prov = {
        "authority": "NMPA/CDE",
        "source_type": "third_party_compilation",
        "source_provider": args.provider,
        "source_file": Path(path).name,
        "snapshot_date": args.snapshot,
        "official_reference": args.official_reference,
        "ingested_at": now,
    }

    records = []
    for raw in df.to_dict(orient="records"):
        rec = normalize_row({k: raw.get(k) for k in columns}, mapping)
        rec.update(prov)
        records.append(rec)

    n = write_records(args.out, records)
    print(f"✅ Wrote {n} rows to {args.out}")
    print(f"   Next: python scripts/cn_catalog_quality_report.py")


if __name__ == "__main__":
    main()
