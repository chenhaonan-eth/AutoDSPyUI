"""
DSPy 程序运行器

INPUT:  human_readable_id, row_data, DataFrame, prompts/*.json, programs/*.json
OUTPUT: generate_program_response(), load_program_metadata(), run_batch_inference(), validate_csv_headers() 函数
POS:    核心模块，用于加载并执行已编译的程序，支持单条和批量推理

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import os
import json
from typing import Dict, Any, List, Tuple, Optional, Callable

import pandas as pd

from dspyui.core.signatures import create_custom_signature
from dspyui.core.modules import create_dspy_module


def load_program_metadata(human_readable_id: str) -> Dict[str, Any]:
    """
    加载程序的元数据信息。
    
    Args:
        human_readable_id: 程序的人类可读 ID
        
    Returns:
        包含程序配置的字典：
        - input_fields: List[str] - 输入字段列表
        - input_descs: List[str] - 输入字段描述列表
        - output_fields: List[str] - 输出字段列表
        - output_descs: List[str] - 输出字段描述列表
        - dspy_module: str - DSPy 模块类型
        - llm_model: str - 使用的 LLM 模型
        - teacher_model: str - 教师模型
        - optimizer: str - 优化器类型
        - instructions: str - 任务指令
        - signature: str - 签名 (input -> output 格式)
        - evaluation_score: float - 评估分数
        - baseline_score: float - 基线分数
        - optimized_prompt: str - 优化后的提示词
        
    Raises:
        ValueError: 当程序文件未找到时
    """
    prompt_path = f"prompts/{human_readable_id}.json"
    program_path = f"programs/{human_readable_id}.json"
    
    # 检查文件是否存在
    if not os.path.exists(prompt_path):
        raise ValueError(f"程序配置文件未找到: {prompt_path}")
    
    if not os.path.exists(program_path):
        raise ValueError(f"程序文件未找到: {program_path}")
    
    # 加载元数据
    with open(prompt_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 构建返回字典，确保所有必需字段都存在
    metadata: Dict[str, Any] = {
        'input_fields': data.get('input_fields', []),
        'input_descs': data.get('input_descriptions', data.get('input_descs', [])),
        'output_fields': data.get('output_fields', []),
        'output_descs': data.get('output_descriptions', data.get('output_descs', [])),
        'dspy_module': data.get('dspy_module', 'Predict'),
        'llm_model': data.get('llm_model', 'N/A'),
        'teacher_model': data.get('teacher_model', 'N/A'),
        'optimizer': data.get('optimizer', 'N/A'),
        'instructions': data.get('instructions', ''),
        'signature': data.get('signature', ''),
        'evaluation_score': data.get('evaluation_score', 0.0),
        'baseline_score': data.get('baseline_score', 0.0),
        'optimized_prompt': data.get('optimized_prompt', ''),
        'human_readable_id': data.get('human_readable_id', human_readable_id),
    }
    
    # 如果没有 signature 字段，从 input_fields 和 output_fields 构建
    if not metadata['signature']:
        input_fields = metadata['input_fields']
        output_fields = metadata['output_fields']
        metadata['signature'] = f"{', '.join(input_fields)} -> {', '.join(output_fields)}"
    
    return metadata


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


def validate_csv_headers(
    csv_headers: List[str],
    input_fields: List[str]
) -> Tuple[bool, str]:
    """
    验证 CSV 头部是否包含所有必需的输入字段。
    
    Args:
        csv_headers: CSV 文件的列名列表
        input_fields: 程序要求的输入字段列表
        
    Returns:
        Tuple[bool, str]: (验证是否通过, 错误信息或成功信息)
        - 如果验证通过，返回 (True, "验证通过")
        - 如果验证失败，返回 (False, 错误信息)
        
    Requirements: 3.2, 3.3
    """
    if not input_fields:
        return False, "程序未定义输入字段"
    
    csv_headers_set = set(csv_headers)
    input_fields_set = set(input_fields)
    
    # 检查 CSV headers 是否包含所有 input_fields (顺序无关)
    missing_fields = input_fields_set - csv_headers_set
    
    if missing_fields:
        missing_str = ", ".join(sorted(missing_fields))
        expected_str = ", ".join(input_fields)
        return False, f"CSV 缺少必需字段: {missing_str}。期望字段: {expected_str}"
    
    return True, "验证通过"


def run_batch_inference(
    human_readable_id: str,
    data: pd.DataFrame,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> pd.DataFrame:
    """
    批量执行推理。
    
    逐行处理 DataFrame 中的数据，调用 generate_program_response() 执行推理，
    并将结果合并到输出 DataFrame 中。
    
    Args:
        human_readable_id: 程序的人类可读 ID
        data: 包含输入数据的 DataFrame，列名应与程序的 input_fields 匹配
        progress_callback: 可选的进度回调函数，接收 (current, total) 参数
        
    Returns:
        包含输入和输出列的 DataFrame，额外包含 _status 列表示处理状态
        - _status: "success" 表示成功，"error" 表示失败
        - 输出字段: 成功时包含推理结果，失败时为空字符串
        
    Raises:
        ValueError: 当程序文件未找到或 CSV 头部验证失败时
        
    Requirements: 3.4, 3.5
    """
    # 加载程序元数据以获取输入输出字段定义
    metadata = load_program_metadata(human_readable_id)
    input_fields = metadata['input_fields']
    output_fields = metadata['output_fields']
    
    # 验证 CSV 头部
    csv_headers = list(data.columns)
    is_valid, error_msg = validate_csv_headers(csv_headers, input_fields)
    if not is_valid:
        raise ValueError(error_msg)
    
    total_rows = len(data)
    results: List[Dict[str, Any]] = []
    
    for idx, row in data.iterrows():
        # 调用进度回调
        if progress_callback:
            progress_callback(idx + 1, total_rows)
        
        # 准备输入数据
        row_data = {field: row[field] for field in input_fields}
        
        # 初始化结果行，包含所有输入字段
        result_row: Dict[str, Any] = row_data.copy()
        
        try:
            # 执行推理
            response = generate_program_response(human_readable_id, row_data)
            
            # 解析输出 - generate_program_response 返回格式化字符串
            # 需要从中提取输出字段的值
            output_values = _parse_response_output(response, output_fields)
            
            for field in output_fields:
                result_row[field] = output_values.get(field, "")
            
            result_row['_status'] = 'success'
            
        except Exception as e:
            # 错误处理：设置空输出和错误状态
            for field in output_fields:
                result_row[field] = ""
            result_row['_status'] = f'error: {str(e)}'
        
        results.append(result_row)
    
    # 构建结果 DataFrame
    result_df = pd.DataFrame(results)
    
    # 确保列顺序：输入字段 -> 输出字段 -> _status
    column_order = input_fields + output_fields + ['_status']
    result_df = result_df[column_order]
    
    return result_df


def _parse_response_output(response: str, output_fields: List[str]) -> Dict[str, str]:
    """
    从 generate_program_response 的格式化输出中解析输出字段值。
    
    Args:
        response: generate_program_response 返回的格式化字符串
        output_fields: 输出字段列表
        
    Returns:
        输出字段名到值的映射字典
    """
    result: Dict[str, str] = {}
    
    # 查找 "Output:" 部分
    if "Output:" not in response:
        return result
    
    output_section = response.split("Output:")[-1].strip()
    
    # 解析每个字段
    for line in output_section.split("\n"):
        line = line.strip()
        if not line:
            continue
        
        # 格式: "field_name: value"
        if ":" in line:
            field_name, value = line.split(":", 1)
            field_name = field_name.strip()
            value = value.strip()
            
            if field_name in output_fields:
                result[field_name] = value
    
    return result
