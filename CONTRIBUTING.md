# Contributing to FormulationOS

Thanks for your interest in FormulationOS. This guide covers the basics
of getting a development environment running, running the tests, and
submitting changes. For the high-level design, see
[`README.md`](README.md) and the paper draft under [`paper/`](paper/).

---

## Development setup

FormulationOS targets Python 3.11+ and uses [Hatch](https://hatch.pypa.io/)
as the build backend. The fastest way to get going:

```bash
git clone <your-fork-url>
cd FormulationOS
make install        # pip install -e ".[all,dev]"
```

`make install` pulls in the `[all,dev]` extras, which include pytest, ruff,
mypy, FastAPI, Streamlit, and the LLM SDKs (openai + anthropic). If you
only need a subset:

```bash
pip install -e ".[dev]"     # just the dev tools (tests, lint)
pip install -e ".[ui]"      # add Streamlit
pip install -e ".[llm]"     # add LLM client SDKs
```

---

## Running the tests

```bash
make test           # full suite, quiet output
pytest -v           # full suite, verbose
pytest tests/test_orchestrator  # one directory
```

The suite has **151 tests** as of Task 7 and takes well under two seconds
to run. No network access is required — LLM clients are exercised with
`MockLLMClient`.

---

## Code style

We use:

- **[ruff](https://docs.astral.sh/ruff/)** for linting and import sorting.
  Configured in `pyproject.toml`. Run with `ruff check src tests`.
- **[mypy](https://mypy-lang.org/)** in strict mode (`pyproject.toml`'s
  `[tool.mypy]` section). Run with `mypy src`.
- **Type hints everywhere** on public APIs. New modules should start
  with `from __future__ import annotations`.

```bash
make lint           # run both
```

---

## Commit messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/).
The format is:

```
<type>(<scope>): <short summary>

<body explaining the change, motivation, and any trade-offs>
```

Common types:

- `feat` — new user-facing capability
- `fix` — bug fix
- `refactor` — code change that neither fixes a bug nor adds a feature
- `test` — adding or fixing tests
- `docs` — documentation only
- `chore` — tooling, dependencies, repo hygiene

Common scopes (matching the package layout): `core`, `tools`, `registry`,
`planner`, `orchestrator`, `report`, `ui`, `llm`, `runtime`, `paper`,
`docs`.

Examples from the history:

```
feat(orchestrator): add Orchestrator wiring Planner → Tool execution → Report
feat(report): extract Report into its own module (Task 5)
feat(ui): add Streamlit UI for FormulationOS (Task 6)
feat(llm): add LLM-based Planner with MiniMax + OpenAI clients (Task 7)
test(planner): exercise literature_review keyword in literature test
```

Keep the summary line under ~72 characters. Use the body to explain
*why* the change was made and any design trade-offs, especially for
non-obvious refactors.

---

## Project layout

```
src/formulation_os/
    core/         # Tool abstraction, ToolSpec, ExecutorSpec
    runtime/      # Executor ABC + PythonExecutor
    tools/        # Loader + builtin mock tools
    registry/     # ToolRegistry
    planner/      # Planner ABC + RuleBasedPlanner + LLMPlanner
    orchestrator/ # Planner → Tool execution → Report
    report/       # Report + ToolResult data model + Markdown rendering
    llm/          # LLMClient ABC + OpenAIClient + MiniMaxClient + MockLLMClient
    ui/           # Streamlit app (single page)
    workspace/    # (planned) persistent state
    api/          # (planned) FastAPI
```

When adding a new layer, mirror the existing package conventions: a
package directory, a `__init__.py` that re-exports the public surface,
implementation in a single module, and a parallel `tests/test_<layer>/`
directory.

---

## Adding a new Tool

See [`docs/tool_author_guide.md`](docs/tool_author_guide.md) for the full
guide. The short version:

1. Create `src/formulation_os/tools/builtins/<your_tool>/`.
2. Add a `tool.yaml` following the
   [Scientific Tool Specification v0.2](docs/sts_specification.md).
3. Add a `backend.py` exposing a `run(input_data: dict) -> dict`
   function (for `executor.type: python`).
4. The loader will pick it up automatically on the next registry load.
5. Add a smoke test under `tests/test_tools/test_builtins/`.

---

## Adding a new Planner

The Planner interface is in `src/formulation_os/planner/base.py`. To add
a new implementation (e.g., embedding-based):

1. Subclass `Planner` and implement `plan(query, top_k)`.
2. Add tests under `tests/test_planner/`.
3. Export it from `src/formulation_os/planner/__init__.py`.
4. Update `make_planner_from_env` if it should be selectable via env var.

---

## Pull request process

1. Create a topic branch off `main`.
2. Keep changes focused. A PR should ideally correspond to one task.
3. Make sure `make test` and `make lint` both pass locally.
4. Write a clear PR description: what changed, why, and how to verify.
5. Reference any related issue or paper section.

---

## License

By contributing, you agree that your contributions will be licensed
under the [MIT License](LICENSE) that covers the project.
