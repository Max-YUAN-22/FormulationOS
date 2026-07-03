# §6. Implementation

> **Note.** This section reflects the v0.1 implementation snapshot. It will evolve as the prototype grows beyond the initial release.

## 6.1 Code organization (5 packages)

```
src/formulation_os/
├── core/        # declarative: Tool, ToolSpec, ExecutorSpec
├── runtime/     # execution: Executor, PythonExecutor (Task 5: DAG runner + Provenance)
├── tools/       # wiring: loader + builtins/ (5 mock tools)
├── registry/    # Task 3: Scientific Registry + embedding-based retrieval
├── planner/     # Task 4: Workflow Planner (LLM) + DAG + Dependency Enforcer
├── workspace/   # Task 7: Scientific Workspace (persistent state)
├── api/         # Task 8: FastAPI
└── ui/          # Task 8: Streamlit
```

The split between `core/` (declarative) and `runtime/` (executive)
is deliberate: the Core has no runtime dependency on any executor
backend. This lets a Tool's metadata be inspected, validated, and
indexed without importing the executor.

## 6.2 Tool loading

```python
from formulation_os.tools import load_tool

tool = load_tool("src/formulation_os/tools/builtins/formulation_ai")
output = tool.execute({"drug_name": "Ibuprofen", "target_dose_mg": 200, "dosage_form": "tablet"})
```

`load_tool` reads `tool.yaml`, validates it against STS v0.2 (Pydantic),
constructs the appropriate `Executor`, and returns a wired `Tool`
instance.

## 6.3 Reproducible execution traces (v0.1)

We **do not** claim bit-identical model outputs. We **do** claim that
every execution emits a **deterministic evidence chain**:

```json
{
  "execution_id": "exec_2026_0630_001_n3",
  "workflow_id": "wf_2026_0630_001",
  "node_id": "n3",
  "tool": "FormulationAI",
  "tool_version": "0.1.0",
  "tool_spec_hash": "sha256:...",
  "input_hash": "sha256:...",
  "output_hash": "sha256:...",
  "executor_type": "python",
  "started_at": "2026-06-30T02:30:00Z",
  "finished_at": "2026-06-30T02:30:01.234Z",
  "duration_ms": 1234,
  "status": "success",
  "compute_env": {"python": "3.11.5", "platform": "darwin", "seed": 42}
}
```

Given the same Workflow DAG, tool versions, and compute environment,
re-executing the workflow produces the **same provenance trace**.
Model outputs may differ (LLMs are non-deterministic), but the
**scientific evidence chain** is reproducible.

> FormulationOS does not promise deterministic models.
> It promises **deterministic evidence**.

## 6.4 Smoke test (Task 2.5)

A minimal end-to-end test (`tests/smoke/test_end_to_end.py`) exercises
the lower layers today: query → load tool → execute → write artifact.
When higher layers arrive (Planner, Runtime, Artifact Generator),
this test evolves to exercise them too.

## 6.5 Built-in mock tools

| Tool | Capability | Domain | Backend |
|------|-----------|--------|---------|
| `FormulationAI` | excipient_design | formulation | mock recipe table |
| `PreformulationAI` | solubility_prediction | preformulation | hash-based BCS lookup |
| `PBPK-AI` | pbpk_simulation | pbpk | Weibull-derived parameters |
| `FormulationDT` | dissolution_profile | digital-twin | Weibull dissolution curve |
| `Literature` | literature_search | literature | synthetic paper generator |

All five are clearly marked `mock: true` and emit a `warnings`
field labeling outputs as `MOCK OUTPUT`.