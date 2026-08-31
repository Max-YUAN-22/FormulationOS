"""China reference-preparation (参比制剂) ingestion — official NMPA .doc batches.

The NMPA/CDE publishes the 仿制药参比制剂目录 in numbered batches, each as a
downloadable Word attachment on a static nmpa.gov.cn path that is NOT behind the
瑞数 anti-bot wall. Those .doc files convert cleanly to a per-cell-per-line table:

    序号 | 药品通用名称 | 英文名称/商品名 | 规格 | 剂型 | 持证商 | 备注1 | 备注2

Each record is exactly 8 lines, delimited by the 序号 token (e.g. "10-1"). This
module holds the pure text parser (testable) + the SQLite writer. The CLI in
scripts/import_cn_reference_products.py handles download + .doc->txt conversion.

Provenance: authority=NMPA/CDE, source_type=official_file (this IS an official
publication) — but still local-only per the gov "All Rights Reserved" caution.
These are reference preparations, so every row carries the unified reference
model: reference_role=CN-CDE-REFERENCE_PREPARATION.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any, Optional

from .cn_catalog_ingest import parse_strength

REFERENCE_DB_COLUMNS = [
    "batch", "seq", "drug_name", "drug_name_en", "trade_name",
    "strength", "strength_value", "strength_unit", "dosage_form",
    "holder", "note", "reference_status",
    "authority", "source_type", "source_provider", "source_file",
    "snapshot_date", "official_reference", "ingested_at",
]

_SEQ_RE = re.compile(r"^\s*(\d+\s*[-–—]\s*\d+)\s*$")
_EMPTY = ("", "　", "-", "—", "————")


def _clean(s: str) -> str:
    return s.replace("　", " ").strip() if s else ""


def _reference_status(note: str) -> str:
    n = note or ""
    if "原研进口" in n:
        return "originator_imported"
    if "原研" in n and "产化" in n:
        return "originator_localized"
    if "原研" in n:
        return "originator"
    if any(t in n for t in ("欧盟上市", "美国上市", "日本上市", "境外上市")):
        return "overseas_marketed"
    if "国内" in n:
        return "domestic"
    return "unspecified"


def parse_reference_doc_text(txt: str, batch: str) -> list[dict[str, Any]]:
    """Parse textutil-converted 参比制剂 .doc text into records."""
    lines = [ln.rstrip() for ln in txt.splitlines()]
    records: list[dict[str, Any]] = []

    # collect (seq, [following non-seq lines until next seq])
    i = 0
    n = len(lines)
    while i < n:
        m = _SEQ_RE.match(lines[i])
        if not m:
            i += 1
            continue
        seq = re.sub(r"\s+", "", m.group(1))
        cells: list[str] = []
        j = i + 1
        while j < n and not _SEQ_RE.match(lines[j]):
            cells.append(lines[j])
            j += 1
        i = j

        # positional cells: 通用名, 英文名/商品名, 规格, 剂型, 持证商, 备注1, (备注2)
        vals = [_clean(c) for c in cells]
        # drop pure-empty trailing cells but keep positions for the first 6
        def cell(k: int) -> str:
            return vals[k] if k < len(vals) else ""

        drug_name = cell(0)
        en_trade = cell(1)
        strength = cell(2)
        dosage_form = cell(3)
        holder = cell(4)
        note = " ".join(v for v in (cell(5), cell(6)) if v and v not in _EMPTY).strip()

        if not drug_name and not en_trade:
            continue

        # "English Name/Trade" -> split on the first slash
        drug_name_en, trade_name = en_trade, ""
        if "/" in en_trade:
            left, right = en_trade.split("/", 1)
            drug_name_en, trade_name = left.strip(), right.strip()

        sv, su = parse_strength(strength)
        records.append({
            "batch": batch,
            "seq": seq,
            "drug_name": drug_name or None,
            "drug_name_en": drug_name_en or None,
            "trade_name": trade_name or None,
            "strength": strength or None,
            "strength_value": sv,
            "strength_unit": su,
            "dosage_form": dosage_form or None,
            "holder": holder or None,
            "note": note or None,
            "reference_status": _reference_status(note),
        })
    return records


def init_reference_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cols = ", ".join(f"{c} TEXT" for c in REFERENCE_DB_COLUMNS)
    conn.execute(f"CREATE TABLE IF NOT EXISTS reference_products ({cols})")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ref_en ON reference_products(drug_name_en COLLATE NOCASE)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ref_seq ON reference_products(batch, seq)")
    conn.commit()
    conn.close()


def write_reference_records(db_path: str, records: list[dict[str, Any]], provenance: dict[str, Any]) -> int:
    init_reference_db(db_path)
    conn = sqlite3.connect(db_path)
    ph = ",".join("?" for _ in REFERENCE_DB_COLUMNS)
    rows = []
    for r in records:
        merged = {**r, **provenance}
        rows.append([_txt(merged.get(c)) for c in REFERENCE_DB_COLUMNS])
    conn.executemany(
        f"INSERT INTO reference_products ({','.join(REFERENCE_DB_COLUMNS)}) VALUES ({ph})", rows
    )
    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM reference_products").fetchone()[0]
    conn.close()
    return total


def _txt(v: Any) -> Optional[str]:
    return None if v is None else str(v)


# -- drugfuture.com/refdrug consolidated browse pages (third-party) -------------
# 11-column rows: 序号 | 通用名 | 英文名/商品名 | 规格 | 剂型 | 持证商 |
#                 来源分类 | (空) | 备注 | 来源批次 | 公布日期
import re as _re


def parse_drugfuture_page(html: str) -> list[dict[str, Any]]:
    """Parse one drugfuture browse page into reference records."""
    out: list[dict[str, Any]] = []
    for tr in _re.findall(r"<tr[^>]*>(.*?)</tr>", html, _re.S):
        tds = _re.findall(r"<td[^>]*>(.*?)</td>", tr, _re.S)
        cells = [_re.sub(r"<[^>]+>", "", c).replace("&nbsp;", " ").strip() for c in tds]
        if not cells or not _re.match(r"^\d+-\d+$", cells[0]):
            continue

        def c(i: int) -> str:
            return cells[i] if i < len(cells) else ""

        en_trade = c(2)
        drug_name_en, trade_name = en_trade, ""
        if "/" in en_trade:
            drug_name_en, trade_name = [x.strip() for x in en_trade.split("/", 1)]
        strength = c(3)
        sv, su = parse_strength(strength)
        batch_raw = c(9)
        note = c(8)
        out.append({
            "batch": _batch_num(batch_raw) or batch_raw,
            "seq": c(0),
            "drug_name": c(1) or None,
            "drug_name_en": drug_name_en or None,
            "trade_name": trade_name or None,
            "strength": strength or None,
            "strength_value": sv,
            "strength_unit": su,
            "dosage_form": c(4) or None,
            "holder": c(5) or None,
            "note": (c(6) + (" " + note if note else "")).strip() or None,  # 来源分类 + 备注
            "reference_status": _reference_status(c(6) or note),
        })
    return out


_CN_NUM = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
           "六": 6, "七": 7, "八": 8, "九": 9, "十": 10, "百": 100}


def _batch_num(text: str) -> Optional[str]:
    """'参比制剂目录第一百零六批' -> '106' (best-effort)."""
    m = _re.search(r"第([零一二三四五六七八九十百]+)批", text or "")
    if not m:
        m2 = _re.search(r"第\s*(\d+)\s*批", text or "")
        return m2.group(1) if m2 else None
    s, total, section = m.group(1), 0, 0
    for ch in s:
        v = _CN_NUM.get(ch, 0)
        if v == 100:
            section = (section or 1) * 100
            total += section
            section = 0
        elif v == 10:
            section = (section or 1) * 10
            total += section
            section = 0
        else:
            section += v
    total += section
    return str(total) if total else None

