# FormulationOS - Demo Guide & Feature Showcase

**An Agentic AI Scientist for Pharmaceutical Formulation**

Version: 3.5 (Phase 31 Complete)  
Date: August 4, 2026  
Deployment: https://formulationos.onrender.com (Render) | http://localhost:8504 (Local)

---

## 🎯 Executive Summary

FormulationOS is an enterprise-grade agentic AI system for pharmaceutical formulation research, inspired by AstraZeneca's ChatInvent (Drug Discovery Today, 2026). It integrates 12 AI modules (PreformulationAI + FormulationAI) with natural language interface, real-time reasoning display, and multimodal output capabilities.

**Key Differentiators:**
- ✅ **ChatInvent-inspired transparency** - Real-time reasoning display
- ✅ **Multimodal output** - Text + molecular structures + auto-generated plots
- ✅ **Dual-mode operation** - Fast Mode (quick) vs Deep Analysis (comprehensive)
- ✅ **Enterprise-grade** - Persistent knowledge base, session management, training data export

---

## 🚀 Core Features

### 1. Natural Language Interface
- **Bilingual Support**: English & Chinese
- **Context-Aware**: Multi-turn dialogue with memory retention
- **Smart Tool Selection**: Autonomously selects from 12 AI modules

### 2. Real-Time Reasoning Display
**Inspired by AstraZeneca's ChatInvent**
- Blue reasoning cards show AI thinking process
- Step-by-step tool execution visualization
- Transparent decision-making

### 3. Multimodal Output (NEW in Phase 31)

#### 🧬 Molecular Structure Visualization
- Auto-detects SMILES in user input
- Displays 2D molecular structure using RDKit
- Example: `SMILES: CC(C)Cc1ccc(cc1)C(C)C(=O)O` → renders Ibuprofen structure

#### 📊 Auto-Generated Visualizations
System intelligently generates relevant plots based on analysis type:

1. **Formulation Strategy Comparison**
   - Horizontal bar chart ranking strategies
   - Triggered by: formulation analysis keywords
   - Shows: Solid Dispersion, Nanocrystal, Cyclodextrin, etc.

2. **pH Stability Profile**
   - Colored bar chart (red=unstable, yellow=moderate, green=stable)
   - Triggered by: pH or stability mentions
   - Shows: Stability scores across pH 1-12

3. **Solubility-Temperature Curves**
   - Line plot showing solubility increase with temperature
   - Triggered by: solubility analysis
   - Shows: mg/mL vs °C relationship

### 4. Dual Analysis Modes (NEW in Phase 31)

#### ⚡ Fast Mode (Default)
- **Purpose**: Quick responses for routine queries
- **Mechanism**: Single AI agent, 5 tool iterations
- **Use Case**: BCS classification, quick property lookup

#### 🧠 Deep Analysis Mode
- **Purpose**: Comprehensive, multi-perspective analysis
- **Mechanism**: Enhanced single-agent (10 iterations) + future multi-agent orchestration
- **Use Case**: Complex formulation strategy evaluation, stability analysis

**Toggle via buttons at top of AI Workspace**

### 5. Persistent Knowledge Base
- **Storage**: SQLite database (`formulation_knowledge.db`)
- **Captures**:
  - All user-AI conversations
  - Drug analyses (SMILES, drug name, properties)
  - Tool call history
  - Formulation strategies evaluated
- **Export**: JSON format for model training

### 6. Session Management
- **Multiple Sessions**: Create and switch between conversations
- **Session History**: Sidebar shows all past sessions
- **Resume Anywhere**: Continue previous analyses seamlessly

---

## 🧪 Demo Scenarios

### Scenario 1: Complete Drug Analysis with Visualizations

**Input:**
```
帮我分析Ibuprofen（布洛芬）的制剂挑战，SMILES: CC(C)Cc1ccc(cc1)C(C)C(=O)O，我想改善其口服生物利用度
```

**Expected Output:**
1. ✅ User message displays immediately
2. ✅ "🧠 Analyzing your query..." status
3. ✅ Real-time reasoning: Step 1, 2, 3... (5 steps)
4. ✅ Comprehensive analysis:
   - BCS Class II classification
   - LogP, LogS, pKa values
   - Formulation strategy recommendations
5. ✅ **🧬 Molecular Structure** section with Ibuprofen 2D structure
6. ✅ **📊 Analysis Visualizations**:
   - Formulation Strategy Ranking bar chart
   - pH Stability Profile
   - Solubility vs Temperature curve
7. ✅ Feedback buttons (👍👎)

**Time**: ~15-30 seconds

---

### Scenario 2: Deep Analysis Mode

**Steps:**
1. Click **"🧠 Deep Analysis"** button at top
2. Input: "Evaluate the best formulation strategy for BCS Class II drugs"
3. Observe:
   - "Deep Analysis Mode" indicator
   - More comprehensive tool calls (up to 10)
   - More detailed reasoning process
   - Enhanced recommendations

**Difference from Fast Mode:**
- Fast: 5 iterations, ~20s
- Deep: 10 iterations, ~40s, more thorough

---

### Scenario 3: Knowledge Base Review

**Steps:**
1. Click **"📚 Knowledge Base"** in top navigation
2. View statistics:
   - Total conversations
   - Drug analyses performed
   - Tool calls made
3. Browse **Recent Training Examples**
   - Drug name, SMILES, timestamp
   - Tool calls executed
   - AI response preview
4. Export training data (JSON)

**Use Case**: Demonstrate data capture for model fine-tuning

---

## 🏗️ System Architecture

### Three-Layer Design

```
┌─────────────────────────────────────────┐
│          LLM Layer                      │
│  - Multi-provider (Claude, GPT-4o)     │
│  - Tool-use loop with result feedback  │
│  - Conversation memory management      │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│          Tool Layer                     │
│  - 5 PreformulationAI modules          │
│  - 7 FormulationAI modules             │
│  - REST API integration                │
│  - Visualization tools (NEW)           │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│        Storage Layer                    │
│  - SQLite knowledge base               │
│  - Session state management            │
│  - Training data export                │
└─────────────────────────────────────────┘
```

---

## 📚 Scientific Foundation

### Inspired by Industry Research

**ChatInvent** (AstraZeneca, Drug Discovery Today 2026)
- Multi-agent architecture for drug discovery
- Real-time reasoning transparency
- User feedback for continuous improvement

### Built on Validated Models

**PreformulationAI & FormulationAI**
- Machine learning models trained on experimental data
- BCS classification accuracy: >85%
- Continuous model updates from user interactions

---

## 🎓 Key Talking Points for Presentation

1. **Enterprise-Grade Quality**
   - "Not a prototype - production-ready system with persistent storage"
   - "Inspired by top-tier pharma research (AstraZeneca, Drug Discovery Today)"

2. **Multimodal Capabilities**
   - "Beyond chatbots - molecular structures, intelligent charts, comprehensive analysis"
   - "System automatically generates relevant visualizations based on analysis type"

3. **Transparency & Trust**
   - "Real-time reasoning display shows exactly what AI is thinking"
   - "Users can verify every step of the analysis process"

4. **Flexible Analysis**
   - "Fast Mode for quick queries, Deep Analysis for comprehensive research"
   - "Future: True multi-agent orchestration for complex problems"

5. **Data-Driven Improvement**
   - "Every interaction captured for model training"
   - "Knowledge base enables RAG and continuous learning"

---

## 🐛 Known Limitations & Future Work

### Current Limitations
1. **Multi-Agent Workflow**: Placeholder implementation (enhanced single-agent mode)
2. **RDKit Dependency**: Required for molecular visualization
3. **Plot Intelligence**: Rule-based visualization selection (future: ML-based)

### Planned Enhancements (Phase 32+)
1. **True Multi-Agent System**: Full Workflow orchestration with parallel agents
2. **3D Molecular Visualization**: Interactive 3D structures
3. **Real-time Collaboration**: Multi-user sessions
4. **Advanced RAG**: Vector database for literature search
5. **Experiment Planning**: Automated DOE generation

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| **Response Time (Fast Mode)** | 15-30s |
| **Response Time (Deep Mode)** | 30-60s |
| **Supported Drugs** | Any SMILES input |
| **Tool Accuracy** | >85% (BCS classification) |
| **Languages** | English, Chinese |
| **Concurrent Sessions** | Unlimited (local) |

---

## 🔗 Access Information

- **Local**: http://localhost:8504
- **Production**: https://formulationos.onrender.com
- **Code**: https://github.com/Max-YUAN-22/FormulationOS
- **PreformulationAI**: https://preformulationai.computpharm.org
- **FormulationAI**: https://formulationai.computpharm.org

---

## 📝 Q&A Preparation

**Q: How is this different from ChatGPT for drug discovery?**
A: Three key differences:
1. **Specialized Tools**: 12 validated AI models specifically for formulation (not general knowledge)
2. **Transparent Reasoning**: See exactly which tools are called and why
3. **Multimodal Output**: Automatic molecular structures and intelligent visualizations

**Q: Can this replace pharmaceutical scientists?**
A: No - it's designed to **augment** scientists, not replace them. Think of it as an intelligent research assistant that can:
- Quickly screen compounds
- Generate initial hypotheses
- Visualize complex data
- Free scientists to focus on experimental design and decision-making

**Q: What about data privacy?**
A: Local deployment option ensures sensitive data never leaves your infrastructure. Knowledge base is SQLite (file-based, no cloud dependency).

**Q: How accurate are the predictions?**
A: Models achieve >85% accuracy on BCS classification (validated against experimental data). However, always verify critical predictions with experiments.

---

**Contact**: Max YUAN  
**Last Updated**: August 4, 2026  
**Version**: Phase 31 Complete
