# FormulationOS — Drug Intelligence Database v1
### Milestone report / 里程碑汇报

**Positioning / 定位:** a *formulation-oriented, multi-source, provenance-aware,
offline* drug intelligence database — **architecture + 25-drug validation +
data-source feasibility study**. Not yet a full-scale (thousands-of-drugs)
production database; the 25 drugs are a deliberate validation set.

---

## 1. What it is / 它是什么

A drug database organised around **five formulation-relevant modules**, where
every value carries **where it came from** and **whether it is measured /
predicted / recorded**:

```
Drug → Chemical Form → US / CN Marketed Product → Patent · Exclusivity · Reference
 ①Identity   ②Physicochemical   ③Drug Forms   ④Approved Products   ⑤Patents & Exclusivity
```

**Each module has a designated PRIMARY source + supplements for cross-validation:**

| Module | Primary | Supplements |
|---|---|---|
| ① Identity | PubChem | ChEMBL, DrugBank* |
| ② Physicochemical | PubChem | ChEMBL, DrugBank* (pKa/logS), CompTox† |
| ③ Drug Forms (salt/crystal) | ChEMBL molecule_form | CSD†, DrugBank* |
| ④ Approved Products | FDA openFDA / Drugs@FDA + DailyMed | **NMPA/CDE 参比制剂**, EMA† |
| ⑤ Patents & Exclusivity | **FDA Orange Book** (patent ≠ exclusivity) | USPTO/EPO/WIPO/CNIPA† |

\* local-only, licence-restricted  · † phase-2 framework stub

**Architecture:** offline ETL fetches each source once → local SQLite → runtime
reads **local only, zero network** (a deployed service is fast and reliable).

---

## 2. 25-drug validation results / 25 药验收

| Metric | Result |
|---|---|
| ① Identity (≥4 fields) | **25/25** |
| ② Physicochemical (≥5 fields) | **25/25** |
| ③ Drug Forms (parent/form) | **25/25** |
| ④ Approved Products (US) | **25/25** |
| ⑤ Patents record_found | **11/25** (+14 `no_record`, 0 `source_unavailable`) |
| Provenance on every value | **100%** |
| Entity/form mismatch detection | 2 drugs (e.g. atorvastatin free-acid vs Ca salt) |
| **CN reference-preparation coverage** | **24/25** (Griseofulvin = genuine `no_record`) |
| Runtime network calls | **0** |

Totals across the 25 drugs: **1,165** US marketed products, **583** US
patent/exclusivity records, **288** CN reference-preparation records.

### Per-drug US vs CN coverage (excerpt)

| Drug | US products | US patents/excl | CN reference | CN holder (sample) |
|---|--:|--:|--:|---|
| Atorvastatin | 68 | 7 | 15 | Pfizer Prism CV |
| Metformin | 61 | 9 | 20 | Nippon Shinyaku |
| Omeprazole | 41 | 0 | 19 | AstraZeneca AB |
| Empagliflozin | 38 | 508 | 12 | Boehringer Ingelheim |
| Diclofenac | 40 | 24 | 12 | Glenwood GmbH |
| Griseofulvin | 43 | 0 | 0 (no_record) | — |

*(full 25-row table in the repo)*

---

## 3. Data-source accessibility study / 数据源可达性(真实调研)

A genuine research finding — what is and isn't obtainable:

| Source | Access | Verdict |
|---|---|---|
| PubChem / ChEMBL / openFDA | free JSON API | ✅ integrated |
| FDA Orange Book | static public file | ✅ integrated (patents/exclusivity) |
| DrugBank full DB | local licensed XML | ✅ integrated, local-only |
| **CDE/NMPA online (目录集/查询)** | **瑞数 anti-bot (HTTP 202 + JS challenge)** | ❌ not machine-accessible |
| **NMPA 参比制剂目录 .doc** | static file (non-瑞数) | ✅ integrated (official) |
| drugfuture.com (参比 compilation) | POST search | ✅ integrated (third-party) |

**CN reference data** was obtained two ways with **honest, separated
provenance**: official NMPA `.doc` (333 rows, `official_file`) + drugfuture
compilation (237 rows, `third_party_compilation`). A **random spot-check of the
overlap agreed 100%** on English name / holder / strength / dosage form.

---

## 4. Methodological rigor / 方法学严谨性

- **Provenance separates authority from channel** — third-party data is never
  labelled `source=CDE`; it records authority=NMPA/CDE + source_type + provider.
- **Entity/form-aware conflicts** — a MW disagreement between parent and salt is
  flagged as an *entity mismatch* (distinct drug_forms), not a value conflict.
- **Three-state status** — `record_found` / `no_record` / `source_unavailable`
  are distinct; "absent" is never silently read as "failed/negative".
- **Salt discipline** — hydrochloride/calcium forms are kept as their own
  products, never merged into the parent molecule to inflate match rates.
- **Reproducible + tested** — offline build scripts; 40+ unit tests over the
  drug-intelligence layer, all passing, zero regression.

---

## 5. Compliance / 合规

- **Public build** (`data/drug_intelligence.db`) = redistributable sources only
  (PubChem, ChEMBL, openFDA, Orange Book) — committable & deployable.
- **Local build** (`*.local.db`) adds DrugBank + CN data — licence-restricted,
  git-ignored, **never deployed** (CDE/NMPA are "All Rights Reserved").

---

## 6. Honest boundaries / 边界(主动披露)

- CN side is **reference preparations only** — the CDE 目录集's *收录类别 /
  一致性评价* fields are behind the 瑞数 wall (need a manual browser export).
- **25-drug validation set**, not yet scaled to thousands.
- drugfuture per-drug search caps at 20 results/drug (pagination is future work).
- Full CN *marketed-product base* (NMPA registration universe) not yet ingested
  (NMPA online is the hardest 瑞数 site; enumeration blocked).

---

## 7. Reproduce / 复现

```
python scripts/build_drug_intelligence.py                     # public (US)
python scripts/fetch_orange_book.py                           # US patents/exclusivity
python scripts/parse_drugbank_xml.py <drugbank.xml.zip>       # DrugBank (local)
python scripts/import_cn_reference_products.py --url <batch.doc> --batch N   # official CN
python scripts/import_cn_reference_drugfuture.py              # CN (25 drugs)
python scripts/cn_reference_spotcheck.py --batch 10 --official <b10.doc>     # QA
python scripts/build_drug_intelligence.py --profile local     # merge all
```
