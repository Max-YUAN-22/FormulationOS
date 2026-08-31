"""China catalog pipeline tests — synthetic data, no Excel, no network."""

from __future__ import annotations

from formulation_os.knowledge import cn_catalog_ingest as ing
from formulation_os.knowledge.drug_synonyms import DrugResolver
from formulation_os.knowledge.sources.nmpa_cde import NmpaCdeAdapter
from formulation_os.knowledge.sources.schema import (
    CATEGORY_APPROVED,
    CONSISTENCY_INFERRED,
    CONSISTENCY_NOT_APPLICABLE,
    CONSISTENCY_PASSED,
    CONSISTENCY_UNKNOWN,
    REF_ROLE_CN_REFERENCE_PREPARATION,
    SourceStatus,
)


# --------------------------------------------------------------------------- #
# Header alias resolution                                                      #
# --------------------------------------------------------------------------- #
def test_resolve_headers_handles_chinese_and_fullwidth_parens():
    cols = ["活性成分", "活性成分（英文）", "药品名称", "剂型", "给药途径",
            "规格", "参比制剂", "批准文号/注册证号", "上市许可持有人", "生产厂商",
            "收录类别"]
    m = ing.resolve_headers(cols)
    assert m["active_ingredient"] == "活性成分"
    assert m["active_ingredient_en"] == "活性成分（英文）"   # full-width parens matched
    assert m["approval_number"] == "批准文号/注册证号"
    assert m["route"] == "给药途径"
    assert m["catalog_category"] == "收录类别"


# --------------------------------------------------------------------------- #
# Strength parsing                                                             #
# --------------------------------------------------------------------------- #
def test_parse_strength():
    assert ing.parse_strength("0.5g") == (0.5, "g")
    assert ing.parse_strength("100mg") == (100.0, "mg")
    assert ing.parse_strength("5mg/ml") == (5.0, "mg/ml")
    assert ing.parse_strength("每片含20mg") == (20.0, "mg")
    assert ing.parse_strength("复方") == (None, None)   # unparseable kept as raw elsewhere
    assert ing.parse_strength(None) == (None, None)


# --------------------------------------------------------------------------- #
# Consistency status derivation — absence is never "failed"                    #
# --------------------------------------------------------------------------- #
def test_consistency_status_rules():
    assert ing.derive_consistency_status("通过", None) == CONSISTENCY_PASSED
    assert ing.derive_consistency_status("是", None) == CONSISTENCY_PASSED
    # innovator / imported originator -> not applicable
    assert ing.derive_consistency_status(None, "创新药") == CONSISTENCY_NOT_APPLICABLE
    assert ing.derive_consistency_status(None, "进口原研药品") == CONSISTENCY_NOT_APPLICABLE
    # category implies passed but no explicit column -> inferred
    assert ing.derive_consistency_status(None, "通过一致性评价的仿制药") == CONSISTENCY_INFERRED
    # nothing said -> unknown (NOT failed)
    assert ing.derive_consistency_status(None, None) == CONSISTENCY_UNKNOWN
    assert ing.derive_consistency_status(None, "其他") == CONSISTENCY_UNKNOWN


# --------------------------------------------------------------------------- #
# Salt handling for matching (never merged into parent)                        #
# --------------------------------------------------------------------------- #
def test_strip_salt_and_classify():
    resolver = DrugResolver()
    targets = {"metformin", "atorvastatin"}
    assert ing.classify_match("Metformin", targets, resolver) == "exact"
    assert ing.classify_match("Metformin Hydrochloride", targets, resolver) == "parent_via_salt"
    assert ing.classify_match("Atorvastatin Calcium", targets, resolver) == "parent_via_salt"
    assert ing.classify_match("Warfarin Sodium", targets, resolver) == "unmatched"
    assert ing.classify_match(None, targets, resolver) == "no_ingredient_en"


# --------------------------------------------------------------------------- #
# End-to-end: normalize rows -> DB -> adapter -> quality report                #
# --------------------------------------------------------------------------- #
_COLS = ["活性成分", "活性成分（英文）", "药品名称", "剂型", "给药途径", "规格",
         "参比制剂", "批准文号/注册证号", "上市许可持有人", "生产厂商",
         "上市销售状态", "收录类别"]

_ROWS = [
    {"活性成分": "二甲双胍", "活性成分（英文）": "Metformin", "药品名称": "二甲双胍片",
     "剂型": "片剂", "给药途径": "口服", "规格": "0.5g", "参比制剂": "格华止",
     "批准文号/注册证号": "国药准字H20023370", "上市许可持有人": "某制药",
     "生产厂商": "某制药厂", "上市销售状态": "正常", "收录类别": "通过一致性评价的仿制药"},
    {"活性成分": "盐酸二甲双胍", "活性成分（英文）": "Metformin Hydrochloride",
     "药品名称": "盐酸二甲双胍缓释片", "剂型": "缓释片", "给药途径": "口服",
     "规格": "500mg", "参比制剂": "", "批准文号/注册证号": "国药准字H20143371",
     "上市许可持有人": "另一制药", "生产厂商": "另一厂", "上市销售状态": "正常",
     "收录类别": "创新药"},
]


def _import_synthetic(db_path):
    mapping = ing.resolve_headers(_COLS)
    prov = {"authority": "NMPA/CDE", "source_type": "third_party_compilation",
            "source_provider": "test", "source_file": "syn.xlsx",
            "snapshot_date": "2026-06", "official_reference": "https://www.cde.org.cn/hymlj/",
            "ingested_at": "2026-08-17T00:00:00Z"}
    records = []
    for raw in _ROWS:
        rec = ing.normalize_row(raw, mapping)
        rec.update(prov)
        records.append(rec)
    return ing.write_records(db_path, records)


def test_import_and_adapter_roundtrip(tmp_path):
    db = str(tmp_path / "nmpa_cde.db")
    n = _import_synthetic(db)
    assert n == 2

    adapter = NmpaCdeAdapter(db_path=db)
    res = adapter.fetch(drug_name="Metformin")
    assert res.status == SourceStatus.OK
    recs = res.records[CATEGORY_APPROVED]
    # exact "Metformin" row matches; the hydrochloride row is NOT swallowed here
    assert any(r["drug_name"].value == "二甲双胍片" for r in recs)
    r0 = recs[0]
    assert r0["region"].value == "CN"
    assert r0["approval_number"].value == "国药准字H20023370"
    assert r0["route"].value == "口服"
    assert r0["consistency_evaluation_status"].value == CONSISTENCY_INFERRED
    # provenance keeps authority separate from channel
    assert r0["approval_number"].to_dict()["authority"] == "NMPA/CDE"
    assert r0["approval_number"].to_dict()["source_type"] == "third_party_compilation"


def test_adapter_unavailable_without_db(tmp_path):
    res = NmpaCdeAdapter(db_path=str(tmp_path / "missing.db")).fetch(drug_name="Metformin")
    assert res.status == SourceStatus.SOURCE_UNAVAILABLE


def test_quality_report_metrics(tmp_path):
    db = str(tmp_path / "nmpa_cde.db")
    _import_synthetic(db)
    rep = ing.quality_report(db, target_names=["Metformin", "Atorvastatin"], resolver=DrugResolver())
    assert rep["total_rows"] == 2
    assert rep["unique_approval_numbers"] == 2
    assert rep["strength_parse_rate_pct"] == 100.0
    rm = rep["resolver_match"]
    assert rm["exact"] == 1            # Metformin
    assert rm["parent_via_salt"] == 1  # Metformin Hydrochloride (NOT merged)
    assert rep["consistency_status_breakdown"][CONSISTENCY_INFERRED] == 1
    assert rep["consistency_status_breakdown"][CONSISTENCY_NOT_APPLICABLE] == 1


# --------------------------------------------------------------------------- #
# Reference-preparation (参比制剂) ingestion from official .doc text            #
# --------------------------------------------------------------------------- #
from formulation_os.knowledge import cn_reference_ingest as refing

_REF_DOC_TEXT = """附件
仿制药参比制剂目录（第十批）
序号
药品通用名称
英文名称/商品名
规格
剂型
持证商
备注1
备注2
10-1
阿司匹林双嘧达莫缓释胶囊
Aspirin and Dipyridamole Sustained-release Capsules/ Aggrenox
阿司匹林25mg与双嘧达莫200mg
胶囊剂（缓释胶囊）
Boehringer Ingelheim Pharma GmbH
欧盟上市（上市国:德国；产地：德国）
　
10-2
艾司奥美拉唑镁肠溶片
Esomeprazole Magnesium Enteric-coated Tablets/NEXIUM
20mg
片剂（肠溶片）
AstraZeneca AB
原研进口
　
"""


def test_parse_reference_doc_text():
    recs = refing.parse_reference_doc_text(_REF_DOC_TEXT, batch="10")
    assert len(recs) == 2
    r0 = recs[0]
    assert r0["seq"] == "10-1"
    assert r0["drug_name"] == "阿司匹林双嘧达莫缓释胶囊"
    assert r0["drug_name_en"] == "Aspirin and Dipyridamole Sustained-release Capsules"
    assert r0["trade_name"] == "Aggrenox"          # split on the slash
    assert r0["dosage_form"].startswith("胶囊剂")
    assert r0["holder"].startswith("Boehringer")
    assert r0["reference_status"] == "overseas_marketed"
    assert recs[1]["reference_status"] == "originator_imported"


def test_reference_write_and_adapter(tmp_path):
    db = str(tmp_path / "nmpa_cde.db")
    recs = refing.parse_reference_doc_text(_REF_DOC_TEXT, batch="10")
    prov = {"authority": "NMPA/CDE", "source_type": "official_file",
            "source_provider": "NMPA", "source_file": "b10.doc",
            "snapshot_date": "batch-10", "official_reference": "https://www.nmpa.gov.cn/",
            "ingested_at": "2026-08-17T00:00:00Z"}
    n = refing.write_reference_records(db, recs, prov)
    assert n == 2

    res = NmpaCdeAdapter(db_path=db).fetch(drug_name="Esomeprazole")
    assert res.status == SourceStatus.OK
    rec = res.records[CATEGORY_APPROVED][0]
    assert rec["region"].value == "CN"
    assert rec["is_reference_preparation"].value is True
    from formulation_os.knowledge.sources.schema import REF_ROLE_CN_REFERENCE_PREPARATION
    assert rec["reference_role"].value == REF_ROLE_CN_REFERENCE_PREPARATION
    assert rec["mah"].value == "AstraZeneca AB"     # 持证商 -> mah
    # official-file provenance keeps authority separate from channel
    assert rec["mah"].to_dict()["source_type"] == "official_file"


# --------------------------------------------------------------------------- #
# drugfuture consolidated browse-page parser + Chinese batch-number parsing    #
# --------------------------------------------------------------------------- #
_DF_PAGE = """
<table>
<tr><td>序号</td><td>药品通用名称</td><td>英文名称/商品名</td><td>规格</td><td>剂型</td><td>持证商</td><td>来源分类</td><td></td><td>备注</td><td>来源批次</td><td>公布日期</td></tr>
<tr><td>106-1</td><td>泽布替尼胶囊</td><td>Zanubrutinib Capsules/百悦泽/BRUKINSA</td><td>80mg</td><td></td><td>百济神州（苏州）生物科技有限公司</td><td>国内上市的原研药品</td><td></td><td>正式通稿</td><td>参比制剂目录第一百零六批</td><td>2026-06-15</td></tr>
<tr><td>10-2</td><td>艾司奥美拉唑镁肠溶片</td><td>Esomeprazole Magnesium Enteric-coated Tablets/NEXIUM</td><td>20mg</td><td>片剂（肠溶片）</td><td>AstraZeneca AB</td><td>原研进口</td><td></td><td></td><td>参比制剂目录第十批</td><td>2018-01-01</td></tr>
</table>
"""


def test_parse_drugfuture_page():
    recs = refing.parse_drugfuture_page(_DF_PAGE)
    assert len(recs) == 2
    r0 = recs[0]
    assert r0["seq"] == "106-1"
    assert r0["batch"] == "106"                       # 第一百零六批 -> 106
    assert r0["drug_name_en"] == "Zanubrutinib Capsules"
    assert r0["trade_name"] == "百悦泽/BRUKINSA"       # keep the rest after first slash
    assert r0["holder"].startswith("百济神州")
    r1 = recs[1]
    assert r1["batch"] == "10"                         # 第十批 -> 10
    assert r1["reference_status"] == "originator_imported"


def test_chinese_batch_number_parsing():
    from formulation_os.knowledge.cn_reference_ingest import _batch_num
    assert _batch_num("参比制剂目录第一百零六批") == "106"
    assert _batch_num("第十批") == "10"
    assert _batch_num("第五十二批") == "52"
    assert _batch_num("第25批") == "25"
