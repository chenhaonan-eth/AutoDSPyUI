"""
DSPy 程序编译器

INPUT:  input_fields, output_fields, dspy_module, llm_model, teacher_model, example_data, optimizer, instructions, metric_type, ...
OUTPUT: compile_program() 函数，返回编译结果和优化后的提示词
POS:    核心编译模块，是整个系统的核心功能

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

from dspyui.config import SUPPORTED_GROQ_MODELS, SUPPORTED_GOOGLE_MODELS, DSPY_CACHE_ENABLED
from dspyui.core.signatures import create_custom_signature
from dspyui.core.modules import create_dspy_module
from dspyui.core.metrics import create_metric
from dspyui.utils.id_generator import generate_human_readable_id


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
    if model.startswith("gpt-"):
        return dspy.LM(f'openai/{model}', api_base=os.environ.get("OPENAI_API_BASE"), cache=DSPY_CACHE_ENABLED)
    elif model.startswith("claude-"):
        return dspy.LM(f'anthropic/{model}', cache=DSPY_CACHE_ENABLED)
    elif model in SUPPORTED_GROQ_MODELS:
        return dspy.LM(f'groq/{model}', api_key=os.environ.get("GROQ_API_KEY"), cache=DSPY_CACHE_ENABLED)
    elif model in SUPPORTED_GOOGLE_MODELS:
        return dspy.LM(f'google/{model}', api_key=os.environ.get("GOOGLE_API_KEY"), cache=DSPY_CACHE_ENABLED)
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
) -> Tuple[str, str]:
    """
    编译 DSPy 程序。

    根据提供的配置和示例数据，优化并编译 DSPy 程序。

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
        (usage_instructions, final_prompt) 元组

    Raises:
        ValueError: 当参数无效或示例数据不足时
    """
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

    # 创建评估指标
    metric = create_metric(metric_type, output_fields, judge_prompt_id)
    
    # 评估参数
    kwargs = dict(num_threads=1, display_progress=True, display_table=1)

    # 使用 dspy.context() 进行线程安全的 LM 配置
    with dspy.context(lm=lm):
        # 建立基线评估
        baseline_evaluate = Evaluate(metric=metric, devset=devset, num_threads=1)
        baseline_score = baseline_evaluate(module)

        # 设置优化器
        if optimizer == "BootstrapFewShot":
            teleprompter = BootstrapFewShot(
                metric=metric,
                teacher_settings=dict(lm=teacher_lm)
            )
            compiled_program = teleprompter.compile(module, trainset=trainset)
        elif optimizer == "BootstrapFewShotWithRandomSearch":
            teleprompter = BootstrapFewShotWithRandomSearch(
                metric=metric,
                teacher_settings=dict(lm=teacher_lm),
                num_threads=1
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
                num_candidates=10,
                init_temperature=1.0
            )
            compiled_program = teleprompter.compile(
                module,
                trainset=trainset,
                valset=devset,
                num_batches=30,
                max_bootstrapped_demos=8,
                max_labeled_demos=16,
                eval_kwargs=kwargs,
                requires_permission_to_run=False
            )
        else:
            raise ValueError(f"Unsupported optimizer: {optimizer}")

        # 评估编译后的程序
        evaluate = Evaluate(metric=metric, devset=devset, num_threads=1)
        score_result = evaluate(compiled_program)

        # 提取数值分数 (兼容 EvaluationResult 对象和数值)
        if hasattr(score_result, 'score'):
            score = score_result.score
        else:
            score = float(score_result)
        
        # 同样处理 baseline_score
        if hasattr(baseline_score, 'score'):
            baseline_score = baseline_score.score
        else:
            baseline_score = float(baseline_score)

        print("Evaluation Score:")
        print(score)

        # 生成人类可读的 ID
        human_readable_id = generate_human_readable_id(
            input_fields, output_fields, dspy_module,
            llm_model, teacher_model, optimizer, instructions
        )

        # 创建目录
        os.makedirs('datasets', exist_ok=True)
        os.makedirs('programs', exist_ok=True)

        # 保存数据集
        dataset_path = os.path.join('datasets', f"{human_readable_id}.csv")
        example_data.to_csv(dataset_path, index=False)
        print(f"Dataset saved to {dataset_path}")

        # 保存编译后的程序
        compiled_program.save(f"programs/{human_readable_id}.json")
        print(f"Compiled program saved to programs/{human_readable_id}.json")

        # 生成使用说明
        usage_instructions = f"""Program compiled successfully!
Evaluation score: {score}
Baseline score: {baseline_score}
The compiled program has been saved as 'programs/{human_readable_id}.json'.
You can now use the compiled program as follows:

compiled_program = dspy.{dspy_module}(CustomSignature)
compiled_program.load('programs/{human_readable_id}.json')
result = compiled_program({', '.join(f'{field}=value' for field in input_fields)})
print({', '.join(f'result.{field}' for field in output_fields)})
"""

        if dspy_module == "ChainOfThoughtWithHint":
            usage_instructions += f"\nHint: {hint}\n"

        # 使用第一行数据测试编译后的程序
        final_prompt = ""
        if len(example_data) > 0:
            first_row = example_data.iloc[0]
            input_data = {field: first_row[field] for field in input_fields}
            result = compiled_program(**input_data)
            messages = dspy.settings.lm.history[-1]['messages']
            for msg in messages:
                final_prompt += f"{msg['content']}\n"

            example_output = f"\nExample usage with first row of data:\n"
            example_output += f"Input: {input_data}\n"
            example_output += f"Output: {result}\n"
            usage_instructions += example_output

    return usage_instructions, final_prompt
