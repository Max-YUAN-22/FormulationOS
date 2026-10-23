#!/usr/bin/env python3
"""Extract VERBATIM DrugBank <groups> per top-level drug into the master spine.

Rules ("不能乱改" guarantees):
  * group strings are stored VERBATIM as they appear in the official XML
    (no translation, no mapping, no filtering);
  * boolean flags are DERIVED 1:1 from the verbatim strings (case-insensitive
    exact match), never inferred;
  * source file identity is pinned by SHA256 recorded in the build manifest
    table, so any future re-run can prove the input is unchanged.

Writes to master.db: x_groups table + manifest row.
    python scripts/add_drugbank_groups.py "<full database.xml>"
"""

from __future__ import annotations

import hashlib
import sqlite3
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

CATS = ("approved", "investigational", "experimental",
        "withdrawn", "illicit", "nutraceutical", "veterinary")


def main() -> None:
    xml_path = sys.argv[1] if len(sys.argv) > 1 else \
        "/Users/Apple/Desktop/Year 4/FYP HSCI4000/Drugbank下载/full database.xml"
    print(f"源文件: {xml_path}")
    print("计算 SHA256(防篡改锚)…", flush=True)
    h = hashlib.sha256()
    with open(xml_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    sha = h.hexdigest()
    print(f"  SHA256 = {sha}")

    out = sqlite3.connect("data/master/master.db")
    out.executescript(
        """
        DROP TABLE IF EXISTS x_groups;
        CREATE TABLE x_groups (
            drugbank_id TEXT PRIMARY KEY,
            name TEXT,
            groups_verbatim TEXT,        -- 官方 XML 原文,逐字保留(顿号连接)
            is_approved INTEGER, is_investigational INTEGER,
            is_experimental INTEGER, is_withdrawn INTEGER,
            is_illicit INTEGER, is_nutraceutical INTEGER,
            is_veterinary INTEGER
        );
        INSERT INTO manifest VALUES ('drugbank_xml_sha256', ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value;
        INSERT INTO manifest VALUES ('drugbank_xml_version', '5.1.19')
            ON CONFLICT(key) DO UPDATE SET value=excluded.value;
        INSERT INTO manifest VALUES ('groups_extracted_at', ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value;
        """
    )
    out.execute(
        "INSERT INTO manifest VALUES ('drugbank_xml_sha256', ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (sha,),
    )
    out.execute(
        "INSERT INTO manifest VALUES ('groups_extracted_at', ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (datetime.now(timezone.utc).isoformat(),),
    )

    depth = 0
    total = 0
    from collections import Counter
    cats = Counter()
    buf = []

    for event, elem in ET.iterparse(xml_path, events=("start", "end")):
        tag = elem.tag.split("}")[-1]
        if event == "start":
            if tag == "drug":
                depth += 1
            continue
        if tag != "drug":
            continue
        depth -= 1
        if depth != 0:
            elem.clear()
            continue
        total += 1

        dbid = None
        for d in elem.iter():
            if d.tag.endswith("drugbank-id") and d.get("primary") == "true":
                dbid = (d.text or "").strip()
                break
        if dbid is None:
            for d in elem.iter():
                if d.tag.endswith("drugbank-id"):
                    dbid = (d.text or "").strip()
                    break
        name = next((d.text for d in elem.iter()
                     if d.tag.endswith("name")), None)
        groups_verbatim = [g.text for g in elem.iter()
                           if g.tag.endswith("group") and g.text]
        gv = ", ".join(groups_verbatim)
        low = {g.lower() for g in groups_verbatim}
        flags = {c: int(c in low) for c in CATS}
        for c in CATS:
            cats[c] += flags[c]

        buf.append((
            dbid, name, gv,
            flags["approved"], flags["investigational"], flags["experimental"],
            flags["withdrawn"], flags["illicit"], flags["nutraceutical"],
            flags["veterinary"],
        ))
        if total % 5000 == 0:
            print(f"  … {total:,} 条", flush=True)
        elem.clear()

    out.executemany("INSERT OR REPLACE INTO x_groups VALUES (?,?,?,?,?,?,?,?,?,?)", buf)
    out.commit()

    print(f"\n✅ x_groups: {total:,} 行(覆盖率 {total:,}/19,857)")
    print("分类计数(必须与上次扫描完全一致,否则判失败):")
    expect = {"approved": 4799, "investigational": 8547, "experimental": 8864,
              "withdrawn": 914, "illicit": 205, "nutraceutical": 135}
    ok = True
    for c in CATS:
        e = expect.get(c)
        mark = "✓" if (e is None or e == cats[c]) else "✗ 不一致!"
        if e is not None and e != cats[c]:
            ok = False
        print(f"  {c.capitalize()}: {cats[c]:,}  {mark} (期望 {e})")
    print("VERDICT:", "PASS" if ok else "FAIL")
    out.close()


if __name__ == "__main__":
    main()
