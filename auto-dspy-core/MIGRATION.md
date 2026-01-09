# Auto-DSPy-Core 迁移指南

## 概述

`auto-dspy-core` 是从 DSPyUI 项目中分离出来的独立核心库，提供 DSPy 程序编译、MLflow 集成和 API 服务支持功能。

## 包信息

- **包名**: `auto-dspy-core` (PyPI)
- **导入名**: `autodspy`
- **版本**: 0.1.0
- **Python 要求**: >= 3.11

## 架构设计

### 模块结构

```
autodspy/
├── config.py           # 配置管理
├── dspy_core/          # DSPy 核心功能
│   ├── signatures.py   # Signature 创建
│   ├── modules.py      # Module 定义
│   ├── metrics.py      # 评估指标
│   ├── compiler.py     # 程序编译
│   ├── runner.py       # 程序执行
│   └── utils.py        # 工具函数
├── mlflow/             # MLflow 集成
│   ├── tracking.py     # 实验追踪
│   ├── registry.py     # 模型注册
│   ├── loader.py       # 模型加载
│   └── service.py      # 高级服务
└── serving/            # API 服务支持
    ├── model_manager.py    # 模型管理
    ├── feedback.py         # 反馈收集
    └── data_exporter.py    # 数据导出
```

### 设计原则

本次重构严格遵循 SOLID 原则：

- **单一职责 (SRP)**: 每个模块专注单一功能领域
  - `dspy_core`: DSPy 程序编译和执行
  - `mlflow`: MLflow 集成和追踪
  - `serving`: API 服务支持
  
- **开放/封闭 (OCP)**: 通过配置对象扩展功能，无需修改核心代码
  - `AutoDSPyConfig` 支持灵活配置
  - 插件式的 MLflow 集成
  
- **依赖倒置 (DIP)**: 依赖配置抽象而非具体实现
  - 通过 `get_config()` 获取配置
  - MLflow 功能可选启用

## 安装

### 从本地安装（开发模式）

```bash
# 在 DSPyUI 项目根目录
uv pip install -e auto-dspy-core
```

### 从 PyPI 安装（未来）

```bash
pip install auto-dspy-core
```

## 快速开始

### 基础使用

```python
import autodspy

# 1. 配置管理
from autodspy import AutoDSPyConfig, set_config

config = AutoDSPyConfig(
    mlflow_enabled=True,
    mlflow_tracking_uri="http://localhost:5000",
    cache_enabled=True
)
set_config(config)

# 2. 编译 DSPy 程序
from autodspy import compile_program

result = compile_program(
    input_fields=["question"],
    output_fields=["answer"],
    dspy_module="Predict",
    llm_model="gpt-4o-mini",
    example_data=train_data,
    optimizer="BootstrapFewShot"
)

# 3. 执行程序
from autodspy import generate_program_response

response = generate_program_response(
    program_path="programs/my_program.json",
    inputs={"question": "What is Python?"}
)
```

### MLflow 集成

```python
from autodspy import (
    init_mlflow,
    register_model,
    load_model_from_registry
)

# 初始化 MLflow
init_mlflow()

# 注册模型
result = register_model(
    run_id="abc123",
    model_name="my-qa-model",
    description="Question answering model"
)

# 加载模型
program, version = load_model_from_registry(
    model_name="my-qa-model",
    version="1"
)
```

### API 服务支持

```python
from autodspy import ModelManager, FeedbackService, DataExporter

# 模型管理
manager = ModelManager()
program = manager.load_model("my-model", version="1")

# 反馈收集
feedback_service = FeedbackService()
feedback_service.add_feedback(
    request_id="req123",
    rating=5,
    comment="Great response"
)

# 数据导出
exporter = DataExporter()
exporter.export_to_csv("feedback.csv")
```

## 配置选项

### AutoDSPyConfig 参数

```python
AutoDSPyConfig(
    # MLflow 配置
    mlflow_enabled: bool = True,
    mlflow_tracking_uri: str = "http://localhost:5000",
    mlflow_experiment_name: str = "dspyui-experiments",
    mlflow_log_traces: bool = True,
    mlflow_log_compiles: bool = True,
    mlflow_log_evals: bool = True,
    
    # DSPy 配置
    cache_enabled: bool = True,
    num_threads: int = 1,
    
    # 编译器配置
    mipro_num_candidates: int = 10,
    mipro_init_temperature: float = 1.4,
    bootstrap_max_demos: int = 4,
)
```

### 环境变量支持

也可以通过环境变量配置：

```bash
# MLflow
export MLFLOW_ENABLED=true
export MLFLOW_TRACKING_URI=http://localhost:5000
export MLFLOW_EXPERIMENT_NAME=my-experiment

# DSPy
export DSPY_CACHE_ENABLED=true
export DSPY_NUM_THREADS=4
```

## 从 dspyui.core 迁移

### 导入变更

**旧代码 (dspyui.core)**:
```python
from dspyui.core.compiler import compile_program
from dspyui.core.runner import generate_program_response
from dspyui.core.signatures import create_custom_signature
from dspyui.core.mlflow_tracking import init_mlflow
from dspyui.core.model_manager import ModelManager
```

**新代码 (autodspy)**:
```python
from autodspy import (
    compile_program,
    generate_program_response,
    create_custom_signature,
    init_mlflow,
    ModelManager,
)
```

### 配置变更

**旧代码**:
```python
from dspyui.config import MLFLOW_ENABLED, MLFLOW_TRACKING_URI
```

**新代码**:
```python
from autodspy import get_config

config = get_config()
mlflow_enabled = config.mlflow_enabled
tracking_uri = config.mlflow_tracking_uri
```

## API 参考

### 核心功能

- `compile_program()` - 编译 DSPy 程序
- `generate_program_response()` - 执行程序生成响应
- `create_custom_signature()` - 创建自定义 Signature
- `create_dspy_module()` - 创建 DSPy Module
- `create_metric()` - 创建评估指标

### MLflow 集成

- `init_mlflow()` - 初始化 MLflow
- `track_compilation()` - 追踪编译过程
- `register_model()` - 注册模型到 Registry
- `load_model_from_registry()` - 从 Registry 加载模型
- `list_registered_models()` - 列出已注册模型

### Serving 支持

- `ModelManager` - 模型管理和缓存
- `FeedbackService` - 反馈收集和管理
- `DataExporter` - 数据导出功能

## 依赖关系

### 核心依赖

```toml
dependencies = [
    "dspy-ai>=3.0.4",
    "pandas>=2.0.0",
    "scikit-learn>=1.3.0",
    "numpy>=1.24.0",
    "pyyaml>=6.0",
    "openai>=1.0.0",
]
```

### 可选依赖

```toml
[project.optional-dependencies]
mlflow = ["mlflow>=2.12.2"]
all = ["auto-dspy-core[mlflow]"]
```

## 开发指南

### 本地开发

```bash
# 克隆项目
cd auto-dspy-core

# 安装开发依赖
uv pip install -e ".[all]"
uv pip install pytest pytest-cov

# 运行测试
pytest tests/
```

### 构建和发布

```bash
# 构建包
uv build

# 发布到 PyPI (需要配置凭证)
uv publish
```

## 故障排查

### 导入错误

**问题**: `ModuleNotFoundError: No module named 'autodspy'`

**解决**: 确保已安装包
```bash
uv pip install -e auto-dspy-core
```

### MLflow 连接错误

**问题**: MLflow 服务器不可用

**解决**: 
1. 检查 MLflow 服务是否运行
2. 验证 `mlflow_tracking_uri` 配置
3. 或禁用 MLflow: `config.mlflow_enabled = False`

### 配置问题

**问题**: 配置未生效

**解决**: 确保在使用功能前设置配置
```python
from autodspy import AutoDSPyConfig, set_config

config = AutoDSPyConfig(...)
set_config(config)  # 必须调用
```

## 更新日志

### v0.1.0 (2026-01-09)

- 🎉 首次发布
- ✨ 从 DSPyUI 分离核心功能
- ✨ 支持配置文件和环境变量
- ✨ 完整的 MLflow 集成
- ✨ API 服务支持功能
- 📝 完整的文档和示例

## 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 许可证

MIT License - 详见 LICENSE 文件

## 支持

- 📧 Email: support@autodspy.dev
- 🐛 Issues: https://github.com/your-org/auto-dspy-core/issues
- 📖 文档: https://autodspy.readthedocs.io
