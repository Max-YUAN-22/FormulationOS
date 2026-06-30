"""Tests for the PythonExecutor."""

from __future__ import annotations

import pytest

from formulation_os.core.tool import ToolExecutionError
from formulation_os.runtime.executor import PythonExecutor


def _add(a: dict) -> dict:
    return {"sum": a["x"] + a["y"]}


def _returns_non_dict(_: dict):
    return "not a dict"


def test_python_executor_calls_function() -> None:
    exec_ = PythonExecutor(
        module="formulation_os.tools.builtins.formulation_ai.backend",
        function="run",
    )
    out = exec_.run({"drug_name": "Ibuprofen", "target_dose_mg": 200, "dosage_form": "tablet"})
    assert out["drug_name"] == "Ibuprofen"
    assert out["dosage_form"] == "tablet"
    assert isinstance(out["excipients"], list)
    assert any("MOCK" in w for w in out["warnings"])


def test_python_executor_resolves_function_by_path() -> None:
    exec_ = PythonExecutor(
        module="tests.test_core.test_executor_python",
        function="_add",
    )
    assert exec_.run({"x": 1, "y": 2}) == {"sum": 3}


def test_python_executor_missing_module_raises_tool_execution_error() -> None:
    with pytest.raises(ToolExecutionError):
        PythonExecutor(module="nonexistent.module", function="run")


def test_python_executor_missing_function_raises_tool_execution_error() -> None:
    with pytest.raises(ToolExecutionError):
        PythonExecutor(
            module="formulation_os.tools.builtins.formulation_ai.backend",
            function="nonexistent_function",
        )


def test_python_executor_wraps_runtime_errors() -> None:
    def _raises(_):
        raise RuntimeError("explode")

    import importlib
    import types

    mod = types.ModuleType("_fake_mod")
    mod.raises = _raises  # type: ignore[attr-defined]
    import sys
    sys.modules["_fake_mod"] = mod
    try:
        exec_ = PythonExecutor(module="_fake_mod", function="raises")
        with pytest.raises(ToolExecutionError):
            exec_.run({})
    finally:
        del sys.modules["_fake_mod"]


def test_python_executor_rejects_non_dict_output() -> None:
    import importlib
    import sys
    import types

    mod = types.ModuleType("_fake_mod2")
    mod.returns_non_dict = _returns_non_dict  # type: ignore[attr-defined]
    sys.modules["_fake_mod2"] = mod
    try:
        exec_ = PythonExecutor(module="_fake_mod2", function="returns_non_dict")
        with pytest.raises(ToolExecutionError):
            exec_.run({})
    finally:
        del sys.modules["_fake_mod2"]