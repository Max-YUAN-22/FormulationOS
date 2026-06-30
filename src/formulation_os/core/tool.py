"""Tool abstraction and Scientific Tool Specification (STS) v0.2 models.

A :class:`Tool` is the foundation of the Scientific Workflow Abstraction.
It packages:

* **Declarative metadata** (``tool.yaml`` parsed into :class:`ToolSpec`)
* **An executable backend** (an :class:`Executor` instance; supplied by the
  :class:`~formulation_os.tools.loader` and implemented in
  :mod:`formulation_os.runtime.executor`)

The Tool abstraction deliberately does **not** know about LLMs, the
Workflow Planner, or any Scientific Workflow concept. Those layers
*consume* tools via the metadata surface (:py:meth:`Tool.to_card`,
:py:meth:`Tool.to_llm_description`) and the
:py:meth:`Tool.execute` entry point.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from formulation_os.core.executor_spec import ExecutorSpec


# --------------------------------------------------------------------------- #
# Exceptions                                                                   #
# --------------------------------------------------------------------------- #


class STSError(Exception):
    """Base exception for Scientific Tool Specification (STS) errors."""


class ToolSpecValidationError(STSError):
    """Raised when a ``tool.yaml`` file fails STS validation."""


class ToolExecutionError(STSError):
    """Raised when a :class:`Tool` execution fails."""

    def __init__(
        self,
        tool_name: str,
        message: str,
        *,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(f"[{tool_name}] {message}")
        self.tool_name = tool_name
        self.cause = cause


# --------------------------------------------------------------------------- #
# STS v0.2 Pydantic models                                                     #
# --------------------------------------------------------------------------- #


class ScientificSemantics(BaseModel):
    """STS Extension 1: informal scientific semantic annotations.

    These are **not** a formal ontology or taxonomy. They are flat
    capability tags plus an optional high-level domain identifier, used
    by the Registry for embedding-based tool retrieval.
    """

    model_config = ConfigDict(extra="forbid")

    capabilities: list[str] = Field(default_factory=list)
    domain: str | None = None


class PlanningHints(BaseModel):
    """STS Extension 2: hints consumed by the Workflow Planner.

    Generalized beyond few-shot prompting to include any prompt-ready
    material: examples, retrieval keywords, or free-form notes. This
    naming survives future evolution to demonstrations, DSL fragments,
    or template snippets.
    """

    model_config = ConfigDict(extra="forbid")

    examples: list[dict[str, Any]] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    notes: str | None = None


class ScientificDependencies(BaseModel):
    """STS Extension 3: cross-tool scientific constraints.

    Used by the Scientific Dependency Enforcer (Task 4) to validate
    that a generated Workflow DAG satisfies declared prerequisites.
    """

    model_config = ConfigDict(extra="forbid")

    upstream_capabilities_optional: list[str] = Field(default_factory=list)
    upstream_capabilities_required: list[str] = Field(default_factory=list)
    rationale: str | None = None


class ProvenanceSpec(BaseModel):
    """STS Extension 4: declarative specification of what to record.

    The Execution Runtime consults this spec when emitting the
    scientific evidence chain for each execution.
    """

    model_config = ConfigDict(extra="forbid")

    record_inputs: bool = True
    record_outputs: bool = True
    record_parameters: bool = True
    record_compute_env: bool = True


class CostMetadata(BaseModel):
    """Optional cost metadata.

    Informational in v0.1. The Scientific Dependency Enforcer (not a
    cost-aware scheduler) is the v0.1 scheduling policy; richer
    multi-objective optimization is future work.
    """

    model_config = ConfigDict(extra="forbid")

    latency_class: str = Field(default="medium")  # low | medium | high
    cost_class: str = Field(default="medium")  # low | medium | high
    confidence: str = Field(default="experimental")  # experimental | validated | production


class ToolSpec(BaseModel):
    """Parsed content of a ``tool.yaml`` file. Single source of truth.

    Implements Scientific Tool Specification (STS) v0.2 — an extension
    schema over standard tool specifications (OpenAPI, MCP tool
    descriptors) that adds four scientific extensions.
    """

    model_config = ConfigDict(extra="forbid")

    # === Standard Metadata ===
    name: str
    version: str = "0.1.0"
    owner: str | None = None
    description: str

    # === STS Extension 1: Scientific Semantics ===
    semantics: ScientificSemantics = Field(default_factory=ScientificSemantics)

    # === Standard I/O (JSON Schema) ===
    input_schema: dict[str, Any] = Field(default_factory=lambda: {"type": "object"})
    output_schema: dict[str, Any] = Field(default_factory=lambda: {"type": "object"})

    # === STS Extension 2: Planning Hints ===
    planning_hints: PlanningHints = Field(default_factory=PlanningHints)

    # === STS Extension 3: Scientific Dependencies ===
    scientific_dependencies: ScientificDependencies = Field(
        default_factory=ScientificDependencies
    )

    # === Executor Declaration ===
    executor: ExecutorSpec

    # === STS Extension 4: Provenance Specification ===
    provenance_spec: ProvenanceSpec = Field(default_factory=ProvenanceSpec)

    # === Optional cost metadata ===
    cost: CostMetadata | None = None

    # === Flags ===
    mock: bool = False

    def model_post_init(self, __context: Any) -> None:
        """Validate the executor spec matches its declared type."""
        self.executor.validate_for_type()


# --------------------------------------------------------------------------- #
# Tool Abstract Base Class                                                     #
# --------------------------------------------------------------------------- #


class Tool(ABC):
    """Container: declarative metadata (STS) + executable backend.

    A Tool is the foundation of the Scientific Workflow Abstraction. It
    exposes:

    * **Metadata proxies** (read-only properties over ``self.spec``) for
      discovery and rendering by the Registry / Planner / API.
    * **An :py:meth:`execute` method** that the Execution Runtime calls
      with validated input.
    """

    def __init__(self, spec: ToolSpec) -> None:
        self.spec = spec

    # ---- Metadata proxies (LLM discovery surface) ------------------------ #

    @property
    def name(self) -> str:
        return self.spec.name

    @property
    def version(self) -> str:
        return self.spec.version

    @property
    def description(self) -> str:
        return self.spec.description

    @property
    def input_schema(self) -> dict[str, Any]:
        return self.spec.input_schema

    @property
    def output_schema(self) -> dict[str, Any]:
        return self.spec.output_schema

    @property
    def capabilities(self) -> list[str]:
        return self.spec.semantics.capabilities

    @property
    def planning_hints(self) -> PlanningHints:
        return self.spec.planning_hints

    # ---- Execution ------------------------------------------------------ #

    @abstractmethod
    def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Run the tool with validated input.

        Args:
            input_data: A dict conforming to ``self.input_schema``.

        Returns:
            A dict conforming to ``self.output_schema``.

        Raises:
            ToolExecutionError: If execution fails for any reason.
        """
        raise NotImplementedError

    # ---- Discovery ------------------------------------------------------ #

    def to_card(self) -> dict[str, Any]:
        """Compact LLM-friendly card used for embedding-based retrieval.

        The card is what gets embedded in the Registry's vector index.
        The full :class:`ToolSpec` is loaded only **after** a tool has
        been selected, not before.
        """
        card: dict[str, Any] = {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "capabilities": self.capabilities,
            "domain": self.spec.semantics.domain,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
        }
        if self.spec.planning_hints.examples:
            card["examples"] = self.spec.planning_hints.examples
        if self.spec.planning_hints.keywords:
            card["keywords"] = self.spec.planning_hints.keywords
        return card

    def to_llm_description(self) -> dict[str, Any]:
        """The JSON description passed to LLMs (OpenAI / Anthropic tool format)."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema,
            "examples": self.spec.planning_hints.examples,
        }

    def __repr__(self) -> str:
        return f"<Tool {self.name} v{self.version} mock={self.spec.mock}>"