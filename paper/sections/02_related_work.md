# §2. Related Work

> **TODO.** Write after Task 2 lands and we have read
> MDCrow, ChemCrow, AI Scientist, FormulationAI papers (Phase 2).

## Sketch

### LLM-orchestrated scientific tools

- **MDCrow** (2024) — agent for molecular dynamics; curated tools + LLM reasoning.
- **ChemCrow** (2024) — agent for chemistry; curated tools + safety checker.
- **AI Scientist** (Sakana, 2024) — automated paper generation; multi-agent loop.

**Contrast with FormulationOS:** all three hardcode tool selection
inside the LLM prompt. FormulationOS decouples retrieval (Registry),
planning (Planner), and execution (Runtime), and treats Scientific
Workflows as first-class persistent objects.

### Scientific workflow systems

- **Airflow**, **Prefect**, **Kubeflow** — generic data-pipeline orchestrators.
- **Galaxy**, **Nextflow** — bioinformatics-specific workflow managers.

**Contrast:** these target batch ETL or batch bioinformatics; they
have no notion of natural-language interface, scientific tool
specification, or provenance as a scientific evidence chain.

### Tool specifications and protocols

- **OpenAPI** — REST API description standard.
- **MCP** (Model Context Protocol) — Anthropic's tool-description format.
- **ToolCards** — flat descriptor used by some agent frameworks.

**Contrast:** STS is an **extension schema** over these standards,
not a replacement. It adds scientific semantics (capabilities,
dependencies, planning hints, provenance hooks) on top of any
underlying tool specification.

### Operating systems analogy

- **Linux processes** — first-class execution abstraction.
- **Plan 9 namespaces**, **BSD jails** — other OS-level abstractions.

**Contrast:** FormulationOS borrows the OS metaphor literally — a
Scientific Workflow is the process abstraction; the Workspace is the
filesystem; the Registry is the package catalog; the Runtime is the
scheduler.