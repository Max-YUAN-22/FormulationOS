# Scientific Model Integration Matrix

**Phase:** 2 — pre-implementation strategy
**Date:** 2026-07-07
**Author:** Max + Mavis
**Status:** Research artefact — pending lab discussion.

## Purpose

This matrix surveys the integration pathway for each of the 5
Ouyang-lab scientific platforms that FormulationOS aims to wrap. Each
row captures the **current state of the upstream platform** and
identifies the **most realistic integration mode** for FormulationOS.

The matrix is the working artefact for the discussion with 师兄 / the
Ouyang lab. It is intentionally explicit about uncertainty: cells
marked ❓ or TBD represent information that requires primary research
or direct lab contact, not assumptions.

## The 5 platforms

Throughout this matrix, claims are tagged:

- **[CONFIRMED]** — verified via direct probe (GitHub API, web curl)
  or committed docs (with sources cited inline).
- **[NEEDS CONFIRMATION]** — based on committed docs or plausible
  inference, but not directly verified; requires supervisor or lab
  confirmation.

| Platform | URL | What it predicts | Pipeline stage |
|---|---|---|---|
| **PreformulationAI** | https://preformulationai.computpharm.org/ (web) [NEEDS CONFIRMATION — URL not directly probed 2026-07-07] | Solubility, BCS, pKa, logD, logS, kinetic solubility, developability [per `docs/ouyang_platforms_summary.md`] | 1 |
| **FormulationAI** | https://formulationai.computpharm.org/ (web) [CONFIRMED — homepage returns 200, /api/* paths probed] | Excipient design across 6 systems (cyclodextrin, solid dispersion, phospholipid complex, nanocrystals, SEDDS, liposome) — 16 properties [per `docs/ouyang_platforms_summary.md`] | 2 |
| **FormulationMM** | https://formulationmm.computpharm.org/ (web) [NEEDS CONFIRMATION — URL not directly probed 2026-07-07] | MD simulation: binding free energies, interaction analysis, parameter files [per `docs/ouyang_platforms_summary.md`] | 4 |
| **FormulationDT** | https://github.com/NamanWang/FormulationDT (code, MIT) [CONFIRMED via GitHub API probe] | 12 formulation strategy decisions; dissolution profile; stability probability; formulatability index [per Wang et al. 2024/2025 paper + `docs/ouyang_platforms_summary.md`] | 3 |
| **AI-PBPK** | https://aipbpk.computpharm.org/ (auth-gated web per docs) [NEEDS CONFIRMATION — URL not directly probed 2026-07-07] | Plasma PK curves; 15-organ tissue distribution; AUC; Cmax; Clearance; Bioavailability [per `docs/ouyang_platforms_summary.md`] | 5 |

The complete scientific pipeline (per `docs/ouyang_platforms_summary.md`):

```
Drug SMILES
    ↓
PreformulationAI       (Stage 1 — molecular properties)
    ↓
FormulationAI          (Stage 2 — excipient design)
    ↓
FormulationDT          (Stage 3 — virtual testing, 12 decisions)
FormulationMM          (Stage 4 — molecular dynamics explanation)
    ↓
AI-PBPK                (Stage 5 — in-vivo prediction, validation)
```

FormulationOS's value-add is that the 5 stages can be **composed as a
single Scientific Workflow** rather than 5 manual submissions.

---

## Integration matrix

| Platform | Public code | Programmatic API | Pretrained weights | License | Current state (v0.1) | Realistic integration mode | Verification |
|---|---|---|---|---|---|---|---|
| **FormulationAI** | [NEEDS CONFIRMATION] | [CONFIRMED] no public REST surface (`/api`, `/swagger`, `/openapi.json` all 301-redirect to home); [NEEDS CONFIRMATION] whether any auth-gated API exists | [NEEDS CONFIRMATION] | CC BY-NC-SA 4.0 [per `docs/maturity/ouyang_platforms.md`] | mock (`formulation_ai/`) | HTTP executor (if API exists behind auth) → fallback to UI-driven workflow demo | Low — homepage probed; auth/API unverified |
| **PreformulationAI** | [NEEDS CONFIRMATION] | [NEEDS CONFIRMATION — URL not probed 2026-07-07]; per `docs/ouyang_platforms_summary.md` no programmatic API is documented | [NEEDS CONFIRMATION] | TBD | mock (`preformulation_ai/`) | HTTP executor (if API exists) → fallback to UI-driven workflow demo | Very low — only the URL form was inferred |
| **FormulationMM** | [NEEDS CONFIRMATION] | [NEEDS CONFIRMATION — URL not probed]; per `docs/ouyang_platforms_summary.md` no programmatic API is documented | [NEEDS CONFIRMATION — heavy compute: MD runs typically per-project] | TBD | mock (`formulation_dt/` partially reused) | docker / subprocess executor (MD engines: GROMACS, Amber, OpenMM); compute-heavy, HPC required | Very low — not probed |
| **FormulationDT** | [CONFIRMED] MIT (`NamanWang/FormulationDT`, ~1.6 MB, last updated 2025-08-09) | [CONFIRMED] no packaged `predict_decisions()` API; no `setup.py` / `pyproject.toml` | [CONFIRMED absent in public repo] no large model files (`.pkl`/`.h5`/`.pt`/`.joblib`) in tracked GitHub history; [NEEDS CONFIRMATION] whether weights exist outside the repo | MIT [CONFIRMED] | mock (`formulation_dt/` — dissolution profile, Weibull curve) | **Adapter pathway (Phase 2.1)**: STS tool + status contract + `model_unavailable` semantics → real inference (Phase 2.2, blocked on upstream) | **High — GitHub API probe 2026-07-07** |
| **AI-PBPK** | [NEEDS CONFIRMATION] partial (SimBiology-derived Python in supplementary, per `docs/ouyang_platforms_summary.md`) | [NEEDS CONFIRMATION] auth-gated Streamlit per docs; [NEEDS CONFIRMATION] whether REST surface exists behind auth | [NEEDS CONFIRMATION] | TBD | mock (`pbpk_ai/`) | HTTP executor (with auth) → fallback to UI-driven workflow demo | Low — only doc-inferred |

**Legend:**

- [CONFIRMED] = verified present/absent via direct probe or unambiguous committed doc.
- [NEEDS CONFIRMATION] = based on committed docs or plausible inference, but not directly verified.
- Verification column summarizes overall probe coverage of that row.

---

## Integration strategies — by platform

### Strategy A — HTTP executor against a deployed web service

**Applies to:** FormulationAI, PreformulationAI, AI-PBPK (if any
expose programmatic endpoints behind auth — TBD).

**FormulationOS implementation (sketch):**

```yaml
executor:
  type: http
  url: https://formulationai.computpharm.org/api/v1/predict
  method: POST
  headers:
    Authorization: Bearer ${FORMULATIONAI_API_KEY}
    Content-Type: application/json
  body_template:
    drug_smiles: ${input.drug_smiles}
    target_dose_mg: ${input.target_dose_mg}
```

**Status:** STS v0.2 declares `http` executor type as reserved
(`docs/sts_specification.md` §6, status "🚧 Task 5 / Planned"). The
paper §4.3 lists it as Phase 2 work.

**Blockers (with verification status):**

1. [CONFIRMED] Probed Ouyang platforms' `/api` paths (FormulationAI,
   FormulationDT) return 301 redirects to home; no public REST surface
   observed. [NEEDS CONFIRMATION] whether PreformulationAI /
   FormulationMM / AI-PBPK follow the same pattern (not probed).
2. [CONFIRMED] No OpenAPI spec observed at any probed URL.
3. [NEEDS CONFIRMATION] Auth tokens / API keys are not documented in
   any source I could verify; whether they exist behind authentication
   is unknown.
4. [CONFIRMED] FormulationDT's `formulationdt.computpharm.org` URL
   currently serves a 2023 FormulationAI mirror. Whether the canonical
   URLs for the other 4 platforms are similarly unreliable requires
   direct probing — **do not generalize from FormulationDT alone**.

### Strategy B — Python executor as Adapter around public GitHub code

**Applies to:** FormulationDT (the only platform with public code).

**FormulationOS implementation (sketch):**

```python
# src/formulation_os/tools/builtins/formulation_dt_real/wrapper.py
_UPSTREAM_AVAILABLE = False
_predict_fn = None

try:
    from formulation_dt import predict_decisions  # type: ignore
    _predict_fn = predict_decisions
    _UPSTREAM_AVAILABLE = True
except ImportError:
    pass


def predict(smiles: str, formulation_type: str = "all") -> dict:
    if not _UPSTREAM_AVAILABLE:
        return {
            "status": "model_unavailable",
            "predictions": None,
            "message": (
                "Adapter ready; install upstream + pretrained weights "
                "to enable predictions."
            ),
            "warnings": ["adapter-only: no predictions produced"],
        }
    return {"status": "ok", "predictions": _predict_fn(smiles, formulation_type)}
```

**Status:** Phase 2.1 deliverable (this commit target). Adapter ships
with `model_unavailable` status; Phase 2.2 adds real inference when
upstream exposes a clean `predict_decisions(smiles, formulation_type)`
API.

**Blockers:**

1. `NamanWang/FormulationDT` does **not** currently expose a
   `predict_decisions` function or `setup.py`.
2. No pretrained weights available on GitHub.
3. README claims `formulationdt.computpharm.org` deployment, but probe
   shows the URL serves a 2023 FormulationAI mirror — actual
   deployment URL needs lab verification.

### Strategy C — Container / subprocess executor for compute-heavy tools

**Applies to:** FormulationMM (MD simulation engines — TBD).

**FormulationOS implementation (sketch):**

```yaml
executor:
  type: docker
  image: formulationmm/formulationmm:latest
  command: ["python", "/app/run_mmp.py"]
  args:
    - "--drug"
    - "${input.drug_smiles}"
    - "--excipient"
    - "${input.excipient_smiles}"
  mounts:
    - {type: bind, src: ${workspace}/mm_runs, dst: /app/output}
```

**Status:** STS v0.2 reserves `docker` executor type; v0.1 does not
implement it. Phase 3 deliverable.

**Blockers (with verification status):**

1. [NEEDS CONFIRMATION] No public Docker image was found in probed
   sources for any Ouyang platform. (Probing was not exhaustive —
   Docker Hub, lab-internal registries, etc., not searched.)
2. [NEEDS CONFIRMATION] Compute-heavy MD simulations are documented
   in `docs/ouyang_platforms_summary.md`; the practical compute
   requirement (GPUs, hours) needs lab confirmation.
3. Output is multi-file (topology + trajectory + analysis) — provenance
   and artifact handling for non-JSON outputs needs design.

---

## Recommended Phase 2 sequencing

Based on the matrix and current blockers:

### Phase 2.1 — FormulationDT adapter pathway (immediate)

- Builds the integration pattern.
- Ships `model_unavailable` status — honest, testable.
- Does **not** require upstream cooperation.
- Proves STS + Python Executor can carry a real-world tool contract.

### Phase 2.2 — FormulationDT real model integration (depends on lab)

Requires **one of**:

1. Pretrained weights from NamanWang / Ouyang's lab, **OR**
2. Re-train from `Code/` + `Data/` (compute-intensive; dataset access uncertain), **OR**
3. API access to a deployed `formulationdt.computpharm.org` service (URL currently unverified).

### Phase 2.3 — FormulationAI / PreformulationAI integration (depends on lab)

- Choose based on what the lab exposes first.
- HTTP executor is the natural fit (assuming the web service has an internal API).
- Requires API spec + credentials.
- **Highest scientific value** of the 5 platforms (most-cited, most-mature).

### Phase 2.4 — FormulationMM integration (Phase 3, deferred)

- Compute-heavy; needs docker executor + HPC.
- Lower priority for paper MVP.
- Necessary for "Stage 4 — molecular dynamics explanation" in the pipeline.

### Phase 2.5 — AI-PBPK integration (depends on lab)

- Auth-gated; depends on credential access.
- Highest scientific value (final validation step) but highest integration cost.
- Necessary for "Stage 5 — in-vivo prediction" in the pipeline.

---

## Strategy decision tree

```
        ┌─ FormulationDT Adapter ──────────┐
        │  Phase 2.1 (next commit target)  │
        │  ↓                                │
        │  model_unavailable OK             │
        └──────────────┬────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
Lab provides              Lab cannot provide
weights / API             weights / API
        │                             │
        ▼                             ▼
Phase 2.2                    FormulationDT stays as
FormulationDT                adapter-only; shift focus
real integration             to FormulationAI /
                             PreformulationAI next
                                     │
                                     ▼
                             Phase 2.3
                             HTTP executor
                             (most realistic next target)
```

---

## Open questions for 师兄 / the lab

1. **FormulationDT web service.** Is `formulationdt.computpharm.org`
   currently deployed? At what URL? Is there a programmatic API
   (public or auth-gated)?
2. **Pretrained weights.** Are pretrained weights for the 12
   FormulationDT decisions available? In what format? Under what
   license terms?
3. **Public code scope.** Are `Code/`, `Data/`, `TrainingRecords_MLP/`
   in `NamanWang/FormulationDT` sufficient to retrain from scratch,
   or is the curated training dataset not fully public?
4. **Inference API packaging.** Would the lab be willing to package
   `predict_decisions(smiles, formulation_type)` as a pip-installable
   Python module? (Smallest possible Phase 2.2 enabler.)
5. **FormulationAI / PreformulationAI APIs.** Do these platforms
   expose a programmatic API (e.g., to power their own web UI)?
   Could FormulationOS access it under a research collaboration?
6. **AI-PBPK.** What auth credentials are required? Is the
   SimBiology-derived Python model available for direct integration,
   or is web-UI access the only path?
7. **License terms.** Are the Ouyang platforms available for
   integration under their published CC BY-NC-SA 4.0 license, or do
   they require additional collaboration agreements?

---

## References

- [`docs/maturity/ouyang_platforms.md`](../maturity/ouyang_platforms.md)
  — Ouyang portfolio analysis (committed 2026-07-03).
- [`docs/ouyang_platforms_summary.md`](../ouyang_platforms_summary.md)
  — Scientific summary of the 5 platforms (inputs, outputs, models,
  limitations, integration paths).
- [`docs/research_notes/formulation_dt_adapter.md`](formulation_dt_adapter.md)
  — FormulationDT-specific research note (this directory).
- [`docs/system_design.md`](../system_design.md) — implementation
  strategy + Adapter pattern (§6.1 Option B).
- [`docs/sts_specification.md`](../sts_specification.md) — STS v0.2
  schema (the contract adapters must satisfy).
- Wang et al. 2024/2025. *J Control Release* 378:619–636. DOI:
  10.1016/j.jconrel.2024.12.043
- NamanWang/FormulationDT repository —
  https://github.com/NamanWang/FormulationDT (MIT, probed 2026-07-07).