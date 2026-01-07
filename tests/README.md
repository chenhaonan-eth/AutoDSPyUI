# Tests 目录

测试文件目录，包含单元测试和属性测试。

## 文件清单

| 文件名 | 功能 |
|--------|------|
| `__init__.py` | 测试包初始化 |
| `test_mlflow_tracking.py` | MLflow 追踪模块单元测试 |

## 运行测试

```bash
# 运行所有测试
uv run pytest tests/ -v

# 运行特定测试文件
uv run pytest tests/test_mlflow_tracking.py -v
```
