"""
筛选高质量预测数据用于训练集扩充

INPUT:  审核后的 CSV 文件 (包含 _quality 列)
OUTPUT: 筛选后的高质量数据 CSV
POS:    数据回收工作流的筛选步骤

用法:
    python scripts/filter_quality_data.py \
        --input results_reviewed.csv \
        --output high_quality_data.csv \
        --quality excellent,good

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import pandas as pd
import argparse
from typing import List


def filter_quality_data(
    input_path: str,
    output_path: str,
    quality_levels: List[str],
    use_corrected: bool = True
) -> pd.DataFrame:
    """
    筛选指定质量等级的数据
    
    Args:
        input_path: 输入 CSV 文件路径
        output_path: 输出 CSV 文件路径
        quality_levels: 要筛选的质量等级列表
        use_corrected: 是否使用修正后的数据
        
    Returns:
        筛选后的 DataFrame
    """
    df = pd.read_csv(input_path)
    
    # 检查是否有 _quality 列
    if '_quality' not in df.columns:
        print("警告: CSV 中没有 _quality 列，将返回所有 _status=success 的数据")
        if '_status' in df.columns:
            filtered = df[df['_status'] == 'success']
        else:
            filtered = df
    else:
        # 筛选指定质量等级
        filtered = df[df['_quality'].isin(quality_levels)]
    
    print(f"原始数据: {len(df)} 条")
    print(f"筛选后: {len(filtered)} 条")
    
    # 处理修正数据
    if use_corrected:
        corrected_columns = [col for col in filtered.columns if col.startswith('_corrected_')]
        for corrected_col in corrected_columns:
            # 从 _corrected_xxx 提取原始字段名
            original_col = corrected_col.replace('_corrected_', '')
            if original_col in filtered.columns:
                # 使用修正值替换原值（如果修正值存在）
                mask = filtered[corrected_col].notna()
                filtered.loc[mask, original_col] = filtered.loc[mask, corrected_col]
                print(f"已应用 {mask.sum()} 条修正数据到 {original_col}")
    
    # 移除审核相关列，只保留训练所需列
    columns_to_drop = [col for col in filtered.columns if col.startswith('_')]
    result = filtered.drop(columns=columns_to_drop, errors='ignore')
    
    result.to_csv(output_path, index=False)
    print(f"筛选完成: {len(result)} 条数据已保存到 {output_path}")
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="筛选高质量预测数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 筛选 good 级别的数据
    python scripts/filter_quality_data.py --input reviewed.csv --output filtered.csv --quality good
    
    # 筛选 good 和 fix 级别的数据 (fix 会自动使用修正后的值)
    python scripts/filter_quality_data.py --input reviewed.csv --output filtered.csv --quality good,fix
    
    # 不使用修正数据
    python scripts/filter_quality_data.py --input reviewed.csv --output filtered.csv --quality good --no-corrected
        """
    )
    parser.add_argument("--input", "-i", required=True, help="输入 CSV 文件路径")
    parser.add_argument("--output", "-o", required=True, help="输出 CSV 文件路径")
    parser.add_argument(
        "--quality", "-q",
        default="good,fix",
        help="质量等级，逗号分隔 (默认: good,fix)"
    )
    parser.add_argument(
        "--no-corrected",
        action="store_true",
        help="不使用修正后的数据"
    )
    
    args = parser.parse_args()
    quality_levels = [q.strip() for q in args.quality.split(",")]
    
    filter_quality_data(
        args.input,
        args.output,
        quality_levels,
        use_corrected=not args.no_corrected
    )


if __name__ == "__main__":
    main()
