# FormulationOS 部署指南

## Streamlit Community Cloud 部署（推荐）

### 前置准备

1. **确保代码已推送到GitHub**：
   ```bash
   git add .
   git commit -m "Add Streamlit deployment files"
   git push origin main
   ```

2. **准备API密钥**（用于Streamlit Cloud配置）：
   - Claude API Key
   - OpenAI API Key  
   - MiniMax API Key

### 部署步骤

#### 1. 访问 Streamlit Community Cloud
https://share.streamlit.io/

#### 2. 连接GitHub账号
- 点击 "New app"
- 授权Streamlit访问你的GitHub仓库

#### 3. 配置应用
- **Repository**: `Max-YUAN-22/FormulationOS`
- **Branch**: `main`
- **Main file path**: `FormulationOS_Complete.py`

#### 4. 配置环境变量（Secrets）
在Streamlit Cloud的 "Advanced settings" → "Secrets" 中添加：

```toml
CLAUDE_API_KEY = "your-claude-api-key-here"
CLAUDE_BASE_URL = "https://www.cun.ai"

GPT_API_KEY = "your-openai-api-key-here"
GPT_BASE_URL = "https://api.openai.com/v1"

MINIMAX_API_KEY = "your-minimax-api-key-here"
MINIMAX_BASE_URL = "https://api.minimaxi.com/v1"
```

**注意：请替换为你自己的API密钥**

#### 5. 修改代码读取Secrets
在 `FormulationOS_Complete.py` 中将硬编码的API密钥改为：

```python
import streamlit as st

# Config from Streamlit Secrets
CLAUDE_API_KEY = st.secrets.get("CLAUDE_API_KEY", "")
GPT_API_KEY = st.secrets.get("GPT_API_KEY", "")
MINIMAX_API_KEY = st.secrets.get("MINIMAX_API_KEY", "")
CLAUDE_BASE_URL = st.secrets.get("CLAUDE_BASE_URL", "https://www.cun.ai")
GPT_BASE_URL = st.secrets.get("GPT_BASE_URL", "https://api.openai.com/v1")
MINIMAX_BASE_URL = st.secrets.get("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1")
```

#### 6. 点击 "Deploy"
- Streamlit Cloud会自动安装依赖（requirements.txt）
- 大约2-3分钟后部署完成
- 获得公开URL：`https://formulationos.streamlit.app`

### 自动更新

每次推送到GitHub main分支，Streamlit Cloud会自动重新部署。

---

## 本地运行

```bash
cd /Users/Apple/FormulationOS
streamlit run FormulationOS_Complete.py --server.port 8503
```

访问：http://localhost:8503

---

## 故障排查

### 问题1：依赖安装失败
检查 `requirements.txt` 是否包含所有必需的包：
- streamlit
- anthropic
- openai
- httpx
- pydantic
- pyyaml

### 问题2：API调用失败
确认Secrets中的API密钥正确配置。

### 问题3：Import错误
确保 `src/formulation_os/` 目录结构完整，所有 `__init__.py` 文件存在。

---

## 支持的平台

✅ **Streamlit Community Cloud**（推荐）
- 免费
- 自动从GitHub同步
- 提供公开URL

✅ **Hugging Face Spaces**
- 免费
- 学术友好
- 支持GPU

✅ **Railway / Render**
- 付费但更灵活
- 支持自定义域名
