"""Demo: multi-source drug intelligence for a single compound.

Shows the source-of-truth-per-category architecture end to end, reading from the
**local, offline** drug-intelligence store (no network at query time). Build the
store first:

    python scripts/build_drug_intelligence.py            # public sources
    python scripts/build_drug_intelligence.py --profile local  # + DrugBank

Then:
    python demos/drug_intelligence_demo.py Ibuprofen
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from formulation_os.tools.builtins.drug_database import backend  # noqa: E402


def main() -> None:
    drug = sys.argv[1] if len(sys.argv) > 1 else "Ibuprofen"
    print(f"🔎 Building drug intelligence for: {drug}\n")

    result = backend.run({"drug_name": drug, "query_type": "all"})

    meta = result.get("_meta", {})
    print("── Sources ─────────────────────────────────────────────")
    print("  used:        ", ", ".join(meta.get("sources_used", [])) or "none")
    print("  not-yet-wired:", ", ".join(s["source"] for s in meta.get("sources_unavailable", [])) or "none")
    if meta.get("conflicts"):
        print("  ⚠ conflicts: ", meta["conflicts"])
    print()

    for cat in ("identity", "physicochemical"):
        print(f"── {cat} ─────────────────────────────────────────")
        for field, values in result.get(cat, {}).items():
            v = values[0]
            tag = v.get("evidence")
            src = v.get("source")
            print(f"  {field:20s} = {v.get('value')}  [{tag} · {src}]")
        print()

    for cat in ("drug_forms", "approved_products", "patents_exclusivity"):
        records = result.get(cat, [])
        print(f"── {cat} ({len(records)} records) ────────────────────")
        for rec in records[:5]:
            flat = {k: fv.get("value") for k, fv in rec.items()}
            print("  ", json.dumps(flat, ensure_ascii=False))
        print()

    print("summary:", result.get("summary"))


if __name__ == "__main__":
    main()
