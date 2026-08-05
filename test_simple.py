import streamlit as st

st.set_page_config(page_title="Test", layout="wide")

# Simple state
if "view" not in st.session_state:
    st.session_state.view = "home"

# Navigation
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Home"):
        st.session_state.view = "home"
        st.rerun()
with col2:
    if st.button("Workspace"):
        st.session_state.view = "workspace"
        st.rerun()
with col3:
    if st.button("KB"):
        st.session_state.view = "kb"
        st.rerun()

st.markdown("---")

# Views
if st.session_state.view == "home":
    st.title("Home Page")
    st.write("This is home - navigation should be fast")
    
elif st.session_state.view == "workspace":
    st.title("Workspace")
    col_left, col_main = st.columns([1, 3])
    
    with col_left:
        st.markdown("### Left Panel")
        st.write("This should be visible")
        
    with col_main:
        st.markdown("### Main Area")
        st.write("Main content here")
        
else:
    st.title("Knowledge Base")
    st.write("KB content")
