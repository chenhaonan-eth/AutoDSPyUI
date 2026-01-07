"""
DSPyUI 应用入口

INPUT:  dspyui.ui.app, dspyui.core.mlflow_tracking
OUTPUT: main() 函数，启动 Gradio 应用
POS:    应用程序入口点，负责初始化 MLflow 并启动 Web 界面

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import logging
from dspyui.ui.app import demo
from dspyui.ui.styles import CUSTOM_CSS
from dspyui.core.mlflow_tracking import init_mlflow

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """启动 DSPyUI Gradio 应用。"""
    # 初始化 MLflow
    mlflow_enabled = init_mlflow()
    if mlflow_enabled:
        logger.info("✅ MLflow 追踪已启用")
    else:
        logger.info("ℹ️  MLflow 追踪已禁用")
    
    # 启动 Gradio 应用
    demo.launch(css=CUSTOM_CSS)


if __name__ == "__main__":
    main()
