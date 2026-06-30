# FormulationAI (Mock)

A mock implementation of an excipient-design model.

**Status:** Mock. Returns deterministic placeholder recipes. Replace with the real FormulationAI when wiring real scientific models.

## When to use

- User wants to design or optimize a drug formulation
- User asks "what excipients should I use for X at Y mg?"

## When NOT to use

- PK/PD questions → use `PBPK-AI`
- Literature review → use `Literature`
- Solubility / permeability prediction → use `PreformulationAI`

## Mock behavior

Returns a canned recipe based on `dosage_form`:

| dosage_form | Excipients (mock) |
|-------------|-------------------|
| tablet | MCC (60%) + lactose monohydrate (30.5%) + Mg-stearate (1%) |
| capsule | Mannitol (70%) + croscarmellose (5%) |
| injection | Water for injection (qs 100%) |
| cream | Petrolatum + glycerin |
| patch | EVA + isopropyl myristate |

All outputs include a `warnings: ["MOCK OUTPUT"]` field.

## Replacing with a real model

1. Update `backend.py` to call the real model (or change `executor` to `http` and point at a deployed endpoint).
2. Flip `mock: false`.
3. Bump `version`.
4. Update `cost.confidence` to `validated` once benchmarked.