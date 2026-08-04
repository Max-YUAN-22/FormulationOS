# FormulationOS - Render 部署指南

## 优势

相比Streamlit Cloud，Render提供：
- ✅ 更灵活的配置
- ✅ 持久化存储支持
- ✅ 自定义域名
- ✅ 更大的资源限制
- ✅ 数据库集成（PostgreSQL/Redis）

---

## 部署步骤

### 1. 确保代码已推送到GitHub

```bash
git add render.yaml README_RENDER_DEPLOYMENT.md
git commit -m "Add Render deployment configuration"
git push origin main
```

### 2. 访问Render Dashboard

https://dashboard.render.com/

### 3. 创建新的Web Service

- 点击 **"New +"** → **"Web Service"**
- 连接GitHub账号
- 选择仓库：`Max-YUAN-22/FormulationOS`
- Render会自动检测到 `render.yaml` 配置文件

### 4. 配置环境变量

在Render Dashboard的 **"Environment"** 标签中添加：

| Key | Value |
|-----|-------|
| `CLAUDE_API_KEY` | 你的Claude API密钥 |
| `CLAUDE_BASE_URL` | https://www.cun.ai |
| `GPT_API_KEY` | 你的OpenAI API密钥 |
| `GPT_BASE_URL` | https://api.openai.com/v1 |
| `MINIMAX_API_KEY` | 你的MiniMax API密钥 |
| `MINIMAX_BASE_URL` | https://api.minimaxi.com/v1 |

**重要：点击每个密钥右侧的 🔒 图标，标记为 "Secret"**

### 5. 部署配置确认

Render会自动从 `render.yaml` 读取配置：

- **Runtime**: Python
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `streamlit run FormulationOS_Complete.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
- **Plan**: Free (可升级到付费计划获得更多资源)

### 6. 点击 "Create Web Service"

Render会：
1. 克隆GitHub仓库
2. 安装依赖（约2-3分钟）
3. 启动应用
4. 提供公开URL：`https://formulationos.onrender.com`

### 7. 访问应用

部署完成后，访问Render提供的URL测试应用。

---

## 自动部署

每次推送到GitHub `main` 分支，Render会自动重新部署应用。

---

## 本地测试Render配置

在本地测试Render的启动命令：

```bash
streamlit run FormulationOS_Complete.py --server.port 8503 --server.address 0.0.0.0 --server.headless true
```

---

## 升级到付费计划

Render Free计划限制：
- 15分钟无活动后自动休眠
- 冷启动需要30-60秒
- 每月750小时免费运行时间

如需：
- 24/7在线
- 更快的响应速度
- 更多计算资源

可升级到 **Starter ($7/月)** 或更高计划。

---

## 故障排查

### 问题1：部署失败 - 依赖安装错误

检查 `requirements.txt` 是否完整。

### 问题2：应用启动失败

查看Render Dashboard的 **"Logs"** 标签，检查错误信息。

### 问题3：API调用失败

确认环境变量中的API密钥配置正确，且已标记为 "Secret"。

### 问题4：应用频繁休眠

Free计划15分钟无活动会休眠。升级到付费计划可避免。

---

## 自定义域名（可选）

Render支持自定义域名：

1. 在Render Dashboard → **"Settings"** → **"Custom Domain"**
2. 添加你的域名（如 `app.formulationos.com`）
3. 在域名DNS设置中添加Render提供的CNAME记录

---

## 监控和日志

- **Logs**: 实时查看应用日志
- **Metrics**: CPU、内存使用情况
- **Events**: 部署历史和状态

---

## 成本估算

| 计划 | 价格 | 特性 |
|------|------|------|
| **Free** | $0/月 | 750小时/月，15分钟自动休眠 |
| **Starter** | $7/月 | 24/7运行，无休眠 |
| **Standard** | $25/月 | 更多资源，优先支持 |

对于学术演示和原型，Free计划通常足够。
