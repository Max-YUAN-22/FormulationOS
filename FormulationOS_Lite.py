import streamlit as st
import uuid
from datetime import datetime

st.set_page_config(page_title="FormulationOS Lite", layout="wide")

# Simple initialization
if "view" not in st.session_state:
    st.session_state.view = "home"
if "messages" not in st.session_state:
    st.session_state.messages = []

# Simple navigation
col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
with col1:
    st.title("🧬 FormulationOS")
with col2:
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.view = "home"
with col3:
    if st.button("💬 AI Workspace", use_container_width=True):
        st.session_state.view = "workspace"
with col4:
    if st.button("📚 Knowledge Base", use_container_width=True):
        st.session_state.view = "kb"

st.markdown("---")

# HOME PAGE
if st.session_state.view == "home":
    st.markdown("<h1 style='text-align: center;'>An Agentic AI Scientist for Pharmaceutical Formulation</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Lightweight demo version - Fast & Responsive</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💬 Conversations", "30")
    with col2:
        st.metric("💊 Drug Analyses", "9")
    with col3:
        st.metric("🔧 AI Tool Calls", "49")

# WORKSPACE
elif st.session_state.view == "workspace":
    col_left, col_main = st.columns([1, 3])
    
    with col_left:
        st.markdown("### 📚 Research Memory")
        with st.expander("💊 Drug Profile", expanded=True):
            st.caption("No drug analyzed yet")
        with st.expander("🔬 Hypotheses"):
            st.caption("No hypotheses yet")
    
    with col_main:
        st.subheader("💬 AI Scientist Chat")
        
        st.warning("""
        ⚠️ **Demo Mode**
        
        This is a lightweight demo version. The full version with AI capabilities 
        requires API configuration.
        """)
        
        # Display messages
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # Chat input
        if prompt := st.chat_input("Describe your research objective..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Add assistant response (mock)
            response = f"**Mock Response**: I received your query about '{prompt[:50]}...'. In the full version, I would analyze this using PreformulationAI and FormulationAI tools."
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            st.rerun()

# KNOWLEDGE BASE
else:
    st.subheader("📚 Knowledge Base")
    st.info("Knowledge base features will be available in the full version.")
