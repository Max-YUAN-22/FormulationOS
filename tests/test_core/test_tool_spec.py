"""Tests for STS v0.2 validation in :class:`ToolSpec`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from formulation_os.core.executor_spec import ExecutorSpec
from formulation_os.core.tool import (
    PlanningHints,
    ProvenanceSpec,
    ScientificDependencies,
    ScientificSemantics,
    ToolSpec,
)


def _minimal_spec(**overrides) -> dict:
    spec = {
        "name": "Demo",
        "version": "0.1.0",
        "description": "A demo tool.",
        "executor": {"type": "python", "module": "demo.backend", "function": "run"},
    }
    spec.update(overrides)
    return spec


def test_minimal_spec_loads() -> None:
    spec = ToolSpec.model_validate(_minimal_spec())
    assert spec.name == "Demo"
    assert spec.version == "0.1.0"
    assert spec.description == "A demo tool."
    assert spec.executor.type == "python"
    assert spec.executor.module == "demo.backend"
    assert spec.executor.function == "run"
    # Defaults
    assert spec.semantics.capabilities == []
    assert spec.semantics.domain is None
    assert spec.planning_hints.examples == []
    assert spec.planning_hints.keywords == []
    assert spec.planning_hints.notes is None
    assert spec.scientific_dependencies.upstream_capabilities_optional == []
    assert spec.scientific_dependencies.upstream_capabilities_required == []
    assert spec.provenance_spec.record_inputs is True
    assert spec.mock is False


def test_full_spec_with_all_sts_extensions() -> None:
    raw = _minimal_spec(
        semantics={"capabilities": ["solubility"], "domain": "preformulation"},
        input_schema={
            "type": "object",
            "properties": {"drug_name": {"type": "string"}},
            "required": ["drug_name"],
        },
        output_schema={"type": "object"},
        planning_hints={
            "examples": [{"input": {"drug_name": "X"}, "output_summary": "y"}],
            "keywords": ["solubility", "logP"],
            "notes": "Use before FormulationAI.",
        },
        scientific_dependencies={
            "upstream_capabilities_optional": ["literature_search"],
            "upstream_capabilities_required": [],
            "rationale": "Better with lit context.",
        },
        provenance_spec={
            "record_inputs": True,
            "record_outputs": True,
            "record_parameters": True,
            "record_compute_env": True,
        },
        cost={"latency_class": "low", "cost_class": "low", "confidence": "experimental"},
        mock=True,
    )
    spec = ToolSpec.model_validate(raw)
    assert spec.semantics.capabilities == ["solubility"]
    assert spec.semantics.domain == "preformulation"
    assert spec.planning_hints.examples[0]["input"]["drug_name"] == "X"
    assert spec.planning_hints.keywords == ["solubility", "logP"]
    assert spec.scientific_dependencies.rationale is not None
    assert spec.provenance_spec.record_inputs is True
    assert spec.cost is not None
    assert spec.cost.latency_class == "low"
    assert spec.mock is True


def test_unknown_field_rejected() -> None:
    raw = _minimal_spec(unknown_field="nope")
    with pytest.raises(ValidationError):
        ToolSpec.model_validate(raw)


def test_executor_missing_required_field_rejected() -> None:
    # python executor must have module + function
    with pytest.raises(ValidationError):
        ToolSpec.model_validate(
            _minimal_spec(executor={"type": "python", "module": "demo"})
        )
    # http executor must have url (use url=None to exercise the missing branch)
    with pytest.raises(ValidationError):
        ToolSpec.model_validate(
            _minimal_spec(executor={"type": "http", "module": "x", "function": "y"})
        )


def test_planning_hints_rejects_arbitrary_keys() -> None:
    # 'few_shots' was the v0.1 name; v0.2 uses 'examples'. Extra keys must be rejected.
    with pytest.raises(ValidationError):
        PlanningHints.model_validate({"few_shots": []})


def test_scientific_dependencies_rationale_optional() -> None:
    deps = ScientificDependencies(upstream_capabilities_required=["x"])
    assert deps.rationale is None


def test_provenance_spec_defaults_to_true() -> None:
    p = ProvenanceSpec()
    assert p.record_inputs and p.record_outputs and p.record_parameters and p.record_compute_env


def test_scientific_semantics_accepts_empty() -> None:
    s = ScientificSemantics()
    assert s.capabilities == []
    assert s.domain is None


def test_executor_spec_validate_for_type() -> None:
    # python ok
    ExecutorSpec(type="python", module="m", function="f").validate_for_type()
    # python missing function
    with pytest.raises(ValueError):
        ExecutorSpec(type="python", module="m").validate_for_type()
    # http missing url
    with pytest.raises(ValueError):
        ExecutorSpec(type="http").validate_for_type()
    # cli missing command
    with pytest.raises(ValueError):
        ExecutorSpec(type="cli").validate_for_type()