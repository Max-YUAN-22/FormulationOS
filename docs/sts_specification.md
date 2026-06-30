# Scientific Tool Specification (STS) — v0.2

> **Status:** Stable for v0.1. Implementation lives in
> [`src/formulation_os/core/tool.py`](../src/formulation_os/core/tool.py).

## 1. Position

STS is an **extension schema** over standard tool specifications such as OpenAPI or MCP tool descriptors. It does **not** replace them — a tool declared under STS can be generated from, or wrapped around, an OpenAPI operation or an MCP tool descriptor. The four scientific extensions below are additive metadata that turn a generic tool into a first-class citizen of a scientific workflow.

This framing is deliberate. We do not invent a new protocol; we extend existing tool specifications with scientific semantics.

## 2. Top-level fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | ✓ | Unique tool identifier (e.g. `FormulationAI`). |
| `version` | string |  | Semver; defaults to `0.1.0`. |
| `owner` | string |  | Owning lab / team / org. |
| `description` | string | ✓ | Natural-language description. The Registry uses this for LLM tool selection prompts. |
| `semantics` | object |  | **STS Extension 1.** Informal scientific semantics. |
| `input_schema` | object |  | JSON Schema for the input dict. |
| `output_schema` | object |  | JSON Schema for the output dict. |
| `planning_hints` | object |  | **STS Extension 2.** Hints for the Workflow Planner. |
| `scientific_dependencies` | object |  | **STS Extension 3.** Cross-tool constraints. |
| `executor` | object | ✓ | Executor declaration. |
| `provenance_spec` | object |  | **STS Extension 4.** What to record in the evidence chain. |
| `cost` | object |  | Optional latency/cost/confidence metadata. |
| `mock` | bool |  | Flag indicating a placeholder. Defaults to `false`. |

Unknown top-level fields are rejected (Pydantic `extra="forbid"`). This is a deliberate constraint: a tool that declares fields outside the STS schema cannot be guaranteed to interoperate.

## 3. STS Extension 1 — Scientific Semantics

```yaml
semantics:
  capabilities:
    - excipient_design
    - tablet
    - capsule
  domain: formulation
```

`capabilities` is a flat list of informal tags, **not** a formal ontology or taxonomy. The Registry embeds these tags alongside the description for vector-based retrieval. `domain` is a single high-level identifier (e.g., `pharmaceutics`, `materials`, `protein`).

## 4. STS Extension 2 — Planning Hints

```yaml
planning_hints:
  examples:
    - input: {drug_name: Ibuprofen, target_dose_mg: 200, dosage_form: tablet}
      output_summary: Tablet with MCC/lactose/Mg-stearate, 200 mg API load
  keywords:
    - excipient
    - formulation
  notes: |
    Prefer this tool after PreformulationAI when BCS info is available.
```

The field is named `examples` rather than `few_shots` because the latter is a specific prompting technique. STS treats examples as a general category that can hold few-shot demonstrations, retrieval exemplars, prompt templates, or DSL fragments — whatever the Workflow Planner (Task 4) chooses to consume.

## 5. STS Extension 3 — Scientific Dependencies

```yaml
scientific_dependencies:
  upstream_capabilities_optional:
    - solubility_prediction
    - literature_search
  upstream_capabilities_required: []
  rationale: |
    Solubility (from PreformulationAI) informs excipient selection.
```

The Workflow Planner and Scientific Dependency Enforcer consult these fields when constructing and validating a Workflow DAG:

- `upstream_capabilities_required` — hard constraints; a Workflow that does not produce these capabilities upstream will be rejected.
- `upstream_capabilities_optional` — soft constraints; the Planner is encouraged to satisfy them but may proceed without.

## 6. Executor declaration

```yaml
executor:
  type: python        # python | http | cli | mcp | grpc | docker
  module: formulation_os.tools.builtins.formulation_ai.backend
  function: run
```

Six executor types are reserved. Only `python` is implemented in v0.1; the other five are interface-defined and arrive in later tasks.

| Type | Required fields | Status |
|------|-----------------|--------|
| `python` | `module`, `function` | ✅ v0.1 |
| `http` | `url`, optional `method`, `headers` | 🚧 Task 5 |
| `cli` | `command`, optional `args` | 🚧 Task 5 |
| `mcp` | `command` (server launch) or `url` (remote) | 🚧 Future |
| `grpc` | `url` | 🚧 Future |
| `docker` | `command` (image), optional `args` | 🚧 Future |

The executor lives in `src/formulation_os/runtime/executor.py`; it is deliberately separate from the Core (`core/tool.py`) so that the Tool abstraction has no runtime dependency on any specific execution backend.

## 7. STS Extension 4 — Provenance Specification

```yaml
provenance_spec:
  record_inputs: true
  record_outputs: true
  record_parameters: true
  record_compute_env: true
```

These booleans declare **what** the Execution Runtime should record in the scientific evidence chain for every execution. The Runtime (Task 5) emits a `ProvenanceRecord` (defined in `paper/sections/06_implementation.md`) that captures, at minimum, the tool name and version, input hash, output hash, executor type, start/finish timestamps, and (when enabled) the compute environment.

> *FormulationOS does not promise deterministic models. It promises deterministic evidence.*

## 8. Cost metadata

```yaml
cost:
  latency_class: low        # low | medium | high
  cost_class: low
  confidence: experimental # experimental | validated | production
```

Cost metadata is **informational** in v0.1. It is exposed via `tool.cost` for downstream consumers and will be consumed by a future cost-aware scheduler. The v0.1 scheduling policy is the **Scientific Dependency Enforcer** (Task 4), which validates DAG correctness rather than optimizing for cost.

## 9. Validation

```python
from formulation_os.core.tool import ToolSpec, ToolSpecValidationError
import yaml

raw = yaml.safe_load(open("tool.yaml"))
try:
    spec = ToolSpec.model_validate(raw)
except Exception as e:
    raise ToolSpecValidationError(str(e))
```

STS validation is implemented by Pydantic and enforced at load time by `formulation_os.tools.loader.load_tool`.

## 10. Versioning

STS follows semantic versioning. The current implementation is **v0.2**.

| Version | Status | Notes |
|---------|--------|-------|
| 0.1.x | Superseded | Initial draft with `few_shots`. |
| **0.2.x** | **Current** | Renamed `few_shots` → `examples`. Stable for v0.1. |
| 0.3.x | Planned | Tool versioning, dependency graph first-class. |

Breaking changes increment the major version. Additive changes increment the minor version.