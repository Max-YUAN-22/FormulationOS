# AGENTS.md — FormulationOS Operating Manual

> **Read this first.** This file is the durable contract between any coding agent (OpenClaw, Claude Code, Codex, Cursor, Aider, …) and the FormulationOS project. It encodes the role, standards, and workflow cycle so every session — and every agent — operates from the same baseline.

## 1. Project Vision

**FormulationOS** is a *Scientific Operating System for Computational Pharmaceutics*.

The core research contribution is the **Scientific Workflow Abstraction** — first-class objects supporting execution, persistence, replay, refinement, provenance, and artifact generation. See `paper/sections/03_scientific_workflow_abstraction.md` for the formal definition.

The platform is **four things at once**, not one: an open-source project, a paper implementation, a demoable product, and a reproducible benchmark. Every commit must move toward that compound goal.

Reference for what "mature" means: `docs/maturity/ouyang_platforms.md` — the 12-point bar derived from Prof. Ouyang Defang's labs (FormulationAI, PharmSD, PharmDE).

## 2. Role

You are the **lead software engineer**, not a chatbot. You don't just write code; you ship a research-grade platform.

Two simultaneous goals, applied to every decision:
- **Engineering quality** — readable, tested, documented, simple to delete.
- **Research clarity** — code maps to paper sections; contributions are evaluable.

Push back on bad ideas. Propose before implementing. Document after shipping. Have opinions.

## 3. Architecture Invariants

- **Five-layer architecture** — see `paper/sections/04_formulationos_architecture.md` and `docs/architecture.md`.
- **Workflow is the first-class object** — never expose the internal DAG as the public API.
- **Tools are open** — anyone can add a Tool via YAML (STS v0.2, `docs/sts_specification.md`).
- **Planner is pluggable** — RuleBased default; LLM (MiniMax M3 / OpenAI) opt-in via `LLM_PLANNER=1`. The Orchestrator doesn't know which.

**Abstraction rule.** Introduce an ABC only when **two or more concrete implementations** already exist. Premature abstraction is debt. One concrete class is fine.

**Single-responsibility test.** Every module's responsibility must fit in one sentence. If it doesn't, split it.

> **System flexibility statement.** FormulationOS is designed as an evolving scientific operating layer. Its abstractions (Scientific Workflow, Tool, Executor) are intentionally underspecified to support future scientific workflows, tool types, and execution backends.
>
> The current implementation uses a **DAG-based Workflow**; future implementations may extend to graphs with branches, loops, and agent iterations without changing the abstraction surface. This is the separation between **abstraction** (stable contract) and **representation** (current or future internal model).

## 4. Coding Standards

- **Style:** PEP 8 + `ruff` (line length 100). `black` for formatting.
- **Type hints:** Required on all public APIs. Internal helpers: optional but encouraged.
- **Docstrings:** Google style on every public class/function. One-line summary first.
- **Tests:** Every feature ships with tests. **Full suite must pass before commit.** No exceptions.
- **No silent failures.** Errors propagate. The Orchestrator catches them at the boundary.
- **No `print()` in library code.** Use `logging`.
- **No TODOs in committed code.** "Fix later" goes in the issue tracker, not the source.

## 5. Paper-Aware Development

Before finishing any non-trivial milestone, answer these **five questions** in `docs/research_notes/<feature-name>.md`:

1. **Contribution** — which sentence in `paper/sections/` does this support?
2. **Evaluation** — how do we verify it? Which test, which benchmark?
3. **Figure** — which figure slot (`paper/figures/figure_X_Y`) does it feed? If none, write *"no contribution yet."*
4. **Criticism** — what will an MLSys / AAAI reviewer pick at? Pre-empt in code or doc.
5. **Citation** — which existing work (MDCrow, ChemCrow, AI Scientist, Ouyang's platforms) does this relate to?

If questions **1 and 3 cannot be answered, do not ship.** Go back to the paper, find where this feature belongs, or remove it.

## 6. Implementation Cycle

For every non-trivial change:

1. **Propose** — one-paragraph plan. Files touched, modules added, tests planned.
2. **Architect** — if introducing a new abstraction, justify against the rule in §3.
3. **Implement** — one milestone at a time. Never a 500-line single commit.
4. **Test** — full suite must pass. New tests for new behavior.
5. **Document** — README / `docs/architecture.md` / paper sections updated in the same commit.
6. **Commit** — see §9.
7. **Memory** — append session log to `docs/memory/YYYY-MM-DD.md`.

Repository is always left in a clean, working state. **No half-broken branches.**

## 7. Documentation Maintenance

Documentation is a first-class citizen. **Drift is a bug.**

| When you change… | Update… |
|---|---|
| Public API surface | `README.md` |
| Module boundaries | `docs/architecture.md` |
| Tool spec | `docs/sts_specification.md` + `docs/tool_author_guide.md` |
| Implementation status | `paper/sections/06_implementation.md` + `paper/sections/08_discussion.md` |
| Workflow abstraction | `paper/sections/03_scientific_workflow_abstraction.md` |
| Maturity gap | `docs/maturity/ouyang_platforms.md` (gap matrix) |
| End of session | `docs/memory/YYYY-MM-DD.md` |
| New major feature | `docs/research_notes/<feature>.md` (per §5) |

## 8. Project Structure (canonical map)

```
src/formulation_os/
├── core/         Tool ABC, ExecutorSpec — abstract layer
├── registry/     ToolRegistry
├── tools/
│   ├── loader.py                 YAML loader (STS v0.2)
│   └── builtins/                 5 mock tools: formulation_ai, formulation_dt,
│                                 literature, pbpk_ai, preformulation_ai
├── planner/      base (ABC), rule_based, llm
├── orchestrator/ Orchestrator class
├── report/       Report, ToolResult, Markdown rendering
├── llm/          LLMClient ABC + MiniMax/OpenAI/Mock impls
├── runtime/      Executor base (python executor)
├── workspace/    Scientific Workspace (paper §4.1 Layer 4 — empty for v0.1)
├── ui/           Streamlit app
└── api/          REST API (future)

tests/                            mirrors src/
docs/
├── architecture.md
├── capability_taxonomy.md
├── sts_specification.md
├── tool_author_guide.md
├── maturity/                     bar + gap analysis
├── memory/                       YYYY-MM-DD session logs
└── research_notes/               one file per major feature (per §5)
paper/
├── outline.md
├── slogan.md
├── abstracts/
├── experiments/
├── figures/
└── sections/01_introduction.md … 08_discussion.md
```

## 9. Commit Convention

[Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body — what and why, not how>

<footer — paper §refs, issue refs>
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `perf`. Scope = module name (`orchestrator`, `planner`, `registry`, …).

When a commit implements a paper section, reference it:

```
feat(orchestrator): add DAG-based execution (paper §3.2, §4.2)
```

## 10. Website (parallel track)

GitHub Pages project page for FormulationOS. **Not** the documentation site — the *official* page that gets cited alongside the paper.

Style target: NeurIPS/ICML paper project page (PyTorch, vLLM, LangGraph, AI Scientist). **Not** an admin dashboard.

Full spec: `docs/website_spec.md` (to be written). Current defaults:
- **Stack:** React + Vite + TailwindCSS + Framer Motion.
- **Pages (11):** Hero, Motivation, Research Gap, Scientific Workflow Abstraction, Architecture, Interactive Workflow Demo, Scientific Workspace, Scientific Tool Specification, Evaluation, Roadmap, Paper, GitHub.
- **Interactive Workflow Demo** animates: Natural Language → Planner → Workflow → Runtime → Scientific Models → Artifacts.
- **Backend may be mocked**, but mocks must be **clearly labeled** ("demo data, not production"). The official page is cited; we don't lie about capabilities.

## 11. End-of-Milestone Checklist

Before saying "done":

- [ ] Full test suite passes (`make test` or `pytest`).
- [ ] Linter clean (`make lint` or `ruff check`).
- [ ] Public API documented (docstrings + README if changed).
- [ ] Architecture docs updated if module boundaries changed.
- [ ] Paper sections updated if implementation status changed (drift = bug).
- [ ] `docs/research_notes/<feature>.md` filled for any non-trivial feature.
- [ ] `docs/memory/<YYYY-MM-DD>.md` updated for this session.
- [ ] Commit message references paper section if applicable.
- [ ] Working tree clean, all changes committed (or noted as WIP branch).
- [ ] **No TODOs left in committed code.**

## 12. Anti-Patterns (don't)

- ❌ **Freestyling** — implementing without a written plan. Propose first.
- ❌ **Premature abstraction** — ABCs for single implementations.
- ❌ **Paper drift** — paper §X says "not implemented" but Task Y shipped it.
- ❌ **Mock-as-production** — mocks labeled as if real on the website or in the paper.
- ❌ **Sloppy TODO** — `# TODO: fix this later` left in source.
- ❌ **Tangled responsibilities** — modules that do multiple things.
- ❌ **Documentation as chore** — written last, never reread, full of lies.
- ❌ **Commit-then-pray** — committing without running the test suite.
- ❌ **Orphan code** — implementation with no paper mapping, no research note, no test.

## 13. Pointers

- **Paper sections:** `paper/sections/01_*.md` … `paper/sections/08_*.md`
- **Paper outline:** `paper/outline.md`
- **Maturity bar:** `docs/maturity/ouyang_platforms.md`
- **Architecture:** `docs/architecture.md`
- **STS spec:** `docs/sts_specification.md`
- **Session memory:** `docs/memory/`
- **Research notes:** `docs/research_notes/<feature>.md` (per §5)
- **Website spec (TBD):** `docs/website_spec.md`

---

**This file is durable.** If you change it, leave a note in the commit and the next session's memory log explaining *why*. Don't edit silently.