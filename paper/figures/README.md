# Figures

This directory holds figure descriptions and (eventually) TikZ/PGF source.

## Figure 1 — FormulationOS Architecture (5 layers)

**Description:** Top-down layered architecture.

- Layer 5: User Interface (Streamlit / REST API / CLI)
- Layer 4: Scientific Workspace (conversation, DAGs, artifacts, cache, reports)
- Layer 3: Workflow Planner (LLM, structured output) + Workflow Graph (DAG)
- Layer 2: Scientific Registry + Execution Runtime (Retry / Parallel / Cache / Provenance)
- Layer 1: Scientific Models (heterogeneous executors)

A cross-layer Artifact Generator produces Markdown / JSON / CSV / PNG / PDF
artifacts that are written back to the Workspace.

**TikZ source:** `architecture.tex` (TODO)

## Figure 2 — STS extension schema (worked example)

**Description:** Show a complete `tool.yaml` for FormulationAI,
annotating each of the four STS extensions with a colored box
(Scientific Semantics, Planning Hints, Scientific Dependencies,
Provenance Specification).

**TikZ source:** `sts_example.tex` (TODO)

## Figure 3 — End-to-end workflow example

**Description:** Walk-through of "Design ibuprofen tablet + PK":

1. NL query enters at Layer 5
2. Planner (Layer 3) produces DAG
3. DAG executes via Runtime (Layer 2)
4. Artifact Generator produces outputs
5. Workspace (Layer 4) stores everything

Show concrete data flow with example artifacts (formulation_ai output,
pbpk_ai output, dissolution curve).

**TikZ source:** `workflow_example.tex` (TODO)

## Figure 4 — DAG for representative workflow

**Description:** Concrete DAG with 5 nodes (Literature, PreformulationAI,
FormulationAI, PBPK-AI, FormulationDT) showing parallelism
(Literature ∥ PreformulationAI) and dependencies.

**TikZ source:** `dag_example.tex` (TODO)

## Figure 5 — Scientific evidence chain

**Description:** Show a single provenance record's fields and how it
links tool version → input hash → output hash → compute env.

**TikZ source:** `evidence_chain.tex` (TODO)