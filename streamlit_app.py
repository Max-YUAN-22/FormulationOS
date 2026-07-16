"""FormulationOS Streamlit UI - Interactive Workflow Planning Interface

This Streamlit app provides a user-friendly interface for:
- Natural language workflow planning
- DAG visualization
- Real-time execution monitoring
- Result visualization

Run with: streamlit run streamlit_app.py
"""

import streamlit as st
from pathlib import Path
import sys
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from formulation_os.llm.client import MiniMaxClient, MockLLMClient
from formulation_os.planner.workflow_planner import WorkflowPlanner
from formulation_os.planner.workflow_search import WorkflowSearchEngine
from formulation_os.planner.workflow_validator import WorkflowValidator
from formulation_os.orchestrator.workflow_orchestrator import WorkflowOrchestrator
from formulation_os.registry import ToolRegistry

# Page config
st.set_page_config(
    page_title="FormulationOS",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .tool-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        margin: 0.25rem;
        background-color: #e8f4f8;
        border-radius: 0.5rem;
        font-size: 0.875rem;
    }
    .workflow-step {
        border-left: 3px solid #1f77b4;
        padding-left: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if "workflow_plan" not in st.session_state:
        st.session_state.workflow_plan = None
    if "execution_results" not in st.session_state:
        st.session_state.execution_results = None
    if "workflow_candidates" not in st.session_state:
        st.session_state.workflow_candidates = None
    if "selected_candidate" not in st.session_state:
        st.session_state.selected_candidate = 0


def load_components():
    """Load FormulationOS components."""
    if "registry" not in st.session_state:
        builtins_dir = Path(__file__).parent / "src" / "formulation_os" / "tools" / "builtins"
        st.session_state.registry = ToolRegistry(builtins_dir).load_all()

    if "client" not in st.session_state:
        import os
        from dotenv import load_dotenv
        load_dotenv()

        api_key = os.getenv("MINIMAX_API_KEY")
        if api_key:
            st.session_state.client = MiniMaxClient(api_key=api_key, max_tokens=2048)
        else:
            st.session_state.client = MockLLMClient(response="{}")

    if "planner" not in st.session_state:
        st.session_state.planner = WorkflowPlanner(
            client=st.session_state.client,
            registry=st.session_state.registry
        )

    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = WorkflowOrchestrator(
            registry=st.session_state.registry
        )


def main():
    """Main Streamlit app."""
    initialize_session_state()
    load_components()

    # Header
    st.markdown('<div class="main-header">🧬 FormulationOS</div>', unsafe_allow_html=True)
    st.markdown("**AI-Powered Scientific Workflow Planning for Pharmaceutical Research**")
    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")

        # LLM Settings
        st.subheader("LLM Settings")
        llm_mode = st.radio(
            "LLM Mode",
            ["MiniMax M3", "Mock (Testing)"],
            index=0 if st.session_state.client.__class__.__name__ == "MiniMaxClient" else 1
        )

        # Tool Library
        st.subheader("📚 Available Tools")
        st.write(f"**{len(list(st.session_state.registry))} tools loaded:**")
        for tool in st.session_state.registry:
            st.markdown(f'<div class="tool-badge">{tool.name}</div>', unsafe_allow_html=True)

        st.markdown("---")

        # Workflow Search Settings
        st.subheader("🔍 Workflow Search")
        use_search = st.checkbox("Enable Multi-Candidate Search", value=False)
        if use_search:
            n_candidates = st.slider("Number of Candidates", 2, 5, 3)
        else:
            n_candidates = 1

    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📝 Planning", "🎯 Execution", "📊 Results"])

    with tab1:
        render_planning_tab(use_search, n_candidates)

    with tab2:
        render_execution_tab()

    with tab3:
        render_results_tab()


def render_planning_tab(use_search: bool, n_candidates: int):
    """Render the workflow planning tab."""
    st.header("Workflow Planning")

    # User query input
    query = st.text_area(
        "Enter your research query:",
        placeholder="Example: Design an oral formulation for ibuprofen 200mg tablet",
        height=100
    )

    # Optional context
    with st.expander("➕ Additional Context (Optional)"):
        drug_name = st.text_input("Drug Name", "")
        target_dose = st.number_input("Target Dose (mg)", min_value=0.0, value=0.0)
        dosage_form = st.selectbox(
            "Dosage Form",
            ["", "tablet", "capsule", "suspension", "injection"]
        )

    # Plan button
    col1, col2 = st.columns([1, 4])
    with col1:
        plan_button = st.button("🚀 Generate Workflow", type="primary", use_container_width=True)

    if plan_button and query:
        # Build context
        context = {}
        if drug_name:
            context["drug_name"] = drug_name
        if target_dose > 0:
            context["target_dose_mg"] = target_dose
        if dosage_form:
            context["dosage_form"] = dosage_form

        with st.spinner("Planning workflow..."):
            if use_search:
                # Multi-candidate search
                search_engine = WorkflowSearchEngine(
                    st.session_state.planner,
                    st.session_state.registry,
                    n_candidates=n_candidates
                )
                candidates = search_engine.search(query, context)
                st.session_state.workflow_candidates = candidates
                st.session_state.workflow_plan = candidates[0].plan if candidates else None
                st.success(f"✅ Generated {len(candidates)} workflow candidates!")
            else:
                # Single workflow
                plan = st.session_state.planner.plan(query, context)
                st.session_state.workflow_plan = plan
                st.session_state.workflow_candidates = None
                if plan:
                    st.success("✅ Workflow generated successfully!")
                else:
                    st.error("❌ Failed to generate workflow")

    # Display workflow candidates
    if st.session_state.workflow_candidates:
        st.markdown("---")
        st.subheader("🔍 Workflow Candidates")

        for candidate in st.session_state.workflow_candidates:
            with st.expander(
                f"**Rank {candidate.rank}** - Score: {candidate.score:.2f} "
                f"({len(candidate.plan['workflow'])} steps)",
                expanded=(candidate.rank == 1)
            ):
                # Metrics
                cols = st.columns(5)
                for i, (metric_name, metric_value) in enumerate(candidate.metrics.items()):
                    with cols[i]:
                        st.metric(metric_name.replace("_", " ").title(), f"{metric_value:.2f}")

                st.markdown("**Rationale:**")
                st.write(candidate.plan.get("rationale", "N/A"))

                st.markdown("**Workflow Steps:**")
                for step in candidate.plan["workflow"]:
                    st.markdown(f"- **{step['step_id']}**: {step['tool']} - {step['goal']}")

                if st.button(f"Select Candidate {candidate.rank}", key=f"select_{candidate.rank}"):
                    st.session_state.selected_candidate = candidate.rank - 1
                    st.session_state.workflow_plan = candidate.plan
                    st.success(f"✅ Selected Candidate {candidate.rank}")
                    st.rerun()

    # Display selected workflow
    elif st.session_state.workflow_plan:
        st.markdown("---")
        display_workflow_plan(st.session_state.workflow_plan)


def display_workflow_plan(plan):
    """Display a workflow plan."""
    st.subheader("📋 Generated Workflow")

    st.markdown("**Rationale:**")
    st.info(plan.get("rationale", "N/A"))

    # DAG Visualization
    st.markdown("**Workflow DAG:**")
    try:
        from formulation_os.ui.dag_visualization import visualize_workflow_dag
        visualize_workflow_dag(plan["workflow"])
    except Exception as e:
        st.warning(f"Could not render DAG: {e}")
        st.caption("Install graphviz: pip install graphviz")

    st.markdown("**Workflow Steps:**")
    for step in plan["workflow"]:
        with st.container():
            st.markdown(f'<div class="workflow-step">', unsafe_allow_html=True)
            st.markdown(f"**{step['step_id']}**: {step['tool']}")
            st.write(f"Goal: {step['goal']}")
            if step.get("depends_on"):
                st.caption(f"Depends on: {', '.join(step['depends_on'])}")
            st.markdown('</div>', unsafe_allow_html=True)


def render_execution_tab():
    """Render the workflow execution tab."""
    st.header("Workflow Execution")

    if not st.session_state.workflow_plan:
        st.warning("⚠️ Please generate a workflow in the Planning tab first.")
        return

    # Display workflow overview
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Workflow Overview")
        st.write(f"**Total Steps:** {len(st.session_state.workflow_plan['workflow'])}")
        st.write(f"**Rationale:** {st.session_state.workflow_plan.get('rationale', 'N/A')[:100]}...")

    with col2:
        # Execution controls
        st.subheader("Controls")
        execute_button = st.button("▶️ Execute Workflow", type="primary", use_container_width=True)

    # Execute workflow
    if execute_button:
        with st.spinner("Executing workflow..."):
            # Build initial inputs
            initial_inputs = {
                "drug_name": "Ibuprofen",
                "target_dose_mg": 200,
                "dosage_form": "tablet"
            }

            # Execute
            try:
                results = st.session_state.orchestrator.execute_workflow(
                    st.session_state.workflow_plan["workflow"],
                    initial_inputs
                )
                st.session_state.execution_results = results
                st.success("✅ Workflow executed successfully!")
            except Exception as e:
                st.error(f"❌ Execution failed: {e}")
                return

    # Display execution progress
    if st.session_state.execution_results:
        st.markdown("---")
        st.subheader("Execution Results")

        # Overall status
        overall_status = st.session_state.execution_results.get("overall_status", "unknown")
        if overall_status == "OK":
            st.success(f"✅ Status: {overall_status}")
        else:
            st.error(f"❌ Status: {overall_status}")

        # Progress visualization
        from formulation_os.ui.dag_visualization import visualize_execution_progress
        completed_steps = set()
        for step_result in st.session_state.execution_results.get("step_results", []):
            if step_result.get("status") == "ok":
                # Extract step_id from tool name or use index
                completed_steps.add(f"step_{len(completed_steps) + 1}")

        visualize_execution_progress(
            st.session_state.workflow_plan["workflow"],
            completed_steps
        )

        # Step-by-step results
        st.markdown("---")
        st.subheader("Step-by-Step Results")

        for i, step_result in enumerate(st.session_state.execution_results.get("step_results", [])):
            with st.expander(
                f"**Step {i+1}**: {step_result.get('tool', 'Unknown')} - "
                f"{'✅' if step_result.get('status') == 'ok' else '❌'}",
                expanded=(i == 0)
            ):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Status", step_result.get("status", "unknown"))
                with col2:
                    st.metric("Duration", f"{step_result.get('duration_ms', 0):.1f}ms")
                with col3:
                    st.metric("Version", step_result.get("version", "N/A"))

                # Summary
                if step_result.get("summary"):
                    st.markdown("**Summary:**")
                    st.info(step_result["summary"])

                # Warnings
                if step_result.get("warnings"):
                    st.markdown("**Warnings:**")
                    for warning in step_result["warnings"]:
                        st.warning(warning)

                # Output data (collapsed)
                with st.expander("Show output data"):
                    st.json(step_result.get("output", {}))


def render_results_tab():
    """Render the results visualization tab."""
    st.header("Execution Results")

    if not st.session_state.execution_results:
        st.warning("⚠️ No execution results yet. Execute a workflow first.")
        return

    results = st.session_state.execution_results

    # Summary metrics
    st.subheader("📊 Summary Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Overall Status",
            results.get("overall_status", "Unknown"),
            delta=None,
            delta_color="normal"
        )

    with col2:
        total_steps = len(results.get("step_results", []))
        st.metric("Total Steps", total_steps)

    with col3:
        success_steps = sum(
            1 for step in results.get("step_results", [])
            if step.get("status") == "ok"
        )
        st.metric("Successful", success_steps)

    with col4:
        total_duration = sum(
            step.get("duration_ms", 0)
            for step in results.get("step_results", [])
        )
        st.metric("Total Time", f"{total_duration:.1f}ms")

    # Timeline visualization
    st.markdown("---")
    st.subheader("⏱️ Execution Timeline")

    from formulation_os.ui.dag_visualization import visualize_workflow_timeline

    # Add execution info to workflow
    workflow_with_execution = []
    for i, step in enumerate(st.session_state.workflow_plan.get("workflow", [])):
        step_copy = dict(step)
        if i < len(results.get("step_results", [])):
            step_result = results["step_results"][i]
            step_copy["status"] = step_result.get("status", "unknown")
            step_copy["duration_ms"] = step_result.get("duration_ms", 0)
        workflow_with_execution.append(step_copy)

    visualize_workflow_timeline(workflow_with_execution)

    # Aggregated results
    st.markdown("---")
    st.subheader("📋 Aggregated Results")

    # Collect all outputs
    all_outputs = {}
    for i, step_result in enumerate(results.get("step_results", [])):
        tool_name = step_result.get("tool", f"Step{i+1}")
        output = step_result.get("output", {})

        if output:
            with st.expander(f"**{tool_name}** Output"):
                # Display key findings
                if "summary" in output:
                    st.info(f"**Summary:** {output['summary']}")

                # Display warnings
                if "warnings" in output and output["warnings"]:
                    for warning in output["warnings"]:
                        st.warning(warning)

                # Display key-value pairs
                st.markdown("**Output Data:**")
                for key, value in output.items():
                    if key not in ["summary", "warnings"]:
                        if isinstance(value, (str, int, float, bool)):
                            st.write(f"- **{key}:** {value}")

                # Full JSON
                with st.expander("View full JSON"):
                    st.json(output)

    # Export results
    st.markdown("---")
    st.subheader("💾 Export Results")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📄 Download as JSON"):
            import json
            json_str = json.dumps(results, indent=2)
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name="workflow_results.json",
                mime="application/json"
            )

    with col2:
        if st.button("📊 Generate Report"):
            st.info("Report generation feature coming soon...")


if __name__ == "__main__":
    main()
