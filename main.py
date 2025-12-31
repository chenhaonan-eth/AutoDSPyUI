"""
DSPyUI 应用入口

INPUT:  dspyui.ui.app
OUTPUT: main() 函数，启动 Gradio 应用
POS:    应用程序入口点

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

from dspyui.ui.app import demo
from dspyui.ui.styles import CUSTOM_CSS


def main() -> None:
    """启动 DSPyUI Gradio 应用。"""
    demo.launch(css=CUSTOM_CSS)


if __name__ == "__main__":
    main()
