<!-- 一旦我所属的文件夹有所变化，请更新我 -->

# core

DSPy 程序编译的核心业务逻辑。
包含 Signature 创建、Module 定义、指标计算、编译器、程序运行器和 API 服务核心组件。

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
| `model_manager.py` | API 服务 | 模型加载和缓存管理，支持版本/阶段/别名加载 |
| `feedback.py` | API 服务 | 用户反馈收集，使用 MLflow log_feedback API |
| `data_exporter.py` | API 服务 | 高质量数据导出，支持 CSV/JSON 格式 |

## API 服务核心组件

### ModelManager (`model_manager.py`)

模型加载和缓存管理器，为 API 服务提供高效的模型访问。

**主要功能：**
- `load_model(name, version, stage, alias)`: 支持三种加载方式
  - 版本号: `models:/name/3`
  - 阶段: `models:/name@Production`
  - 别名: `models:/name@champion`
- `invalidate_cache(name)`: 使指定模型的缓存失效
- `invalidate_all()`: 清空所有缓存
- `get_cache_stats()`: 获取缓存统计信息

**特性：**
- 线程安全的缓存实现
- 支持 TTL 过期
- 自动缓存命中/未命中统计

### FeedbackService (`feedback.py`)

用户反馈收集服务，使用 MLflow log_feedback API 记录反馈。

**主要功能：**
- `record_feedback(trace_id, rating, corrected_output, comment, user_id)`: 记录用户反馈
- `validate_trace_exists(trace_id)`: 验证 trace_id 是否存在

**支持的反馈类型：**
- `user_rating`: thumbs_up / thumbs_down
- `corrected_output`: 用户修正的输出
- `comment`: 文字评论

### DataExporter (`data_exporter.py`)

高质量数据导出服务，用于数据飞轮闭环。

**主要功能：**
- `query_traces_with_feedback(model_name, rating, start_date, end_date, limit)`: 查询带反馈的 traces
- `export_training_data(traces_df, format)`: 导出为 CSV/JSON 格式
- `export_streaming(model_name, rating, format, ...)`: 流式导出，适用于大数据量

**导出逻辑：**
- 优先使用 `corrected_output`（用户修正）
- 否则使用原始 `output`
- 支持日期范围过滤

## 最近更新 (2026-01-08)

- 文档更新：添加 API 服务核心组件详细说明
  - `ModelManager`: 模型加载和缓存管理器
  - `FeedbackService`: 用户反馈收集服务
  - `DataExporter`: 高质量数据导出服务

## 历史更新 (2026-01-07)

- `model_manager.py`: 新增模型加载和缓存管理器
  - `ModelManager` 类：支持模型加载、缓存和版本管理
  - `load_model()`: 支持版本号、阶段、别名三种加载方式
  - `invalidate_cache()`: 使指定模型的缓存失效
  - `get_cache_stats()`: 获取缓存统计信息
  - 线程安全的缓存实现，支持 TTL 过期

- `feedback.py`: 新增用户反馈收集服务
  - `FeedbackService` 类：使用 MLflow log_feedback API 记录反馈
  - `record_feedback()`: 记录评分、修正输出、评论
  - `validate_trace_exists()`: 验证 trace_id 是否存在
  - `FeedbackRecord` 数据类：反馈记录结构

- `data_exporter.py`: 新增高质量数据导出服务
  - `DataExporter` 类：查询和导出带反馈的 traces
  - `query_traces_with_feedback()`: 按反馈评分、日期范围过滤
  - `export_training_data()`: 支持 CSV/JSON 格式导出
  - `export_streaming()`: 流式导出，适用于大数据量

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
