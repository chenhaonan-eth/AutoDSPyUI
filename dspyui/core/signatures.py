"""
DSPy Signature 创建模块

INPUT:  input_fields, output_fields, instructions, input_descs, output_descs
OUTPUT: create_custom_signature() 函数，返回自定义 DSPy Signature 类
POS:    核心模块，被 compiler 和 runner 调用创建 Signature

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

from typing import List, Type

import dspy
from pydantic import create_model


def create_custom_signature(
    input_fields: List[str],
    output_fields: List[str],
    instructions: str,
    input_descs: List[str],
    output_descs: List[str]
) -> Type[dspy.Signature]:
    """
    创建自定义的 DSPy Signature。

    根据提供的输入/输出字段和描述，动态创建 Signature 类。

    Args:
        input_fields: 输入字段名称列表
        output_fields: 输出字段名称列表
        instructions: Signature 的指令/文档字符串
        input_descs: 输入字段描述列表
        output_descs: 输出字段描述列表

    Returns:
        动态创建的 Signature 类

    Example:
        >>> sig = create_custom_signature(
        ...     ["topic"], ["joke"],
        ...     "Generate a joke about the topic",
        ...     ["The topic to joke about"], ["The generated joke"]
        ... )
    """
    fields = {}
    
    # 创建输入字段
    for i, field in enumerate(input_fields):
        if i < len(input_descs) and input_descs[i]:
            fields[field] = (
                str,
                dspy.InputField(
                    default=...,
                    desc=input_descs[i],
                    json_schema_extra={"__dspy_field_type": "input"}
                )
            )
        else:
            fields[field] = (
                str,
                dspy.InputField(
                    default=...,
                    json_schema_extra={"__dspy_field_type": "input"}
                )
            )
    
    # 创建输出字段
    for i, field in enumerate(output_fields):
        if i < len(output_descs) and output_descs[i]:
            fields[field] = (
                str,
                dspy.OutputField(
                    default=...,
                    desc=output_descs[i],
                    json_schema_extra={"__dspy_field_type": "output"}
                )
            )
        else:
            fields[field] = (
                str,
                dspy.OutputField(
                    default=...,
                    json_schema_extra={"__dspy_field_type": "output"}
                )
            )
    
    # 使用 pydantic 创建模型
    CustomSignatureModel = create_model('CustomSignatureModel', **fields)
    
    class CustomSignature(dspy.Signature, CustomSignatureModel):
        """
        {instructions}
        """
    
    # 格式化 docstring
    CustomSignature.__doc__ = CustomSignature.__doc__.format(instructions=instructions)
    
    return CustomSignature
