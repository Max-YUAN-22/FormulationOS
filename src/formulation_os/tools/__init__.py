"""Tools package: Tool loader and built-in mock tools.

The Tools package is the **wiring layer** between declarative metadata
(:mod:`formulation_os.core`) and execution backends
(:mod:`formulation_os.runtime`).
"""

from formulation_os.tools.loader import load_tool

__all__ = ["load_tool"]