# PBPK-AI (Mock)

A mock implementation of a physiologically-based pharmacokinetic model.

**Status:** Mock. Returns deterministic placeholder PK parameters. Replace with a real PBPK model (e.g., a population-PBPK simulator or a published compartmental model) when wiring real models.

## When to use

- User asks about PK / PD predictions
- Validating a proposed formulation against therapeutic PK targets
- Comparing routes of administration

## Mock behavior

PK parameters are deterministically derived from `drug_name` + `dose_mg` (same input → same output). Confidence is always 0.42 to make it clear that this is mock data.

## Outputs

| Field | Meaning |
|-------|---------|
| `cmax_ng_ml` | Peak plasma concentration |
| `auc_ng_h_ml` | Area under the curve |
| `t_half_h` | Elimination half-life |
| `clearance_L_h` | Total body clearance |
| `vd_L` | Volume of distribution |
| `confidence` | Self-reported confidence (always 0.42 for mock) |