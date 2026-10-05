#!/usr/bin/env python3
"""Export the curated drug-intelligence set as a deliverable dataset (Excel+CSV).

One row per drug; columns are the formulation-relevant fields the professor's
platform asked for (identity / physicochemical / in-vivo structured ADME /
experimental solid-state / US+CN products / patents), each carrying its source.
Writes:
    data/export/drug_dataset.xlsx   (sheet 1: 数据集, sheet 2: 字段说明)
    data/export/drug_dataset.csv

    python scripts/export_drug_dataset.py [--db data/drug_intelligence.local.db]
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import sqlite3  # noqa: E402


def _first(profile: dict, cat: str, field: str):
    vals = (profile.get(cat) or {}).get(field)
    return vals[0].get("value") if vals else None


def _src(profile: dict, cat: str, field: str):
    vals = (profile.get(cat) or {}).get(field)
    return (vals[0].get("source") or "") if vals else ""


def _num_range(v):
    """structured dict {'min','max','unit'} -> (min, max, unit)."""
    if isinstance(v, dict):
        return v.get("min"), v.get("max"), v.get("unit", "")
    return None, None, ""


def _lookup_tables():
    """Name-keyed aux tables from local drugbank.db + chembl_drugs.db."""
    aux: dict[str, dict] = {}
    try:
        import sqlite3
        c = sqlite3.connect("data/drugbank/drugbank.db")
        c.row_factory = sqlite3.Row
        for r in c.execute(
            "SELECT name, state, classification_superclass, classification_class,"
            " absorption, indication FROM drugs"
        ):
            aux[r["name"].strip().lower()] = {
                "db_state": r["state"],
                "superclass": r["classification_superclass"],
                "class": r["classification_class"],
                "absorption": (r["absorption"] or "")[:300] or None,
                "indication": (r["indication"] or "")[:300] or None,
            }
        c.close()
        c = sqlite3.connect("data/drugbank/chembl_drugs.db")
        for name, first_ap, oral, par, top, bb in c.execute(
            "SELECT name, first_approval, oral, parenteral, topical, black_box FROM drugs"
        ):
            key = (name or "").strip().lower()
            if key in aux:
                aux[key].update({
                    "first_approval": first_ap, "oral": oral,
                    "parenteral": par, "topical": top, "black_box": bb,
                })
        c.close()
    except Exception:
        pass
    return aux


def row_for(profile: dict, aux: dict[str, dict] | None = None) -> dict:
    name = profile.get("preferred_name") or profile.get("query", "")
    iv = profile.get("in_vivo", {})
    ss = profile.get("solid_state", {})
    ph = profile.get("physicochemical", {})
    ident = profile.get("identity", {})
    a = (aux or {}).get(name.strip().lower(), {})

    hl_min, hl_max, _ = _num_range(_first(profile, "in_vivo", "half_life_h"))
    pb_raw = _first(profile, "in_vivo", "protein_binding_pct")
    pb = pb_raw.get("value") if isinstance(pb_raw, dict) else pb_raw
    vd = _first(profile, "in_vivo", "vd") or {}
    cl = _first(profile, "in_vivo", "clearance_structured") or {}
    cl_txt = ""
    if cl:
        cl_txt = (f"{cl.get('min')}–{cl.get('max')}" if cl.get("min") != cl.get("max")
                  else str(cl.get("min")))
        if cl.get("unit"):
            cl_txt += f" {cl['unit']}"
    vd_txt = f"{vd.get('value')} {vd.get('unit','')}".strip() if isinstance(vd, dict) else ""

    ap = profile.get("approved_products", [])
    us_recs = [r for r in ap if r.get("region", {}).get("value") != "CN"]
    cn_recs = [r for r in ap if r.get("region", {}).get("value") == "CN"]

    pat = profile.get("patents_exclusivity", [])
    patents = [r for r in pat if r.get("type", {}).get("value") == "patent"]
    uniq_pats = {str(r.get("patent_number", {}).get("value", "")) for r in patents} - {""}
    latest_exp = ""
    for r in patents:
        e = str(r.get("patent_expire_date", {}).get("value", ""))
        if e > latest_exp:
            latest_exp = e

    meta = profile.get("_meta", {})

    def yn(v):
        return "是" if v in (1, True, "1", "True") else ("否" if v in (0, False, "0", "False") else None)

    return {
        "药物名称": name,
        "CAS号": _first(profile, "identity", "cas_number"),
        "DrugBank ID": _first(profile, "identity", "drugbank_id"),
        "ChEMBL ID": _first(profile, "identity", "chembl_id"),
        "IUPAC名": _first(profile, "identity", "iupac_name"),
        "InChIKey": _first(profile, "identity", "inchikey"),
        "SMILES": _first(profile, "identity", "smiles"),
        "药物分类( superclass)": a.get("superclass"),
        "药物分类(class)": a.get("class"),
        "物理状态": a.get("db_state"),
        "首次批准年份 (ChEMBL)": a.get("first_approval"),
        "口服": yn(a.get("oral")),
        "注射": yn(a.get("parenteral")),
        "外用": yn(a.get("topical")),
        "黑框警告": yn(a.get("black_box")),
        "分子量 (g/mol)": _first(profile, "physicochemical", "molecular_weight"),
        "LogP (PubChem XLogP)": _first(profile, "physicochemical", "xlogp"),
        "LogP (ChEMBL aLogP)": _first(profile, "physicochemical", "alogp"),
        "TPSA (Å²)": _first(profile, "physicochemical", "tpsa"),
        "氢键供体HBD": _first(profile, "physicochemical", "hbd"),
        "氢键受体HBA": _first(profile, "physicochemical", "hba"),
        "可旋转键": _first(profile, "physicochemical", "rotatable_bonds"),
        "RO5违规数": _first(profile, "physicochemical", "ro5_violations"),
        "pKa (最强酸性)": _first(profile, "physicochemical", "pka_strongest_acidic"),
        "pKa (最强碱性)": _first(profile, "physicochemical", "pka_strongest_basic"),
        "logS (计算)": _first(profile, "physicochemical", "logs"),
        "BCS分类(预测)": _first(profile, "physicochemical", "bcs_class_predicted"),
        "半衰期-下限 (h)": hl_min,
        "半衰期-上限 (h)": hl_max,
        "血浆蛋白结合率 (%)": pb,
        "分布容积 Vd": vd_txt,
        "清除率 CL": cl_txt,
        "吸收(叙述,截断)": a.get("absorption"),
        "适应症(叙述,截断)": a.get("indication"),
        "熔点 (实验, °C)": _first(profile, "solid_state", "melting_point_experimental"),
        "水溶解度 (实验)": _first(profile, "solid_state", "water_solubility_experimental"),
        "水溶解度文献来源": (profile.get("solid_state", {}).get("water_solubility_experimental", [{}])[0]
                      .get("official_reference") if ss.get("water_solubility_experimental") else None),
        "等电点 (实验)": _first(profile, "solid_state", "isoelectric_point_experimental"),
        "美国上市产品数 (FDA)": len(us_recs),
        "中国参比制剂记录数 (NMPA/CDE)": len(cn_recs),
        "在册专利数 (Orange Book)": len(uniq_pats) if uniq_pats else 0,
        "最晚专利到期": latest_exp or None,
        "数据来源": ", ".join(meta.get("sources_used", [])),
        "数据快照": str(date.today()),
        "_us_recs": us_recs,
        "_cn_recs": cn_recs,
    }


DATA_DICTIONARY = [
    ("药物名称", "规范英文名(preferred name)", "PubChem/ChEMBL/DrugBank"),
    ("CAS号 / DrugBank ID / ChEMBL ID", "药物身份标识符", "DrugBank/ChEMBL (recorded)"),
    ("分子量 ~ RO5违规数", "计算理化描述符", "PubChem(预测/记录)、ChEMBL(预测)"),
    ("pKa / logS", "电离与溶解度(计算值,非实验)", "DrugBank (predicted)"),
    ("BCS分类(预测)", "MW/LogP/PSA 启发式预测,非实验BCS", "本项目规则"),
    ("半衰期-上/下限 (h)", "由DrugBank文字叙述结构化抽取,统一为小时", "DrugBank (experimental, extracted)"),
    ("血浆蛋白结合率 (%)", "由DrugBank文字叙述抽取的百分比", "DrugBank (experimental, extracted)"),
    ("分布容积 Vd / 清除率 CL", "按原文献单位保留(L 或 L/kg;± 展开为区间)", "DrugBank (experimental, extracted)"),
    ("熔点/水溶解度/等电点 (实验)", "DrugBank experimental-properties 实验值", "DrugBank + 原始文献引用"),
    ("美国上市产品数", "Drugs@FDA 产品记录数", "openFDA (official)"),
    ("中国参比制剂记录数", "NMPA 参比制剂目录(官方.doc + drugfuture 汇总,已去重)", "NMPA/CDE"),
    ("在册专利数/最晚到期", "FDA Orange Book,按专利号去重", "FDA Orange Book (official)"),
    ("数据来源/快照", "该行所有数据源与导出日期", "—"),
]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default="data/drug_intelligence.local.db")
    ap.add_argument("--out-dir", default="data/export")
    args = ap.parse_args()

    aux = _lookup_tables()
    conn = sqlite3.connect(args.db)
    rows, us_sheet, cn_sheet = [], [], []
    for name, pj in conn.execute("SELECT name, profile_json FROM drug_profiles ORDER BY name"):
        p = __import__("json").loads(pj)
        if not (p.get("approved_products") or p.get("patents_exclusivity")):
            continue
        r = row_for(p, aux)
        drug = r["药物名称"]
        for rec in r.pop("_us_recs", []):
            us_sheet.append({"药物": drug, **{k: v.get("value") for k, v in rec.items()
                                              if isinstance(v, dict)}})
        for rec in r.pop("_cn_recs", []):
            cn_sheet.append({"药物": drug, **{k: v.get("value") for k, v in rec.items()
                                              if isinstance(v, dict)}})
        rows.append(r)
    conn.close()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    import pandas as pd
    df = pd.DataFrame(rows)
    csv_path = out_dir / "drug_dataset.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    xlsx_path = out_dir / "drug_dataset.xlsx"
    try:
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as w:
            df.to_excel(w, sheet_name="数据集", index=False)
            pd.DataFrame(us_sheet).drop_duplicates().to_excel(w, sheet_name="美国上市产品", index=False)
            pd.DataFrame(cn_sheet).drop_duplicates().to_excel(w, sheet_name="中国参比制剂", index=False)
            pd.DataFrame(DATA_DICTIONARY, columns=["字段", "说明", "来源与证据类型"]).to_excel(
                w, sheet_name="字段说明", index=False)
    except Exception as e:  # openpyxl missing -> CSV still delivered
        xlsx_path = None
        print(f"(xlsx skipped: {e})")

    filled = {c: int(df[c].notna().sum()) for c in df.columns}
    print(f"✅ 数据集导出: {len(df)} 个药物 × {len(df.columns)} 列 "
          f"| 美国产品明细 {len(us_sheet)} 行 · 中国参比明细 {len(cn_sheet)} 行")
    print(f"   CSV : {csv_path}")
    if xlsx_path:
        print(f"   Excel: {xlsx_path} (数据集/美国产品/中国参比/字段说明 四个sheet)")
    print("   关键字段覆盖:")
    for c in ("半衰期-下限 (h)", "血浆蛋白结合率 (%)", "熔点 (实验, °C)", "水溶解度 (实验)",
              "药物分类(class)", "首次批准年份 (ChEMBL)"):
        print(f"     {c}: {filled.get(c, 0)}/{len(df)}")


if __name__ == "__main__":
    main()
