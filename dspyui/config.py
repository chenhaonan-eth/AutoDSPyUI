"""
DSPyUI 配置常量

INPUT:  环境变量 (OPENAI_API_KEY, GROQ_API_KEY, GOOGLE_API_KEY, DSPY_CACHE_ENABLED 等)
OUTPUT: LLM_OPTIONS, SUPPORTED_GROQ_MODELS, SUPPORTED_GOOGLE_MODELS, 默认 LM 配置
POS:    全局配置模块，被 core 和 ui 模块依赖

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import os
from typing import List

import dspy

# 支持的 Groq 模型列表
SUPPORTED_GROQ_MODELS: List[str] = [
    "mixtral-8x7b-32768",
    "gemma-7b-it",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "gemma2-9b-it"
]

# 支持的 Google 模型列表
SUPPORTED_GOOGLE_MODELS: List[str] = [
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]

# UI 中显示的 LLM 模型选项
LLM_OPTIONS: List[str] = [
    "gpt-3.5-turbo", "gpt-4", "gpt-4o", "gpt-4o-mini",
    "claude-3-5-sonnet-20240620", "claude-3-opus-20240229",
    *SUPPORTED_GROQ_MODELS,
    *SUPPORTED_GOOGLE_MODELS
]

# 默认 LM 配置
# 注意: 使用 MIPRO 或 BootstrapFewShotWithRandomSearch 时需要全局配置 LM
DEFAULT_LM_MODEL = "openai/gpt-4o-mini"

# DSPy 缓存配置
# 从环境变量读取，默认启用缓存
DSPY_CACHE_ENABLED: bool = os.environ.get("DSPY_CACHE_ENABLED", "true").lower() == "true"


def configure_default_lm() -> dspy.LM:
    """
    配置并返回默认的 DSPy LM 实例。
    
    Returns:
        dspy.LM: 配置好的默认语言模型
    """
    lm = dspy.LM(DEFAULT_LM_MODEL, cache=DSPY_CACHE_ENABLED)
    dspy.configure(lm=lm)
    return lm


# 国际化配置
DEFAULT_LANGUAGE: str = os.environ.get("DSPYUI_LANGUAGE", "zh_CN")  # 默认中文，可通过环境变量切换

# 初始化默认 LM
default_lm = configure_default_lm()
