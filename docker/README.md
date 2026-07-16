# FormulationOS Docker Deployment

## 概述

本目录包含用于部署Preformulation-AI和Formulation-AI服务的Docker配置。

## 文件说明

- `docker-compose.yml` - Docker Compose配置文件
- `deploy.sh` - 一键部署脚本
- `test_apis.sh` - API健康检查脚本

## 前置要求

- Docker Desktop (Mac) 或 Docker Engine (Linux)
- Docker Compose v2.0+
- 8GB+ RAM推荐

## 快速开始

### 1. 部署服务

```bash
cd /Users/Apple/FormulationOS/docker
./deploy.sh
```

这将启动：
- **Preformulation-AI** - `http://localhost:8000`
- **Formulation-AI** - `http://localhost:8001`

### 2. 测试API

```bash
./test_apis.sh
```

### 3. 配置FormulationOS

编辑 `/Users/Apple/FormulationOS/.env`：

```bash
USE_REAL_FORMULATION_TOOLS=true
PREFORMULATION_AI_BASE_URL=http://localhost:8000
FORMULATION_AI_BASE_URL=http://localhost:8001
```

### 4. 运行测试

```bash
cd /Users/Apple/FormulationOS
python demo_gpt_planner.py "设计布洛芬200mg口服制剂"
```

## 常用命令

### 查看服务状态

```bash
docker-compose ps
```

### 查看日志

```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f preformulation-ai
docker-compose logs -f formulation-ai
```

### 停止服务

```bash
docker-compose down
```

### 重启服务

```bash
docker-compose restart
```

### 重新构建

```bash
docker-compose up -d --build
```

## 故障排查

### 服务无法启动

1. 检查端口是否被占用：
```bash
lsof -i :8000
lsof -i :8001
```

2. 查看容器日志：
```bash
docker-compose logs preformulation-ai
```

### 健康检查失败

等待更长时间（模型加载可能需要1-2分钟）：
```bash
watch -n 5 'docker-compose ps'
```

### 模型文件缺失

某些服务可能需要预训练模型文件。请检查：
- Preformulation: `/app/runner/src/files/`
- Formulation-AI: `/app/models/`

## 注意事项

⚠️ **开发环境使用**：当前配置适用于本地开发环境。生产部署需要额外配置：
- SSL/TLS证书
- 反向代理（Nginx/Traefik）
- 认证和授权
- 日志聚合
- 监控和告警

## 架构说明

```
┌─────────────────┐
│ FormulationOS   │
│  (Orchestrator) │
└────────┬────────┘
         │
         ├──HTTP──► Preformulation-AI (8000)
         │          - 预处方分析
         │          - 物理化学性质预测
         │
         └──HTTP──► Formulation-AI (8001)
                    - 处方设计
                    - 辅料选择
```

## 更多信息

- [FormulationOS文档](../README.md)
- [Preformulation项目](/Users/Apple/Desktop/Preformulation)
- [Formulation-AI项目](/Users/Apple/Desktop/Formulation-AI)
