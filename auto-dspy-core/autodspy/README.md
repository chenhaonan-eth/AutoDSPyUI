# AutoDSPy 包结构

Auto-DSPy-Core 的核心实现，提供 DSPy 程序编译、MLflow 集成和 API 服务支持。

## 模块结构

```
autodspy/
├── __init__.py          # 包入口，导出所有公共 API
├── config.py            # 配置管理
├── dspy/                # DSPy 核心功能
│   ├── signatures.py    # Signature 创建
│   ├── modules.py       # Module 创建
│   ├── metrics.py       # 评估指标
│   ├── compiler.py      # 程序编译
│   ├── runner.py        # 程序执行
│   └── utils.py         # 工具函数
├── mlflow/              # MLflow 集成
│   ├── tracking.py      # 实验追踪
│   ├── registry.py      # 模型注册
│   ├── loader.py        # 模型加载
│   └── service.py       # 高层服务
└── serving/             # API 服务支持
    ├── model_manager.py # 模型缓存管理
    ├── feedback.py      # 反馈收集
    └── data_exporter.py # 数据导出
```

## 依赖关系

```
autodspy
  ├── config (无依赖)
  ├── dspy
  │   ├── signatures (无依赖)
  │   ├── modules (依赖 signatures)
  │   ├── metrics (依赖 signatures, modules)
  │   ├── compiler (依赖 config, signatures, modules, metrics, mlflow.tracking, utils)
  │   ├── runner (依赖 config, signatures, modules)
  │   └── utils (无依赖)
  ├── mlflow
  │   ├── tracking (依赖 config)
  │   ├── registry (依赖 config)
  │   ├── loader (依赖 config, tracking)
  │   └── service (依赖 registry, tracking)
  └── serving
      ├── model_manager (依赖 config)
      ├── feedback (依赖 config)
      └── data_exporter (依赖 config)
```

## 使用示例

```python
import autodspy

# 配置
config = autodspy.get_config()

# 编译程序
result = autodspy.compile_program(
    input_fields=["topic"],
    output_fields=["joke"],
    dspy_module="Predict",
    llm_model="gpt-4o-mini",
    teacher_model="gpt-4o-mini",
    example_data=df,
    optimizer="BootstrapFewShot",
    instructions="Generate a funny joke",
    metric_type="Exact Match"
)

# MLflow 追踪
autodspy.init_mlflow()
with autodspy.track_compilation("experiment", params) as run:
    # 编译逻辑
    pass

# Serving
manager = autodspy.ModelManager()
program, version = manager.load_model("model-name", stage="Production")
```
