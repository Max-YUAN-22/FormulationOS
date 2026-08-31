#!/usr/bin/env python3
"""Pre-build lightweight local profiles for the whole ChEMBL catalog (offline).

Zero network: reads chembl_drugs.db (4,225 drugs) and writes identity +
physicochemical profiles into the drug-intelligence store, so every browsable
drug has a *local* card. Does NOT overwrite drugs that already have a full-depth
profile (the curated set enriched with products/patents/CN).

    python scripts/prebuild_catalog_lite.py                 # -> data/drug_intelligence.db (public)
    python scripts/prebuild_catalog_lite.py --out data/drug_intelligence.local.db
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from formulation_os.knowledge.catalog_lite import build_lite_profile  # noqa: E402
from formulation_os.knowledge.chembl_database import ChEMBLDrugDatabase  # noqa: E402
from formulation_os.knowledge.local_store import LocalDrugStore  # noqa: E402
import sqlite3  # noqa: E402


def _existing_full(db_path: str) -> set[str]:
    """Names already present that have full depth (approved_products/patents)."""
    if not Path(db_path).exists():
        return set()
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT name, profile_json FROM drug_profiles").fetchall()
    except sqlite3.OperationalError:
        conn.close()
        return set()
    conn.close()
    full = set()
    import json
    for name, pj in rows:
        try:
            p = json.loads(pj)
        except Exception:
            continue
        if p.get("approved_products") or p.get("patents_exclusivity") or p.get("drug_forms"):
            full.add(name.lower())
    return full


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="data/drug_intelligence.db")
    ap.add_argument("--chembl", default="data/drugbank/chembl_drugs.db")
    args = ap.parse_args()

    keep_full = _existing_full(args.out)
    store = LocalDrugStore(args.out, for_write=True)
    store.init_schema()

    df = ChEMBLDrugDatabase(args.chembl).get_all_drugs()
    now = datetime.now(timezone.utc).isoformat()
    written = skipped = 0
    for row in df.to_dict(orient="records"):
        name = row.get("name")
        if not name:
            continue
        if name.lower() in keep_full:
            skipped += 1
            continue
        store.write(name, build_lite_profile(row), built_at=now)
        written += 1

    print(f"✅ Lite catalog into {args.out}: wrote {written}, kept {skipped} full-depth")
    print(f"   Stats: {store.stats()}")


if __name__ == "__main__":
    main()
