# Research Notes

Per [AGENTS.md §5](../../../AGENTS.md#5-paper-aware-development): every
non-trivial feature ships with a research note that answers the
**5-question reviewer checklist**. This directory collects them.

The 5 questions (from AGENTS.md §5):

1. **Contribution** — which sentence in `paper/sections/` does this support?
2. **Evaluation** — how do we verify it? Which test, which benchmark?
3. **Figure** — which figure slot (`paper/figures/figure_X_Y`) does it feed? If none, write *"no contribution yet."*
4. **Criticism** — what will an MLSys / AAAI reviewer pick at? Pre-empt in code or doc.
5. **Citation** — which existing work (MDCrow, ChemCrow, AI Scientist, Ouyang's platforms, …) does this relate to?

If questions **1 and 3 cannot be answered, do not ship.** Go back to
the paper, find where this feature belongs, or remove it.

## Index

| Note | Feature | Status | Paper § |
|---|---|---|---|
| [formulation_dt_adapter.md](formulation_dt_adapter.md) | FormulationDT Scientific Tool Adapter (Phase 2.1) | Pre-implementation — pending lab discussion | §4, §5, §6.5, §8.4 |
| [scientific_model_integration_matrix.md](scientific_model_integration_matrix.md) | 5-platform integration survey (Phase 2 strategy) | Pre-implementation — pending lab discussion | §8.4 |

## Related committed docs

These are the durable reference documents that research notes build on:

- [`docs/maturity/ouyang_platforms.md`](../maturity/ouyang_platforms.md) — Ouyang portfolio analysis (the maturity bar)
- [`docs/ouyang_platforms_summary.md`](../ouyang_platforms_summary.md) — scientific summary of the 5 platforms (inputs, outputs, models, limitations, integration paths)
- [`docs/sts_specification.md`](../sts_specification.md) — STS v0.2 schema (the contract adapters must satisfy)
- [`docs/system_design.md`](../system_design.md) — implementation strategy + Adapter pattern (§6.1 Option B)
- [`docs/research_plan.md`](../research_plan.md) — overall research direction