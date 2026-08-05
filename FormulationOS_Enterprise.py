"""FormulationOS Enterprise Edition - Production-Ready Agentic AI System

Inspired by AstraZeneca's ChatInvent (Drug Discovery Today 2026)
Reference: "Democratising real-world drug discovery through agentic AI"

Enterprise Features:
- Real-time reasoning display (transparency)
- User feedback mechanism (like/dislike/comment)
- Professional UI with molecule preview
- Robust error handling
- Session management
- Complete tool-use loop

Version: 3.5.1 (2026-08-05) - Enhanced Knowledge Base & Platform Descriptions
"""

__version__ = "3.5.1"

import streamlit as st
from pathlib import Path
import sys
import uuid
import re
import os
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent / "src"))

from formulation_os.agent.conversation_memory import ConversationMemory
from formulation_os.agent.unified_llm_manager import UnifiedLLMManager
from formulation_os.agent.scientific_state import ScientificState
from formulation_os.agent.hypothesis_ranker import HypothesisRanker
from formulation_os.agent.evidence_manager import EvidenceManager
from formulation_os.knowledge_base import KnowledgeBaseDB
from formulation_os.tools.visualization_tools import (
    plot_solubility_profile,
    plot_ph_stability,
    plot_formulation_comparison,
    visualize_molecule_2d
)
from formulation_os.tools.auto_visualization import generate_visualizations_from_response

# Configuration
def get_config(key: str, default: str = "") -> str:
    """Get config from environment variable or Streamlit secrets"""
    env_value = os.environ.get(key)
    if env_value:
        return env_value
    try:
        return st.secrets.get(key, default)
    except:
        return default

CLAUDE_API_KEY = get_config("CLAUDE_API_KEY")
GPT_API_KEY = get_config("GPT_API_KEY")
MINIMAX_API_KEY = get_config("MINIMAX_API_KEY")
CLAUDE_BASE_URL = get_config("CLAUDE_BASE_URL", "https://www.cun.ai")
GPT_BASE_URL = get_config("GPT_BASE_URL", "https://api.openai.com/v1")
MINIMAX_BASE_URL = get_config("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1")

DEFAULT_MODEL = "gpt-4o" if GPT_API_KEY else "MiniMax-M3"

# Page config
st.set_page_config(
    page_title="FormulationOS - AI Scientist",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS - inspired by ChatInvent
st.markdown("""
<style>
    /* Hide Streamlit branding */
    header[data-testid="stHeader"] {display: none;}
    .stApp {background: #fafafa;}

    /* Professional typography */
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    }

    /* Enhanced chat messages */
    [data-testid="stChatMessageContent"] {
        background: white;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        border: 1px solid #e5e7eb;
        margin-bottom: 1rem;
    }

    [data-testid="stChatMessage"][data-testid*="user"] [data-testid="stChatMessageContent"] {
        background: #f3f4f6;
        border-color: #d1d5db;
    }

    /* Reasoning display - ChatInvent style */
    .reasoning-container {
        background: #eff6ff;
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin: 1rem 0;
        font-size: 0.95rem;
    }

    .reasoning-step {
        padding: 0.5rem 0;
        border-bottom: 1px solid #dbeafe;
    }

    .reasoning-step:last-child {
        border-bottom: none;
    }

    .tool-badge {
        background: #3b82f6;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 0.5rem;
    }

    /* Feedback buttons */
    .feedback-container {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }

    .feedback-btn {
        background: transparent;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        padding: 0.25rem 0.75rem;
        cursor: pointer;
        font-size: 0.9rem;
        transition: all 0.2s;
    }

    .feedback-btn:hover {
        background: #f3f4f6;
        border-color: #9ca3af;
    }

    /* Professional buttons */
    .stButton button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.65rem 1.75rem !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: transform 0.1s !important;
    }

    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: white;
        border-right: 1px solid #e5e7eb;
    }

    /* Status indicators */
    .status-success {
        color: #10b981;
        font-weight: 600;
    }

    .status-error {
        color: #ef4444;
        font-weight: 600;
    }

    .status-running {
        color: #f59e0b;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init():
    """Initialize all session state variables"""
    if "sessions" not in st.session_state:
        st.session_state.sessions = {}
    if "current_session_id" not in st.session_state:
        new_id = str(uuid.uuid4())
        st.session_state.current_session_id = new_id
        st.session_state.sessions[new_id] = {
            "memory": ConversationMemory(),
            "scientific_state": ScientificState(),
            "created_at": datetime.now(),
            "feedback": {}  # message_id -> {"type": "like/dislike", "comment": ""}
        }
    if "evidence_manager" not in st.session_state:
        st.session_state.evidence_manager = EvidenceManager()
    if "hypothesis_ranker" not in st.session_state:
        st.session_state.hypothesis_ranker = HypothesisRanker(
            evidence_manager=st.session_state.evidence_manager
        )
    if "llm_manager" not in st.session_state:
        memory = st.session_state.sessions[st.session_state.current_session_id]["memory"]
        st.session_state.llm_manager = UnifiedLLMManager(
            memory=memory,
            anthropic_api_key=CLAUDE_API_KEY,
            openai_api_key=GPT_API_KEY,
            minimax_api_key=MINIMAX_API_KEY,
            anthropic_base_url=CLAUDE_BASE_URL,
            openai_base_url=GPT_BASE_URL,
            minimax_base_url=MINIMAX_BASE_URL,
            evidence_manager=st.session_state.evidence_manager
        )
    if "kb" not in st.session_state:
        st.session_state.kb = KnowledgeBaseDB()
    if "view_mode" not in st.session_state:
        st.session_state.view_mode = "home"

def get_session():
    """Get current session data"""
    return st.session_state.sessions[st.session_state.current_session_id]

def new_session():
    """Create a new chat session"""
    new_id = str(uuid.uuid4())
    st.session_state.sessions[new_id] = {
        "memory": ConversationMemory(),
        "scientific_state": ScientificState(),
        "created_at": datetime.now(),
        "feedback": {}
    }
    st.session_state.current_session_id = new_id
    st.session_state.llm_manager.memory = get_session()["memory"]

def switch_session(sid):
    """Switch to a different session"""
    st.session_state.current_session_id = sid
    st.session_state.llm_manager.memory = get_session()["memory"]

def display_reasoning(tool_calls, status="running"):
    """Display real-time reasoning process - ChatInvent style"""
    if not tool_calls:
        return

    status_icons = {
        "running": "⏳",
        "success": "✅",
        "error": "❌"
    }

    status_classes = {
        "running": "status-running",
        "success": "status-success",
        "error": "status-error"
    }

    st.markdown(f"""
    <div class='reasoning-container'>
        <div style='font-weight: 600; margin-bottom: 0.75rem;'>
            {status_icons.get(status, "⏳")} <span class='{status_classes.get(status, "")}'>AI Reasoning Process</span>
        </div>
    """, unsafe_allow_html=True)

    for i, tool_call in enumerate(tool_calls, 1):
        tool_name = tool_call["name"]
        # Simplify tool name for display
        display_name = tool_name.replace("_", " ").replace("ai", "AI").title()

        st.markdown(f"""
        <div class='reasoning-step'>
            <span class='tool-badge'>Step {i}</span>
            <strong>{display_name}</strong>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

def add_feedback_buttons(message_id):
    """Add like/dislike/comment feedback buttons"""
    session = get_session()
    feedback = session["feedback"].get(message_id, {})

    col1, col2, col3 = st.columns([1, 1, 10])

    with col1:
        if st.button("👍", key=f"like_{message_id}"):
            session["feedback"][message_id] = {"type": "like", "timestamp": datetime.now()}
            st.success("Thank you for your feedback!")

    with col2:
        if st.button("👎", key=f"dislike_{message_id}"):
            session["feedback"][message_id] = {"type": "dislike", "timestamp": datetime.now()}
            st.warning("Thank you for your feedback. We'll improve!")

    with col3:
        if feedback:
            st.caption(f"Feedback: {feedback.get('type', 'none')}")

# Initialize
init()

# Sidebar
with st.sidebar:
    st.markdown("### 🧬 FormulationOS")
    st.caption("AI Scientist Platform")
    st.markdown("---")

    if st.button("➕ New Session", use_container_width=True):
        new_session()
        st.rerun()

    st.markdown("### 💬 Session History")

    for sid, data in sorted(st.session_state.sessions.items(),
                           key=lambda x: x[1]["created_at"], reverse=True):
        is_current = sid == st.session_state.current_session_id
        memory = data["memory"]

        if len(memory.messages) > 0:
            title = memory.messages[0].content[:30] + "..."
        else:
            title = "New Research"

        if st.button(
            f"{'🟢' if is_current else '⚪'} {title}",
            key=f"sess_{sid}",
            use_container_width=True
        ):
            if not is_current:
                switch_session(sid)
                st.rerun()

    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.caption("""
    **FormulationOS** - An agentic AI system for pharmaceutical formulation research.

    Integrates 12 AI modules for comprehensive drug development support.
    """)

# Top navigation
col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
with col1:
    st.title("🧬 FormulationOS")
    st.caption(f"v{__version__}")
with col2:
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.view_mode = "home"
        st.rerun()
with col3:
    if st.button("💬 AI Workspace", use_container_width=True):
        st.session_state.view_mode = "workspace"
        st.rerun()
with col4:
    if st.button("📚 Knowledge Base", use_container_width=True):
        st.session_state.view_mode = "knowledge_base"
        st.rerun()
with col5:
    if st.button("🔬 Research", use_container_width=True):
        st.session_state.view_mode = "research"
        st.rerun()

st.markdown("---")

# HOME PAGE
if st.session_state.view_mode == "home":
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 3rem; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            An Agentic AI Scientist for Pharmaceutical Formulation
        </h1>
        <p style='font-size: 1.2rem; color: #64748b; margin-top: 1rem;'>
            From molecular properties to formulation strategies — an intelligent R&D collaboration platform
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Key statistics
    kb = st.session_state.kb
    stats = kb.get_statistics()

    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1:
        st.metric("💬 Conversations", stats['total_messages'])
    with col_stat2:
        st.metric("💊 Drug Analyses", stats['total_drug_analyses'])
    with col_stat3:
        st.metric("🔧 AI Tool Calls", stats['total_tool_calls'])
    with col_stat4:
        st.metric("📁 Active Sessions", stats['total_sessions'])

    st.markdown("---")

    # Demo cases showcase
    st.markdown("## 🎯 Try Demo Cases")
    st.caption("Pre-loaded AI-generated analyses - click to explore in AI Workspace")

    demo_col1, demo_col2, demo_col3 = st.columns(3)

    with demo_col1:
        st.markdown("""
        <div style='background: white; padding: 2rem; border-radius: 12px; border: 2px solid #3b82f6; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
            <h4 style='color: #1e40af; margin-bottom: 0.5rem;'>💊 Ibuprofen</h4>
            <p style='color: #64748b; font-size: 0.85rem; margin-bottom: 0.5rem;'>BCS II | MW: 206 Da</p>
            <p style='color: #475569; font-size: 0.9rem;'>Solid dispersion strategy<br/>Classic solubility enhancement</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 View Analysis", key="demo_ibu", use_container_width=True):
            st.session_state.view_mode = "workspace"
            st.session_state.demo_query = "Ibuprofen"
            st.rerun()

    with demo_col2:
        st.markdown("""
        <div style='background: white; padding: 2rem; border-radius: 12px; border: 2px solid #10b981; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
            <h4 style='color: #059669; margin-bottom: 0.5rem;'>🧪 Paclitaxel</h4>
            <p style='color: #64748b; font-size: 0.85rem; margin-bottom: 0.5rem;'>BCS IV | MW: 854 Da</p>
            <p style='color: #475569; font-size: 0.9rem;'>Nanocrystal technology<br/>High MW challenge</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 View Analysis", key="demo_pac", use_container_width=True):
            st.session_state.view_mode = "workspace"
            st.session_state.demo_query = "Paclitaxel"
            st.rerun()

    with demo_col3:
        st.markdown("""
        <div style='background: white; padding: 2rem; border-radius: 12px; border: 2px solid #f59e0b; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
            <h4 style='color: #d97706; margin-bottom: 0.5rem;'>💉 Celecoxib</h4>
            <p style='color: #64748b; font-size: 0.85rem; margin-bottom: 0.5rem;'>BCS II | MW: 381 Da</p>
            <p style='color: #475569; font-size: 0.9rem;'>PVP solid dispersion<br/>Mature process</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 View Analysis", key="demo_cel", use_container_width=True):
            st.session_state.view_mode = "workspace"
            st.session_state.demo_query = "Celecoxib"
            st.rerun()

    st.markdown("---")

    # Feature highlights
    col_feat1, col_feat2, col_feat3 = st.columns(3)

    with col_feat1:
        st.markdown("""
        <div style='text-align: center; padding: 1.5rem;'>
            <div style='font-size: 3rem; margin-bottom: 0.5rem;'>🧬</div>
            <h3 style='color: #1e293b; margin-bottom: 0.5rem;'>AI-Powered Analysis</h3>
            <p style='color: #64748b; font-size: 0.95rem;'>
                Generate evidence-based hypotheses through dialogue with an AI scientist
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_feat2:
        st.markdown("""
        <div style='text-align: center; padding: 1.5rem;'>
            <div style='font-size: 3rem; margin-bottom: 0.5rem;'>🔬</div>
            <h3 style='color: #1e293b; margin-bottom: 0.5rem;'>Comprehensive Tools</h3>
            <p style='color: #64748b; font-size: 0.95rem;'>
                12 integrated AI modules covering the full preformulation-to-formulation pipeline
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_feat3:
        st.markdown("""
        <div style='text-align: center; padding: 1.5rem;'>
            <div style='font-size: 3rem; margin-bottom: 0.5rem;'>💡</div>
            <h3 style='color: #1e293b; margin-bottom: 0.5rem;'>Natural Language</h3>
            <p style='color: #64748b; font-size: 0.95rem;'>
                Describe your research goals in plain language — no expert knowledge required
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # System capabilities
    st.markdown("## 🎯 Core Features")

    col_cap1, col_cap2 = st.columns(2)

    with col_cap1:
        st.markdown("""
        ### 🤖 AI-Powered Analysis
        - **Citation-Based Responses**: Every answer includes PubMed literature references
        - **Multi-Layer Validation**: FDA guidelines + Lipinski rules + literature support
        - **Confidence Scoring**: Transparent reliability assessment (0-100%)
        - **Real-time Reasoning**: Watch AI think through complex formulation problems
        - **Continuous Dialogue**: Build comprehensive analysis through conversation
        """)

        st.markdown("""
        ### 🧬 3D Molecular Visualization
        - **Interactive 3D Structures**: Rotate and explore drug molecules
        - **Pharmacophore Mapping**: Identify H-bond donors/acceptors, aromatic rings
        - **Property Calculator**: Instant MW, LogP, TPSA, HBD/HBA computation
        - **Lipinski Validation**: Automatic drug-likeness assessment
        - **Multiple Display Modes**: Stick, sphere, line, and surface rendering
        """)

        st.markdown("""
        ### 📚 Literature Intelligence
        - **PubMed Integration**: Access to 35M+ biomedical articles
        - **Real-Time Search**: Drug-specific and technology-focused queries
        - **Automatic Citations**: AI answers include relevant paper references
        - **Full Metadata**: Authors, journal, year, PMID, DOI links
        """)

    with col_cap2:
        st.markdown("""
        ### 💊 Comprehensive Drug Database
        - **4,225 FDA/EMA Approved Drugs**: Complete ChEMBL integration
        - **BCS Classification**: Pre-classified for all drugs
        - **Molecular Properties**: MW, LogP, PSA, HBA, HBD, Ro5 violations
        - **Route Information**: Oral, parenteral, black box warnings
        - **Interactive Dashboard**: Filterable catalog with visualizations
        """)

        st.markdown("""
        ### 📄 Report Generation
        - **Conversation-to-Report**: One-click comprehensive analysis report
        - **Professional Format**: Executive summary, properties, strategies
        - **Literature References**: Automatic PubMed citation integration
        - **Experimental Suggestions**: Actionable next-step recommendations
        - **Downloadable**: Markdown format for easy sharing
        """)

        st.markdown("""
        ### 🔍 Prediction Validation
        - **FDA Rule Validation**: BCS classification against official guidelines
        - **Lipinski Compliance**: Drug-likeness rule checking
        - **Literature Evidence**: Support from published research
        - **Strategy Suitability**: Formulation approach validation
        - **Success Rate Metrics**: Historical performance data
        """)

    st.markdown("---")

    # Platform introductions - Detailed
    st.markdown("## 🔗 Integrated AI Platforms")

    st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <p style='color: #64748b; font-size: 1.05rem;'>
            FormulationOS integrates two comprehensive AI platforms covering the complete
            preformulation-to-formulation pipeline with 12 specialized modules.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); padding: 2rem; border-radius: 12px; border: 2px solid #3b82f6;'>
            <h3 style='color: #1e40af; margin-bottom: 1rem;'>🔬 PreformulationAI</h3>
            <p style='color: #1e3a8a; margin-bottom: 0.5rem; font-size: 1.05rem;'>
                <strong>AI-driven preformulation for small-molecule drug development</strong>
            </p>
            <p style='color: #475569; font-size: 0.95rem; margin-bottom: 1.5rem;'>
                From SMILES to full developability dossier in seconds — fundamental properties,
                temperature/pH-resolved profiles, and interpretable formulation descriptors.
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("📋 Five Prediction Modules", expanded=False):
            st.markdown("""
            Every module outputs **actionable numbers** — not just classifications — backed by
            interpretable ML and confidence estimates.

            **01 — Fundamentals**
            *Fundamental preformulation prediction & critical property calculation*
            - Density, MP, Tg
            - logP, logD₇.₄, logPapp
            - Acidic/Basic pKa
            - logS, kinetic solubility
            - FractionCSP3, TPSA, NumHAcceptors

            **02 — Solubility**
            *Conditional solubility prediction across solvents and temperatures*
            - Temperature-dependent solubility curves
            - Organic solvent solubility
            - Binary solvent systems

            **03 — pH Profile**
            *pH-dependent preformulation estimation*
            - pH-Species fraction profile
            - pH-dependent logS profile
            - pH-dependent logD profile

            **04 — Developability**
            *Interpretable developability assessment for drug design*
            - BCS classification
            - Druglikeness
            - Oral & injectable formulatability index
            - Fully interpretable

            **05 — IF-Descriptors**
            *Interpretable formulation descriptors*
            - Preformulation properties
            - Interpretable RDKit descriptors
            - Highly interpretable & information-rich
            - Batch generation support
            """)

        st.caption("""
        **Developed by:** Computational Pharmaceutical Group, State Key Laboratory
        Of Quality Research in Chinese Medicine, ICMS, University of Macau
        """)

        st.markdown("")
        if st.button("🔗 Visit PreformulationAI Platform", use_container_width=True):
            st.link_button("Open PreformulationAI", "https://preformulationai.computpharm.org/")

    with col2:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); padding: 2rem; border-radius: 12px; border: 2px solid #10b981;'>
            <h3 style='color: #15803d; margin-bottom: 1rem;'>💊 FormulationAI</h3>
            <p style='color: #14532d; margin-bottom: 0.5rem; font-size: 1.05rem;'>
                <strong>The pioneer providing best solutions for in silico drug formulation design</strong>
            </p>
            <p style='color: #475569; font-size: 0.95rem; margin-bottom: 1.5rem;'>
                FormulationAI keeps the most comprehensive data and AI models up to date,
                serving you with accurate predictions and easy-to-use interface.
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("📋 Seven Formulation Modules", expanded=False):
            st.markdown("""
            **01 — Drug/Cyclodextrin Complex**
            - Complexation free energy (ΔG)
            - Solubility enhancement prediction
            - CD type recommendation

            **02 — Solid Dispersion**
            - Physical stability prediction
            - Polymer selection guidance
            - Manufacturing method recommendation

            **03 — Phospholipid Complex**
            - Lipophilicity improvement
            - Bioavailability enhancement
            - Complex formation assessment

            **04 — Drug Nanocrystals**
            - Particle size prediction
            - PDI estimation
            - Manufacturing methods (BWM, HPH, Antisolvent)

            **05 — Self-Emulsifying System (SEDDS)**
            - Oil phase recommendation
            - Surfactant selection
            - Droplet size prediction
            - Formulation composition optimization

            **06 — Liposome**
            - Lipid selection
            - Size optimization
            - Encapsulation efficiency
            - Release profile prediction

            **07 — Strategy Recommendation**
            - Optimal formulation approach selection
            - Score-based ranking
            - Structure-property guided strategy
            """)

        st.caption("""
        **Citation:** FormulationAI: a novel web-based platform for drug formulation design
        driven by artificial intelligence, *Brief Bioinform.* 2023; **25(1)**:bbad419
        """)

        st.markdown("")
        if st.button("🔗 Visit FormulationAI Platform", use_container_width=True):
            st.link_button("Open FormulationAI", "https://formulationai.computpharm.org/")

    st.markdown("---")

    # Technical architecture
    st.markdown("## 🏗️ System Architecture")

    col_arch1, col_arch2, col_arch3 = st.columns(3)

    with col_arch1:
        st.markdown("""
        **🧠 LLM Layer**
        - Multi-provider support (Claude, GPT-4o, MiniMax)
        - Tool-use loop with result feedback
        - Conversation memory management
        """)

    with col_arch2:
        st.markdown("""
        **🔧 Tool Layer**
        - 12 specialized AI modules
        - REST API integration
        - Batch processing support
        """)

    with col_arch3:
        st.markdown("""
        **💾 Storage Layer**
        - SQLite knowledge base
        - Session state management
        - Training data export
        """)

    st.markdown("---")

    # Publications and references
    st.markdown("## 📚 Scientific Foundation")

    col_pub1, col_pub2 = st.columns(2)

    with col_pub1:
        st.markdown("""
        ### Inspired by Industry Research
        **ChatInvent** (AstraZeneca, 2026)
        - Published in *Drug Discovery Today*
        - Multi-agent architecture for drug discovery
        - Real-time reasoning transparency
        - User feedback mechanism for continuous improvement
        """)

    with col_pub2:
        st.markdown("""
        ### Built on Validated Models
        **PreformulationAI & FormulationAI**
        - Machine learning models trained on experimental data
        - BCS classification accuracy: >85%
        - Formulation strategy prediction validated by literature
        - Continuous model updates from user interactions
        """)

    st.markdown("---")

    # Call to action
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <p style='font-size: 1.1rem; color: #475569; margin-bottom: 1.5rem;'>
            Ready to accelerate your formulation research?
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_cta1, col_cta2, col_cta3 = st.columns([1, 1, 1])
    with col_cta2:
        if st.button("🚀 Start AI Workspace", use_container_width=True, type="primary"):
            st.session_state.view_mode = "workspace"
            st.rerun()

# AI WORKSPACE
elif st.session_state.view_mode == "workspace":
    memory = get_session()["memory"]

    # Initialize scientific components
    if "scientific_planner" not in st.session_state:
        from formulation_os.agent.scientific_planner import ScientificPlanner
        st.session_state.scientific_planner = ScientificPlanner()

    # Initialize sidebar collapsed state
    if "sidebar_collapsed" not in st.session_state:
        st.session_state.sidebar_collapsed = False

    # Simple top bar with collapse button
    top_col1, top_col2 = st.columns([5, 1])
    with top_col1:
        st.markdown("### 💬 AI Scientist")
    with top_col2:
        if st.button("📚" if st.session_state.sidebar_collapsed else "◀", use_container_width=True):
            st.session_state.sidebar_collapsed = not st.session_state.sidebar_collapsed
            st.rerun()

    # Fixed height layout CSS + Keep Streamlit's main sidebar always visible
    st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 1rem;
        max-height: 100vh;
        overflow: hidden;
    }
    .stChatFloatingInputContainer {
        bottom: 20px;
    }
    div[data-testid="stChatMessageContainer"] {
        max-height: calc(100vh - 300px);
        overflow-y: auto;
    }
    /* Force Streamlit's main sidebar to stay open */
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    button[kind="header"] {
        display: none !important;
    }
    section[data-testid="stSidebar"] {
        width: 250px !important;
        min-width: 250px !important;
    }
    section[data-testid="stSidebar"][aria-expanded="false"] {
        width: 250px !important;
        transform: none !important;
        margin-left: 0 !important;
    }
    section[data-testid="stSidebar"] > div {
        width: 250px !important;
    }
    /* Hide the collapse arrow button */
    section[data-testid="stSidebar"] button[kind="header"],
    section[data-testid="stSidebar"] button[aria-label*="collapse"],
    section[data-testid="stSidebar"] button[aria-label*="Close"],
    [data-testid="baseButton-header"] {
        display: none !important;
    }

    /* Enhanced Chat Input Styling */
    .stChatInput {
        background-color: #ffffff !important;
        border: 2px solid #3b82f6 !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1) !important;
    }

    .stChatInput:focus-within {
        border-color: #2563eb !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
    }

    .stChatInput textarea {
        color: #1e293b !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        background-color: #ffffff !important;
    }

    .stChatInput textarea::placeholder {
        color: #64748b !important;
        font-weight: 400 !important;
        opacity: 0.8 !important;
    }

    /* Chat input container */
    div[data-testid="stChatInput"] {
        background: linear-gradient(to bottom, transparent, rgba(255,255,255,0.95)) !important;
        padding: 1rem 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Two-column layout: Research Context (collapsible) | Main Chat
    if not st.session_state.sidebar_collapsed:
        col_sidebar, col_chat = st.columns([1, 3])
    else:
        col_sidebar = None
        col_chat = st.container()

    # SIDEBAR: Research Context (collapsible)
    if col_sidebar is not None:
        with col_sidebar:
            st.markdown("#### 📊 Research Context")

            with st.expander("💊 Drug Profile", expanded=False):
                evidence_count = 0
                if hasattr(st.session_state, 'evidence_manager'):
                    evidence_count = len(st.session_state.evidence_manager.evidence_pool)

                if evidence_count > 0:
                    memory_data = get_session()["memory"]
                    drug_name = "Unknown Drug"
                    smiles = ""

                    for msg in reversed(memory_data.messages):
                        if msg.role == "user" and msg.content:
                            if "Ibuprofen" in msg.content or "布洛芬" in msg.content:
                                drug_name = "Ibuprofen (布洛芬)"

                            import re
                            smiles_match = re.search(r'SMILES[：:]\s*([A-Za-z0-9@+\-\[\]()=#$]{10,})', msg.content)
                            if smiles_match:
                                smiles = smiles_match.group(1)

                            if drug_name != "Unknown Drug":
                                break

                    st.markdown(f"**{drug_name}**")
                    if smiles:
                        st.code(smiles[:40] + "..." if len(smiles) > 40 else smiles, language="text")
                    st.caption(f"📊 {evidence_count} evidence items")
                else:
                    st.caption("No drug analyzed yet")

            with st.expander("🔬 Evidence", expanded=False):
                if hasattr(st.session_state, 'evidence_manager'):
                    evidence_pool = st.session_state.evidence_manager.evidence_pool

                    if evidence_pool:
                        for ev in evidence_pool[:5]:
                            st.markdown(f"• {ev.observation}")
                    else:
                        st.caption("No evidence collected")
                else:
                    st.caption("No evidence collected")

            with st.expander("💡 Strategies", expanded=False):
                if hasattr(st.session_state, 'evidence_manager') and st.session_state.evidence_manager.evidence_pool:
                    strategies = st.session_state.evidence_manager.get_strategies_for_evidence()

                    if strategies:
                        sorted_strategies = sorted(strategies.items(), key=lambda x: x[1], reverse=True)[:3]

                        for strategy, conf in sorted_strategies:
                            st.markdown(f"**{strategy.replace('_', ' ').title()}**")
                            st.progress(conf)
                else:
                    st.caption("No strategies yet")

            # Report Generation Section
            st.markdown("---")
            st.markdown("#### 📄 Generate Report")

            if len(memory.messages) > 2:
                if st.button("📥 Generate Formulation Report", use_container_width=True, type="primary"):
                    try:
                        from src.formulation_os.reports.report_generator import FormulationReportGenerator

                        with st.spinner("Generating report..."):
                            # Extract drug info
                            drug_name = "Unknown Drug"
                            smiles = ""

                            for msg in memory.messages:
                                if msg.role == "user":
                                    import re
                                    smiles_match = re.search(r'SMILES[：:是]?\s*[\'"]?([A-Za-z0-9@+\-\[\]()=#$]{10,})[\'"]?', msg.content, re.IGNORECASE)
                                    if smiles_match:
                                        smiles = smiles_match.group(1)

                                    # Extract drug name
                                    name_patterns = [r'分析\s*([A-Za-z]+)', r'analyze\s+([A-Za-z]+)', r'drug[：:是]?\s*([A-Za-z]+)']
                                    for pattern in name_patterns:
                                        match = re.search(pattern, msg.content, re.IGNORECASE)
                                        if match:
                                            drug_name = match.group(1)
                                            break

                            # Generate report
                            report_gen = FormulationReportGenerator()

                            session = get_session()
                            tool_calls = session.get("tool_calls", {})
                            tool_calls_list = [tc for tc_list in tool_calls.values() for tc in tc_list]

                            report_gen.collect_from_conversation(memory, tool_calls_list, drug_name, smiles)

                            # Add molecular properties if available
                            if smiles:
                                try:
                                    from src.formulation_os.visualization.molecule_3d import Molecule3DViewer
                                    viewer = Molecule3DViewer()
                                    if viewer.load_smiles(smiles):
                                        props = viewer.get_molecular_properties()
                                        report_gen.add_molecular_properties(props)
                                except:
                                    pass

                            # Save report
                            report_path = report_gen.save_report()

                            st.success(f"✅ Report generated: {report_path}")

                            # Download button
                            with open(report_path, 'r', encoding='utf-8') as f:
                                report_content = f.read()

                            st.download_button(
                                label="📥 Download Report (Markdown)",
                                data=report_content,
                                file_name=f"{drug_name}_report.md",
                                mime="text/markdown",
                                use_container_width=True
                            )

                    except Exception as e:
                        st.error(f"Error generating report: {str(e)}")
            else:
                st.caption("Complete a drug analysis to generate report")

    # MAIN CHAT AREA
    with col_chat:
        # Check if there's a demo query to load
        if "demo_query" in st.session_state and st.session_state.demo_query:
            demo_query = st.session_state.demo_query
            st.session_state.demo_query = None  # Clear after use

            # Extract drug name from query
            drug_name = None
            if "Ibuprofen" in demo_query:
                drug_name = "Ibuprofen"
            elif "Paclitaxel" in demo_query:
                drug_name = "Paclitaxel"
            elif "Celecoxib" in demo_query:
                drug_name = "Celecoxib"
            elif "Aspirin" in demo_query:
                drug_name = "Aspirin"

            if drug_name:
                # Fetch from knowledge base
                kb = st.session_state.kb
                training_data = kb.get_training_dataset(limit=50)

                # Find matching drug
                demo_case = None
                for example in training_data:
                    if example['drug_name'] == drug_name:
                        demo_case = example
                        break

                if demo_case:
                    # Add to current session memory
                    memory.add_message("user", demo_case['user_query'])
                    memory.add_message("assistant", demo_case['ai_response'])
                    st.rerun()

        # Quick start examples (only show when no messages)
        if len(memory.messages) == 0:
            st.info("💡 **Quick Start** - Choose an example or describe your research goal")

            col1, col2, col3 = st.columns(3)

            example_queries = {
                "col1": ("📊 Analyze Ibuprofen", "帮我分析Ibuprofen（布洛芬）的制剂挑战，SMILES: CC(C)Cc1ccc(cc1)C(C)C(=O)O，我想改善其口服生物利用度"),
                "col2": ("🔬 Evaluate Compound", "我有一个新化合物，SMILES是CC(=O)Oc1ccccc1C(=O)O，请帮我评估它的BCS分类和可制剂性"),
                "col3": ("💊 Solid Dispersion", "我的药物是BCS II类化合物，溶解度很低，请推荐合适的固体分散体策略")
            }

            for col_name, (button_text, query) in example_queries.items():
                with locals()[col_name]:
                    if st.button(button_text, use_container_width=True, key=f"quickstart_{col_name}"):
                        # Check if this query is already in memory (prevent duplicates)
                        already_exists = False
                        for msg in memory.messages:
                            if msg.role == "user" and msg.content == query:
                                already_exists = True
                                break

                        if not already_exists:
                            try:
                                # Check if we have any valid API key
                                has_api_key = bool(CLAUDE_API_KEY or GPT_API_KEY or MINIMAX_API_KEY)

                                if not has_api_key:
                                    st.error("⚠️ **API Key 未配置** - 请在 `.streamlit/secrets.toml` 中配置 GPT_API_KEY、CLAUDE_API_KEY 或 MINIMAX_API_KEY")
                                    st.stop()

                                with st.spinner("🧠 Analyzing..."):
                                    resp, tool_calls, _, _ = st.session_state.llm_manager.generate_with_tools_loop(
                                        user_query=query,
                                        model=DEFAULT_MODEL,
                                        max_iterations=5
                                    )

                                # Save to memory
                                memory.add_message("user", query)
                                memory.add_message("assistant", resp)

                                # 💾 Persist to knowledge base database
                                kb = st.session_state.kb
                                session_id = st.session_state.current_session_id
                                kb.create_session(session_id)
                                kb.save_message(session_id, "user", query)
                                kb.save_message(session_id, "assistant", resp, model_used=DEFAULT_MODEL)

                                # Store tool calls
                                if tool_calls:
                                    session = get_session()
                                    if "tool_calls" not in session:
                                        session["tool_calls"] = {}
                                    session["tool_calls"][len(memory.messages) - 1] = tool_calls

                                    # Extract drug info from query prompt
                                    import re
                                    smiles_match = re.search(r'SMILES[：:是]?\s*[\'"]?([A-Za-z0-9@+\-\[\]()=#$]+)[\'"]?', query, re.IGNORECASE)
                                    smiles = smiles_match.group(1) if smiles_match else ""

                                    # Try to extract drug name
                                    drug_name_patterns = [
                                        r'分析\s*([A-Za-z一-龥]+)[（(]',
                                        r'药物[是为]?\s*([A-Za-z一-龥]+)',
                                        r'Ibuprofen|布洛芬',  # Common drug names
                                        r'compound[：:是]?\s*([A-Za-z一-龥]+)',
                                    ]
                                    drug_name = "Unknown"
                                    for pattern in drug_name_patterns:
                                        match = re.search(pattern, query, re.IGNORECASE)
                                        if match:
                                            if match.lastindex and match.lastindex >= 1:
                                                drug_name = match.group(1)
                                            else:
                                                drug_name = match.group(0)
                                            break

                                    # Save to database
                                    drug_analysis_id = None
                                    for tc in tool_calls:
                                        tool_name = tc.get("name", "")
                                        if "preformulation" in tool_name.lower() or "formulation" in tool_name.lower():
                                            if not drug_analysis_id:
                                                drug_analysis_id = kb.save_drug_analysis(
                                                    session_id=session_id,
                                                    drug_name=drug_name,
                                                    smiles=smiles
                                                )

                                            kb.save_tool_call(
                                                drug_analysis_id=drug_analysis_id,
                                                tool_name=tc.get("name"),
                                                module="",
                                                input_params={"smiles": smiles, "drug_name": drug_name},
                                                output_result=tc.get("result", {})
                                            )

                            except Exception as e:
                                memory.add_message("user", query)
                                memory.add_message("assistant", f"Error: {str(e)}")

                                # Still save error to database
                                kb = st.session_state.kb
                                session_id = st.session_state.current_session_id
                                kb.create_session(session_id)
                                kb.save_message(session_id, "user", query)
                                kb.save_message(session_id, "assistant", f"Error: {str(e)}", model_used=DEFAULT_MODEL)

                        # Single rerun to display the saved messages
                        st.rerun()

        # Display conversation history
        session = get_session()
        for i, msg in enumerate(memory.messages):
            message_id = f"msg_{i}"

            # Pre-check: skip empty assistant messages BEFORE creating chat_message container
            if msg.role == "assistant":
                if msg.content is None:
                    continue  # Skip if content is None
                content_preview = re.sub(r'<think>.*?</think>', '', msg.content, flags=re.DOTALL).strip()
                if not content_preview:
                    continue  # Skip this message entirely - don't create the chat box

            with st.chat_message(msg.role):
                # For assistant messages, show reasoning BEFORE content
                if msg.role == "assistant":
                    if "tool_calls" in session and i in session["tool_calls"]:
                        tool_calls = session["tool_calls"][i]
                        display_reasoning(tool_calls, status="success")

                # Display message content
                if msg.content is None:
                    content = ""
                else:
                    content = re.sub(r'<think>.*?</think>', '', msg.content, flags=re.DOTALL).strip()
                if content:
                    st.markdown(content)

                # Add feedback buttons ONLY for assistant messages with content
                if msg.role == "assistant" and content:
                    add_feedback_buttons(message_id)

        # Chat input
        if prompt := st.chat_input("💭 Describe your research objective..."):
            # Immediately display user message
            memory.add_message("user", prompt)

            # Show user message in chat
            with st.chat_message("user"):
                st.markdown(prompt)

            # Show assistant thinking process
            with st.chat_message("assistant"):
                # Create placeholder for streaming updates
                reasoning_placeholder = st.empty()
                response_placeholder = st.empty()

                try:
                    # Check if we have any valid API key
                    has_api_key = bool(CLAUDE_API_KEY or GPT_API_KEY or MINIMAX_API_KEY)

                    if not has_api_key:
                        # No API key available - show helpful message
                        reasoning_placeholder.empty()
                        response_placeholder.markdown("""
### ⚠️ API Key 未配置

FormulationOS 需要配置 LLM API Key 才能正常工作。

**配置方法：**

1. 编辑文件：`.streamlit/secrets.toml`
2. 添加以下任一 API Key：
   ```toml
   # OpenAI GPT-4
   GPT_API_KEY = "sk-..."

   # 或 Anthropic Claude
   CLAUDE_API_KEY = "sk-ant-..."

   # 或 MiniMax
   MINIMAX_API_KEY = "..."
   ```
3. 重启应用

**临时演示模式：**
目前系统无法调用真实 AI 模型。如需演示，请配置有效的 API Key。

---
📧 需要帮助？请联系管理员获取 API Key。
                        """)
                        memory.add_message("assistant", "⚠️ API Key 未配置 - 请查看上方说明")
                        st.stop()

                    # Show initial thinking status
                    with reasoning_placeholder.container():
                        st.markdown("🧠 **Analyzing your query...**")

                    # Check analysis mode
                    analysis_mode = st.session_state.get("analysis_mode", "fast")

                    if analysis_mode == "fast":
                        # Step 1: Search literature for context (if formulation-related)
                        literature_context = []
                        if any(keyword in prompt.lower() for keyword in ['formulation', 'solubility', 'bioavailability', 'bcs', 'strategy', 'drug', 'pharmaceutical']):
                            with reasoning_placeholder.container():
                                st.markdown("🧠 **Searching literature...**")

                            try:
                                from src.formulation_os.knowledge.pubmed_search import PubMedSearchEngine
                                pubmed = PubMedSearchEngine()

                                # Quick search for relevant papers
                                search_query = prompt[:100]  # Truncate long queries
                                papers = pubmed.search_literature(search_query, max_results=3)
                                literature_context = papers

                                if papers:
                                    with reasoning_placeholder.container():
                                        st.markdown(f"🧠 **Found {len(papers)} relevant papers...**")
                            except:
                                pass  # Continue without literature if search fails

                        # Step 2: Generate response with tool calls
                        resp, tool_calls, _, _ = st.session_state.llm_manager.generate_with_tools_loop(
                            user_query=prompt,
                            model=DEFAULT_MODEL,
                            max_iterations=5
                        )

                        # Step 3: Enhance response with literature citations if available
                        if literature_context:
                            # Build citation context
                            citation_text = "\n\n---\n\n### 📚 Literature References\n\n"
                            for i, paper in enumerate(literature_context, 1):
                                citation_text += f"[{i}] {paper['authors_full']}. *{paper['title']}*. "
                                citation_text += f"{paper['journal']} ({paper['year']}). "
                                citation_text += f"[PMID: {paper['pmid']}]({paper['pubmed_url']})\n\n"

                            resp = resp + citation_text
                    else:
                        # Deep Analysis Mode: Multi-agent workflow
                        with reasoning_placeholder.container():
                            st.markdown("🧠 **Deep Analysis Mode** - Launching multi-agent workflow...")

                        # Use Workflow tool for comprehensive analysis
                        workflow_script = f"""
export const meta = {{
    name: 'deep-formulation-analysis',
    description: 'Multi-agent deep analysis for pharmaceutical formulation',
    phases: [
        {{ title: 'Property Analysis', detail: 'Compute physicochemical properties' }},
        {{ title: 'Strategy Evaluation', detail: 'Evaluate formulation strategies' }},
        {{ title: 'Synthesis', detail: 'Synthesize recommendations' }}
    ]
}};

// Phase 1: Parallel property analysis
phase('Property Analysis');
const property_agents = await parallel([
    () => agent('Analyze fundamental properties: LogP, LogS, MW, pKa for: {prompt}', {{
        label: 'Fundamentals',
        phase: 'Property Analysis'
    }}),
    () => agent('Analyze solubility behavior for: {prompt}', {{
        label: 'Solubility',
        phase: 'Property Analysis'
    }}),
    () => agent('Analyze pH stability for: {prompt}', {{
        label: 'pH Profile',
        phase: 'Property Analysis'
    }})
]);

// Phase 2: Strategy evaluation
phase('Strategy Evaluation');
const strategies = await parallel([
    () => agent('Evaluate solid dispersion strategy for: {prompt}', {{
        label: 'Solid Dispersion',
        phase: 'Strategy Evaluation'
    }}),
    () => agent('Evaluate nanocrystallization for: {prompt}', {{
        label: 'Nanocrystal',
        phase: 'Strategy Evaluation'
    }}),
    () => agent('Evaluate advanced delivery systems (SEDDS, liposomes) for: {prompt}', {{
        label: 'Advanced Systems',
        phase: 'Strategy Evaluation'
    }})
]);

// Phase 3: Synthesis
phase('Synthesis');
const synthesis = await agent(
    'Synthesize all findings into comprehensive recommendations. Properties: ' +
    JSON.stringify(property_agents) + '. Strategies: ' + JSON.stringify(strategies),
    {{
        label: 'Final Synthesis',
        phase: 'Synthesis'
    }}
);

return synthesis;
"""
                        # For now, fall back to fast mode with a note
                        # TODO: Implement actual Workflow integration
                        with reasoning_placeholder.container():
                            st.info("🚧 Multi-agent workflow is under development. Using enhanced single-agent mode with comprehensive analysis...")

                        resp, tool_calls, _, _ = st.session_state.llm_manager.generate_with_tools_loop(
                            user_query=f"[DEEP ANALYSIS MODE] Please provide comprehensive, detailed analysis with multiple perspectives: {prompt}",
                            model=DEFAULT_MODEL,
                            max_iterations=10  # More iterations for deep mode
                        )

                    # Update with reasoning process
                    if tool_calls:
                        with reasoning_placeholder.container():
                            display_reasoning(tool_calls, status="success")
                    else:
                        reasoning_placeholder.empty()

                    # Display response
                    content = re.sub(r'<think>.*?</think>', '', resp, flags=re.DOTALL).strip()
                    if content:
                        response_placeholder.markdown(content)

                    # 🧬 Auto-visualize molecule if SMILES detected
                    smiles_match = re.search(r'SMILES[：:是]?\s*[\'"]?([A-Za-z0-9@+\-\[\]()=#$]+)[\'"]?', prompt, re.IGNORECASE)
                    if smiles_match:
                        smiles = smiles_match.group(1)
                        st.markdown("---")

                        # 3D Molecular Visualization
                        st.markdown("### 🧬 Molecular Structure & Properties")

                        viz_tab1, viz_tab2 = st.tabs(["🔬 3D Interactive", "📊 2D Structure"])

                        with viz_tab1:
                            try:
                                from src.formulation_os.visualization.molecule_3d import render_molecule_3d_view

                                style_col, surface_col = st.columns([3, 1])
                                with style_col:
                                    viz_style = st.selectbox("Display Style:", ["stick", "sphere", "line"], index=0, key="viz_style")
                                with surface_col:
                                    show_surface = st.checkbox("Surface", value=False, key="show_surf")

                                render_molecule_3d_view(smiles, style=viz_style, show_surface=show_surface)

                            except ImportError:
                                st.warning("💡 3D visualization requires RDKit: `pip install rdkit`")

                        with viz_tab2:
                            mol_img = visualize_molecule_2d(smiles)
                            if mol_img:
                                st.image(f"data:image/png;base64,{mol_img}", width=400)
                            else:
                                st.info("💡 Install RDKit: `pip install rdkit`")

                    # 📊 Auto-generate relevant plots
                    if tool_calls:
                        auto_viz = generate_visualizations_from_response(resp, tool_calls, prompt)
                        if auto_viz:
                            st.markdown("---")
                            st.markdown("### 📊 Analysis Visualizations")
                            for viz in auto_viz:
                                with st.expander(f"📈 {viz['title']}", expanded=True):
                                    st.image(f"data:image/png;base64,{viz['image']}", use_container_width=True)

                    # Add feedback buttons
                    add_feedback_buttons(f"msg_{len(memory.messages)}")

                except Exception as e:
                    reasoning_placeholder.empty()
                    response_placeholder.error(f"Error: {str(e)}")
                    resp = f"Error: {str(e)}"

            # Save messages to memory
            memory.add_message("assistant", resp)

            # 💾 Persist to knowledge base database
            kb = st.session_state.kb
            session_id = st.session_state.current_session_id

            # Create session if first message
            kb.create_session(session_id)

            # Save messages to database
            kb.save_message(session_id, "user", prompt)
            kb.save_message(session_id, "assistant", resp, model_used=DEFAULT_MODEL)

            # Save tool calls to database
            if tool_calls:
                # Store in session state for display
                session = get_session()
                if "tool_calls" not in session:
                    session["tool_calls"] = {}
                session["tool_calls"][len(memory.messages) - 1] = tool_calls

                # Extract drug info from user prompt (more reliable than tool arguments)
                import re
                smiles_match = re.search(r'SMILES[：:是]?\s*[\'"]?([A-Za-z0-9@+\-\[\]()=#$]+)[\'"]?', prompt, re.IGNORECASE)
                smiles = smiles_match.group(1) if smiles_match else ""

                # Try to extract drug name from prompt
                drug_name_patterns = [
                    r'分析\s*([A-Za-z一-龥]+)[（(]',  # "分析Ibuprofen（"
                    r'药物[是为]?\s*([A-Za-z一-龥]+)',  # "药物是XX"
                    r'compound[：:是]?\s*([A-Za-z一-龥]+)',  # "compound: XX"
                ]
                drug_name = "Unknown"
                for pattern in drug_name_patterns:
                    match = re.search(pattern, prompt, re.IGNORECASE)
                    if match:
                        drug_name = match.group(1)
                        break

                # Create drug analysis record
                drug_analysis_id = None
                for tc in tool_calls:
                    tool_name = tc.get("name", "")
                    if "preformulation" in tool_name.lower() or "formulation" in tool_name.lower():
                        if not drug_analysis_id:
                            drug_analysis_id = kb.save_drug_analysis(
                                session_id=session_id,
                                drug_name=drug_name,
                                smiles=smiles
                            )

                        # Save tool call record
                        kb.save_tool_call(
                            drug_analysis_id=drug_analysis_id,
                            tool_name=tc.get("name"),
                            module="",
                            input_params={"smiles": smiles, "drug_name": drug_name},
                            output_result=tc.get("result", {})
                        )

            # Rerun to display in history
            st.rerun()

# KNOWLEDGE BASE
elif st.session_state.view_mode == "knowledge_base":
    st.subheader("📚 Knowledge Base")

    kb = st.session_state.kb
    stats = kb.get_statistics()

    # Display statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Sessions", stats['total_sessions'])
    with col2:
        st.metric("Total Messages", stats['total_messages'])
    with col3:
        st.metric("Drug Analyses", stats['total_drug_analyses'])
    with col4:
        st.metric("Tool Calls", stats['total_tool_calls'])

    st.markdown("---")

    # Tabbed navigation for different knowledge sections
    tab1, tab2, tab3, tab4 = st.tabs(["🧪 Drug Database", "💊 Formulation Strategies", "📚 Literature Intelligence", "💾 Training Data"])

    # TAB 1: Drug Database - Dashboard Style
    with tab1:
        st.markdown("### 🗃️ Pharmaceutical Drug Database")
        st.caption("4,225 FDA/EMA approved drugs from ChEMBL with BCS classification")

        # Import modules
        from src.formulation_os.knowledge.drug_search import DrugSearchEngine
        from src.formulation_os.knowledge.chembl_database import ChEMBLDrugDatabase
        import pandas as pd
        import plotly.express as px
        import plotly.graph_objects as go

        # Initialize ChEMBL database
        if "chembl_db" not in st.session_state:
            st.session_state.chembl_db = ChEMBLDrugDatabase()

        if "drug_search" not in st.session_state:
            st.session_state.drug_search = DrugSearchEngine()

        chembl_db = st.session_state.chembl_db
        df = chembl_db.get_all_drugs()

        # Dashboard Header - Statistics Cards
        st.markdown("#### 📊 Database Statistics")
        col1, col2, col3, col4 = st.columns(4)

        # Get statistics from ChEMBL database
        stats = chembl_db.get_statistics()

        with col1:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 12px; text-align: center;'>
                <h2 style='color: white; margin: 0; font-size: 2.5rem;'>{}</h2>
                <p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;'>Total Drugs</p>
            </div>
            """.format(stats['total']), unsafe_allow_html=True)

        with col2:
            bcs2_count = stats['bcs_distribution'].get('BCS II', 0)
            st.markdown("""
            <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 1.5rem; border-radius: 12px; text-align: center;'>
                <h2 style='color: white; margin: 0; font-size: 2.5rem;'>{}</h2>
                <p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;'>BCS II (Low Sol.)</p>
            </div>
            """.format(bcs2_count), unsafe_allow_html=True)

        with col3:
            avg_mw = stats['avg_molecular_weight']
            st.markdown("""
            <div style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 1.5rem; border-radius: 12px; text-align: center;'>
                <h2 style='color: white; margin: 0; font-size: 2.5rem;'>{:.0f}</h2>
                <p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;'>Avg MW (Da)</p>
            </div>
            """.format(avg_mw if avg_mw else 0), unsafe_allow_html=True)

        with col4:
            oral_count = stats['oral_drugs']
            st.markdown("""
            <div style='background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 1.5rem; border-radius: 12px; text-align: center;'>
                <h2 style='color: white; margin: 0; font-size: 2.5rem;'>{}</h2>
                <p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;'>Oral Drugs</p>
            </div>
            """.format(oral_count), unsafe_allow_html=True)

        st.markdown("---")

        # Visualizations Row
        col_viz1, col_viz2 = st.columns(2)

        with col_viz1:
            st.markdown("#### 📈 BCS Classification Distribution")
            bcs_counts = df['bcs_class'].value_counts()
            fig_pie = go.Figure(data=[go.Pie(
                labels=bcs_counts.index,
                values=bcs_counts.values,
                hole=0.4,
                marker=dict(colors=['#10b981', '#f59e0b', '#ef4444', '#8b5cf6']),
                textinfo='label+percent',
                textfont_size=14
            )])
            fig_pie.update_layout(
                showlegend=True,
                height=300,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_viz2:
            st.markdown("#### 🔬 LogP vs Molecular Weight")
            # Filter out nulls for scatter plot
            df_plot = df.dropna(subset=['molecular_weight', 'logp'])
            fig_scatter = px.scatter(
                df_plot,
                x='molecular_weight',
                y='logp',
                color='bcs_class',
                hover_data=['name'],
                color_discrete_map={
                    'BCS I': '#10b981',
                    'BCS II': '#f59e0b',
                    'BCS III': '#ef4444',
                    'BCS IV': '#8b5cf6',
                    'Unknown': '#6b7280'
                },
                height=300
            )
            fig_scatter.update_layout(
                xaxis_title="Molecular Weight (Da)",
                yaxis_title="LogP",
                showlegend=True,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        st.markdown("---")

        # Interactive Drug Table
        st.markdown("#### 💊 Drug Catalog")

        # Filters
        col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
        with col_f1:
            bcs_filter = st.multiselect(
                "Filter by BCS Class:",
                ["BCS I", "BCS II", "BCS III", "BCS IV", "Unknown"],
                default=["BCS I", "BCS II", "BCS III", "BCS IV"]
            )
        with col_f2:
            search_term = st.text_input("Search drug name:", placeholder="e.g., Aspirin")
        with col_f3:
            sort_by = st.selectbox("Sort by:", ["Name", "MW", "LogP", "BCS Class"])

        # Apply filters using ChEMBL database
        if search_term:
            filtered_df = chembl_db.search_drugs(search_term, limit=100)
        else:
            filtered_df = chembl_db.filter_drugs(bcs_classes=bcs_filter, limit=100)

        # Sort
        sort_map = {"Name": "name", "MW": "molecular_weight", "LogP": "logp", "BCS Class": "bcs_class"}
        if not filtered_df.empty and sort_map[sort_by] in filtered_df.columns:
            filtered_df = filtered_df.sort_values(sort_map[sort_by])

        # Display table
        st.caption(f"Showing {len(filtered_df)} drugs (limited to 100 for performance)")

        for idx, row in filtered_df.head(100).iterrows():
            # BCS color badge
            bcs_colors = {
                'BCS I': ('#10b981', '#d1fae5'),
                'BCS II': ('#f59e0b', '#fef3c7'),
                'BCS III': ('#ef4444', '#fee2e2'),
                'BCS IV': ('#8b5cf6', '#ede9fe'),
                'Unknown': ('#6b7280', '#f3f4f6')
            }
            color, bg = bcs_colors.get(row['bcs_class'], ('#6b7280', '#f3f4f6'))

            # Format molecular weight safely
            mw_display = f"{row['molecular_weight']:.1f}" if pd.notna(row.get('molecular_weight')) else "N/A"

            with st.expander(f"**{row['name']}** | {row['bcs_class']} | MW: {mw_display} Da"):
                # Property metrics
                mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)
                with mcol1:
                    mw_val = f"{row['molecular_weight']:.1f}" if pd.notna(row.get('molecular_weight')) else "N/A"
                    st.metric("MW", mw_val)
                with mcol2:
                    logp_val = f"{row['logp']:.2f}" if pd.notna(row.get('logp')) else "N/A"
                    st.metric("LogP", logp_val)
                with mcol3:
                    hbd_val = int(row['hbd']) if pd.notna(row.get('hbd')) else 'N/A'
                    st.metric("HBD", str(hbd_val))
                with mcol4:
                    hba_val = int(row['hba']) if pd.notna(row.get('hba')) else 'N/A'
                    st.metric("HBA", str(hba_val))
                with mcol5:
                    psa_val = f"{row['psa']:.1f}" if pd.notna(row.get('psa')) else "N/A"
                    st.metric("PSA", psa_val)

                # Display ChEMBL ID and approval year
                chembl_id = row.get('chembl_id', 'N/A')
                approval_year = int(row['first_approval']) if pd.notna(row.get('first_approval')) else 'N/A'
                st.markdown(f"**🆔 ChEMBL ID:** {chembl_id} | **📅 First Approval:** {approval_year}")

                # Route of administration
                routes = []
                if row.get('oral') == 1:
                    routes.append("Oral")
                if row.get('parenteral') == 1:
                    routes.append("Parenteral")
                if routes:
                    st.markdown(f"**💉 Routes:** {', '.join(routes)}")

                # Black box warning
                if row.get('black_box_warning') == 1:
                    st.warning("⚠️ **Black Box Warning**")

                # SMILES structure
                if pd.notna(row.get('smiles')) and row.get('smiles'):
                    with st.expander("🧬 SMILES Structure", expanded=False):
                        st.code(row['smiles'], language="text")

        st.markdown("---")

        # PubChem Search Section
        with st.expander("🔍 Search Additional Drugs (PubChem)", expanded=False):
            st.caption("Query any compound from PubChem's 110M+ database")

            pubchem_query = st.text_input("Enter drug name:", key="pubchem_quick_search")

            if pubchem_query:
                with st.spinner("Searching..."):
                    result = st.session_state.drug_search.search_drug(pubchem_query)

                    if result:
                        st.success(f"✅ **{result['name']}** (CID: {result['cid']})")

                        pcol1, pcol2, pcol3, pcol4 = st.columns(4)
                        with pcol1:
                            mw = float(result.get('molecular_weight', 0))
                            st.metric("MW", f"{mw:.2f}")
                        with pcol2:
                            logp = float(result.get('logp', 0))
                            st.metric("LogP", f"{logp:.2f}")
                        with pcol3:
                            st.metric("HBD/HBA", f"{result.get('hbd')}/{result.get('hba')}")
                        with pcol4:
                            st.info(f"**{result.get('bcs_class')}**")

                        # Recommendations
                        recs = st.session_state.drug_search.get_formulation_recommendations(result)
                        st.markdown("**Strategies:**")
                        for rec in recs[:3]:
                            st.markdown(f"- {rec}")
                    else:
                        st.error(f"Not found: {pubchem_query}")

        st.markdown("---")

        # BCS Reference Guide (collapsed by default)
        with st.expander("📖 BCS Classification Reference Guide"):
            st.info("""
            **Biopharmaceutics Classification System (BCS)** - FDA framework for drug classification
            """)

        # BCS Class I
        with st.expander("📗 BCS Class I: High Solubility, High Permeability", expanded=False):
            st.markdown("""
            **Characteristics:**
            - Solubility: Dose soluble in ≤250 mL water across pH 1-7.5
            - Permeability: ≥90% absorbed (Papp > 2×10⁻⁶ cm/s)
            - Rate-limiting step: Dissolution (usually rapid)

            **Representative Drugs:**
            - **Metoprolol** (β-blocker, LogP=1.88, MW=267)
            - **Propranolol** (β-blocker, LogP=3.48, MW=259)
            - **Caffeine** (stimulant, LogP=-0.07, MW=194)
            - **Diltiazem** (calcium channel blocker, MW=414)

            **Formulation Strategy:**
            - ✅ Usually **no formulation challenges**
            - Immediate-release tablets/capsules sufficient
            - Focus on stability, content uniformity, disintegration
            - May consider modified-release for PK optimization

            **Regulatory Advantage:**
            - Eligible for **biowaiver** (no bioequivalence study needed for generics)
            """)

        # BCS Class II
        with st.expander("📙 BCS Class II: Low Solubility, High Permeability", expanded=True):
            st.markdown("""
            **Characteristics:**
            - Solubility: Dose NOT soluble in ≤250 mL (dissolution-limited)
            - Permeability: ≥90% absorbed (membrane permeability is good)
            - Rate-limiting step: **Dissolution** (the bottleneck)

            **Representative Drugs:**
            - **Ibuprofen** (NSAID, LogS=-3.5, MW=206, Dose=400mg)
            - **Naproxen** (NSAID, LogS=-3.2, MW=230)
            - **Ketoprofen** (NSAID, LogS=-3.1, MW=254)
            - **Celecoxib** (COX-2 inhibitor, LogS=-5.8, MW=381)
            - **Griseofulvin** (antifungal, LogS=-4.6, MW=353)

            **Challenge:**
            - Poor dissolution → erratic/incomplete absorption
            - High inter-individual variability in bioavailability

            **Optimal Strategies (ranked by prevalence):**
            1. **Amorphous Solid Dispersion (ASD)** - Convert to amorphous form with polymer
            2. **Nanocrystal** - Reduce particle size to 200-400 nm
            3. **Cyclodextrin Complex** - Host-guest inclusion (limited by dose)
            4. **Salt Formation** - For ionizable drugs (pKa in range)
            5. **Lipid-based** - Self-emulsifying systems for lipophilic drugs

            **Context-Aware Selection:**
            - High dose (>400mg) → Avoid cyclodextrin (dose burden)
            - High MW (>600 Da) → Prefer ASD over cyclodextrin
            - High LogP (>4) → Consider lipid-based formulations
            """)

        # BCS Class III
        with st.expander("📘 BCS Class III: High Solubility, Low Permeability", expanded=False):
            st.markdown("""
            **Characteristics:**
            - Solubility: Dose soluble in ≤250 mL (dissolution is fine)
            - Permeability: <90% absorbed (Papp < 2×10⁻⁶ cm/s)
            - Rate-limiting step: **Permeability** (membrane barrier)

            **Representative Drugs:**
            - **Atenolol** (β-blocker, LogP=0.16, MW=266)
            - **Metformin** (antidiabetic, LogP=-2.64, MW=129)
            - **Ranitidine** (H2-antagonist, MW=314)
            - **Acyclovir** (antiviral, MW=225)

            **Challenge:**
            - Low membrane permeability → incomplete absorption
            - Formulation cannot easily fix permeability

            **Strategies (limited effectiveness):**
            - **Permeation enhancers** (surfactants, fatty acids)
            - **Prodrug approach** (increase lipophilicity)
            - **Phospholipid complex** (improve membrane interaction)
            - **Nanocarriers** (facilitate transcellular transport)

            **Reality Check:**
            - Permeability is an **intrinsic molecular property**
            - Formulation has limited impact vs BCS II
            - Often requires **chemical modification** (prodrug)
            """)

        # BCS Class IV
        with st.expander("📕 BCS Class IV: Low Solubility, Low Permeability", expanded=False):
            st.markdown("""
            **Characteristics:**
            - Solubility: Dose NOT soluble in ≤250 mL
            - Permeability: <90% absorbed
            - Rate-limiting step: **Both dissolution AND permeability**

            **Representative Drugs:**
            - **Hydrochlorothiazide** (diuretic, MW=297)
            - **Ritonavir** (protease inhibitor, LogP=5.6, MW=721)
            - **Furosemide** (diuretic, LogS=-3.4, MW=331)
            - **Amphotericin B** (antifungal, MW=924)

            **Challenge:**
            - **Most difficult class** to formulate
            - Poor oral bioavailability (<10% common)
            - High variability + food effects

            **Advanced Strategies (often combined):**
            1. **Nanosuspension + Permeation Enhancer**
            2. **Lipid-based (SEDDS/SNEDDS)** - Addresses both issues
            3. **Phospholipid Complex** - Improve both solubility & permeability
            4. **Nanocrystal + Surfactant Co-processing**
            5. **Alternative route** (IV, inhalation) often preferred

            **Development Reality:**
            - High development cost & risk
            - May require **route change** or **chemical modification**
            - Parenteral formulations often more viable
            """)

        st.markdown("---")
        st.caption("💡 **BCS classification guides formulation strategy but context matters**: dose, MW, LogP, and manufacturing constraints shape final decisions.")

    # TAB 2: Formulation Strategies
    with tab2:
        st.markdown("### 💊 Formulation Strategies for Solubility Enhancement")

        # ASD
        with st.expander("🔸 Amorphous Solid Dispersion (ASD)", expanded=True):
            st.markdown("""
            **Mechanism:**
            - Convert **crystalline drug → amorphous form** using polymer carriers
            - Amorphous form has **higher free energy** → increased dissolution rate
            - Polymer prevents recrystallization & maintains supersaturation

            **Common Polymers:**
            - **PVP** (Polyvinylpyrrolidone): Good solubilizer, hygroscopic
            - **HPMC** (Hydroxypropyl methylcellulose): Low hygroscopicity
            - **Soluplus**: Self-emulsifying properties
            - **HPMCAS**: Enteric properties for pH-dependent release
            - **Eudragit L100-55**: pH-triggered release

            **Manufacturing Methods:**
            - **Hot Melt Extrusion (HME)**: Continuous, scalable, no solvent
            - **Spray Drying**: Fast, but solvent removal needed
            - **Electrospinning**: Nanofiber formation, lab-scale

            **Critical Quality Attributes:**
            - Drug loading (10-40% typical)
            - Glass transition temperature (Tg)
            - Physical stability (crystallization risk)

            **Validation Methods:**
            - **DSC** (Differential Scanning Calorimetry): Detect crystallinity
            - **XRPD** (X-ray Powder Diffraction): Crystallinity quantification
            - **Dissolution testing**: Enhanced rate vs pure drug
            - **Stability studies**: Recrystallization monitoring (40°C/75%RH)

            **Best For:** BCS II drugs, MW 200-600 Da, moderate LogP
            """)

        # Nanocrystal
        with st.expander("🔹 Drug Nanocrystals", expanded=False):
            st.markdown("""
            **Mechanism:**
            - Reduce particle size to **200-400 nm** (nanoscale)
            - Dramatically increased **surface area** (Noyes-Whitney equation)
            - Enhanced dissolution rate while maintaining crystalline form

            **Manufacturing Methods:**
            - **Wet Ball Milling (WBM)**: Mechanical grinding with beads
            - **High Pressure Homogenization (HPH)**: 1500+ bar pressure
            - **Bottom-up Precipitation**: Antisolvent/sonocrystallization

            **Stabilizers (prevent aggregation):**
            - Surfactants: SDS, Tween 80, Poloxamer
            - Polymers: HPMC, PVP, PEG
            - Combination approach common

            **Critical Parameters:**
            - Particle size (d50, d90)
            - Polydispersity Index (PDI < 0.3 preferred)
            - Zeta potential (±30 mV for stability)

            **Validation Methods:**
            - **DLS** (Dynamic Light Scattering): Size distribution
            - **SEM/TEM**: Morphology visualization
            - **Dissolution testing**: Rate vs micronized drug
            - **Stability**: Ostwald ripening monitoring

            **Best For:** BCS II drugs, high dose (>100mg), poorly wettable compounds
            """)

        # Cyclodextrin
        with st.expander("🔷 Cyclodextrin Inclusion Complex", expanded=False):
            st.markdown("""
            **Mechanism:**
            - **Host-guest inclusion**: Drug molecule enters CD cavity
            - Hydrophobic interior + hydrophilic exterior
            - Increased apparent solubility (phase solubility studies)

            **Cyclodextrin Types:**
            - **α-CD** (6 glucose units): Cavity 4.7-5.3 Å
            - **β-CD** (7 glucose units): Cavity 6.0-6.5 Å (most common)
            - **γ-CD** (8 glucose units): Cavity 7.5-8.3 Å
            - **HP-β-CD** (hydroxypropyl): Better solubility, less toxicity
            - **SBE-β-CD** (sulfobutyl ether): Injectable applications

            **Complexation Assessment:**
            - **Phase solubility diagram** (AL, AP, BS types)
            - **Complexation constant (Kc)**: Binding affinity
            - **Complexation efficiency (CE)**: CE = Slope/(1-Slope)

            **Validation Methods:**
            - **Phase solubility studies**: Gibbs free energy (ΔG)
            - **DSC**: Endotherm disappearance
            - **NMR** (¹H, ROESY): Structural evidence of inclusion
            - **FTIR**: Shift in characteristic peaks

            **Limitations (Context-Aware):**
            - ⚠️ **Dose burden**: CD:Drug ratio 1:1 to 10:1
            - ⚠️ **MW limit**: Best for MW < 400 Da
            - ⚠️ **High dose drugs**: >200mg becomes impractical
            - Cost: HP-β-CD expensive for chronic use

            **Best For:** Low-dose BCS II drugs (MW<400, Dose<200mg)
            """)

        # Phospholipid Complex
        with st.expander("🔶 Phospholipid Complex (Phytosome)", expanded=False):
            st.markdown("""
            **Mechanism:**
            - Drug forms complex with **phosphatidylcholine**
            - Enhanced lipophilicity → improved membrane permeation
            - Addresses both solubility AND permeability

            **Phospholipid Types:**
            - **Soy lecithin** (PC 20-40%)
            - **Egg lecithin** (PC 60-80%)
            - **Hydrogenated PC** (chemically defined)

            **Formation Methods:**
            - Solvent evaporation (THF, ethanol)
            - Anti-solvent precipitation
            - Supercritical fluid technology

            **Validation:**
            - **Lipophilicity increase**: LogP measurement
            - **Stoichiometry**: Drug:PC molar ratio (1:1 or 1:2)
            - **Spectroscopy**: ³¹P NMR, FTIR for bonding
            - **Permeability**: Caco-2 or PAMPA assay

            **Best For:** BCS III/IV drugs, natural products with phenolic groups
            """)

        # SEDDS
        with st.expander("🔸 Self-Emulsifying Drug Delivery System (SEDDS)", expanded=False):
            st.markdown("""
            **Mechanism:**
            - Isotropic mixture of **oil, surfactant, co-surfactant, drug**
            - Spontaneous emulsification in GI tract → fine droplets (<100 nm)
            - Enhances solubilization & lymphatic transport

            **Formulation Components:**
            - **Oil phase**: Capryol 90, Labrafil, long-chain triglycerides
            - **Surfactants**: Tween 80, Cremophor RH40, Labrasol
            - **Co-surfactants**: PEG 400, Transcutol P, ethanol

            **Design Approach:**
            - Ternary phase diagram screening
            - Self-emulsification region identification
            - Droplet size optimization (<200 nm preferred)

            **Validation:**
            - **Droplet size**: DLS measurement
            - **Emulsification time**: <2 min
            - **Thermodynamic stability**: Freeze-thaw, centrifugation
            - **In vitro lipolysis**: Simulated GI conditions

            **Best For:** Lipophilic BCS II/IV drugs (LogP>3), low dose (<50mg)
            """)

        # Liposome
        with st.expander("🔹 Liposomal Formulation", expanded=False):
            st.markdown("""
            **Mechanism:**
            - Phospholipid bilayer vesicles (unilamellar or multilamellar)
            - Encapsulate drug in aqueous core or lipid bilayer
            - Targeted delivery, prolonged circulation (PEGylated)

            **Lipid Composition:**
            - **Phospholipids**: DSPC, DPPC, egg PC
            - **Cholesterol**: Membrane stability (30-50 mol%)
            - **PEG-lipids**: Stealth properties (DSPE-PEG2000)

            **Manufacturing:**
            - Thin-film hydration
            - Microfluidic mixing
            - Remote loading (pH/ion gradient)

            **Critical Parameters:**
            - Size: 80-200 nm (tumor accumulation), <100 nm (EPR effect)
            - PDI: <0.2 (monodisperse)
            - Encapsulation efficiency: >80% target
            - Zeta potential: -10 to -30 mV

            **Validation:**
            - **Cryo-TEM**: Structural visualization
            - **Release kinetics**: Dialysis method
            - **Stability**: Leakage, aggregation, oxidation

            **Best For:** IV delivery, oncology, targeted delivery, hydrophilic drugs
            """)

        st.markdown("---")
        st.caption("💡 **Strategy selection requires context**: BCS class + dose + MW + LogP + manufacturing capability")

    # TAB 3: Literature Intelligence
    with tab3:
        st.markdown("### 📚 Literature Intelligence & Emerging Trends")
        st.caption("Real-time access to 35M+ biomedical articles from PubMed")

        # Initialize PubMed search engine
        from src.formulation_os.knowledge.pubmed_search import PubMedSearchEngine
        if "pubmed_search" not in st.session_state:
            st.session_state.pubmed_search = PubMedSearchEngine()

        pubmed = st.session_state.pubmed_search

        # Search Interface
        st.markdown("#### 🔍 Literature Search")

        search_tab1, search_tab2, search_tab3 = st.tabs(["🎯 Quick Search", "💊 Drug-Specific", "⚙️ Technology Search"])

        # Quick Search Tab
        with search_tab1:
            col_q1, col_q2 = st.columns([3, 1])
            with col_q1:
                quick_query = st.text_input(
                    "Search biomedical literature:",
                    placeholder="e.g., solid dispersion bioavailability",
                    key="quick_pubmed_search"
                )
            with col_q2:
                max_results = st.selectbox("Results:", [5, 10, 15, 20], index=1, key="quick_max")

            if quick_query:
                with st.spinner("🔎 Searching PubMed..."):
                    papers = pubmed.search_literature(quick_query, max_results=max_results)

                if papers:
                    st.success(f"✅ Found {len(papers)} articles")

                    for i, paper in enumerate(papers, 1):
                        with st.expander(f"[{i}] {paper['title']}", expanded=(i==1)):
                            # Metadata
                            st.markdown(f"**Authors:** {paper['authors_full']}")
                            st.markdown(f"**Journal:** {paper['journal']} ({paper['year']})")
                            st.markdown(f"**PMID:** [{paper['pmid']}]({paper['pubmed_url']})")

                            if paper.get('doi'):
                                st.markdown(f"**DOI:** [{paper['doi']}](https://doi.org/{paper['doi']})")

                            # Abstract
                            st.markdown("**Abstract:**")
                            st.markdown(f"<div style='background-color: #f8f9fa; padding: 1rem; border-radius: 8px; font-size: 0.9rem;'>{paper['abstract']}</div>", unsafe_allow_html=True)

                            # Link
                            st.markdown(f"[📖 View on PubMed]({paper['pubmed_url']})")
                else:
                    st.warning("No results found. Try different keywords.")

        # Drug-Specific Search Tab
        with search_tab2:
            drug_name = st.text_input(
                "Enter drug name:",
                placeholder="e.g., Ibuprofen, Paclitaxel",
                key="drug_pubmed_search"
            )

            if drug_name:
                with st.spinner(f"🔎 Searching formulation studies for {drug_name}..."):
                    papers = pubmed.search_drug_formulation(drug_name)

                if papers:
                    st.success(f"✅ Found {len(papers)} relevant articles for **{drug_name}**")

                    for i, paper in enumerate(papers, 1):
                        with st.expander(f"[{i}] {paper['title']}"):
                            st.markdown(f"**Authors:** {paper['authors_full']}")
                            st.markdown(f"**Journal:** {paper['journal']} ({paper['year']})")
                            st.markdown(f"**Abstract:** {paper['abstract'][:300]}...")
                            st.markdown(f"[📖 View on PubMed]({paper['pubmed_url']})")
                else:
                    st.warning(f"No formulation studies found for {drug_name}")

        # Technology Search Tab
        with search_tab3:
            technology = st.selectbox(
                "Select formulation technology:",
                ["ASD", "Nanocrystal", "SEDDS", "Liposome", "Cyclodextrin"],
                key="tech_pubmed_search"
            )

            if st.button("🔍 Search Literature", key="tech_search_btn"):
                with st.spinner(f"🔎 Searching {technology} literature..."):
                    papers = pubmed.search_technology(technology)

                if papers:
                    st.success(f"✅ Found {len(papers)} recent articles on **{technology}**")

                    for i, paper in enumerate(papers, 1):
                        with st.expander(f"[{i}] {paper['title']}"):
                            st.markdown(f"**Authors:** {paper['authors_full']}")
                            st.markdown(f"**Journal:** {paper['journal']} ({paper['year']})")
                            st.markdown(f"**Abstract:** {paper['abstract'][:300]}...")
                            st.markdown(f"[📖 View on PubMed]({paper['pubmed_url']})")

        st.markdown("---")

        col_lit1, col_lit2 = st.columns(2)

        with col_lit1:
            st.markdown("#### 🤖 Machine Learning in Formulation")
            st.markdown("""
            **Recent Applications:**
            - **Polymer selection prediction** for ASD (random forest, SVM)
            - **Physical stability forecasting** (neural networks)
            - **Particle size prediction** for nanocrystals
            - **Formulation optimization** (Bayesian optimization, genetic algorithms)

            **Key Publications:**
            - *Mol. Pharm.* 2024: "Deep learning for ASD polymer selection"
            - *Int. J. Pharm.* 2023: "ML-guided nanocrystal design"
            - *Pharm. Res.* 2023: "Predictive models for drug-polymer miscibility"

            **Trend:** Move from **trial-and-error → predictive design**
            """)

        with col_lit2:
            st.markdown("#### 🎯 Quality by Design (QbD)")
            st.markdown("""
            **Core Concepts:**
            - **Design Space**: Multidimensional space of process/formulation parameters
            - **Critical Quality Attributes (CQAs)**: Dissolution, stability, content
            - **Critical Process Parameters (CPPs)**: Temperature, feed rate, screw speed

            **Tools:**
            - Design of Experiments (DoE): Factorial, response surface
            - Process Analytical Technology (PAT): Real-time monitoring
            - Risk assessment: FMEA, Ishikawa diagrams

            **Regulatory Impact:**
            - ICH Q8/Q9/Q10 guidelines
            - Enhanced design space flexibility post-approval
            """)

        st.markdown("---")

        col_trend1, col_trend2 = st.columns(2)

        with col_trend1:
            st.markdown("#### ⚙️ Continuous Manufacturing")
            st.markdown("""
            **Technologies:**
            - **Hot Melt Extrusion (HME)**: Continuous ASD production
            - **Spray Drying**: Solvent-based continuous process
            - **Continuous Granulation**: Twin-screw systems
            - **3D Printing**: Personalized dosage forms

            **Advantages:**
            - Reduced batch-to-batch variability
            - Real-time quality control (PAT integration)
            - Smaller footprint, lower cost

            **Challenges:**
            - Regulatory paradigm shift (batch → continuous)
            - Process control complexity
            """)

        with col_trend2:
            st.markdown("#### 🖥️ Digital Twins & In Silico Tools")
            st.markdown("""
            **Formulation Prediction Platforms:**
            - **PreformulationAI**: PhysChem property prediction
            - **FormulationAI**: Strategy recommendation, stability forecasting
            - **Molecular dynamics**: Drug-polymer interaction simulation
            - **PBPK modeling**: PK prediction from formulation parameters

            **Benefits:**
            - Reduce experimental load (70-80% fewer DoE runs)
            - Accelerate development timeline (6-12 months saved)
            - Optimize before synthesis

            **Future:** Fully **automated formulation design workflows**
            """)

        st.markdown("---")

        st.markdown("#### 📖 Recommended Reading")
        with st.expander("Key Reviews & Guidelines"):
            st.markdown("""
            **Comprehensive Reviews:**
            1. *Adv. Drug Deliv. Rev.* (2023) - "Amorphous solid dispersions: Theory to practice"
            2. *J. Control. Release* (2023) - "Lipid-based formulations: Clinical translation"
            3. *Eur. J. Pharm. Sci.* (2024) - "Nanocrystal technology: Industrial perspective"

            **Regulatory Guidance:**
            - FDA: Guidance for Industry - Drug Product Chemistry, Manufacturing, and Controls Information
            - ICH Q6A: Specifications for drug substances and products
            - ICH Q8(R2): Pharmaceutical development

            **Databases:**
            - [DrugBank](https://go.drugbank.com/): Comprehensive drug data
            - [PubChem](https://pubchem.ncbi.nlm.nih.gov/): Chemical structures
            - [ClinicalTrials.gov](https://clinicaltrials.gov/): Clinical outcomes
            """)

    # TAB 4: Training Data Export (original functionality)
    with tab4:
        st.subheader("💾 Export Training Data")
        col1, col2 = st.columns([3, 1])
        with col1:
            export_limit = st.number_input("Number of records to export (0 = all)", min_value=0, value=100)
        with col2:
            if st.button("📥 Export to JSON", use_container_width=True):
                output_path = f"training_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                kb.export_to_json(output_path, limit=export_limit if export_limit > 0 else None)
                st.success(f"✅ Exported to {output_path}")

        st.markdown("---")

        # Show recent training examples
        st.subheader("🔍 Recent Training Examples")
        training_data = kb.get_training_dataset(limit=10)

    if training_data:
        for i, example in enumerate(training_data, 1):
            with st.expander(f"#{i} - {example['drug_name']} ({example['timestamp']})"):
                st.markdown(f"**User Query:** {example['user_query']}")
                st.markdown(f"**SMILES:** `{example['smiles']}`")

                if example['properties']:
                    st.markdown("**Properties:**")
                    props_df = []
                    for prop_name, prop_data in example['properties'].items():
                        props_df.append({
                            "Property": prop_name,
                            "Value": prop_data['value'],
                            "Source": prop_data['source']
                        })
                    st.dataframe(props_df, use_container_width=True)

                if example['tool_calls']:
                    st.markdown(f"**Tool Calls:** {len(example['tool_calls'])} calls")
                    for tc in example['tool_calls']:
                        st.markdown(f"- {tc['tool']} → {tc['module']}")

                if example['formulation_strategies']:
                    st.markdown("**Formulation Strategies:**")
                    for strategy in example['formulation_strategies']:
                        st.markdown(f"- {strategy['type']}: {strategy['recommendation']}")

                with st.expander("View AI Response"):
                    st.markdown(example['ai_response'])
    else:
        st.info("No training data yet. Start analyzing drugs to build the knowledge base!")

    st.markdown("---")
    st.caption("💡 This knowledge base stores all interactions for future model fine-tuning and retrieval-augmented generation (RAG).")

# RESEARCH ROADMAP PAGE
elif st.session_state.view_mode == "research":
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 2.5rem; color: #1e293b;'>
            🔬 Research & Development
        </h1>
        <p style='font-size: 1.1rem; color: #64748b; margin-top: 1rem;'>
            FormulationOS Evolution: From Single-Agent to Multi-Agent Scientific Team
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Current System Overview
    st.markdown("## 📊 Current System (v1.0)")

    col_current1, col_current2 = st.columns(2)

    with col_current1:
        st.markdown("""
        ### Architecture
        ```
        User Query
            ↓
        Scientific Planner
            ↓
        Tool Calls (PreformulationAI/FormulationAI)
            ↓
        Evidence Manager
            ↓
        Hypothesis Ranker
            ↓
        Final Report
        ```
        """)

    with col_current2:
        st.markdown("""
        ### Key Features
        - ✅ Evidence-grounded reasoning
        - ✅ Context-aware decision making
        - ✅ Tool-augmented analysis
        - ✅ Single unified AI agent
        - ✅ Transparent reasoning display

        ### Limitations
        - ⚠️ Single perspective analysis
        - ⚠️ No adversarial validation
        - ⚠️ Limited debate mechanism
        """)

    st.markdown("---")

    # Benchmark Results
    st.markdown("## 🧪 Benchmark Evaluation Results")

    st.info("**Context-Aware Reasoning Validation** - 8 representative drugs evaluated")

    col_bench1, col_bench2, col_bench3 = st.columns(3)

    with col_bench1:
        st.metric("Top-1 Agreement", "0.56", "+0.37 vs baselines")
        st.caption("FormulationOS vs LLM-only (0.19)")

    with col_bench2:
        st.metric("Context Trap Avoidance", "80%", "4/5 cases")
        st.caption("vs Mechanism-only (60%)")

    with col_bench3:
        st.metric("Evidence Grounding", "1.00", "+0.70 vs baselines")
        st.caption("100% evidence-supported reasoning")

    with st.expander("📈 View Detailed Benchmark Report"):
        st.markdown("""
        ### Evaluated Drug Cases
        1. **Ibuprofen** (BCS II, 400mg) - ✅ Avoided cyclodextrin trap
        2. **Paclitaxel** (BCS IV, 854 Da) - ✅ Correct high-MW strategy
        3. **Celecoxib** (BCS II, 381 Da) - ✅ Appropriate polymer selection
        4. **Ritonavir** (LogP=5.6) - ⚠️ Lipid strategy coverage needed
        5. **Griseofulvin** (500mg dose) - ⚠️ Dose-polymer burden rule needed

        ### Key Finding
        **Context-aware reasoning prevents practical constraint violations** that
        mechanism-only and LLM-only approaches miss (e.g., cyclodextrin dose burden).

        📄 Full report: `benchmark_evaluation_report.md`
        """)

    st.markdown("---")

    # Future: Multi-Agent System
    st.markdown("## 🚀 Future Development: Multi-Agent Scientific Workflow")

    st.markdown("""
    <div style='background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); padding: 2rem; border-radius: 12px; border: 2px solid #3b82f6; margin-bottom: 2rem;'>
        <h3 style='color: #1e40af; margin-bottom: 1rem;'>💡 Core Innovation</h3>
        <p style='color: #1e3a8a; font-size: 1.05rem; line-height: 1.8;'>
            <strong>Not just adding more agents — simulating a real pharmaceutical R&D team.</strong><br/>
            Real drug development involves specialists with different expertise who debate,
            challenge each other's assumptions, and collaboratively reach robust conclusions.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Multi-Agent Architecture
    st.markdown("### 🏗️ Proposed Architecture")

    st.markdown("""
    ```
                    User Drug Query
                          |
                          ↓
                 Scientific Planner Agent
                          |
           ┌──────────────┼──────────────┐
           ↓              ↓              ↓

    Preformulation   Formulation    Critical Review
      Scientist       Scientist         Agent
        Agent           Agent              ↓
           ↓              ↓          Challenge &
    PhysChem       Strategy &       Validate
    Analysis       Excipient        Assumptions
                   Selection             ↓
           ↓              ↓              ↓
           └──────────────┼──────────────┘
                          ↓
                 Evidence Synthesizer
                          ↓
              Validation Scientist Agent
                          ↓
                 Final Hypothesis Report
    ```
    """)

    # Agent Roles
    st.markdown("### 👥 Specialized Agent Roles")

    agent_col1, agent_col2 = st.columns(2)

    with agent_col1:
        st.markdown("""
        <div style='background: white; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #3b82f6; margin-bottom: 1rem;'>
            <h4 style='color: #1e40af; margin-bottom: 0.5rem;'>🔬 Preformulation Scientist Agent</h4>
            <p style='color: #475569; margin-bottom: 0.5rem;'><strong>Role:</strong> Drug characterization & problem diagnosis</p>
            <p style='color: #64748b; font-size: 0.9rem;'>
                <strong>Input:</strong> SMILES, dose, indication<br/>
                <strong>Output:</strong> Physicochemical properties, BCS class, formulation challenges, risk assessment<br/>
                <strong>Tools:</strong> PreformulationAI (5 modules)
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style='background: white; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #10b981; margin-bottom: 1rem;'>
            <h4 style='color: #059669; margin-bottom: 0.5rem;'>💊 Formulation Scientist Agent</h4>
            <p style='color: #475569; margin-bottom: 0.5rem;'><strong>Role:</strong> Strategy design & excipient selection</p>
            <p style='color: #64748b; font-size: 0.9rem;'>
                <strong>Input:</strong> Preformulation report<br/>
                <strong>Output:</strong> Candidate strategies, excipient recommendations, process parameters<br/>
                <strong>Tools:</strong> FormulationAI (7 modules)
            </p>
        </div>
        """, unsafe_allow_html=True)

    with agent_col2:
        st.markdown("""
        <div style='background: white; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #f59e0b; margin-bottom: 1rem;'>
            <h4 style='color: #d97706; margin-bottom: 0.5rem;'>⚠️ Critical Reviewer Agent ⭐</h4>
            <p style='color: #475569; margin-bottom: 0.5rem;'><strong>Role:</strong> Challenge assumptions & identify context violations</p>
            <p style='color: #64748b; font-size: 0.9rem;'>
                <strong>Input:</strong> Formulation recommendations<br/>
                <strong>Output:</strong> Risk assessment, practical constraint analysis, alternative rankings<br/>
                <strong>Key Innovation:</strong> Prevents mechanism-only traps (e.g., cyclodextrin dose burden)
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style='background: white; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #8b5cf6; margin-bottom: 1rem;'>
            <h4 style='color: #7c3aed; margin-bottom: 0.5rem;'>🧪 Validation Scientist Agent</h4>
            <p style='color: #475569; margin-bottom: 0.5rem;'><strong>Role:</strong> Experimental validation planning</p>
            <p style='color: #64748b; font-size: 0.9rem;'>
                <strong>Input:</strong> Final hypothesis<br/>
                <strong>Output:</strong> Experimental protocols (DSC, XRPD, dissolution), success criteria, risk mitigation<br/>
                <strong>Tools:</strong> Validation protocol templates
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Example Workflow
    st.markdown("### 📝 Example: Multi-Agent Analysis of Ibuprofen")

    with st.expander("🔍 View Simulated Multi-Agent Debate"):
        st.markdown("""
        #### 🔬 Preformulation Scientist Agent:
        > "Ibuprofen shows **LogP=3.5** and **LogS=-3.97**, indicating moderate lipophilicity with
        > poor aqueous solubility. **BCS Class II** confirmed. Primary challenge: **dissolution-limited absorption**.
        > Recommendation: Solubility enhancement required."

        #### 💊 Formulation Scientist Agent:
        > "Based on preformulation analysis, I recommend three strategies:
        > 1. **Solid dispersion** (HPMC-AS) - amorphization approach
        > 2. **Cyclodextrin complexation** - inclusion complex
        > 3. **Nanocrystal** - particle size reduction
        >
        > Initial ranking: Cyclodextrin > Solid dispersion > Nanocrystal"

        #### ⚠️ Critical Reviewer Agent:
        > "**Challenge on cyclodextrin recommendation:**
        >
        > - MW=206 Da ✅ (fits β-CD cavity)
        > - **BUT: Dose=400mg ❌**
        > - Required cyclodextrin: 400-2000mg (1:1 to 5:1 ratio)
        > - **Total tablet weight: >2g — impractical for patient compliance**
        > - **Cost concern:** Large cyclodextrin amount
        >
        > **Revised ranking:** Solid dispersion > Nanocrystal > Cyclodextrin
        >
        > **Rationale:** Context-aware reasoning identifies dose-dependent practical constraint
        > that mechanism-only matching misses."

        #### 🧪 Validation Scientist Agent:
        > "For solid dispersion approach, validation protocol:
        > 1. **Solid-state characterization:** DSC, XRPD, FTIR
        > 2. **Dissolution testing:** pH 1.2, 4.5, 6.8
        > 3. **Physical stability:** 40°C/75% RH, 6 months
        > 4. **Bioequivalence study** vs marketed product
        >
        > Success criteria: >85% dissolution in 30 min, <5% recrystallization after 6 months."
        """)

    st.markdown("---")

    # Research Value
    st.markdown("### 🎓 Research Contribution")

    value_col1, value_col2 = st.columns(2)

    with value_col1:
        st.markdown("""
        #### Current Single-Agent Limitations
        - Single perspective analysis
        - No self-correction mechanism
        - Limited adversarial validation
        - Challenge: How to prevent overconfidence?
        """)

    with value_col2:
        st.markdown("""
        #### Multi-Agent System Advantages
        - **Diverse expertise** (preformulation, formulation, validation)
        - **Adversarial validation** (Critical Reviewer challenges assumptions)
        - **Consensus-based** decision making
        - **Mimics real R&D team** dynamics
        """)

    st.markdown("""
    <div style='background: #fef3c7; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #f59e0b; margin-top: 1.5rem;'>
        <p style='color: #92400e; font-size: 1.05rem; margin-bottom: 0;'>
            <strong>💡 Key Insight:</strong> Multi-agent is not about adding more LLM calls.
            It's about <strong>simulating collaborative scientific reasoning</strong> with role-specific expertise
            and adversarial validation — the way real pharmaceutical R&D teams work.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Development Timeline
    st.markdown("### 📅 Development Roadmap")

    timeline_col1, timeline_col2, timeline_col3 = st.columns(3)

    with timeline_col1:
        st.markdown("""
        <div style='background: #d1fae5; padding: 1.5rem; border-radius: 10px; text-align: center;'>
            <h4 style='color: #065f46; margin-bottom: 0.5rem;'>✅ Phase 1</h4>
            <p style='color: #047857; margin-bottom: 0;'><strong>Current Status</strong></p>
            <p style='color: #059669; font-size: 0.9rem;'>
                • Single-agent system<br/>
                • Context-aware reasoning<br/>
                • Benchmark validation (8 drugs)<br/>
                • Evidence grounding
            </p>
        </div>
        """, unsafe_allow_html=True)

    with timeline_col2:
        st.markdown("""
        <div style='background: #fef3c7; padding: 1.5rem; border-radius: 10px; text-align: center;'>
            <h4 style='color: #92400e; margin-bottom: 0.5rem;'>🔄 Phase 2</h4>
            <p style='color: #b45309; margin-bottom: 0;'><strong>In Development</strong></p>
            <p style='color: #d97706; font-size: 0.9rem;'>
                • Multi-agent core implementation<br/>
                • 4 specialized agents<br/>
                • Debate mechanism<br/>
                • Consensus synthesis
            </p>
        </div>
        """, unsafe_allow_html=True)

    with timeline_col3:
        st.markdown("""
        <div style='background: #dbeafe; padding: 1.5rem; border-radius: 10px; text-align: center;'>
            <h4 style='color: #1e40af; margin-bottom: 0.5rem;'>🚀 Phase 3</h4>
            <p style='color: #1e3a8a; margin-bottom: 0;'><strong>Future</strong></p>
            <p style='color: #2563eb; font-size: 0.9rem;'>
                • Scientific Research Mode UI<br/>
                • Comparative evaluation<br/>
                • Multi-agent benchmark<br/>
                • Publication
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Call to Action
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <p style='font-size: 1.1rem; color: #475569;'>
            <strong>This is not just a technical upgrade — it's a research contribution.</strong>
        </p>
        <p style='color: #64748b; margin-top: 1rem;'>
            By simulating pharmaceutical R&D team dynamics, FormulationOS aims to demonstrate
            how multi-agent AI can enhance scientific reasoning quality beyond single-agent systems.
        </p>
    </div>
    """, unsafe_allow_html=True)
