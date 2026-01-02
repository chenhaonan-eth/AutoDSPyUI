"""
合并原始训练数据和新筛选的高质量数据

INPUT:  原始数据集 CSV, 新数据集 CSV
OUTPUT: 合并后的数据集 CSV
POS:    数据回收工作流的合并步骤

用法:
    python scripts/merge_datasets.py \
        --original example_data/xiaohongshu_rewrite.csv \
        --new high_quality_data.csv \
        --output example_data/xiaohongshu_rewrite_v2.csv \
        --dedupe

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import pandas as pd
import argparse
from typing import List, Optional


def merge_datasets(
    original_path: str,
    new_path: str,
    output_path: str,
    dedupe: bool = True,
    dedupe_columns: Optional[List[str]] = None,
    max_new_ratio: float = 0.5
) -> pd.DataFrame:
    """
    合并数据集
    
    Args:
        original_path: 原始数据集路径
        new_path: 新数据集路径
        output_path: 输出路径
        dedupe: 是否去重
        dedupe_columns: 用于去重的列，默认使用所有 original_ 开头的列
        max_new_ratio: 新数据最大占比，超过则警告
        
    Returns:
        合并后的 DataFrame
    """
    original = pd.read_csv(original_path)
    new_data = pd.read_csv(new_path)
    
    print(f"原始数据: {len(original)} 条")
    print(f"新增数据: {len(new_data)} 条")
    
    # 检查新数据占比
    new_ratio = len(new_data) / (len(original) + len(new_data))
    if new_ratio > max_new_ratio:
        print(f"⚠️ 警告: 新数据占比 {new_ratio:.1%} 超过建议值 {max_new_ratio:.0%}")
        print("   过多新数据可能导致模型'遗忘'原有模式")
    
    # 确保列一致
    original_columns = set(original.columns)
    new_columns = set(new_data.columns)
    
    if original_columns != new_columns:
        common_columns = list(original_columns & new_columns)
        missing_in_new = original_columns - new_columns
        missing_in_original = new_columns - original_columns
        
        if missing_in_new:
            print(f"⚠️ 新数据缺少列: {missing_in_new}")
        if missing_in_original:
            print(f"⚠️ 原数据缺少列: {missing_in_original}")
        
        print(f"将只保留共同列: {common_columns}")
        original = original[common_columns]
        new_data = new_data[common_columns]
    else:
        common_columns = list(original.columns)
    
    # 合并
    merged = pd.concat([original, new_data], ignore_index=True)
    
    # 去重
    if dedupe:
        if dedupe_columns is None:
            # 默认使用输入字段去重 (original_ 开头的列)
            dedupe_columns = [col for col in common_columns if col.startswith('original_')]
            if not dedupe_columns:
                # 如果没有 original_ 开头的列，使用前半部分列
                dedupe_columns = common_columns[:len(common_columns)//2]
        
        print(f"去重依据列: {dedupe_columns}")
        before_dedupe = len(merged)
        merged = merged.drop_duplicates(subset=dedupe_columns, keep='last')
        removed = before_dedupe - len(merged)
        if removed > 0:
            print(f"去重: 移除 {removed} 条重复数据")
    
    merged.to_csv(output_path, index=False)
    print(f"合并完成: {len(merged)} 条数据已保存到 {output_path}")
    
    # 打印统计信息
    print("\n--- 统计信息 ---")
    print(f"原始数据: {len(original)} 条")
    print(f"新增数据: {len(new_data)} 条")
    print(f"最终数据: {len(merged)} 条")
    print(f"新数据占比: {len(new_data)/len(merged):.1%}")
    
    return merged


def main():
    parser = argparse.ArgumentParser(
        description="合并数据集",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 基本合并
    python scripts/merge_datasets.py --original data_v1.csv --new new_data.csv --output data_v2.csv
    
    # 合并并去重
    python scripts/merge_datasets.py --original data_v1.csv --new new_data.csv --output data_v2.csv --dedupe
    
    # 指定去重列
    python scripts/merge_datasets.py --original data_v1.csv --new new_data.csv --output data_v2.csv --dedupe --dedupe-columns "title,content"
        """
    )
    parser.add_argument("--original", "-o", required=True, help="原始数据集路径")
    parser.add_argument("--new", "-n", required=True, help="新数据集路径")
    parser.add_argument("--output", required=True, help="输出路径")
    parser.add_argument("--dedupe", "-d", action="store_true", help="是否去重")
    parser.add_argument(
        "--dedupe-columns",
        help="用于去重的列，逗号分隔 (默认: 所有 original_ 开头的列)"
    )
    parser.add_argument(
        "--max-new-ratio",
        type=float,
        default=0.5,
        help="新数据最大占比警告阈值 (默认: 0.5)"
    )
    
    args = parser.parse_args()
    
    dedupe_columns = None
    if args.dedupe_columns:
        dedupe_columns = [col.strip() for col in args.dedupe_columns.split(",")]
    
    merge_datasets(
        args.original,
        args.new,
        args.output,
        dedupe=args.dedupe,
        dedupe_columns=dedupe_columns,
        max_new_ratio=args.max_new_ratio
    )


if __name__ == "__main__":
    main()
