# Phase 2 Integration Strategy — Decision Document

**Status:** Draft for stakeholder review
**Date:** 2026-07-07 / 2026-07-08
**Author:** Max + Mavis

## Purpose

Document the strategic decision points for moving FormulationOS from
mock-only v0.1 toward real scientific model integration (Phase 2).
This is the **decision document** — not a survey of every platform.
The goal is to identify the binding bottlenecks, present the realistic
integration strategies, and surface the choices that need explicit
stakeholder input.

Throughout this document, claims are tagged:

- **[CONFIRMED]** — verified via direct probe (GitHub API, web curl)
  or unambiguous committed doc (sources cited inline).
- **[NEEDS CONFIRMATION]** — based on committed docs or plausible
  inference, but not directly verified; requires stakeholder
  confirmation.

---

## 1. Current FormulationOS status

### 1.1 Integration readiness — the relevant question

The question for Phase 2 is not "does the system have tests?" but
"**is the OS layer ready to carry a real scientific model?**" The
answer, by layer:

| Layer | Component | Ready for real-model integration? |
|---|---|---|
| 1 (Models) | 5 mock tools | ❌ All `mock: true`; placeholder outputs only |
| 2 (Registry + Runtime) | ToolRegistry + PythonExecutor + Orchestrator | ✅ Plumbing works; only `python` executor type is implemented (HTTP / CLI / MCP / gRPC / Docker reserved in STS v0.2) |
| 3 (Planner) | RuleBasedPlanner + LLMPlanner (MiniMax M3 / OpenAI) | ✅ Routes queries to registered tools; embedding-based retrieval is keyword-only today (Task 3 v2 planned) |
| 4 (Workspace) | empty directory | ⏸ Planned (Phase 2+); not needed for one-shot integration |
| 5 (UI) | Streamlit app | ✅ End-to-end demo with mocks; will surface real outputs once any tool returns them |

**Bottom line.** The OS layer is ready to wrap a real model. The
binding gap is **Layer 1**: no real scientific model has been
integrated yet. The Phase 2 question is therefore not "build more
plumbing" but "which model to wrap, under what access conditions".

### 1.2 Code support for paper claims

| Paper concept | Code support | [CONFIRMED] |
|---|---|---|
| Scientific Workflow as first-class object | `Orchestrator` + `Report` (container of `ToolResult`s) | `orchestrator/orchestrator.py` |
| Tool abstraction | `Tool` ABC + `ToolSpec` (Pydantic, STS v0.2, `extra="forbid"`) | `core/tool.py` |
| Runtime / Executor | `Executor` ABC + `PythonExecutor` | `runtime/executor.py` |
| Planner pluggability | `Planner` ABC + 2 implementations | `planner/base.py` |
| STS v0.2 schema | 4 extension models (ScientificSemantics, PlanningHints, ScientificDependencies, ProvenanceSpec) | `core/tool.py`, `docs/sts_specification.md` |

### 1.3 What is NOT yet shipped

- **Real scientific models** — all 5 built-in tools are mocks.
  [CONFIRMED — each `tools/builtins/*/backend.py`]
- **HTTP / CLI / MCP / gRPC / Docker executors** — only `python`
  executor is implemented. [CONFIRMED — `runtime/executor.py`]
- **Full provenance emission** — paper §6.3 shows the full
  `execution_id / tool_version / input_hash / output_hash / ...`
  schema, but v0.1 Orchestrator captures only `duration_ms` and
  `warnings`. [CONFIRMED — `orchestrator/orchestrator.py:_run_one`]

### 1.4 Reference maturity bar

Prof. Ouyang's published platforms (documented in
`docs/maturity/ouyang_platforms.md`) define the maturity target:
real ML models behind every prediction, multi-paper track record,
account system, application-domain analysis, citation metadata,
experimental validation. FormulationOS's path is to **wrap** real
platforms rather than build them, so the maturity target for
FormulationOS is set by which platform it integrates first.

---

## 2. Why scientific model integration is challenging

The challenges below are framed academically: each is a class of
problem that motivates the STS / Scientific Workflow contribution.

### 2.1 Challenge 1 — Heterogeneous execution interfaces

Scientific tools in pharmaceutics ship under **at least five
distinct execution modalities**:

| Modality | Example | Executor type needed |
|---|---|---|
| Python package (in-process) | a scikit-learn / PyTorch module | `python` (✅ v0.1) |
| REST API | a hosted prediction service | `http` (🚧 Task 5 / Phase 2) |
| CLI executable | a GROMACS / Amber binary | `cli` (🚧 Task 5) |
| MCP server | a Model-Context-Protocol tool | `mcp` (📋 future) |
| Containerized simulation | a Docker image with full MD stack | `docker` (📋 future) |

A real integration must accommodate **at least two** of these in a
single workflow (e.g., a Python-package pre-formulation tool feeding
a Docker-based MD simulation). STS v0.2 declares all five executor
types in `executor.type`, but only `python` is implemented in v0.1.

### 2.2 Challenge 2 — Scientific artifact heterogeneity

Inputs and outputs are not generic tensors. Each platform has its
own scientific schema:

- **FormulationAI**: `drug_smiles + experimental conditions`
  → `excipient set + composition + process parameters` (structured
  JSON; ≥16 properties across 6 formulation systems).
- **FormulationMM**: `molecular structure (SMILES / .mol / .pdb)`
  → `MD trajectory + topology + binding free energies` (multi-file,
  GB-scale; not JSON).
- **AI-PBPK**: `dose + compound + route + simulation_time`
  → `PK curve + tissue distribution across 15 organs + AUC/Cmax`
  (numeric time series + structured metadata).
- **Literature**: `query string` → `paper list + abstracts + DOI`
  (text + structured citation metadata).

A Scientific OS must carry these heterogeneous artifacts through a
single Workflow — typed via the `input_schema` and `output_schema`
of STS, and persisted via the Workspace (Layer 4, Phase 2+). This
artifact heterogeneity is exactly what STS's Scientific Semantics +
Scientific Dependencies extensions are designed to express.

### 2.3 Challenge 3 — Deterministic evidence, not deterministic models

FormulationOS does **not** promise that two runs of the same
workflow produce identical model outputs. It does promise that two
runs produce **identical evidence chains** (tool version, input hash,
output hash, executor type, timestamps, compute environment). This
is the load-bearing principle of paper §1, §6.3, §8: reviewers
expect reproducibility of the **trace**, not of the prediction.

Operationally, this means a Phase 2 integration must:

- Record `tool_version`, `tool_spec_hash`, `input_hash`, `output_hash`
  on every execution (paper §6.3 schema; v0.1 partial — see §1.3).
- Surface a `warnings` field whenever a tool returns placeholder /
  unavailable output (so downstream consumers cannot mistake
  heuristic output for a real prediction).
- Be explicit about **what is and is not** reproducible across runs.

### 2.4 Risk of fabricating predictions

A naive integration may substitute a heuristic fallback (e.g.,
Lipinski-rule Ro5) when the real model is unavailable, and label
the heuristic output as the real prediction. This is the
"mock-as-production" anti-pattern (AGENTS.md §12); it would draw
immediate reviewer attack and break the deterministic-evidence
contract.

The **safe pattern** is: integration returns explicit
`model_unavailable` status when upstream is missing, with no
fabricated predictions. Phase 2.1 ships this safe pattern; Phase 2.2
(real inference) is blocked on upstream access conditions.

### 2.5 License boundary

[NEEDS CONFIRMATION] The published Ouyang platforms are documented
as CC BY-NC-SA 4.0 in `docs/maturity/ouyang_platforms.md`. Whether
this license covers integration into a third-party tool, or whether
a separate collaboration agreement is required for academic /
non-commercial redistribution, requires stakeholder confirmation.
The **NC** (Non-Commercial) clause is the binding constraint for
FormulationOS distribution.

---

## 3. Five-platform integration matrix

See `docs/research_notes/scientific_model_integration_matrix.md` for
the full matrix with per-cell verification tags. Summary:

| Platform | Code | API | Weights | Verification |
|---|---|---|---|---|
| FormulationAI | [NEEDS CONFIRMATION] | [CONFIRMED no public REST] | [NEEDS CONFIRMATION] | Low |
| PreformulationAI | [NEEDS CONFIRMATION] | [NEEDS CONFIRMATION] | [NEEDS CONFIRMATION] | Very low |
| FormulationMM | [NEEDS CONFIRMATION] | [NEEDS CONFIRMATION] | [NEEDS CONFIRMATION] | Very low |
| **FormulationDT** | [CONFIRMED] MIT | [CONFIRMED absent] | [CONFIRMED absent in repo] | **High** |
| AI-PBPK | [NEEDS CONFIRMATION] partial | [NEEDS CONFIRMATION] | [NEEDS CONFIRMATION] | Low |

**Highest-confidence target** (public evidence base is strongest):
**FormulationDT**, where the GitHub repository state is fully
documented and probe-verified.

---

## 4. FormulationDT — candidate first integration target

See `docs/research_notes/formulation_dt_adapter.md` for full
investigation. Summary of probe 2026-07-07:

### 4.1 What is confirmed about the candidate

| Asset | Status | Evidence |
|---|---|---|
| Public source code | [CONFIRMED] present (MIT, ~1.6 MB) | GitHub API |
| Per-decision training scripts (DT, KNN, LR, LightGBM, NN, RF, SVM, nBayes) | [CONFIRMED] present | GitHub repo `Code/` directory |
| Packaged `predict_decisions()` API | [CONFIRMED absent] | No `setup.py` / `pyproject.toml` |
| Pretrained weights in public repo | [CONFIRMED absent] | GitHub code search returned no large model files in tracked history |
| Deployed web service at `formulationdt.computpharm.org` | [CONFIRMED unreliable] | URL returns 200 but body is a 2023 HTTrack mirror of `formulationai.computpharm.org`; `/api`, `/predict`, `/swagger`, `/docs` paths 404 |

### 4.2 What requires confirmation

1. **Pretrained weights.** The Wang et al. 2024/2025 paper reports
   ROC_AUC 0.78–0.98 (per `docs/ouyang_platforms_summary.md`),
   implying trained models exist somewhere — but where? In the
   upstream team's private storage? On a non-public deployment?
   [NEEDS CONFIRMATION]
2. **Packaged inference API.** Would the upstream team accept a
   collaboration to package `predict_decisions(smiles, formulation_type)`
   as a pip-installable module? [NEEDS CONFIRMATION]
3. **Actual deployment URL.** Where is the FormulationDT web service
   actually deployed (if anywhere)? The canonical
   `formulationdt.computpharm.org` is a mirror; the real deployment
   may be auth-gated at a different domain. [NEEDS CONFIRMATION]
4. **Code scope for retraining.** Are `Code/`, `Data/`,
   `TrainingRecords_MLP/` in `NamanWang/FormulationDT` sufficient to
   retrain from scratch, or is the curated training dataset only
   partial? [NEEDS CONFIRMATION]
5. **Citation correctness.** Is the canonical paper Wang et al.
   2024/2025 (*J Control Release* 378:619–636, DOI:
   10.1016/j.jconrel.2024.12.043)? DOI not directly verified 2026-07-07;
   documented in `docs/ouyang_platforms_summary.md`. [NEEDS CONFIRMATION]

### 4.3 Conclusion

**FormulationDT is currently the most accessible candidate for the
first integration**, because its public repository state is fully
documented and probe-verified, with an MIT license. However,
**production integration requires model packaging**: either (a)
pretrained weights + a packaged `predict_decisions()` API from the
upstream team, or (b) a self-hosted retraining pipeline built on
the public `Code/` + `Data/`.

Without either, only the **adapter pathway** (Phase 2.1) is
shippable — demonstrating the STS integration contract and
returning `model_unavailable` when upstream is absent. The adapter
pathway is itself a paper-worthy contribution (proves STS can
carry a real-world tool contract), but does **not** make any
prediction claim.

---

## 5. Strategic decision points (5 core questions)

These are the decisions that need explicit input. Other open
questions are downstream of these.

### Q1 — Integration philosophy

Should FormulationOS aim to **wrap existing models** as the primary
integration strategy, or **rebuild models into a unified backend**?

- **Option A — Wrapper (recommended).** Each platform remains
  authoritative at its own lab; FormulationOS adds a thin STS /
  Executor layer on top. Lower cost; preserves each platform's
  independence; matches STS's role as an extension schema over
  existing tools (paper §5).
- **Option B — Unified backend.** Port or reimplement each platform's
  model inside FormulationOS. Higher cost; tighter coupling;
  diverges from "operating layer over scientific models" framing.

### Q2 — Access to existing platforms

For each of the 5 Ouyang platforms, which of the following are
available **for the project**?

| Platform | Code | Weights | Public API | Auth-gated API | Internal call |
|---|---|---|---|---|---|
| FormulationAI | ? | ? | ? | ? | ? |
| PreformulationAI | ? | ? | ? | ? | ? |
| FormulationMM | ? | ? | ? | ? | ? |
| FormulationDT | ✅ MIT [CONFIRMED] | ? | ❌ [CONFIRMED] | ? | ? |
| AI-PBPK | ? | ? | ❌ [per docs] | ? | ? |

**This table is the binding input.** Filling it determines which
integration strategies are realistic.

### Q3 — First milestone scope

Is the first Phase 2 milestone:

- **A.** "FormulationOS + **adapter pathway only** for FormulationDT"
  (Phase 2.1; ships immediately; no model claim) — or
- **B.** "FormulationOS + **one fully-integrated real model**"
  (Phase 2.1 + 2.2; requires upstream cooperation on weights + API)?

The example pipeline below shows what a one-real-model milestone
would look like end-to-end:

```
User query:
  "I want oral formulation for drug X"
        ↓
Planner (routes to relevant tools)
        ↓
PreformulationAI     (solubility / BCS / pKa)
        ↓
FormulationAI        (excipient design)
        ↓
PBPK                 (in-vivo prediction)
        ↓
Report (with provenance)
```

### Q4 — Research positioning

Is the paper's headline framing:

- **A.** "Scientific Agent System" (LLM-centric; emphasizes planner
  and natural-language interface), or
- **B.** "Scientific Workflow Operating System" (OS-centric;
  emphasizes Scientific Workflow Abstraction, STS, deterministic
  evidence, heterogeneous executors)?

Current paper draft (`paper/sections/01_introduction.md`,
`03_scientific_workflow_abstraction.md`, `04_formulationos_architecture.md`)
leans toward B. Confirming this is important before the paper
abstract is finalised.

### Q5 — Validation strategy

How should the system's effectiveness be demonstrated?

- **A. Case study comparison.** Drug formulation optimization
  *without* orchestration (manual stage-by-stage) *vs.* *with*
  FormulationOS. Quantitative metric: time-to-decision, error
  rate across manual transfer, evidence-chain completeness.
- **B. Adapter pathway validation.** Demonstrate that the
  FormulationDT adapter handles (1) valid input → `model_unavailable`
  with clear message, (2) invalid input → `error`, (3) when
  upstream is granted access → real predictions. This validates
  STS + Python Executor on a real-world contract.
- **C. Workflow benchmark.** Run a fixed multi-tool workflow
  (e.g., PreformulationAI → FormulationAI) repeatedly and
  measure evidence-chain reproducibility under varying inputs.

A combination is likely: B + C validate the OS layer; A is needed
only if B+C alone are insufficient for the publication venue.

---

## 6. Proposed discussion agenda (30 minutes)

1. **(5 min) FormulationOS walk-through.** Streamlit UI; rule-based
   planner; the 5-layer architecture in `docs/architecture.md`.

2. **(5 min) Integration challenges.** Walk through §2 — heterogeneous
   execution interfaces, scientific artifact heterogeneity,
   deterministic-evidence contract. These motivate the STS
   contribution.

3. **(5 min) FormulationDT as candidate first target.** §4 — show
   the GitHub + web probe results, the [CONFIRMED] matrix,
   the 5 [NEEDS CONFIRMATION] questions.

4. **(10 min) Decisions on Q1–Q5.** Walk through §5. The output of
   this session is a decision on Phase 2.1 scope (adapter only vs.
   one-real-model) and an access-level assessment for each of the
   5 platforms.

5. **(5 min) Action items.** Decide on (a) what fills the Q2 access
   matrix, (b) next-step commitments, (c) whether slides (10-page
   internal deck) are needed before any further code.

---

## Appendix — Source documents

### Committed docs

- `docs/maturity/ouyang_platforms.md` — Ouyang portfolio analysis
  (2026-07-03).
- `docs/ouyang_platforms_summary.md` — scientific summary of the
  5 platforms.
- `docs/sts_specification.md` — STS v0.2 schema.
- `docs/system_design.md` — implementation strategy + Adapter
  pattern (§6.1 Option B).
- `docs/research_plan.md` — overall research direction.
- `paper/sections/01_introduction.md` … `08_discussion.md` — paper
  draft.

### Research notes (this directory)

- `docs/research_notes/README.md` — index.
- `docs/research_notes/formulation_dt_adapter.md` — FormulationDT
  adapter research note.
- `docs/research_notes/scientific_model_integration_matrix.md` —
  5-platform integration matrix.

### Probes performed 2026-07-07

- GitHub API: `NamanWang/FormulationDT` repo facts and contents.
- Direct curl: `formulationdt.computpharm.org` HTML body + path
  enumeration.
- Direct curl: `formulationai.computpharm.org` path enumeration.

Probes were lightweight (HTTPS GET on the GitHub API and direct HTTP
GET on the public URLs); no authentication was attempted.