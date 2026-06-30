"""Executor abstraction and its in-process Python implementation.

The Executor is the **execution backend** of a Tool. It is deliberately
separate from the Tool's metadata (:mod:`formulation_os.core.tool`)
because the same Executor interface must support heterogeneous execution
modalities: in-process Python (this file), REST APIs (future), CLI
subprocesses (future), MCP servers (future), gRPC services (future),
and Docker containers (future).
"""

from __future__ import annotations

import importlib
from abc import ABC, abstractmethod
from typing import Any

from formulation_os.core.tool import ToolExecutionError


class Executor(ABC):
    """Pluggable execution backend for a Tool.

    An Executor receives a validated input dict (conforming to the
    Tool's ``input_schema``) and returns a result dict (conforming to
    the Tool's ``output_schema``).
    """

    @abstractmethod
    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the underlying tool with the given input.

        Args:
            input_data: Validated input dict.

        Returns:
            Output dict.

        Raises:
            ToolExecutionError: If execution fails for any reason.
        """
        raise NotImplementedError


class PythonExecutor(Executor):
    """Calls a Python function in-process.

    Used for mocks and for in-lab scientific models that ship as Python
    packages. The target function must accept a single ``dict`` argument
    and return a single ``dict``.
    """

    def __init__(self, module: str, function: str) -> None:
        self._module_path = module
        self._function_name = function
        self._func = self._resolve()

    def _resolve(self) -> Any:
        try:
            module = importlib.import_module(self._module_path)
            return getattr(module, self._function_name)
        except (ImportError, AttributeError) as e:
            raise ToolExecutionError(
                self._module_path,
                f"Cannot resolve {self._module_path}:{self._function_name}: {e}",
                cause=e,
            ) from e

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        try:
            result = self._func(input_data)
        except ToolExecutionError:
            raise
        except Exception as e:
            raise ToolExecutionError(
                self._module_path,
                f"Backend execution failed: {e}",
                cause=e,
            ) from e
        if not isinstance(result, dict):
            raise ToolExecutionError(
                self._module_path,
                f"Backend must return a dict, got {type(result).__name__}.",
            )
        return result

    def __repr__(self) -> str:
        return f"<PythonExecutor {self._module_path}:{self._function_name}>"