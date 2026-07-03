# Paper Outline (Target: ~8 pages main)

## 1. Introduction (1 page)

- Scientific Foundation Models are exploding — every lab has its own
  models, APIs, repos. No unified orchestration layer exists.
- Pharmaceutics is the example domain (FormulationAI, PreformulationAI,
  PBPK-AI, FormulationDT) but the problem is general.
- We propose **FormulationOS**, a Scientific Operating System.
- Contributions: five items, anchored on **Scientific Workflow Abstraction**.

## 2. Related Work (1 page)

- LLM-orchestrated scientific tools: MDCrow, ChemCrow, AI Scientist.
- Scientific foundation models in drug discovery.
- Scientific workflow systems: Airflow, Prefect, Kubeflow, Galaxy, Nextflow.
- Tool specifications: OpenAPI, MCP, ToolCards.
- Operating-system analogies in scientific computing.

## 3. Scientific Workflow Abstraction (~1 page) ★

- Definition: a first-class abstraction unifying execution, persistence,
  replay, refinement, provenance, and artifacts.
- Internal representation: in the current implementation, a directed
  acyclic execution graph (DAG). The abstraction is independent of
  representation — future implementations may support loops, agent
  iterations, or multi-turn refinement without changing the abstraction.
- Comparison with OS process abstraction.

## 4. FormulationOS Architecture (~2 pages)

- Five-layer architecture (Figure 1).
- Each layer's responsibility and interfaces.
- Walk-through example: end-to-end flow for "design ibuprofen tablet + PK".

## 5. Scientific Tool Specification (STS) (~1 page)

- Position: extension schema over OpenAPI/MCP.
- Four scientific extensions.
- Worked example: full `tool.yaml` for FormulationAI.

## 6. Implementation (~1 page)

- Code organization (5 packages).
- Tool loading and Executor wiring.
- Reproducible execution traces (no claim of bit-identical model outputs).

## 7. Evaluation (~1.5 pages)

Seven evaluations:
- 7.1 Functional Evaluation: Planner accuracy + Dependency Enforcer
- 7.2 Retrieval Evaluation: top-k Recall / MRR / nDCG@k
- 7.3 Efficiency Evaluation: Replay savings + Parallel speedup
- 7.4 Usability Evaluation: Workspace reuse across sessions
- 7.5 Provenance Evaluation: trace completeness and trace-back time

## 8. Discussion (~0.5 page)

- Current state (v0.1 prototype): Tool abstraction, Registry, Rule-based + LLM Planner, Orchestrator, Report, Streamlit UI, and 5 mock tools are live. Active exploration: real model integration, Scientific Workspace, evaluation suite, larger-registry validation.
- Future work: real model integration; cost-aware scheduling;
  automated capability induction; cross-domain generalization
  (materials, protein, climate).

## References

(~30 entries — MDCrow, ChemCrow, AI Scientist, OpenAI function calling,
Anthropic tool use, MCP, OpenAPI, Galaxy, Airflow, Nextflow, plus key
pharmaceutics / PBPK references.)