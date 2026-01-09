# Auto-DSPy-Core 测试

本目录包含 auto-dspy-core 包的单元测试和集成测试。

## 测试结构

```
tests/
├── __init__.py
├── README.md
├── conftest.py                 # pytest 配置和共享 fixtures
├── test_config.py              # 配置管理测试 ✅
├── test_dspy_core/             # DSPy 核心功能测试
│   ├── __init__.py             ✅
│   ├── test_signatures.py      ✅
│   ├── test_modules.py         (待创建)
│   ├── test_metrics.py         (待创建)
│   ├── test_compiler.py        (待创建)
│   └── test_runner.py          (待创建)
├── test_mlflow/                # MLflow 集成测试
│   ├── __init__.py             ✅
│   ├── test_tracking.py        ✅
│   ├── test_registry.py        ✅
│   ├── test_loader.py          ✅
│   └── test_service.py         ✅
└── test_serving/               # Serving 功能测试
    ├── __init__.py             ✅
    ├── test_model_manager.py   ✅
    ├── test_feedback.py        ✅
    └── test_data_exporter.py   ✅
```

## 运行测试

### 运行所有测试

```bash
cd auto-dspy-core
uv run pytest tests/ -v
```

### 运行特定模块测试

```bash
# 配置测试
uv run pytest tests/test_config.py -v

# DSPy 核心测试
uv run pytest tests/test_dspy_core/ -v

# MLflow 测试
uv run pytest tests/test_mlflow/ -v

# Serving 测试
uv run pytest tests/test_serving/ -v
```

### 运行带覆盖率的测试

```bash
uv run pytest tests/ --cov=autodspy --cov-report=html
```

### 运行特定测试

```bash
# 运行特定测试类
uv run pytest tests/test_config.py::TestAutoDS PyConfig -v

# 运行特定测试方法
uv run pytest tests/test_config.py::TestAutoDSPyConfig::test_default_values -v
```

## 测试分类

### 单元测试
- 测试单个函数或类的功能
- 使用 mock 隔离外部依赖
- 快速执行

### 集成测试
- 测试多个组件的协作
- 可能需要外部服务（如 MLflow）
- 使用 `@pytest.mark.integration` 标记

### 端到端测试
- 测试完整的工作流程
- 需要完整的环境设置
- 使用 `@pytest.mark.e2e` 标记

## 测试标记

```python
import pytest

# 标记为集成测试
@pytest.mark.integration
def test_mlflow_connection():
    pass

# 标记为需要 MLflow 的测试
@pytest.mark.requires_mlflow
def test_model_registration():
    pass

# 标记为慢速测试
@pytest.mark.slow
def test_large_dataset_compilation():
    pass
```

## 跳过特定测试

```bash
# 跳过集成测试
uv run pytest tests/ -v -m "not integration"

# 只运行单元测试
uv run pytest tests/ -v -m "unit"

# 跳过需要 MLflow 的测试
uv run pytest tests/ -v -m "not requires_mlflow"
```

## 环境变量

测试可能需要以下环境变量：

```bash
# MLflow 配置
export MLFLOW_TRACKING_URI=http://localhost:5000
export MLFLOW_EXPERIMENT_NAME=test-experiments

# LLM API 配置（用于集成测试）
export OPENAI_API_KEY=your-api-key
export OPENAI_API_BASE=https://api.openai.com/v1
```

## 贡献测试

添加新测试时请遵循：

1. 使用描述性的测试名称
2. 添加文档字符串说明测试目的
3. 使用适当的 pytest 标记
4. 确保测试可以独立运行
5. 清理测试产生的临时文件

## 故障排查

### 导入错误

确保已安装包：
```bash
uv pip install -e ".[all]"
```

### MLflow 测试失败

确保 MLflow 服务运行：
```bash
mlflow server --host 0.0.0.0 --port 5000
```

或禁用 MLflow 测试：
```bash
uv run pytest tests/ -v -m "not requires_mlflow"
```
