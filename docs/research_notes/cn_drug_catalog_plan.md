# China Marketed-Drug Catalog (NMPA/CDE) — Integration Plan v1

Status: **approved, implementation gated on a sample third-party Excel file.**
Scope this round: China `approved_products` + reference-product + consistency
status. No other modules.

## Sourcing decision & licence handling

- Acquisition: **third-party consolidated Excel** (compiled from CDE 中国上市药品
  目录集 / 参比制剂目录). User supplies the sample file.
- Licence: CDE pages carry "All Rights Reserved"; third-party compilations have
  unclear redistribution rights. Therefore the China DB is treated exactly like
  DrugBank: **local-only**.
  - built to `data/nmpa_cde/nmpa_cde.db` → git-ignored (`*.db`), never committed
  - merged only into `data/drug_intelligence.local.db` (build `--profile local`)
  - **never** into the public `data/drug_intelligence.db`, never deployed
- A future `import_cde_official.py` (from CDE year-end electronic edition) can
  feed a redistributable build once licence terms are confirmed.

## Provenance — separate the *authority* from the *channel* (constraint 1)

Do NOT tag third-party data as `source=CDE`. Every CN value carries:

    authority           = "NMPA/CDE"          # who is the factual authority
    source_type         = "third_party_compilation"
    source_provider     = "<provider name>"   # who compiled the Excel
    source_file         = "<filename.xlsx>"
    source_snapshot_date= "<edition/version date from the file>"
    official_reference  = "https://www.cde.org.cn/hymlj/..."   # canonical page
    ingested_at         = "<ETL run timestamp>"

## Scripts (constraint 2)

- `scripts/import_cn_drug_catalog.py` (a.k.a. import_nmpa_cde_excel) — parse the
  third-party Excel → `data/nmpa_cde/nmpa_cde.db`. NOT named fetch_* (nothing is
  fetched from NMPA/CDE directly).
- Reserved for later: `scripts/import_cde_official.py` — official CDE files.

## Reference-product model — do NOT equate CN 参比制剂 with US RLD (constraint 3)

Unified structure, region/authority/role preserved:

    reference_product:
      region          # US | CN
      authority       # FDA | CDE
      reference_role  # RLD | RS | REFERENCE_PREPARATION
      is_reference    # bool
      product_ref     # link to the marketed product / identifier

Examples: US-FDA-RLD, US-FDA-RS, CN-CDE-REFERENCE_PREPARATION.
(US RLD/RS currently live as fields on OB/openFDA product records; migrate them
into this model incrementally — CN emits the new model from the start.)

## approved_products — CN fields (constraint 4)

Add/normalise:
- `route` (给药途径), `catalog_category` (收录类别)
- `region` = "CN", plus: drug_name/_en, trade_name/_en, active_ingredient/_en,
  dosage_form, strength, approval_number (批准文号/注册证号), mah (上市许可持有人),
  manufacturer (生产厂商), first_approval_date, marketing_status, atc_code,
  te_code, reference_preparation, standard_product
- `consistency_evaluation_status` (enum, NOT bool):
    passed | not_applicable | unknown | inferred_from_catalog_category
  "not in the sheet" must NEVER auto-map to "not passed".

## Import → quality report FIRST, then attach to drugs (constraint 5)

Acceptance is the quality report, not "import succeeded". First-round metrics:
- total rows; unique approval_number / product / active_ingredient counts
- missing % for: active_ingredient_en, approval_number, strength, dosage_form
- duplicate approval_numbers; fully-duplicate rows
- strength parse rate; top unparseable strength patterns
- DrugResolver match: exact-English-name rate, alias rate, unmatched active
  ingredients (count + samples)

## Entity/form discipline carries over (constraint 6)

Keep v1 layering: **canonical identity → chemical form → product**.
Do NOT collapse 盐酸二甲双胍/Metformin Hydrochloride into Metformin (parent) just
to raise match rate. Salt-specific forms map to distinct drug_forms; the product
links to the specific form, which links to the parent.

Target hierarchy after this round:
**Drug → Chemical Form → US/CN Marketed Product → Patent/Exclusivity/Reference**

## Sequence

1. (now) schema groundwork: provenance fields, consistency enum, reference roles.
2. (on sample file) column mapping → `import_cn_drug_catalog.py` → nmpa_cde.db.
3. full-catalog quality report (above metrics).
4. `NmpaCdeAdapter` (local-only) → attach CN data to the existing 25 drugs.
5. per-drug US-vs-CN coverage report. Stop; no other modules.
