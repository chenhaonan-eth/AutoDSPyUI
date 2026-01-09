# MLflow 集成指南

DSPyUI 集成了 MLflow 用于实验追踪、模型注册和程序生命周期管理。

## 功能概述

- **实验追踪**: 自动记录编译参数、评估指标和工件
- **模型注册**: 将编译后的程序注册到 MLflow Model Registry
- **版本管理**: 管理模型版本和阶段（Staging、Production、Archived）
- **推理追踪**: 记录批量推理的统计信息和 LLM 调用详情

## 部署架构

DSPyUI 使用 Docker Compose 部署 MLflow 服务，包含三个核心组件：

```
┌─────────────────────────────────────────┐
│        DSPyUI + MLflow 架构              │
├─────────────────────────────────────────┤
│  DSPyUI (本地运行)                       │
│  └── 连接到 Docker MLflow               │
├─────────────────────────────────────────┤
│  Docker Compose 服务                     │
│  ├── MLflow Server (端口 5000)          │
│  ├── PostgreSQL (元数据存储)            │
│  └── MinIO (工件存储)                   │
└─────────────────────────────────────────┘
```

**组件说明**：
- **MLflow Server**: 追踪服务器和 Web UI
- **PostgreSQL**: 存储实验元数据（替代 SQLite，支持并发）
- **MinIO**: S3 兼容的对象存储，存储模型工件

**优势**：
- 生产就绪的存储方案
- 支持并发访问和团队协作
- 数据持久化在 Docker 卷中
- 易于扩展和迁移

## 快速开始

### 1. 启动 MLflow Docker 服务

DSPyUI 使用 Docker Compose 运行 MLflow 服务，包含：
- **PostgreSQL**: 存储实验元数据
- **MinIO**: S3 兼容的对象存储，用于存储模型工件
- **MLflow Server**: 追踪服务器和 UI

```bash
# 进入 docker-compose 目录
cd docker/docker-compose

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f mlflow
```

### 2. 配置环境变量

在项目根目录的 `.env` 文件中配置：

```bash
# MLflow 基础配置
MLFLOW_ENABLED=true
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=dspyui-experiments

# Autolog 配置（可选）
MLFLOW_LOG_TRACES=true
MLFLOW_LOG_TRACES_FROM_COMPILE=false
MLFLOW_LOG_TRACES_FROM_EVAL=true
MLFLOW_LOG_COMPILES=true
MLFLOW_LOG_EVALS=true
```

### 3. 启动 DSPyUI

```bash
# 返回项目根目录
cd ../..

# 启动 DSPyUI（会自动检测 MLflow 服务）
bash webui.sh
```

### 4. 访问 MLflow UI

打开浏览器访问 `http://localhost:5000`，可以：

- 查看实验运行记录
- 比较不同编译配置的效果
- 管理注册的模型版本
- 查看详细的评估结果

### 5. 访问 MinIO 控制台（可选）

打开浏览器访问 `http://localhost:9001`：

- 用户名: `minio`
- 密码: `minio123`

可以查看和管理存储的模型工件。

## 核心功能

### 编译追踪

每次编译 DSPy 程序时，MLflow 会自动记录：

- **参数**: 输入输出字段、模型配置、优化器设置等
- **指标**: 基线分数、评估分数、分数提升等
- **工件**: 编译后的程序 JSON、优化后的提示词、数据集文件

### 模型注册

编译完成后，可以将程序注册到 Model Registry：

1. 在编译页面点击"注册模型"按钮
2. 输入模型名称和描述
3. 选择模型阶段（Staging/Production）

### 推理追踪

运行批量推理时，MLflow 会记录：

- 总行数、成功数、错误数
- Token 使用量和延迟统计
- 详细的 LLM 调用追踪（如果启用）

## 配置选项

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `MLFLOW_ENABLED` | `true` | 是否启用 MLflow 集成 |
| `MLFLOW_TRACKING_URI` | `http://localhost:5000` | MLflow 追踪服务器地址 |
| `MLFLOW_EXPERIMENT_NAME` | `dspyui-experiments` | 实验名称 |
| `MLFLOW_LOG_TRACES` | `true` | 是否记录 LLM 调用追踪 |
| `MLFLOW_LOG_TRACES_FROM_COMPILE` | `false` | 是否记录编译过程的追踪 |
| `MLFLOW_LOG_TRACES_FROM_EVAL` | `true` | 是否记录评估过程的追踪 |
| `MLFLOW_LOG_COMPILES` | `true` | 是否自动记录编译信息 |
| `MLFLOW_LOG_EVALS` | `true` | 是否自动记录评估信息 |

## Docker Compose 管理

### 常用命令

```bash
# 启动服务
cd docker/docker-compose
docker-compose up -d

# 停止服务
docker-compose down

# 停止并删除数据卷（清空所有数据）
docker-compose down -v

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f mlflow
docker-compose logs -f postgres
docker-compose logs -f minio

# 查看服务状态
docker-compose ps
```

### 数据持久化

Docker Compose 使用命名卷存储数据：

- `pgdata`: PostgreSQL 数据库数据
- `minio-data`: MinIO 对象存储数据

即使容器重启，数据也会保留。如需完全清空数据，使用 `docker-compose down -v`。

### 端口配置

默认端口映射：

- `5000`: MLflow UI 和 API
- `5432`: PostgreSQL（可选，用于外部访问）
- `9000`: MinIO API
- `9001`: MinIO 控制台

如需修改端口，编辑 `docker/docker-compose/.env` 文件。

## 最佳实践

1. **实验命名**: 使用描述性的实验名称，便于后续查找
2. **模型注册**: 只注册表现良好的模型版本
3. **阶段管理**: 合理使用 Staging 和 Production 阶段
4. **追踪控制**: 在生产环境中可以关闭详细追踪以提升性能
5. **定期备份**: 定期备份 Docker 卷数据

## 故障排除

### MLflow 服务器连接失败

**症状**: DSPyUI 启动时提示无法连接到 MLflow

**解决方案**:
1. 检查 Docker 服务是否运行: `docker-compose ps`
2. 检查 MLflow 健康状态: `curl http://localhost:5000/health`
3. 查看 MLflow 日志: `docker-compose logs mlflow`
4. 确认 `.env` 中 `MLFLOW_TRACKING_URI` 配置正确

### 追踪数据丢失

**症状**: 实验记录突然消失

**解决方案**:
1. 检查 Docker 卷是否存在: `docker volume ls | grep mlflow`
2. 确认没有执行 `docker-compose down -v`（会删除数据）
3. 检查 PostgreSQL 连接: `docker-compose logs postgres`

### 模型注册失败

**症状**: 注册模型时报错

**解决方案**:
1. 检查模型名称是否符合 MLflow 命名规范（字母、数字、下划线、连字符）
2. 确认 MinIO 服务正常: `docker-compose logs minio`
3. 检查存储空间是否充足: `docker system df`

### 端口冲突

**症状**: Docker Compose 启动失败，提示端口被占用

**解决方案**:
1. 检查端口占用: `lsof -i :5000`
2. 修改 `docker/docker-compose/.env` 中的端口配置
3. 重启 Docker Compose

### 性能问题

**症状**: MLflow UI 响应缓慢

**解决方案**:
1. 关闭不必要的追踪: 设置 `MLFLOW_LOG_TRACES=false`
2. 清理旧实验数据
3. 增加 Docker 资源限制（CPU、内存）

## 数据迁移

### 从本地 SQLite 迁移到 Docker

如果之前使用本地 SQLite 存储 MLflow 数据，可以迁移到 Docker：

```bash
# 1. 导出旧数据（如果需要）
# 注意：这需要手动操作，MLflow 没有内置迁移工具

# 2. 启动新的 Docker 服务
cd docker/docker-compose
docker-compose up -d

# 3. 更新 .env 配置
# MLFLOW_TRACKING_URI=http://localhost:5000

# 4. 重新运行编译任务，数据会自动记录到新服务
```

## 高级配置

### 使用远程 MLflow 服务器

如果团队有共享的 MLflow 服务器：

```bash
# .env
MLFLOW_TRACKING_URI=https://mlflow.your-company.com
```

### 自定义实验名称

为不同项目使用不同的实验名称：

```bash
# .env
MLFLOW_EXPERIMENT_NAME=my-project-experiments
```

### 禁用 MLflow

如果不需要实验追踪：

```bash
# .env
MLFLOW_ENABLED=false
```

## 从本地 MLflow 迁移

如果你之前使用本地 MLflow（SQLite + 文件系统），可以按以下步骤迁移到 Docker MLflow。

### 变更对比

| 项目 | 本地 MLflow | Docker MLflow |
|------|------------|---------------|
| 启动方式 | `bash webui.sh --mlflow` | `docker-compose up -d` |
| 元数据存储 | SQLite (`mlflow_data/`) | PostgreSQL (Docker 卷) |
| 工件存储 | 本地文件系统 (`mlartifacts/`) | MinIO (Docker 卷) |
| 并发支持 | 有限 | 完全支持 |
| 团队协作 | 困难 | 容易 |

### 迁移步骤

#### 1. 备份现有数据（可选）

```bash
# 备份本地 MLflow 数据
cp -r mlartifacts mlartifacts.backup
cp -r mlflow_data mlflow_data.backup
cp -r mlruns mlruns.backup
```

#### 2. 启动 Docker 服务

```bash
cd docker/docker-compose
docker-compose up -d
docker-compose ps  # 验证服务运行
```

#### 3. 更新环境变量

编辑 `.env` 文件，移除本地存储配置：

```bash
# 移除这些行（已不需要）
# MLFLOW_BACKEND_STORE_URI="sqlite:///mlflow_data/mlflow.db"
# MLFLOW_ARTIFACT_ROOT="./mlartifacts"
# MLFLOW_LOG_FILE="mlflow_data/mlflow.log"

# 确保这些配置正确
MLFLOW_ENABLED="true"
MLFLOW_TRACKING_URI="http://localhost:5000"
MLFLOW_EXPERIMENT_NAME="dspyui-experiments"
```

#### 4. 测试新配置

```bash
cd ../..
bash webui.sh
open http://localhost:5000  # 访问 MLflow UI
```

#### 5. 清理旧数据（可选）

确认新系统工作正常后：

```bash
rm -rf mlartifacts mlflow_data
# 保留 mlruns 作为备份（如果需要）
```

### 数据迁移选项

**选项 1: 重新运行实验**（推荐）
- 最简单的方法
- 在新系统中重新运行重要的实验

**选项 2: 手动导出/导入**
```bash
# 从旧系统导出
mlflow experiments export --experiment-id 0 --output-dir ./export

# 导入到新系统
mlflow experiments import --input-dir ./export
```

**选项 3: 数据库迁移**（复杂）
- 需要从 SQLite 导出数据并导入到 PostgreSQL
- 需要迁移工件到 MinIO
- 建议咨询 DBA

### 迁移常见问题

**Q: 旧数据会丢失吗？**
A: 不会。旧数据仍保存在本地目录中，可以选择保留或删除。

**Q: 可以回退到旧系统吗？**
A: 可以。只要保留了旧数据目录，随时可以回退：
```bash
docker-compose down
# 恢复旧的 .env 配置
bash webui.sh --mlflow
```

**Q: Docker 服务占用太多资源怎么办？**
A: 在 Docker Desktop 设置中调整资源限制，或不使用时停止服务：
```bash
docker-compose down
```

## 相关文档

- [系统架构文档](./architecture.md)
- [模型部署与数据飞轮](./serving_and_feedback.md)
- [MLflow 官方文档](https://mlflow.org/docs/latest/index.html)
- [MinIO 文档](https://min.io/docs/minio/linux/index.html)
