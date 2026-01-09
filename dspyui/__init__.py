"""
DSPyUI 主包

INPUT:  autodspy (核心功能), config, utils, ui 子模块
OUTPUT: 公共 API (compile_program, list_prompts, generate_program_response 等)
POS:    包入口，统一导出公共接口

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

from dspyui.config import (
    LLM_OPTIONS,
    SUPPORTED_GROQ_MODELS,
    SUPPORTED_GOOGLE_MODELS,
    DEFAULT_LM_MODEL,
)
# 从 autodspy 导入核心功能
from autodspy import compile_program, generate_program_response
from dspyui.utils.file_ops import list_prompts, load_example_csv, export_to_csv

__all__ = [
    # 配置
    "LLM_OPTIONS",
    "SUPPORTED_GROQ_MODELS", 
    "SUPPORTED_GOOGLE_MODELS",
    "DEFAULT_LM_MODEL",
    # 核心功能
    "compile_program",
    "generate_program_response",
    # 工具函数
    "list_prompts",
    "load_example_csv",
    "export_to_csv",
]
