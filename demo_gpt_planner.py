#!/usr/bin/env python3
"""Demo: GPT Workflow Planner + Mock Executor

This script demonstrates FormulationOS Phase 2.0:
- Use an LLM (GPT) to plan a formulation workflow from natural language
- Execute the planned workflow using mock tools
- Generate an integrated scientific report

Example:
    python demo_gpt_planner.py "Design an oral formulation for ibuprofen 200mg"
"""

import json
import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, will use system environment variables
    pass

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent / "src"))

from formulation_os.llm.client import MockLLMClient, OpenAIClient, MiniMaxClient
from formulation_os.orchestrator.workflow_orchestrator import WorkflowOrchestrator
from formulation_os.planner.workflow_planner import WorkflowPlanner
from formulation_os.registry import ToolRegistry


def create_mock_client() -> MockLLMClient:
    """Create a mock LLM client with a predefined workflow response."""
    mock_workflow = {
        "workflow": [
            {
                "step_id": "step_1",
                "tool": "PreformulationAI",
                "goal": "Predict physicochemical properties (solubility, stability)",
                "depends_on": []
            },
            {
                "step_id": "step_2",
                "tool": "FormulationAI",
                "goal": "Recommend formulation strategy and excipients",
                "depends_on": ["step_1"]
            },
            {
                "step_id": "step_3",
                "tool": "FormulationDT",
                "goal": "Simulate dissolution profile",
                "depends_on": ["step_2"]
            },
            {
                "step_id": "step_4",
                "tool": "PBPK-AI",
                "goal": "Predict pharmacokinetics and bioavailability",
                "depends_on": ["step_2"]
            }
        ],
        "rationale": "Sequential preformulation → formulation design, then parallel dissolution simulation and PK prediction"
    }
    return MockLLMClient(response=json.dumps(mock_workflow))


def main() -> None:
    """Run the GPT Planner demo."""
    print("=" * 70)
    print("FormulationOS Phase 2.0 Demo")
    print("GPT Workflow Planner + Mock Executor")
    print("=" * 70)
    print()

    # Get user query
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "Design an oral formulation for ibuprofen 200mg tablet"

    print(f"📝 User Query:")
    print(f"   {query}")
    print()

    # Initialize components
    print("🔧 Initializing components...")

    # Load tools
    builtins_dir = Path(__file__).parent / "src" / "formulation_os" / "tools" / "builtins"
    registry = ToolRegistry(builtins_dir).load_all()
    print(f"   ✓ Loaded {len(list(registry))} tools: {', '.join(t.name for t in registry)}")

    # Create LLM client (mock for demo, can switch to real LLM)
    # Options: "mock", "openai", "minimax"
    llm_mode = "minimax"  # Change this to switch LLM provider

    import os

    if llm_mode == "minimax":
        # Use MiniMax (configured with your API key)
        api_key = os.getenv("MINIMAX_API_KEY")
        if not api_key:
            print("   ⚠ MINIMAX_API_KEY not set, falling back to mock")
            client = create_mock_client()
        else:
            client = MiniMaxClient(api_key=api_key, model="MiniMax-M3", max_tokens=2048)
            print("   ✓ Using MiniMax M3")
    elif llm_mode == "openai":
        # Use OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("   ⚠ OPENAI_API_KEY not set, falling back to mock")
            client = create_mock_client()
        else:
            client = OpenAIClient(api_key=api_key, model="gpt-4o-mini")
            print("   ✓ Using OpenAI GPT-4o-mini")
    else:
        # Use mock
        client = create_mock_client()
        print("   ✓ Using mock LLM (predefined workflow)")

    planner = WorkflowPlanner(registry, client)
    orchestrator = WorkflowOrchestrator(registry)
    print()

    # Step 1: Plan workflow
    print("🤖 Step 1: Planning workflow with LLM...")
    workflow_plan = planner.plan_workflow(query)

    if workflow_plan is None:
        print("   ❌ Planning failed!")
        sys.exit(1)

    print(f"   ✓ Generated workflow with {len(workflow_plan['workflow'])} steps")
    print(f"   📋 Rationale: {workflow_plan['rationale']}")
    print()
    print("   Workflow DAG:")
    for step in workflow_plan["workflow"]:
        deps = ", ".join(step["depends_on"]) if step["depends_on"] else "none"
        print(f"      {step['step_id']}: {step['tool']}")
        print(f"         Goal: {step['goal']}")
        print(f"         Depends on: {deps}")
    print()

    # Step 2: Execute workflow
    print("⚙️  Step 2: Executing workflow...")
    initial_inputs = {
        "drug_name": "Ibuprofen",
        "target_dose_mg": 200,
        "dosage_form": "tablet"
    }
    print(f"   Initial inputs: {initial_inputs}")
    print()

    report = orchestrator.execute_workflow(workflow_plan, query, initial_inputs)

    # Step 3: Display results
    print("📊 Step 3: Results")
    print(f"   Overall status: {report.status.upper()}")
    print(f"   Total tools executed: {len(report.tool_results)}")
    print()

    for i, result in enumerate(report.tool_results, 1):
        status_icon = "✓" if result.status == "ok" else "✗"
        print(f"   {status_icon} Tool {i}: {result.tool_name} v{result.tool_version}")
        print(f"      Status: {result.status}")
        print(f"      Duration: {result.duration_ms:.1f}ms")

        if result.warnings:
            for warning in result.warnings:
                print(f"      ⚠ Warning: {warning}")

        if result.output:
            # Show a preview of the output
            if isinstance(result.output, dict):
                summary = result.output.get("summary", "")
                if summary:
                    print(f"      Summary: {summary}")

        if result.error:
            print(f"      ❌ Error: {result.error}")
        print()

    print("=" * 70)
    print("✅ Demo completed!")
    print()
    print("💡 Next steps:")
    print("   1. Replace MockLLMClient with OpenAIClient (set OPENAI_API_KEY)")
    print("   2. Replace mock tools with real FormulationAI/PBPK APIs")
    print("   3. Add Streamlit UI for interactive workflow planning")
    print("=" * 70)


if __name__ == "__main__":
    main()
