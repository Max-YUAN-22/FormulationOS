"""China marketed-drug catalog ingestion (NMPA/CDE via third-party compilation).

Pure, testable ingestion logic — no Excel/pandas dependency here (the CLI in
``scripts/import_cn_drug_catalog.py`` reads the workbook and feeds rows in). This
keeps the header-alias resolution, strength parsing, consistency-status
derivation and DB writing unit-testable on synthetic rows.

The 《中国上市药品目录集》 column set is standardised; we resolve real headers
against alias lists so a third-party compilation that renames/re-orders columns
still maps correctly.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any, Optional

from .sources.schema import (
    CONSISTENCY_INFERRED,
    CONSISTENCY_NOT_APPLICABLE,
    CONSISTENCY_PASSED,
    CONSISTENCY_UNKNOWN,
)

# Canonical logical field -> candidate header strings (Chinese + English variants).
# Comparison is done after normalising whitespace and full/half-width parens.
HEADER_ALIASES: dict[str, list[str]] = {
    "active_ingredient":    ["活性成分", "通用名(活性成分)", "成分"],
    "active_ingredient_en": ["活性成分(英文)", "活性成分英文", "英文活性成分", "active ingredient", "active_ingredient_en"],
    "drug_name":            ["药品名称", "通用名", "药品通用名"],
    "drug_name_en":         ["药品名称(英文)", "药品英文名", "英文名称", "drug name", "drug_name_en"],
    "trade_name":           ["商品名", "商品名称"],
    "trade_name_en":        ["商品名(英文)", "商品名英文", "trade name"],
    "dosage_form":          ["剂型"],
    "route":                ["给药途径", "给药方式"],
    "strength":             ["规格"],
    "reference_preparation":["参比制剂"],
    "standard_product":     ["标准制剂"],
    "te_code":              ["治疗等效性评价代码", "治疗等效性代码", "te代码", "te code"],
    "atc_code":             ["atc代码", "atc", "解剖学治疗学及化学分类代码", "解剖学治疗学及化学分类系统代码"],
    "approval_number":      ["批准文号/注册证号", "批准文号", "注册证号", "批准文号(注册证号)"],
    "mah":                  ["上市许可持有人", "持有人", "上市许可持有人(mah)"],
    "manufacturer":         ["生产厂商", "生产企业", "生产单位"],
    "first_approval_date":  ["首次批准日期", "批准日期", "首次上市日期"],
    "marketing_status":     ["上市销售状态", "上市销售状况", "销售状态"],
    "catalog_category":     ["收录类别", "类别"],
    # optional explicit consistency column (some compilations add one)
    "consistency_raw":      ["一致性评价", "一致性评价情况", "是否通过一致性评价", "一致性评价状态"],
    "is_reference_raw":     ["是否参比制剂", "参比制剂标识"],
}

DB_COLUMNS = [
    "active_ingredient", "active_ingredient_en", "drug_name", "drug_name_en",
    "trade_name", "trade_name_en", "dosage_form", "route", "strength",
    "strength_value", "strength_unit",
    "reference_preparation", "standard_product", "is_reference_preparation",
    "te_code", "atc_code", "approval_number", "mah", "manufacturer",
    "first_approval_date", "marketing_status", "catalog_category",
    "consistency_evaluation_status",
    # provenance (authority separated from channel)
    "authority", "source_type", "source_provider", "source_file",
    "snapshot_date", "official_reference", "ingested_at",
]


def _norm_header(h: str) -> str:
    if h is None:
        return ""
    s = str(h).strip().lower()
    s = s.replace("（", "(").replace("）", ")").replace("：", ":")
    s = re.sub(r"\s+", "", s)
    return s


def resolve_headers(columns: list[str]) -> dict[str, str]:
    """Map canonical field -> actual column name present in the sheet."""
    norm_to_actual = {_norm_header(c): c for c in columns}
    mapping: dict[str, str] = {}
    for field, aliases in HEADER_ALIASES.items():
        for alias in aliases:
            key = _norm_header(alias)
            if key in norm_to_actual:
                mapping[field] = norm_to_actual[key]
                break
    return mapping


_STRENGTH_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(mg/ml|mg/g|μg|ug|mcg|mg|g|ml|l|iu|u|%|万单位|单位)",
    re.IGNORECASE,
)


def parse_strength(raw: Optional[str]) -> tuple[Optional[float], Optional[str]]:
    """Best-effort (value, unit) from a strength string. Raw is always kept."""
    if not raw:
        return None, None
    m = _STRENGTH_RE.search(str(raw))
    if not m:
        return None, None
    try:
        return float(m.group(1)), m.group(2).lower()
    except ValueError:
        return None, m.group(2).lower()


# Category strings that indicate an innovator / imported originator (consistency
# evaluation not applicable) vs a generic that passed it.
_CAT_INNOVATOR = ("创新", "改良", "进口原研", "原研")
_CAT_PASSED = ("通过", "一致性评价")
_PASS_TOKENS = ("通过", "是", "yes", "passed", "true", "1")


def derive_consistency_status(
    consistency_raw: Optional[str],
    catalog_category: Optional[str],
) -> str:
    """Map to an explicit status. Absence is NEVER 'failed'.

    - explicit column says passed         -> passed
    - explicit column present but negative -> unknown (we don't assert 'failed')
    - no explicit column, category implies passed -> inferred_from_catalog_category
    - category is innovator/imported originator    -> not_applicable
    - otherwise                                     -> unknown
    """
    if consistency_raw:
        val = str(consistency_raw).strip().lower()
        if any(tok in val for tok in _PASS_TOKENS):
            return CONSISTENCY_PASSED
        return CONSISTENCY_UNKNOWN
    cat = str(catalog_category or "")
    if any(t in cat for t in _CAT_INNOVATOR):
        return CONSISTENCY_NOT_APPLICABLE
    if any(t in cat for t in _CAT_PASSED):
        return CONSISTENCY_INFERRED
    return CONSISTENCY_UNKNOWN


def _truthy(v: Any) -> bool:
    return str(v).strip().lower() in _PASS_TOKENS if v is not None else False


def normalize_row(raw: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    """Turn one raw sheet row into a normalized record (dict of DB_COLUMNS)."""
    def get(field: str) -> Optional[Any]:
        col = mapping.get(field)
        if col is None:
            return None
        v = raw.get(col)
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    rec: dict[str, Any] = {c: None for c in DB_COLUMNS}
    for field in HEADER_ALIASES:
        if field in ("consistency_raw", "is_reference_raw"):
            continue
        if field in rec:
            rec[field] = get(field)

    sv, su = parse_strength(rec.get("strength"))
    rec["strength_value"], rec["strength_unit"] = sv, su
    rec["is_reference_preparation"] = 1 if _truthy(get("is_reference_raw")) else 0
    rec["consistency_evaluation_status"] = derive_consistency_status(
        get("consistency_raw"), rec.get("catalog_category")
    )
    return rec


# -- SQLite ---------------------------------------------------------------------

def init_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cols = ", ".join(f"{c} TEXT" for c in DB_COLUMNS)
    conn.execute(f"CREATE TABLE IF NOT EXISTS marketed_products ({cols})")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cn_ing_en ON marketed_products(active_ingredient_en COLLATE NOCASE)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cn_approval ON marketed_products(approval_number)")
    conn.commit()
    conn.close()


def write_records(db_path: str, records: list[dict[str, Any]]) -> int:
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    placeholders = ",".join("?" for _ in DB_COLUMNS)
    conn.executemany(
        f"INSERT INTO marketed_products ({','.join(DB_COLUMNS)}) VALUES ({placeholders})",
        [[_to_text(r.get(c)) for c in DB_COLUMNS] for r in records],
    )
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM marketed_products").fetchone()[0]
    conn.close()
    return n


def _to_text(v: Any) -> Optional[str]:
    if v is None:
        return None
    return str(v)


# -- web-compilation parser: 药学数据中心 pharm.ncmi.cn detail pages -------------
# These accessible (non-瑞数) pages carry NMPA registration records in a
# 【label】：value format. This is registration-level data (NOT the CDE 目录集), so
# provenance is tagged source_type=web_compilation, authority=NMPA — never CDE.

# NCMI 【label】 -> our canonical field. 产品类别 (化学药品) is a drug *type*, NOT
# the CDE 收录类别, so it is deliberately NOT mapped to catalog_category.
NCMI_LABEL_MAP = {
    "注册证号": "approval_number",
    "批准文号": "approval_number",
    "产品名称（中文）": "drug_name",
    "产品名称（英文）": "drug_name_en",
    "商品名（中文）": "trade_name",
    "商品名（英文）": "trade_name_en",
    "剂型（中文）": "dosage_form",
    "规格（中文）": "strength",
    "上市许可持有人中文名称": "mah",
    "上市许可持有人英文名称": "mah_en",
    "生产厂商（中文）": "manufacturer",
    "生产厂商（英文）": "manufacturer_en",
    "发证日期": "first_approval_date",
}


def parse_ncmi_detail(html: str) -> dict[str, Any]:
    """Parse a pharm.ncmi.cn drug detail page into canonical fields."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    pairs = re.findall(r"【([^】]+)】\s*[:：]\s*([^【]*)", text)
    raw: dict[str, str] = {}
    for label, val in pairs:
        v = val.strip()
        if v and v not in ("————", "-", "—"):
            raw[label.strip()] = v

    rec: dict[str, Any] = {}
    for label, field in NCMI_LABEL_MAP.items():
        if label in raw and not rec.get(field):
            rec[field] = raw[label]
    # prefer Chinese MAH/manufacturer, fall back to English
    if not rec.get("mah") and rec.get("mah_en"):
        rec["mah"] = rec.pop("mah_en")
    if not rec.get("manufacturer") and rec.get("manufacturer_en"):
        rec["manufacturer"] = rec.pop("manufacturer_en")
    rec.pop("mah_en", None)
    rec.pop("manufacturer_en", None)
    return rec


def build_web_record(
    parsed: dict[str, Any],
    active_ingredient_en: str,
    provenance: dict[str, Any],
) -> dict[str, Any]:
    """Turn a parsed web record into a full marketed_products row.

    ``active_ingredient_en`` is the canonical English name of the drug this page
    was found for (so matching works); the page's own product name is kept in
    drug_name_en. Salt-specific product names are NOT rewritten to the parent.
    """
    rec: dict[str, Any] = {c: None for c in DB_COLUMNS}
    for k, v in parsed.items():
        if k in rec:
            rec[k] = v
    rec["active_ingredient_en"] = active_ingredient_en
    sv, su = parse_strength(rec.get("strength"))
    rec["strength_value"], rec["strength_unit"] = sv, su
    rec["is_reference_preparation"] = 0
    # No CDE 收录类别 here -> consistency genuinely unknown (never assume failed).
    rec["consistency_evaluation_status"] = "unknown"
    rec.update(provenance)
    return rec



# -- data-quality report --------------------------------------------------------

_SALT_TOKENS = [
    "hydrochloride", "hcl", "calcium", "sodium", "potassium", "magnesium",
    "sulfate", "sulphate", "mesylate", "besylate", "maleate", "citrate",
    "tartrate", "phosphate", "acetate", "fumarate", "succinate", "lysine",
    "bromide", "chloride", "nitrate", "hydrate", "dihydrate", "monohydrate",
    "hemihydrate", "hydrobromide", "bitartrate", "pamoate", "valerate",
]


def strip_salt(name: str) -> str:
    """Remove trailing salt/hydrate tokens — for MATCHING ONLY, never for merging."""
    s = " ".join(str(name).strip().lower().split())
    changed = True
    while changed:
        changed = False
        for tok in _SALT_TOKENS:
            if s.endswith(" " + tok):
                s = s[: -(len(tok) + 1)].strip()
                changed = True
    return s


def classify_match(ingredient_en: Optional[str], targets_lower: set[str], resolver) -> str:
    """How a CN active-ingredient (English) relates to our target drug set.

    Returns one of: exact | alias | parent_via_salt | unmatched | no_ingredient_en.
    parent_via_salt is reported SEPARATELY so we never silently fold a salt into
    the parent molecule (constraint 6).
    """
    if not ingredient_en:
        return "no_ingredient_en"
    s = " ".join(str(ingredient_en).strip().lower().split())
    if s in targets_lower:
        return "exact"
    if resolver is not None and resolver.resolve(ingredient_en).preferred_name.lower() in targets_lower:
        return "alias"
    base = strip_salt(s)
    if base and base != s:
        if base in targets_lower:
            return "parent_via_salt"
        if resolver is not None and resolver.resolve(base).preferred_name.lower() in targets_lower:
            return "parent_via_salt"
    return "unmatched"


def quality_report(db_path: str, target_names: Optional[list[str]] = None, resolver=None) -> dict[str, Any]:
    """Compute the acceptance metrics for an imported China catalog DB."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM marketed_products").fetchall()
    conn.close()

    total = len(rows)
    approvals = [r["approval_number"] for r in rows if r["approval_number"]]
    ings_en = [r["active_ingredient_en"] for r in rows if r["active_ingredient_en"]]
    products = {(r["drug_name"], r["approval_number"]) for r in rows}

    def missing(col: str) -> float:
        n = sum(1 for r in rows if not r[col])
        return round(100 * n / total, 1) if total else 0.0

    strength_parsed = sum(1 for r in rows if r["strength_value"])
    strength_have = sum(1 for r in rows if r["strength"])

    # duplicate detection
    from collections import Counter
    appr_counts = Counter(approvals)
    dup_approvals = sum(c for c in appr_counts.values() if c > 1) - sum(1 for c in appr_counts.values() if c > 1)
    full_rows = [tuple((r[c] or "") for c in DB_COLUMNS if c not in ("ingested_at",)) for r in rows]
    full_dupes = len(full_rows) - len(set(full_rows))

    report: dict[str, Any] = {
        "total_rows": total,
        "unique_approval_numbers": len(set(approvals)),
        "unique_products": len(products),
        "unique_active_ingredients_en": len(set(i.lower() for i in ings_en)),
        "missing_pct": {
            "active_ingredient_en": missing("active_ingredient_en"),
            "approval_number": missing("approval_number"),
            "strength": missing("strength"),
            "dosage_form": missing("dosage_form"),
            "route": missing("route"),
        },
        "duplicate_approval_numbers": dup_approvals,
        "fully_duplicate_rows": full_dupes,
        "strength_parse_rate_pct": round(100 * strength_parsed / strength_have, 1) if strength_have else 0.0,
        "consistency_status_breakdown": dict(Counter(r["consistency_evaluation_status"] for r in rows)),
    }

    if target_names is not None:
        targets_lower = {t.lower() for t in target_names}
        cls = Counter(classify_match(r["active_ingredient_en"], targets_lower, resolver) for r in rows)
        # per-target coverage (how many of our drugs have >=1 CN row)
        matched_targets = set()
        unmatched_samples = []
        for r in rows:
            c = classify_match(r["active_ingredient_en"], targets_lower, resolver)
            if c in ("exact", "alias", "parent_via_salt") and r["active_ingredient_en"]:
                base = strip_salt(r["active_ingredient_en"].lower())
                pref = resolver.resolve(r["active_ingredient_en"]).preferred_name.lower() if resolver else base
                for t in targets_lower:
                    if t in (r["active_ingredient_en"].lower(), base, pref):
                        matched_targets.add(t)
            elif c == "unmatched" and len(unmatched_samples) < 20:
                unmatched_samples.append(r["active_ingredient_en"])
        report["resolver_match"] = {
            "exact": cls.get("exact", 0),
            "alias": cls.get("alias", 0),
            "parent_via_salt": cls.get("parent_via_salt", 0),
            "unmatched": cls.get("unmatched", 0),
            "no_ingredient_en": cls.get("no_ingredient_en", 0),
            "targets_with_cn_data": f"{len(matched_targets)}/{len(targets_lower)}",
            "unmatched_samples": unmatched_samples,
        }
    return report
