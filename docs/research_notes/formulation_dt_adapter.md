# FormulationDT Scientific Tool Adapter — Research Note

**Phase:** 2.1 — Pre-implementation (pending lab discussion)
**Date:** 2026-07-07
**Author:** Max + Mavis
**Status:** Design only — no code committed yet.

> **Critical distinction (Phase 2.1 vs 2.2).** This note covers the
> **adapter pathway** (Phase 2.1): STS can wrap a real public
> pharmaceutics ML platform; an adapter is implemented and tested.
> It does **not** cover Phase 2.2 (real pretrained-model integration),
> which is blocked on upstream checkpoints + a packaged inference API.
>
> Throughout this note, claims are tagged **[CONFIRMED]** (verified via
> direct probe or committed docs, with sources cited) or
> **[NEEDS CONFIRMATION]** (inherited from committed docs or plausible
> inference, but not directly verified; requires supervisor or lab
> confirmation).

---

## 1. Contribution

This work supports:

- **paper §4 (FormulationOS Architecture)** §4.3 (heterogeneous executor
  backends) — FormulationDT is the first candidate for the `python`
  executor type beyond mocks.
- **paper §5 (STS Extension Schema)** — exercises the 4 STS
  extensions (Scientific Semantics, Scientific Dependencies, Planning
  Hints, Provenance Specification) on a third-party ML platform
  contract. Whether the schema is **sufficient** for general
  third-party ML platforms is itself an open empirical question —
  FormulationDT is one data point.
- **paper §6.5 (Implementation: built-in tools table)** — adds a new
  row next to the 5 mocks: "FormulationDT (Wang 2024/2025) — adapter
  implemented, returns `model_unavailable` when upstream missing
  (Phase 2.1)".
- **paper §8.4 (Future work)** — reframes "Real model integration" from
  a single binary task into a **two-stage pipeline**: (a) adapter
  pathway, then (b) checkpoint integration. This is more honest about
  what is and is not shippable now.

### What we explicitly claim (Phase 2.1)

> "We implement a Scientific Tool Adapter demonstrating that the STS
> v0.2 schema is sufficient to wrap a publicly-available pharmaceutics
> ML platform (NamanWang/FormulationDT, MIT). The adapter exposes a
> stable interface contract; when upstream pretrained weights or a
> packaged inference API are absent, the adapter returns an explicit
> `model_unavailable` status rather than fabricating predictions."

### What we explicitly do NOT claim

- ❌ "FormulationOS integrates the FormulationDT pretrained model."
- ❌ "12 formulation strategy decisions are available via FormulationOS."
- ❌ "Adapter predictions are validated against published benchmarks."
- ❌ "The adapter reproduces the ROC_AUC 0.78–0.98 reported in
  Wang et al. 2024/2025."

These claims belong to Phase 2.2 and are deferred until upstream
checkpoints + a packaged inference API are available.

---

## 2. Evaluation

### Phase 2.1 verification (this commit target)

| Test | Asserts |
|---|---|
| `T1 — STS schema validation` | `tool.yaml` parses via `ToolSpec.model_validate()`; STS v0.2 rejects unknown fields (`extra="forbid"`). |
| `T2 — Adapter contract signature` | `run(input: dict) -> dict` is callable with well-formed input; never raises uncaught exception. |
| `T3 — Model-unavailable path` | When upstream package is missing, returns `status="model_unavailable"`, `predictions is None`, `warnings` contains adapter-only message. **No fabricated predictions.** |
| `T4 — Invalid-input path` | Bad SMILES (or empty) returns `status="error"` with explicit reason; does not raise. |
| `T5 — Provenance hooks` | Adapter records tool version, input hash, output hash, executor type, timestamps. Reuses v0.1 `ProvenanceSpec`. |
| `T6 — End-to-end smoke` | Registry loads the adapter; Planner ranks it; Orchestrator executes; Report renders with `model_unavailable` status and the upstream-not-found warning surfaced. |

### Phase 2.2 verification (future, blocked)

- **M1 — Benchmark parity.** Comparison against Wang et al. 2024/2025's
  reported ROC_AUC (0.78–0.98) on a held-out drug set.
- **M2 — Stability.** Across FormulationOS runs, `input_hash` is
  deterministic; `output_hash` is deterministic for non-LLM tools.
- **M3 — Cost + latency.** Profile under realistic batch sizes; record
  in `cost:` field of ToolSpec.

### Tests that explicitly REJECT the "fake 12 predictions" pattern

A naive adapter that takes SMILES, runs RDKit + Lipinski rules, and
emits 12 "decisions" would pass tests that assert
`len(decisions) == 12` — but it would fail **T3** (it fabricates
predictions when the real model is missing) and **T6** (the output
would be misleading in any downstream Report). Tests **must** assert:

- `out["status"] == "model_unavailable"` when upstream missing, AND
- `out["predictions"] is None` in that case, AND
- `out["warnings"]` contains a string with `"adapter"` AND `"upstream"` (or equivalent).

A test that asserts `len(out["formulation_decisions"]) == 12` is a
**regression bait**: it would pass under both the honest adapter and
the fake-heuristic adapter, hiding the very behaviour we forbid. Do
not write such a test.

---

## 3. Figure

**No new figure slot.**

The adapter can be added as a single row in the paper §6.5
implementation table, and as a sub-element of Figure 1 (5-layer
architecture, Layer 1 "Scientific Models") showing the Adapter pathway
visually — `FormulationOS → Adapter → Upstream (when available)` with
a clear "Adapter ready, model checkpoint pending" annotation.

If a dedicated figure is desired in a future revision, a small
flowchart would suffice. Not required for the current paper draft.

---

## 4. Criticism

### What reviewers will attack (and our counters)

| Attack | Counter |
|---|---|
| "You claim integration but only show an empty adapter." | Adapter returns explicit `model_unavailable` status; Phase 2.2 will plug in checkpoints; interface stability is proven by T1–T6 tests. The paper claim is about the *pathway*, not the inference result. |
| "Why not use MCP / OpenAPI directly?" | STS is an **extension schema** over MCP/OpenAPI; a FormulationOS tool can be derived from an MCP descriptor (see `docs/sts_specification.md` §1, §5.4). |
| "NamanWang/FormulationDT isn't a real scientific tool." | It is — Wang et al. 2024/2025, *Journal of Controlled Release* 378:619–636, DOI: 10.1016/j.jconrel.2024.12.043, MIT-licensed repository. |
| "How is this different from LangChain tool wrapping?" | STS has 4 scientific extensions that LangChain tools lack: **Scientific Semantics**, **Scientific Dependencies**, **Planning Hints**, **Provenance Specification**. None of these are first-class in LangChain / LlamaIndex / generic agent frameworks. |
| "Your adapter returns no predictions — what's the point?" | The contribution is the **integration pathway**, not the inference result. The pathway proves STS can carry a real tool contract; the predictions arrive when the upstream checkpoint lands. This separation is itself a paper-worthy framing (paper §8.4: deterministic evidence, not deterministic models). |
| "Why a separate `formulation_dt_real` directory next to the existing `formulation_dt` mock?" | The existing `formulation_dt` mock is committed on `main` (dissolution profile, Weibull curve, 155 tests). Replacing it would break v0.1 evidence. The new adapter is a **pathway demonstrator**, distinct from the mock. |

### Risk: drift between Phase 2.1 and Phase 2.2 documentation

Once Phase 2.2 lands, the README + ToolSpec must be updated to flip
`mock: true → mock: false` and to add the upstream benchmark numbers
to §2 above. A drift here would re-introduce the "mock-as-production"
anti-pattern from AGENTS.md §12.

---

## 5. Citation

### Primary (the wrapped tool)

- Wang et al. 2024/2025. **AI-directed formulation strategy design
  initiates rational drug development.** *Journal of Controlled Release*
  378:619–636. DOI: 10.1016/j.jconrel.2024.12.043.
- Repository: https://github.com/NamanWang/FormulationDT (MIT license).

### Related (FormulationOS context)

- Ouyang Defang lab portfolio: https://www.computpharm.org/ (FormulationAI,
  PharmSD, PharmDE, PreformulationAI, FormulationMM, AI-PBPK).
- FormulationAI main paper: *Briefings in Bioinformatics* 2023 (bbad419,
  66+ citations).
- See [`docs/maturity/ouyang_platforms.md`](../maturity/ouyang_platforms.md)
  for full portfolio analysis.
- See [`docs/ouyang_platforms_summary.md`](../ouyang_platforms_summary.md)
  for scientific capabilities (inputs, outputs, models, limitations,
  integration paths).

### Related (LLM-orchestrated scientific tools, for related-work)

- MDCrow — Pharm-AI for chemistry.
- ChemCrow — chemistry tool use.
- AI Scientist (Sakana) — autonomous research.

### Related (tool specifications STS extends)

- Model Context Protocol (MCP) — Anthropic.
- OpenAPI — tool descriptor standard.
- ToolCards — research prototypes.

### Related (scientific workflow systems)

- Galaxy, Nextflow, Snakemake, Airflow, Prefect, Kubeflow — comparison
  in paper §2 (Related Work).

---

## Appendix A — NamanWang/FormulationDT repository investigation

**Probed 2026-07-07** via GitHub API (HTTPS).

### Repository facts

| Field | Value |
|---|---|
| Owner / name | `NamanWang` / `FormulationDT` |
| Description | "the first data-driven and knowledge-guided AI formulation strategy decision platform" |
| Primary language | Jupyter Notebook |
| License | MIT |
| Repo size | ~1.6 MB |
| Last updated | 2025-08-09 |
| Stars | 0 (low visibility) |
| README length | 180 bytes (minimal) |

### Top-level layout

```
.gitignore
Code/                  # training + inference scripts (per-decision classifiers)
Data/                  # training datasets — exact contents TBD
LICENSE                # MIT
README.md              # 180 bytes
TrainingRecords_MLP/   # model training records — exact format TBD
```

### What is present

- **Training code** for multiple per-decision classifiers: DT, KNN,
  LR, LightGBM, NN, RF, SVM, nBayes (per the published paper).
- **Feature engineering** based on RDKit descriptor calculation.
- **Training scripts** (presumably end-to-end pipelines).

### What is NOT present (as of probe)

- **Pretrained weights** (`.pkl`, `.h5`, `.pt`, `.joblib`) — GitHub code
  search returned no large model files in tracked git history.
- **Packaged inference API** — no `setup.py` / `pyproject.toml`
  exposing a `predict_decisions(smiles, formulation_type)` function;
  no top-level `formulation_dt/__init__.py`.
- **Continuous integration** — no `.github/workflows/` observed.

### Web service probe [CONFIRMED via direct curl, 2026-07-07]

The repository README claims availability at
`http://formulationdt.computpharm.org/`. Probe of this URL:

- HTTP 200 returned, but the **HTML body is a 2023 HTTrack mirror of
  `formulationai.computpharm.org`** (authored by Jie Dong, describes
  FormulationAI's drug solubilization).
- `/api`, `/predict`, `/swagger`, `/docs` paths all return 404
  (or 301 redirect to home).

[NEEDS CONFIRMATION] The reason this URL serves a mirror rather than
the documented FormulationDT deployment is **not clear from public
sources**. Possibilities to be ruled out by supervisor / lab
verification include: (a) the domain is parked / aliased to a sibling
site, (b) the actual deployment is at a different URL, (c) the
deployment is auth-gated at a different domain, (d) the deployment is
offline or under maintenance. Each requires lab confirmation; we do
not assume any of them.

**Practical implication.** The HTTP executor pathway against
`formulationdt.computpharm.org` is **not directly verifiable from
public sources**. The adapter pathway (Phase 2.1) does not depend on
this URL and remains viable.

### Integration strategy implications [status as of 2026-07-07]

| Option | Feasibility | Source of status |
|---|---|---|
| **HTTP executor** against `formulationdt.computpharm.org` | Blocked from public probing | [CONFIRMED] URL serves a 2023 mirror; [NEEDS CONFIRMATION] whether an alternate URL or auth-gated API exists |
| **Python executor (Adapter)** wrapping `formulation_dt` package | Partially blocked | [CONFIRMED] code present, no `setup.py`, no packaged inference API, no pretrained weights; [NEEDS CONFIRMATION] whether the lab will package an API or share weights |
| **Adapter pathway (Phase 2.1)** demonstrating interface + status contracts | Available | [CONFIRMED] no upstream dependency; tests can be written and run locally |

---

## Appendix B — Open questions for the lab / 师兄

These are the concrete questions to bring to the discussion:

1. **FormulationDT web service.** Is `formulationdt.computpharm.org`
   currently deployed? If yes, at what URL? Is there a programmatic
   API (public or auth-gated)?
2. **Pretrained weights.** Are pretrained weights for the 12
   FormulationDT decisions available? In what format (`.pkl`,
   `.joblib`, ONNX, …)? Under what license terms?
3. **Public code scope.** Are `Code/`, `Data/`, `TrainingRecords_MLP/`
   in `NamanWang/FormulationDT` sufficient to retrain from scratch, or
   is the curated training dataset not fully public?
4. **Inference API packaging.** Would the lab be willing to package
   `predict_decisions(smiles, formulation_type)` as a pip-installable
   Python module? (Smallest possible Phase 2.2 enabler.)
5. **FormulationAI / PreformulationAI.** Do these platforms expose a
   programmatic API (e.g., to power their own web UI)? Could
   FormulationOS access it under a research collaboration?
6. **AI-PBPK.** What auth credentials are required? Is the
   SimBiology-derived Python model available for direct integration,
   or is web-UI access the only path?
7. **License.** Are the Ouyang platforms available for integration
   under their published CC BY-NC-SA 4.0 license, or do they require
   additional collaboration agreements?