"""
ID 生成工具

INPUT:  input_fields, output_fields, dspy_module, llm_model, teacher_model, optimizer, instructions
OUTPUT: generate_human_readable_id() 函数
POS:    工具函数，被 compiler 模块调用生成程序唯一标识

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import datetime
from typing import List


def generate_human_readable_id(
    input_fields: List[str],
    output_fields: List[str],
    dspy_module: str,
    llm_model: str,
    teacher_model: str,
    optimizer: str,
    instructions: str
) -> str:
    """
    生成人类可读的程序 ID。

    基于输入/输出字段、模型、模块和优化器信息生成唯一标识符。

    Args:
        input_fields: 输入字段列表
        output_fields: 输出字段列表
        dspy_module: DSPy 模块类型 (Predict/ChainOfThought等)
        llm_model: 使用的 LLM 模型
        teacher_model: 教师模型
        optimizer: 优化器类型
        instructions: 程序指令

    Returns:
        格式为 "{Signature}-{Model}_{Module}_{Optimizer}-{Date}" 的唯一 ID
    """
    # 创建基于签名的名称
    signature = '_'.join(input_fields + [':'] + output_fields)
    signature_pascal = ''.join(word.capitalize() for word in signature.split('_'))
    
    # 组合相关信息
    model_name = ''.join(word.capitalize() for word in llm_model.split('-'))
    module_name = dspy_module
    optimizer_name = ''.join(
        word.capitalize() 
        for word in optimizer.replace('bootstrap', 'bs').replace('randomsearch', 'rs').split('_')
    )
    
    # 获取当前日期
    current_date = datetime.date.today().strftime("%Y%m%d")
    
    # 创建带日期的人类可读 ID
    unique_id = f"{signature_pascal}-{model_name}_{module_name}_{optimizer_name}-{current_date}"
    
    return unique_id
