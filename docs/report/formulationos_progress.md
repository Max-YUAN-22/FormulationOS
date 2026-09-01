# FormulationOS 进展汇报
### Intelligent Design & Performance Prediction Platform for AI-Driven Drug Delivery Systems Based on a Multi-Agent Framework
### （FYP HSCI4000）— 平台进展 & 药物分子数据库构建

> 用法:每个 `##` 是一页。建议现场配合 `python demos/drug_report_card.py <药名>` 演示。

---

## 0 · 项目定位:两个语境

本 FYP 题目 = **基于多智能体框架的、AI 驱动药物递送系统的智能设计与性能预测平台**
（本项目内部代号 **FormulationOS**）。本学期成果落在**两个相互衔接的语境**里:

```
① FYP:FormulationOS(多智能体设计/预测平台)
        └─ 需要一个"事实底座"数据层 ─► 药物分子数据库

② 教授的「制剂数据库平台」大项目
        ├─ DrugDB(药物分子数据库)  ← 本人负责，本轮重点
        ├─ ExcipientDB(辅料库)      ← 他人
        └─ FormulationDB(处方库)    ← 他人
```

**一句话**:药物分子数据库既是 FYP 平台的**数据层**,又是教授制剂数据库平台里
**我负责的 DrugDB 组件**——本学期把它从 mock 做成了一个真实的 v1。

---

## 1 · FormulationOS 是什么

面向 AI 驱动药物递送系统的**智能设计 + 性能预测平台**:自然语言 → 智能体规划/
编排 → 调用专业 AI 模型 + 带溯源的药物情报数据库 → 输出制剂设计与评估。

近期主要进展:
1. **平台侧**:三个 AI 模型模块接入真实训练模型,已部署(Render/Streamlit);
   多智能体框架的**规划/编排地基**已搭。
2. **数据侧(本轮重点)**:药物分子数据库(DrugDB)重建为**多源、带溯源、全离线**
   的 **Drug Intelligence Database v1**——**4,230 药本地目录 + ~110 药全深度**
   (中美产品/专利),并**接进网页单药下钻**(运行时零外网)。

---

## 2 · FormulationOS 架构(诚实版)

```
                自然语言 (中/英)
                      │
        ┌─────────────▼──────────────────┐
        │  推理/规划层                     │
        │  • Scientific Planner + Workflow │  ← 规则/LLM/能力感知 DAG
        │  • Orchestrator(编排执行)       │
        │  • LLM 管理 (Claude/GPT/MiniMax) │  ← tool-use 循环
        └─────────────┬──────────────────┘
                      │ 调用
   ┌──────────────────┼─────────────────────┐
   │ AI 模型模块       │        数据/知识层    │
   │ • PreFormulationAI│  • Drug Intelligence DB(新,DrugDB)
   │ • FormulationAI2.0│  • Literature (PubMed)
   │ • Solid Dispersion│  • Knowledge base (SQLite)
   └──────────────────┴─────────────────────┘
                      │
              Streamlit Web UI (Render 部署)
```

> **多智能体现状**:当前为**单智能体 + 工作流规划/编排**(planner + orchestrator +
> 能力感知路由 + 科学推理/证据管理),这是**多智能体框架的地基**;完整的多智能体
> 科学团队(多角色协作)是**路线图**,尚未完成——不夸大。

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

## 7 · 规模与验证结果

**两层规模**:**4,230 药本地目录**(身份+理化+预测BCS,零联网)+ **~110 药全深度**
(中美上市产品 / 专利·独占 / 盐型;本地另含 DrugBank pKa·logS + 中国参比制剂)。

深度层验证(从 25 药起步,现扩到 ~110 常见药):

| 指标 | 结果 |
|---|---|
| ① Identity / ② 理化 / ③ 盐型 | 全深度药全部覆盖 |
| ④ 美国上市产品 | **5,210** 条(累计) |
| ⑤ 专利·独占期(Orange Book) | **1,313** 条(累计) |
| **中国参比制剂覆盖** | **110/111** 药(仅 Griseofulvin 无记录) |
| 溯源完整率 | **100%** |
| 实体/形态识别 | 如阿托伐他汀游离酸 vs 钙盐 |
| **运行时外网调用** | **0**(全栈离线,含网页下钻) |

**网页集成**:Knowledge Base「Drug Database」= 4,225 目录浏览 + **单药深度情报卡
下钻**(点药出 5 模块 + 溯源 + 中美产品 + 专利),**运行时零外网**。

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
- **深度层 ~110 药**(常见药),其余 ~4,120 药为轻量档案(身份+理化+预测BCS)
- DT / MM / PBPK / Toxicity 模块未接入
- drugfuture 每药封顶 20 条(翻页待补);官方/第三方去重已做

---

## 13 · 下一步

1. 深度层 110 → 数百 → 千级(增量,加名单跑一次构建即可)
2. 补齐中国侧:注册底册(NMPA)、CDE 目录集(需导出授权)、一致性评价、说明书
3. 接入二阶段源:CompTox(实验理化)、深度专利、EMA
4. 深度卡下钻已接进 Streamlit;进一步把 DrugDB 送给 AI 模型(情报 → 预测)
5. 视优先级恢复 Formulation DT / PBPK

---

## 14 · 小结

- **FYP 定位**:基于多智能体框架的 AI 药物递送设计/预测平台(FormulationOS);
  本学期在**平台**与**数据**两侧同步推进。
- **平台**:3 个 AI 模型接真模型 + 已部署;多智能体的规划/编排地基已搭(完整多
  智能体团队为路线图)。
- **数据(本人负责的 DrugDB)**:多源、带溯源、**全离线**的药物情报库 v1——
  **4,230 药本地目录 + ~110 药全深度**(中美产品/专利,本地含 DrugBank+中国参比),
  溯源 100%、运行时零外网、已接进网页下钻。同时是 FYP 平台的数据层 + 教授制剂
  数据库平台的 DrugDB 组件。
- **方法学**:溯源分层、实体校验、三态状态、合规分级——经得起追问。
- **一句话**:一个**靠谱的 v1 基线**,不是"几个 API 拼起来",可平滑扩展。
