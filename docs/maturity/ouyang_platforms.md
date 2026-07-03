# Prof. 欧阳德方 (Defang Ouyang) — Platform Portfolio

_A reference for FormulationOS's "mature platform" bar. Sources: computpharm.org front pages, Crossref API for paper metadata, direct curl where web_search/web_fetch timed out (2026-07-03)._

## The lab

**Computational Pharmaceutical Group**
- **PI:** Prof. Defang Ouyang (欧阳德方), University of Macau — `defangouyang@um.edu.mo`
- **Lead engineer:** Jie Dong (now Central South University, `jiedong@csu.edu.cn`)
- **Affiliation:** State Key Laboratory of Quality Research in Chinese Medicine, ICMS, University of Macau
- **Theme:** "computational pharmaceutics" — AI/ML for formulation, dissolution, drug-excipient interactions, molecular dynamics, PBPK

## The platform portfolio

All hosted under `*.computpharm.org`:

| Platform | URL | What it does | Paper |
|---|---|---|---|
| **FormulationAI** | https://formulationai.computpharm.org/ | Comprehensive in silico formulation design across **6 systems** (cyclodextrin, solid dispersion, phospholipid complex, nanocrystals, self-emulsifying, liposome) with **16 properties** | Briefings in Bioinformatics, 2023 (bbad419, **66+ citations**) |
| **PharmSD** | https://pharmsd.computpharm.org/ | Solid dispersion — dissolution type + rate (vs 26 polymers), physical stability (vs 25 polymers), F2 calculator, **application-domain analysis** | Int J Pharm, 2021 (120705) |
| **PharmDE** | https://pharmde.computpharm.org/ | Drug-excipient incompatibility — DB search (basic, similarity), risk prediction (drug, formulation) | Int J Pharm, 2021 (120962) |

Each platform is single-task, web-UI, real ML models. Plus supporting methodology papers (e.g., integrated ML + molecular modeling + PBPK for SD design, EJPB 2021). **PharmSD alone has 3+ supporting papers** — that's the multi-paper track-record pattern.

## Maturity characteristics (the bar to clear)

What every Ouyang platform has, that "demoable prototype" doesn't:

1. **Real ML models behind every prediction** — not mocks. Multiple algorithms compared systematically per property.
2. **Curated datasets** — "10 years of collected data" framing. Sources documented per dataset.
3. **Multi-paper support per platform** — main paper + methodology papers + property-specific papers. Each mature platform has 3+ publications.
4. **Task-focused web UI** — separate page per prediction type. Not a chat. Not a dashboard. Scientific-tool UI.
5. **Account system** — sign in / sign up. Manual verification.
6. **Application-Domain (AD) analysis** — first-class "is this prediction reliable for my input?" tool (PharmSD has it).
7. **Auxiliary scientific tools** — e.g., F2 calculator (regulatory similarity factor), AD analysis.
8. **Citation metadata baked into UI** — every page has a "Please cite" block listing the supporting papers.
9. **Documentation / Help pages** — separate from the prediction UI.
10. **Adoption tracking** — visit counter ("Visits from Nov 29, 2024").
11. **Clear license** — CC BY-NC-SA 4.0.
12. **Experimental validation** — paired experimental studies in supporting papers; benchmarks reported in main paper.

## What FormulationOS v0.1 has that Ouyang platforms don't

The differentiators:

| Dimension | Ouyang platforms | FormulationOS v0.1 |
|---|---|---|
| **Interface** | Web UI, fixed forms | Natural language → Orchestrator |
| **Composability** | One task per platform, fixed | Tool registry, planner picks the right tool |
| **Extensibility** | Closed (lab's own models) | Open — Tool abstraction, STS v0.2, YAML specs, anyone can add |
| **LLM integration** | None | MiniMax M3 opt-in planner (Task 7 ✅) |
| **Research workflow** | One prediction at a time | Multi-tool orchestration, structured Report, provenance hooks |
| **Planner** | None — fixed routing | Rule-based default, LLM opt-in |

## The maturity gap (what we don't have yet)

| Missing | Why it matters | Reference impl |
|---|---|---|
| Real models (Task 8) | Everything else is moot without predictions that work | Wrap FormulationAI as first external tool |
| Datasets / data layer | Models need data; no provenance without it | Document FormulationAI's published datasets |
| Validation suite | Can't claim "mature" without benchmark numbers | Reproduce one FormulationAI benchmark |
| Application-Domain analysis | Industry users always ask "is this reliable?" | Steal PharmSD's AD analysis pattern |
| Citation metadata in UI | Researchers reuse platforms that remind them to cite | Add `cite:` to ToolSpec, surface in Report |
| Multi-paper track record | 1 paper = 1 platform; 3 papers = credibility | Plan paper series: platform + 2+ property papers |
| Account / community | None yet | Out of scope for paper MVP, but plan for v1.0 |

## Positioning for the FormulationOS paper

The clean framing: **Ouyang-style platforms are vertical — one URL per problem. FormulationOS is horizontal — the NL orchestration layer that can wrap, extend, and route across many such tools.**

The minimum maturity bar to claim in the paper:
- At least one Ouyang-style platform wrapped as a FormulationOS tool
- Validation showing parity (or improvement) on at least one published benchmark
- Provenance + report that an end-user can hand to a regulatory reviewer

## What I'd borrow, immediately

If I had one engineering week:

1. **`cite:` field in ToolSpec** — surfaces in the Report footer. Researchers will cite us by reflex.
2. **Application-Domain tool stub** — interface only, in the mock-tools set, so the orchestrator pattern is in place for when a real AD model lands.
3. **Wrap FormulationAI's cyclodextrin model as our first external tool** — concrete validation target.
4. **Dataset descriptor in ToolSpec** — links to source data, dates, sample counts. Provenance foundation.

## Sources

- https://www.computpharm.org/ (lab home, partially under construction)
- https://formulationai.computpharm.org/ (scraped front page)
- https://pharmsd.computpharm.org/ (scraped front page)
- https://pharmde.computpharm.org/ (scraped front page)
- Crossref API: papers, abstracts, citation counts
- Search infrastructure (web_search / web_fetch) was timing out throughout — direct curl was the workaround