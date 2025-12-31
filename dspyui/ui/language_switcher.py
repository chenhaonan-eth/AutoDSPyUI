"""
语言切换组件

INPUT:  dspyui.i18n (翻译系统), gradio
OUTPUT: create_language_switcher() 函数
POS:    UI 辅助组件，提供语言切换功能和重启提示

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import gradio as gr
from dspyui.i18n import t, set_language, get_current_language


def create_language_switcher():
    """
    创建语言切换器组件。
    
    由于 Gradio 限制，语言切换需要重启应用才能生效。
    
    Returns:
        tuple: (language_dropdown, restart_notice)
    """
    current_lang = get_current_language()
    
    # 语言选项 - 使用双语显示
    language_options = [
        ("中文 / Chinese", "zh_CN"),
        ("English / 英文", "en_US")
    ]
    
    with gr.Row():
        with gr.Column(scale=7):
            pass  # 占位，让语言选择器靠右
        with gr.Column(scale=3):
            language_dropdown = gr.Dropdown(
                choices=language_options,
                value=current_lang,
                label=t("common.language_selector"),
                interactive=True,
                show_label=True,
                container=True
            )
    
    # 重启提示信息
    restart_notice = gr.Markdown(
        visible=False,
        elem_classes="language-notice"
    )
    
    def on_language_change(new_lang):
        """处理语言切换"""
        current = get_current_language()
        if new_lang != current:
            set_language(new_lang)
            
            # 根据新语言显示重启提示
            if new_lang == "zh_CN":
                notice_text = "⚠️ 语言已切换为中文，请重启应用以查看完整效果。"
            else:
                notice_text = "⚠️ Language switched to English, please restart the app to see full effect."
            
            return gr.update(value=notice_text, visible=True)
        return gr.update(visible=False)
    
    # 绑定语言切换事件
    language_dropdown.change(
        on_language_change,
        inputs=[language_dropdown],
        outputs=[restart_notice]
    )
    
    return language_dropdown, restart_notice