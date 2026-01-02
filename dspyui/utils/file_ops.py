"""
文件操作工具

INPUT:  prompts/, programs/, example_data/, datasets/ 目录
OUTPUT: list_prompts(), list_programs(), load_example_csv(), export_to_csv() 函数
POS:    工具函数，提供提示词、程序和数据文件的读写操作

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import os
import json
from typing import List, Dict, Any, Optional

import pandas as pd


def list_programs() -> List[Dict[str, Any]]:
    """
    列出所有可用的已编译程序。
    
    扫描 programs/ 和 prompts/ 目录，返回同时存在两个文件的程序列表。
    
    Returns:
        程序信息列表，每项包含：
        - id: 程序 ID (human_readable_id 或文件名)
        - signature: 签名 (input -> output 格式)
        - model: 使用的 LLM 模型
        - eval_score: 评估分数
    """
    programs_dir = 'programs'
    prompts_dir = 'prompts'
    
    # 检查目录是否存在
    if not os.path.exists(programs_dir):
        print(f"Programs directory does not exist: {programs_dir}")
        return []
    
    if not os.path.exists(prompts_dir):
        print(f"Prompts directory does not exist: {prompts_dir}")
        return []
    
    # 获取两个目录下的 JSON 文件名
    program_files = {f for f in os.listdir(programs_dir) if f.endswith('.json')}
    prompt_files = {f for f in os.listdir(prompts_dir) if f.endswith('.json')}
    
    # 找出同时存在于两个目录的文件
    common_files = program_files & prompt_files
    
    if not common_files:
        print("No programs found with both program and prompt files")
        return []
    
    program_list: List[Dict[str, Any]] = []
    
    for filename in sorted(common_files):
        prompt_path = os.path.join(prompts_dir, filename)
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取程序信息
            program_id = data.get('human_readable_id', filename.replace('.json', ''))
            signature = data.get('signature', '')
            
            # 如果没有 signature 字段，从 input_fields 和 output_fields 构建
            if not signature:
                input_fields = data.get('input_fields', [])
                output_fields = data.get('output_fields', [])
                signature = f"{', '.join(input_fields)} -> {', '.join(output_fields)}"
            
            model = data.get('llm_model', 'N/A')
            eval_score = data.get('evaluation_score', 'N/A')
            
            program_list.append({
                'id': program_id,
                'signature': signature,
                'model': model,
                'eval_score': eval_score
            })
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading prompt file {filename}: {e}")
            continue
    
    print(f"Found {len(program_list)} available programs")
    return program_list


def list_prompts(
    signature_filter: Optional[str] = None,
    output_filter: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    列出保存的提示词。

    Args:
        signature_filter: 可选的签名过滤器，用于筛选匹配的签名
        output_filter: 可选的输出字段过滤器列表

    Returns:
        包含提示词详情的字典列表，每个字典包含 ID、Signature、Eval Score、Details
    """
    if not os.path.exists('prompts'):
        print("Prompts directory does not exist")
        return []
    
    files = os.listdir('prompts')
    if not files:
        print("No prompt files found in the prompts directory")
        return []
    
    prompt_details: List[Dict[str, Any]] = []
    for file in files:
        if file.endswith('.json'):
            with open(os.path.join('prompts', file), 'r') as f:
                data = json.load(f)
                prompt_id = file
                signature = f"{', '.join(data['input_fields'])} -> {', '.join(data['output_fields'])}"
                input_signature = f"{', '.join(data['input_fields'])}"
                
                eval_score = data.get('evaluation_score', 'N/A')
                # 排除示例数据
                details = {k: v for k, v in data.items() if k != 'example_data'}
                
                # 检查签名过滤器
                if signature_filter and signature_filter.lower() not in signature.lower():
                    print(f"Skipping file {file} due to signature mismatch")
                    continue

                # 检查输出过滤器
                if output_filter:
                    if not all(filter_item.lower() in input_signature.lower() for filter_item in output_filter):
                        continue
                
                prompt_details.append({
                    "ID": prompt_id,
                    "Signature": signature,
                    "Eval Score": eval_score,
                    "Details": json.dumps(details, indent=4)
                })
    
    print(f"Found {len(prompt_details)} saved prompts")
    return prompt_details


def load_example_csv(example_name: str) -> Optional[pd.DataFrame]:
    """
    加载示例 CSV 文件。

    Args:
        example_name: 示例文件名（不含扩展名）

    Returns:
        加载的 DataFrame，如果文件不存在则返回 None
    """
    csv_path = f"example_data/{example_name}.csv"
    try:
        df = pd.read_csv(csv_path)
        return df
    except FileNotFoundError:
        print(f"CSV file not found: {csv_path}")
        return None


def export_to_csv(data: List[Dict[str, Any]]) -> str:
    """
    将数据导出为 CSV 文件。

    Args:
        data: 要导出的数据列表

    Returns:
        导出的文件名
    """
    df = pd.DataFrame(data)
    filename = "exported_data.csv"
    df.to_csv(filename, index=False)
    return filename
