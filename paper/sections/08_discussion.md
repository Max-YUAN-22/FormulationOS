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

## 8.3 Limitations (v0.1)

- **Mocks only.** All five tools return deterministic placeholder data. Real model integration is the next milestone.
- **Small registry.** With 5 tools, retrieval is trivial. We have not yet validated scaling to 50–500 tools (planned).
- **LLM planner not yet integrated.** v0.1 has tool abstraction + loading only. The Planner (Task 4) will use an LLM with structured output.
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