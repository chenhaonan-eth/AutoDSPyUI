"""
Run Program Tab

INPUT:  dspyui.core.runner, dspyui.utils.file_ops, gradio, pandas
OUTPUT: create_run_tab() 函数
POS:    运行程序 Tab，提供已编译程序的交互式推理界面，支持单条和批量推理、历史记录

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import tempfile
import os

import gradio as gr
import pandas as pd

from dspyui.core.runner import (
    load_program_metadata,
    generate_program_response,
    validate_csv_headers,
    run_batch_inference,
)
from dspyui.utils.file_ops import list_programs
from dspyui.i18n import t


# 最大输入字段数量
MAX_INPUT_FIELDS = 10

# 最大历史记录数量
MAX_HISTORY_SIZE = 10


@dataclass
class InferenceHistoryItem:
    """
    推理历史记录项。
    
    Attributes:
        timestamp: 推理执行时间
        program_id: 程序 ID
        inputs: 输入字段值字典
        outputs: 输出字段值字典
    """
    timestamp: datetime
    program_id: str
    inputs: Dict[str, str]
    outputs: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "program_id": self.program_id,
            "inputs": self.inputs,
            "outputs": self.outputs,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InferenceHistoryItem":
        """从字典创建实例"""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            program_id=data["program_id"],
            inputs=data["inputs"],
            outputs=data["outputs"],
        )
    
    def format_display(self) -> str:
        """格式化为显示字符串"""
        time_str = self.timestamp.strftime("%H:%M:%S")
        input_preview = ", ".join(f"{k}={v[:20]}..." if len(v) > 20 else f"{k}={v}" 
                                   for k, v in list(self.inputs.items())[:2])
        return f"[{time_str}] {input_preview}"


def add_history_item(
    history: List[Dict[str, Any]],
    program_id: str,
    inputs: Dict[str, str],
    outputs: Dict[str, str],
) -> List[Dict[str, Any]]:
    """
    添加历史记录项。
    
    Args:
        history: 当前历史记录列表
        program_id: 程序 ID
        inputs: 输入字段值
        outputs: 输出字段值
        
    Returns:
        更新后的历史记录列表（最多 MAX_HISTORY_SIZE 条）
    
    Requirements: 5.1, 5.2
    """
    item = InferenceHistoryItem(
        timestamp=datetime.now(),
        program_id=program_id,
        inputs=inputs,
        outputs=outputs,
    )
    
    # 添加到列表开头（最新的在前）
    new_history = [item.to_dict()] + history
    
    # 限制最大数量
    if len(new_history) > MAX_HISTORY_SIZE:
        new_history = new_history[:MAX_HISTORY_SIZE]
    
    return new_history


def get_history_choices(history: List[Dict[str, Any]]) -> List[Tuple[str, int]]:
    """
    获取历史记录的选择列表。
    
    Args:
        history: 历史记录列表
        
    Returns:
        (显示文本, 索引) 元组列表
    """
    choices = []
    for i, item_dict in enumerate(history):
        item = InferenceHistoryItem.from_dict(item_dict)
        choices.append((item.format_display(), i))
    return choices


def clear_history() -> List[Dict[str, Any]]:
    """
    清空历史记录。
    
    Returns:
        空的历史记录列表
        
    Requirements: 5.4
    """
    return []


def create_run_tab() -> None:
    """
    创建 Run Program Tab。
    
    包含：
    - 程序选择器
    - 程序信息展示区
    - 动态输入字段
    - 运行按钮和结果展示
    - 批量处理区域
    
    Requirements: 1.1, 1.2, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1-3.6, 4.1-4.5
    """
    with gr.TabItem(t("run.tab_title")):
        # === 状态变量 ===
        current_program_id = gr.State(None)
        current_metadata = gr.State(None)
        current_mode = gr.State("single")  # "single" or "batch"
        batch_result_df = gr.State(None)  # 存储批量推理结果
        inference_history = gr.State([])  # 存储历史记录列表
        
        # === 1. 标题 ===
        gr.Markdown(f"# {t('run.title')}")
        gr.Markdown(t("run.subtitle"))
        
        # === 2. 程序选择区域 ===
        # 初始化时加载程序列表
        initial_programs = list_programs()
        initial_choices = [
            f"{p['id']} - {p['signature']} (Score: {p['eval_score']})"
            for p in initial_programs
        ] if initial_programs else []
        
        with gr.Row():
            with gr.Column(scale=3):
                program_dropdown = gr.Dropdown(
                    label=t("run.select_program"),
                    choices=initial_choices,
                    value=None,
                    interactive=True,
                    allow_custom_value=False,
                )
            with gr.Column(scale=1):
                refresh_btn = gr.Button(
                    t("run.refresh_programs"),
                    size="sm",
                )
        
        # === 3. 程序信息展示区域 ===
        with gr.Group(visible=False) as program_info_group:
            gr.Markdown(f"### {t('run.program_info.title')}")
            
            with gr.Row():
                signature_display = gr.Textbox(
                    label=t("run.program_info.signature"),
                    interactive=False,
                )
                model_display = gr.Textbox(
                    label=t("run.program_info.model"),
                    interactive=False,
                )
                module_display = gr.Textbox(
                    label=t("run.program_info.module"),
                    interactive=False,
                )
            
            with gr.Row():
                teacher_display = gr.Textbox(
                    label=t("run.program_info.teacher_model"),
                    interactive=False,
                )
                optimizer_display = gr.Textbox(
                    label=t("run.program_info.optimizer"),
                    interactive=False,
                )
            
            with gr.Row():
                eval_score_display = gr.Number(
                    label=t("run.program_info.evaluation_score"),
                    interactive=False,
                )
                baseline_score_display = gr.Number(
                    label=t("run.program_info.baseline_score"),
                    interactive=False,
                )
            
            instructions_display = gr.Textbox(
                label=t("run.program_info.instructions"),
                interactive=False,
                lines=2,
            )
            
            # 可展开的优化提示词区域
            with gr.Accordion(
                t("run.program_info.view_prompt"),
                open=False,
            ):
                optimized_prompt_display = gr.Textbox(
                    label=t("run.program_info.optimized_prompt"),
                    interactive=False,
                    lines=15,
                    elem_classes=["optimized-prompt-textbox"],
                )
        
        # === 4. 输入区域 ===
        with gr.Group(visible=False) as input_section_group:
            gr.Markdown(f"### {t('run.input_section.title')}")
            gr.Markdown(t("run.input_section.description"))
            
            # 固定数量的输入字段槽位
            input_fields: List[Tuple[gr.Group, gr.Textbox]] = []
            for i in range(MAX_INPUT_FIELDS):
                with gr.Group(visible=False) as input_group:
                    input_textbox = gr.Textbox(
                        label=f"Input {i+1}",
                        placeholder="",
                        interactive=True,
                        lines=2,
                    )
                input_fields.append((input_group, input_textbox))
        
        # === 5. 运行按钮和输出区域 ===
        with gr.Group(visible=False) as output_section_group:
            with gr.Row():
                run_btn = gr.Button(
                    t("run.buttons.run"),
                    variant="primary",
                    scale=1,
                )
                clear_btn = gr.Button(
                    t("run.buttons.clear"),
                    scale=1,
                )
            
            # 加载状态指示器
            loading_indicator = gr.Markdown(
                value=f"⏳ {t('run.loading.inference')}",
                visible=False,
            )
            
            gr.Markdown(f"### {t('run.output_section.title')}")
            
            output_display = gr.Textbox(
                label=t("run.output_section.description"),
                interactive=False,
                lines=10,
                max_lines=20,
            )
            
            error_display = gr.Markdown(visible=False)
        
        # === 6. 模式切换和批量处理区域 ===
        with gr.Group(visible=False) as batch_section_group:
            gr.Markdown(f"### {t('run.batch.title')}")
            
            # 模式切换按钮
            with gr.Row():
                mode_toggle_btn = gr.Button(
                    t("run.mode.switch_to_batch"),
                    variant="secondary",
                    scale=1,
                )
            
            # 批量处理区域 (初始隐藏)
            with gr.Group(visible=False) as batch_upload_group:
                # 显示期望的列名
                expected_headers_display = gr.Textbox(
                    label=t("run.batch.expected_headers"),
                    interactive=False,
                    lines=1,
                )
                
                # CSV 上传组件
                csv_upload = gr.File(
                    label=t("run.batch.upload_csv"),
                    file_types=[".csv"],
                    type="filepath",
                )
                
                # CSV 验证状态显示
                csv_validation_status = gr.Markdown(visible=False)
                
                # 开始批量推理按钮
                start_batch_btn = gr.Button(
                    t("run.batch.start_batch"),
                    variant="primary",
                    interactive=False,
                )
                
                # 进度显示
                batch_progress = gr.Markdown(
                    value="",
                    visible=False,
                )
                
                # 结果预览表格
                batch_results_table = gr.Dataframe(
                    label=t("run.batch.results_preview"),
                    visible=False,
                    interactive=False,
                )
                
                # 导出按钮和下载组件
                with gr.Row(visible=False) as export_row:
                    export_btn = gr.Button(
                        t("run.batch.export_results"),
                        variant="secondary",
                    )
                    download_file = gr.File(
                        label=t("run.batch.download_csv"),
                        visible=False,
                    )
        
        # === 7. 历史记录区域 ===
        with gr.Group(visible=False) as history_section_group:
            gr.Markdown(f"### {t('run.history.title')}")
            gr.Markdown(t("run.history.description"))
            
            # 历史记录列表
            history_list = gr.Dropdown(
                label=t("run.history.click_to_restore"),
                choices=[],
                value=None,
                interactive=True,
                allow_custom_value=False,
            )
            
            # 清空历史按钮
            clear_history_btn = gr.Button(
                t("run.history.clear"),
                variant="secondary",
                size="sm",
            )
            
            # 空历史提示
            history_empty_msg = gr.Markdown(
                value=f"📭 {t('run.history.empty')}",
                visible=True,
            )
        
        # === 事件处理函数 ===
        
        def refresh_program_list() -> Dict[str, Any]:
            """刷新程序列表"""
            programs = list_programs()
            if not programs:
                return gr.update(
                    choices=[],
                    value=None,
                    info=t("run.no_programs_available"),
                )
            
            # 构建选项列表: "ID - Signature (Score: X)"
            choices = [
                f"{p['id']} - {p['signature']} (Score: {p['eval_score']})"
                for p in programs
            ]
            return gr.update(choices=choices, value=None)
        
        def on_program_select(
            selection: Optional[str],
        ) -> Tuple[Any, ...]:
            """
            当用户选择程序时加载元数据并更新 UI。
            
            Returns:
                更新所有相关组件的元组
            """
            if not selection:
                # 隐藏所有区域
                updates = [
                    None,  # current_program_id
                    None,  # current_metadata
                    gr.update(visible=False),  # program_info_group
                    gr.update(visible=False),  # input_section_group
                    gr.update(visible=False),  # output_section_group
                    "",  # signature_display
                    "",  # model_display
                    "",  # module_display
                    "",  # teacher_display
                    "",  # optimizer_display
                    0.0,  # eval_score_display
                    0.0,  # baseline_score_display
                    "",  # instructions_display
                    "",  # optimized_prompt_display
                ]
                # 隐藏所有输入字段
                for _ in range(MAX_INPUT_FIELDS):
                    updates.append(gr.update(visible=False))  # input_group
                    updates.append(gr.update(value="", label=""))  # input_textbox
                
                return tuple(updates)
            
            # 从选择中提取程序 ID
            program_id = selection.split(" - ")[0]
            
            try:
                metadata = load_program_metadata(program_id)
            except ValueError as e:
                # 加载失败，显示错误
                updates = [
                    None,
                    None,
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    "",
                    "",
                    "",
                    "",
                    "",
                    0.0,
                    0.0,
                    "",
                    "",
                ]
                for _ in range(MAX_INPUT_FIELDS):
                    updates.append(gr.update(visible=False))
                    updates.append(gr.update(value="", label=""))
                
                gr.Warning(t("run.errors.load_failed").format(error=str(e)))
                return tuple(updates)
            
            # 构建更新
            input_fields_list = metadata.get('input_fields', [])
            input_descs_list = metadata.get('input_descs', [])
            
            updates = [
                program_id,  # current_program_id
                metadata,  # current_metadata
                gr.update(visible=True),  # program_info_group
                gr.update(visible=True),  # input_section_group
                gr.update(visible=True),  # output_section_group
                metadata.get('signature', ''),  # signature_display
                metadata.get('llm_model', ''),  # model_display
                metadata.get('dspy_module', ''),  # module_display
                metadata.get('teacher_model', ''),  # teacher_display
                metadata.get('optimizer', ''),  # optimizer_display
                metadata.get('evaluation_score', 0.0),  # eval_score_display
                metadata.get('baseline_score', 0.0),  # baseline_score_display
                metadata.get('instructions', ''),  # instructions_display
                metadata.get('optimized_prompt', ''),  # optimized_prompt_display
            ]
            
            # 更新输入字段
            for i in range(MAX_INPUT_FIELDS):
                if i < len(input_fields_list):
                    field_name = input_fields_list[i]
                    field_desc = input_descs_list[i] if i < len(input_descs_list) else ""
                    label = f"{field_name}" + (f" ({field_desc})" if field_desc else "")
                    updates.append(gr.update(visible=True))  # input_group
                    updates.append(gr.update(value="", label=label, placeholder=field_desc))  # input_textbox
                else:
                    updates.append(gr.update(visible=False))  # input_group
                    updates.append(gr.update(value="", label=""))  # input_textbox
            
            return tuple(updates)
        
        def run_inference(
            program_id: Optional[str],
            metadata: Optional[Dict[str, Any]],
            history: List[Dict[str, Any]],
            *input_values: str,
        ) -> Tuple[str, Any, Any, List[Dict[str, Any]], Any, Any, Any]:
            """
            执行单条推理并更新历史记录。
            
            Args:
                program_id: 程序 ID
                metadata: 程序元数据
                history: 当前历史记录列表
                *input_values: 输入字段的值
                
            Returns:
                (输出文本, 错误显示更新, 加载指示器更新, 更新后的历史记录,
                 历史列表更新, 空历史提示更新, 历史区域更新)
                 
            Requirements: 2.2, 2.3, 5.1
            """
            if not program_id or not metadata:
                return (
                    "",
                    gr.update(visible=True, value=f"⚠️ {t('run.errors.load_failed').format(error='No program selected')}"),
                    gr.update(visible=False),
                    history,
                    gr.update(),  # history_list
                    gr.update(),  # history_empty_msg
                    gr.update(),  # history_section_group
                )
            
            input_fields_list = metadata.get('input_fields', [])
            
            # 检查是否所有必填字段都已填写
            row_data: Dict[str, Any] = {}
            for i, field_name in enumerate(input_fields_list):
                if i < len(input_values):
                    value = input_values[i]
                    if not value or not value.strip():
                        return (
                            "",
                            gr.update(visible=True, value=f"⚠️ {t('run.errors.empty_input')}"),
                            gr.update(visible=False),
                            history,
                            gr.update(),
                            gr.update(),
                            gr.update(),
                        )
                    row_data[field_name] = value
                else:
                    return (
                        "",
                        gr.update(visible=True, value=f"⚠️ {t('run.errors.empty_input')}"),
                        gr.update(visible=False),
                        history,
                        gr.update(),
                        gr.update(),
                        gr.update(),
                    )
            
            try:
                result = generate_program_response(program_id, row_data)
                
                # 添加到历史记录
                outputs = {"result": result}
                new_history = add_history_item(history, program_id, row_data, outputs)
                
                # 更新历史列表选项
                choices = get_history_choices(new_history)
                choice_labels = [c[0] for c in choices]
                
                return (
                    result,
                    gr.update(visible=False),
                    gr.update(visible=False),
                    new_history,
                    gr.update(choices=choice_labels, value=None),
                    gr.update(visible=False),  # 隐藏空历史提示
                    gr.update(visible=True),  # 显示历史区域
                )
            except Exception as e:
                error_msg = t("run.errors.inference_failed").format(error=str(e))
                return (
                    "",
                    gr.update(visible=True, value=f"❌ {error_msg}"),
                    gr.update(visible=False),
                    history,
                    gr.update(),
                    gr.update(),
                    gr.update(),
                )
        
        def clear_inputs(*args) -> Tuple[Any, ...]:
            """清空所有输入和输出"""
            updates = [""]  # output_display
            updates.append(gr.update(visible=False))  # error_display
            updates.append(gr.update(visible=False))  # loading_indicator
            for _ in range(MAX_INPUT_FIELDS):
                updates.append("")  # input_textbox value
            return tuple(updates)
        
        # === 历史记录事件处理函数 ===
        
        def on_history_select(
            selection: Optional[str],
            history: List[Dict[str, Any]],
            metadata: Optional[Dict[str, Any]],
        ) -> Tuple[Any, ...]:
            """
            当用户选择历史记录项时，回填输入字段。
            
            Args:
                selection: 选中的历史记录显示文本
                history: 历史记录列表
                metadata: 当前程序元数据
                
            Returns:
                更新输入字段的元组
                
            Requirements: 5.3
            """
            if not selection or not history or not metadata:
                # 返回空更新
                updates = []
                for _ in range(MAX_INPUT_FIELDS):
                    updates.append(gr.update())
                return tuple(updates)
            
            # 根据选择文本找到对应的历史记录索引
            choices = get_history_choices(history)
            selected_index = None
            for label, idx in choices:
                if label == selection:
                    selected_index = idx
                    break
            
            if selected_index is None or selected_index >= len(history):
                updates = []
                for _ in range(MAX_INPUT_FIELDS):
                    updates.append(gr.update())
                return tuple(updates)
            
            # 获取历史记录项
            item_dict = history[selected_index]
            item = InferenceHistoryItem.from_dict(item_dict)
            
            # 获取输入字段列表
            input_fields_list = metadata.get('input_fields', [])
            
            # 构建更新
            updates = []
            for i in range(MAX_INPUT_FIELDS):
                if i < len(input_fields_list):
                    field_name = input_fields_list[i]
                    value = item.inputs.get(field_name, "")
                    updates.append(gr.update(value=value))
                else:
                    updates.append(gr.update())
            
            return tuple(updates)
        
        def on_clear_history() -> Tuple[List[Dict[str, Any]], Any, Any]:
            """
            清空历史记录。
            
            Returns:
                (空历史列表, 历史列表更新, 空历史提示更新)
                
            Requirements: 5.4
            """
            gr.Info(t("run.success.history_cleared"))
            return (
                [],  # inference_history
                gr.update(choices=[], value=None),  # history_list
                gr.update(visible=True),  # history_empty_msg
            )
        
        # === 批量处理事件处理函数 ===
        
        def toggle_mode(
            current_mode_val: str,
            metadata: Optional[Dict[str, Any]],
        ) -> Tuple[Any, ...]:
            """
            切换单条/批量模式。
            
            Args:
                current_mode_val: 当前模式 ("single" or "batch")
                metadata: 程序元数据
                
            Returns:
                更新组件的元组
            """
            if current_mode_val == "single":
                # 切换到批量模式
                new_mode = "batch"
                btn_text = t("run.mode.switch_to_single")
                show_batch = True
                show_single_input = False
                show_single_output = False
                
                # 获取期望的列名
                if metadata:
                    input_fields_list = metadata.get('input_fields', [])
                    expected_headers = ", ".join(input_fields_list)
                else:
                    expected_headers = ""
            else:
                # 切换到单条模式
                new_mode = "single"
                btn_text = t("run.mode.switch_to_batch")
                show_batch = False
                show_single_input = True
                show_single_output = True
                expected_headers = ""
            
            return (
                new_mode,  # current_mode
                gr.update(value=btn_text),  # mode_toggle_btn
                gr.update(visible=show_batch),  # batch_upload_group
                gr.update(visible=show_single_input),  # input_section_group
                gr.update(visible=show_single_output),  # output_section_group
                gr.update(value=expected_headers),  # expected_headers_display
                gr.update(visible=False),  # csv_validation_status
                gr.update(interactive=False),  # start_batch_btn
                None,  # csv_upload (reset)
                gr.update(visible=False),  # batch_results_table
                gr.update(visible=False),  # export_row
                gr.update(visible=False),  # batch_progress
            )
        
        def on_csv_upload(
            file_path: Optional[str],
            metadata: Optional[Dict[str, Any]],
        ) -> Tuple[Any, ...]:
            """
            处理 CSV 文件上传，验证头部。
            
            Args:
                file_path: 上传的 CSV 文件路径
                metadata: 程序元数据
                
            Returns:
                更新组件的元组
            """
            if not file_path or not metadata:
                return (
                    gr.update(visible=False),  # csv_validation_status
                    gr.update(interactive=False),  # start_batch_btn
                )
            
            try:
                # 读取 CSV 文件头部
                df = pd.read_csv(file_path, nrows=0)
                csv_headers = list(df.columns)
                
                # 获取程序的输入字段
                input_fields_list = metadata.get('input_fields', [])
                
                # 验证头部
                is_valid, error_msg = validate_csv_headers(csv_headers, input_fields_list)
                
                if is_valid:
                    return (
                        gr.update(
                            visible=True,
                            value=f"✅ {t('run.batch.completed')}: CSV 文件验证通过"
                        ),  # csv_validation_status
                        gr.update(interactive=True),  # start_batch_btn
                    )
                else:
                    return (
                        gr.update(
                            visible=True,
                            value=f"❌ {error_msg}"
                        ),  # csv_validation_status
                        gr.update(interactive=False),  # start_batch_btn
                    )
                    
            except Exception as e:
                return (
                    gr.update(
                        visible=True,
                        value=f"❌ {t('run.errors.csv_upload_failed').format(error=str(e))}"
                    ),  # csv_validation_status
                    gr.update(interactive=False),  # start_batch_btn
                )
        
        def run_batch(
            file_path: Optional[str],
            program_id: Optional[str],
            metadata: Optional[Dict[str, Any]],
            progress: gr.Progress = gr.Progress(),
        ) -> Tuple[Any, ...]:
            """
            执行批量推理。
            
            Args:
                file_path: CSV 文件路径
                program_id: 程序 ID
                metadata: 程序元数据
                progress: Gradio 进度对象
                
            Returns:
                更新组件的元组
            """
            if not file_path or not program_id or not metadata:
                return (
                    gr.update(visible=True, value="❌ 缺少必要参数"),  # batch_progress
                    gr.update(visible=False),  # batch_results_table
                    gr.update(visible=False),  # export_row
                    None,  # batch_result_df
                )
            
            try:
                # 读取 CSV 文件
                df = pd.read_csv(file_path)
                total_rows = len(df)
                
                # 定义进度回调
                def progress_callback(current: int, total: int) -> None:
                    progress((current, total), desc=t("run.batch.processing").format(current=current, total=total))
                
                # 执行批量推理
                result_df = run_batch_inference(
                    program_id,
                    df,
                    progress_callback=progress_callback,
                )
                
                # 统计成功/失败数量
                success_count = len(result_df[result_df['_status'] == 'success'])
                error_count = total_rows - success_count
                
                status_msg = f"✅ {t('run.success.batch_complete').format(count=total_rows)}"
                if error_count > 0:
                    status_msg += f" ({error_count} 条失败)"
                
                return (
                    gr.update(visible=True, value=status_msg),  # batch_progress
                    gr.update(visible=True, value=result_df),  # batch_results_table
                    gr.update(visible=True),  # export_row
                    result_df,  # batch_result_df
                )
                
            except Exception as e:
                return (
                    gr.update(visible=True, value=f"❌ {t('run.errors.inference_failed').format(error=str(e))}"),  # batch_progress
                    gr.update(visible=False),  # batch_results_table
                    gr.update(visible=False),  # export_row
                    None,  # batch_result_df
                )
        
        def export_results(
            result_df: Optional[pd.DataFrame],
            program_id: Optional[str],
        ) -> Any:
            """
            导出批量推理结果为 CSV 文件。
            
            Args:
                result_df: 结果 DataFrame
                program_id: 程序 ID
                
            Returns:
                下载文件路径
            """
            if result_df is None or result_df.empty:
                return gr.update(visible=False)
            
            # 创建临时文件
            temp_dir = tempfile.gettempdir()
            safe_id = program_id.replace(":", "_").replace("/", "_") if program_id else "results"
            file_name = f"{safe_id}_batch_results.csv"
            file_path = os.path.join(temp_dir, file_name)
            
            # 保存 CSV
            result_df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            return gr.update(visible=True, value=file_path)
        
        # === 事件绑定 ===
        
        # 提取组件列表
        input_group_components = [g for g, t in input_fields]
        input_textbox_components = [t for g, t in input_fields]
        
        # 程序选择输出组件
        program_select_outputs = [
            current_program_id,
            current_metadata,
            program_info_group,
            input_section_group,
            output_section_group,
            signature_display,
            model_display,
            module_display,
            teacher_display,
            optimizer_display,
            eval_score_display,
            baseline_score_display,
            instructions_display,
            optimized_prompt_display,
        ]
        # 添加输入字段组件
        for g, tb in input_fields:
            program_select_outputs.append(g)
            program_select_outputs.append(tb)
        
        # 刷新按钮
        refresh_btn.click(
            refresh_program_list,
            outputs=[program_dropdown],
        )
        
        # 程序选择 - 需要更新函数以处理批量区域和历史记录区域
        def on_program_select_with_batch(
            selection: Optional[str],
            history: List[Dict[str, Any]],
        ) -> Tuple[Any, ...]:
            """
            当用户选择程序时加载元数据并更新 UI（包括批量区域和历史记录区域）。
            """
            base_result = on_program_select(selection)
            
            # 添加批量区域和历史记录区域的更新
            if selection:
                # 显示批量区域，重置为单条模式
                batch_updates = [
                    gr.update(visible=True),  # batch_section_group
                    "single",  # current_mode
                    gr.update(value=t("run.mode.switch_to_batch")),  # mode_toggle_btn
                    gr.update(visible=False),  # batch_upload_group
                ]
                
                # 历史记录区域更新
                if history:
                    choices = get_history_choices(history)
                    choice_labels = [c[0] for c in choices]
                    history_updates = [
                        gr.update(visible=True),  # history_section_group
                        gr.update(choices=choice_labels, value=None),  # history_list
                        gr.update(visible=False),  # history_empty_msg
                    ]
                else:
                    history_updates = [
                        gr.update(visible=True),  # history_section_group
                        gr.update(choices=[], value=None),  # history_list
                        gr.update(visible=True),  # history_empty_msg
                    ]
            else:
                batch_updates = [
                    gr.update(visible=False),  # batch_section_group
                    "single",  # current_mode
                    gr.update(value=t("run.mode.switch_to_batch")),  # mode_toggle_btn
                    gr.update(visible=False),  # batch_upload_group
                ]
                history_updates = [
                    gr.update(visible=False),  # history_section_group
                    gr.update(choices=[], value=None),  # history_list
                    gr.update(visible=True),  # history_empty_msg
                ]
            
            return base_result + tuple(batch_updates) + tuple(history_updates)
        
        # 更新程序选择输出组件列表
        program_select_outputs_with_batch = program_select_outputs + [
            batch_section_group,
            current_mode,
            mode_toggle_btn,
            batch_upload_group,
            history_section_group,
            history_list,
            history_empty_msg,
        ]
        
        program_dropdown.change(
            on_program_select_with_batch,
            inputs=[program_dropdown, inference_history],
            outputs=program_select_outputs_with_batch,
        )
        
        # 模式切换按钮
        mode_toggle_btn.click(
            toggle_mode,
            inputs=[current_mode, current_metadata],
            outputs=[
                current_mode,
                mode_toggle_btn,
                batch_upload_group,
                input_section_group,
                output_section_group,
                expected_headers_display,
                csv_validation_status,
                start_batch_btn,
                csv_upload,
                batch_results_table,
                export_row,
                batch_progress,
            ],
        )
        
        # CSV 上传验证
        csv_upload.change(
            on_csv_upload,
            inputs=[csv_upload, current_metadata],
            outputs=[csv_validation_status, start_batch_btn],
        )
        
        # 开始批量推理
        start_batch_btn.click(
            run_batch,
            inputs=[csv_upload, current_program_id, current_metadata],
            outputs=[batch_progress, batch_results_table, export_row, batch_result_df],
        )
        
        # 导出结果
        export_btn.click(
            export_results,
            inputs=[batch_result_df, current_program_id],
            outputs=[download_file],
        )
        
        # 运行按钮 - 先显示加载指示器，然后执行推理
        def show_loading():
            """显示加载指示器"""
            return gr.update(visible=True), gr.update(interactive=False)
        
        run_btn.click(
            show_loading,
            outputs=[loading_indicator, run_btn],
        ).then(
            run_inference,
            inputs=[current_program_id, current_metadata, inference_history] + input_textbox_components,
            outputs=[
                output_display,
                error_display,
                loading_indicator,
                inference_history,
                history_list,
                history_empty_msg,
                history_section_group,
            ],
        ).then(
            lambda: gr.update(interactive=True),
            outputs=[run_btn],
        )
        
        # 清空按钮
        clear_outputs = [output_display, error_display, loading_indicator] + input_textbox_components
        clear_btn.click(
            clear_inputs,
            outputs=clear_outputs,
        )
        
        # 历史记录选择 - 回填输入
        history_list.change(
            on_history_select,
            inputs=[history_list, inference_history, current_metadata],
            outputs=input_textbox_components,
        )
        
        # 清空历史按钮
        clear_history_btn.click(
            on_clear_history,
            outputs=[inference_history, history_list, history_empty_msg],
        )
        
        # 页面加载时刷新程序列表
        program_dropdown.render = lambda: refresh_program_list()
