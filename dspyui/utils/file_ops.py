"""
文件操作工具

INPUT:  prompts/, example_data/, datasets/ 目录
OUTPUT: list_prompts(), load_example_csv(), export_to_csv() 函数
POS:    工具函数，提供提示词和数据文件的读写操作

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import os
import json
from typing import List, Dict, Any, Optional

import pandas as pd


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
