# PreformulationAI (Mock)

A mock implementation of a preformulation property predictor.

**Status:** Mock. Returns deterministic placeholder BCS / solubility values. Replace with a real predictor (e.g., a graph neural network trained on ChEMBL / Tox21) when wiring real models.

## When to use

- Early-stage compound screening
- BCS class assignment for an API
- Solubility / logP / permeability estimation

## Mock behavior

The mock returns values derived deterministically from a hash of the `drug_name` string — i.e., the same name always yields the same numbers. This is a property useful for testing:

- `Ibuprofen` → solubility ~21 mg/mL, logP ~3.5, BCS II
- `Acetaminophen` → solubility ~14 mg/mL, logP ~0.5, BCS III

All outputs include `warnings: ["MOCK OUTPUT"]`.

## Outputs

| Field | Meaning |
|-------|---------|
| `solubility_mg_ml` | Aqueous solubility (pH 6.8) |
| `logp` | Calculated logP |
| `permeability_cm_s` | Apparent permeability |
| `bcs_class` | Biopharmaceutics Classification (I–IV) |
| `stability_ph` | pH-dependent stability profile |