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
"""

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
from formulation_os.knowledge_base import KnowledgeBaseDB

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
    if "llm_manager" not in st.session_state:
        memory = st.session_state.sessions[st.session_state.current_session_id]["memory"]
        st.session_state.llm_manager = UnifiedLLMManager(
            memory=memory,
            anthropic_api_key=CLAUDE_API_KEY,
            openai_api_key=GPT_API_KEY,
            minimax_api_key=MINIMAX_API_KEY,
            anthropic_base_url=CLAUDE_BASE_URL,
            openai_base_url=GPT_BASE_URL,
            minimax_base_url=MINIMAX_BASE_URL
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
col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
with col1:
    st.title("🧬 FormulationOS")
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

    # Platform introductions
    st.markdown("## 🔗 Integrated AI Platforms")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); padding: 2rem; border-radius: 12px; border: 1px solid #bfdbfe;'>
            <h3 style='color: #1e40af; margin-bottom: 1rem;'>🔬 PreformulationAI</h3>
            <p style='color: #1e3a8a; margin-bottom: 1rem;'>
                <strong>5 AI Modules for Drug Characterization</strong>
            </p>
            <ul style='color: #1e3a8a; line-height: 1.8;'>
                <li><strong>Fundamentals</strong>: LogP, LogS, MW, pKa, HBD/HBA</li>
                <li><strong>Solubility</strong>: Temperature and solvent-dependent behavior</li>
                <li><strong>pH Profile</strong>: pH-dependent stability analysis</li>
                <li><strong>Developability</strong>: BCS classification, druglikeness, formulatability</li>
                <li><strong>IF Descriptors</strong>: Interpretable formulation descriptors</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        if st.button("🔗 Visit PreformulationAI Platform", use_container_width=True):
            st.markdown("[PreformulationAI](https://preformulationai.computpharm.org/)")

    with col2:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); padding: 2rem; border-radius: 12px; border: 1px solid #bbf7d0;'>
            <h3 style='color: #15803d; margin-bottom: 1rem;'>💊 FormulationAI</h3>
            <p style='color: #14532d; margin-bottom: 1rem;'>
                <strong>7 AI Modules for Formulation Design</strong>
            </p>
            <ul style='color: #14532d; line-height: 1.8;'>
                <li><strong>Strategy Recommendation</strong>: Overall formulation strategy ranking</li>
                <li><strong>Solid Dispersion</strong>: Physical stability prediction</li>
                <li><strong>Nanocrystal</strong>: Particle size and PDI prediction</li>
                <li><strong>Cyclodextrin</strong>: Complexation free energy (ΔG)</li>
                <li><strong>Phospholipid Complex</strong>: Permeability enhancement</li>
                <li><strong>SEDDS</strong>: Self-emulsifying system design</li>
                <li><strong>Liposome</strong>: Targeted delivery parameters</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        if st.button("🔗 Visit FormulationAI Platform", use_container_width=True):
            st.markdown("[FormulationAI](https://formulationai.computpharm.org/)")

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

    st.subheader("💬 AI Scientist Chat")
    st.caption("Natural language interface for drug formulation research")

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

                                # Save to database
                                drug_analysis_id = None
                                for tc in tool_calls:
                                    tool_name = tc.get("name", "")
                                    if "preformulation" in tool_name.lower() or "formulation" in tool_name.lower():
                                        args = tc.get("arguments", {})
                                        smiles = args.get("smiles", args.get("SMILES", ""))
                                        drug_name = args.get("drug_name", "Unknown")

                                        if not drug_analysis_id:
                                            drug_analysis_id = kb.save_drug_analysis(
                                                session_id=session_id,
                                                drug_name=drug_name,
                                                smiles=smiles
                                            )

                                        kb.save_tool_call(
                                            drug_analysis_id=drug_analysis_id,
                                            tool_name=tc.get("name"),
                                            module=args.get("module", ""),
                                            input_params=args,
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

        with st.chat_message(msg.role):
            # For assistant messages, show reasoning BEFORE content
            if msg.role == "assistant":
                if "tool_calls" in session and i in session["tool_calls"]:
                    tool_calls = session["tool_calls"][i]
                    display_reasoning(tool_calls, status="success")

            # Display message content
            content = re.sub(r'<think>.*?</think>', '', msg.content, flags=re.DOTALL).strip()

            # Only display assistant messages with actual content
            if msg.role == "assistant" and not content:
                continue  # Skip empty assistant messages entirely

            if content:
                st.markdown(content)

            # Add feedback buttons ONLY for assistant messages with content
            if msg.role == "assistant" and content:
                add_feedback_buttons(message_id)

    # Chat input
    if prompt := st.chat_input("💭 Describe your research objective..."):
        try:
            with st.spinner("🧠 Analyzing..."):
                resp, tool_calls, _, _ = st.session_state.llm_manager.generate_with_tools_loop(
                    user_query=prompt,
                    model=DEFAULT_MODEL,
                    max_iterations=5
                )

            # Save messages to memory
            memory.add_message("user", prompt)
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

                # Create drug analysis record if drug detected
                # (Simple heuristic: check if SMILES is in prompt or tool calls involve drug analysis)
                drug_analysis_id = None
                for tc in tool_calls:
                    tool_name = tc.get("name", "")
                    if "preformulation" in tool_name.lower() or "formulation" in tool_name.lower():
                        # Extract drug info from tool call
                        args = tc.get("arguments", {})
                        smiles = args.get("smiles", args.get("SMILES", ""))
                        drug_name = args.get("drug_name", "Unknown")

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
                            module=args.get("module", ""),
                            input_params=args,
                            output_result=tc.get("result", {})
                        )

        except Exception as e:
            memory.add_message("user", prompt)
            memory.add_message("assistant", f"Error: {str(e)}")

            # Still save error to database for debugging
            kb = st.session_state.kb
            session_id = st.session_state.current_session_id
            kb.create_session(session_id)
            kb.save_message(session_id, "user", prompt)
            kb.save_message(session_id, "assistant", f"Error: {str(e)}", model_used=DEFAULT_MODEL)

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

    # Export options
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
