<!-- 一旦我所属的文件夹有所变化，请更新我 -->

# core

DSPy 程序编译的核心业务逻辑。
包含 Signature 创建、Module 定义、指标计算、编译器和程序运行器。

## 文件清单

| 文件 | 地位 | 功能 |
|-----|------|------|
| `__init__.py` | 入口 | 导出核心 API |
| `signatures.py` | 核心 | 创建自定义 DSPy Signature |
| `modules.py` | 核心 | 创建 DSPy Module (Predict/CoT) |
| `metrics.py` | 核心 | 评估指标 (精确匹配/余弦/LLM Judge) |
| `compiler.py` | 核心 | 程序编译主逻辑，集成 MLflow 追踪 |
| `runner.py` | 核心 | 程序执行逻辑，支持本地和 MLflow 模型推理 |
| `mlflow_tracking.py` | MLflow | 实验追踪 (Run 记录、指标、工件) |
| `mlflow_registry.py` | MLflow | 模型注册管理 (register_model, transition_stage) |
| `mlflow_loader.py` | MLflow | 模型加载 (从 Registry/Run 加载模型) |
| `mlflow_service.py` | MLflow | 业务逻辑层，高层接口 |

## 最近更新 (2026-01-07)

- `runner.py`: 集成 MLflow 批量推理追踪功能
  - 在 `run_batch_inference()` 中记录批量统计 (total_rows, success_count, error_count, total_latency, avg_latency_per_row, success_rate)
  - 新增 `_log_batch_inference_stats()` 内部函数，处理 MLflow 统计记录
  - 添加 `time` 模块用于计算推理耗时
  - 添加 `logging` 模块用于日志记录

- `compiler.py`: 集成 MLflow 追踪功能
  - 在 `compile_program()` 中使用 `track_compilation()` 上下文管理器
  - 调用 `log_compilation_metrics()` 记录 baseline_score, evaluation_score, score_improvement
  - 调用 `log_compilation_artifacts()` 记录程序 JSON 和数据集 CSV
  - 调用 `log_evaluation_table()` 记录 per-example 评估结果
  - 调用 `log_dataset_metadata()` 记录数据集元数据
  - 编译完成后在使用说明中添加 MLflow UI 链接

- `mlflow_tracking.py`: 增强模型注册功能
  - `register_model()`: 增强支持元数据记录 (input_fields, output_fields, instructions, evaluation_score, signature, dspy_module, optimizer)
  - `transition_model_stage()`: 增强支持 archive_existing 参数和阶段验证
  - `get_mlflow_ui_url()`: 增强支持 experiment_id, model_name, model_version 参数
  - `_get_experiment_id_for_run()`: 新增辅助函数，获取 Run 所属的 Experiment ID

- `mlflow_tracking.py`: 新增 MLflow 追踪模块
  - `init_mlflow()`: 初始化 MLflow 和 DSPy autolog
  - `truncate_param()`: 参数截断辅助函数
  - `track_compilation()`: 编译追踪上下文管理器
  - `log_compilation_metrics()`: 记录编译评估指标
  - `log_compilation_artifacts()`: 记录编译工件
  - `log_evaluation_table()`: 记录详细评估结果（支持 per-example 结果、聚合指标、metric 配置）
  - `compute_dataset_hash()`: 计算数据集 SHA-256 哈希（确定性）
  - `log_dataset_metadata()`: 记录数据集元数据 (row_count, column_names, file_hash)
  - `_serialize_value()`: 值序列化辅助函数（内部使用）

## 历史更新 (2026-01-02)

- `runner.py`: 新增 `load_program_metadata()` 函数，支持加载程序元数据
- `runner.py`: 新增 `run_batch_inference()` 函数，支持批量推理
- `runner.py`: 新增 `validate_csv_headers()` 函数，验证 CSV 头部
