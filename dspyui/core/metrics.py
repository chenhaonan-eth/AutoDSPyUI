"""
评估指标模块

INPUT:  metric_type, output_fields, judge_prompt_id (可选)
OUTPUT: create_metric() 函数，返回评估指标函数
POS:    核心模块，被 compiler 调用创建评估指标

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import os
import json
from typing import List, Callable, Optional, Any

import numpy as np
import dspy
from openai import OpenAI

from dspyui.core.signatures import create_custom_signature
from dspyui.core.modules import create_dspy_module


def create_exact_match_metric(output_fields: List[str]) -> Callable:
    """
    创建精确匹配指标。

    Args:
        output_fields: 输出字段列表

    Returns:
        精确匹配评估函数
    """
    def metric(gold: Any, pred: Any, trace: Any = None) -> int:
        print("Gold:", gold)
        print("Pred:", pred)
        print("Pred type:", type(pred))
        print("Pred attributes:", dir(pred))
        
        if isinstance(pred, dspy.Prediction):
            print("Prediction fields:", pred.__dict__)
        
        # 检查 pred 是否为空或 None
        if not pred or (isinstance(pred, dspy.Prediction) and not pred.__dict__):
            print("Warning: Prediction is empty or None")
            return 0
        
        try:
            return int(all(gold[field] == getattr(pred, field) for field in output_fields))
        except AttributeError as e:
            print(f"AttributeError: {e}")
            return 0
    
    return metric


def create_cosine_similarity_metric(output_fields: List[str]) -> Callable:
    """
    创建余弦相似度指标。

    Args:
        output_fields: 输出字段列表

    Returns:
        余弦相似度评估函数
    """
    client = OpenAI()

    def get_embedding(text: str) -> List[float]:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def metric(gold: Any, pred: Any, trace: Any = None) -> float:
        gold_vector = np.concatenate([get_embedding(str(gold[field])) for field in output_fields])
        pred_vector = np.concatenate([get_embedding(str(pred[field])) for field in output_fields])
        
        similarity = cosine_similarity(gold_vector, pred_vector)
        return similarity
    
    return metric


def create_llm_judge_metric(
    output_fields: List[str],
    judge_prompt_id: str
) -> Callable:
    """
    创建 LLM-as-a-Judge 指标。

    Args:
        output_fields: 输出字段列表
        judge_prompt_id: 评判提示词 ID

    Returns:
        LLM 评判评估函数

    Raises:
        ValueError: 当评判提示词或程序未找到时
    """
    example2_id = "JokeTopic:Funny-Gpt4oMini_ChainOfThought_Bootstrapfewshotwithrandomsearch-20241003.json"
    
    # 加载评判提示词详情
    if judge_prompt_id == example2_id:
        judge_prompt_path = f"example_data/{judge_prompt_id}"
    else:
        judge_prompt_path = f"prompts/{judge_prompt_id}.json"
    
    if not os.path.exists(judge_prompt_path):
        raise ValueError(f"Judge prompt not found: {judge_prompt_path}")
    
    with open(judge_prompt_path, 'r') as f:
        judge_prompt_details = json.load(f)

    print("Judge Prompt Path:", judge_prompt_path)
    print("Judge Prompt Details:", judge_prompt_details)
    
    judge_input_fields = judge_prompt_details.get('input_fields', [])
    judge_input_descs = judge_prompt_details.get('input_descs', [])
    judge_output_fields = judge_prompt_details.get('output_fields', [])
    judge_output_descs = judge_prompt_details.get('output_descs', [])
    judge_module = judge_prompt_details.get('dspy_module', 'Predict')
    judge_instructions = judge_prompt_details.get('instructions', '')
    judge_human_readable_id = judge_prompt_details.get('human_readable_id')

    print("Judge Prompt Details:")
    print(json.dumps(judge_prompt_details, indent=2))
    
    # 创建评判程序的自定义签名
    JudgeSignature = create_custom_signature(
        judge_input_fields, judge_output_fields, 
        judge_instructions, judge_input_descs, judge_output_descs
    )
    
    print("\nJudge Signature:")
    print(JudgeSignature)
    
    # 创建评判程序
    judge_program = create_dspy_module(judge_module, JudgeSignature)
    
    print("\nJudge Program:")
    print(judge_program)
    
    # 加载编译好的评判程序
    if judge_prompt_id == example2_id:
        judge_program_path = f"example_data/{judge_human_readable_id}-program.json"
    else:
        judge_program_path = f"programs/{judge_human_readable_id}.json"
    
    if not os.path.exists(judge_program_path):
        raise ValueError(f"Compiled judge program not found: {judge_program_path}")
    
    with open(judge_program_path, 'r') as f:
        judge_program_content = json.load(f)
    
    print("\nCompiled Judge Program Content:")
    print(json.dumps(judge_program_content, indent=2))
    
    judge_program.load(judge_program_path)
    
    def metric(gold: Any, pred: Any, trace: Any = None) -> float:
        try:
            # 准备评判程序的输入
            judge_input = {}
            for field in judge_input_fields:
                if field in gold:
                    judge_input[field] = gold[field]
                elif field in pred:
                    judge_input[field] = pred[field]
                else:
                    print(f"Warning: Required judge input field '{field}' not found in gold or pred")
                    judge_input[field] = ""
            
            print("Judge Input:")
            print(json.dumps(judge_input, indent=2))
            
            # 运行评判程序
            result = judge_program(**judge_input)
            
            print("Judge Program Result:")
            print(result)
            print("Result type:", type(result))
            print("Result attributes:", dir(result))
            if hasattr(result, 'toDict'):
                print("Result as dict:", result.toDict())
            
            # 从评判输出中提取分数
            if len(judge_output_fields) == 1:
                score_field = judge_output_fields[0]
                if hasattr(result, score_field):
                    score = getattr(result, score_field)
                    print(f"Score: {score}")
                    return float(score)
                else:
                    result_dict = result.toDict() if hasattr(result, 'toDict') else {}
                    if score_field in result_dict:
                        score = result_dict[score_field]
                        print(f"Score: {score}")
                        return float(score)
                    else:
                        print(f"Error: Judge program did not return expected field '{score_field}'")
                        print(f"Available fields: {result_dict.keys() if result_dict else dir(result)}")
                        return 0.0
            else:
                print(f"Error: Expected 1 output field, got {len(judge_output_fields)}")
                print(f"Output fields: {judge_output_fields}")
                return 0.0
        except Exception as e:
            print(f"Error in metric function: {str(e)}")
            return 0.0
    
    return metric


def create_metric(
    metric_type: str,
    output_fields: List[str],
    judge_prompt_id: Optional[str] = None
) -> Callable:
    """
    创建评估指标函数。

    根据指定的指标类型创建对应的评估函数。

    Args:
        metric_type: 指标类型，支持 "Exact Match", "Cosine Similarity", "LLM-as-a-Judge"
        output_fields: 输出字段列表
        judge_prompt_id: 评判提示词 ID，仅在 LLM-as-a-Judge 时需要

    Returns:
        评估指标函数

    Raises:
        ValueError: 当指定不支持的指标类型或缺少必要参数时
    """
    if metric_type == "Exact Match":
        return create_exact_match_metric(output_fields)
    elif metric_type == "Cosine Similarity":
        return create_cosine_similarity_metric(output_fields)
    elif metric_type == "LLM-as-a-Judge":
        if judge_prompt_id is None:
            raise ValueError("Judge prompt ID is required for LLM-as-a-Judge metric")
        return create_llm_judge_metric(output_fields, judge_prompt_id)
    else:
        raise ValueError(f"Unknown metric type: {metric_type}")
