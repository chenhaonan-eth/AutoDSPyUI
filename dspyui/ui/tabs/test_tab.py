"""
Test Model Tab

INPUT:  dspyui.core.mlflow_loader, dspyui.core.runner, gradio
OUTPUT: create_test_tab() 函数
POS:    测试 Tab，提供从 MLflow 加载模型进行测试的界面

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

from typing import Optional, List, Dict, Any

import gradio as gr
import pandas as pd

from dspyui.config import MLFLOW_ENABLED, LLM_OPTIONS
from dspyui.core.mlflow_loader import (
    list_registered_models,
    list_model_versions,
    get_model_metadata,
)
from dspyui.core.runner import (
    generate_response_from_mlflow,
    run_batch_inference_from_mlflow,
)
from dspyui.i18n import t


def create_test_tab() -> None:
    """
    创建 Test Model Tab。
    
    功能：
    - 模型选择器：选择已注册模型和版本
    - LM 选择器：选择推理用的 LLM
    - 单条测试：输入数据，查看输出
    - 批量测试：上传 CSV，批量推理
    """
    with gr.TabItem(t("test.tab_title")):
        if not MLFLOW_ENABLED:
            gr.Markdown(t("test.mlflow_disabled"))
            return
        
        gr.Markdown(f"# {t('test.title')}")
        gr.Markdown(t("test.description"))
        
        # 状态变量
        selected_model_metadata = gr.State({})
        
        # ============================================================
        # 模型选择区
        # ============================================================
        with gr.Group():
            gr.Markdown(f"### {t('test.model_selection')}")
            
            with gr.Row():
                # 获取已注册模型列表
                models = list_registered_models()
                model_names = [m["name"] for m in models] if models else []
                
                model_dropdown = gr.Dropdown(
                    label=t("test.model_name"),
                    choices=model_names,
                    value=model_names[0] if model_names else None,
                    interactive=True,
                    scale=2
                )
                
                version_dropdown = gr.Dropdown(
                    label=t("test.model_version"),
                    choices=[],
                    interactive=True,
                    scale=1
                )
                
                llm_dropdown = gr.Dropdown(
                    label=t("test.llm_model"),
                    choices=LLM_OPTIONS,
                    value="gpt-4o-mini",
                    interactive=True,
                    scale=1
                )
            
            # 模型信息展示
            model_info = gr.Markdown(visible=False)
        
        # 模型选择联动
        def on_model_change(model_name: str):
            """模型切换时更新版本列表"""
            if not model_name:
                return gr.update(choices=[], value=None), gr.update(visible=False, value=""), {}
            
            versions = list_model_versions(model_name)
            version_choices = [v["version"] for v in versions]
            default_version = version_choices[0] if version_choices else None
            
            if default_version:
                metadata = get_model_metadata(model_name, default_version)
                info_text = _format_model_info(metadata)
                return (
                    gr.update(choices=version_choices, value=default_version),
                    gr.update(visible=True, value=info_text),
                    metadata
                )
            
            return gr.update(choices=version_choices, value=None), gr.update(visible=False), {}
        
        def on_version_change(model_name: str, version: str):
            """版本切换时更新模型信息"""
            if not model_name or not version:
                return gr.update(visible=False, value=""), {}
            
            metadata = get_model_metadata(model_name, version)
            info_text = _format_model_info(metadata)
            return gr.update(visible=True, value=info_text), metadata
        
        model_dropdown.change(
            on_model_change,
            inputs=[model_dropdown],
            outputs=[version_dropdown, model_info, selected_model_metadata]
        )
        
        version_dropdown.change(
            on_version_change,
            inputs=[model_dropdown, version_dropdown],
            outputs=[model_info, selected_model_metadata]
        )
        
        # ============================================================
        # 单条测试区
        # ============================================================
        with gr.Group():
            gr.Markdown(f"### {t('test.single_test')}")
            
            # 动态输入区域
            @gr.render(inputs=[selected_model_metadata])
            def render_input_fields(metadata: Dict):
                input_fields = metadata.get("input_fields", [])
                
                if not input_fields:
                    gr.Markdown(t("test.select_model_first"))
                    return
                
                input_components = []
                for field in input_fields:
                    tb = gr.Textbox(
                        label=field,
                        placeholder=f"{t('test.enter')} {field}...",
                        lines=2
                    )
                    input_components.append(tb)
                
                test_btn = gr.Button(t("test.run_test"), variant="primary")
                output_display = gr.Textbox(
                    label=t("test.output"),
                    lines=6,
                    interactive=False
                )
                
                def run_single_test(*input_values):
                    """执行单条测试"""
                    model_name = metadata.get("model_name") or model_dropdown.value
                    version = metadata.get("version") or version_dropdown.value
                    
                    if not model_name or not version:
                        return t("test.error_no_model")
                    
                    # 构建输入数据
                    input_fields = metadata.get("input_fields", [])
                    row_data = dict(zip(input_fields, input_values))
                    
                    try:
                        # 获取当前选择的 LLM
                        llm = llm_dropdown.value or "gpt-4o-mini"
                        result = generate_response_from_mlflow(
                            model_name=model_name,
                            version=version,
                            row_data=row_data,
                            llm_model=llm
                        )
                        return result
                    except Exception as e:
                        return f"Error: {str(e)}"
                
                test_btn.click(
                    run_single_test,
                    inputs=input_components,
                    outputs=[output_display]
                )
        
        # ============================================================
        # 批量测试区
        # ============================================================
        with gr.Group():
            gr.Markdown(f"### {t('test.batch_test')}")
            
            with gr.Row():
                csv_upload = gr.File(
                    label=t("test.upload_csv"),
                    file_types=[".csv"],
                    scale=2
                )
                batch_btn = gr.Button(t("test.run_batch"), variant="secondary", scale=1)
            
            batch_progress = gr.Textbox(label=t("test.progress"), interactive=False, visible=False)
            batch_result = gr.Dataframe(label=t("test.batch_result"), interactive=False)
            download_btn = gr.File(label=t("test.download_result"), visible=False)
            
            def run_batch_test(file, model_name, version, llm_model, metadata):
                """执行批量测试"""
                if file is None:
                    gr.Warning(t("test.error_no_file"))
                    return None, gr.update(visible=False)
                
                if not model_name or not version:
                    gr.Warning(t("test.error_no_model"))
                    return None, gr.update(visible=False)
                
                try:
                    # 读取 CSV
                    data = pd.read_csv(file.name)
                    
                    # 执行批量推理
                    result_df = run_batch_inference_from_mlflow(
                        model_name=model_name,
                        version=version,
                        data=data,
                        llm_model=llm_model
                    )
                    
                    # 保存结果
                    output_path = f"/tmp/batch_result_{model_name}_{version}.csv"
                    result_df.to_csv(output_path, index=False)
                    
                    return result_df, gr.update(visible=True, value=output_path)
                    
                except Exception as e:
                    gr.Error(f"{t('test.error')}: {str(e)}")
                    return None, gr.update(visible=False)
            
            batch_btn.click(
                run_batch_test,
                inputs=[csv_upload, model_dropdown, version_dropdown, llm_dropdown, selected_model_metadata],
                outputs=[batch_result, download_btn]
            )


def _format_model_info(metadata: Dict[str, Any]) -> str:
    """格式化模型信息为 Markdown"""
    if not metadata:
        return ""
    
    parts = []
    
    if metadata.get("input_fields"):
        parts.append(f"**Input:** {', '.join(metadata['input_fields'])}")
    if metadata.get("output_fields"):
        parts.append(f"**Output:** {', '.join(metadata['output_fields'])}")
    if metadata.get("dspy_module"):
        parts.append(f"**Module:** {metadata['dspy_module']}")
    if metadata.get("optimizer"):
        parts.append(f"**Optimizer:** {metadata['optimizer']}")
    if metadata.get("evaluation_score"):
        parts.append(f"**Score:** {metadata['evaluation_score']:.4f}")
    if metadata.get("stage"):
        parts.append(f"**Stage:** {metadata['stage']}")
    
    return " | ".join(parts) if parts else ""
