"""
对比两个编译程序的结构和性能

INPUT:  两个程序的 JSON 文件路径
OUTPUT: 对比报告 (打印到控制台)
POS:    数据回收工作流的验证步骤

用法:
    python scripts/compare_programs.py \
        --program1 programs/v1.json \
        --program2 programs/v2.json

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import json
import argparse
from typing import Dict, Any, List


def load_program(path: str) -> Dict[str, Any]:
    """加载程序 JSON"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_demos(program: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从程序中提取 demos"""
    # 尝试不同的键名
    for key in ['cot.predict', 'predict', 'cot']:
        if key in program:
            return program[key].get('demos', [])
    return []


def analyze_demos(demos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """分析 demos 的统计信息"""
    if not demos:
        return {'total': 0, 'augmented': 0, 'labeled': 0}
    
    augmented = sum(1 for d in demos if d.get('augmented', False))
    labeled = len(demos) - augmented
    
    # 分析字段
    fields = set()
    for demo in demos:
        fields.update(demo.keys())
    
    # 移除元数据字段
    meta_fields = {'augmented', 'reasoning'}
    content_fields = fields - meta_fields
    
    return {
        'total': len(demos),
        'augmented': augmented,
        'labeled': labeled,
        'fields': list(content_fields),
        'has_reasoning': any('reasoning' in d for d in demos)
    }


def compare_programs(program1_path: str, program2_path: str, verbose: bool = False):
    """对比两个程序"""
    p1 = load_program(program1_path)
    p2 = load_program(program2_path)
    
    demos1 = get_demos(p1)
    demos2 = get_demos(p2)
    
    stats1 = analyze_demos(demos1)
    stats2 = analyze_demos(demos2)
    
    print("=" * 60)
    print("程序对比报告")
    print("=" * 60)
    
    print(f"\n{'指标':<20} {'程序 1':<15} {'程序 2':<15} {'变化':<15}")
    print("-" * 60)
    
    # Demos 数量
    diff_total = stats2['total'] - stats1['total']
    diff_str = f"+{diff_total}" if diff_total > 0 else str(diff_total)
    print(f"{'Demos 总数':<20} {stats1['total']:<15} {stats2['total']:<15} {diff_str:<15}")
    
    # 增强示例
    diff_aug = stats2['augmented'] - stats1['augmented']
    diff_str = f"+{diff_aug}" if diff_aug > 0 else str(diff_aug)
    print(f"{'增强示例':<20} {stats1['augmented']:<15} {stats2['augmented']:<15} {diff_str:<15}")
    
    # 标注示例
    diff_lab = stats2['labeled'] - stats1['labeled']
    diff_str = f"+{diff_lab}" if diff_lab > 0 else str(diff_lab)
    print(f"{'标注示例':<20} {stats1['labeled']:<15} {stats2['labeled']:<15} {diff_str:<15}")
    
    # 是否有推理
    has_r1 = "是" if stats1['has_reasoning'] else "否"
    has_r2 = "是" if stats2['has_reasoning'] else "否"
    print(f"{'包含推理':<20} {has_r1:<15} {has_r2:<15}")
    
    print("\n" + "=" * 60)
    
    # 字段对比
    if stats1['fields'] or stats2['fields']:
        print("\n字段信息:")
        print(f"  程序 1: {', '.join(sorted(stats1['fields']))}")
        print(f"  程序 2: {', '.join(sorted(stats2['fields']))}")
    
    # 详细信息
    if verbose and demos1:
        print("\n" + "=" * 60)
        print("程序 1 Demos 详情:")
        print("-" * 60)
        for i, demo in enumerate(demos1[:3]):  # 只显示前 3 个
            print(f"\nDemo {i+1}:")
            for key, value in demo.items():
                if key == 'reasoning':
                    print(f"  {key}: {str(value)[:100]}...")
                else:
                    print(f"  {key}: {str(value)[:50]}...")
    
    if verbose and demos2:
        print("\n" + "=" * 60)
        print("程序 2 Demos 详情:")
        print("-" * 60)
        for i, demo in enumerate(demos2[:3]):
            print(f"\nDemo {i+1}:")
            for key, value in demo.items():
                if key == 'reasoning':
                    print(f"  {key}: {str(value)[:100]}...")
                else:
                    print(f"  {key}: {str(value)[:50]}...")
    
    # 建议
    print("\n" + "=" * 60)
    print("建议:")
    print("-" * 60)
    
    if stats2['total'] > stats1['total']:
        print("✓ 程序 2 有更多 demos，可能表现更好")
    elif stats2['total'] < stats1['total']:
        print("⚠ 程序 2 demos 减少，需要验证性能")
    
    if stats2['augmented'] > stats1['augmented']:
        print("✓ 程序 2 有更多增强示例，编译器找到了更多有效模式")
    
    print("\n建议使用相同测试集对比两个程序的实际输出质量")


def main():
    parser = argparse.ArgumentParser(
        description="对比两个编译程序",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 基本对比
    python scripts/compare_programs.py --program1 programs/v1.json --program2 programs/v2.json
    
    # 详细对比
    python scripts/compare_programs.py --program1 programs/v1.json --program2 programs/v2.json --verbose
        """
    )
    parser.add_argument("--program1", "-p1", required=True, help="第一个程序路径")
    parser.add_argument("--program2", "-p2", required=True, help="第二个程序路径")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    
    args = parser.parse_args()
    compare_programs(args.program1, args.program2, args.verbose)


if __name__ == "__main__":
    main()
