# §7. Evaluation

> **Note.** This section describes the planned evaluation framework. Numbers will be populated as the 7 evaluations are run. The detailed methodology is in `paper/experiments/plan.md`.

## 7.1 Functional Evaluation (Planner accuracy + Dependency Enforcer)

- **Planner accuracy.** NL query → expected Workflow DAG (golden). Measure exact-match and node-level F1 across N queries.
- **Dependency Enforcer.** Construct N DAGs with known-good / known-bad dependency structures. Measure detection rate and false-positive rate.

## 7.2 Retrieval Evaluation (Registry / embedding quality)

- **Top-k Recall, MRR, nDCG@k.** Build a relevance-judged set: for each NL query, mark which tools are relevant. Compare embedding-based retrieval vs. description-matching vs. random.

## 7.3 Efficiency Evaluation (Replay + Parallel)

- **Replay.** Modify a single node in a Workflow; measure wall-clock time to re-execute and verify only affected nodes ran.
- **Parallel.** Construct a Workflow with parallel branches; measure wall-clock vs. sequential execution.

## 7.4 Usability Evaluation (Workspace reuse)

- **Cross-session reuse.** Define N task templates. Measure user actions to re-run a similar workflow (manual vs. Workspace-replay).

## 7.5 Provenance Evaluation

- **Trace completeness.** For each execution, verify that all four
  declared provenance fields (inputs, outputs, parameters,
  compute_env) are recorded when enabled.
- **Trace-back time.** User is given a final artifact and asked to
  find the input that produced it. Measure wall-clock.

(See `paper/experiments/plan.md` for detailed methodology.)