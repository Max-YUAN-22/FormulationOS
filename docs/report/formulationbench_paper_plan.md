# FormulationBench — 论文定位与骨架(v1)
**Target: Journal of Controlled Release(family home)· 备选 APSB / BIB**
**命名依据**:FormulationAI / BCS / DE / LAI / MM → FormulationBench = 生态缺的评估层

---

## Positioning(三个挂钩,全部来自导师自己的工作)

1. **QbCD 的 QA 层** — "Quality by computational design" (ADDR 2025) 主张质量须被设计并验证;本框架=对 AI 本身的 Quality Assurance。原句可引:"...harness AI to advance rational drug development" — 前提是 AI 可信,而可信需要可测。
2. **AI-strategy 论文的下一章** — "AI-directed formulation strategy design initiates rational drug development" (JCR 2025) 提出了 AI 策略设计;本文系统回答"这些策略建议有多可靠、何时失效、如何缓解"。
3. **家族工具的统一标尺** — FormulationAI (top-1 78%)、FormulationBCS (85%) 等各自内部验证;本文首次将家族工具与 LLM agent 放上同一受控评估,公开可复现。

**标题候选**
- FormulationBench: a controlled evaluation framework for evidence-grounded AI in pharmaceutical formulation development
- Toward trustworthy computer-driven formulation development: benchmarking evidence-grounded AI formulation agents

---

## Paper Outline(JCR 常规结构)

### 1. Introduction
- AI 工具在制剂开发中的扩散(FormulationXXX 家族、ChatInvent 等)
- 可靠性未被量化;我们实测裸 LLM 数值错误率 ~58%(pilot 预告)
- QbCD 逻辑:QA of the AI itself;贡献 3 条:框架 + 首批量化数据(失败模式分类学)+ 缓解方案(证据接地 +50pp)

### 2. The FormulationBench framework
- 2.1 Evidence oracle:provenance-complete DB(2,139 药 × 7 模块;每值 source+evidence+快照)
- 2.2 Task taxonomy(五层):L1 evidence correctness → L2 mechanism reasoning → L3 evidence arbitration → L4 strategy selection → L5 R&D utility(roadmap;本文实现 L1–L4)
- 2.3 Controlled conditions:no-tool / generic-RAG / DB-tool / DB+provenance labels / adversarial injection
- 2.4 Scoring:auto via provenance oracle;rubric+validated LLM-judge(推理题);expert baseline

### 3. Implementation
- 题目集(分层:BCS/电离/盐型/剂量/年代;模板×3)、污染控制(私有集/合成探针/canary)、模型矩阵

### 4. Results
- 4.1 Grounding effect(42%→92% 完整版;置信区间+显著性)
- 4.2 失败模式分类学(编造/盐型混淆/口径混用/条件缺失;按 regime 分层报告——BCS II 弱酸 vs 中性难溶等)
- 4.3 家族工具 vs LLM agents 同场对比(FormulationAI 策略推荐、FormulationBCS、Solid Dispersion LGBM 上尺)
- 4.4 Sequential evidence-update case(证据逐轮揭示,判断是否更新)
- 4.5 Calibration/abstention(证据缺失时 abstain vs confabulate)

### 5. Case studies
- Sporanox(一药两解的策略 ground truth)· Metformin(证据仲裁真实案例)· Atorvastatin(实体/晶型)

### 6. Discussion
- 对 QbCD 的意义;对监管 AI 可信性议程(FDA/EMA)的呼应;局限(静态题集、小分子口服为主、判分哲学)

### 7. Availability
- 公开子集 + 代码 + 私有集协议

---

## 与现有资产的对账(哪些章节已有素材)

| 章节 | 素材状态 |
|---|---|
| 2.1 oracle | ✅ 已建成(2,139 药,DB 快照可冻结)|
| 2.2 taxonomy | ✅ 五层地图+pilot 4 类题型 |
| 4.1 grounding | 🟡 30 题试点已有;需扩至 300 题×多模型 |
| 4.2 失败分类学 | 🟡 16+8 题审计清单已生成;需人工分类+扩量 |
| 4.3 家族工具上尺 | ❌ 待做(FormulationAI/BCS 有 API/模型,可跑)|
| 4.4 sequential | ❌ 待设计(架构契合:证据逐轮揭示)|
| 4.5 calibration | 🟡 hedging 已测;abstention 题型待加 |
| 案例章节 | ✅ 三个案例全部有真实数据 |

## 6 周执行节奏(对齐 W1–W4 任务)
W1 题目v2+审计 → W2 专家评审(导师 2-3h)+多模型运行器 → W3 全量矩阵+家族工具上尺 → W4 分析+初稿 → W5-6 导师审+投 JCR
