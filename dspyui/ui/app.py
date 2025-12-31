"""
Gradio 主应用

INPUT:  dspyui.ui.styles, dspyui.ui.tabs, dspyui.ui.language_switcher
OUTPUT: create_app() 函数, demo 实例
POS:    UI 入口，组装所有 Tab 并创建 Gradio Blocks 应用

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import gradio as gr

from dspyui.ui.styles import CUSTOM_CSS
from dspyui.ui.tabs.compile_tab import create_compile_tab
from dspyui.ui.tabs.browse_tab import create_browse_tab
from dspyui.ui.language_switcher import create_language_switcher
from dspyui.i18n import t


def create_app() -> gr.Blocks:
    """
    创建 DSPyUI Gradio 应用。

    Returns:
        配置好的 Gradio Blocks 应用实例
    """
    with gr.Blocks(title="DSPyUI") as app:
        # 顶部标题和语言切换器
        with gr.Row():
            with gr.Column(scale=8):
                gr.Markdown(f"# {t('compile.title')}")
            with gr.Column(scale=4):
                language_dropdown, restart_notice = create_language_switcher()
        
        # 重启提示
        restart_notice
        
        # 主要内容区域
        with gr.Tabs():
            create_compile_tab()
            create_browse_tab()
    
    # Store CSS for use in launch()
    app._custom_css = CUSTOM_CSS
    return app


# 创建全局 demo 实例
demo = create_app()
