# Render 重新部署完整指南

## 问题
当前Render部署显示旧的中文版本，多次手动部署无效。需要完全重置。

## 解决方案：删除旧服务并重新创建

### 步骤 1：删除旧服务
1. 登录 https://dashboard.render.com/
2. 找到 `formulationos` 服务
3. 点击进入服务详情页
4. 进入 **Settings** → 滚动到最底部
5. 点击 **Delete Web Service**
6. 输入服务名确认删除

### 步骤 2：创建新服务
1. 回到 Dashboard，点击 **"New +"** → **"Web Service"**
2. 选择 **"Connect to GitHub"**
3. 找到并选择 **`Max-YUAN-22/FormulationOS`** 仓库
4. 点击 **"Connect"**

### 步骤 3：配置服务
填写以下信息：

**Basic Settings:**
- **Name**: `formulationos` （或任何你想要的名字）
- **Region**: `Oregon (US West)` （免费层）
- **Branch**: `main` ⚠️ **非常重要**
- **Root Directory**: 留空
- **Runtime**: `Python 3`

**Build & Deploy:**
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `streamlit run FormulationOS_Enterprise.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`

**Instance Type:**
- 选择 **Free** (0.5GB RAM)

### 步骤 4：配置环境变量
在创建服务页面或创建后进入 Settings → Environment，添加：

**必需的环境变量：**
```
PYTHON_VERSION = 3.11.0
GPT_BASE_URL = https://www.cun.ai/v1
CLAUDE_BASE_URL = https://www.cun.ai
MINIMAX_BASE_URL = https://api.minimaxi.com/v1
```

**需要手动添加的密钥（点击 "Add Environment Variable"）：**
```
GPT_API_KEY = sk-rpuahfQDWzbqQKW0AbzGJpo7OMpftFRAaOsFzQUXqUXlMMNW
CLAUDE_API_KEY = (你的Claude API密钥)
MINIMAX_API_KEY = (你的Minimax API密钥，如果有)
PREFORMULATION_AI_API_KEY = (你的PreformulationAI密钥，如果有)
FORMULATION_AI_API_KEY = (你的FormulationAI密钥，如果有)
```

**注意：** 对于API密钥，建议设置为 **Secret**（不要选择 sync: false，直接输入值）

### 步骤 5：部署
1. 点击 **"Create Web Service"**
2. Render会自动开始构建和部署
3. 查看 **Logs** 标签页监控部署进度

### 步骤 6：验证部署成功
部署完成后（通常3-5分钟）：

1. 访问Render提供的URL（类似 `https://formulationos-xxx.onrender.com`）
2. **检查标题栏应该显示**: `🧬 FormulationOS v3.5.1`
3. **检查功能**:
   - ✅ 5个导航按钮：Home, AI Workspace, Knowledge Base, Research
   - ✅ 首页有详细的PreformulationAI/FormulationAI平台介绍（可展开查看5/7个模块）
   - ✅ Knowledge Base有4个标签页：Drug Database, Formulation Strategies, Literature Intelligence, Training Data
   - ✅ Research页面显示多智能体路线图
   - ✅ Demo案例是英文的（Ibuprofen, Paclitaxel, Celecoxib）

### 可能遇到的问题

**问题1: 部署失败 - ModuleNotFoundError**
**解决**: 检查 requirements.txt 是否包含所有依赖
```bash
streamlit>=1.28.0
anthropic>=0.18.0
openai>=1.12.0
pandas>=2.0.0
matplotlib>=3.7.0
plotly>=5.14.0
```

**问题2: 部署成功但打不开**
**解决**: 
- 检查 Start Command 是否正确
- 确认使用了 `--server.port=$PORT`（Render动态分配端口）
- 确认使用了 `--server.address=0.0.0.0`

**问题3: 页面报错**
**解决**: 检查环境变量，特别是 GPT_API_KEY 是否正确设置

### 自动部署设置
服务创建后，确保启用自动部署：
1. Settings → Build & Deploy
2. **Auto-Deploy**: 选择 **Yes**
3. **Branch**: 确认是 **main**

之后每次 `git push` 到 main 分支，Render会自动重新部署。

## 为什么需要重新创建？
旧服务可能存在：
- GitHub连接配置错误（使用了错误的commit或branch）
- 缓存损坏（清除缓存无效）
- 初始部署时的配置错误遗留
- Render内部的deployment pipeline卡住

重新创建服务可以完全避免这些问题，从干净的状态开始。

## 预期结果
新部署的网站应该和本地 http://localhost:8509 **完全一致**：
- 版本号 v3.5.1
- 详细的平台介绍（12个AI模块）
- 扩展的Knowledge Base（4个标签页，包含BCS分类、制剂策略等专业内容）
- Research页面（多智能体研发路线图）
- 英文的Demo案例

部署完成后将URL发给我验证！
