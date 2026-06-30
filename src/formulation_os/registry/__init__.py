"""Scientific Registry: catalog of Tools (Task 3).

The Registry provides name-based lookup, in-memory registration, and
metadata surfaces for retrieval. The Planner consumes the Registry
through its abstract :class:`~formulation_os.planner.base.Planner`
interface, so swapping rule-based for LLM-based or embedding-based
planners does not require Registry changes.
"""

from formulation_os.registry.registry import ToolRegistry

__all__ = ["ToolRegistry"]