"""Scientific Registry: catalog of all Tools available to the Workflow Planner.

The Registry is the single entry point through which the Planner
discovers and resolves Tools. In v0.1 it is a simple in-memory map;
Task 3 also introduces an embedding-based retrieval surface (top-k
recall against the Registry's tool cards).

Why a Registry (and not a free-for-all over the filesystem)?
The Registry provides:

- **Identity.** Tools are referenced by name (`FormulationAI`), not by
  path. This decouples downstream code from disk layout.
- **Lookup.** O(1) ``get(name)`` for fast resolution.
- **Discovery.** ``list()`` and ``list_metadata()`` power the Planner's
  retrieval prompt.
- **Composition.** Loaders can be swapped (YAML on disk → Python
  entry-points → MCP server discovery) without changing downstream
  code.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from formulation_os.core.tool import Tool
from formulation_os.tools import load_tool


class ToolRegistry:
    """Catalog of :class:`Tool` instances.

    Tools can be loaded from disk via :meth:`load_all` (which discovers
    one tool per subdirectory containing ``tool.yaml``) or registered
    in-memory via :meth:`register`.
    """

    def __init__(self, tools_dir: str | Path | None = None) -> None:
        self.tools_dir = Path(tools_dir) if tools_dir else None
        self._tools: dict[str, Tool] = {}

    # ---- Loading -------------------------------------------------------- #

    def load_all(self) -> "ToolRegistry":
        """Discover and load all tools from subdirectories of ``tools_dir``.

        Each immediate subdirectory containing a ``tool.yaml`` file is
        loaded as a Tool. Subdirectories without ``tool.yaml`` are
        skipped silently.

        Returns:
            Self, for chaining.

        Raises:
            ValueError: If ``tools_dir`` was not provided at construction.
        """
        if self.tools_dir is None:
            raise ValueError(
                "ToolRegistry.load_all() requires tools_dir to be set "
                "at construction."
            )
        for sub in sorted(self.tools_dir.iterdir()):
            if not sub.is_dir():
                continue
            if not (sub / "tool.yaml").exists():
                continue
            tool = load_tool(sub)
            self.register(tool)
        return self

    def register(self, tool: Tool) -> None:
        """Add a Tool to the registry (or replace an existing one with the same name)."""
        self._tools[tool.name] = tool

    # ---- Lookup --------------------------------------------------------- #

    def get(self, name: str) -> Tool:
        """Return the Tool registered under ``name``.

        Raises:
            KeyError: If no Tool with that name is registered.
        """
        if name not in self._tools:
            raise KeyError(
                f"Tool '{name}' not found in registry. "
                f"Known tools: {sorted(self._tools.keys())}"
            )
        return self._tools[name]

    def try_get(self, name: str) -> Tool | None:
        """Return the Tool under ``name``, or None if not registered."""
        return self._tools.get(name)

    # ---- Discovery ------------------------------------------------------ #

    def list(self) -> list[Tool]:
        """Return all registered Tools."""
        return list(self._tools.values())

    def names(self) -> list[str]:
        """Return all registered tool names (sorted)."""
        return sorted(self._tools.keys())

    def list_metadata(self) -> list[dict[str, Any]]:
        """Return LLM-friendly cards for every registered Tool.

        The cards are what an embedding-based retriever (Task 3 v2)
        will embed in the vector index.
        """
        return [tool.to_card() for tool in self._tools.values()]

    # ---- Dunder --------------------------------------------------------- #

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and name in self._tools

    def __iter__(self):
        return iter(self._tools.values())

    def __repr__(self) -> str:
        return f"<ToolRegistry n_tools={len(self._tools)}>"