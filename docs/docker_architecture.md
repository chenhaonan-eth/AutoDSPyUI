# DSPyUI 部署架构指南

## 设计原则

**务实优先，按需演进**

本架构遵循 "先让它工作，再让它快，最后让它优雅" 的原则。避免过度设计，根据实际需求逐步优化。

## 当前问题

1. **环境混乱**: 开发和生产配置混在一起
2. **协作冲突**: 团队成员的 MLflow 数据可能互相覆盖
3. **部署不规范**: 缺少标准化的部署流程

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────┐
│           DSPyUI 单体架构                │
├─────────────────────────────────────────┤
│  开发环境 (Development)                  │
│  └── 本地运行 (uv run)                  │
├─────────────────────────────────────────┤
│  生产环境 (Production)                   │
│  ├── DSPyUI 容器 (Gradio + FastAPI)     │
│  ├── MLflow (本地文件系统)              │
│  └── 数据持久化 (Volume 挂载)           │
└─────────────────────────────────────────┘
```

### 项目结构

保持当前简洁的结构，无需拆分微服务：

```
DSPyUI/
├── dspyui/              # 主应用包
│   ├── core/            # 核心逻辑 (编译、指标、模型管理)
│   ├── api/             # FastAPI 服务
│   ├── ui/              # Gradio 界面
│   ├── utils/           # 工具函数
│   ├── i18n/            # 国际化
│   └── config.py        # 配置管理
├── data/                # 数据目录
│   ├── datasets/        # 用户数据集
│   ├── programs/        # 编译后程序
│   ├── prompts/         # 保存的提示词
│   └── mlruns/          # MLflow 数据
├── tests/               # 测试
├── docs/                # 文档
├── scripts/             # 工具脚本
├── .env.example         # 环境变量模板
├── Dockerfile           # 生产部署镜像
├── docker-compose.yml   # 生产部署配置
├── main.py              # Gradio 入口
├── serve.py             # FastAPI 入口
└── pyproject.toml       # 项目配置
```

## 环境配置

### 配置文件管理

使用单一 `.env` 文件，通过环境变量区分环境：

```bash
# .env.example (模板文件，提交到 Git)
# 复制为 .env 并填入实际值

# 环境标识
ENVIRONMENT=development  # development | production

# LLM API 配置
OPENAI_API_KEY=your_key_here
OPENAI_API_BASE=https://api.openai.com/v1

# DSPy 配置
DSPY_CACHE_ENABLED=true
DSPY_NUM_THREADS=1

# MLflow 配置
MLFLOW_ENABLED=true
MLFLOW_TRACKING_URI=./data/mlruns
MLFLOW_EXPERIMENT_NAME=dspyui-experiments

# 日志配置
LOG_LEVEL=INFO  # DEBUG | INFO | WARNING | ERROR

# 界面配置
DSPYUI_LANGUAGE=zh_CN  # zh_CN | en_US
```

### 配置类改进

```python
# dspyui/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

class Settings(BaseSettings):
    # 环境标识
    environment: str = "development"
    
    # 路径配置
    data_dir: Path = Path("./data")
    mlruns_dir: Path = Path("./data/mlruns")
    
    # MLflow 配置
    mlflow_enabled: bool = True
    mlflow_tracking_uri: str = "./data/mlruns"
    mlflow_experiment_name: str = "dspyui-experiments"
    
    # 日志配置
    log_level: str = "INFO"
    
    # 界面配置
    dspyui_language: str = "zh_CN"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

## 部署方案

### 开发环境

**直接运行，无需 Docker**

```bash
# 安装依赖
uv sync

# 启动 Gradio UI
bash webui.sh

# 或启动 FastAPI 服务
uv run python serve.py
```

### 生产环境

#### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装 uv
RUN pip install uv

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 安装依赖
RUN uv sync --frozen --no-dev

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data/mlruns /app/data/datasets /app/data/programs /app/data/prompts

# 暴露端口
EXPOSE 7860 8000

# 启动脚本
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
```

#### docker-entrypoint.sh

```bash
#!/bin/bash
set -e

# 根据 SERVICE 环境变量决定启动哪个服务
if [ "$SERVICE" = "api" ]; then
    echo "Starting FastAPI service..."
    exec uv run uvicorn dspyui.api.app:app --host 0.0.0.0 --port 8000
else
    echo "Starting Gradio UI..."
    exec uv run python main.py
fi
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  dspyui-web:
    build: .
    container_name: dspyui-web
    environment:
      - ENVIRONMENT=production
      - SERVICE=web
    env_file:
      - .env
    ports:
      - "7860:7860"
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7860"]
      interval: 30s
      timeout: 10s
      retries: 3

  dspyui-api:
    build: .
    container_name: dspyui-api
    environment:
      - ENVIRONMENT=production
      - SERVICE=api
    env_file:
      - .env
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  data:
    driver: local
```

### 部署命令

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart
```

## 团队协作

### MLflow 实验管理

**命名规范**

```python
# 在代码中使用用户名和项目名
import os
from dspyui.config import get_settings

settings = get_settings()
user = os.getenv("USER", "unknown")
project = "joke_generation"

experiment_name = f"{user}_{project}"
```

**标签系统**

```python
# 为实验添加标签
mlflow.set_tags({
    "user": user,
    "project": project,
    "type": "optimization",  # research | optimization | production | debugging
    "optimizer": "BootstrapFewShot"
})
```

### Git 工作流

```bash
# 功能分支开发
git checkout -b feature/new-metric

# 提交代码
git add .
git commit -m "feat: 添加新的评估指标"

# 推送并创建 PR
git push origin feature/new-metric
```

### 数据管理

**目录结构**

```
data/
├── datasets/           # 用户数据集 (Git ignore)
├── programs/           # 编译后程序 (Git ignore)
├── prompts/            # 提示词 (可选择性提交)
└── mlruns/            # MLflow 数据 (Git ignore)
```

**.gitignore 配置**

```gitignore
# 数据文件
data/datasets/
data/programs/
data/mlruns/

# 环境配置
.env

# Python
__pycache__/
*.pyc
.pytest_cache/
```

## 性能优化路线图

### 阶段 1: 单机部署 (当前)

**适用场景**: 团队 < 5 人，用户 < 100

**技术栈**:
- 单个 Docker 容器
- 本地文件系统
- MLflow 默认配置 (SQLite + 文件系统)

**成本**: 最低

### 阶段 2: 性能优化 (用户 > 100)

**触发条件**:
- MLflow UI 响应变慢
- 并发编译任务排队
- 磁盘空间不足

**优化措施**:
1. 添加 Redis 缓存 (LLM 响应缓存)
2. 使用 PostgreSQL (替代 SQLite)
3. 配置 Nginx 反向代理

**docker-compose.yml 扩展**:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: mlflow
      POSTGRES_USER: mlflow
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  redis_data:
  postgres_data:
```

### 阶段 3: 水平扩展 (用户 > 1000)

**触发条件**:
- 单机 CPU/内存瓶颈
- 需要高可用性
- 多地域部署需求

**优化措施**:
1. 使用对象存储 (MinIO/S3) 存储 artifacts
2. 多实例部署 + 负载均衡
3. 考虑 Kubernetes (如果真的需要)

## 监控和维护

### 健康检查

```python
# dspyui/api/routes/health.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "dspyui-api",
        "version": "1.0.0"
    }
```

### 日志管理

```python
# dspyui/utils/logger.py
import logging
from dspyui.config import get_settings

settings = get_settings()

logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("dspyui")
```

### 备份策略

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 备份 MLflow 数据
cp -r ./data/mlruns "$BACKUP_DIR/"

# 备份编译后的程序
cp -r ./data/programs "$BACKUP_DIR/"

# 备份提示词
cp -r ./data/prompts "$BACKUP_DIR/"

echo "Backup completed: $BACKUP_DIR"
```

## 实施计划

### 第 1 周: 配置优化
- [ ] 改进 `config.py` 使用 Pydantic Settings
- [ ] 创建 `.env.example` 模板
- [ ] 更新文档说明环境变量

### 第 2 周: Docker 化
- [ ] 编写 `Dockerfile`
- [ ] 编写 `docker-compose.yml`
- [ ] 测试容器部署流程
- [ ] 编写部署文档

### 第 3 周: 团队协作规范
- [ ] 制定 MLflow 实验命名规范
- [ ] 配置 Git 工作流
- [ ] 编写协作指南
- [ ] 团队培训

### 第 4 周: 监控和维护
- [ ] 添加健康检查接口
- [ ] 配置日志系统
- [ ] 编写备份脚本
- [ ] 编写运维文档

## 关键原则

1. **KISS (Keep It Simple)**: 保持架构简单，避免过度设计
2. **YAGNI (You Aren't Gonna Need It)**: 只实现当前需要的功能
3. **渐进式优化**: 根据实际需求逐步演进，不要一开始就构建复杂系统
4. **数据优先**: 关注数据存储、版本管理和检索效率
5. **用户反馈驱动**: 根据真实用户反馈迭代，而不是理论设计

## 总结

这个架构设计专注于解决当前的实际问题，避免了微服务、Kubernetes 等过度复杂的技术。通过简单的 Docker 部署和清晰的配置管理，实现了环境隔离和团队协作。

当项目真正遇到性能瓶颈或规模扩张时，可以按照路线图逐步优化。记住：**先让它工作，再让它快，最后让它优雅。**