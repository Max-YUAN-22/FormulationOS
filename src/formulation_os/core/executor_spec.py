"""ExecutorSpec: the declarative description of how a Tool is executed.

The :class:`ExecutorSpec` is the YAML-serializable half of the executor
abstraction. It declares **what** executor to use and **how to reach it**.
The actual execution logic lives in :mod:`formulation_os.runtime.executor`.

Keeping these two halves separate means the Core (Tool + ToolSpec) has no
runtime dependency on any executor backend.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ExecutorType = Literal["python", "http", "cli", "mcp", "grpc", "docker"]


class ExecutorSpec(BaseModel):
    """Declarative description of a tool's execution backend.

    Attributes:
        type: One of ``python``, ``http``, ``cli``, ``mcp``, ``grpc``, ``docker``.
        module: For ``python``: the importable module path.
        function: For ``python``: the callable name within the module.
        url: For ``http``: the endpoint URL.
        method: For ``http``: HTTP method (default ``POST``).
        command: For ``cli``/``docker``: the command to invoke.
        args: For ``cli``/``docker``: argument template.
        headers: For ``http``: optional HTTP headers (e.g., auth).
    """

    model_config = ConfigDict(extra="forbid")

    type: ExecutorType
    module: str | None = None
    function: str | None = None
    url: str | None = None
    method: str | None = None
    command: str | None = None
    args: list[str] | None = None
    headers: dict[str, str] | None = None

    def validate_for_type(self) -> None:
        """Check that the spec carries the fields required for its declared type.

        Raises:
            ValueError: If required fields are missing.
        """
        if self.type == "python":
            if not self.module or not self.function:
                raise ValueError(
                    "ExecutorSpec of type 'python' requires 'module' and 'function'."
                )
        elif self.type == "http":
            if not self.url:
                raise ValueError("ExecutorSpec of type 'http' requires 'url'.")
        elif self.type in ("cli", "docker"):
            if not self.command:
                raise ValueError(f"ExecutorSpec of type '{self.type}' requires 'command'.")