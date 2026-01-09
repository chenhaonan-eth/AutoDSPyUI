"""
MLflow 集成模块

INPUT:  无
OUTPUT: MLflow 相关的所有公共函数和类
POS:    MLflow 功能模块入口
"""

from autodspy.mlflow.tracking import (
    init_mlflow,
    is_mlflow_available,
    track_compilation,
    log_compilation_metrics,
    log_compilation_artifacts,
    log_dspy_model,
    log_evaluation_table,
    compute_dataset_hash,
    log_dataset_metadata,
    get_mlflow_ui_url,
    truncate_param,
    set_model_alias,
    delete_model_alias,
    get_model_version_by_alias,
)
from autodspy.mlflow.registry import (
    register_model,
    transition_model_stage,  # deprecated
    set_model_alias as registry_set_model_alias,
    delete_model_alias as registry_delete_model_alias,
)
from autodspy.mlflow.loader import (
    load_model_from_registry,
    load_model_by_alias,
    load_model_from_run,
    list_registered_models,
    list_model_versions,
    get_model_metadata,
    load_prompt_artifact,
    get_registered_run_ids,
)
from autodspy.mlflow.service import (
    ModelRegistrationResult,
    register_compiled_model,
    validate_model_name,
)

__all__ = [
    # Tracking
    "init_mlflow",
    "is_mlflow_available",
    "track_compilation",
    "log_compilation_metrics",
    "log_compilation_artifacts",
    "log_dspy_model",
    "log_evaluation_table",
    "compute_dataset_hash",
    "log_dataset_metadata",
    "get_mlflow_ui_url",
    "truncate_param",
    # Model Alias (推荐)
    "set_model_alias",
    "delete_model_alias",
    "get_model_version_by_alias",
    # Registry
    "register_model",
    "transition_model_stage",  # deprecated, use set_model_alias
    # Loader
    "load_model_from_registry",
    "load_model_by_alias",
    "load_model_from_run",
    "list_registered_models",
    "list_model_versions",
    "get_model_metadata",
    "load_prompt_artifact",
    "get_registered_run_ids",
    # Service
    "ModelRegistrationResult",
    "register_compiled_model",
    "validate_model_name",
]
