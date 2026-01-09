# Auto-DSPy-Core

DSPy 程序自动化编译和 MLflow 集成核心库

## 功能特性

- **DSPy 核心功能**: Signature 创建、Module 定义、评估指标、程序编译和执行
- **MLflow 集成**: 实验追踪、模型注册、版本管理
- **Serving 支持**: 模型缓存管理、用户反馈收集、数据导出

## 安装

```bash
# 基础安装
pip install auto-dspy-core

# 包含 MLflow 支持
pip install auto-dspy-core[mlflow]

# 完整安装
pip install auto-dspy-core[all]
```

## 快速开始

```python
import autodspy

# 配置
config = autodspy.get_config()

# 编译 DSPy 程序
result = autodspy.compile_program(
    input_fields=["topic"],
    output_fields=["joke"],
    dspy_module="Predict",
    llm_model="gpt-4o-mini",
    teacher_model="gpt-4o-mini",
    example_data=df,
    optimizer="BootstrapFewShot",
    instructions="Generate a funny joke about the topic",
    metric_type="Exact Match"
)

# 使用 MLflow
autodspy.init_mlflow()
with autodspy.track_compilation("my-experiment", params) as run:
    # 编译逻辑
    pass
```

## 配置

支持三种配置方式（优先级从高到低）：

1. 环境变量
2. 配置文件（YAML）
3. 默认值

```python
# 从配置文件加载
config = autodspy.load_config("autodspy-config.yaml")

# 或使用环境变量
# DSPY_CACHE_ENABLED=true
# MLFLOW_ENABLED=true
# MLFLOW_TRACKING_URI=http://localhost:5000
```

## 测试

运行测试套件:

```bash
# 安装开发依赖
uv sync

# 运行所有测试
uv run pytest tests/ -v

# 运行单元测试
uv run pytest tests/ -v -m "unit"

# 跳过需要 MLflow 的测试
uv run pytest tests/ -v -m "not requires_mlflow"

# 生成覆盖率报告
uv run pytest tests/ --cov=autodspy --cov-report=html
```

详细测试指南请参阅 [TESTING.md](TESTING.md)。

## 迁移指南

从 dspyui.core 迁移请参阅 [MIGRATION.md](MIGRATION.md)。

## 许可证

MIT License
