"""
Auto-DSPy-Core: DSPy 程序自动化编译和 MLflow 集成

提供 DSPy 程序编译、执行、MLflow 追踪和 API 服务支持的完整解决方案

INPUT:  无
OUTPUT: 所有公共 API
POS:    包入口
"""

__version__ = "0.1.0"

# 配置
from autodspy.config import (
    AutoDSPyConfig,
    get_config,
    set_config,
    load_config,
    reset_config,
)

# DSPy 核心功能
from autodspy.dspy_core import (
    create_custom_signature,
    create_dspy_module,
    create_metric,
    compile_program,
    generate_program_response,
    load_program_metadata,
    run_batch_inference,
    validate_csv_headers,
    generate_human_readable_id,
)

# MLflow 集成
from autodspy.mlflow import (
    init_mlflow,
    is_mlflow_available,
    track_compilation,
    log_compilation_metrics,
    log_compilation_artifacts,
    log_dspy_model,
    log_evaluation_table,
    register_model,
    transition_model_stage,
    load_model_from_registry,
    load_model_from_run,
    list_registered_models,
    list_model_versions,
    get_model_metadata,
    get_mlflow_ui_url,
    ModelRegistrationResult,
    register_compiled_model,
    load_prompt_artifact,
    get_registered_run_ids,
)

# Serving 支持
from autodspy.serving import (
    ModelManager,
    FeedbackService,
    FeedbackRecord,
    DataExporter,
)

__all__ = [
    # 版本
    "__version__",
    # 配置
    "AutoDSPyConfig",
    "get_config",
    "set_config",
    "load_config",
    "reset_config",
    # DSPy
    "create_custom_signature",
    "create_dspy_module",
    "create_metric",
    "compile_program",
    "generate_program_response",
    "load_program_metadata",
    "run_batch_inference",
    "validate_csv_headers",
    "generate_human_readable_id",
    # MLflow
    "init_mlflow",
    "is_mlflow_available",
    "track_compilation",
    "log_compilation_metrics",
    "log_compilation_artifacts",
    "log_dspy_model",
    "log_evaluation_table",
    "register_model",
    "transition_model_stage",
    "load_model_from_registry",
    "load_model_from_run",
    "list_registered_models",
    "list_model_versions",
    "get_model_metadata",
    "get_mlflow_ui_url",
    "ModelRegistrationResult",
    "register_compiled_model",
    "load_prompt_artifact",
    "get_registered_run_ids",
    # Serving
    "ModelManager",
    "FeedbackService",
    "FeedbackRecord",
    "DataExporter",
]
