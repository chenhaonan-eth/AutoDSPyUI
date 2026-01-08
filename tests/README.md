# Tests 目录

测试文件目录，包含单元测试、属性测试和集成测试。

## 文件清单

| 文件名 | 功能 |
|--------|------|
| `__init__.py` | 测试包初始化 |
| `test_mlflow_tracking.py` | MLflow 追踪模块单元测试 |
| `test_mlflow_service.py` | MLflow 服务模块单元测试 |
| `test_integration_predict_feedback_export.py` | Predict → Feedback → Export 流程集成测试 |
| `test_integration_model_lifecycle.py` | 模型版本切换流程集成测试 |

## 运行测试

```bash
# 运行所有测试
uv run pytest tests/ -v

# 运行特定测试文件
uv run pytest tests/test_mlflow_tracking.py -v

# 运行集成测试
uv run pytest tests/test_integration_*.py -v

# 运行单元测试
uv run pytest tests/test_*.py -k "not integration" -v
```

## 测试分类

### 单元测试
- `test_mlflow_tracking.py`: MLflow 追踪功能单元测试
- `test_mlflow_service.py`: MLflow 服务功能单元测试

### 集成测试
- `test_integration_predict_feedback_export.py`: 完整数据飞轮流程测试
- `test_integration_model_lifecycle.py`: 模型生命周期管理流程测试
