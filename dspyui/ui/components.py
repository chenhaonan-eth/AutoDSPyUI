"""
可复用 UI 组件

INPUT:  gradio, pandas
OUTPUT: 辅助函数和组件创建函数
POS:    UI 辅助模块，被各 tab 模块调用

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

from typing import List, Tuple, Any

import gradio as gr
import pandas as pd


def add_field(values: List[Tuple[str, str]]) -> Tuple[List[Tuple[str, str]], Any]:
    """
    添加一个新字段。

    Args:
        values: 当前字段列表

    Returns:
        (更新后的字段列表, 移除按钮更新)
    """
    new_values = values + [("", "")]
    return new_values, gr.update(interactive=True)


def remove_last_field(values: List[Tuple[str, str]]) -> Tuple[List[Tuple[str, str]], Any]:
    """
    移除最后一个字段。

    Args:
        values: 当前字段列表

    Returns:
        (更新后的字段列表, 移除按钮更新)
    """
    new_values = values[:-1] if values else values
    return new_values, gr.update(interactive=bool(new_values))


def load_csv(filename: str) -> pd.DataFrame:
    """
    从 example_data 目录加载 CSV 文件。

    Args:
        filename: CSV 文件名

    Returns:
        加载的 DataFrame，出错时返回空 DataFrame
    """
    try:
        df = pd.read_csv(f"example_data/{filename}")
        return df
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return pd.DataFrame()
