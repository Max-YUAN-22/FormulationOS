# FormulationOS

**A Scientific Operating System for Computational Pharmaceutics**

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-151%20passing-brightgreen)](#development)
[![Status](https://img.shields.io/badge/status-v0.1%20MVP-yellow)](#status)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

FormulationOS is an operating layer that orchestrates heterogeneous
scientific AI models through natural language. It introduces the
**Scientific Workflow Abstraction** — a first-class abstraction that
unifies execution, persistence, replay, refinement, provenance, and
artifacts under a unified operating layer. In the current
implementation, Scientific Workflows are expressed as directed acyclic
execution graphs (DAGs).

See the [architecture diagram](docs/architecture.md) for the one-page
overview of the 5-layer stack and the query data flow.

> **FormulationOS is designed as an evolving scientific operating
> layer.** Its abstractions (Scientific Workflow, Tool, Executor) are
> intentionally underspecified to support future scientific workflows,
> tool types, and execution backends. The current implementation uses
> a DAG-based Workflow; future implementations may extend to graphs
> with branches, loops, and agent iterations without changing the
> abstraction surface.

---

## Status

🚧 **v0.1 MVP — initial prototype, abstractions designed for extensibility.** End-to-end demo is wired:
Planner → Registry → Orchestrator → Report → Streamlit UI, with 5
built-in mock Tools and 151 passing tests. See the [roadmap
section](#roadmap) for what's next.

---

## Quickstart

Three steps. No API key required for the rule-based demo.

### 1. Install

```bash
git clone <repo-url> FormulationOS
cd FormulationOS
make install          # pip install -e ".[all,dev]"
```

Or with plain `pip` if you don't have `make`:

```bash
pip install -e ".[all,dev]"
```

`make install` pulls in the dev tools (pytest, mypy, ruff), the UI
(Streamlit), and the LLM SDKs (openai, anthropic). If you only need a
subset:

```bash
pip install -e ".[dev]"    # tests + lint, no UI, no LLM SDKs
pip install -e ".[ui]"     # add Streamlit
pip install -e ".[llm]"    # add openai + anthropic SDKs
```

### 2. Run the tests

```bash
make test              # 151 tests, ~2 seconds
```

### 3. Launch the UI

```bash
make run-ui            # rule-based planner, no key required
# → opens http://localhost:8501 in your browser
```

You'll see a query input pre-filled with an example. Click **Run ▶**
and the planner picks a tool, the tool executes, and the rendered
Report appears below.

**With the LLM planner** (MiniMax M3 by default):

```bash
export MINIMAX_API_KEY=sk-...          # or ANTHROPIC_API_KEY
make run-ui-llm
# same UI, but routing is now done by the LLM
```

To stop the server: `Ctrl-C`.

---

## What you'll see

The Streamlit UI has two panels:

- **Sidebar** — a list of the 5 built-in tools (Literature,
  FormulationAI, PreformulationAI, PBPK-AI, FormulationDT) with each
  tool's description, domain, and capabilities. Acts as a live check
  that the registry loaded.
- **Main panel** — a query input (with example queries as defaults)
  and a Run button. After clicking Run, the chosen tool's result
  appears as a card (status, duration, input/output JSON, warnings),
  with the raw Markdown Report in a collapsed expander below.

Example queries that route cleanly with the rule-based planner:

| Query | Routes to |
|-------|-----------|
| `Find recent literature review on solubility` | Literature |
| `I want to formulate ibuprofen as a tablet` | FormulationAI |
| `What is the bioavailability of caffeine?` | PBPK-AI |
| `Predict solubility of naproxen` | PreformulationAI |

---

## Architecture (5 layers)

| Layer | Component | Status |
|-------|-----------|--------|
| 5 | User Interface (Streamlit / REST API / CLI) | **Streamlit UI live** |
| 4 | Scientific Workspace (persistent state) | planned |
| 3 | Workflow Planner + Workflow Graph (DAG) | **Rule-based + LLM live** |
| 2 | Scientific Registry + Execution Runtime | **Registry + Orchestrator live** |
| 1 | Scientific Models (heterogeneous executors) | **5 mocks live** |

See [`docs/architecture.md`](docs/architecture.md) for the full
diagram, or [`paper/sections/04_formulationos_architecture.md`](paper/sections/04_formulationos_architecture.md)
for the design rationale.

---

## Scientific Tool Specification (STS)

Tools are declared via `tool.yaml` following the
[STS v0.2 specification](docs/sts_specification.md).

STS is an **extension schema** over standard tool specifications
(OpenAPI, MCP tool descriptors), adding four scientific extensions:

1. **Scientific Semantics** — informal capability annotations
2. **Planning Hints** — examples, keywords, notes for the Workflow Planner
3. **Scientific Dependencies** — cross-tool constraints
4. **Provenance Specification** — declarative trace requirements

To add a new tool, see
[`docs/tool_author_guide.md`](docs/tool_author_guide.md).

---

## Built-in Mock Tools

| Tool | Capability | Domain |
|------|-----------|--------|
| `FormulationAI` | excipient design | formulation |
| `PreformulationAI` | solubility / permeability / stability prediction | preformulation |
| `PBPK-AI` | PK parameter estimation | pbpk |
| `FormulationDT` | dissolution profile / particle simulation | digital-twin |
| `Literature` | literature search | literature |

All five are mocks (`mock: true`) that return deterministic placeholder
data with `warnings` fields clearly labeled. See Task 8 for real
model integration.

---

## Development

```bash
make install    # editable install with [all,dev]
make test       # full pytest run
make lint       # ruff + mypy
make run-ui     # Streamlit (rule-based)
make run-ui-llm # Streamlit (LLM; needs MINIMAX_API_KEY or ANTHROPIC_API_KEY)
make clean      # remove caches and build artifacts
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the dev setup, code
style, commit-message convention, and how to add a new Tool or
Planner.

---

## Roadmap

Phase 1 (this MVP) is complete. Phase 2 work:

- **Task 8: Real model integration.** Replace the 5 mock backends with
  real PK/PD/Formulation/DT solvers. Model selection, license
  management, benchmark validation.
- **Scientific Workspace (Layer 4).** Persistent state, replay,
  refinement, provenance panel.
- **Provenance record format.** Structured scientific evidence chain
  for every execution.
- **HTTP / CLI / MCP / gRPC Executors.** Today only `python`
  executors are supported; the other five types from STS v0.2 are
  planned.
- **Embedding-based retriever.** Vector index over
  `Tool.to_card()` for sub-millisecond semantic tool retrieval.

---

## Paper

This project is being prepared as a submission to an AI Systems venue.
See [`paper/`](paper/) for the working draft.

**Slogan:**
> *FormulationOS elevates Scientific Workflows to first-class citizens, enabling heterogeneous scientific foundation models to be executed, persisted, refined, replayed, and traced under a unified operating layer.*

**Anti-deterministic-models principle:**
> *FormulationOS does not promise deterministic models. It promises deterministic evidence.*

---

## License

MIT — see [LICENSE](LICENSE).
