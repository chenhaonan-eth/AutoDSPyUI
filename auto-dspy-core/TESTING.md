# Auto-DSPy-Core 测试指南

本文档说明如何运行和维护 auto-dspy-core 包的测试套件。

## 测试结构

```
tests/
├── __init__.py                 # 测试包初始化
├── README.md                   # 测试总览
├── conftest.py                 # pytest 配置和共享 fixtures
├── run_tests.sh                # 测试运行脚本
├── test_config.py              # 配置管理测试 ✅
├── test_dspy_core/             # DSPy 核心功能测试
│   ├── __init__.py
│   ├── README.md
│   └── test_signatures.py      # Signature 创建测试 ✅
├── test_mlflow/                # MLflow 集成测试
│   ├── __init__.py
│   ├── README.md
│   ├── test_tracking.py        # 追踪功能测试 ✅
│   ├── test_registry.py        # 注册表测试 ✅
│   ├── test_loader.py          # 加载器测试 ✅
│   └── test_service.py         # 服务层测试 ✅
└── test_serving/               # Serving 功能测试
    ├── __init__.py
    ├── README.md
    ├── test_model_manager.py   # 模型管理器测试 ✅
    ├── test_feedback.py        # 反馈服务测试 ✅
    └── test_data_exporter.py   # 数据导出测试 ✅
```

## 快速开始

### 安装依赖

```bash
cd auto-dspy-core
uv sync
```

### 运行所有测试

```bash
uv run pytest tests/ -v
```

### 使用测试脚本

```bash
# 运行所有测试
./tests/run_tests.sh

# 运行特定路径的测试
./tests/run_tests.sh tests/test_config.py

# 运行带标记的测试
./tests/run_tests.sh tests/ "unit"

# 跳过集成测试
./tests/run_tests.sh tests/ "not integration"
```

## 测试分类

### 单元测试 (unit)

测试单个函数或类的功能，使用 mock 隔离外部依赖。

```bash
uv run pytest tests/ -v -m "unit"
```

### 集成测试 (integration)

测试多个组件的协作，可能需要外部服务。

```bash
uv run pytest tests/ -v -m "integration"
```

### 需要 MLflow 的测试 (requires_mlflow)

需要 MLflow 服务运行的测试。

```bash
# 跳过需要 MLflow 的测试
uv run pytest tests/ -v -m "not requires_mlflow"
```

## 测试覆盖

### 已完成 ✅

1. **配置管理** (`test_config.py`)
   - 默认配置值
   - 环境变量加载
   - YAML 配置文件
   - 配置重置

2. **MLflow 追踪** (`test_mlflow/test_tracking.py`)
   - 参数截断
   - 数据集哈希
   - UI URL 构造
   - 初始化流程
   - 编译追踪
   - 指标记录
   - 模型注册

3. **MLflow 注册表** (`test_mlflow/test_registry.py`)
   - 模型列表
   - 版本查询
   - 元数据获取

4. **MLflow 加载器** (`test_mlflow/test_loader.py`)
   - 从注册表加载
   - 从运行加载
   - 提示词工件
   - 运行 ID 查询

5. **MLflow 服务** (`test_mlflow/test_service.py`)
   - 模型名称验证
   - 编译模型注册
   - 错误处理

6. **模型管理器** (`test_serving/test_model_manager.py`)
   - 模型加载
   - 缓存管理
   - 缓存失效
   - 缓存统计

7. **反馈服务** (`test_serving/test_feedback.py`)
   - 反馈提交
   - 反馈查询
   - 评分验证

8. **数据导出** (`test_serving/test_data_exporter.py`)
   - 追踪导出
   - 数据扁平化
   - 格式转换

9. **Signature 创建** (`test_dspy_core/test_signatures.py`)
   - 简单 Signature
   - 多字段 Signature
   - 字段描述

### 待实现 ⏳

1. **DSPy Modules** (`test_dspy_core/test_modules.py`)
   - Predict 模块
   - ChainOfThought 模块
   - 自定义模块

2. **评估指标** (`test_dspy_core/test_metrics.py`)
   - 精确匹配
   - 余弦相似度
   - LLM Judge

3. **编译器** (`test_dspy_core/test_compiler.py`)
   - BootstrapFewShot
   - MIPRO
   - 其他优化器

4. **程序执行** (`test_dspy_core/test_runner.py`)
   - 单条推理
   - 批量推理
   - 错误处理

## 测试最佳实践

### 1. 使用 Fixtures

共享的测试设置应放在 `conftest.py` 中:

```python
@pytest.fixture
def mock_config():
    """模拟配置对象"""
    from autodspy import AutoDSPyConfig
    return AutoDSPyConfig(mlflow_enabled=False)
```

### 2. 标记测试

使用 pytest 标记分类测试:

```python
@pytest.mark.unit
def test_simple_function():
    pass

@pytest.mark.integration
@pytest.mark.requires_mlflow
def test_mlflow_integration():
    pass
```

### 3. Mock 外部依赖

使用 `unittest.mock` 隔离外部依赖:

```python
from unittest.mock import patch, MagicMock

def test_with_mock():
    with patch('autodspy.mlflow.tracking.mlflow') as mock_mlflow:
        mock_mlflow.log_metric.return_value = None
        # 测试逻辑
```

### 4. 测试命名

测试函数名应清晰描述测试内容:

```python
def test_create_signature_with_multiple_inputs():
    """创建多输入 Signature 应成功"""
    pass
```

### 5. 文档字符串

每个测试应包含文档字符串说明测试目的:

```python
def test_cache_invalidation():
    """
    测试缓存失效功能
    
    验证:
    1. 失效特定模型缓存
    2. 后续加载重新加载模型
    """
    pass
```

## 持续集成

### GitHub Actions 配置示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install uv
        run: pip install uv
      - name: Install dependencies
        run: uv sync
      - name: Run tests
        run: uv run pytest tests/ -v --cov=autodspy
```

## 故障排查

### 导入错误

确保已安装包:

```bash
uv pip install -e ".[all]"
```

### MLflow 测试失败

跳过需要 MLflow 的测试:

```bash
uv run pytest tests/ -v -m "not requires_mlflow"
```

或启动 MLflow 服务:

```bash
mlflow server --host 0.0.0.0 --port 5000
```

### 网络超时

某些测试可能需要网络连接,可以设置更长的超时:

```bash
uv run pytest tests/ -v --timeout=60
```

## 贡献测试

添加新测试时请:

1. 遵循现有的测试结构和命名约定
2. 添加适当的 pytest 标记
3. 包含清晰的文档字符串
4. 更新相关的 README.md
5. 确保测试可以独立运行
6. 清理测试产生的临时文件

## 测试覆盖率

生成覆盖率报告:

```bash
uv run pytest tests/ --cov=autodspy --cov-report=html
```

查看报告:

```bash
open htmlcov/index.html
```

## 参考资源

- [pytest 文档](https://docs.pytest.org/)
- [unittest.mock 文档](https://docs.python.org/3/library/unittest.mock.html)
- [MLflow 测试指南](https://mlflow.org/docs/latest/python_api/index.html)
