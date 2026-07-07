# Discussion — Defending FormulationOS Against Alternative Approaches

> This document is written from a reviewer's perspective. Each section poses a natural objection and provides our best response. No marketing.

## Q1: Why not just write Python to call the APIs?

**Objection:** "The platforms have web APIs (or can be scraped). Why don't scientists just write a Python script?"

**Response:**

- A Python script solves the *mechanical* integration, not the *scientific* integration. The scientist still manually decides which platforms to call, in which order, with which parameters, and how to interpret results.
- FormulationOS provides the **scientific dependency layer**: a workflow that uses a PBPK model must receive drug properties (LogS, pKa, etc.) from an upstream property predictor. This is enforced by the Workflow graph, not by the scientist remembering.
- FormulationOS provides **provenance** out of the box. A Python script produces no traceable evidence.
- FormulationOS provides **replay and refinement**. Change one node; the system knows which downstream nodes are affected. A Python script starts from scratch.
- FormulationOS provides a **shared registry**. New tools are added by writing one YAML file; the Planner and the runtime know about them automatically. A Python script is hardcoded to specific tools.

**Bottom line:** FormulationOS is a small layer of scientific infrastructure, not a replacement for code. The scientist still writes glue code for novel workflows; FormulationOS handles the well-trodden paths.

## Q2: Why call it an "OS" when it's not Linux?

**Objection:** "An OS manages processes, files, memory, devices. FormulationOS is a Python library. The 'OS' label is misleading."

**Response:**

- We use "OS" as a *metaphor for the operating layer*, not as a claim to be a kernel. The paper §3.3 explicitly draws the parallel: processes → Scientific Workflows, process ID → workflow_id, `fork` → workflow refinement, filesystem → Scientific Workspace, `strace` → provenance record.
- The metaphor is useful because it captures the *abstraction* we want: a layer that makes heterogeneous tools feel like first-class objects with state, identity, and lifecycle.
- The metaphor is not useful when taken too far. We are not building a kernel, scheduler, or filesystem. We are building a Scientific Operating Layer for a specific vertical.
- "Operating Layer" is the more accurate phrase; the paper title uses it.

**Bottom line:** The OS framing is a metaphor for the abstraction. Where the metaphor holds, it's powerful (first-class workflow objects, persistent state, provenance). Where it doesn't, we don't claim it (no kernel, no scheduler, no filesystem).

## Q3: Why a workflow abstraction when we have LangGraph / Airflow / Prefect?

**Objection:** "LangGraph has DAGs, Airflow has DAGs, Prefect has DAGs. Why yet another workflow abstraction?"

**Response:**

- General-purpose workflow systems (Airflow, Prefect) optimize for **data pipeline orchestration**: ETL jobs, scheduled tasks, container orchestration. They have no concept of scientific semantics.
- LangGraph has a *richer* execution model (cycles, conditional branches) but is designed for **agent conversations**: chat-style task completion. It does not capture scientific provenance or scientific-dependency enforcement.
- FormulationOS is specifically designed for **scientific workflows**: scientific-tool specification (STS v0.2) with 4 scientific extensions (capability annotations, planning hints, scientific dependencies, provenance spec), and a Workflow abstraction with 6 scientific properties (executable, persistent, replayable, refinable, provenance-aware, artifact-centric).
- The closest analog is **Galaxy** (scientific workflow system for genomics). Galaxy shows that scientific workflows are different from data pipelines: they have domain-specific tools, reproducibility requirements, and provenance capture.
- FormulationOS is a **domain-specialized** workflow system for scientific workflows, not a general-purpose one. It can be built on top of LangGraph, but the domain semantics are ours.

**Bottom line:** Workflow abstractions differ in *what* they orchestrate. Ours orchestrates scientific tools with domain-specific semantics. Galaxy did this for genomics; FormulationOS does it for computational pharmaceutics.

## Q4: Why not an Agent (AutoGen / OpenManus / Claude Code / OpenHands)?

**Objection:** "AutoGen has multi-agent conversation. OpenManus is a browser-use agent. Claude Code and OpenHands write code. Why not use them?"

**Response:**

- **AutoGen** is designed for multi-agent *conversation*; it does not produce reproducible scientific evidence chains. It is chat-first; we are evidence-first.
- **OpenManus** is a browser-use agent; it can interact with web platforms by clicking buttons. This is closer to the scraping approach we explicitly rejected (brittle, no ToS, reviewer concern).
- **Claude Code** is a coding assistant; it edits files. We are not editing files; we are running scientific models and collecting evidence.
- **OpenHands** is similar to Claude Code: software-engineering agent.
- **The fundamental difference:** agents optimize for *task completion* (often chat-style). FormulationOS optimizes for *reproducible scientific evidence*. The output of a FormulationOS workflow is not "Task done!" — it is a Markdown report with provenance metadata that an FDA reviewer could inspect.
- **Reproducibility:** an agent run is not reproducible by default (LLM outputs vary). A FormulationOS workflow run is reproducible: the same Workflow DAG, tool versions, and compute environment produce the same evidence chain (model outputs may differ, but the evidence is reproducible).

**Bottom line:** Agents and workflows solve different problems. Agents are appropriate when the task is "help me figure this out" (interactive). Workflows are appropriate when the task is "produce a reproducible scientific record" (regulatory).

## Q5: Why not just use MCP?

**Objection:** "Model Context Protocol (MCP) is the standard for tool discovery. Why build on top of it instead of using it directly?"

**Response:**

- MCP is a **protocol for tool discovery and invocation**, not a workflow orchestrator. We use MCP as a foundation, not as a competitor.
- STS v0.2 is **layered on top of MCP / OpenAPI**: we add 4 scientific extensions (capability annotations, planning hints, scientific dependencies, provenance spec). An STS tool can be generated from an MCP tool descriptor.
- The scientific value-add over MCP is the **scientific-dependency enforcement**: an MCP tool says "I take a SMILES and return a solubility"; an STS tool says "I take a SMILES and return a solubility, **and** I require no upstream capabilities" or "I depend on solubility_prediction (optional)".
- The Planner can use MCP tool discovery, but it uses **STS** to reason about scientific constraints. This is a domain-specific layer above MCP.

**Bottom line:** MCP is a substrate; FormulationOS is the scientific layer above it. We are not competing with MCP; we are using it.

## Q6: Why does pharmaceutics need a Scientific Workflow specifically?

**Objection:** "This could be done for materials, protein, climate, etc. Why focus on pharmaceutics?"

**Response:**

- **Pharmaceutics is a natural fit.** Drug R&D is intrinsically multi-stage (pre-formulation → formulation → testing → mechanism → in-vivo), each stage has dedicated models, and the workflow is a regulatory artifact.
- **Pharmaceutics has a real maturity bar.** Prof. Ouyang's lab has built 5+ production platforms with peer-reviewed publications, validated datasets, and regulatory relevance. This is the bar FormulationOS targets.
- **Pharmaceutics has regulatory reproducibility requirements.** FDA, EMA, and ICH increasingly require traceable evidence chains for drug approval. A Scientific Workflow abstraction directly supports this.
- **The architecture is domain-agnostic, but the validation must be in a specific domain.** We instantiate in pharmaceutics because the platforms are public, the maturity bar is concrete, and the regulatory relevance is real.
- **Cross-domain generalization is future work, not current work.** Future work may extend to materials, protein, climate. The architecture is designed for this (per `AGENTS.md` §3 system flexibility statement), but the validation is in pharmaceutics.

**Bottom line:** The architecture is general; the validation is specific. We instantiate in pharmaceutics because the maturity bar and regulatory relevance are real and reachable.

## Summary: Our Unique Position

| | FormulationOS provides | Competitor provides |
|---|---|---|
| **vs Raw Python** | Scientific dependency enforcement, provenance, replay, registry | Mechanical integration |
| **vs Linux/Windows OS** | First-class workflow objects, persistent state, lifecycle | Process, file, memory management |
| **vs Airflow/Prefect** | Scientific semantics, STS, scientific-dependency graph | Generic data-pipeline orchestration |
| **vs LangGraph** | Scientific provenance, artifact-centric output, reproducibility | Richer execution model (cycles), agent-style |
| **vs AutoGen** | Reproducible evidence, deterministic-evidence guarantee | Multi-agent conversation, chat-style |
| **vs OpenManus** | Programmatic integration, no browser automation | Browser-use automation |
| **vs Claude Code / OpenHands** | Scientific model invocation, evidence collection | Code editing |
| **vs MCP** | Scientific-dependency layer, planner-aware constraints | Tool discovery and invocation protocol |
| **vs Galaxy** | Domain-specialized for pharmaceutics; LLM-plannable | Domain-specialized for genomics |
| **vs New model** | Integration of existing models | Novel prediction algorithm |

The unique position: **FormulationOS is the Scientific Operating Layer for Computational Pharmaceutics — a domain-specialized workflow abstraction that composes existing scientific foundation models into reproducible, traceable, replanable scientific workflows.**

It is not a new model, not a chat agent, not a Linux replacement, not a competitor to MCP. It is a missing layer in the scientific computing stack.
