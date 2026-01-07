# MLflow 集成指南

DSPyUI 集成了 MLflow 用于实验追踪、模型注册和程序生命周期管理。

## 功能概述

- **实验追踪**: 自动记录编译参数、评估指标和工件
- **模型注册**: 将编译后的程序注册到 MLflow Model Registry
- **版本管理**: 管理模型版本和阶段（Staging、Production、Archived）
- **推理追踪**: 记录批量推理的统计信息和 LLM 调用详情

## 快速开始

### 1. 启动 MLflow 服务器

```bash
# 在单独的终端中启动 MLflow 服务器
uv run mlflow server --port 5000
```

### 2. 配置环境变量

在 `.env` 文件中添加以下配置：

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

### 3. 使用 MLflow UI

访问 `http://localhost:5000` 打开 MLflow UI，可以：

- 查看实验运行记录
- 比较不同编译配置的效果
- 管理注册的模型版本
- 查看详细的评估结果

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

## 最佳实践

1. **实验命名**: 使用描述性的实验名称，便于后续查找
2. **模型注册**: 只注册表现良好的模型版本
3. **阶段管理**: 合理使用 Staging 和 Production 阶段
4. **追踪控制**: 在生产环境中可以关闭详细追踪以提升性能

## 故障排除

### MLflow 服务器连接失败

- 检查 `MLFLOW_TRACKING_URI` 配置是否正确
- 确认 MLflow 服务器正在运行
- 检查网络连接和防火墙设置

### 追踪数据丢失

- 确认 `MLFLOW_ENABLED=true`
- 检查 MLflow 服务器存储空间
- 查看应用日志中的 MLflow 相关错误

### 模型注册失败

- 检查模型名称是否符合 MLflow 命名规范
- 确认有足够的存储空间
- 验证 MLflow 服务器权限设置