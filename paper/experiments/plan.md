# Evaluation Plan

Seven system evaluations. Naming follows the "Functional / Retrieval /
Efficiency / Usability / Provenance" pattern (more AI-Systems-paper
idiomatic than "System Experiment N").

## §7.1 Functional Evaluation

### 7.1.A Planner Accuracy

**Goal.** Measure how accurately the LLM-based Workflow Planner
(Task 4) translates natural-language queries into correct Workflow
DAGs.

**Setup.**
- N=50 natural-language queries spanning the 5 built-in tools.
- For each query, hand-author a golden DAG (node set + edges + per-node args).
- Run the Planner with each query, parse the produced DAG.
- Compare predicted DAG vs. golden DAG.

**Metrics.**
- **Exact-match rate** (graph isomorphism).
- **Node-level precision / recall / F1.**
- **Edge-level precision / recall / F1.**
- **Per-tool precision / recall.**

### 7.1.B Scientific Dependency Enforcer

**Goal.** Measure whether the Dependency Enforcer correctly rejects
DAGs that violate declared scientific dependencies.

**Setup.**
- N=100 synthetic DAGs, half with valid dependency structures, half
  with violations (missing required upstream capabilities, orphan
  nodes, cycles).
- Run the Enforcer; record accept/reject decisions.

**Metrics.**
- **Detection rate** (true positives).
- **False-positive rate** (valid DAGs wrongly rejected).
- **Latency** (DAG size → Enforcer time).

## §7.2 Retrieval Evaluation

**Goal.** Measure whether embedding-based tool retrieval outperforms
naive description-matching.

**Setup.**
- Build a relevance-judged dataset: for each of N=50 NL queries, mark
  which tools are relevant (1–3 of the 5).
- Generate tool cards (compact LLM-friendly descriptors).
- Embed cards + queries using a chosen embedding model (BGE-small,
  Qwen, etc.).
- Run retrieval: top-k candidates.

**Methods compared.**
- Embedding cosine similarity.
- LLM description-matching (Prompt: *"given this query, which tools
  apply?"*).
- Random baseline.

**Metrics.**
- **Top-k Recall** (k=1, 3, 5).
- **MRR** (Mean Reciprocal Rank).
- **nDCG@k**.

## §7.3 Efficiency Evaluation

### 7.3.A Replay Savings

**Goal.** Quantify the benefit of incremental re-execution after a
Workflow refinement.

**Setup.**
- Construct a 5-node Workflow.
- Modify one node's arguments; re-run.
- Measure wall-clock for (a) full re-run, (b) incremental (affected
  nodes only).

**Metrics.**
- **Speedup ratio.**
- **Affected-node count** vs. **total-node count.**

### 7.3.B Parallel Speedup

**Goal.** Quantify parallel-execution benefit.

**Setup.**
- Construct DAGs with varying degrees of parallelism (1, 2, 4 parallel branches).
- Run sequentially vs. in parallel.

**Metrics.**
- **Speedup ratio** (sequential_time / parallel_time).
- **Parallel efficiency** (speedup / branch_count).

## §7.4 Usability Evaluation

### 7.4.A Cross-Session Workspace Reuse

**Goal.** Measure how much user effort is saved by Workspace persistence.

**Setup.**
- N=5 task templates (e.g., "screen compound X", "compare two formulations").
- Have users execute each template twice in two sessions (with and
  without Workspace replay).

**Metrics.**
- **Number of user actions** (clicks / commands / API calls) per task.
- **Time to completion.**
- **Subjective preference** (post-task survey).

## §7.5 Provenance Evaluation

### 7.5.A Trace Completeness

**Goal.** Verify that all declared provenance fields are recorded.

**Setup.**
- For each execution with `provenance_spec` enabling inputs /
  outputs / parameters / compute_env, verify the corresponding
  fields exist in the provenance record.

**Metrics.**
- **Coverage** (% of declared fields actually recorded).
- **Accuracy** (hash matches content).

### 7.5.B Trace-Back Time

**Goal.** Measure how quickly a user can trace a final artifact back
to its inputs and tool versions.

**Setup.**
- N=20 final artifacts (one per executed workflow).
- For each, ask a user to identify the upstream tool version and
  input drug name. Time the lookup.

**Metrics.**
- **Mean trace-back time.**
- **Success rate** (% of artifacts correctly traced).

## Implementation schedule

| Eval | Depends on | Target milestone |
|------|-----------|------------------|
| 7.1.A | Task 4 (Planner) | After Planner lands |
| 7.1.B | Task 4 (Dependency Enforcer) | After Enforcer lands |
| 7.2 | Task 3 (Registry + retrieval) | After Registry lands |
| 7.3.A | Task 5 (Runtime + cache + DAG diff) | After Runtime lands |
| 7.3.B | Task 5 (Runtime + parallel) | After Runtime lands |
| 7.4.A | Task 7 (Workspace) | After Workspace lands |
| 7.5.A | Task 5 (Provenance record format) | After Runtime lands |
| 7.5.B | Task 8 (UI exposes provenance panel) | After UI lands |

## Datasets

- **NL queries:** Hand-authored, covering the 5 built-in tools.
- **Golden DAGs:** Hand-authored alongside queries.
- **Tool relevance judgments:** Hand-authored alongside queries.
- **Synthetic DAGs (7.1.B):** Programmatic generation.
- **Trace-back tasks (7.5.B):** Generated from real executions.