# §5. Scientific Tool Specification (STS) — Extension Schema

> **TODO.** Finalize after Task 2 lands (✅ done). Expand after
> Tasks 3 (Registry) and 4 (Dependency Enforcer) land.

## 5.1 Position

STS is an **extension schema** over standard tool specifications such
as OpenAPI or MCP tool descriptors. It does **not** propose a new
protocol; it augments existing ones with scientific semantics.

This framing is deliberate. A reviewer asking "Why not MCP?" gets the
answer: STS is not in competition with MCP. A tool declared under STS
can be derived from, or wrapped around, an MCP tool descriptor or an
OpenAPI operation. The four extensions below are additive metadata
that turn a generic tool into a first-class scientific citizen.

## 5.2 Four scientific extensions

### Extension 1 — Scientific Semantics

```yaml
semantics:
  capabilities: [excipient_design, tablet, capsule]
  domain: formulation
```

Informal capability tags (not a formal taxonomy) + a single
high-level domain identifier.

### Extension 2 — Planning Hints

```yaml
planning_hints:
  examples:
    - input: {drug_name: Ibuprofen, target_dose_mg: 200, dosage_form: tablet}
      output_summary: Tablet with MCC/lactose/Mg-stearate, 200 mg
  keywords: [excipient, formulation, dosage form]
  notes: |
    Prefer this tool after PreformulationAI when BCS info is available.
```

Named `examples` rather than `few_shots` because the latter is a
specific prompting technique. STS treats examples as a general
category: few-shot demonstrations, retrieval exemplars, prompt
templates, DSL fragments — whatever the Planner chooses to consume.

### Extension 3 — Scientific Dependencies

```yaml
scientific_dependencies:
  upstream_capabilities_optional: [solubility_prediction, literature_search]
  upstream_capabilities_required: []
  rationale: |
    Solubility informs excipient selection.
```

Consulted by the Scientific Dependency Enforcer (Task 4) when
validating Workflow DAGs.

### Extension 4 — Provenance Specification

```yaml
provenance_spec:
  record_inputs: true
  record_outputs: true
  record_parameters: true
  record_compute_env: true
```

Declarative specification of **what** to record in the scientific
evidence chain. The Runtime consults this spec when emitting each
execution's provenance record.

## 5.3 Executor declaration

```yaml
executor:
  type: python        # python | http | cli | mcp | grpc | docker
  module: formulation_os.tools.builtins.formulation_ai.backend
  function: run
```

The executor is a Runtime concern, deliberately separated from the
Tool's metadata (Core). See §6.

## 5.4 Why "extension schema" not "new protocol"

| Risk | Mitigation |
|------|------------|
| "Why not MCP?" | STS augments MCP; it does not replace it. |
| "Why not OpenAPI?" | Same — STS augments OpenAPI's tool descriptors. |
| "Why invent a new protocol?" | We did not. We added scientific semantics to existing ones. |
| "How do I migrate my MCP tool?" | Wrap it: load MCP descriptor → fill in `semantics`, `planning_hints`, `scientific_dependencies`, `provenance_spec`. |