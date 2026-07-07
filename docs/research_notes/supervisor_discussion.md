# Supervisor Discussion — Phase 2 Scientific Model Integration

**Status:** Draft for supervisor meeting
**Date:** 2026-07-07 / 2026-07-08
**Author:** Max + Mavis

## Purpose

Document the current state of FormulationOS, the integration challenges
faced when moving from mocks to real scientific models, and the
specific questions to bring to the supervisor. This document is the
**discussion agenda** — not a commitment to any particular integration
path.

Throughout this document, claims are tagged:

- **[CONFIRMED]** — verified via direct probe (GitHub API, web curl)
  or unambiguous committed doc (sources cited inline).
- **[NEEDS CONFIRMATION]** — based on committed docs or plausible
  inference, but not directly verified; requires supervisor or lab
  confirmation.

---

## 1. Current FormulationOS status

### 1.1 What is shipped on `main`

| Item | Status | Source |
|---|---|---|
| HEAD commit | `4ac26ee docs: remove internal meeting prep from public repo` | [CONFIRMED — `git log --oneline -1`] |
| Working tree | Clean apart from untracked docs/research_notes/ and docs/memory/2026-07-07.md | [CONFIRMED — `git status`] |
| Test suite | 151 passing on `main` | [CONFIRMED — `make test`, 2026-07-07] |
| Code size | ~3300 lines Python | [CONFIRMED — `find src -name '*.py' | xargs wc -l`] |
| Commits | 13 on `main` since bootstrap | [CONFIRMED — `git log --oneline`] |

### 1.2 Architecture and code support

The 5-layer architecture is committed in `docs/architecture.md` and
`paper/sections/04_formulationos_architecture.md`. Code support:

| Layer | Component | Code | Status |
|---|---|---|---|
| 1 | Scientific Models | `src/formulation_os/tools/builtins/*/` (5 mocks) | Live (mock-only) |
| 2 | Registry + Runtime | `registry/registry.py`, `runtime/executor.py`, `orchestrator/orchestrator.py` | Live (PythonExecutor only) |
| 3 | Workflow Planner | `planner/rule_based.py`, `planner/llm.py`, `planner/base.py` | Live (Rule-based default + LLM opt-in) |
| 4 | Scientific Workspace | `workspace/` (empty) | Planned (Phase 2+) |
| 5 | User Interface | `ui/app.py` (Streamlit) | Live |

### 1.3 Paper claim → code support

| Paper concept | Code support | [CONFIRMED] |
|---|---|---|
| Scientific Workflow as first-class object | `Orchestrator` + `Report` (container of `ToolResult`s) | `orchestrator/orchestrator.py` |
| Tool abstraction | `Tool` ABC + `ToolSpec` (Pydantic, STS v0.2, `extra="forbid"`) | `core/tool.py` |
| Runtime / Executor | `Executor` ABC + `PythonExecutor` | `runtime/executor.py` |
| Planner pluggability | `Planner` ABC + 2 implementations | `planner/base.py` |
| STS v0.2 schema | `ToolSpec` enforces `extra="forbid"`; 4 extension models (ScientificSemantics, PlanningHints, ScientificDependencies, ProvenanceSpec) | `core/tool.py`, `docs/sts_specification.md` |
| Streamlit UI demo | `ui/app.py` end-to-end | Manual launch |

### 1.4 What is NOT yet shipped

- **Real scientific models.** All 5 built-in tools are mocks
  (`mock: true`, output includes `warnings: ["MOCK OUTPUT..."]`).
  [CONFIRMED — each `tools/builtins/*/backend.py`]
- **HTTP / CLI / MCP / gRPC / Docker executors.** Only `python`
  executor is implemented. [CONFIRMED — `runtime/executor.py`,
  `tools/loader.py`]
- **Scientific Workspace (Layer 4).** Directory exists but is empty.
  [CONFIRMED — `ls src/formulation_os/workspace/`]
- **Full provenance emission.** Paper §6.3 shows the full
  `execution_id / tool_version / input_hash / output_hash / ...`
  schema, but v0.1 Orchestrator captures only `duration_ms` and
  `warnings`. [CONFIRMED — `orchestrator/orchestrator.py:_run_one`]
- **Embedding-based retriever.** Keyword-only matching today; vector
  index planned for Task 3 v2. [CONFIRMED —
  `planner/rule_based.py` docstring]

### 1.5 Position relative to the maturity bar

The supervisor's reference bar (Prof. Ouyang's lab platforms,
documented in `docs/maturity/ouyang_platforms.md`) lists 7 maturity
characteristics: real ML models, curated datasets, multi-paper
track record, task-focused web UI, account system, application-domain
analysis, experimental validation. FormulationOS v0.1 satisfies **0
of 7**. The gap is the Phase 2+ work — but the bar is per-platform,
not per-OS. FormulationOS's path is to **wrap** real platforms
rather than build them, so the question is which platform to wrap
first, and under what conditions.

---

## 2. Why scientific model integration is challenging

### 2.1 Five distinct platforms, five distinct interfaces

The Ouyang portfolio covers 5 pipeline stages:

```
PreformulationAI → FormulationAI → FormulationDT
                                 → FormulationMM → AI-PBPK
```

Each platform is **independent** in interface, license, deployment
mode, and scientific methodology. There is no common API, no shared
SDK, no unified authentication system across the 5 platforms.

[NEEDS CONFIRMATION] The absence of a shared API is inferred from
probed public URLs and `docs/ouyang_platforms_summary.md` (which
documents each platform's web UI as the only documented interface).
The lab may have internal APIs not surfaced in either source.

### 2.2 Three artefacts matter for integration

For any platform, integration requires **at least one** of:

1. **Public source code** — to wrap a Python executor around it.
2. **Deployed service with programmatic API** — to wrap an HTTP
   executor against it.
3. **Pretrained model weights** — to actually run inference (vs.
   retraining from scratch, which is compute-prohibitive).

Most platforms have **at most one** of these three. See §3 for the
matrix.

### 2.3 No public inference API observed (probed 2026-07-07)

[CONFIRMED] Direct curl probes of `formulationai.computpharm.org` and
`formulationdt.computpharm.org` returned:

- `/api`, `/swagger`, `/openapi.json`, `/docs` paths: 301 redirect
  to home page; no public REST surface observed.
- HTTP 200 on the homepage returns the web UI HTML; no JSON API
  endpoints visible in the response body.

[NEEDS CONFIRMATION] The other three platforms (PreformulationAI,
FormulationMM, AI-PBPK) were **not directly probed** on 2026-07-07;
their API status is inferred from `docs/ouyang_platforms_summary.md`
which documents "no programmatic API" for each.

### 2.4 Risk of fabricating predictions

A natural temptation when wrapping a platform without weights is to
provide a **heuristic fallback** that returns plausible-looking
results. This was the anti-pattern in a discarded working tree
(2026-07-07): an "adapter" that computed MW / logP / Lipinski rules
and emitted 12 fake "decisions" labeled as FormulationDT predictions.
This violates AGENTS.md §12 (mock-as-production) and would draw
immediate reviewer attack.

The **safe pattern** is: adapter returns explicit `model_unavailable`
status when upstream is missing, with no fabricated predictions.
Phase 2.1 ships this safe pattern; Phase 2.2 (real inference) is
blocked on upstream cooperation.

### 2.5 License and collaboration boundary

[NEEDS CONFIRMATION] Ouyang's published platforms are documented as
CC BY-NC-SA 4.0 in `docs/maturity/ouyang_platforms.md`. Whether this
license covers integration into a third-party tool, or whether a
separate collaboration agreement is required for academic /
non-commercial redistribution, requires supervisor / lab confirmation.
The **NC** (Non-Commercial) clause is the binding constraint for
FormulationOS distribution.

---

## 3. Five platform integration matrix

See `docs/research_notes/scientific_model_integration_matrix.md` for
the full matrix with verification tags per cell. Summary (verification
status in brackets):

| Platform | Code | API | Weights | Realistic mode | Verification |
|---|---|---|---|---|---|
| FormulationAI | [NEEDS CONFIRMATION] | [CONFIRMED no public REST] | [NEEDS CONFIRMATION] | HTTP executor + UI demo fallback | Low |
| PreformulationAI | [NEEDS CONFIRMATION] | [NEEDS CONFIRMATION — not probed] | [NEEDS CONFIRMATION] | HTTP executor + UI demo fallback | Very low |
| FormulationMM | [NEEDS CONFIRMATION] | [NEEDS CONFIRMATION — not probed] | [NEEDS CONFIRMATION] | docker executor (Phase 3) | Very low |
| **FormulationDT** | [CONFIRMED] MIT | [CONFIRMED absent] | [CONFIRMED absent in repo] | **Adapter pathway (Phase 2.1)** | **High** |
| AI-PBPK | [NEEDS CONFIRMATION] partial | [NEEDS CONFIRMATION] | [NEEDS CONFIRMATION] | HTTP + auth | Low |

**Highest-confidence target** (where the public evidence base is
strongest): **FormulationDT**, where the GitHub repository state is
fully documented and probe-verified.

---

## 4. FormulationDT investigation

See `docs/research_notes/formulation_dt_adapter.md` for full details.
Summary of probe 2026-07-07:

### 4.1 Confirmed facts

| Fact | Source |
|---|---|
| Repo exists at `NamanWang/FormulationDT` | [CONFIRMED — GitHub API] |
| MIT license | [CONFIRMED — GitHub API] |
| ~1.6 MB, primary language Jupyter Notebook | [CONFIRMED — GitHub API] |
| 0 stars, last updated 2025-08-09 | [CONFIRMED — GitHub API] |
| README is 180 bytes — minimal | [CONFIRMED — GitHub API] |
| Top-level layout: `Code/`, `Data/`, `TrainingRecords_MLP/`, `LICENSE` | [CONFIRMED — GitHub API] |
| **No `setup.py` / `pyproject.toml`** — not pip-installable | [CONFIRMED — GitHub API] |
| **No large model files** (`.pkl`, `.h5`, `.pt`, `.joblib`) in tracked history | [CONFIRMED — GitHub code search; caveat: code search needs auth for full coverage] |
| **Paper exists**: Wang et al. 2024/2025, *J Control Release* 378:619–636, DOI: 10.1016/j.jconrel.2024.12.043 | [NEEDS CONFIRMATION — DOI not directly verified 2026-07-07; documented in `docs/ouyang_platforms_summary.md`] |
| **Canonical URL is unreliable**: `formulationdt.computpharm.org` returns 200 but body is a 2023 HTTrack mirror of `formulationai.computpharm.org` | [CONFIRMED — direct curl 2026-07-07] |

### 4.2 Open questions (requires supervisor / lab)

1. Where is the **actual** FormulationDT web deployment?
2. Are pretrained weights for the 12 decisions **available outside
   the published paper**? (The paper claims ROC_AUC 0.78–0.98 per
   `docs/ouyang_platforms_summary.md`; this implies trained models
   exist somewhere — but where?)
3. Would the lab **package** `predict_decisions(smiles, formulation_type)`
   as a pip-installable Python module? (Smallest possible Phase 2.2
   enabler.)
4. Are `Code/`, `Data/`, `TrainingRecords_MLP/` sufficient to
   **retrain** from scratch, or is the curated training dataset
   only partial?
5. Is the Wang et al. 2024/2025 DOI correct, or is the canonical
   paper published under a different DOI / venue?

### 4.3 Phase 2.1 deliverable (does not depend on lab answers)

Even without lab answers, FormulationOS can ship a **Phase 2.1
adapter** that:

- Implements the STS v0.2 contract for `FormulationDTReal`.
- Returns `status="model_unavailable"` when upstream is absent.
- Returns `status="error"` on invalid input.
- **Never fabricates predictions.**
- Ships with 6 tests (T1–T6 in research note).
- Adds a row to paper §6.5 implementation table.

This is a **proof of pattern**, not a claim of model integration.
Reviewers can verify the integration pathway without depending on
upstream cooperation.

---

## 5. Open questions for supervisor meeting

### 5.1 Strategy questions

1. **Phase 2 sequencing.** Recommended sequence:
   - Phase 2.1 = FormulationDT adapter pathway (no model claim;
     immediately shippable).
   - Phase 2.3 = FormulationAI / PreformulationAI HTTP executor
     (highest scientific value, but requires API access).
   - Phase 2.5 = AI-PBPK (final validation step; highest integration
     cost).
   Is this sequencing consistent with the supervisor's view?

2. **Adapter alone vs broader scope.** Is shipping a FormulationDT
   adapter (without model integration) sufficient for the paper's
   "real model integration" claim, or does the paper require at
   least one fully-integrated real model?

3. **OS-layer vs model-layer split.** Should the paper focus on the
   OS layer (workflow abstraction, STS, provenance, deterministic
   evidence) and treat real model integration as future work, or
   should it demonstrate end-to-end real-model workflow as the
   headline result?

### 5.2 Lab cooperation questions

4. **FormulationDT deployment.** Where is the actual web service?
   Is there a programmatic API behind the UI?
5. **Pretrained weights access.** Under what conditions (if any)
   can FormulationOS access the 12-decision pretrained weights?
6. **Inference API packaging.** Would the lab accept a collaboration
   to package `predict_decisions()` as a pip module?
7. **FormulationAI / PreformulationAI APIs.** Do these have any
   programmatic surface (public or auth-gated)?
8. **AI-PBPK.** What credentials are required for integration?

### 5.3 License / collaboration questions

9. **License scope.** Does CC BY-NC-SA 4.0 cover integration into
   FormulationOS, or does a separate collaboration agreement apply?
10. **Co-authorship / acknowledgement.** Would supervisor
    collaboration with the Ouyang lab be in scope (paper
    acknowledgement, joint publication)?

### 5.4 Practical questions

11. **Compute for retraining.** If retraining is required, what
    compute is available? (FormulationDT's training scale per
    `docs/ouyang_platforms_summary.md` suggests a 700K-sample dataset
    — unclear if the full dataset is public.)
12. **Paper timeline.** What is the supervisor's view on the
    publication timeline for the current paper draft?

---

## 6. Proposed discussion points (30-min meeting agenda)

1. **(5 min) FormulationOS status walk-through.** Show the Streamlit
   UI; demo the rule-based planner picking tools; show the 151 tests
   passing; show the 5-layer architecture in `docs/architecture.md`.

2. **(5 min) Adapter pathway concept.** Walk through
   `docs/research_notes/formulation_dt_adapter.md` — explain why
   the adapter does NOT fabricate predictions, why `model_unavailable`
   is the safe pattern, what T1–T6 tests verify.

3. **(5 min) FormulationDT probe findings.** Show the GitHub probe
   results (training code only, no API, no weights) and the
   web-probe finding (canonical URL is a 2023 mirror).

4. **(10 min) Five-platform integration matrix.** Walk through
   `docs/research_notes/scientific_model_integration_matrix.md` —
   discuss which platform the supervisor sees as the highest-value
   first integration target.

5. **(5 min) Open questions and decision.** Decide on Phase 2.1
   scope (adapter only vs. requiring real model) and lab cooperation
   strategy.

---

## Appendix — Source documents

### Committed docs that inform this document

- `docs/maturity/ouyang_platforms.md` — Ouyang portfolio analysis
  (2026-07-03, commit `ba0c0b0`).
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
  adapter research note (5-question reviewer checklist).
- `docs/research_notes/scientific_model_integration_matrix.md` —
  5-platform integration matrix.

### Probes performed 2026-07-07

- GitHub API: `NamanWang/FormulationDT` repo facts and contents.
- Direct curl: `formulationdt.computpharm.org` HTML body + path
  enumeration.
- Direct curl: `formulationai.computpharm.org` path enumeration.

Probes were lightweight (HTTPS GET on the GitHub API and direct HTTP
GET on the public URLs); no authentication was attempted.