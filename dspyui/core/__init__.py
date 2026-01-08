"""
核心模块入口

INPUT:  signatures, modules, metrics, compiler, runner, mlflow_*, model_manager, feedback, data_exporter 子模块
OUTPUT: create_custom_signature, create_dspy_module, compile_program, generate_program_response,
        generate_response_from_mlflow, run_batch_inference_from_mlflow, ModelManager, FeedbackService, DataExporter 等
POS:    核心层入口，被 ui 和 api 模块调用

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

from dspyui.core.signatures import create_custom_signature
from dspyui.core.modules import create_dspy_module
from dspyui.core.metrics import create_metric
from dspyui.core.compiler import compile_program
from dspyui.core.runner import (
    generate_program_response,
    generate_response_from_mlflow,
    run_batch_inference_from_mlflow,
)
from dspyui.core.model_manager import ModelManager
from dspyui.core.feedback import FeedbackService, FeedbackRecord
from dspyui.core.data_exporter import DataExporter

__all__ = [
    "create_custom_signature",
    "create_dspy_module",
    "create_metric",
    "compile_program",
    "generate_program_response",
    "generate_response_from_mlflow",
    "run_batch_inference_from_mlflow",
    # Serving & Feedback
    "ModelManager",
    "FeedbackService",
    "FeedbackRecord",
    "DataExporter",
]

