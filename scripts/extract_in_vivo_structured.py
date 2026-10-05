#!/usr/bin/env python3
"""Patch stored drug-intelligence profiles with structured ADME numbers.

Runs the in_vivo_extract regexes over each profile's existing in_vivo prose
(already in the local store) and writes the structured fields back in place —
offline, no network, no rebuild needed. New builds get the same fields via the
DrugBank adapter automatically.

    python scripts/extract_in_vivo_structured.py [db_path]
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from formulation_os.knowledge.in_vivo_extract import extract_structured  # noqa: E402

_DB = sys.argv[1] if len(sys.argv) > 1 else "data/drug_intelligence.local.db"


def main() -> None:
    if not Path(_DB).exists():
        print(f"❌ {_DB} not found")
        return
    conn = sqlite3.connect(_DB)
    rows = conn.execute("SELECT name, profile_json FROM drug_profiles").fetchall()
    patched = drugs = fields = 0
    for name, pj in rows:
        p = json.loads(pj)
        iv = p.get("in_vivo", {})
        prose = {k: [{"value": v[0]["value"]}] for k, v in iv.items() if v}
        extracted = extract_structured(prose)
        if not extracted:
            continue
        drugs += 1
        for sname, sval in extracted.items():
            if sname not in iv:
                iv[sname] = [{
                    "value": sval,
                    "evidence": "experimental",
                    "source": "DrugBank",
                    "source_type": "extracted_from_curated_text",
                }]
                fields += 1
        p["in_vivo"] = iv
        conn.execute("UPDATE drug_profiles SET profile_json=? WHERE name=?",
                     (json.dumps(p, ensure_ascii=False), name))
        patched += 1
    conn.commit()
    conn.close()
    print(f"✅ Patched {drugs} drugs, added {fields} structured fields into {_DB}")


if __name__ == "__main__":
    main()
