# FormulationOS

**A Scientific Operating System for Computational Pharmaceutics**

FormulationOS is an operating layer that orchestrates heterogeneous scientific AI models through natural language. It introduces the **Scientific Workflow Abstraction** — a first-class abstraction that unifies execution, persistence, replay, refinement, provenance, and artifacts under a unified operating layer. In the current implementation, Scientific Workflows are expressed as directed acyclic execution graphs (DAGs).

---

## Status

🚧 **v0.1 (in development)** — Architecture Frozen v1.0.

End-to-end MVP demo ready: Planner → Registry → Orchestrator → Report → Streamlit UI, with 5 built-in mock Tools and 117 passing tests.
See [`paper/outline.md`](paper/outline.md) for the paper outline.

---

## Quickstart

```bash
# Install in editable mode with dev + API + UI extras
pip install -e ".[all,dev]"

# Run all tests
pytest

# Run the end-to-end smoke test (Task 2.5)
pytest tests/smoke/test_end_to_end.py -v -s

# Launch the Streamlit UI (requires the [ui] extra)
pip install -e ".[ui]"
streamlit run src/formulation_os/ui/app.py
```

---

## Architecture (5 Layers)

| Layer | Component | Status |
|-------|-----------|--------|
| 5 | User Interface (Streamlit / REST API / CLI) | **Streamlit UI live** |
| 4 | Scientific Workspace (persistent state) | planned |
| 3 | Workflow Planner (LLM-based) + Workflow Graph (DAG) | **Rule-based Planner live** |
| 2 | Scientific Registry + Execution Runtime (with provenance) | **Registry + Orchestrator live** |
| 1 | Scientific Models (heterogeneous executors) | **5 mocks live** |

See [`paper/sections/04_formulationos_architecture.md`](paper/sections/04_formulationos_architecture.md).

---

## Scientific Tool Specification (STS)

Tools are declared via `tool.yaml` following the [STS v0.2 specification](docs/sts_specification.md).

STS is an **extension schema** over standard tool specifications (OpenAPI, MCP tool descriptors), adding four scientific extensions:

1. **Scientific Semantics** — informal capability annotations
2. **Planning Hints** — examples, keywords, notes for the Workflow Planner
3. **Scientific Dependencies** — cross-tool constraints
4. **Provenance Specification** — declarative trace requirements

To add a new tool, see [docs/tool_author_guide.md](docs/tool_author_guide.md).

---

## Built-in Mock Tools

| Tool | Capability | Domain |
|------|-----------|--------|
| `FormulationAI` | excipient design | formulation |
| `PreformulationAI` | solubility / permeability / stability prediction | preformulation |
| `PBPK-AI` | PK parameter estimation | pbpk |
| `FormulationDT` | dissolution profile / particle simulation | digital-twin |
| `Literature` | literature search | literature |

All five are mocks (`mock: true`) that return deterministic placeholder data with `warnings` fields clearly labeled.

---

## Paper

This project is being prepared as a submission to an AI Systems venue. See [`paper/`](paper/) for the working draft.

**Slogan:**
> *FormulationOS elevates Scientific Workflows to first-class citizens, enabling heterogeneous scientific foundation models to be executed, persisted, refined, replayed, and traced under a unified operating layer.*

**Anti-deterministic-models principle:**
> *FormulationOS does not promise deterministic models. It promises deterministic evidence.*

---

## License

MIT — see [LICENSE](LICENSE).