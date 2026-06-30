# FormulationDT (Mock)

A mock implementation of a formulation digital twin.

**Status:** Mock. Returns deterministic dissolution curves following a Weibull-like profile, parameterized by a hash of `drug_name`. Replace with a real population-PBPK + particle simulation when wiring real models.

## When to use

- In-silico dissolution prediction
- Comparing formulation prototypes
- Particle-engineering questions

## Mock behavior

Dissolution follows a Weibull-like curve where the time-to-50%-dissolved (T50) is deterministically derived from the drug name. The curve is sampled at 0, 5, 10, 15, 30, 45, 60, 90, 120 minutes (or up to `duration_min`).

## Outputs

| Field | Meaning |
|-------|---------|
| `dissolution_curve` | List of `(t_min, pct_dissolved)` points |
| `f2_similarity` | Mock f2 value against a hypothetical reference |
| `medium` | The dissolution medium used |