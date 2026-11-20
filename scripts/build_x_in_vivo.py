#!/usr/bin/env python3
"""Build x_in_vivo: structured ADME numbers extracted from master_drug prose.

Runs the rule-based extractors (src/formulation_os/knowledge/in_vivo_extract.py)
over the four numeric ADME prose columns of master_drug and writes:

  * x_in_vivo table   — one row per drug, structured value + matched snippet
                        per field (the verbatim prose stays in master_drug;
                        this table adds structure, never replaces the source);
  * data/processed/in_vivo_audit.csv — one row per (drug, field) INCLUDING
                        prose-without-extraction, so coverage is auditable:
                        every value sits next to the exact text it came from.

Values are AS-STATED (units kept verbatim, no normalisation beyond
half-life -> hours): honest provenance over fake uniformity. No guessing —
no confident match means no structured value.

    python scripts/build_x_in_vivo.py
"""

from __future__ import annotations

import csv
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from formulation_os.knowledge.in_vivo_extract import (  # noqa: E402
    extract_clearance,
    extract_half_life,
    extract_protein_binding,
    extract_volume_of_distribution,
)

AUDIT = Path("data/processed/in_vivo_audit.csv")


def main() -> None:
    db = sqlite3.connect("data/master/master.db")
    db.row_factory = sqlite3.Row

    db.executescript(
        """
        DROP TABLE IF EXISTS x_in_vivo;
        CREATE TABLE x_in_vivo (
            drugbank_id TEXT PRIMARY KEY,
            name TEXT,
            -- half-life, normalised to hours (min..max interval)
            half_life_h_min REAL, half_life_h_max REAL, half_life_raw TEXT,
            -- protein binding, percent; qualitative=1 for 'negligibly bound'
            protein_binding_pct REAL, protein_binding_qualitative INTEGER,
            protein_binding_raw TEXT,
            -- volume of distribution, as-stated unit
            vd_value REAL, vd_unit TEXT, vd_raw TEXT,
            -- clearance, as-stated unit (interval or point)
            clearance_min REAL, clearance_max REAL, clearance_unit TEXT,
            clearance_raw TEXT,
            extracted_fields INTEGER
        );
        """
    )

    rows = db.execute(
        """SELECT drugbank_id, name, half_life, protein_binding,
                  volume_of_distribution, clearance
           FROM master_drug"""
    ).fetchall()

    audit_rows: list[dict] = []
    cov = {"half_life": [0, 0], "protein_binding": [0, 0],
           "volume_of_distribution": [0, 0], "clearance": [0, 0]}

    for r in rows:
        rec: dict = {
            "drugbank_id": r["drugbank_id"], "name": r["name"],
            "half_life_h_min": None, "half_life_h_max": None, "half_life_raw": None,
            "protein_binding_pct": None, "protein_binding_qualitative": None,
            "protein_binding_raw": None,
            "vd_value": None, "vd_unit": None, "vd_raw": None,
            "clearance_min": None, "clearance_max": None, "clearance_unit": None,
            "clearance_raw": None, "extracted_fields": 0,
        }

        def audited(field: str, prose: str, fn):
            """Run one extractor, record audit line, return result or None."""
            prose = (prose or "").strip()
            if not prose:
                return None
            res = fn(prose)
            cov[field][0] += 1
            if res:
                cov[field][1] += 1
            audit_rows.append({
                "drugbank_id": r["drugbank_id"], "name": r["name"], "field": field,
                "verbatim_prose": prose, "matched_raw": (res or {}).get("raw", ""),
                "extracted": "" if res is None else
                    ",".join(f"{k}={v}" for k, v in res.items() if k != "raw"),
            })
            return res

        hl = audited("half_life", r["half_life"], extract_half_life)
        if hl:
            rec["half_life_h_min"], rec["half_life_h_max"] = hl["min"], hl["max"]
            rec["half_life_raw"] = hl["raw"]
            rec["extracted_fields"] += 1

        pb = audited("protein_binding", r["protein_binding"], extract_protein_binding)
        if pb:
            rec["protein_binding_pct"] = pb["value"]
            rec["protein_binding_raw"] = pb["raw"]
            if pb["value"] == 0.0:
                rec["protein_binding_qualitative"] = 1
            rec["extracted_fields"] += 1

        vd = audited("volume_of_distribution", r["volume_of_distribution"],
                     extract_volume_of_distribution)
        if vd:
            rec["vd_value"], rec["vd_unit"], rec["vd_raw"] = vd["value"], vd["unit"], vd["raw"]
            rec["extracted_fields"] += 1

        cl = audited("clearance", r["clearance"], extract_clearance)
        if cl:
            rec["clearance_min"], rec["clearance_max"] = cl["min"], cl["max"]
            rec["clearance_unit"], rec["clearance_raw"] = cl["unit"], cl["raw"]
            rec["extracted_fields"] += 1

        if rec["extracted_fields"]:
            db.execute(
                """INSERT OR REPLACE INTO x_in_vivo
                   (drugbank_id, name, half_life_h_min, half_life_h_max, half_life_raw,
                    protein_binding_pct, protein_binding_qualitative, protein_binding_raw,
                    vd_value, vd_unit, vd_raw,
                    clearance_min, clearance_max, clearance_unit, clearance_raw,
                    extracted_fields)
                   VALUES (:drugbank_id, :name, :half_life_h_min, :half_life_h_max,
                           :half_life_raw, :protein_binding_pct,
                           :protein_binding_qualitative, :protein_binding_raw,
                           :vd_value, :vd_unit, :vd_raw,
                           :clearance_min, :clearance_max, :clearance_unit,
                           :clearance_raw, :extracted_fields)""",
                rec,
            )

    db.commit()

    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(audit_rows[0].keys()))
        w.writeheader()
        w.writerows(audit_rows)

    print(f"x_in_vivo rows: {db.execute('SELECT COUNT(*) FROM x_in_vivo').fetchone()[0]}")
    for field, (prose_n, ext_n) in cov.items():
        pct = 100.0 * ext_n / prose_n if prose_n else 0.0
        print(f"  {field:24s} prose={prose_n:5d}  extracted={ext_n:5d}  ({pct:.1f}%)")
    print(f"audit CSV: {AUDIT} ({len(audit_rows)} rows, failures included)")

    db.execute(
        "INSERT OR REPLACE INTO manifest (key, value) VALUES (?, ?)",
        ("in_vivo_extracted_at", datetime.now(timezone.utc).isoformat()),
    )
    db.execute(
        "INSERT OR REPLACE INTO manifest (key, value) VALUES (?, ?)",
        ("in_vivo_rule_module", "src/formulation_os/knowledge/in_vivo_extract.py"),
    )
    db.commit()


if __name__ == "__main__":
    main()
