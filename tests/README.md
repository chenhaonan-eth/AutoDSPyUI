# Tests 目录

测试文件目录，包含单元测试、属性测试和集成测试。

## 文件清单

| 文件名 | 功能 | MLflow 依赖 |
|--------|------|-------------|
| `__init__.py` | 测试包初始化 | 否 |
| `test_mlflow_tracking.py` | MLflow 追踪模块单元测试 | ✅ 是 |
| `test_mlflow_service.py` | MLflow 服务模块单元测试 | 否（使用 mock） |
| `test_mlflow_connection.py` | MLflow 连接测试 | 否（仅检查连接） |
| `test_mlflow_docker.py` | MLflow Docker 服务测试 | 否（仅检查连接） |
| `test_integration_predict_feedback_export.py` | Predict → Feedback → Export 流程集成测试 | ✅ 是 |
| `test_integration_model_lifecycle.py` | 模型版本切换流程集成测试 | ✅ 是 |

## 运行测试

```bash
# 运行所有测试（MLflow 依赖的测试会自动跳过）
uv run pytest tests/ -v

# 运行特定测试文件
uv run pytest tests/test_mlflow_tracking.py -v

# 运行集成测试
uv run pytest tests/test_integration_*.py -v

# 运行单元测试
uv run pytest tests/test_*.py -k "not integration" -v

# 安装 MLflow 后运行完整测试
uv add mlflow
uv run pytest tests/ -v
```

## 测试分类

### 单元测试
- `test_mlflow_tracking.py`: MLflow 追踪功能单元测试（需要 MLflow）
- `test_mlflow_service.py`: MLflow 服务功能单元测试（使用 mock，无需 MLflow）

### 集成测试
- `test_integration_predict_feedback_export.py`: 完整数据飞轮流程测试（需要 MLflow）
- `test_integration_model_lifecycle.py`: 模型生命周期管理流程测试（需要 MLflow）

### 连接测试
- `test_mlflow_connection.py`: 检查 MLflow 服务连接状态
- `test_mlflow_docker.py`: 检查 Docker 部署的 MLflow 服务

## MLflow 依赖说明

部分测试需要安装 MLflow 才能运行。如果 MLflow 未安装，这些测试会自动跳过并显示：
```
SKIPPED [reason] MLflow 未安装，跳过 XXX 测试
```

要运行完整测试套件，请先安装 MLflow：
```bash
uv add mlflow
```
