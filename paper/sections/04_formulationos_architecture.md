# §4. FormulationOS Architecture

> **Note.** The 5-layer organization below is the current conceptual stack. As the prototype evolves, layers may be refined, merged, or split; the abstraction surface (Workflow, Tool, Executor) remains the stable contract.

## 4.1 Five layers

(See Figure 1 in `paper/figures/`.)

| Layer | Component | Task |
|-------|-----------|------|
| 5 | User Interface (Streamlit, REST, CLI) | Task 8 |
| 4 | Scientific Workspace | Task 7 |
| 3 | Workflow Planner (LLM-based) + Workflow Graph (DAG) | Task 4 |
| 2 | Scientific Registry + Execution Runtime | Tasks 3, 5 |
| 1 | Scientific Models (heterogeneous executors) | Tasks 2, 5 |

## 4.2 Walk-through example

User query:
> *"Design an oral tablet formulation for ibuprofen at 200 mg, then
> validate its pharmacokinetics."*

Step-by-step:

1. **Planner** (Layer 3) parses the query, consults the Workspace
   (Layer 4) for prior context, retrieves candidate tools from the
   Registry (Layer 2), and produces a Workflow DAG:

```
Literature          (literature_search)
       │
       ▼
PreformulationAI    (solubility_prediction)
       │
       ▼
FormulationAI       (excipient_design)
       │
       ▼
PBPK-AI             (pbpk_simulation)
       │
       ▼
FormulationDT       (dissolution_profile)
```

2. **Dependency Enforcer** validates the DAG (e.g., PBPK-AI's
   declared `upstream_capabilities_optional` includes `excipient_design` ✓).

3. **Runtime** (Layer 2) executes the DAG topologically:
   - Parallel branches where independent.
   - Cache results keyed by input hash.
   - Emit provenance records after each node.

4. **Artifact Generator** (cross-layer) produces:
   - `report.md` — Markdown summary
   - `data.json` — structured outputs
   - `dissolution.csv`, `pk.csv` — tabular data
   - `dissolution.png`, `pk_curve.png` — figures

5. **Workspace** (Layer 4) persists:
   - The Workflow DAG (replayable)
   - All artifacts (with provenance pointers)
   - The conversation turn

6. **User Interface** (Layer 5) renders:
   - Markdown report
   - DAG visualization
   - Artifact download links
   - Provenance panel

## 4.3 Heterogeneous executor backends

The Runtime supports six executor types:

| Type | Status | Use case |
|------|--------|----------|
| `python` | ✅ v0.1 | in-process Python function |
| `http` | 🚧 Task 5 | REST API |
| `cli` | 🚧 Task 5 | subprocess |
| `mcp` | 📋 future | Model Context Protocol server |
| `grpc` | 📋 future | gRPC service |
| `docker` | 📋 future | containerized tool |

A new executor type does not require changes to the Planner, Registry,
Workspace, or Artifact Generator.