#!/usr/bin/env python3
"""Comparison Demo: Template Planner vs Capability-Aware Planner

This demo shows the difference between:
1. Original WorkflowPlanner (template-based)
2. CapabilityAwarePlanner (reasoning-based)

Key improvements in Capability-Aware version:
- Reads tool metadata (capabilities, dependencies)
- Provides justification for each step
- Reasons about different formulation types
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from formulation_os.llm.client import MockLLMClient
from formulation_os.planner.capability_aware_planner import CapabilityAwarePlanner
from formulation_os.planner.workflow_planner import WorkflowPlanner
from formulation_os.registry import ToolRegistry


def create_template_response() -> str:
    """Mock response from template-based planner."""
    return json.dumps({
        "workflow": [
            {
                "step_id": "step_1",
                "tool": "PreformulationAI",
                "goal": "Predict properties",
                "depends_on": []
            },
            {
                "step_id": "step_2",
                "tool": "FormulationAI",
                "goal": "Design formulation",
                "depends_on": ["step_1"]
            }
        ],
        "rationale": "Standard workflow"
    })


def create_capability_aware_response() -> str:
    """Mock response from capability-aware planner."""
    return json.dumps({
        "workflow": [
            {
                "step_id": "step_1",
                "tool": "PreformulationAI",
                "goal": "Predict physicochemical properties",
                "depends_on": [],
                "justification": "Need solubility data before selecting excipients. PreformulationAI provides BCS classification which determines formulation strategy."
            },
            {
                "step_id": "step_2",
                "tool": "FormulationAI",
                "goal": "Design tablet formulation",
                "depends_on": ["step_1"],
                "justification": "FormulationAI capabilities include tablet design. Depends on solubility_prediction from PreformulationAI to select appropriate excipients for BCS class."
            }
        ],
        "rationale": "Sequential workflow: solubility analysis informs excipient selection for optimal tablet formulation"
    })


def main() -> None:
    print("=" * 70)
    print("Comparison: Template-Based vs Capability-Aware Planning")
    print("=" * 70)
    print()

    # Setup
    builtins_dir = Path(__file__).parent / "src" / "formulation_os" / "tools" / "builtins"
    registry = ToolRegistry(builtins_dir).load_all()
    query = "Design a tablet formulation for ibuprofen"

    print(f"📝 Query: {query}\n")

    # Original Planner (Template-Based)
    print("─" * 70)
    print("1️⃣  ORIGINAL PLANNER (Template-Based)")
    print("─" * 70)

    template_client = MockLLMClient(response=create_template_response())
    template_planner = WorkflowPlanner(registry, template_client)

    plan1 = template_planner.plan_workflow(query)
    if plan1:
        print(f"✓ Generated {len(plan1['workflow'])} steps")
        print(f"Rationale: {plan1['rationale']}\n")
        for step in plan1["workflow"]:
            print(f"  {step['step_id']}: {step['tool']}")
            print(f"    Goal: {step['goal']}")
            if step.get('justification'):
                print(f"    Justification: {step['justification']}")
            print()
    print()

    # Capability-Aware Planner
    print("─" * 70)
    print("2️⃣  CAPABILITY-AWARE PLANNER (Reasoning-Based)")
    print("─" * 70)

    capability_client = MockLLMClient(response=create_capability_aware_response())
    capability_planner = CapabilityAwarePlanner(registry, capability_client)

    plan2 = capability_planner.plan_workflow(query)
    if plan2:
        print(f"✓ Generated {len(plan2['workflow'])} steps")
        print(f"Rationale: {plan2['rationale']}\n")
        for step in plan2["workflow"]:
            print(f"  {step['step_id']}: {step['tool']}")
            print(f"    Goal: {step['goal']}")
            if step.get('justification'):
                print(f"    ✨ Justification: {step['justification']}")
            print()
    print()

    # Comparison
    print("=" * 70)
    print("📊 KEY DIFFERENCES")
    print("=" * 70)
    print()
    print("Original Planner:")
    print("  • Generic goals ('Predict properties')")
    print("  • No justification")
    print("  • Template-based ('Standard workflow')")
    print()
    print("Capability-Aware Planner:")
    print("  • Specific goals based on capabilities")
    print("  • ✨ Scientific justification for each step")
    print("  • Reasoning-based (mentions BCS class, dependencies)")
    print()
    print("💡 The Capability-Aware Planner provides:")
    print("  1. Explainable workflows")
    print("  2. Scientific rationale")
    print("  3. Metadata-driven decisions")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
