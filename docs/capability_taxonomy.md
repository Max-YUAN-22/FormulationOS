# Scientific Semantics — Current Capabilities

> **Status:** v0.1. Informal capability tags (not a formal taxonomy).
> See [`sts_specification.md`](sts_specification.md#3-sts-extension-1--scientific-semantics).

The set of `capabilities` declared by built-in tools in v0.1.

## By domain

### formulation

| Capability | Tool |
|------------|------|
| `excipient_design` | `FormulationAI` |
| `tablet` | `FormulationAI` |
| `capsule` | `FormulationAI` |

### preformulation

| Capability | Tool |
|------------|------|
| `solubility_prediction` | `PreformulationAI` |
| `permeability` | `PreformulationAI` |
| `stability` | `PreformulationAI` |

### pbpk

| Capability | Tool |
|------------|------|
| `pbpk_simulation` | `PBPK-AI` |
| `parameter_estimation` | `PBPK-AI` |

### digital-twin

| Capability | Tool |
|------------|------|
| `dissolution_profile` | `FormulationDT` |
| `particle_simulation` | `FormulationDT` |

### literature

| Capability | Tool |
|------------|------|
| `literature_search` | `Literature` |
| `citation_retrieval` | `Literature` |

## Conventions

- Lower-case, snake-case identifiers.
- Plural-free, action-or-noun forms (e.g., `solubility_prediction`, not `solubility_predictions`).
- No hierarchical separators (`.`, `:`). Capabilities are flat tags.
- New capabilities should be added to this document when a new tool is registered.

## Cross-domain example

A workflow that touches multiple domains:

```
Literature          (literature_search)
       │
       ▼
PreformulationAI    (solubility_prediction)
       │
       ▼
FormulationAI       (excipient_design)
       │
       ▼
PBPK-AI             (parameter_estimation)
       │
       ▼
FormulationDT       (dissolution_profile)
```

Each node carries capabilities; the Scientific Dependency Enforcer uses them to validate the Workflow DAG.