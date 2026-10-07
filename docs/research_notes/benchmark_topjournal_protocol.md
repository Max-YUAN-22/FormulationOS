# Research Protocol — FormulationBench
## A Benchmark and Controlled Agent Framework for Evaluating Evidence-Grounded Formulation Reasoning

**Version:** v1.0 (pre-registration draft) · **Date:** 2026-10-06 · **Status:** pilot running

> Pre-registration style: hypotheses, metrics, kill/pivot criteria and analysis plan are
> fixed BEFORE the full evaluation runs. Deviations must be documented.

---

## 1. Research questions (falsifiable)

- **RQ1 (fabrication):** What fraction of numeric drug-property claims made by LLMs
  without tool access are wrong vs. an authoritative multi-source database?
- **RQ2 (evidence-type blindness):** Do LLMs distinguish experimental from predicted
  values, or do they present computed descriptors as measured facts?
- **RQ3 (entity/form robustness):** When parent and salt forms carry different property
  values (MW, BCS-relevant params), do models resolve, confound, or acknowledge the
  ambiguity — and does tool-grounded access change this?
- **RQ4 (grounding effect size):** How much does provenance-complete database access
  improve factual accuracy, evidence-type consistency, and strategy agreement with
  real-world marketed products?
- **RQ5 (strategy external validity):** How concordant are model formulation
  recommendations with the dosage forms of actually marketed products?

## 2. Hypotheses (pre-registered)

| # | Hypothesis | Kill/pivot criterion (from 30-q pilot) |
|---|---|---|
| H1 | no-tool numeric accuracy < 80% | if >90% → type saturated, shift weight to adversarial types |
| H2 | >30% of numeric claims on predicted fields are unhedged or called experimental | if <10% → drop C-type, replace with conflict-injection |
| H3 | salt-mismatch rate > 25% without tools | if <10% and >50% acknowledged → entity type saturated |
| H4 | with_db grounding improves A-type accuracy ≥15 pp | if <5 pp → grounding effect too weak → reframe paper around H2/H3 |
| H5 | tool-invocation rate ≥80% when tool is offered | if <50% → agent harness issue, fix before science |

## 3. Task taxonomy (target n=300; pilot n=30)

| Type | Description | Ground truth | Auto-scorable |
|---|---|---|---|
| A numeric-retrieval | property lookup (MW/logP/pKa/t1/2/MP/solubility) | DB value ± tolerance | yes |
| B entity-form | parent vs salt vs hydrate conflicts | DB multi-source values | yes |
| C evidence-type | is a value experimental/predicted/recorded? | DB evidence field | yes |
| D strategy-vs-market | recommended strategy vs marketed dosage form/routes | openFDA products | yes (categorical) |
| E conflict-injection (adversarial) | feed a perturbed DB value; does the agent detect/flag? | injected truth | yes |
| F multi-step reasoning | drug → properties → strategy chain; graded rubric | rubric + expert | LLM-judge + expert 20% |

Sampling: stratified by BCS class, therapeutic area, era (approval year), and data
richness — to prevent "famous drug only" bias. Drug set drawn from the 2,139
full-depth DB profiles; question text template-varied (3 paraphrase templates each)
to reduce format overfitting.

## 4. Contamination control

1. **Private held-out split (30%)**: never published; results on it reported as primary.
2. **Canary strings** embedded in question set to detect leakage into training data.
3. **Perturbation probes**: synthetic drug names (real properties, novel identities) —
   a model answering these correctly from memory proves memorisation, not reasoning.
4. **DB version pinning**: all ground truth tied to a frozen DB snapshot hash.

## 5. Models, conditions, statistics

- **Models (≥6):** DeepSeek-V4-Pro, GPT-5.4(-mini), Claude (proxy), Qwen/Llama
  open-weights (local), MiniMax-M3, + one small model for cost axis.
- **Conditions (5):** (1) no-tool; (2) generic-RAG (texts, no provenance); (3) DrugDB
  tool (values only); (4) DrugDB tool + provenance labels; (5) DrugDB + conflict
  injection (adversarial).
- **Runs:** n ≥ 3 per (model × condition) at temperature 0.1; report mean ± CI
  (bootstrap 10k), paired comparisons McNemar / paired bootstrap; Holm-corrected.
- **Human baseline:** ≥2 formulation scientists (supervisor lab) answer a 50-question
  subset; report human-vs-model gap. Inter-annotator agreement (Cohen's κ) on C/F types.
- **LLM-judge validation:** judge scores on F-type validated against expert grades on
  the 20% overlap (report Pearson/Spearman; judge used only if ρ ≥ 0.7).

## 6. Primary endpoints (paper claims ride on these)

1. Fabrication rate (RQ1) per model/condition.
2. Grounding effect size: accuracy delta condition(1)→condition(3/4) with CI.
3. Evidence-type consistency (RQ2) — novel metric enabled by provenance-complete DB.
4. Entity-form resolution profile (RQ3) incl. adversarial delta.
5. Strategy concordance with marketed products (RQ5).

## 7. Quality gates (what makes it top-venue)

- [x] Pre-registered hypotheses + kill criteria (this document)
- [ ] Expert validation of all 300 questions (supervisor + 师兄; κ reported)
- [ ] ≥6 models × 5 conditions × ≥3 runs with CIs and significance tests
- [ ] Human expert baseline on subset
- [ ] Contamination probes + private split
- [ ] Failure taxonomy (≥50 hand-audited errors) + case studies
- [ ] Full reproducibility package (code, frozen DB snapshot, prompts, logs)
- [ ] Metric validation vs expert judgment

## 8. Target venues (pharmaceutics-first tiering)

Framing note: the paper is positioned as **"reliability evaluation methodology for
AI-driven formulation design"** (pharmaceutics methods paper), NOT as an ML benchmark
paper. The contribution story for reviewers: AI is entering pharmaceutical development;
its reliability is unquantified; we provide the quantification method, first data
(fabrication rates, entity-confusion profiles), failure taxonomy, and a mitigation
(+50pp with provenance-grounded access) — relevant to formulators and to ongoing
regulatory discussions on AI credibility (FDA/EMA).

1. **Drug Discovery Today** (AI methods/commentary; fast-moving AI+pharma scope)
2. **Acta Pharmaceutica Sinica B** (publishes AI-pharmaceutics methods)
3. **Molecular Pharmaceutics / Pharmaceutical Research** (methods + data)
4. Fallback: Briefings in Bioinformatics (lab precedent: FormulationAI) / J. Chem. Inf. Model.
   / Digital Discovery

## 9. Timeline (from pilot signal)

| Week | Work |
|---|---|
| W1 | Pilot analysis + kill/pivot decision; question generator v2 (stratified, 300); expert review pack |
| W2 | Expert validation round; multi-model runner; contamination probes |
| W3 | Full evaluation matrix (~6 models × 5 conditions × 3 runs); human baseline |
| W4 | Analysis, failure taxonomy, paper draft |
| W5-6 | Internal review (professor), revision, submission |

## 10. Division of labour (to agree with supervisor)

- Student: infrastructure, runs, analysis, paper draft
- Supervisor lab: expert question validation, human baseline, domain review
- DrugDB team (student): frozen DB snapshot + provenance schema documentation
