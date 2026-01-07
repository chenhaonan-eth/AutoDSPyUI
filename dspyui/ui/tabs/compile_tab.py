"""
Compile Program Tab

INPUT:  dspyui.core.compiler, dspyui.utils.file_ops, gradio, pandas
OUTPUT: create_compile_tab() 函数
POS:    主功能 Tab，提供 DSPy 程序编译界面

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import os
import json
import random
from typing import List, Tuple, Any, Dict, Optional

import gradio as gr
import pandas as pd

from dspyui.core.compiler import compile_program
from dspyui.core.runner import generate_program_response
from dspyui.utils.file_ops import list_prompts, export_to_csv
from dspyui.ui.components import add_field, remove_last_field, load_csv
from dspyui.config import LLM_OPTIONS, MLFLOW_ENABLED
from dspyui.core.mlflow_tracking import get_mlflow_ui_url
from dspyui.i18n import t


# 最大输入/输出字段数量
MAX_FIELDS = 5

# 示例评判提示词签名（用于 LLM-as-a-Judge）
EXAMPLE_JUDGE_SIGNATURE = "JokeTopic:Funny-Gpt4oMini_ChainOfThought_Bootstrapfewshotwithrandomsearch-20241003.json - joke, topic -> funny (Score: 100)"


def create_compile_tab() -> None:
    """创建 Compile Program Tab。使用固定组件槽位避免 @gr.render 的 KeyError 问题。"""
    with gr.TabItem(t("compile.tab_title")):

        # === 1. 标题和示例按钮 ===
        with gr.Row():
            with gr.Column():
                gr.Markdown(f"# {t('compile.title')}")
                gr.Markdown(t("compile.subtitle"))

            with gr.Column():
                gr.Markdown(f"### {t('compile.examples.title')}")
                with gr.Row():  
                    example1 = gr.Button(t("compile.examples.judging_jokes"))
                    example2 = gr.Button(t("compile.examples.telling_jokes"))
                    example3 = gr.Button(t("compile.examples.rewriting_jokes"))
        
        # === 2. 任务指令 ===
        with gr.Row():
            with gr.Column(scale=4):
                instructions = gr.Textbox(
                    label=t("compile.instructions.label"),
                    lines=3,
                    placeholder=t("compile.instructions.placeholder"),
                    info=t("compile.instructions.info"),
                    interactive=True
                )

        # === 3. 状态变量 ===
        input_count = gr.State(0)
        output_count = gr.State(0)
        file_data = gr.State(None)
        row_choice_options = gr.State([])
        prompt_details_state = gr.State({})  # 存储程序详情，用于模型注册
        
        # === 4. 输入/输出按钮 ===
        with gr.Row():
            with gr.Column():
                gr.Markdown(f"### {t('compile.inputs.title')}")
                gr.Markdown(t("compile.inputs.description"))
                with gr.Row():
                    add_input_btn = gr.Button(t("compile.inputs.add_button"))
                    remove_input_btn = gr.Button(t("compile.inputs.remove_button"), interactive=False)

            with gr.Column():
                gr.Markdown(f"### {t('compile.outputs.title')}")
                gr.Markdown(t("compile.outputs.description"))
                with gr.Row():  
                    add_output_btn = gr.Button(t("compile.outputs.add_button"))
                    remove_output_btn = gr.Button(t("compile.outputs.remove_button"), interactive=False)

        # === 5. 固定数量的输入/输出字段槽位 ===
        input_names = []
        input_descs = []
        output_names = []
        output_descs = []
        
        with gr.Row():
            with gr.Column():
                for i in range(MAX_FIELDS):
                    with gr.Group(visible=False) as input_group:
                        input_name = gr.Textbox(
                            placeholder=t("compile.inputs.placeholder_name").format(i=i+1),
                            show_label=False,
                            label=f"{t('compile.inputs.title')} {i+1} {t('compile.inputs.placeholder_name').split('{')[0]}",
                            info=t("compile.inputs.name_info"),
                            interactive=True,
                        )
                        input_desc = gr.Textbox(
                            placeholder=t("compile.inputs.placeholder_desc"),
                            show_label=False,
                            label=f"{t('compile.inputs.title')} {i+1} {t('compile.inputs.placeholder_desc').split('（')[0]}",
                            interactive=True,
                        )
                    input_names.append((input_group, input_name))
                    input_descs.append(input_desc)
                    
                input_placeholder = gr.Markdown(t("compile.inputs.placeholder_message"), elem_classes="red-text")
                
            with gr.Column():
                for i in range(MAX_FIELDS):
                    with gr.Group(visible=False) as output_group:
                        output_name = gr.Textbox(
                            placeholder=t("compile.outputs.placeholder_name").format(i=i+1),
                            show_label=False,
                            label=f"{t('compile.outputs.title')} {i+1} {t('compile.outputs.placeholder_name').split('{')[0]}",
                            info=t("compile.outputs.name_info"),
                            interactive=True,
                        )
                        output_desc = gr.Textbox(
                            placeholder=t("compile.outputs.placeholder_desc"),
                            show_label=False,
                            label=f"{t('compile.outputs.title')} {i+1} {t('compile.outputs.placeholder_desc').split('（')[0]}",
                            interactive=True,
                        )
                    output_names.append((output_group, output_name))
                    output_descs.append(output_desc)
                    
                output_placeholder = gr.Markdown(t("compile.outputs.placeholder_message"), elem_classes="red-text")

        # === 6. Data 区域 ===
        with gr.Column():
            gr.Markdown(f"### {t('compile.data.title')}")
            gr.Markdown(t("compile.data.description"))
            with gr.Row():
                enter_manually_btn = gr.Button(t("compile.data.enter_manually"), interactive=False)
                upload_csv_btn = gr.UploadButton(t("compile.data.upload_csv"), file_types=[".csv"], interactive=False)

            example_data = gr.Dataframe(
                interactive=True,
                row_count=1,
                visible=False,
                label=t("compile.data.example_data_label"),
            )
            export_csv_btn = gr.Button(t("compile.data.export_csv"), interactive=False)
            csv_download = gr.File(label=t("compile.data.download_csv"), visible=False)
            error_message = gr.Markdown()

        # === 7. Settings 区域 ===
        with gr.Column():
            gr.Markdown(f"### {t('compile.settings.title')}")
            with gr.Row():
                llm_model = gr.Dropdown(
                    LLM_OPTIONS,
                    label=t("compile.settings.model_label"),
                    value="gpt-4o-mini",
                    info=t("compile.settings.model_info"),
                    interactive=True
                )
                teacher_model = gr.Dropdown(
                    LLM_OPTIONS,
                    label=t("compile.settings.teacher_label"),
                    value="gpt-4o",
                    info=t("compile.settings.teacher_info"),
                    interactive=True
                )
                with gr.Column():
                    dspy_module = gr.Dropdown(
                        ["Predict", "ChainOfThought", "ChainOfThoughtWithHint"],
                        label=t("compile.settings.module_label"),
                        value="Predict",
                        info=t("compile.settings.module_info"),
                        interactive=True
                    )
                    hint_textbox = gr.Textbox(
                        label=t("compile.settings.hint_label"),
                        lines=2,
                        placeholder=t("compile.settings.hint_placeholder"),
                        visible=False,
                        interactive=True
                    )

            with gr.Row():
                optimizer = gr.Dropdown(
                    ["BootstrapFewShot", "BootstrapFewShotWithRandomSearch", "MIPRO", "MIPROv2", "COPRO"],
                    label=t("compile.settings.optimizer_label"),
                    value="BootstrapFewShot",
                    info=t("compile.settings.optimizer_info"),
                    interactive=True
                )
                with gr.Column():
                    metric_type = gr.Radio(
                        [t("compile.metrics.exact_match"), t("compile.metrics.cosine_similarity"), t("compile.metrics.llm_as_judge")],
                        label=t("compile.settings.metric_label"),
                        value=t("compile.metrics.exact_match"),
                        info=t("compile.settings.metric_info"),
                        interactive=True
                    )
                    judge_prompt = gr.Dropdown(
                        choices=[],
                        label=t("compile.settings.judge_prompt_label"),
                        visible=False,
                        interactive=True
                    )

            compile_button = gr.Button(t("compile.buttons.compile"), visible=False, variant="primary")

        # === 8. Results 区域 ===
        with gr.Column():
            gr.Markdown(f"### {t('compile.results.title')}")
            with gr.Row():
                signature = gr.Textbox(label=t("compile.results.signature_label"), interactive=False)
                evaluation_score = gr.Number(label=t("compile.results.evaluation_score_label"), interactive=False)
                baseline_score = gr.Number(label=t("compile.results.baseline_score_label"), interactive=False)
            
            # MLflow UI 链接区域
            with gr.Row(visible=False) as mlflow_links_row:
                mlflow_experiment_btn = gr.Button(
                    t("compile.mlflow.view_experiment"), 
                    variant="secondary",
                    size="sm"
                )
                mlflow_run_btn = gr.Button(
                    t("compile.mlflow.view_run"), 
                    variant="secondary", 
                    size="sm",
                    visible=False
                )
                current_run_id = gr.State(None)
            
            optimized_prompt = gr.Textbox(
                label=t("compile.results.optimized_prompt_label"), 
                interactive=False, 
                lines=15,
                max_lines=30
            )

            # MLflow 模型注册区域
            if MLFLOW_ENABLED:
                with gr.Row(visible=False) as mlflow_register_row:
                    with gr.Column(scale=3):
                        model_name_input = gr.Textbox(
                            label=t("compile.mlflow.model_name_label"),
                            placeholder=t("compile.mlflow.model_name_placeholder"),
                            interactive=True
                        )
                    with gr.Column(scale=1):
                        register_model_btn = gr.Button(
                            t("compile.mlflow.register_model"),
                            variant="primary",
                            size="sm"
                        )
                
                register_status = gr.Markdown(visible=False)

        # === 9. 测试区域 ===
        with gr.Row():
            with gr.Column(scale=1):
                human_readable_id = gr.Textbox(interactive=False, visible=False)
                row_selector = gr.Dropdown(
                    choices=[],
                    label=t("compile.results.select_row_label"),
                    interactive=True,
                    visible=False,
                )
                random_row_button = gr.Button(t("compile.buttons.select_random_row"), visible=False)
                generate_button = gr.Button(t("compile.buttons.generate"), visible=False, variant="primary")

            with gr.Column(scale=2):
                generate_output = gr.Textbox(label=t("compile.results.generated_response_label"), interactive=False, lines=10, visible=False)

        # === 事件处理函数 ===
        def add_input_field(count):
            if count >= MAX_FIELDS:
                return count, gr.update(), gr.update()
            new_count = count + 1
            updates = []
            for i in range(MAX_FIELDS):
                updates.append(gr.update(visible=i < new_count))
            return (new_count, gr.update(interactive=new_count > 0), 
                    gr.update(visible=new_count == 0), *updates)
        
        def remove_input_field(count):
            if count <= 0:
                return count, gr.update(), gr.update()
            new_count = count - 1
            updates = []
            for i in range(MAX_FIELDS):
                updates.append(gr.update(visible=i < new_count))
            return (new_count, gr.update(interactive=new_count > 0),
                    gr.update(visible=new_count == 0), *updates)
        
        def add_output_field(count):
            if count >= MAX_FIELDS:
                return count, gr.update(), gr.update()
            new_count = count + 1
            updates = []
            for i in range(MAX_FIELDS):
                updates.append(gr.update(visible=i < new_count))
            return (new_count, gr.update(interactive=new_count > 0),
                    gr.update(visible=new_count == 0), *updates)
        
        def remove_output_field(count):
            if count <= 0:
                return count, gr.update(), gr.update()
            new_count = count - 1
            updates = []
            for i in range(MAX_FIELDS):
                updates.append(gr.update(visible=i < new_count))
            return (new_count, gr.update(interactive=new_count > 0),
                    gr.update(visible=new_count == 0), *updates)

        def update_data_buttons(in_count, out_count, fdata):
            can_add = in_count > 0 and out_count > 0 and fdata is None
            return gr.update(interactive=can_add), gr.update(interactive=can_add)

        def show_dataframe(in_count, out_count, *field_values):
            # field_values: input_names (MAX_FIELDS) + input_descs (MAX_FIELDS) + output_names + output_descs
            input_name_vals = field_values[:MAX_FIELDS]
            output_name_vals = field_values[MAX_FIELDS*2:MAX_FIELDS*3]
            
            headers = []
            for i in range(in_count):
                name = input_name_vals[i] if input_name_vals[i] else f"Input{i+1}"
                headers.append(name)
            for i in range(out_count):
                name = output_name_vals[i] if output_name_vals[i] else f"Output{i+1}"
                headers.append(name)
            
            new_df = pd.DataFrame(columns=headers)
            return (gr.update(visible=True, value=new_df, headers=headers), 
                    gr.update(interactive=True), gr.update(visible=True),
                    gr.update(interactive=False), gr.update(interactive=False))

        def process_csv(file, in_count, out_count, *field_values):
            if file is None:
                return None, gr.update(), gr.update(), gr.update()
            try:
                df = pd.read_csv(file.name)
                input_name_vals = field_values[:MAX_FIELDS]
                output_name_vals = field_values[MAX_FIELDS*2:MAX_FIELDS*3]
                
                expected = []
                for i in range(in_count):
                    expected.append(input_name_vals[i] if input_name_vals[i] else f"Input{i+1}")
                for i in range(out_count):
                    expected.append(output_name_vals[i] if output_name_vals[i] else f"Output{i+1}")
                
                if list(df.columns) != expected:
                    return (None, gr.update(visible=False), gr.update(visible=False),
                            gr.update(visible=True, value=t("compile.errors.header_mismatch").format(expected=expected, actual=list(df.columns))))
                return (df, gr.update(visible=True, value=df), gr.update(visible=True),
                        gr.update(visible=False))
            except Exception as e:
                return None, gr.update(), gr.update(), gr.update(visible=True, value=t("compile.errors.general_error").format(error=str(e)))

        def update_compile_visibility(fdata, in_count, out_count):
            visible = fdata is not None and in_count > 0 and out_count > 0
            return gr.update(visible=visible)

        def compile_fn(in_count, out_count, fdata, llm, teacher, module, opt, instr, metric, judge, hint, *field_values):
            input_name_vals = field_values[:MAX_FIELDS]
            input_desc_vals = field_values[MAX_FIELDS:MAX_FIELDS*2]
            output_name_vals = field_values[MAX_FIELDS*2:MAX_FIELDS*3]
            output_desc_vals = field_values[MAX_FIELDS*3:]
            
            input_fields = [input_name_vals[i] or f"Input{i+1}" for i in range(in_count)]
            input_descs = [input_desc_vals[i] for i in range(in_count) if input_desc_vals[i]]
            output_fields = [output_name_vals[i] or f"Output{i+1}" for i in range(out_count)]
            output_descs = [output_desc_vals[i] for i in range(out_count) if output_desc_vals[i]]
            
            judge_id = None
            if metric == t("compile.metrics.llm_as_judge") and judge:
                judge_id = judge.split(' - ')[0]
            
            # 将翻译后的 metric 显示值转换回英文键
            metric_map = {
                t("compile.metrics.exact_match"): "Exact Match",
                t("compile.metrics.cosine_similarity"): "Cosine Similarity",
                t("compile.metrics.llm_as_judge"): "LLM-as-a-Judge",
            }
            metric_key = metric_map.get(metric, metric)
            
            hint_val = hint if module == "ChainOfThoughtWithHint" else None
            
            usage_result, opt_prompt, run_id, prompt_details = compile_program(
                input_fields, output_fields, module, llm, teacher,
                fdata, opt, instr, metric_key, judge_id, input_descs, output_descs, hint_val
            )
            
            sig = prompt_details["signature"]
            eval_score = prompt_details["evaluation_score"]
            base_score = prompt_details["baseline_score"]
            hr_id = prompt_details["human_readable_id"]
            
            row_opts = [f"Row {i+1}" for i in range(len(fdata))]
            
            return (sig, eval_score, opt_prompt, 
                    gr.update(choices=row_opts, visible=True, value="Row 1"),
                    gr.update(visible=True), row_opts, gr.update(visible=True),
                    gr.update(visible=True), hr_id, gr.update(visible=True), base_score,
                    gr.update(visible=MLFLOW_ENABLED), run_id, 
                    gr.update(visible=bool(run_id and MLFLOW_ENABLED)),
                    gr.update(visible=bool(run_id and MLFLOW_ENABLED)),  # mlflow_register_row
                    gr.update(value=f"{hr_id}-model"),                   # model_name_input
                    prompt_details)                                             # prompt_details_state

        def generate_response(hr_id, row_sel, df):
            row_idx = int(row_sel.split()[1]) - 1
            selected = df.iloc[row_idx].to_dict()
            return generate_program_response(hr_id, selected)

        def select_random_row(opts):
            if opts:
                return gr.update(value=random.choice(opts))
            return gr.update()

        def update_hint_visibility(module):
            return gr.update(visible=module == "ChainOfThoughtWithHint")

        def load_example(task_instr, inputs_data, outputs_data, csv_file):
            """加载示例数据"""
            in_count = len(inputs_data)
            out_count = len(outputs_data)
            
            # 准备输入字段更新
            input_updates = []
            input_desc_updates = []
            for i in range(MAX_FIELDS):
                if i < in_count:
                    input_updates.append(gr.update(visible=True))
                    input_updates.append(gr.update(value=inputs_data[i][0]))
                    input_desc_updates.append(gr.update(value=inputs_data[i][1] if len(inputs_data[i]) > 1 else ""))
                else:
                    input_updates.append(gr.update(visible=False))
                    input_updates.append(gr.update(value=""))
                    input_desc_updates.append(gr.update(value=""))
            
            # 准备输出字段更新
            output_updates = []
            output_desc_updates = []
            for i in range(MAX_FIELDS):
                if i < out_count:
                    output_updates.append(gr.update(visible=True))
                    output_updates.append(gr.update(value=outputs_data[i][0]))
                    output_desc_updates.append(gr.update(value=outputs_data[i][1] if len(outputs_data[i]) > 1 else ""))
                else:
                    output_updates.append(gr.update(visible=False))
                    output_updates.append(gr.update(value=""))
                    output_desc_updates.append(gr.update(value=""))
            
            df = load_csv(csv_file)
            
            return (
                gr.update(value=task_instr),  # instructions
                in_count,  # input_count
                out_count,  # output_count
                gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False),  # example buttons
                df,  # file_data
                gr.update(visible=in_count == 0),  # input_placeholder
                gr.update(visible=out_count == 0),  # output_placeholder
                gr.update(interactive=in_count > 0),  # remove_input_btn
                gr.update(interactive=out_count > 0),  # remove_output_btn
                gr.update(visible=True, value=df),  # example_data
                gr.update(visible=True),  # compile_button
                gr.update(interactive=False), gr.update(interactive=False),  # enter_manually, upload_csv
                gr.update(interactive=True),  # export_csv
                *input_updates,  # input groups and names
                *input_desc_updates,  # input descs
                *output_updates,  # output groups and names
                *output_desc_updates,  # output descs
            )

        # === 事件绑定 ===
        input_group_components = [g for g, n in input_names]
        input_name_components = [n for g, n in input_names]
        output_group_components = [g for g, n in output_names]
        output_name_components = [n for g, n in output_names]
        
        add_input_btn.click(
            add_input_field,
            inputs=[input_count],
            outputs=[input_count, remove_input_btn, input_placeholder] + input_group_components
        ).then(
            update_data_buttons,
            inputs=[input_count, output_count, file_data],
            outputs=[enter_manually_btn, upload_csv_btn]
        )
        
        remove_input_btn.click(
            remove_input_field,
            inputs=[input_count],
            outputs=[input_count, remove_input_btn, input_placeholder] + input_group_components
        ).then(
            update_data_buttons,
            inputs=[input_count, output_count, file_data],
            outputs=[enter_manually_btn, upload_csv_btn]
        )
        
        add_output_btn.click(
            add_output_field,
            inputs=[output_count],
            outputs=[output_count, remove_output_btn, output_placeholder] + output_group_components
        ).then(
            update_data_buttons,
            inputs=[input_count, output_count, file_data],
            outputs=[enter_manually_btn, upload_csv_btn]
        )
        
        remove_output_btn.click(
            remove_output_field,
            inputs=[output_count],
            outputs=[output_count, remove_output_btn, output_placeholder] + output_group_components
        ).then(
            update_data_buttons,
            inputs=[input_count, output_count, file_data],
            outputs=[enter_manually_btn, upload_csv_btn]
        )

        all_field_values = input_name_components + input_descs + output_name_components + output_descs
        
        enter_manually_btn.click(
            show_dataframe,
            inputs=[input_count, output_count] + all_field_values,
            outputs=[example_data, export_csv_btn, compile_button, enter_manually_btn, upload_csv_btn]
        ).then(
            lambda: pd.DataFrame(),
            outputs=[file_data]
        )
        
        upload_csv_btn.upload(
            process_csv,
            inputs=[upload_csv_btn, input_count, output_count] + all_field_values,
            outputs=[file_data, example_data, compile_button, error_message]
        ).then(
            lambda: (gr.update(interactive=False), gr.update(interactive=False)),
            outputs=[enter_manually_btn, upload_csv_btn]
        )
        
        export_csv_btn.click(
            export_to_csv,
            inputs=[example_data],
            outputs=[csv_download]
        ).then(
            lambda: gr.update(visible=True),
            outputs=[csv_download]
        )
        
        compile_button.click(
            compile_fn,
            inputs=[input_count, output_count, file_data, llm_model, teacher_model, 
                    dspy_module, optimizer, instructions, metric_type, judge_prompt, 
                    hint_textbox] + all_field_values,
            outputs=[signature, evaluation_score, optimized_prompt, row_selector,
                     random_row_button, row_choice_options, generate_button, 
                     generate_output, human_readable_id, human_readable_id, baseline_score,
                     mlflow_links_row, current_run_id, mlflow_run_btn,
                     mlflow_register_row, model_name_input, prompt_details_state]
        )
        
        generate_button.click(
            generate_response,
            inputs=[human_readable_id, row_selector, example_data],
            outputs=[generate_output]
        )
        
        random_row_button.click(
            select_random_row,
            inputs=[row_choice_options],
            outputs=[row_selector]
        )
        
        dspy_module.change(update_hint_visibility, inputs=[dspy_module], outputs=[hint_textbox])

        # MLflow UI 按钮事件
        def open_mlflow_experiment():
            """打开 MLflow 实验页面"""
            if MLFLOW_ENABLED:
                url = get_mlflow_ui_url()
                gr.Info(t("compile.mlflow.experiment_page_info").format(url=url))
                return url
            return ""
        
        def open_mlflow_run(run_id):
            """打开 MLflow Run 页面"""
            if MLFLOW_ENABLED and run_id:
                url = get_mlflow_ui_url(run_id=run_id)
                gr.Info(t("compile.mlflow.run_page_info").format(url=url))
                return url
            return ""
        
        # 添加隐藏的文本框来显示 URL
        mlflow_experiment_url = gr.Textbox(visible=False)
        mlflow_run_url = gr.Textbox(visible=False)
        
        mlflow_experiment_btn.click(
            open_mlflow_experiment,
            outputs=[mlflow_experiment_url]
        )
        
        mlflow_run_btn.click(
            open_mlflow_run,
            inputs=[current_run_id],
            outputs=[mlflow_run_url]
        )

        # MLflow 模型注册
        def on_register_model_click(model_name: str, run_id: str, prompt_details: Dict[str, Any]):
            """处理注册模型按钮点击事件"""
            from dspyui.core.mlflow_service import register_compiled_model
            
            # 调用业务逻辑层
            result = register_compiled_model(
                run_id=run_id,
                model_name=model_name,
                prompt_details=prompt_details
            )
            
            # 根据结果更新 UI
            if result.success:
                message = t("compile.mlflow.register_model_success").format(
                    version=result.version
                ) + f" [{t('compile.mlflow.view_model')}]({result.model_url})"
                return gr.update(visible=True, value=message)
            else:
                error_key = f"compile.mlflow.register_model_{result.error_code}"
                if result.error_code == "exception":
                    message = t("compile.mlflow.register_model_error").format(
                        error=result.error_message
                    )
                else:
                    message = t(error_key)
                return gr.update(visible=True, value=message)

        if MLFLOW_ENABLED:
            register_model_btn.click(
                on_register_model_click,
                inputs=[model_name_input, current_run_id, prompt_details_state],
                outputs=[register_status]
            )

        # metric_type 变化时更新 judge_prompt 下拉列表
        def update_judge_prompt_visibility(metric, in_count, out_count, *field_values):
            """当 metric_type 变为 LLM-as-a-Judge 时，显示并填充 judge_prompt 下拉列表"""
            if metric != t("compile.metrics.llm_as_judge"):
                # 隐藏时同时清空 value，避免残留值导致 choices 不匹配错误
                return gr.update(visible=False, choices=[], value=None)
            
            # 提取当前输入/输出字段名
            input_name_vals = field_values[:MAX_FIELDS]
            output_name_vals = field_values[MAX_FIELDS:]
            
            input_fields = [input_name_vals[i] or f"Input{i+1}" for i in range(in_count)]
            output_fields = [output_name_vals[i] or f"Output{i+1}" for i in range(out_count)]
            
            # 获取匹配的评判提示词
            prompts = list_prompts(output_filter=input_fields + output_fields)
            choices = [f"{p['ID']} - {p['Signature']} (Score: {p['Eval Score']})" for p in prompts]
            choices.append(EXAMPLE_JUDGE_SIGNATURE)
            
            # 确保 value 在 choices 中，避免 Gradio 报错
            default_value = EXAMPLE_JUDGE_SIGNATURE if EXAMPLE_JUDGE_SIGNATURE in choices else (choices[0] if choices else None)
            return gr.update(visible=True, choices=choices, value=default_value)

        metric_type.change(
            update_judge_prompt_visibility,
            inputs=[metric_type, input_count, output_count] + input_name_components + output_name_components,
            outputs=[judge_prompt]
        )

        # Example 按钮输出组件列表
        example_outputs = [
            instructions, input_count, output_count,
            example1, example2, example3, file_data,
            input_placeholder, output_placeholder,
            remove_input_btn, remove_output_btn,
            example_data, compile_button,
            enter_manually_btn, upload_csv_btn, export_csv_btn
        ]
        # 添加所有输入组和名称
        for g, n in input_names:
            example_outputs.extend([g, n])
        example_outputs.extend(input_descs)
        for g, n in output_names:
            example_outputs.extend([g, n])
        example_outputs.extend(output_descs)

        example1.click(
            lambda: load_example(
                t("compile.examples.judging_jokes_instruction"),
                [("joke", t("compile.examples.joke_desc")), ("topic", t("compile.examples.topic_desc"))],
                [("funny", t("compile.examples.funny_desc"))],
                "rating_jokes.csv"
            ),
            outputs=example_outputs
        )
        
        example2.click(
            lambda: load_example(
                t("compile.examples.telling_jokes_instruction"),
                [("topic", t("compile.examples.topic_desc"))],
                [("joke", t("compile.examples.joke_output_desc"))],
                "telling_jokes.csv"
            ),
            outputs=example_outputs
        )
        
        example3.click(
            lambda: load_example(
                t("compile.examples.rewriting_jokes_instruction"),
                [("joke", t("compile.examples.joke_input_desc")), ("comedian", t("compile.examples.comedian_desc"))],
                [("rewritten_joke", t("compile.examples.rewritten_joke_desc"))],
                "rewriting_jokes.csv"
            ),
            outputs=example_outputs
        )
