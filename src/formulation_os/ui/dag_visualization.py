"""DAG Visualization for Streamlit UI

Visualizes workflow DAG using graphviz or plotly.
"""

import streamlit as st
from typing import Any


def visualize_workflow_dag(workflow: list[dict[str, Any]]) -> None:
    """Visualize workflow as a DAG using graphviz.

    Args:
        workflow: List of workflow steps
    """
    try:
        import graphviz
    except ImportError:
        st.error("graphviz library not installed. Install with: pip install graphviz")
        return

    # Create directed graph
    dot = graphviz.Digraph(comment='Workflow DAG')
    dot.attr(rankdir='TB')  # Top to bottom
    dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue')

    # Add nodes
    for step in workflow:
        step_id = step.get("step_id", "unknown")
        tool = step.get("tool", "Unknown")
        goal = step.get("goal", "")

        # Truncate goal if too long
        if len(goal) > 40:
            goal = goal[:37] + "..."

        label = f"{step_id}\\n{tool}\\n{goal}"
        dot.node(step_id, label)

    # Add edges (dependencies)
    for step in workflow:
        step_id = step.get("step_id", "unknown")
        depends_on = step.get("depends_on", [])

        for dep in depends_on:
            dot.edge(dep, step_id)

    # Render in Streamlit
    st.graphviz_chart(dot)


def visualize_workflow_timeline(workflow: list[dict[str, Any]]) -> None:
    """Visualize workflow execution as a timeline.

    Args:
        workflow: List of workflow steps with execution info
    """
    import pandas as pd

    # Extract execution data
    timeline_data = []
    for step in workflow:
        step_id = step.get("step_id", "unknown")
        tool = step.get("tool", "Unknown")
        status = step.get("status", "pending")
        duration = step.get("duration_ms", 0)

        timeline_data.append({
            "Step": step_id,
            "Tool": tool,
            "Status": status,
            "Duration (ms)": duration
        })

    df = pd.DataFrame(timeline_data)

    # Display as table
    st.dataframe(df, use_container_width=True)

    # Display as bar chart
    if df["Duration (ms)"].sum() > 0:
        st.bar_chart(df.set_index("Step")["Duration (ms)"])


def visualize_execution_progress(
    workflow: list[dict[str, Any]],
    completed_steps: set[str]
) -> None:
    """Show execution progress with step status indicators.

    Args:
        workflow: List of workflow steps
        completed_steps: Set of completed step IDs
    """
    total_steps = len(workflow)
    completed_count = len(completed_steps)

    # Progress bar
    st.progress(completed_count / total_steps if total_steps > 0 else 0)
    st.caption(f"Progress: {completed_count}/{total_steps} steps completed")

    # Step status
    for step in workflow:
        step_id = step.get("step_id", "unknown")
        tool = step.get("tool", "Unknown")
        goal = step.get("goal", "")

        if step_id in completed_steps:
            st.success(f"✅ {step_id}: {tool} - {goal}")
        else:
            st.info(f"⏳ {step_id}: {tool} - {goal}")
