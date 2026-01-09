"""
DSPy 程序编译器

INPUT:  input_fields, output_fields, dspy_module, llm_model, teacher_model, example_data, optimizer, instructions, metric_type, ...
        mlflow_tracking 模块提供的追踪函数
OUTPUT: compile_program() 函数，返回编译结果和优化后的提示词
POS:    核心编译模块，是整个系统的核心功能，集成 MLflow 追踪

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple

import dspy
import pandas as pd
from dspy.evaluate import Evaluate
from dspy.teleprompt import (
    BootstrapFewShot,
    BootstrapFewShotWithRandomSearch,
    MIPROv2,
    COPRO,
)

from autodspy.config import get_config
from autodspy.dspy_core.signatures import create_custom_signature
from autodspy.dspy_core.modules import create_dspy_module
from autodspy.dspy_core.metrics import create_metric
from autodspy.dspy_core.utils import generate_human_readable_id
from autodspy.mlflow.tracking import (
    init_mlflow,
    track_compilation,
    log_compilation_metrics,
    log_compilation_artifacts,
    log_dspy_model,
    log_evaluation_table,
    compute_dataset_hash,
    log_dataset_metadata,
    get_mlflow_ui_url,
    truncate_param,
)


def _create_lm(model: str) -> dspy.LM:
    """
    创建 DSPy LM 实例。

    Args:
        model: 模型名称

    Returns:
        配置好的 LM 实例

    Raises:
        ValueError: 当模型不支持时
    """
    config = get_config()
    
    if model.startswith("gpt-"):
        return dspy.LM(f'openai/{model}', api_base=os.environ.get("OPENAI_API_BASE"), cache=config.cache_enabled)
    elif model.startswith("claude-"):
        return dspy.LM(f'anthropic/{model}', cache=config.cache_enabled)
    elif model in config.supported_groq_models:
        return dspy.LM(f'groq/{model}', api_key=os.environ.get("GROQ_API_KEY"), cache=config.cache_enabled)
    elif model in config.supported_google_models:
        return dspy.LM(f'google/{model}', api_key=os.environ.get("GOOGLE_API_KEY"), cache=config.cache_enabled)
    elif model in config.supported_deepseek_models:
        return dspy.LM(
            f'openai/{model}',
            api_key=os.environ.get("DEEPSEEK_API_KEY"),
            api_base=os.environ.get("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1"),
            cache=config.cache_enabled
        )
    else:
        raise ValueError(f"Unsupported LLM model: {model}")


def compile_program(
    input_fields: List[str],
    output_fields: List[str],
    dspy_module: str,
    llm_model: str,
    teacher_model: str,
    example_data: pd.DataFrame,
    optimizer: str,
    instructions: str,
    metric_type: str,
    judge_prompt_id: Optional[str] = None,
    input_descs: Optional[List[str]] = None,
    output_descs: Optional[List[str]] = None,
    hint: Optional[str] = None
) -> Tuple[str, str, Optional[str], Dict[str, Any]]:
    """
    编译 DSPy 程序。

    根据提供的配置和示例数据，优化并编译 DSPy 程序。
    集成 MLflow 追踪，记录编译参数、指标和工件。

    Args:
        input_fields: 输入字段列表
        output_fields: 输出字段列表
        dspy_module: DSPy 模块类型
        llm_model: 使用的 LLM 模型
        teacher_model: 教师模型
        example_data: 示例数据 DataFrame
        optimizer: 优化器类型
        instructions: 程序指令
        metric_type: 评估指标类型
        judge_prompt_id: 评判提示词 ID (LLM-as-a-Judge 时需要)
        input_descs: 输入字段描述列表
        output_descs: 输出字段描述列表
        hint: 提示信息 (ChainOfThoughtWithHint 时需要)

    Returns:
        (usage_instructions, final_prompt, run_id) 元组，其中 run_id 为 MLflow Run ID（如果启用）

    Raises:
        ValueError: 当参数无效或示例数据不足时
    """
    # 初始化变量
    final_prompt = ""
    
    # 初始化 MLflow（如果启用）
    init_mlflow()
    
    # 设置 LLM 模型
    lm = _create_lm(llm_model)
    teacher_lm = _create_lm(teacher_model)

    # 创建自定义签名
    CustomSignature = create_custom_signature(
        input_fields, output_fields, instructions,
        input_descs or [], output_descs or []
    )

    # 创建 DSPy 模块
    module = create_dspy_module(dspy_module, CustomSignature, hint)

    # 转换 DataFrame 为字典列表
    example_data_list = example_data.to_dict('records')

    # 检查示例数据数量
    if len(example_data_list) < 2:
        raise ValueError("At least two examples are required for compilation.")

    # 创建数据集
    dataset = [
        dspy.Example(
            **{input_fields[i]: example[input_fields[i]] for i in range(len(input_fields))},
            **{output_fields[i]: str(example[output_fields[i]]) for i in range(len(output_fields))}
        ).with_inputs(*input_fields)
        for example in example_data_list
    ]

    # 拆分数据集
    split_index = int(0.8 * len(dataset))
    trainset, devset = dataset[:split_index], dataset[split_index:]

    # 获取配置
    config = get_config()
    
    # 创建评估指标（默认使用 zero-shot 评判程序，避免需要预先训练）
    metric = create_metric(metric_type, output_fields, judge_prompt_id, use_compiled_judge=False)
    
    # 评估参数 (num_threads 从配置读取)
    kwargs = dict(num_threads=config.num_threads, display_progress=True, display_table=1)

    # 生成人类可读的 ID（提前生成，用于 MLflow run_name）
    human_readable_id = generate_human_readable_id(
        input_fields, output_fields, dspy_module,
        llm_model, teacher_model, optimizer, instructions
    )
    
    # 准备 MLflow 编译参数
    compile_params = {
        "input_fields": ",".join(input_fields),
        "output_fields": ",".join(output_fields),
        "dspy_module": dspy_module,
        "llm_model": llm_model,
        "teacher_model": teacher_model,
        "optimizer": optimizer,
        "metric_type": metric_type,
        "instructions": truncate_param(instructions),
        "dataset_hash": compute_dataset_hash(example_data),
        "dataset_rows": len(example_data),
        "dataset_columns": ",".join(example_data.columns.tolist()),
    }
    
    # 添加可选参数
    if judge_prompt_id:
        compile_params["judge_prompt_id"] = judge_prompt_id
    if hint:
        compile_params["hint"] = truncate_param(hint)
    
    # MLflow Run 名称
    run_name = f"{dspy_module}_{optimizer}_{llm_model}"
    
    # 使用 MLflow 追踪上下文管理器
    with track_compilation(run_name, compile_params) as mlflow_run:
        # 记录数据集元数据
        log_dataset_metadata(example_data, "training_data")
        
        # 使用 dspy.context() 进行线程安全的 LM 配置
        with dspy.context(lm=lm):
            # 建立基线评估
            baseline_evaluate = Evaluate(metric=metric, devset=devset, num_threads=config.num_threads)
            baseline_score = baseline_evaluate(module)

            # 设置优化器
            if optimizer == "BootstrapFewShot":
                teleprompter = BootstrapFewShot(
                    metric=metric,
                    max_bootstrapped_demos=config.bootstrap_max_bootstrapped_demos,
                    max_labeled_demos=config.bootstrap_max_labeled_demos,
                    teacher_settings=dict(lm=teacher_lm)
                )
                compiled_program = teleprompter.compile(module, trainset=trainset)
            elif optimizer == "BootstrapFewShotWithRandomSearch":
                teleprompter = BootstrapFewShotWithRandomSearch(
                    metric=metric,
                    max_bootstrapped_demos=config.bootstrap_max_bootstrapped_demos,
                    max_labeled_demos=config.bootstrap_max_labeled_demos,
                    teacher_settings=dict(lm=teacher_lm),
                    num_threads=config.num_threads
                )
                compiled_program = teleprompter.compile(module, trainset=trainset, valset=devset)
            elif optimizer == "COPRO":
                teleprompter = COPRO(
                    metric=metric,
                    teacher_settings=dict(lm=teacher_lm)
                )
                compiled_program = teleprompter.compile(module, trainset=trainset, eval_kwargs=kwargs)
            elif optimizer == "MIPROv2":
                teleprompter = MIPROv2(
                    metric=metric,
                    prompt_model=lm,
                    task_model=teacher_lm,
                    num_candidates=config.mipro_num_candidates,
                    init_temperature=config.mipro_init_temperature
                )
                compiled_program = teleprompter.compile(
                    module,
                    trainset=trainset,
                    valset=devset,
                    num_batches=config.mipro_num_batches,
                    max_bootstrapped_demos=config.mipro_max_bootstrapped_demos,
                    max_labeled_demos=config.mipro_max_labeled_demos,
                    eval_kwargs=kwargs,
                    requires_permission_to_run=False
                )
            else:
                raise ValueError(f"Unsupported optimizer: {optimizer}")

            # 评估编译后的程序
            evaluate = Evaluate(metric=metric, devset=devset, num_threads=config.num_threads)
            score_result = evaluate(compiled_program)

            # 提取数值分数 (兼容 EvaluationResult 对象和数值)
            if hasattr(score_result, 'score'):
                score = score_result.score
            else:
                score = float(score_result)
            
            # 同样处理 baseline_score
            if hasattr(baseline_score, 'score'):
                baseline_score_value = baseline_score.score
            else:
                baseline_score_value = float(baseline_score)

            print("Evaluation Score:")
            print(score)

            # 创建目录
            os.makedirs('datasets', exist_ok=True)
            os.makedirs('programs', exist_ok=True)
            os.makedirs('prompts', exist_ok=True)

            # 保存数据集
            dataset_path = os.path.join('datasets', f"{human_readable_id}.csv")
            example_data.to_csv(dataset_path, index=False)
            print(f"Dataset saved to {dataset_path}")

            # 保存编译后的程序
            program_path = f"programs/{human_readable_id}.json"
            compiled_program.save(program_path)
            print(f"Compiled program saved to {program_path}")

            # 保存提示词详情
            prompt_path = f"prompts/{human_readable_id}.json"
            prompt_details = {
                "input_fields": input_fields,
                "input_descriptions": input_descs or [],
                "output_fields": output_fields,
                "output_descriptions": output_descs or [],
                "dspy_module": dspy_module,
                "llm_model": llm_model,
                "teacher_model": teacher_model,
                "optimizer": optimizer,
                "instructions": instructions,
                "signature": f"{', '.join(input_fields)} -> {', '.join(output_fields)}",
                "evaluation_score": score,
                "baseline_score": baseline_score_value,
                "optimized_prompt": final_prompt,
                "human_readable_id": human_readable_id,
                "mlflow_run_id": mlflow_run.info.run_id if mlflow_run else None
            }
            with open(prompt_path, 'w', encoding='utf-8') as f:
                json.dump(prompt_details, f, indent=4)
            print(f"Prompt details saved to {prompt_path}")

            # 记录 MLflow 编译指标
            log_compilation_metrics(
                baseline_score=baseline_score_value,
                evaluation_score=score,
                trainset_size=len(trainset),
                devset_size=len(devset)
            )
            
            # 记录 MLflow 编译工件
            log_compilation_artifacts(
                program_path=program_path,
                prompt_path=prompt_path,
                dataset_path=dataset_path
            )
            
            # 记录 DSPy 模型（用于 Model Registry）
            log_dspy_model(
                compiled_program=compiled_program,
                artifact_path="program"
            )
            
            # 记录详细评估结果（如果可用）
            if hasattr(score_result, 'results') and score_result.results:
                # 将评估结果转换为标准格式
                eval_results = []
                for idx, result in enumerate(score_result.results):
                    # 初始化记录
                    eval_record = {"example_id": idx}
                    
                    # 灵活处理各种结果格式 (dict, tuple, list, scalar)
                    if isinstance(result, dict):
                        eval_record["score"] = float(result.get('score', 0))
                        if 'example' in result: eval_record["input"] = str(result['example'])
                        if 'prediction' in result: eval_record["actual_output"] = str(result['prediction'])
                        if 'expected' in result: eval_record["expected_output"] = str(result['expected'])
                    elif isinstance(result, (tuple, list)):
                        # 处理常见元组格式: (example, prediction, score) 或 (score,)
                        if len(result) >= 3:
                            eval_record["input"] = str(result[0])
                            eval_record["actual_output"] = str(result[1])
                            eval_record["score"] = float(result[2])
                        elif len(result) >= 1:
                            eval_record["score"] = float(result[-1])
                    else:
                        # 标量分数
                        eval_record["score"] = float(result)
                        
                    eval_results.append(eval_record)
                
                log_evaluation_table(
                    eval_results=eval_results,
                    artifact_name="eval_results.json",
                    metric_name=metric_type,
                    metric_config={"judge_prompt_id": judge_prompt_id} if judge_prompt_id else None
                )

            # 生成使用说明
            usage_instructions = f"""Program compiled successfully!
Evaluation score: {score}
Baseline score: {baseline_score_value}
The compiled program has been saved as 'programs/{human_readable_id}.json'.
You can now use the compiled program as follows:

compiled_program = dspy.{dspy_module}(CustomSignature)
compiled_program.load('programs/{human_readable_id}.json')
result = compiled_program({', '.join(f'{field}=value' for field in input_fields)})
print({', '.join(f'result.{field}' for field in output_fields)})
"""

            if dspy_module == "ChainOfThoughtWithHint":
                usage_instructions += f"\nHint: {hint}\n"
            
            # 添加 MLflow UI 链接（如果有活跃的 Run）
            if mlflow_run:
                mlflow_ui_url = get_mlflow_ui_url(run_id=mlflow_run.info.run_id)
                usage_instructions += f"\nMLflow Run: {mlflow_ui_url}\n"

            # 初始化 final_prompt
            final_prompt = ""
            
            # 使用第一行数据测试编译后的程序
            if len(example_data) > 0:
                first_row = example_data.iloc[0]
                input_data = {field: first_row[field] for field in input_fields}
                result = compiled_program(**input_data)
                
                # 安全地获取 LLM 历史记录
                if hasattr(dspy.settings, 'lm') and hasattr(dspy.settings.lm, 'history') and dspy.settings.lm.history:
                    messages = dspy.settings.lm.history[-1].get('messages', [])
                    for msg in messages:
                        if isinstance(msg, dict) and 'content' in msg:
                            final_prompt += f"{msg['content']}\n"

                example_output = f"\nExample usage with first row of data:\n"
                example_output += f"Input: {input_data}\n"
                example_output += f"Output: {result}\n"
                usage_instructions += example_output

    return usage_instructions, final_prompt, (mlflow_run.info.run_id if mlflow_run else None), prompt_details
