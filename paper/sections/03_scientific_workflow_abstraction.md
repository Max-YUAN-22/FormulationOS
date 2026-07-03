# §3. Scientific Workflow Abstraction

> **Note.** The Workflow Abstraction defined in this section is conceptual and intended to be extensible. The current implementation uses a DAG-based execution model (see §3.2); future implementations may extend to graphs with branches, loops, and agent iterations without changing the abstraction surface. The separation between abstraction (stable contract) and representation (current or future internal model) is the central design point.

## 3.1 Definition

A **Scientific Workflow** is a first-class abstraction in FormulationOS
that unifies six properties under a single object:

| Property | Meaning |
|----------|---------|
| **Executable** | Can be invoked by the Execution Runtime to produce results. |
| **Persistent** | Can be stored in the Workspace and reloaded across sessions. |
| **Replayable** | Can be re-executed, either in full or incrementally. |
| **Refinable** | Can be modified (node args added / changed / removed) and re-run with affected nodes only. |
| **Provenance-aware** | Every execution produces a reproducible evidence chain. |
| **Artifact-centric** | Outputs are scientific artifacts (Markdown, JSON, CSV, figures, PDF), not chat replies. |

## 3.2 Internal representation

> In the **current implementation**, a Scientific Workflow is
> internally represented as a **directed acyclic execution graph**
> (DAG): nodes are tool invocations, edges are data dependencies.
>
> The abstraction is **independent of the representation**. Future
> implementations may represent Scientific Workflows as graphs with
> conditional branches, loops, agent iterations, or multi-turn
> refinement — without changing the abstraction surface.

This is the key separation: the abstraction is **what a Workflow
means**; the DAG is **how we currently implement it**.

## 3.3 Analogy to OS processes

| OS | FormulationOS |
|----|---------------|
| Process | Scientific Workflow |
| Process ID | workflow_id |
| Process state (running / ready / blocked) | workflow state (pending / running / completed / failed) |
| System call `fork` | workflow refinement |
| Filesystem | Scientific Workspace |
| Page table | Tool Registry cache |
| Scheduler | Scientific Dependency Enforcer |
| `kill -9` | workflow cancellation |
| `strace` | provenance record |

> If processes are the fundamental abstraction in Linux, then
> Scientific Workflows are the fundamental abstraction in FormulationOS.

## 3.4 Why a new abstraction (not "just a DAG")

Reviewer risk: *"Isn't a Scientific Workflow just a DAG?"*

**No.** A DAG is a data structure. A Scientific Workflow is a
**first-class operating-system object** with state, identity,
persistence, lifecycle, and a contract. The DAG is only the
**internal representation** of that object's execution plan.