"""
DSPyUI 配置常量

INPUT:  环境变量 (OPENAI_API_KEY, GROQ_API_KEY, GOOGLE_API_KEY, DSPY_CACHE_ENABLED, DSPY_NUM_THREADS, MLflow 相关环境变量等)
OUTPUT: LLM_OPTIONS, SUPPORTED_GROQ_MODELS, SUPPORTED_GOOGLE_MODELS, 默认 LM 配置, 训练参数配置, MLflow 配置常量
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

# 支持的 DeepSeek 模型列表
SUPPORTED_DEEPSEEK_MODELS: List[str] = [
    "deepseek-chat"
]

# UI 中显示的 LLM 模型选项
LLM_OPTIONS: List[str] = [
    "gpt-3.5-turbo", "gpt-4", "gpt-4o", "gpt-4o-mini",
    "claude-3-5-sonnet-20240620", "claude-3-opus-20240229",
    *SUPPORTED_GROQ_MODELS,
    *SUPPORTED_GOOGLE_MODELS,
    *SUPPORTED_DEEPSEEK_MODELS
]

# 默认 LM 配置
# 注意: 使用 MIPRO 或 BootstrapFewShotWithRandomSearch 时需要全局配置 LM
DEFAULT_LM_MODEL = "openai/gpt-4o-mini"

# DSPy 缓存配置
# 从环境变量读取，默认启用缓存
DSPY_CACHE_ENABLED: bool = os.environ.get("DSPY_CACHE_ENABLED", "true").lower() == "true"

# ============================================================
# 训练/编译参数配置
# ============================================================

# 并发线程数: 控制评估和优化时的并行度
# 增大可加速训练，但需注意 LLM API 的并发限制
DSPY_NUM_THREADS: int = int(os.environ.get("DSPY_NUM_THREADS", "1"))

# ============================================================
# MIPROv2 优化器参数
# ============================================================

# 候选提示词数量: 每轮生成多少个候选提示词进行评估
# 越大搜索空间越广，但耗时越长
MIPRO_NUM_CANDIDATES: int = int(os.environ.get("MIPRO_NUM_CANDIDATES", "10"))

# 初始温度: 控制提示词生成的随机性
# 较高温度产生更多样的候选，较低温度更保守
MIPRO_INIT_TEMPERATURE: float = float(os.environ.get("MIPRO_INIT_TEMPERATURE", "1.0"))

# 批次数量: 优化迭代的总批次数
# 越多迭代越充分，但耗时越长
MIPRO_NUM_BATCHES: int = int(os.environ.get("MIPRO_NUM_BATCHES", "30"))

# 最大自举示例数: 从训练集自动生成的 few-shot 示例数量上限
MIPRO_MAX_BOOTSTRAPPED_DEMOS: int = int(os.environ.get("MIPRO_MAX_BOOTSTRAPPED_DEMOS", "8"))

# 最大标注示例数: 使用的人工标注示例数量上限
MIPRO_MAX_LABELED_DEMOS: int = int(os.environ.get("MIPRO_MAX_LABELED_DEMOS", "16"))

# ============================================================
# BootstrapFewShot 优化器参数
# ============================================================

# 最大自举示例数: 自动生成的 few-shot 示例数量上限
# 默认 4 个，太多会增加 token 消耗且可能引入噪声
BOOTSTRAP_MAX_BOOTSTRAPPED_DEMOS: int = int(os.environ.get("BOOTSTRAP_MAX_BOOTSTRAPPED_DEMOS", "4"))

# 最大标注示例数: 使用的人工标注示例数量上限
BOOTSTRAP_MAX_LABELED_DEMOS: int = int(os.environ.get("BOOTSTRAP_MAX_LABELED_DEMOS", "4"))


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

# ============================================================
# MLflow 集成配置
# ============================================================

# MLflow 启用开关: 控制是否启用 MLflow 追踪功能
MLFLOW_ENABLED: bool = os.environ.get("MLFLOW_ENABLED", "true").lower() == "true"

# MLflow 追踪服务器 URI: 指定 MLflow 追踪服务器地址
# 默认使用本地服务器，需要先启动 MLflow 服务器 (bash webui.sh --mlflow)
MLFLOW_TRACKING_URI: str = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")

# MLflow 实验名称: 用于组织和分组相关的运行记录
MLFLOW_EXPERIMENT_NAME: str = os.environ.get("MLFLOW_EXPERIMENT_NAME", "dspyui-experiments")

# MLflow UI 基础 URL: 当无法从 tracking URI 推断时使用
# 留空时会尝试从 MLFLOW_TRACKING_URI 推断，或回退到 http://localhost:5000
MLFLOW_UI_BASE_URL: str = os.environ.get("MLFLOW_UI_BASE_URL", "")

# ============================================================
# MLflow Autolog 参数配置
# ============================================================

# 启用 LLM 调用追踪: 记录所有 LLM 请求和响应的详细信息
MLFLOW_LOG_TRACES: bool = os.environ.get("MLFLOW_LOG_TRACES", "true").lower() == "true"

# 编译时追踪: 在 DSPy 程序编译过程中记录 LLM 调用
MLFLOW_LOG_TRACES_FROM_COMPILE: bool = os.environ.get("MLFLOW_LOG_TRACES_FROM_COMPILE", "false").lower() == "true"

# 评估时追踪: 在程序评估过程中记录 LLM 调用
MLFLOW_LOG_TRACES_FROM_EVAL: bool = os.environ.get("MLFLOW_LOG_TRACES_FROM_EVAL", "true").lower() == "true"

# 编译过程记录: 自动记录编译过程的参数和配置
MLFLOW_LOG_COMPILES: bool = os.environ.get("MLFLOW_LOG_COMPILES", "true").lower() == "true"

# 评估过程记录: 自动记录评估过程的指标和结果
MLFLOW_LOG_EVALS: bool = os.environ.get("MLFLOW_LOG_EVALS", "true").lower() == "true"

# 初始化默认 LM
default_lm = configure_default_lm()
