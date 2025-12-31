"""
核心模块入口

INPUT:  signatures, modules, metrics, compiler, runner 子模块
OUTPUT: create_custom_signature, create_dspy_module, compile_program, generate_program_response 等
POS:    核心层入口，被 ui 模块调用

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

from dspyui.core.signatures import create_custom_signature
from dspyui.core.modules import create_dspy_module
from dspyui.core.metrics import create_metric
from dspyui.core.compiler import compile_program
from dspyui.core.runner import generate_program_response

__all__ = [
    "create_custom_signature",
    "create_dspy_module",
    "create_metric",
    "compile_program",
    "generate_program_response",
]
