import streamlit as st
import uuid
from datetime import datetime
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from formulation_os.agent.evidence_manager import EvidenceManager
from formulation_os.agent.context_reasoner import DrugContext, ContextReasoner
from formulation_os.agent.hypothesis_ranker import create_hypothesis_ranker_from_evidence

st.set_page_config(page_title="FormulationOS", page_icon="🧬", layout="wide")

# Minimal initialization
if "view" not in st.session_state:
    st.session_state.view = "home"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "evidence_manager" not in st.session_state:
    st.session_state.evidence_manager = EvidenceManager()

# Navigation
col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
with col1:
    st.title("🧬 FormulationOS")
with col2:
    if st.button("🏠 Home", use_container_width=True, key="nav_home"):
        st.session_state.view = "home"
with col3:
    if st.button("💬 AI Workspace", use_container_width=True, key="nav_workspace"):
        st.session_state.view = "workspace"
with col4:
    if st.button("📚 Knowledge Base", use_container_width=True, key="nav_kb"):
        st.session_state.view = "kb"

st.markdown("---")

# HOME PAGE
if st.session_state.view == "home":
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 2.5rem; color: #1e293b;'>
            An Agentic AI Scientist for Pharmaceutical Formulation
        </h1>
        <p style='font-size: 1.1rem; color: #64748b; margin-top: 1rem;'>
            From molecular properties to formulation strategies — an intelligent R&D collaboration platform
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💬 Conversations", "30")
    with col2:
        st.metric("💊 Drug Analyses", "9")
    with col3:
        st.metric("🔧 AI Tool Calls", "49")
    with col4:
        st.metric("📁 Active Sessions", "15")
    
    st.markdown("---")
    
    # Feature highlights
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🧬 AI-Powered Analysis")
        st.write("Generate evidence-based hypotheses through dialogue")
    with col2:
        st.markdown("### 🔬 Comprehensive Tools")
        st.write("12 integrated AI modules for full preformulation pipeline")
    with col3:
        st.markdown("### 💡 Natural Language")
        st.write("Describe research goals in plain language")

# WORKSPACE
elif st.session_state.view == "workspace":
    col_left, col_main = st.columns([1, 3])
    
    with col_left:
        st.markdown("### 📚 Research Memory")
        with st.expander("💊 Drug Profile", expanded=True):
            st.caption("No drug analyzed yet")
        with st.expander("🔬 Hypotheses", expanded=False):
            st.caption("No hypotheses generated yet")
        with st.expander("💡 Key Insights", expanded=False):
            st.caption("Insights will appear here")
    
    with col_main:
        st.subheader("💬 AI Scientist Chat")
        
        # API warning
        st.warning("""
        ⚠️ **Mock Backend Mode**
        
        Currently using simulated data for demonstration. Configure API keys for real predictions:
        - `CLAUDE_API_KEY` or `GPT_API_KEY` or `MINIMAX_API_KEY`
        
        **Current Mode:** Evidence-based reasoning with Mock data
        """)
        
        # Mode selection
        st.markdown("### 🎯 Analysis Mode")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⚡ Fast Mode", use_container_width=True, type="primary"):
                st.info("Fast Mode: Quick analysis with 5 iterations (~30s)")
        with col2:
            if st.button("🧠 Deep Analysis", use_container_width=True):
                st.info("Deep Analysis: Comprehensive multi-perspective analysis (~2-5min)")
        
        st.markdown("---")
        
        # Quick start examples
        if len(st.session_state.messages) == 0:
            st.info("💡 **Quick Start** - Try an example below")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📊 Analyze Ibuprofen", use_container_width=True, key="ex1"):
                    prompt = "帮我分析Ibuprofen（布洛芬）的制剂挑战，SMILES: CC(C)Cc1ccc(cc1)C(C)C(=O)O"
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    
                    # Mock tool output
                    mock_result = {
                        "drug_name": "Ibuprofen",
                        "logp": 3.97,
                        "logs": -3.97,
                        "molecular_weight": 206.28,
                        "bcs_class": "II",
                        "permeability": 0.00025
                    }
                    
                    # Evidence-based analysis
                    evidence_list = st.session_state.evidence_manager.capture_from_tool_call(
                        "preformulation_fundamentals", mock_result
                    )
                    
                    # Create drug context
                    drug_context = DrugContext(
                        molecular_weight=206.28,
                        logP=3.97,
                        logS=-3.97,
                        bcs_class="II",
                        dose=400
                    )
                    
                    # Hypothesis ranking
                    ranker = create_hypothesis_ranker_from_evidence(
                        st.session_state.evidence_manager, drug_context
                    )
                    ranked = ranker.rank_hypotheses()
                    
                    # Build response
                    response = f"""### Ibuprofen (布洛芬) Analysis

**Physicochemical Properties:**
- Molecular Weight: 206.28 g/mol
- LogP: 3.97 (Highly lipophilic)
- LogS: -3.97 (Poor aqueous solubility)
- BCS Class: II (Low solubility, High permeability)

**📊 Evidence-Based Analysis:**

{len(evidence_list)} pieces of evidence identified:
"""
                    for i, ev in enumerate(evidence_list, 1):
                        response += f"\n**Evidence #{i}:** {ev.mechanism.value}\n"
                        response += f"- Observation: {ev.observation}\n"
                        response += f"- Interpretation: {ev.interpretation}\n"
                        response += f"- Confidence: {ev.confidence:.0%}\n"
                    
                    response += "\n\n**🔬 Formulation Strategy Ranking:**\n\n"
                    
                    for i, hyp in enumerate(ranked[:3], 1):
                        response += f"**#{i}: {hyp.strategy_name}** (Confidence: {hyp.final_confidence:.2f})\n"
                        response += f"- Evidence Strength: {hyp.evidence_strength:.2f}\n"
                        response += f"- Mechanism Match: {hyp.mechanism_compatibility:.2f}\n"
                        response += f"- Context Suitability: {hyp.context_compatibility:.2f}\n\n"
                        
                        if hyp.context_assessment:
                            response += f"**Advantages:** {', '.join(hyp.context_assessment.advantages[:2])}\n"
                            response += f"**Limitations:** {', '.join(hyp.context_assessment.limitations[:2])}\n\n"
                    
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()
            
            with col2:
                if st.button("🔬 Evaluate Compound", use_container_width=True, key="ex2"):
                    st.session_state.messages.append({
                        "role": "user",
                        "content": "我有一个新化合物，SMILES是CC(=O)Oc1ccccc1C(=O)O，请帮我评估它的BCS分类"
                    })
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "**Mock Response**: This is Aspirin. In the full version, I would call PreformulationAI to predict BCS classification."
                    })
                    st.rerun()
            
            with col3:
                if st.button("💊 Solid Dispersion", use_container_width=True, key="ex3"):
                    st.session_state.messages.append({
                        "role": "user",
                        "content": "我的药物是BCS II类化合物，溶解度很低，请推荐合适的固体分散体策略"
                    })
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "**Mock Response**: For BCS Class II compounds with low solubility, I recommend evaluating solid dispersion strategies."
                    })
                    st.rerun()
        
        # Display messages
        for i, msg in enumerate(st.session_state.messages):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # Chat input
        if prompt := st.chat_input("💭 Describe your research objective..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"**Mock Response**: Received query about '{prompt[:50]}...'. Configure API keys to enable real AI analysis."
            })
            st.rerun()

# KNOWLEDGE BASE
else:
    st.subheader("📚 Knowledge Base")
    st.info("Knowledge base features: session history, training data export, statistics.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Records", "30")
    with col2:
        st.metric("Drug Analyses", "9")
    with col3:
        st.metric("Tool Calls", "49")

