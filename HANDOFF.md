# HANDOFF — 给第二台机器上的 agent(以及任何接手的人)

> 新会话从这里开始:先读 `AGENTS.md`(项目契约),再读本文(当前状态 + 红线)。
> 最后更新:2026-11-26,对应 origin/main `dd78fee` 之后的本地进度(见 §2)。

## 1. 项目现状(一句话 + 核心数字)

**FormulationOS = 制剂数据库 + 置信度分层 + 置信度分层驱动的制剂 AI 基准。**
数据库层已从"拼装完成"进入"审计完成"状态:

* 主脊柱 19,857 药(DrugBank 5.1.19 全量,SHA256 钉死)
* 三源置信度:**A 级阶梯 564 → 542(PubChem 结构验证)→ 534(双重结构验证)**
* MW 三源一致金标 2,042(对容差 ±0.1% 稳健);LogP CONFLICT 是方法噪声(MAE 0.67–0.82,均值≈0)
* 体内结构化 2,422 药;固态交叉验证 mp 586 agree / 154 disagree,ws 506 / 160 near / 175 disagree
* 结构验证揪出 **312(PubChem)+ 21(ChEMBL)个名字匹配假阳性**——已剔除并标注
* W1 题库 v2:100 题、五题型、种子 20261120 冻结、SHA256 入 manifest
* 一页纸可信度报告:`reports/VERIFICATION.md`(给教授/审稿人看的版本)

## 2. 本机恢复(数据层不在 git 里!)

git 只有代码 + 公共域快照。**授权数据层在 `FormulationOS_sync_20261125.zip`**(主 Mac 桌面,AirDrop/scp 过来):

1. `git clone https://github.com/Max-YUAN-22/FormulationOS.git && cd FormulationOS`
2. `unzip -o ../FormulationOS_sync_20261125.zip -d .`
3. 完整性校验(**必须逐字一致**,否则停下找原因,不要硬跑):
   `python3 -c "import hashlib;print(hashlib.sha256(open('data/master/master.db','rb').read()).hexdigest())"`
   → 前缀必须是 `e8a861f243810325`
4. `pip install -r requirements.txt`
5. 复现验证:`python scripts/build_confidence3.py` 应逐字输出 v3 数字(A=564/542/534)
6. API keys 不在任何包里:`.streamlit/secrets.toml`(参考 `.example`)或环境变量

## 3. 红线(先读再动手)

1. **公开仓库永远不放** master.db、DrugBank 衍生内容、含 verbatim 的 JSONL/CSV。gitignore 已配好(`*.db`、指定文件)——**不要为了"传个方便"去 -f add**。两台自己机器之间拷贝没问题,公开仓库不行(DrugBank 学术许可)。
2. **历史泄密**:commit `9afa74c` 里有一个已暴露的 API key(`sk-rpua...`),**必须已在发行平台吊销**。若没做,提醒用户立刻做。历史清洗(filter-repo + force push)是否执行待用户拍板。
3. **数字纪律**:论文/汇报里任何数字必须能一条 SQL 查出来;重建后跑 `scripts/build_master_fingerprint.py` 对比指纹;改库不改指纹 = 事故。
4. **匹配纪律**:凡引用置信度数字,默认用**双重验证子集**(`x_confidence.pubchem_match_level='exact_match' AND chembl_match_level='exact_match'`);名字级匹配只是 fallback,不算金标。
5. **冻结不变量**(改动=事故,要改就开新版本并记录):种子 20261120、容差(MW 2%/LogP 0.5/TPSA 15%)、全部快照 SHA256、协议版本号。
6. **已修过的坑别再踩**:unicode 双胞胎(`µ`U+00B5 vs `μ`U+03BC;`°C`.upper() ≠ `C`)、PUG View 栏目名(`Solubility` 不是 `Water Solubility`;数值在 `StringWithMarkup→String` 或 `Number+Unit`)、PubChem 限速 ≤5 req/s(全局限速器在 fetcher 里,别拆)。

## 4. 当前待办(按优先级)

1. **gold audit 人工核对**:`data/processed/gold_audit_sample.csv` 326 行,人填 `human_verdict` 列 → precision + Wilson CI。机器做不了,这是论文入场券。
2. **W2 双裁判多模型矩阵**:runner 未接(等用户定被测模型/裁判/预算)。骨架在 `benchmark/pilot_grounding.py`(42%→92% 那次)与 `unified_llm_manager`。评分口径已在题库 `scoring_spec` 里写死,别重发明。
3. DrugBank 5.1.22 恢复下载后:重跑全管道当复现实验(见 10-24 决议)。
4. MP 分歧审计的 21 个 DrugBank 修正候选(`data/processed/mp_disagreement_audit.csv`)待文献复核——论文亮点素材。

## 5. 关键文件索引

| 要查什么 | 去哪 |
|---|---|
| 可信度阶梯 + 审计结论 | `reports/VERIFICATION.md` |
| 全库表结构/行数/哈希 | `data/processed/master_fingerprint.json` |
| 每药的置信度与匹配级 | `x_confidence`(pubchem/chembl_match_level 两列) |
| 固态双源比对 | `x_exp_crosscheck`(每行双 verbatim) |
| LogP 方法噪声量化 | `x_logp_analysis` |
| 覆盖矩阵(论文 Table 1) | `x_coverage` |
| 题库(本地,不入 git) | `benchmark/results/w1_v2_question_bank.jsonl` |

## 6. 与主机的日常同步约定

代码走 `git pull/push`;数据层低频变更,重打 zip 传(包内 RESTORE.md 有制作约定)。
两台机器**同时改代码**时:先 pull 再动手,commit 粒度小,信息写清动机。
