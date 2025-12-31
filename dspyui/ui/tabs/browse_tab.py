"""
Browse Prompts Tab

INPUT:  dspyui.utils.file_ops, gradio
OUTPUT: create_browse_tab() 函数
POS:    浏览提示词 Tab，展示已保存的提示词列表

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import json
from typing import Optional, Dict, Any, List

import gradio as gr

from dspyui.utils.file_ops import list_prompts
from dspyui.i18n import t


def create_browse_tab() -> None:
    """
    创建 View Prompts Tab。
    
    包含：
    - 提示词过滤和排序
    - 提示词卡片列表
    - 详情查看功能
    """
    with gr.TabItem(t("browse.tab_title")):
        prompts = list_prompts()
        selected_prompt = gr.State(None)
        
        # 提取唯一签名
        unique_signatures = sorted(set(p["Signature"] for p in prompts))

        close_details_btn = gr.Button(t("browse.close_details_button"), elem_classes="close-details-btn", size="sm", visible=False)
        close_details_btn.click(
            lambda: (None, gr.update(visible=False)),
            outputs=[selected_prompt, close_details_btn]
        )

        # 详情渲染
        @gr.render(inputs=[selected_prompt])
        def render_prompt_details(sel_prompt: Optional[Dict[str, Any]]):
            if sel_prompt is not None:
                with gr.Row():
                    with gr.Column():
                        details = json.loads(sel_prompt["Details"])
                        gr.Markdown(f"## {details['human_readable_id']}")
                        with gr.Group():
                            with gr.Column(elem_classes="prompt-details-full"):
                                gr.Number(
                                    value=float(sel_prompt['Eval Score']),
                                    label=t("browse.details.evaluation_score"),
                                    interactive=False
                                )
                                
                                with gr.Row():
                                    gr.Dropdown(
                                        choices=details['input_fields'],
                                        value=details['input_fields'],
                                        label=t("browse.details.input_fields"),
                                        interactive=False,
                                        multiselect=True,
                                        info=", ".join(details.get('input_descs', []))
                                    )
                                    gr.Dropdown(
                                        choices=details['output_fields'],
                                        value=details['output_fields'],
                                        label=t("browse.details.output_fields"),
                                        interactive=False,
                                        multiselect=True,
                                        info=", ".join(details.get('output_descs', []))
                                    )
                                
                                with gr.Row():
                                    gr.Dropdown(choices=[details['dspy_module']], value=details['dspy_module'], label=t("browse.details.module"), interactive=False)
                                    gr.Dropdown(choices=[details['llm_model']], value=details['llm_model'], label=t("browse.details.model"), interactive=False)
                                    gr.Dropdown(choices=[details['teacher_model']], value=details['teacher_model'], label=t("browse.details.teacher_model"), interactive=False)
                                    gr.Dropdown(choices=[details['optimizer']], value=details['optimizer'], label=t("browse.details.optimizer"), interactive=False)
                                
                                gr.Textbox(value=details['instructions'], label=t("browse.details.instructions"), interactive=False)
                                gr.Textbox(value=details['optimized_prompt'], label=t("browse.details.optimized_prompt"), interactive=False)
                                
                                # 其他字段
                                skip_keys = ['signature', 'evaluation_score', 'input_fields', 'output_fields',
                                            'dspy_module', 'llm_model', 'teacher_model', 'optimizer',
                                            'instructions', 'optimized_prompt', 'human_readable_id']
                                for key, value in details.items():
                                    if key not in skip_keys:
                                        if isinstance(value, list):
                                            gr.Dropdown(choices=value, value=value, label=key.replace('_', ' ').title(), interactive=False, multiselect=True)
                                        elif isinstance(value, bool):
                                            gr.Checkbox(value=value, label=key.replace('_', ' ').title(), interactive=False)
                                        elif isinstance(value, (int, float)):
                                            gr.Number(value=value, label=key.replace('_', ' ').title(), interactive=False)
                                        else:
                                            gr.Textbox(value=str(value), label=key.replace('_', ' ').title(), interactive=False)

        gr.Markdown(f"# {t('browse.title')}")
        
        # 过滤和排序
        with gr.Row():
            filter_signature = gr.Dropdown(
                label=t("browse.filter_signature_label"),
                choices=[t("browse.all_option")] + unique_signatures,
                value=t("browse.all_option"),
                scale=2
            )
            sort_by = gr.Radio(
                [t("browse.run_date_option"), t("browse.evaluation_score_option")],
                label=t("browse.sort_by_label"),
                value=t("browse.run_date_option"),
                scale=1
            )
            sort_order = gr.Radio(
                [t("browse.descending_option"), t("browse.ascending_option")],
                label=t("browse.sort_order_label"),
                value=t("browse.descending_option"),
                scale=1
            )

        # 渲染提示词卡片
        @gr.render(inputs=[filter_signature, sort_by, sort_order])
        def render_prompts(filter_sig: str, sort: str, order: str):
            if filter_sig and filter_sig != t("browse.all_option"):
                filtered_prompts = list_prompts(signature_filter=filter_sig)
            else:
                filtered_prompts = prompts
            
            if sort == t("browse.evaluation_score_option"):
                key_func = lambda x: float(x["Eval Score"])
            else:
                key_func = lambda x: x["ID"]
            
            sorted_prompts = sorted(filtered_prompts, key=key_func, reverse=(order == t("browse.descending_option")))
            
            prompt_components: List[tuple] = []
            
            for i in range(0, len(sorted_prompts), 3):
                with gr.Row():
                    for j in range(3):
                        if i + j < len(sorted_prompts):
                            prompt = sorted_prompts[i + j]
                            with gr.Column():
                                with gr.Group(elem_classes="prompt-card"):
                                    with gr.Column(elem_classes="prompt-details"):
                                        gr.Markdown(f"**{t('browse.card.id')}:** {prompt['ID']}")
                                        gr.Markdown(f"**{t('browse.card.signature')}:** {prompt['Signature']}")
                                        gr.Markdown(f"**{t('browse.card.eval_score')}:** {prompt['Eval Score']}")
                                    view_details_btn = gr.Button(t("browse.view_details_button"), elem_classes="view-details-btn", size="sm")
                                
                                prompt_components.append((prompt, view_details_btn))
            
            for prompt, btn in prompt_components:
                btn.click(
                    lambda p=prompt: (p, gr.update(visible=True)),
                    outputs=[selected_prompt, close_details_btn]
                )
