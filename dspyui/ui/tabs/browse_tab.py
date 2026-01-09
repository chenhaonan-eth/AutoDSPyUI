"""
Browse Prompts Tab

INPUT:  autodspy (register_model, get_mlflow_ui_url, get_registered_run_ids, load_prompt_artifact, register_compiled_model), dspyui.utils.file_ops, gradio
OUTPUT: create_browse_tab() 函数
POS:    浏览提示词 Tab，展示已保存的提示词列表

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import json
from typing import Optional, Dict, Any, List

import gradio as gr

from dspyui.utils.file_ops import list_prompts
from dspyui.config import MLFLOW_ENABLED
from autodspy import register_model, get_mlflow_ui_url, get_registered_run_ids
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
                                with gr.Row():
                                    gr.Number(
                                        value=float(sel_prompt['Eval Score']) if (sel_prompt['Eval Score'] and str(sel_prompt['Eval Score']) != 'N/A') else 0.0,
                                        label=t("browse.details.evaluation_score"),
                                        interactive=False
                                    )
                                    if MLFLOW_ENABLED:
                                        # 再次检查注册状态以便在详情页显示
                                        reg_run_ids = get_registered_run_ids()
                                        try:
                                            run_id = details.get("mlflow_run_id")
                                            if run_id and run_id in reg_run_ids:
                                                gr.Markdown(f"### {t('browse.card.registered')}")
                                            else:
                                                gr.Markdown(f"### *{t('browse.card.unregistered')}*")
                                        except Exception:
                                            pass
                                
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
                                
                                # MLflow 模型注册区域
                                if MLFLOW_ENABLED:
                                    with gr.Row():
                                        model_name_input = gr.Textbox(
                                            label=t("browse.mlflow.model_name_label"),
                                            placeholder=t("browse.mlflow.model_name_placeholder"),
                                            value=f"{details['human_readable_id']}-model"
                                        )
                                        register_model_btn = gr.Button(
                                            t("browse.mlflow.register_model"),
                                            variant="primary",
                                            size="sm"
                                        )
                                    
                                    register_status = gr.Markdown(visible=False)
                                    
                                    def register_model_action(model_name, prompt_details):
                                        """注册模型到 MLflow Model Registry"""
                                        from autodspy import register_compiled_model
                                        
                                        run_id = prompt_details.get('mlflow_run_id')
                                        
                                        # 调用业务逻辑层
                                        result = register_compiled_model(
                                            run_id=run_id,
                                            model_name=model_name,
                                            prompt_details=prompt_details
                                        )
                                        
                                        # UI 更新逻辑
                                        if result.success:
                                            message = t("browse.mlflow.register_model_success").format(
                                                version=result.version
                                            ) + f" [{t('browse.mlflow.view_model')}]({result.model_url})"
                                            return gr.update(visible=True, value=message)
                                        else:
                                            error_key = f"browse.mlflow.register_model_{result.error_code}"
                                            if result.error_code == "exception":
                                                message = t("browse.mlflow.register_model_error").format(
                                                    error=result.error_message
                                                )
                                            else:
                                                message = t(error_key)
                                            return gr.update(visible=True, value=message)
                                    
                                    register_model_btn.click(
                                        lambda name, details=details: register_model_action(name, details),
                                        inputs=[model_name_input],
                                        outputs=[register_status]
                                    )
                                
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
        
        # MLflow 已注册模型区域
        if MLFLOW_ENABLED:
            with gr.Accordion(t("browse.mlflow.registered_models_title"), open=False):
                gr.Markdown(t("browse.mlflow.load_models_hint") if "browse.mlflow.load_models_hint" in str(t("browse.mlflow")) else "点击下方按钮加载已注册的模型列表")
                refresh_models_btn = gr.Button(t("browse.mlflow.refresh_models"), size="sm", variant="primary")
                
                def load_registered_models():
                    """加载已注册的模型列表"""
                    try:
                        from mlflow import MlflowClient
                        
                        client = MlflowClient()
                        models = client.search_registered_models()
                        
                        model_data = []
                        for model in models:
                            for version in model.latest_versions:
                                model_data.append([
                                    model.name,
                                    version.version,
                                    version.current_stage,
                                    version.tags.get("evaluation_score", "N/A"),
                                    version.creation_timestamp,
                                    version.run_id
                                ])
                        
                        return model_data
                    except Exception as e:
                        gr.Warning(f"加载模型列表失败: {str(e)}")
                        return []
                
                registered_models_display = gr.Dataframe(
                    headers=[
                        t("browse.mlflow.model_table_headers.model_name"),
                        t("browse.mlflow.model_table_headers.version"),
                        t("browse.mlflow.model_table_headers.stage"),
                        t("browse.mlflow.model_table_headers.evaluation_score"),
                        t("browse.mlflow.model_table_headers.creation_time"),
                        t("browse.mlflow.model_table_headers.run_id")
                    ],
                    interactive=False,
                    wrap=True
                )
                
                
                # 处理模型行选择以查看详情
                def on_model_select(evt: gr.SelectData):
                    """当选择模型行时，加载其提示词详情并显示"""
                    from autodspy import load_prompt_artifact
                    
                    # 获取选择的行为数据
                    # evt.index 是 (row, col)
                    row_index = evt.index[0]
                    # 我们需要从 registered_models_display 的当前值中获取数据
                    # 但在这里我们直接重新加载或者从状态中获取。
                    # 简化方案：使用 gr.State 存储模型数据列表
                    
                # 为了支持选择，我们需要一个状态来存储模型数据
                mlflow_models_state = gr.State([])
                
                def refresh_models():
                    """刷新模型列表并更新状态"""
                    models = load_registered_models()
                    return gr.update(value=models), models
                
                refresh_models_btn.click(
                    refresh_models,
                    outputs=[registered_models_display, mlflow_models_state]
                )
                
                def show_mlflow_prompt_details(evt: gr.SelectData, models_list):
                    if not models_list:
                        return None, gr.update(visible=False)
                    
                    row_index = evt.index[0]
                    if row_index >= len(models_list):
                        return None, gr.update(visible=False)
                    
                    selected_row = models_list[row_index]
                    run_id = selected_row[5] # Run ID 是最后一列
                    
                    from autodspy import load_prompt_artifact
                    prompt_data = load_prompt_artifact(run_id)
                    
                    if prompt_data:
                        # 构造与 local prompts 兼容的数据结构
                        formatted_prompt = {
                            "ID": f"MLflow-{run_id[:8]}",
                            "Signature": f"{', '.join(prompt_data['input_fields'])} -> {', '.join(prompt_data['output_fields'])}",
                            "Eval Score": prompt_data.get('evaluation_score', 'N/A'),
                            "Details": json.dumps(prompt_data, indent=4)
                        }
                        return formatted_prompt, gr.update(visible=True)
                    else:
                        gr.Warning(t("browse.mlflow.load_artifact_failed") if "browse.mlflow.load_artifact_failed" in t("browse") else "Failed to load prompt artifact")
                        return None, gr.update(visible=False)

                registered_models_display.select(
                    show_mlflow_prompt_details,
                    inputs=[mlflow_models_state],
                    outputs=[selected_prompt, close_details_btn]
                )
        
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
                key_func = lambda x: float(x["Eval Score"]) if (x["Eval Score"] and x["Eval Score"] != 'N/A') else -1.0
            else:
                key_func = lambda x: x["ID"]
            
            sorted_prompts = sorted(filtered_prompts, key=key_func, reverse=(order == t("browse.descending_option")))
            
            # 获取已注册的 Run ID
            registered_run_ids = get_registered_run_ids() if MLFLOW_ENABLED else set()
            
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
                                        
                                        # 显示注册状态
                                        if MLFLOW_ENABLED:
                                            try:
                                                details = json.loads(prompt["Details"])
                                                run_id = details.get("mlflow_run_id")
                                                if run_id and run_id in registered_run_ids:
                                                    gr.Markdown(f"**{t('browse.card.registered')}**")
                                                else:
                                                    gr.Markdown(f"*{t('browse.card.unregistered')}*")
                                            except Exception:
                                                pass
                                    view_details_btn = gr.Button(t("browse.view_details_button"), elem_classes="view-details-btn", size="sm")
                                
                                prompt_components.append((prompt, view_details_btn))
            
            for prompt, btn in prompt_components:
                btn.click(
                    lambda p=prompt: (p, gr.update(visible=True)),
                    outputs=[selected_prompt, close_details_btn]
                )
