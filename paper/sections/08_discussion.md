# §8. Discussion

> **TODO.** Finalize after all evaluations complete.

## 8.1 What FormulationOS is

- An **operating layer**, not an LLM, not an agent, not a model.
- A **protocol extension**, not a new protocol.
- A **scientific workflow system**, not a generic data-pipeline orchestrator.

## 8.2 What FormulationOS is not

- Not a chatbot.
- Not a "PharmGPT" (we do not train a new model).
- Not a replacement for OpenAPI / MCP / Airflow / Galaxy. We extend and complement them.
- Not a deterministic-model system. We are a **deterministic-evidence** system.

## 8.3 Current state and prototype boundaries (v0.1)

The current prototype implementation provides:

- **Tool abstraction** — `Tool` ABC + STS v0.2 declarative schema + PythonExecutor.
- **Registry + Rule-based Planner** — token + capability matching, embedding-retrieval scaffolded.
- **LLM Planner** — opt-in via `LLM_PLANNER=1`. Supports MiniMax M3 (Anthropic-compatible) and OpenAI. Mock client for tests.
- **Orchestrator** — top-k tool execution, error-tolerant (status="partial" on tool failure).
- **Report generator** — dataclass + Markdown rendering, warnings surfaced.
- **Streamlit UI** — end-to-end demo, no API key required in rule-based mode.
- **5 built-in mock tools** — FormulationAI, PreformulationAI, PBPK-AI, FormulationDT, Literature. All clearly labeled `mock: true`.
- **151 tests passing**, end-to-end smoke test, 18 commits on `main`.

Areas under active exploration (prototype boundaries, not production-ready):

- **Mock tools.** The 5 built-in backends return deterministic placeholder data, clearly labeled in their output. Real model integration is the next major milestone (HTTP executor against `formulationai.computpharm.org` is the first target).
- **Small registry.** With 5 tools, retrieval is trivial. Scaling to 50–500 tools will require validation of embedding-based retrieval quality.
- **Scientific Workspace (Layer 4).** Persistence, replay, refinement, and provenance UI are prototype-stage features planned for a later phase.
- **Single-user, single-machine.** No multi-tenant Workspace, no distributed Runtime.

## 8.4 Future work

1. **Real model integration.** Wire the actual lab-internal FormulationAI / PreformulationAI / PBPK-AI / FormulationDT via their existing executor types.
2. **Larger registry.** Scale to 50–500 tools. Validate embedding retrieval quality at scale.
3. **Cost-aware scheduling.** Extend the Dependency Enforcer with cost metadata to optimize latency / cost / confidence.
4. **Automated capability induction.** Replace hand-curated `capabilities` with LLM-extracted tags from tool descriptions.
5. **Cross-domain generalization.** The FormulationOS architecture is domain-agnostic; instantiation for materials, protein, and climate workflows is planned.
6. **Multi-agent workflows.** Extend Scientific Workflows to support loops, agent iterations, and multi-turn refinement.
7. **Provenance as first-class research output.** Export provenance records as citable artifacts.

## 8.5 Closing

> FormulationOS elevates Scientific Workflows to first-class citizens,
> enabling heterogeneous scientific foundation models to be executed,
> persisted, refined, replayed, and traced under a unified operating
> layer.