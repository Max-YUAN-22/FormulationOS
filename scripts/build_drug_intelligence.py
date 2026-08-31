#!/usr/bin/env python3
"""Offline builder for the local drug-intelligence database.

Fetches from the ingestion sources (PubChem / ChEMBL / openFDA — live; DrugBank
— local parsed file) ONCE, and writes provenance-aware profiles into a local
SQLite store. The deployed service then reads only from that store, with no
network access.

Two build profiles:

  public  (default)  -> data/drug_intelligence.db
                        Redistributable sources only (PubChem, ChEMBL, openFDA).
                        Safe to commit and ship to the deployed service.

  local              -> data/drug_intelligence.local.db
                        Adds DrugBank (licence-restricted). Git-ignored, stays on
                        your machine only. Requires the parsed DrugBank DB
                        (scripts/parse_drugbank_xml.py) at data/drugbank/drugbank.db.

Usage:
    python scripts/build_drug_intelligence.py                 # public, curated list
    python scripts/build_drug_intelligence.py --profile local # + DrugBank
    python scripts/build_drug_intelligence.py --drugs Ibuprofen,Aspirin
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from formulation_os.knowledge.curated_drugs_list import CURATED_DRUGS  # noqa: E402
from formulation_os.knowledge.drug_intelligence import (  # noqa: E402
    DrugIntelligenceAggregator,
    default_adapters,
)
from formulation_os.knowledge.local_store import LocalDrugStore  # noqa: E402

_PUBLIC_DB = "data/drug_intelligence.db"
_LOCAL_DB = "data/drug_intelligence.local.db"
# Sources excluded from a public (redistributable) build.
_LICENCE_RESTRICTED = {"DrugBank", "NMPA/CDE (China)"}


def build_adapters(profile: str):
    adapters = default_adapters()
    if profile == "public":
        for name in _LICENCE_RESTRICTED:
            adapters.pop(name, None)
    return adapters


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profile", choices=["public", "local"], default="public")
    ap.add_argument("--drugs", help="comma-separated drug names (default: curated list)")
    ap.add_argument("--out", help="override output DB path")
    args = ap.parse_args()

    drugs = [d.strip() for d in args.drugs.split(",")] if args.drugs else CURATED_DRUGS
    out_path = args.out or (_LOCAL_DB if args.profile == "local" else _PUBLIC_DB)

    print(f"🏗  Building {args.profile} drug-intelligence DB -> {out_path}")
    print(f"    {len(drugs)} drugs, sources: {', '.join(build_adapters(args.profile))}")
    if args.profile == "public":
        print("    (DrugBank excluded — licence-restricted, use --profile local locally)")
    print()

    aggregator = DrugIntelligenceAggregator(adapters=build_adapters(args.profile))
    store = LocalDrugStore(out_path, for_write=True)
    store.init_schema()

    now = datetime.now(timezone.utc).isoformat()
    ok = 0
    for i, drug in enumerate(drugs, 1):
        try:
            profile = aggregator.build(drug_name=drug)
            store.write(drug, profile.to_dict(), built_at=now)
            used = ", ".join(profile.sources_used) or "none"
            print(f"  [{i}/{len(drugs)}] {drug:16s} ✓  sources: {used}")
            ok += 1
        except Exception as exc:  # keep going; one bad drug shouldn't abort build
            print(f"  [{i}/{len(drugs)}] {drug:16s} ✗  {exc}")

    print()
    print(f"✅ Done: {ok}/{len(drugs)} drugs written to {out_path}")
    print(f"   Stats: {store.stats()}")
    if args.profile == "public":
        print(f"   To ship it: git add -f {out_path} && commit (see chembl_drugs.db precedent)")


if __name__ == "__main__":
    main()
