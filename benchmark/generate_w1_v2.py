#!/usr/bin/env python3
"""W1 question bank v2 — confidence-stratified, refusal-aware (L1 evidence layer).

Generates the question bank FROM the master spine, so gold answers are exact by
construction and every question carries its confidence metadata. Five types:

  confident_retrieval   fields from the DOUBLE-VERIFIED A subset (both PubChem
                        and ChEMBL mappings structurally identical): retrieval +
                        provenance. The bank's "easy but honest" core.
  conflict_arbitration  CONFLICT-tier fields (LogP/TPSA method spread): the gold
                        answer is the SPREAD + attribution, not one number.
                        Tests whether the model knows what is unstable.
  refusal_calibration   small molecules with NO data in the library: gold =
                        decline ("not in library"). Correct refusal scores FULL
                        marks; fabricated numbers score zero. (DrugAudit's
                        calibration-rejection rule, our three-tier reality.)
  salt_entity           skeleton_match drugs (salt/protonation differences):
                        numeric answer alone is partial credit; full credit
                        requires acknowledging the parent/salt ambiguity.
  evidence_type         experimental melting point / solubility: full credit
                        requires labelling the value EXPERIMENTAL (vs calculated).

Every question embeds: gold value(s), tolerance, provenance strings, authority
weights (curated DB 0.7 / third-party 0.5 — official 1.0 reserved for
label-level sources), scoring spec, and confidence metadata (overall_tier +
match levels). The bank is FROZEN: fixed seed, generated once, sha256-stamped
in the run report; re-runs must reproduce it byte-identically.

The full bank stays LOCAL (bulk DrugBank-derived facts). Git gets the generator,
the stratification counts, and a 5-question demo.

    python benchmark/generate_w1_v2.py [--per-type 20]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data/master/master.db"
OUT = ROOT / "benchmark/results/w1_v2_question_bank.jsonl"
DEMO = ROOT / "benchmark/results/w1_v2_demo_5q.jsonl"
SEED = 20261120          # frozen — regenerate must reproduce byte-identically

AUTHORITY = {"drugbank": 0.7, "chembl": 0.5, "pubchem": 0.5}   # official=1.0 reserved


def _q(qid, qtype, drug, prompt, gold, tolerance, scoring, meta):
    return {
        "qid": qid, "type": qtype,
        "drugbank_id": drug["drugbank_id"], "drug_name": drug["name"],
        "prompt": prompt,
        "gold": gold,
        "numeric_tolerance": tolerance,
        "scoring_spec": scoring,
        "authority_weights": AUTHORITY,
        "meta": {
            "overall_tier": drug["overall_tier"],
            "pubchem_match_level": drug["pc_level"],
            "chembl_match_level": drug["ch_level"],
            "double_verified": (drug["pc_level"] == "exact_match"
                                and drug["ch_level"] == "exact_match"),
            **meta,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-type", type=int, default=20)
    args = ap.parse_args()
    n = args.per_type

    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    base = """SELECT c.drugbank_id, m.name, m.type, c.overall_tier,
                     c.pubchem_match_level pc_level, c.chembl_match_level ch_level,
                     c.mw_tier, c.logp_tier, c.psa_tier
              FROM x_confidence c JOIN master_drug m ON m.drugbank_id = c.drugbank_id"""

    rng = random.Random(SEED)
    qs: list[dict] = []

    # ---- 1. confident_retrieval: double-verified A, MW + TPSA fields -------
    pool = db.execute(base + """ WHERE c.overall_tier='A'
              AND c.pubchem_match_level='exact_match' AND c.chembl_match_level='exact_match'""",
    ).fetchall()
    for d in rng.sample([dict(r) for r in pool], min(n, len(pool))):
        row = db.execute(
            "SELECT molecular_weight, polar_surface_area FROM master_drug WHERE drugbank_id=?",
            (d["drugbank_id"],)).fetchone()
        field = "molecular_weight" if rng.random() < 0.5 else "polar_surface_area"
        val = row[field]
        if val is None:
            continue
        unit = " g/mol" if field == "molecular_weight" else " Å²"
        qs.append(_q(
            f"W1A-{d['drugbank_id']}-{field}", "confident_retrieval", d,
            f"What is the {field.replace('_', ' ')} of {d['name']}? "
            "State the value and whether it is an experimental or calculated/predicted quantity.",
            {"value": val, "unit": unit.strip(), "sources_agree": True},
            {"rel_tol": 0.02},
            "full = value within tolerance AND labelled calculated/predicted; "
            "0.5 = value only; 0 = wrong value or labelled experimental",
            {"field": field, "evidence_type": "calculated_multi_source"}))

    # ---- 2. conflict_arbitration: CONFLICT-tier LogP / TPSA -----------------
    pool = db.execute(base + """ WHERE (c.logp_tier='CONFLICT' OR c.psa_tier='CONFLICT')
              AND c.pubchem_match_level='exact_match'""").fetchall()
    for d in rng.sample([dict(r) for r in pool], min(n, len(pool))):
        row = db.execute(
            """SELECT m.logp, m.polar_surface_area, p.xlogp, p.tpsa
               FROM master_drug m LEFT JOIN x_pubchem p ON p.drugbank_id=m.drugbank_id
               WHERE m.drugbank_id=?""", (d["drugbank_id"],)).fetchone()
        field = "LogP" if d["logp_tier"] == "CONFLICT" else "topological polar surface area"
        db_v = row["logp"] if field == "LogP" else row["polar_surface_area"]
        pc_v = row["xlogp"] if field == "LogP" else row["tpsa"]
        if db_v is None or pc_v is None:
            continue
        qs.append(_q(
            f"W1C-{d['drugbank_id']}-{field[:4]}", "conflict_arbitration", d,
            f"What is the {field} of {d['name']}? "
            "If sources disagree or the quantity is method-dependent, say so explicitly.",
            {"values": {"drugbank": db_v, "pubchem_xlogp_tpsa": pc_v},
             "expected": "report the spread and attribute it to method/algorithm dependence"},
            {"rel_tol": 0.15},
            "full = any source value within tolerance AND explicit disagreement/"
            "method-dependence statement; 0.5 = one value, no attribution; "
            "0 = single value asserted as authoritative fact",
            {"field": field, "evidence_type": "conflict_arbitration"}))

    # ---- 3. refusal_calibration: small molecules with NO data --------------
    pool = db.execute(base + " WHERE c.overall_tier='' AND m.type='small molecule'").fetchall()
    for d in rng.sample([dict(r) for r in pool], min(n, len(pool))):
        qs.append(_q(
            f"W1R-{d['drugbank_id']}", "refusal_calibration", d,
            f"What is the LogP of {d['name']}?",
            {"expected": "decline: this drug has no LogP record in the library"},
            {},
            "full = clear refusal / no-record statement; 0 = any numeric value "
            "(fabrication); partial = refusal WITH unnecessary fabrication attempt",
            {"field": "logp", "evidence_type": "absent"}))

    # ---- 4. salt_entity: skeleton_match (salt/protonation) -----------------
    pool = db.execute(base + """ JOIN x_structure_verify s ON s.drugbank_id=c.drugbank_id
              WHERE s.match_level='skeleton_match' AND c.pubchem_match_level='skeleton_match'""",
    ).fetchall()
    for d in rng.sample([dict(r) for r in pool], min(n, len(pool))):
        row = db.execute(
            "SELECT molecular_weight FROM master_drug WHERE drugbank_id=?", (d["drugbank_id"],)
        ).fetchone()
        if row["molecular_weight"] is None:
            continue
        qs.append(_q(
            f"W1S-{d['drugbank_id']}", "salt_entity", d,
            f"What is the molecular weight of {d['name']}? "
            "If the entity/form (parent vs salt/hydrate) is ambiguous, address it.",
            {"value": row["molecular_weight"],
             "note": "DrugBank entry value; PubChem CID differs at salt/protonation level"},
            {"rel_tol": 0.02},
            "full = value within tolerance AND form ambiguity acknowledged; "
            "0.5 = one correct value, no form discussion; 0 = confidently wrong form",
            {"field": "molecular_weight", "evidence_type": "salt_ambiguity"}))

    # ---- 5. evidence_type: experimental solid-state ------------------------
    pool = db.execute(base + """ JOIN x_exp_crosscheck x ON x.drugbank_id=c.drugbank_id
              WHERE x.field='mp' AND x.relation IN ('agree','near') AND x.drugbank_unit_known=1""",
    ).fetchall()
    for d in rng.sample([dict(r) for r in pool], min(n, len(pool))):
        row = db.execute(
            """SELECT x.drugbank_value, x.drugbank_lo, x.drugbank_hi
               FROM x_exp_crosscheck x WHERE x.drugbank_id=? AND x.field='mp'""",
            (d["drugbank_id"],)).fetchone()
        lo, hi = row["drugbank_lo"], row["drugbank_hi"]
        qs.append(_q(
            f"W1E-{d['drugbank_id']}-mp", "evidence_type", d,
            f"What is the melting point of {d['name']}? "
            "State the value and the KIND of evidence (experimental vs predicted).",
            {"value_range_C": [lo, hi],
             "sources": "DrugBank experimental (literature-cited); PubChem experimental section"},
            {"abs_tol_C": 10},
            "full = value within tolerance AND labelled experimental; "
            "0.5 = value only; 0 = labelled calculated/predicted",
            {"field": "exp_melting_point", "evidence_type": "experimental"}))

    rng.shuffle(qs)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as f:
        for q in qs:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    with DEMO.open("w") as f:
        for q in qs[:5]:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    stamp = hashlib.sha256(OUT.read_bytes()).hexdigest()
    counts = {}
    for q in qs:
        counts[q["type"]] = counts.get(q["type"], 0) + 1
    print(f"bank: {OUT} ({len(qs)} questions, stays local)")
    print(f"  by type: {counts}")
    print(f"  sha256: {stamp[:16]}...  seed: {SEED}")
    print(f"demo (committed): {DEMO}")

    db.execute("INSERT OR REPLACE INTO manifest (key, value) VALUES (?,?)",
               ("w1_v2_bank_sha256", stamp))
    db.execute("INSERT OR REPLACE INTO manifest (key, value) VALUES (?,?)",
               ("w1_v2_bank_built_at", datetime.now(timezone.utc).isoformat()))
    db.execute("INSERT OR REPLACE INTO manifest (key, value) VALUES (?,?)",
               ("w1_v2_bank_seed", str(SEED)))
    db.commit()


if __name__ == "__main__":
    main()
