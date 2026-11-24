# Verification layers — how much of this database can you believe?

One page, one ladder, every number traceable to a frozen snapshot. Read this
before trusting any headline figure.

## The confidence ladder (smaller = stronger)

| subset | definition | A-tier drugs |
|---|---|---|
| A (all) | 3-source field agreement (MW/TPSA/LogP) | **564** |
| A (PubChem verified) | + PubChem CID structurally identical (full InChIKey) | **542** |
| **A (double-verified)** | + ChEMBL mapping structurally identical | **534** |

`x_confidence.pubchem_match_level` / `chembl_match_level` carry the level per
row; queries should default to the double-verified subset for headline claims.

## What structure verification found (the audit that justifies the ladder)

Name-based matching (the obvious weak point) was verified against InChIKey:

* PubChem side (14,992 mapped): 90.5% exact / 3.7% skeleton (salt/protonation,
  flagged) / **2.1% mismatch (312 wrong-structure matches — excluded)** /
  3.7% unverifiable (biologics, no master InChIKey)
* ChEMBL side (2,701 mapped): 78.6% exact / 1.6% skeleton / **0.8% mismatch
  (21 — excluded)** / 19.0% unverifiable
* Mismatch causes, from samples: class-name resolution (Vitamin E → one
  tocopherol), salt variants (Doxycycline → hyclate), isomer collisions
  (Minoxidil). All systematic, all now labelled, none silently included.

## Threshold robustness (are the tolerances arbitrary? No — and we measured)

Frozen sweep (`scripts/build_tolerance_sensitivity.py`):

| tolerance | 1%/2%/5% (MW) | 0.3/0.5/1.0 (LogP) | 10%/15%/25% (TPSA) |
|---|---|---|---|
| A3 count | 2040 / 2042 / 2057 | 284 / 628 / 1328 | 1670 / 1729 / 1799 |

* MW headline is **threshold-robust** (±0.1% over a 5× tolerance range).
* LogP is honest threshold-sensitive: the CONFLICT tier there is *method
  spread*, quantified in `x_logp_analysis` (pairwise MAE 0.67–0.82, means ≈ 0)
  — noise between prediction algorithms, not source corruption.

## Solid-state crosscheck (formulation-core fields, second source)

DrugBank experimental MP/solubility vs PubChem experimental sections
(`x_exp_crosscheck`, both verbatims kept per row):

* Melting point: 586 agree / 154 disagree / 1,059 unparsed (PubChem simply has
  no number for ~half these drugs)
* MP disagreement audit: 90 decomposition-marker, 32 unit-unknown, 13
  polymorph-suspect + 8 salt-form (→ **21 DrugBank correction candidates**),
  11 interval-vs-point
* Solubility: 506 agree / 160 near / 175 disagree / 966 unparsed

## Human verification (the last mile — pending)

`data/processed/gold_audit_sample.csv`: 326 rows, stratified (A / B /
CONFLICT / in-vivo), seed 20261120 frozen, every master value next to every
other source's value, blank verdict columns. Once filled: precision +
Wilson 95% CI. Machine cannot do this step; it is the human-signature layer.

## Reproducibility

* All PubChem responses frozen as JSONL (public domain, committed);
  sha256 in `manifest`. DB builds are offline against these snapshots.
* master.db itself never enters the public repo (DrugBank licence);
  `data/processed/master_fingerprint.json` (row counts + schema + SHA256)
  proves any rebuild reproduced the same state.

## Known limits (stated, not hidden)

* 560 PubChem + 513 ChEMBL mappings unverifiable (biologics/mixtures without
  master InChIKey) — stay at name level, labelled.
* In-vivo extraction precision awaits the human audit above.
* Salt-form (skeleton_match) rows: numeric comparisons are parent-vs-salt and
  are flagged, not force-agreed.
