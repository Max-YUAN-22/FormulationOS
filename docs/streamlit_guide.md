# FormulationOS Streamlit UI - User Guide

## 🎯 概述

FormulationOS Streamlit UI 是一个交互式Web界面，用于：
- 自然语言工作流规划
- DAG可视化
- 实时执行监控
- 结果分析和导出

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /Users/Apple/FormulationOS
pip install -e ".[ui,llm]"
pip install graphviz  # For DAG visualization
```

### 2. 启动应用

```bash
streamlit run streamlit_app.py
```

应用将在浏览器中打开：`http://localhost:8501`

## 📖 使用指南

### Planning（规划）标签页

1. **输入查询**
   - 在文本框中输入您的研究需求
   - 示例："设计布洛芬200mg口服制剂"

2. **添加上下文（可选）**
   - 展开"Additional Context"
   - 输入药物名称、剂量、剂型

3. **选择规划模式**
   - **单一工作流**：生成一个最佳方案
   - **多候选搜索**：生成多个方案供选择
     - 勾选"Enable Multi-Candidate Search"
     - 调整候选数量（2-5个）

4. **生成工作流**
   - 点击"🚀 Generate Workflow"
   - 查看生成的工作流：
     - Rationale（理由）
     - DAG可视化图
     - 详细步骤列表

5. **比较候选方案（如果启用搜索）**
   - 查看每个候选的评分指标
   - 展开查看详细信息
   - 点击"Select Candidate"选择方案

### Execution（执行）标签页

1. **查看工作流概览**
   - 总步骤数
   - 工作流理由

2. **执行工作流**
   - 点击"▶️ Execute Workflow"
   - 等待执行完成

3. **查看实时进度**
   - 进度条显示完成百分比
   - ✅/⏳状态指示器
   - 总体状态（OK/Failed）

4. **查看步骤结果**
   - 展开每个步骤查看详情
   - Status、Duration、Version指标
   - Summary摘要
   - Warnings警告
   - 完整JSON输出

### Results（结果）标签页

1. **查看摘要指标**
   - Overall Status
   - Total Steps
   - Successful Steps
   - Total Time

2. **分析执行时间线**
   - 表格形式查看每步时间
   - 柱状图对比耗时

3. **查看聚合结果**
   - 每个工具的输出
   - 关键发现
   - 警告信息
   - 完整数据

4. **导出结果**
   - 点击"📄 Download as JSON"
   - 保存完整结果为JSON文件

## 🎨 界面功能

### 侧边栏

- **LLM Settings**：选择MiniMax M3或Mock模式
- **Available Tools**：显示所有可用工具（7个）
- **Workflow Search**：配置多候选搜索

### 主要特性

- **DAG可视化**：Graphviz有向图展示工作流结构
- **实时监控**：执行过程中的进度条和状态更新
- **结果对比**：多候选方案的并排比较
- **数据导出**：JSON格式下载完整结果

## 🔧 配置

### 环境变量

在`.env`文件中配置：

```bash
# LLM API Key
MINIMAX_API_KEY=your-api-key

# 真实工具（可选）
USE_REAL_FORMULATION_TOOLS=false
PREFORMULATION_AI_BASE_URL=http://localhost:8000
FORMULATION_AI_BASE_URL=http://localhost:8001
```

### LLM模式切换

在侧边栏选择：
- **MiniMax M3**：使用真实的MiniMax API
- **Mock (Testing)**：使用预定义的测试数据

## 📊 工作流搜索评分

启用多候选搜索时，每个方案按以下维度评分：

| 维度 | 权重 | 说明 |
|------|------|------|
| Validity | 40% | 工作流是否有效（无错误） |
| Completeness | 20% | 是否包含完整的justification |
| Complexity | 20% | 步骤数是否合理（3-6步最佳） |
| Parallelism | 10% | 能否并行执行 |
| Rationale Quality | 10% | 理由描述质量 |

**总分范围**：0-1（越高越好）

## 🛠️ 故障排查

### DAG图无法显示

**问题**：提示"Could not render DAG"

**解决**：
```bash
pip install graphviz

# macOS
brew install graphviz

# Ubuntu/Debian
sudo apt-get install graphviz
```

### LLM调用失败

**问题**：Planning失败或返回空结果

**检查**：
1. `.env`文件中的`MINIMAX_API_KEY`是否正确
2. 网络连接是否正常
3. 尝试切换到Mock模式测试

### 执行失败

**问题**：Execution Tab显示错误

**检查**：
1. 工作流是否已生成
2. 查看具体错误信息
3. 检查工具配置

## 💡 最佳实践

1. **先测试Mock模式**
   - 验证界面功能
   - 理解工作流结构

2. **使用多候选搜索**
   - 对比不同方案
   - 选择最优工作流

3. **导出结果**
   - 保存重要实验数据
   - 便于后续分析

4. **查看DAG图**
   - 理解步骤依赖关系
   - 识别并行执行机会

## 🎓 示例工作流

### 示例1：口服制剂设计

**查询**：
```
设计一个布洛芬200mg的口服制剂
```

**上下文**：
- Drug Name: Ibuprofen
- Target Dose: 200
- Dosage Form: tablet

**预期工作流**：
1. Literature → 文献检索
2. PreformulationAI → 性质预测
3. FormulationAI → 处方设计
4. FormulationDT → 溶出模拟

### 示例2：注射剂开发

**查询**：
```
开发一种紫杉醇注射液，需要评估毒性和药代动力学
```

**预期工作流**：
1. DrugDatabase → 查询药物信息
2. ToxicityPrediction → 毒性评估
3. FormulationAI → 注射剂设计
4. PBPK-AI → 药代动力学预测

## 📚 更多信息

- [FormulationOS文档](README.md)
- [工作流搜索引擎](src/formulation_os/planner/workflow_search.py)
- [自动修复机制](src/formulation_os/planner/workflow_autofixer.py)
- [Docker部署指南](docker/README.md)
