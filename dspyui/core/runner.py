"""
DSPy 程序运行器

INPUT:  human_readable_id, row_data
OUTPUT: generate_program_response() 函数，返回程序执行结果
POS:    核心模块，用于加载并执行已编译的程序

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import os
import json
from typing import Dict, Any

from dspyui.core.signatures import create_custom_signature
from dspyui.core.modules import create_dspy_module


def generate_program_response(
    human_readable_id: str,
    row_data: Dict[str, Any]
) -> str:
    """
    使用编译好的程序生成响应。

    加载指定 ID 的编译程序，并使用提供的数据执行它。

    Args:
        human_readable_id: 程序的人类可读 ID
        row_data: 输入数据字典

    Returns:
        格式化的输入输出结果字符串

    Raises:
        ValueError: 当程序文件未找到时
    """
    # 加载程序详情
    program_path = f"programs/{human_readable_id}.json"
    prompt_path = f"prompts/{human_readable_id}.json"

    print("program_path:", program_path)
    
    if not os.path.exists(program_path):
        raise ValueError(f"Compiled program not found: {program_path}")

    with open(prompt_path, 'r') as f:
        program_details = json.load(f)
    
    # 提取必要信息
    input_fields = program_details.get('input_fields', [])
    input_descs = program_details.get('input_descs', [])    
    output_fields = program_details.get('output_fields', [])
    output_descs = program_details.get('output_descs', [])
    dspy_module = program_details.get('dspy_module', 'Predict')
    instructions = program_details.get('instructions', '')

    print("input_fields:", input_fields)
    print("output_fields:", output_fields)
    print("instructions:", instructions)
    print("input_descs:", input_descs)
    print("output_descs:", output_descs)
    print("dspy_module:", dspy_module)

    # 创建自定义签名
    CustomSignature = create_custom_signature(
        input_fields, output_fields, instructions, input_descs, output_descs
    )
    print("CustomSignature:", CustomSignature)
    
    # 创建并加载程序
    compiled_program = create_dspy_module(dspy_module, CustomSignature)
    print("compiled_program:", compiled_program)
    compiled_program.load(program_path)
    print("compiled_program after load:", compiled_program)

    # 准备输入
    program_input: Dict[str, Any] = {}
    for field in input_fields:
        if field in row_data:
            program_input[field] = row_data[field]
        else:
            print(f"Warning: Required input field '{field}' not found in row_data")
            program_input[field] = ""

    # 执行程序
    try:
        result = compiled_program(**program_input)
        print("result:", result)
    except Exception as e:
        print(f"Error executing program: {str(e)}")
        return f"Error: {str(e)}"

    # 格式化输出
    output = "Input:\n"
    for field in input_fields:
        output += f"{field}: {program_input[field]}\n"

    print("result:", result)

    output += "\nOutput:\n"
    for field in output_fields:
        output += f"{field}: {getattr(result, field)}\n"

    print("output:", output)

    return output
