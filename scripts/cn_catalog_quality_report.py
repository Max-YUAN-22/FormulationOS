#!/usr/bin/env python3
"""Data-quality report for the imported China catalog (constraint 5).

Acceptance is THIS report, not "import succeeded". Run after
scripts/import_cn_drug_catalog.py.

    python scripts/cn_catalog_quality_report.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from formulation_os.knowledge.cn_catalog_ingest import quality_report  # noqa: E402
from formulation_os.knowledge.curated_drugs_list import CURATED_DRUGS  # noqa: E402
from formulation_os.knowledge.drug_synonyms import DrugResolver  # noqa: E402

_DB = "data/nmpa_cde/nmpa_cde.db"


def main() -> None:
    db = sys.argv[1] if len(sys.argv) > 1 else _DB
    if not Path(db).exists():
        print(f"❌ {db} not found. Run scripts/import_cn_drug_catalog.py first.")
        sys.exit(1)

    rep = quality_report(db, target_names=CURATED_DRUGS, resolver=DrugResolver())
    print("═══════ China catalog — data quality report ═══════")
    print(json.dumps(rep, ensure_ascii=False, indent=2))

    rm = rep.get("resolver_match", {})
    print("\n── Key takeaways ──")
    print(f"  rows={rep['total_rows']}  unique approvals={rep['unique_approval_numbers']}  "
          f"unique APIs(en)={rep['unique_active_ingredients_en']}")
    print(f"  strength parse rate: {rep['strength_parse_rate_pct']}%")
    print(f"  25-drug coverage: {rm.get('targets_with_cn_data')}  "
          f"(exact={rm.get('exact')}, alias={rm.get('alias')}, "
          f"parent_via_salt={rm.get('parent_via_salt')}, unmatched={rm.get('unmatched')})")


if __name__ == "__main__":
    main()
