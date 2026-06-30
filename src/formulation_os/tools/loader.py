"""Load :class:`Tool` instances from on-disk directories.

A tool directory must contain:

* ``tool.yaml`` — required, an STS v0.2 declaration.
* ``README.md`` — optional, human-readable documentation.
* ``backend.py`` — required for ``python`` executors; contains the
  callable referenced by ``executor.module`` + ``executor.function``.

The loader is intentionally minimal in v0.1: it discovers one tool per
directory and returns a wired :class:`Tool` instance. The
:class:`~formulation_os.registry.registry.ScientificRegistry` (Task 3)
composes multiple loaders into a queryable collection.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from formulation_os.core.executor_spec import ExecutorSpec
from formulation_os.core.tool import (
    Tool,
    ToolExecutionError,
    ToolSpec,
    ToolSpecValidationError,
)
from formulation_os.runtime.executor import Executor, PythonExecutor


class _GenericTool(Tool):
    """Default Tool implementation wiring metadata to an Executor."""

    def __init__(self, spec: ToolSpec, executor: Executor) -> None:
        super().__init__(spec)
        self._executor = executor

    def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        try:
            return self._executor.run(input_data)
        except ToolExecutionError:
            raise
        except Exception as e:
            raise ToolExecutionError(self.name, f"Backend execution failed: {e}", cause=e) from e


def _build_executor(spec: ExecutorSpec) -> Executor:
    """Construct an Executor instance from a declarative :class:`ExecutorSpec`."""
    if spec.type == "python":
        return PythonExecutor(spec.module or "", spec.function or "")
    raise NotImplementedError(
        f"Executor type '{spec.type}' is not yet implemented. "
        "Supported in v0.1: 'python'."
    )


def load_tool(tool_dir: str | Path) -> Tool:
    """Load a Tool from a directory containing ``tool.yaml``.

    Args:
        tool_dir: Path to a directory. Must contain a valid STS v0.2
            ``tool.yaml`` file.

    Returns:
        A wired :class:`Tool` instance.

    Raises:
        FileNotFoundError: If ``tool.yaml`` does not exist.
        ToolSpecValidationError: If ``tool.yaml`` fails STS validation.
        NotImplementedError: If the declared executor type is not yet supported.
    """
    tool_dir = Path(tool_dir)
    yaml_path = tool_dir / "tool.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"No tool.yaml in {tool_dir}")

    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ToolSpecValidationError(
            f"tool.yaml in {tool_dir} must contain a YAML mapping at the top level."
        )

    try:
        spec = ToolSpec.model_validate(raw)
    except Exception as e:
        raise ToolSpecValidationError(
            f"tool.yaml in {tool_dir} failed STS v0.2 validation: {e}"
        ) from e

    executor = _build_executor(spec.executor)
    return _GenericTool(spec=spec, executor=executor)