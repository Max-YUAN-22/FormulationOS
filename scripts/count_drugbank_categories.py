#!/usr/bin/env python3
"""Count exact drug categories from the raw DrugBank XML (depth-aware).

Resolves the 19,857 vs 11,511 discrepancy: counts only TOP-LEVEL <drug>
elements (depth-tracked iterparse, excluding nested interaction <drug>),
broken down by their <groups> membership.

    python scripts/count_drugbank_categories.py "path/to/full database.xml"
"""

import sys
import xml.etree.ElementTree as ET
from collections import Counter

CATS = ["approved", "investigational", "experimental", "nutraceutical", "illicit", "withdrawn", "veterinary"]


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "/Users/Apple/Desktop/Year 4/FYP HSCI4000/Drugbank下载/full database.xml"
    depth = 0
    total_top = 0
    cat_counter: Counter = Counter()
    combo: Counter = Counter()
    type_counter: Counter = Counter()

    for event, elem in ET.iterparse(path, events=("start", "end")):
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
        # 顶级药物条目
        total_top += 1
        t = elem.get("type")
        if t:
            type_counter[t] += 1
        groups = [g.text.strip().lower() for g in elem.iter() if g.tag.endswith("group") and g.text]
        groups = [g for g in groups if g in CATS]
        for g in groups:
            cat_counter[g] += 1
        combo["+".join(sorted(set(groups))[:3])] += 1
        elem.clear()

    print(f"顶级药物条目总数: {total_top:,}")
    print("\n按类型:")
    for k, v in type_counter.most_common():
        print(f"  {k}: {v:,}")
    print("\n按收录类别(每药可属多类):")
    for c in CATS:
        print(f"  {c.capitalize()}: {cat_counter.get(c, 0):,}")
    print("\nTop 组合:")
    for k, v in combo.most_common(8):
        print(f"  {k}: {v:,}")


if __name__ == "__main__":
    main()
