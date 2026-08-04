"""FormulationOS - AI Scientist Workspace (Fixed)

Complete working version with three-column layout and Knowledge Base
"""

import streamlit as st
from pathlib import Path
import sys
import uuid
import re
import os
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))

from formulation_os.agent.conversation_memory import ConversationMemory
from formulation_os.agent.unified_llm_manager import UnifiedLLMManager
from formulation_os.agent.scientific_state import ScientificState
from formulation_os.knowledge_base import KnowledgeBaseDB

# Config - Read from environment variables (Render) or Streamlit Secrets (Streamlit Cloud)
def get_config(key: str, default: str = "") -> str:
    """Get config from environment variable or Streamlit secrets"""
    # Try environment variable first (for Render, Railway, etc.)
    env_value = os.environ.get(key)
    if env_value:
        return env_value

    # Fall back to Streamlit secrets (for Streamlit Cloud)
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

# Use GPT-4o by default for better tool calling support
DEFAULT_MODEL = "gpt-4o" if GPT_API_KEY else "MiniMax-M3"

st.set_page_config(
    page_title="FormulationOS - AI Scientist",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Clean CSS
st.markdown("""
<style>
    header[data-testid="stHeader"] {display: none;}
    .stApp {background: #f5f7fa;}
    .main {padding: 1rem !important;}

    .stButton button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.6rem 1.5rem !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# View mode
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "home"

# Initialize
def init():
    if "sessions" not in st.session_state:
        st.session_state.sessions = {}
    if "current_session_id" not in st.session_state:
        new_id = str(uuid.uuid4())
        st.session_state.current_session_id = new_id
        st.session_state.sessions[new_id] = {
            "memory": ConversationMemory(),
            "scientific_state": ScientificState(),
            "created_at": datetime.now()
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

def get_session():
    return st.session_state.sessions[st.session_state.current_session_id]

def get_scientific_state() -> ScientificState:
    return get_session()["scientific_state"]

def new_session():
    new_id = str(uuid.uuid4())
    st.session_state.sessions[new_id] = {
        "memory": ConversationMemory(),
        "scientific_state": ScientificState(),
        "created_at": datetime.now()
    }
    st.session_state.current_session_id = new_id
    st.session_state.llm_manager.memory = get_session()["memory"]

def switch_session(sid):
    st.session_state.current_session_id = sid
    st.session_state.llm_manager.memory = get_session()["memory"]

init()

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

if st.session_state.view_mode == "home":
    # HOME PAGE
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 3rem; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            An Agentic AI Scientist for Pharmaceutical Formulation
        </h1>
        <p style='font-size: 1.2rem; color: #64748b; margin-top: 1rem;'>
            从分子特性到制剂策略，全流程智能化研发协作平台
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("##")

    # What is FormulationOS
    st.markdown("### 🎯 什么是 FormulationOS？")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **传统制剂研发流程：**

        📋 查文献 → 💭 拍脑袋 → 🧪 做实验 → 📊 看结果 → 🔄 重复...

        ❌ 效率低下、依赖经验、缺乏系统性
        """)

    with col2:
        st.markdown("""
        **FormulationOS 工作方式：**

        🧬 输入分子 → 🤖 AI推理 → 💡 生成假设 → 🎯 设计验证 → 📈 迭代优化

        ✅ 数据驱动、证据支撑、可追溯、可复现
        """)

    st.markdown("---")

    # Core Capabilities
    st.markdown("### 🚀 核心能力：Agentic AI 科研协作")

    st.info("💡 **什么是 Agentic？** AI 不是简单的问答机器人，而是能够**自主调用工具、生成假设、设计实验**的科研协作伙伴")

    tab1, tab2, tab3 = st.tabs(["🧬 PreformulationAI", "💊 FormulationAI", "🔄 Agentic 工作流"])

    with tab1:
        st.markdown("#### 🧬 PreformulationAI")
        st.caption("AI-driven preformulation for small-molecule drug development")

        st.info("📝 From a SMILES string to a full developability dossier in seconds — ten fundamental preformulation properties, temperature- and pH-resolved profiles, and interpretable formulation descriptors.")

        st.markdown("##### Five Prediction Modules")
        st.markdown("Every module outputs actionable numbers — not just classifications — backed by interpretable ML and confidence estimates.")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **01 — Fundamentals**
            Fundamental preformulation prediction & critical property calculation
            - Density, MP, Tg
            - logP, logD₇.₄, logPapp
            - Acidic / Basic pKa
            - logS, kinetic solubility
            - FractionCSP3, TPSA, NumHAcceptors

            **02 — Solubility**
            Conditional solubility prediction across solvents and temperatures
            - Temperature-dependent solubility curves
            - Organic solvent solubility
            - Binary solvent systems

            **03 — pH Profile**
            pH-dependent preformulation estimation
            - pH-Species fraction profile
            - pH-dependent logS profile
            - pH-dependent logD profile
            """)

        with col2:
            st.markdown("""
            **04 — Developability**
            Interpretable developability assessment for drug design
            - BCS classification
            - Druglikeness
            - Oral & injectable formulatability index
            - Fully interpretable

            **05 — IF-Descriptors**
            Interpretable formulation descriptors
            - Preformulation properties
            - Interpretable RDKit descriptors
            - Highly interpretable & information-rich
            - Batch generation support
            """)

        st.markdown("---")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            st.link_button("🌐 访问 PreformulationAI 官方平台", "https://preformulationai.computpharm.org/", use_container_width=True)
        with col_btn2:
            st.caption("Computational Pharmaceutical Group, State Key Laboratory Of Quality Research in Chinese Medicine, ICMS, University of Macau")

    with tab2:
        st.markdown("#### 💊 FormulationAI")
        st.caption("The pioneer providing best solutions for in silico drug formulation design")

        st.info("📝 FormulationAI keeps the most comprehensive data and artificial intelligent models up to date, and serves you with accurate predictions and easy-to-use interface.")

        st.markdown("##### Seven Formulation Modules")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **Drug/Cyclodextrin Complex**
            - Complexation free energy (ΔG)
            - Solubility enhancement prediction
            - CD type recommendation

            **Solid Dispersion**
            - Physical stability prediction
            - Polymer selection guidance
            - Manufacturing method recommendation

            **Phospholipid Complex**
            - Lipophilicity improvement
            - Bioavailability enhancement
            - Complex formation assessment

            **Drug Nanocrystals**
            - Particle size prediction
            - PDI estimation
            - Manufacturing methods (BWM, HPH, Antisolvent)
            """)

        with col2:
            st.markdown("""
            **Self-Emulsifying System (SEDDS)**
            - Oil phase recommendation
            - Surfactant selection
            - Droplet size prediction
            - Formulation composition optimization

            **Liposome**
            - Lipid selection
            - Size optimization
            - Encapsulation efficiency
            - Release profile prediction

            **Strategy Recommendation**
            - Optimal formulation approach selection
            - Score-based ranking
            - Structure-property guided strategy
            """)

        st.markdown("---")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            st.link_button("🌐 访问 FormulationAI 官方平台", "https://formulationai.computpharm.org/", use_container_width=True)
        with col_btn2:
            st.caption("**Please cite:** FormulationAI: a novel web-based platform for drug formulation design driven by artificial intelligence, *Brief Bioinform.* 2023; 25(1):bbad419")

    with tab3:
        st.markdown("""
        #### AI 如何自主工作？

        **示例对话：**

        👤 **你**：帮我分析 Ibuprofen 的口服制剂优化方案

        🤖 **AI 自主推理过程**：

        1️⃣ **理解目标** → "需要改善口服生物利用度"

        2️⃣ **调用 PreformulationAI** →
        ```python
        # AI 自动调用工具
        preformulation_ai_fundamentals(smiles="CC(C)Cc1ccc(cc1)C(C)C(=O)O")
        preformulation_ai_developability(...)
        ```

        3️⃣ **解读结果** →
        - LogP = 3.5（高疏水）
        - LogS = -4.2（低溶解度）
        - **诊断：BCS II类，溶解度是主要瓶颈**

        4️⃣ **生成假设** →
        - 💡 假设1：无定形化可提升溶解速率
        - 💡 假设2：纳米晶可增加表面积

        5️⃣ **调用 FormulationAI 验证** →
        ```python
        formulation_ai_solid_dispersion(drug_smiles="...", polymer="PVP")
        formulation_ai_nanocrystal(...)
        ```

        6️⃣ **设计实验** →
        - 📋 建议用 DSC/XRPD 验证无定形态
        - 📋 建议做体外溶出对比实验

        ---

        ✨ **关键特性：**
        - ✅ 自主决策工具调用顺序
        - ✅ 结合多工具证据生成假设
        - ✅ 标注不确定性，而非直接给结论
        - ✅ 全程可追溯、可解释
        """)

    st.markdown("---")

    # Quick Start
    st.markdown("### 🎬 快速开始")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        #### 1️⃣ 进入 AI Workspace
        点击顶部 **💬 AI Workspace** 按钮
        """)

    with col2:
        st.markdown("""
        #### 2️⃣ 描述研究目标
        用自然语言描述你的问题：
        - "分析 Ibuprofen 的制剂挑战"
        - "帮我筛选适合 BCS II 类的策略"
        """)

    with col3:
        st.markdown("""
        #### 3️⃣ 观察 AI 推理
        AI 会自动：
        - 🔧 调用工具获取数据
        - 🧠 解读结果生成假设
        - 📊 展示科学状态面板
        """)

    st.markdown("##")

    if st.button("🚀 开始使用 AI Workspace", use_container_width=True, type="primary"):
        st.session_state.view_mode = "workspace"
        st.rerun()

elif st.session_state.view_mode == "workspace":
    # THREE-COLUMN WORKSPACE
    col_left, col_center, col_right = st.columns([2, 5, 3])

    # LEFT - History
    with col_left:
        st.subheader("📚 Research Projects")

        if st.button("➕ New Research", use_container_width=True):
            new_session()
            st.rerun()

        st.markdown("---")

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

    # CENTER - Chat
    with col_center:
        st.subheader("💬 AI Scientist Chat")
        st.caption("Collaborative pharmaceutical formulation research")

        memory = get_session()["memory"]

        # Show quick start guide if no messages
        if len(memory.messages) == 0:
            st.info("💡 **快速开始** - 选择一个示例问题或输入你自己的研究目标")

            col_ex1, col_ex2, col_ex3 = st.columns(3)

            with col_ex1:
                if st.button("📊 分析 Ibuprofen 制剂挑战", use_container_width=True):
                    st.session_state.quick_start_query = "帮我分析Ibuprofen（布洛芬）的制剂挑战，SMILES: CC(C)Cc1ccc(cc1)C(C)C(=O)O，我想改善其口服生物利用度"
                    st.rerun()

            with col_ex2:
                if st.button("🔬 评估新化合物可制剂性", use_container_width=True):
                    st.session_state.quick_start_query = "我有一个新化合物，SMILES是CC(=O)Oc1ccccc1C(=O)O，请帮我评估它的BCS分类和可制剂性"
                    st.rerun()

            with col_ex3:
                if st.button("💊 推荐固体分散体策略", use_container_width=True):
                    st.session_state.quick_start_query = "我的药物是BCS II类化合物，溶解度很低，请推荐合适的固体分散体策略"
                    st.rerun()

        # Handle quick start
        if "quick_start_query" in st.session_state and st.session_state.quick_start_query:
            query = st.session_state.quick_start_query
            st.session_state.quick_start_query = None

            memory.add_message("user", query)

            with st.chat_message("user"):
                st.markdown(query)

            with st.chat_message("assistant"):
                with st.spinner("🧠 分析中..."):
                    try:
                        resp, tool_calls, _, _ = st.session_state.llm_manager.generate_response(
                            user_query=query,
                            model=DEFAULT_MODEL
                        )

                        # Execute tool calls if any
                        if tool_calls:
                            st.info(f"🔧 调用 {len(tool_calls)} 个工具...")

                            for tool_call in tool_calls:
                                tool_name = tool_call["name"]
                                tool_input = tool_call["input"]

                                with st.expander(f"调用工具: {tool_name}"):
                                    st.json(tool_input)

                                    # Execute tool
                                    result = st.session_state.llm_manager.execute_tool_call(
                                        tool_name, tool_input
                                    )
                                    st.json(result)

                            st.success("✅ 工具调用完成")

                        display = re.sub(r'<think>.*?</think>', '', resp, flags=re.DOTALL).strip()
                        st.markdown(display)
                        memory.add_message("assistant", resp)
                    except Exception as e:
                        err = f"❌ Error: {str(e)}"
                        st.error(err)
                        memory.add_message("assistant", err)
            st.rerun()

        for msg in memory.messages:
            with st.chat_message(msg.role):
                content = re.sub(r'<think>.*?</think>', '', msg.content, flags=re.DOTALL).strip()
                st.markdown(content)

        if prompt := st.chat_input("💭 Describe your research objective..."):
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("🧠 Analyzing..."):
                    try:
                        # Use the full tool-use loop
                        resp, tool_calls, _, _ = st.session_state.llm_manager.generate_with_tools_loop(
                            user_query=prompt,
                            model=DEFAULT_MODEL,
                            max_iterations=5
                        )

                        # Display tool calls summary if any were made
                        if tool_calls:
                            with st.expander(f"🔧 调用了 {len(tool_calls)} 个工具", expanded=False):
                                for i, tool_call in enumerate(tool_calls, 1):
                                    st.markdown(f"**{i}. {tool_call['name']}**")
                                    st.json(tool_call["input"])

                        # Display final response
                        display = re.sub(r'<think>.*?</think>', '', resp, flags=re.DOTALL).strip()
                        st.markdown(display)
                    except Exception as e:
                        err = f"❌ Error: {str(e)}"
                        st.error(err)
                        memory.add_message("assistant", err)

    # RIGHT - Scientific Panel
    with col_right:
        st.subheader("🔬 Scientific State")

        # Usage tips
        with st.expander("💡 使用提示", expanded=False):
            st.markdown("""
            **如何与AI科学家对话：**

            ✅ **好的提问方式：**
            - "分析Ibuprofen的制剂挑战，SMILES: CC(C)Cc1ccc..."
            - "这个化合物是BCS几类？需要什么制剂策略？"
            - "帮我比较固体分散体和纳米晶两种方案"

            ❌ **避免的提问：**
            - "你好"（太泛泛，AI不知道你的目标）
            - "帮我做实验"（AI只能提供计算预测）

            **AI会做什么：**
            - 🔧 自动调用PreformulationAI/FormulationAI工具
            - 💡 生成基于证据的假设（而非直接推荐）
            - 📊 解释结果的科学含义
            - ⚠️ 标注不确定性和需要验证的部分
            """)

        sci_state = get_scientific_state()

        if sci_state.compound:
            st.markdown(f"**Drug**: {sci_state.compound.drug_name}")
            if sci_state.compound.smiles:
                st.code(sci_state.compound.smiles, language="text")

            if sci_state.properties:
                props = sci_state.properties
                cols = st.columns(2)

                if props.logP is not None:
                    cols[0].metric("LogP", f"{props.logP:.2f}")
                if props.logS is not None:
                    cols[1].metric("LogS", f"{props.logS:.2f}")
                if props.bcs_class:
                    st.metric("BCS Class", props.bcs_class)
        else:
            st.info("No compound under investigation")

        st.markdown("---")
        st.markdown("### 💡 Hypotheses")

        if sci_state.hypotheses:
            for h in sci_state.hypotheses:
                with st.expander(f"{h.id}: {h.name}"):
                    st.markdown(f"**Mechanism**: {h.mechanism}")
                    st.markdown("**Evidence**:")
                    for e in h.evidence:
                        st.markdown(f"- {e}")
                    if h.confidence_score:
                        st.metric("Confidence", f"{h.confidence_score:.0%}")
        else:
            st.info("No hypotheses generated yet")

else:
    # KNOWLEDGE BASE PAGE
    st.header("📚 Knowledge Base")

    tab1, tab2, tab3 = st.tabs(["Drug Database", "Formulation Strategies", "Literature"])

    with tab1:
        st.subheader("🧪 Drug Knowledge")

        st.markdown("""
        ### Common BCS Classifications

        **BCS Class I** (High solubility, High permeability)
        - Metoprolol, Propranolol
        - Usually no formulation challenges

        **BCS Class II** (Low solubility, High permeability)
        - **Ibuprofen**, Naproxen, Ketoprofen
        - Challenge: Dissolution-limited absorption
        - Strategies: ASD, Nanocrystal, Cyclodextrin

        **BCS Class III** (High solubility, Low permeability)
        - Atenolol, Metformin
        - Challenge: Permeability barrier

        **BCS Class IV** (Low solubility, Low permeability)
        - Hydrochlorothiazide
        - Most challenging class
        """)

    with tab2:
        st.subheader("🎯 Formulation Strategies")

        strategies = {
            "Amorphous Solid Dispersion": {
                "mechanism": "Convert crystalline drug to amorphous form using polymer carriers",
                "polymers": ["PVP", "HPMC", "Soluplus"],
                "validation": ["DSC", "XRPD", "Dissolution"]
            },
            "Nanocrystal": {
                "mechanism": "Reduce particle size to nanoscale for enhanced surface area",
                "methods": ["Wet milling", "HPH", "Bottom-up precipitation"],
                "validation": ["DLS", "SEM", "Dissolution"]
            },
            "Cyclodextrin Complex": {
                "mechanism": "Host-guest inclusion complex for solubility enhancement",
                "types": ["α-CD", "β-CD", "γ-CD", "HP-β-CD"],
                "validation": ["Phase solubility", "DSC", "NMR"]
            }
        }

        for name, info in strategies.items():
            with st.expander(name):
                st.markdown(f"**Mechanism**: {info['mechanism']}")
                if 'polymers' in info:
                    st.markdown(f"**Common polymers**: {', '.join(info['polymers'])}")
                if 'methods' in info:
                    st.markdown(f"**Methods**: {', '.join(info['methods'])}")
                if 'types' in info:
                    st.markdown(f"**Types**: {', '.join(info['types'])}")
                st.markdown(f"**Validation**: {', '.join(info['validation'])}")

    with tab3:
        st.subheader("📖 Literature Intelligence")

        st.info("Literature search functionality will be integrated with PubMed API in future release")

        st.markdown("""
        ### Recent Trends

        - **Machine Learning in Formulation**: Predictive models for polymer selection
        - **QbD Approaches**: Design space optimization
        - **Continuous Manufacturing**: Hot melt extrusion, spray drying
        - **Digital Twins**: In silico formulation optimization
        """)
