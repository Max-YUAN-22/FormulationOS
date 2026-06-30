"""End-to-End Smoke Test (Task 2.5).

Goal: prove that the lower layers — Tool loading + Tool execution —
are correctly wired together, so that when the Workflow Planner
(Task 4), Execution Runtime (Task 5), and Artifact Generator
(Task 6) land on top, the full pipeline works.

In v0.1:

    User query
        ↓
    Tool loaded from disk
        ↓
    Tool executed
        ↓
    Result serialized as artifact.json

When the higher layers arrive, this test will evolve to exercise them
too (the planner producing a DAG, the runtime executing it, the artifact
generator producing Markdown + figures).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from formulation_os.tools.loader import load_tool
from tests.conftest import BUILTINS_DIR


def test_smoke_ibuprofen_tablet(tmp_path: Path) -> None:
    """User: 'Design an ibuprofen tablet at 200 mg.' → artifact.json."""
    artifact_path = tmp_path / "artifact.json"

    # 1. Load the tool from disk
    tool = load_tool(BUILTINS_DIR / "formulation_ai")
    assert tool.name == "FormulationAI"
    assert tool.spec.mock is True

    # 2. Translate user query to tool input (Planner will do this in Task 4)
    user_query = "Design an ibuprofen tablet at 200 mg."
    input_data = {
        "drug_name": "Ibuprofen",
        "target_dose_mg": 200,
        "dosage_form": "tablet",
    }

    # 3. Execute the tool
    output = tool.execute(input_data)
    assert output["drug_name"] == "Ibuprofen"
    assert "excipients" in output

    # 4. Wrap into a v0.1 artifact and write to disk
    artifact = {
        "artifact_id": "smoke_formulation_ibuprofen_tablet",
        "type": "tool_output",
        "user_query": user_query,
        "tool": tool.name,
        "tool_version": tool.version,
        "mock": tool.spec.mock,
        "input": input_data,
        "output": output,
        "produced_at": datetime.now(timezone.utc).isoformat(),
        "provenance": {
            "execution_id": "smoke_001",
            "tool_name": tool.name,
            "tool_version": tool.version,
            "record_inputs": True,
            "record_outputs": True,
            "record_compute_env": False,
        },
    }
    artifact_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")

    # 5. Round-trip verify
    reloaded = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert reloaded["tool"] == "FormulationAI"
    assert reloaded["output"]["excipients"][0]["name"]


def test_smoke_load_all_five_builtins() -> None:
    """All 5 built-in mock tools should load and execute successfully."""
    for tool_name in ("formulation_ai", "preformulation_ai", "pbpk_ai", "formulation_dt", "literature"):
        tool = load_tool(BUILTINS_DIR / tool_name)
        # Each tool has at least one of these standard input shapes
        for candidate_input in (
            {"drug_name": "TestCompound"},
            {"query": "test query"},
        ):
            try:
                out = tool.execute(candidate_input)
                assert isinstance(out, dict)
                break
            except Exception:
                continue
        else:
            pytest.fail(f"No standard input shape worked for {tool_name}")