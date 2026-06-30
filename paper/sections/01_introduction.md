# §1. Introduction

> **TODO.** Write after Tasks 1–3 land (Tool abstraction, Registry, Planner).

## Sketch

1. **Motivation.** Scientific Foundation Models are exploding. Each lab
   has its own models (FormulationAI, PreformulationAI, PBPK-AI,
   FormulationDT, AlphaFold, ESM, AtomGPT, ClimateGPT, ...), each with
   its own API, repo, and paper. No unified orchestration layer exists.
2. **Pharmaceutics as instance.** Computational pharmaceutics is an
   acute case: drug formulation involves multiple interacting models
   (property prediction → excipient selection → PK simulation →
   dissolution), each in a different lab, with no shared workflow
   substrate.
3. **Our position.** FormulationOS is not a chatbot, not a
   "PharmGPT", not an agent framework. It is a **Scientific Operating
   System** — an orchestration layer with first-class Scientific
   Workflows, persistent Workspace, reproducible evidence chain, and
   a tool catalog with declarative specifications.
4. **Contributions.** Five items:
   - Scientific Workflow Abstraction
   - Scientific Workspace
   - Execution Runtime with Scientific Evidence Chains
   - Scientific Registry with STS (extension schema)
   - FormulationOS: implementation + evaluation
5. **Anti-claim.** We do not promise deterministic models; we promise
   deterministic evidence.

## Bullet references

- See `paper/slogan.md` for one-line statements.
- See `paper/abstracts/v1.md` for the current abstract.