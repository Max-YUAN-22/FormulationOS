"""Streamlit UI for FormulationOS (Task 6).

A thin presentation layer over :class:`~formulation_os.orchestrator.Orchestrator`
and :class:`~formulation_os.report.Report`. The UI is intentionally a single
page with no chat history, no streaming, and no DAG visualization. Those are
future work.

Run with::

    pip install -e ".[ui]"
    streamlit run src/formulation_os/ui/app.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from formulation_os.core.tool import Tool
from formulation_os.orchestrator import Orchestrator
from formulation_os.planner import RuleBasedPlanner
from formulation_os.registry import ToolRegistry
from formulation_os.report import Report

# Path to the built-in tools directory, resolved relative to this file so the
# app works regardless of the working directory `streamlit run` is invoked from.
APP_DIR = Path(__file__).resolve().parent
BUILTINS_DIR = APP_DIR.parent / "tools" / "builtins"

# Optional dependency — Streamlit is only needed when actually serving the UI.
try:
    import streamlit as st

    _STREAMLIT_AVAILABLE = True
except ImportError:  # pragma: no cover — exercised in CI when streamlit absent
    st = None  # type: ignore[assignment]
    _STREAMLIT_AVAILABLE = False


__all__ = [
    "APP_DIR",
    "BUILTINS_DIR",
    "build_orchestrator",
    "main",
    "tool_card_data",
]


# --------------------------------------------------------------------------- #
# Helpers (Streamlit-free, unit-testable)                                     #
# --------------------------------------------------------------------------- #


def tool_card_data(tool: Tool) -> dict[str, Any]:
    """Return displayable metadata for a Tool without touching Streamlit.

    Used by the sidebar renderer and by unit tests. The returned dict is
    plain JSON-serializable data; the Streamlit app decides how to lay it out.
    """
    return {
        "name": tool.name,
        "version": tool.version,
        "description": tool.description,
        "domain": tool.spec.semantics.domain or "—",
        "capabilities": list(tool.capabilities),
        "is_mock": tool.spec.mock,
    }


def build_orchestrator(tools_dir: Path | None = None) -> Orchestrator:
    """Construct an :class:`Orchestrator` wired to the built-in mock Tools.

    Args:
        tools_dir: Optional override for the built-ins directory. Defaults
            to the in-tree ``BUILTINS_DIR``.
    """
    tools_dir = tools_dir or BUILTINS_DIR
    registry = ToolRegistry(tools_dir).load_all()
    return Orchestrator(RuleBasedPlanner(registry), registry)


# Streamlit-cached orchestrator. Defined at module level so that
# ``@st.cache_resource`` can wrap it; falls back to a plain function when
# Streamlit isn't installed so the module remains importable in CI.
if _STREAMLIT_AVAILABLE:
    @st.cache_resource(show_spinner=False)  # type: ignore[misc]
    def _cached_orchestrator() -> Orchestrator:
        return build_orchestrator()
else:  # pragma: no cover
    def _cached_orchestrator() -> Orchestrator:
        return build_orchestrator()


# --------------------------------------------------------------------------- #
# Streamlit entry point                                                       #
# --------------------------------------------------------------------------- #


# Example queries that route cleanly with the RuleBasedPlanner. Surfaced as
# defaults in the query input so first-time users see something working.
_EXAMPLE_QUERIES: tuple[str, ...] = (
    "Find recent literature review on solubility",
    "I want to formulate ibuprofen as a tablet",
    "What is the bioavailability of caffeine?",
    "Predict solubility of naproxen",
)


def main() -> None:
    """Streamlit entry point. Renders the full UI."""
    if not _STREAMLIT_AVAILABLE:
        raise RuntimeError(
            "Streamlit is not installed. Install with: pip install -e '.[ui]'"
        )

    st.set_page_config(
        page_title="FormulationOS",
        page_icon="🧪",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🧪 FormulationOS")
    st.caption(
        "A Scientific Operating System for Computational Pharmaceutics — v0.1 prototype"
    )

    orch = _cached_orchestrator()
    _render_sidebar(orch)
    _render_main(orch)


def _render_sidebar(orch: Orchestrator) -> None:
    """Sidebar: list the Tools loaded in the registry."""
    with st.sidebar:
        st.header("Available Tools")
        st.caption(f"{len(orch.registry)} tools loaded from registry")
        for tool in orch.registry:
            data = tool_card_data(tool)
            with st.expander(f"**{data['name']}** v{data['version']}"):
                st.write(data["description"])
                st.caption(f"**Domain:** `{data['domain']}`")
                caps = data["capabilities"]
                st.caption(f"**Capabilities:** {', '.join(caps) if caps else '—'}")
                if data["is_mock"]:
                    st.caption("🧪 *Mock implementation*")

        st.divider()
        st.caption("FormulationOS v0.1.0 · MVP prototype")


def _render_main(orch: Orchestrator) -> None:
    """Main panel: query input, Run button, and the rendered Report."""
    st.subheader("Try a query")

    col_input, col_button = st.columns([4, 1])
    with col_input:
        query = st.text_input(
            "Query",
            value=_EXAMPLE_QUERIES[0],
            label_visibility="collapsed",
            placeholder="Ask a pharmaceutics question…",
        )
    with col_button:
        run_clicked = st.button(
            "Run ▶", type="primary", use_container_width=True
        )

    if run_clicked and query.strip():
        with st.spinner("Planning and executing…"):
            report = orch.run(query.strip(), top_k=1)
        _render_report(report)


# Status pill colors used in the report header.
_STATUS_ICONS: dict[str, str] = {
    "ok": "🟢",
    "partial": "🟡",
    "error": "🔴",
    "no_match": "⚪",
}


def _render_report(report: Report) -> None:
    """Render a :class:`Report` as Streamlit components."""
    st.divider()

    icon = _STATUS_ICONS.get(report.status, "•")
    st.subheader(f"{icon} Report — {report.status.upper()}")
    st.caption(
        f"Generated {report.produced_at.strftime('%Y-%m-%d %H:%M:%S UTC')} · "
        f"{len(report.tool_results)} tool(s) executed"
    )

    if not report.tool_results:
        st.info("No tools matched this query. Try rephrasing or broadening it.")
    else:
        for tr in report.tool_results:
            with st.container(border=True):
                col_a, col_b, col_c = st.columns([3, 1, 1])
                with col_a:
                    st.markdown(f"### {tr.tool_name} v{tr.tool_version}")
                with col_b:
                    st.caption(f"Status: **{tr.status}**")
                with col_c:
                    st.caption(f"{tr.duration_ms:.2f} ms")

                if tr.error:
                    st.error(f"**Error:** {tr.error}")
                for w in tr.warnings:
                    st.warning(w)

                with st.expander("Input", expanded=False):
                    st.json(tr.input)
                with st.expander("Output", expanded=True):
                    st.json(tr.output)

    with st.expander("Raw Markdown", expanded=False):
        st.code(report.to_markdown(), language="markdown")


if __name__ == "__main__":  # pragma: no cover
    main()
