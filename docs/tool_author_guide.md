# Tool Author Guide

How to add a new Tool to FormulationOS.

A Tool is a directory containing:

```
my_tool/
├── tool.yaml       # STS v0.2 declaration (required)
├── README.md       # human-readable docs (strongly recommended)
└── backend.py      # executor implementation (for type: python)
```

## Step 1 — Create the directory

```bash
mkdir -p src/formulation_os/tools/builtins/my_tool
```

## Step 2 — Write `backend.py`

A function that takes a single `dict` argument and returns a `dict`:

```python
"""Backend for MyTool.

Replace this docstring with a description of what the tool does,
what its inputs mean, and what the outputs represent.
"""

from typing import Any


def run(input_data: dict[str, Any]) -> dict[str, Any]:
    drug_name = input_data["drug_name"]
    # ... call your model, return results ...
    return {
        "drug_name": drug_name,
        "result": "...",
        "warnings": [],
    }
```

The function **must** return a dict. Returning any other type will raise `ToolExecutionError` at runtime.

## Step 3 — Write `tool.yaml`

```yaml
name: MyTool
version: 0.1.0
owner: my-lab
description: |
  What my tool does in plain English. Include "use this when" and
  "do not use this when" guidance — the Workflow Planner consumes
  this description.

semantics:
  capabilities:
    - my_capability
  domain: my-domain

input_schema:
  type: object
  properties:
    drug_name: {type: string}
  required: [drug_name]

output_schema:
  type: object
  properties:
    result: {type: string}
  required: [result]

planning_hints:
  examples:
    - input: {drug_name: Ibuprofen}
      output_summary: Mocked example
  keywords: [my, keywords]

scientific_dependencies:
  upstream_capabilities_optional: []
  upstream_capabilities_required: []

executor:
  type: python
  module: formulation_os.tools.builtins.my_tool.backend
  function: run

provenance_spec:
  record_inputs: true
  record_outputs: true
  record_parameters: true
  record_compute_env: true

mock: true
```

See [`sts_specification.md`](sts_specification.md) for full field semantics.

## Step 4 — Write `README.md`

A short human-readable document with:

- One-paragraph summary
- When to use / when not to use
- Output table (what each field means)
- A "Replacing with a real model" section

Use one of the five built-in tools as a template (`src/formulation_os/tools/builtins/formulation_ai/README.md` is a good example).

## Step 5 — Add a test

Add `tests/test_tools/test_builtins/test_my_tool.py`:

```python
from formulation_os.tools.loader import load_tool
from tests.conftest import BUILTINS_DIR


def test_my_tool_basic() -> None:
    tool = load_tool(BUILTINS_DIR / "my_tool")
    out = tool.execute({"drug_name": "Ibuprofen"})
    assert "result" in out
```

## Step 6 — Run the smoke test

```bash
pytest tests/smoke/test_end_to_end.py -v
```

If your tool loads and executes successfully, you're done.

## Optional — wire a real model

To replace the mock with a real model, you can either:

1. **Implement it in Python** — wrap your model in `backend.py`. Update `mock: false` and bump `version`.
2. **Deploy it as a REST API** — change `executor.type` to `http` and point `executor.url` at your service (requires the HTTP Executor from Task 5).
3. **Wrap it as a CLI** — change `executor.type` to `cli` and specify `executor.command` and `executor.args` (requires the CLI Executor from Task 5).
4. **Use MCP** — change `executor.type` to `mcp` and supply MCP server launch info (requires the MCP Executor, future task).

In all cases, the Workflow Planner, Scientific Registry, and downstream layers require **no changes**. Adding a new Tool means adding a new directory under `tools/builtins/`.