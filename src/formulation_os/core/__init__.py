"""Core abstractions: Tool, ToolSpec (STS), and shared exceptions.

The core package defines the **declarative** half of the Tool abstraction
(metadata, schemas, contracts). It does NOT depend on any executor
implementation — that lives in :mod:`formulation_os.runtime`.
"""

from formulation_os.core.executor_spec import ExecutorSpec
from formulation_os.core.tool import (
    STSError,
    CostMetadata,
    PlanningHints,
    ProvenanceSpec,
    ScientificDependencies,
    ScientificSemantics,
    Tool,
    ToolExecutionError,
    ToolSpec,
    ToolSpecValidationError,
)

__all__ = [
    "STSError",
    "CostMetadata",
    "ExecutorSpec",
    "PlanningHints",
    "ProvenanceSpec",
    "ScientificDependencies",
    "ScientificSemantics",
    "Tool",
    "ToolExecutionError",
    "ToolSpec",
    "ToolSpecValidationError",
]