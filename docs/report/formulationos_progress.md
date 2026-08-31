# FormulationOS 进展汇报
### FormulationOS & 药物分子数据库构建 — Progress Report

> 用法:每个 `##` 是一页。建议现场配合 `python demos/drug_report_card.py <药名>` 演示。

---

## 1 · 一句话定位

**FormulationOS** = 一个面向药物制剂研发的 **AI 操作系统**:自然语言接口 →
LLM 编排 → 调用多个专业 AI 模型 + 一个**带溯源的多源药物情报数据库**,输出制剂
设计与评估建议。

近期主要进展有两块:
1. **平台侧**:三个 AI 模块接入真实训练模型,部署上线(Render / Streamlit)。
2. **数据侧**(本轮重点):把原来的 mock「药物数据库」重建为一个**多源、带溯源、
   离线**的 **Drug Intelligence Database v1**。

---

## 2 · FormulationOS 架构

```
                自然语言 (中/英)
                      │
        ┌─────────────▼─────────────┐
        │   LLM 编排层 (Claude/GPT/MiniMax) │  ← tool-use 循环
        └─────────────┬─────────────┘
                      │ 调用
   ┌──────────────────┼─────────────────────┐
   │ AI 模型模块       │        数据/知识层    │
   │ • PreFormulationAI│  • Drug Intelligence DB(新)
   │ • FormulationAI2.0│  • Literature (PubMed)
   │ • Solid Dispersion│  • Knowledge base (SQLite)
   └──────────────────┴─────────────────────┘
                      │
              Streamlit Web UI (Render 部署)
```

---

## 3 · 模块集成状态(诚实版)

| 模块 | 状态 | 真实模型 |
|---|---|---|
| **PreFormulationAI** | ✅ 已接入 | 38 个文件(PyTorch pKa/熔点/logP/溶解度 + sklearn 成药性) |
| **FormulationAI 2.0** | ✅ 已接入 | 12 个决策树模型(BCS/策略推荐) |
| **Solid Dispersion** | ✅ 已接入 | LightGBM 固体分散预测 |
| **Drug Intelligence DB** | ✅ 新建 v1 | 多源聚合(见后) |
| **Literature** | ✅ 功能性 | PubMed 检索(无需模型) |
| Formulation DT(数字孪生) | ⏸ 暂不接入 | 框架预留 |
| PBPK-AI / Toxicity / MM | ⏸ 桩 | 未接入 |

**要点**:不夸大——3 个 AI 模型接真模型,数据层是本轮新建;DT/MM/PBPK 明确标为
未接入。

---

## 4 · 为什么要重建药物数据库

原来的 `drug_database` 是 **mock**(写死布洛芬)。对制剂研发,数据库必须回答的不是
"这分子是什么",而是:

> 这个 API 是哪种化学形式?有哪些与制剂相关的理化性质?在什么条件下测的?
> 出现在哪些上市处方里?专利/独占期到什么时候?**每条数据来源可靠吗?**

于是重建为 **Drug Intelligence Database** —— 面向制剂的、带溯源的多源情报库。

---

## 5 · 数据库架构:5 模块 + 每模块指定主数据源

```
Drug → Chemical Form → US/CN Marketed Product → Patent · Exclusivity · Reference
```

| 模块 | 主数据源 | 补充/交叉验证 |
|---|---|---|
| ① Identity | PubChem | ChEMBL, DrugBank* |
| ② 理化性质 | PubChem | ChEMBL, DrugBank*(pKa/logS), CompTox† |
| ③ 盐型/晶型 | ChEMBL | CSD†, DrugBank* |
| ④ 上市产品 | FDA openFDA + DailyMed | **NMPA/CDE 参比制剂**, EMA† |
| ⑤ 专利·独占期 | **FDA Orange Book** | USPTO/EPO/WIPO/CNIPA† |

\* 本地、许可受限 · † 二阶段框架桩

**架构原则**:离线构建 → 本地 SQLite → **运行时零外网**(服务快、稳、可离线)。

---

## 6 · 核心设计:溯源与科学严谨

- **每个值带来源 + 证据类型**:experimental / predicted / recorded
- **溯源分层**:authority(NMPA/CDE)与 channel(官方文件 / 第三方汇总)分开
  —— 第三方数据**绝不冒充**官方
- **实体/盐型校验**:MW 冲突先判是否同一化学实体;游离酸 vs 盐 → 标 form
  mismatch 而非数据错误
- **三态状态**:record_found / no_record / **source_unavailable**
  ——"没查到"绝不等于"未通过/阴性"
- **盐型纪律**:盐酸盐/钙盐保留为独立产品,不为凑匹配率并进母体

---

## 7 · 25 药验证结果

| 指标 | 结果 |
|---|---|
| ① Identity | **25/25** |
| ② 理化(≥5字段) | **25/25** |
| ③ 盐型/晶型 | **25/25** |
| ④ 美国上市产品 | **25/25** |
| ⑤ 专利 record_found | **11/25**(+14 no_record,0 unavailable) |
| **中国参比制剂覆盖** | **24/25** |
| 溯源完整率 | **100%** |
| 实体/形态识别 | 2 例(如阿托伐他汀游离酸 vs 钙盐) |
| 运行时外网调用 | **0** |

累计:**1,165** 美国上市产品 · **583** 美国专利/独占 · **288** 中国参比制剂。

---

## 8 · 数据源可达性研究(真实调研,是"发现")

| 数据源 | 可达性 | 结论 |
|---|---|---|
| PubChem / ChEMBL / openFDA | 免费 API | ✅ 已接入 |
| FDA Orange Book | 静态公开文件 | ✅ 已接入(专利/独占) |
| DrugBank 全库 | 本地许可 XML | ✅ 本地接入 |
| **CDE/NMPA 在线库** | **瑞数反爬(HTTP 202)** | ❌ 编程不可达 |
| **NMPA 参比制剂 .doc** | 静态文件(非瑞数) | ✅ 官方接入 |
| drugfuture(参比汇总) | POST 检索 | ✅ 第三方接入 |

**中国参比数据**用两法获取、溯源分开:官方 .doc(333 条)+ drugfuture(237 条);
**随机抽查重叠记录,官方 vs 第三方 100% 吻合**。

---

## 9 · 现场演示

```bash
python demos/drug_report_card.py Metformin      # 中美双全 + 专利≠独占
python demos/drug_report_card.py Atorvastatin   # 盐型/实体识别的故事
```
一屏展示:5 模块 + 每条数据来源标注 + 美国/中国拆分 + 冲突/实体提示 + 三态状态。

---

## 10 · 数据库如何服务 FormulationOS

```
用户输入药名
   → Drug Intelligence DB(身份/理化/盐型/上市/专利,带溯源)
   → PreFormulationAI(溶解度/渗透性/成药性预测)
   → FormulationAI 2.0 / Solid Dispersion(制剂策略)
   → 制剂设计建议
```
数据库不再是孤立表,而是 FormulationOS 的**输入数据层**——AI 模型的"事实底座"。

---

## 11 · 合规

- **公开版**(`drug_intelligence.db`)= 仅可再分发源(PubChem/ChEMBL/openFDA/
  Orange Book)——可提交、可部署
- **本地版**(`*.local.db`)+ DrugBank + 中国数据 = 许可受限,**仅本地、不部署**
  (CDE/NMPA "All Rights Reserved")

---

## 12 · 边界(主动披露)

- 中国侧目前**只到参比制剂**;CDE 目录集的收录类别/一致性评价在瑞数墙后,需授权导出
- **25 药是验证集**,尚未扩到千级
- DT / MM / PBPK / Toxicity 模块未接入
- drugfuture 每药封顶 20 条(翻页待补);官方/第三方去重已做

---

## 13 · 下一步

1. 扩展验证集 25 → 数百 → 千级
2. 补齐中国侧:注册底册(NMPA)、CDE 目录集(需导出授权)、一致性评价、说明书
3. 接入二阶段源:CompTox(实验理化)、深度专利、EMA
4. 把 Drug Intelligence DB 接进 Streamlit 前端(药名搜索 → 情报卡 → 送 AI 模型)
5. 视优先级恢复 Formulation DT / PBPK

---

## 14 · 小结

- **平台**:3 个 AI 模块接真模型,已部署
- **数据**:多源、带溯源、离线的药物情报库 v1,25 药验证,中美双侧,溯源 100%
- **方法学**:溯源分层、实体校验、三态状态、合规分级——经得起追问
- **定位**:这是一个**靠谱的 v1 基线**,不是"几个 API 拼起来",可平滑扩展
