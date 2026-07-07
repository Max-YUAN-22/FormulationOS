# Discussion Checklist — Pre-Meeting Prep

> Use this as a 30-min meeting agenda with 师兄. Keep to 2 pages; concrete and decision-oriented.

## Where We Are Now (v0.1 → v0.2)

- ✅ v0.1 MVP: 5 mock tools, 151 tests, 18 commits, GitHub live
- ✅ Architecture frozen (5 layers, 11 packages)
- ✅ STS v0.2 stable; Planner pluggable (RuleBased + LLM)
- ✅ Report generator; Streamlit UI; LLM planner (MiniMax M3 / OpenAI)
- ✅ Documentation aligned: flexibility statement, prototype framing
- ✅ AGENTS.md + paper sections updated
- 🔄 Pending: real tool integration (Phase 2)
- 🔄 Pending: Research proposal (this document)

## Biggest Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Reviewer: "just a DAG with provenance" | Medium | High | 6-property definition; abstraction-vs-representation separation |
| Ouyang lab doesn't give internal access | Medium | Medium | Web-form wrapping fallback; Zenodo data for MM |
| AI-PBPK supplementary has only equations, not code | High | Low | Deprioritize AI-PBPK; focus on FormulationDT (MIT) first |
| LLM planner is commodity (no novelty) | Medium | Medium | Pair with tool retrieval + scientific-dependency enforcement |
| 5 platforms not enough to claim "real integration" | Medium | Medium | Phase 2 = 3 real + 2 mock; clear paper claim |

## Biggest Innovations

- **Workflow as first-class object** (analogous to OS processes) with 6 properties
- **Scientific Tool Specification (STS) v0.2** — extension schema over OpenAPI/MCP with 4 scientific extensions
- **Deterministic-evidence guarantee** (not deterministic-model)
- **Domain-specialized** for pharmaceutics; architecture domain-agnostic
- **5 real platforms** as integration targets (unprecedented in workflow-OS literature)
- **PBPK + formulation + molecular dynamics** all in one workflow (cross-scale integration)

## Routes Available

| Route | Description | Paper Claim |
|---|---|---|
| A. Workflow OS (most stable) | Systems paper; architecture + design | "Scientific Operating Layer for Computational Pharmaceutics" |
| B. LLM Planning (medium risk) | Agent + planning + tool retrieval | "LLM Planning for Pharmaceutical Foundation Models" |
| C. Learning Workflow (high risk) | Meta-learning over provenance traces | "Cost-Aware Workflow Optimization" |
| D. Cross-Domain (long term) | Apply architecture to materials, protein, climate | "Domain-Agnostic Scientific Workflow OS" |

**Recommended path:** Start with A, fold in B as a section, defer C to v2.

## Decisions Needed from 师兄

1. **Internal access to FormulationAI / PreformulationAI / FormulationMM** — does the lab have inference scripts, APIs, or docker images? (vs web-form-only)
2. **AI-PBPK access** — is there a group account, or do we use the Streamlit app account-by-account?
3. **Authorship / collaboration** — if we publish integration, do we (a) cite + acknowledge, (b) co-author, (c) contribute code upstream?
4. **Paper target venue** — MLSys, AAAI, ICLR, KDD, or specialty (e.g., J Control Release)?
5. **Co-authorship scope** — who is on the paper? Just Max, or include the Ouyang group?

## Technical Choices to Make

| Choice | Options | Default | When to revisit |
|---|---|---|---|
| Workflow representation | DAG (current) | DAG | When we need cycles / agent iteration |
| Planner default | RuleBased | RuleBased | When real tool integration needs LLM |
| Provenance format | JSON, Parquet, custom | JSON | When storage scale matters |
| LLM planner | MiniMax M3, OpenAI, Anthropic | MiniMax M3 | If LLM quality gap appears |
| Tool integration | Adapter pattern | Adapter | When 3rd-party API changes |
| Scientific deps | Optional vs required | Both | When planner accuracy suffers |

## What's Worth Continuing

- Workflow as first-class object (core abstraction; do not abandon)
- STS v0.2 (clean, stable; iterate on extensions as needed)
- LLM planner (complement to RuleBased; opt-in)
- Adapter pattern for tool integration (3rd-party friendly)
- Mock tools as the substrate for v0.1 (cheap to develop, easy to swap)

## What's Worth Dropping (or Deferring)

- **Web scrapers** for Ouyang's platforms (brittle; ask for internal access instead)
- **Direct vendor** of 3rd-party code (use adapter pattern; respect upstream license)
- **AI-PBPK reimplementation** until we have proof the supplementary has working code
- **Caching / incremental re-execution** (premature optimization; build when needed)
- **Multi-tenant Workspace** (out of scope for v1.0)

## What's Worth a Paper

- **Workflow OS** (Direction 1) — the architecture + 5-platform integration
- **LLM Planning** (Direction 2) — if we beat general-purpose agents on real R&D queries
- **Application-domain analysis** — borrowing PharmSD's pattern
- **PBPK integration** — the cross-scale story (molecular → tissue → whole body)

## What's Just Engineering (not paper-worthy)

- HTTP executor for public web platforms
- Streamlit UI iteration
- pytest infrastructure
- Lint / type checking
- Documentation polish

## Concrete Next Steps (post-meeting)

1. Discuss and get answers to 5 decisions above
2. Write the v0.2 milestone plan based on answers
3. Pick paper target venue
4. Begin real tool integration (Phase 2)
5. Write a draft Abstract based on chosen direction

## Risk-Weighted Timeline

| Path | Timeline | Risk |
|---|---|---|
| Workflow OS paper (A) | 3-4 months | Low (architecture work, not research) |
| + LLM planning (B) section | 4-6 months | Medium (empirical work) |
| + Cross-domain demo | 6-9 months | Medium (cross-domain expertise) |
| + Learning workflow (C) | 12+ months | High (research-heavy) |
