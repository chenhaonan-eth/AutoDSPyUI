# 数据回收再利用实操指南

## 概述

本文档介绍如何将 DSPyUI 生成的预测数据回收再利用，形成持续优化的闭环。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           数据优化闭环                                        │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
    │ 原始数据  │ ──► │ 编译程序  │ ──► │ 批量推理  │ ──► │ 预测结果  │
    └──────────┘      └──────────┘      └──────────┘      └──────────┘
         ▲                                                      │
         │                                                      │
         │            ┌──────────┐      ┌──────────┐           │
         └─────────── │ 扩充数据  │ ◄── │ 人工审核  │ ◄─────────┘
                      └──────────┘      └──────────┘
```

---

## 第一步：理解当前数据结构

### 1.1 文件位置

| 文件类型 | 路径 | 说明 |
|---------|------|------|
| 原始训练数据 | `example_data/*.csv` | 用户上传的原始数据 |
| 编译时数据集 | `datasets/*.csv` | 编译时使用的数据快照 |
| 编译后程序 | `programs/*.json` | 包含优化后的 demos |
| 程序配置 | `prompts/*.json` | 程序的元数据配置 |

### 1.2 数据集 CSV 结构

以小红书改写任务为例：

```csv
original_title,original_content,original_tags,rewritten_title,rewritten_content,rewritten_tags
"原标题1","原内容1","#标签1","改写标题1","改写内容1","#新标签1"
"原标题2","原内容2","#标签2","改写标题2","改写内容2","#新标签2"
```

- **输入字段**: `original_title`, `original_content`, `original_tags`
- **输出字段**: `rewritten_title`, `rewritten_content`, `rewritten_tags`

### 1.3 程序 JSON 结构

```json
{
  "cot.predict": {
    "demos": [
      {
        "augmented": true,
        "original_title": "...",
        "original_content": "...",
        "reasoning": "...",
        "rewritten_title": "...",
        "rewritten_content": "..."
      }
    ],
    "signature": { ... }
  }
}
```

- `demos`: 编译器自动选择的 few-shot 示例
- `augmented: true`: 表示这是编译过程中生成的增强示例

---

## 第二步：运行批量推理生成预测数据

### 2.1 准备输入数据

创建一个只包含输入字段的 CSV 文件：

```csv
original_title,original_content,original_tags
"新标题1","新内容1","#新标签1"
"新标题2","新内容2","#新标签2"
```

### 2.2 使用 Run Tab 执行批量推理

1. 打开 DSPyUI 界面
2. 进入 **Run** 标签页
3. 选择已编译的程序
4. 上传输入 CSV 文件
5. 点击 **批量运行**
6. 等待推理完成，下载结果

### 2.3 推理结果格式

输出的 CSV 包含：

```csv
original_title,original_content,original_tags,rewritten_title,rewritten_content,rewritten_tags,_status
"新标题1","新内容1","#新标签1","生成的标题1","生成的内容1","#生成标签1","success"
```

---

## 第三步：人工审核预测结果

### 3.1 审核标准

建议从以下维度评估预测结果：

| 维度 | 评估标准 | 权重建议 |
|------|---------|---------|
| 准确性 | 是否正确理解原文意图 | 30% |
| 流畅性 | 语言是否自然流畅 | 25% |
| 创意性 | 改写是否有新意 | 20% |
| 格式规范 | 是否符合平台规范 | 15% |
| 情感保持 | 是否保持原文情感基调 | 10% |

### 3.2 标记方法

在 CSV 中添加审核列：

```csv
original_title,...,rewritten_title,...,_status,_quality,_notes
"标题1",...,"生成标题1",...,"success","good",""
"标题2",...,"生成标题2",...,"success","bad","语气不对"
"标题3",...,"生成标题3",...,"success","excellent","可作为示例"
```

**质量等级**:
- `excellent`: 优秀，可直接作为新的训练示例
- `good`: 良好，可用但不作为示例
- `fair`: 一般，需要修改后使用
- `bad`: 差，不可用

### 3.3 修正数据

对于 `fair` 级别的数据，手动修正后可以使用：

```csv
original_title,...,rewritten_title,...,_quality,_corrected_title,_corrected_content
"标题1",...,"生成标题1",...,"fair","修正后的标题","修正后的内容"
```

---

## 第四步：筛选高质量数据

### 4.1 使用 Python 脚本筛选

创建 `scripts/filter_quality_data.py`:

```python
"""
筛选高质量预测数据用于训练集扩充

用法:
    python scripts/filter_quality_data.py \
        --input results_reviewed.csv \
        --output high_quality_data.csv \
        --quality excellent,good
"""

import pandas as pd
import argparse


def filter_quality_data(input_path: str, output_path: str, quality_levels: list):
    """筛选指定质量等级的数据"""
    df = pd.read_csv(input_path)
    
    # 筛选指定质量等级
    filtered = df[df['_quality'].isin(quality_levels)]
    
    # 移除审核相关列，只保留训练所需列
    columns_to_drop = [col for col in filtered.columns if col.startswith('_')]
    result = filtered.drop(columns=columns_to_drop)
    
    # 处理修正数据
    if '_corrected_title' in df.columns:
        # 如果有修正列，使用修正后的值
        for idx, row in result.iterrows():
            if pd.notna(df.loc[idx, '_corrected_title']):
                result.loc[idx, 'rewritten_title'] = df.loc[idx, '_corrected_title']
            if pd.notna(df.loc[idx, '_corrected_content']):
                result.loc[idx, 'rewritten_content'] = df.loc[idx, '_corrected_content']
    
    result.to_csv(output_path, index=False)
    print(f"筛选完成: {len(result)} 条数据已保存到 {output_path}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="筛选高质量预测数据")
    parser.add_argument("--input", required=True, help="输入 CSV 文件路径")
    parser.add_argument("--output", required=True, help="输出 CSV 文件路径")
    parser.add_argument("--quality", default="excellent,good", help="质量等级，逗号分隔")
    
    args = parser.parse_args()
    quality_levels = [q.strip() for q in args.quality.split(",")]
    
    filter_quality_data(args.input, args.output, quality_levels)
```

### 4.2 执行筛选

```bash
python scripts/filter_quality_data.py \
    --input results_reviewed.csv \
    --output high_quality_data.csv \
    --quality excellent
```

---

## 第五步：合并数据并重新编译

### 5.1 合并原始数据和新数据

创建 `scripts/merge_datasets.py`:

```python
"""
合并原始训练数据和新筛选的高质量数据

用法:
    python scripts/merge_datasets.py \
        --original example_data/xiaohongshu_rewrite.csv \
        --new high_quality_data.csv \
        --output example_data/xiaohongshu_rewrite_v2.csv \
        --dedupe
"""

import pandas as pd
import argparse
from typing import List


def merge_datasets(
    original_path: str,
    new_path: str,
    output_path: str,
    dedupe: bool = True,
    dedupe_columns: List[str] = None
):
    """合并数据集"""
    original = pd.read_csv(original_path)
    new_data = pd.read_csv(new_path)
    
    print(f"原始数据: {len(original)} 条")
    print(f"新增数据: {len(new_data)} 条")
    
    # 确保列一致
    common_columns = list(set(original.columns) & set(new_data.columns))
    original = original[common_columns]
    new_data = new_data[common_columns]
    
    # 合并
    merged = pd.concat([original, new_data], ignore_index=True)
    
    # 去重
    if dedupe:
        if dedupe_columns is None:
            # 默认使用输入字段去重
            dedupe_columns = [col for col in common_columns if col.startswith('original_')]
        
        before_dedupe = len(merged)
        merged = merged.drop_duplicates(subset=dedupe_columns, keep='last')
        print(f"去重: 移除 {before_dedupe - len(merged)} 条重复数据")
    
    merged.to_csv(output_path, index=False)
    print(f"合并完成: {len(merged)} 条数据已保存到 {output_path}")
    return merged


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="合并数据集")
    parser.add_argument("--original", required=True, help="原始数据集路径")
    parser.add_argument("--new", required=True, help="新数据集路径")
    parser.add_argument("--output", required=True, help="输出路径")
    parser.add_argument("--dedupe", action="store_true", help="是否去重")
    
    args = parser.parse_args()
    merge_datasets(args.original, args.new, args.output, args.dedupe)
```

### 5.2 执行合并

```bash
python scripts/merge_datasets.py \
    --original example_data/xiaohongshu_rewrite.csv \
    --new high_quality_data.csv \
    --output example_data/xiaohongshu_rewrite_v2.csv \
    --dedupe
```

### 5.3 使用新数据重新编译

1. 打开 DSPyUI 界面
2. 进入 **Compile** 标签页
3. 上传合并后的新数据集 `xiaohongshu_rewrite_v2.csv`
4. 保持其他配置不变（或根据需要调整）
5. 点击 **编译**
6. 对比新旧程序的评估分数

---

## 第六步：版本管理与对比

### 6.1 命名规范

建议使用日期后缀区分版本：

```
programs/
├── XiaohongshuRewrite-Gpt4oMini_ChainOfThought_Bootstrapfewshot-20260101.json  # v1
├── XiaohongshuRewrite-Gpt4oMini_ChainOfThought_Bootstrapfewshot-20260115.json  # v2
└── XiaohongshuRewrite-Gpt4oMini_ChainOfThought_Bootstrapfewshot-20260201.json  # v3
```

### 6.2 版本对比脚本

创建 `scripts/compare_programs.py`:

```python
"""
对比两个编译程序的性能

用法:
    python scripts/compare_programs.py \
        --program1 programs/v1.json \
        --program2 programs/v2.json \
        --test_data test_data.csv
"""

import json
import argparse


def compare_programs(program1_path: str, program2_path: str):
    """对比两个程序的 demos 数量和结构"""
    with open(program1_path, 'r', encoding='utf-8') as f:
        p1 = json.load(f)
    
    with open(program2_path, 'r', encoding='utf-8') as f:
        p2 = json.load(f)
    
    # 获取 demos
    demos1 = p1.get('cot.predict', p1.get('predict', {})).get('demos', [])
    demos2 = p2.get('cot.predict', p2.get('predict', {})).get('demos', [])
    
    print(f"程序 1: {len(demos1)} 个 demos")
    print(f"程序 2: {len(demos2)} 个 demos")
    
    # 统计 augmented demos
    aug1 = sum(1 for d in demos1 if d.get('augmented', False))
    aug2 = sum(1 for d in demos2 if d.get('augmented', False))
    
    print(f"程序 1 增强示例: {aug1}")
    print(f"程序 2 增强示例: {aug2}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="对比编译程序")
    parser.add_argument("--program1", required=True)
    parser.add_argument("--program2", required=True)
    
    args = parser.parse_args()
    compare_programs(args.program1, args.program2)
```

---

## 第七步：持续优化循环

### 7.1 建议的迭代周期

```
Week 1: 收集预测数据 (100-500 条)
         ↓
Week 2: 人工审核 + 筛选高质量数据
         ↓
Week 3: 合并数据 + 重新编译
         ↓
Week 4: A/B 测试新旧程序
         ↓
(重复)
```

### 7.2 数据量建议

| 迭代轮次 | 原始数据量 | 新增数据量 | 总数据量 |
|---------|-----------|-----------|---------|
| 初始 | 20-50 | - | 20-50 |
| 第 1 轮 | 20-50 | 10-20 | 30-70 |
| 第 2 轮 | 30-70 | 15-30 | 45-100 |
| 第 3 轮 | 45-100 | 20-40 | 65-140 |

### 7.3 质量监控指标

每次迭代后记录：

| 指标 | 说明 |
|------|------|
| 评估分数 | DSPy 编译后的 evaluation score |
| 基线分数 | baseline score |
| 分数提升 | (评估分数 - 基线分数) / 基线分数 |
| 数据量 | 训练集大小 |
| 高质量率 | excellent + good 数据占比 |

---

## 附录：完整工作流脚本

创建 `scripts/data_recycling_workflow.sh`:

```bash
#!/bin/bash
# 数据回收再利用完整工作流

set -e

# 配置
PROGRAM_ID="OriginalTitleOriginalContentOriginalTags:RewrittenTitleRewrittenContentRewrittenTags-DeepseekChat_ChainOfThought_Bootstrapfewshot-20260101"
INPUT_DATA="new_inputs.csv"
REVIEWED_DATA="results_reviewed.csv"
ORIGINAL_DATA="example_data/xiaohongshu_rewrite.csv"
OUTPUT_DATA="example_data/xiaohongshu_rewrite_v2.csv"

echo "=== 数据回收再利用工作流 ==="

# Step 1: 批量推理 (需要在 UI 中完成，或使用 Python API)
echo "Step 1: 请在 DSPyUI 中执行批量推理，然后将审核后的结果保存为 ${REVIEWED_DATA}"
read -p "完成后按 Enter 继续..."

# Step 2: 筛选高质量数据
echo "Step 2: 筛选高质量数据..."
python scripts/filter_quality_data.py \
    --input "${REVIEWED_DATA}" \
    --output "high_quality_data.csv" \
    --quality "excellent"

# Step 3: 合并数据集
echo "Step 3: 合并数据集..."
python scripts/merge_datasets.py \
    --original "${ORIGINAL_DATA}" \
    --new "high_quality_data.csv" \
    --output "${OUTPUT_DATA}" \
    --dedupe

# Step 4: 提示重新编译
echo "Step 4: 请在 DSPyUI 中使用 ${OUTPUT_DATA} 重新编译程序"
echo "=== 工作流完成 ==="
```

---

## 常见问题

### Q1: 新数据应该占多大比例？

建议新数据占总数据的 20-40%。过多新数据可能导致模型"遗忘"原有模式。

### Q2: 如何判断是否需要重新编译？

当满足以下条件时建议重新编译：
- 积累了 10+ 条高质量新数据
- 发现模型在某类输入上表现不佳
- 业务需求发生变化

### Q3: 编译后分数下降怎么办？

可能原因：
1. 新数据质量不够高 → 提高审核标准
2. 新数据与原数据分布差异大 → 检查数据一致性
3. 数据量过少 → 积累更多数据后再编译

### Q4: 可以只更新 demos 而不重新编译吗？

可以，但不推荐。直接修改 `programs/*.json` 中的 demos 可以快速测试，但：
- 手动选择的 demos 可能不是最优的
- 缺少编译器的自动优化
- 难以保证一致性

---

## 总结

数据回收再利用的核心流程：

1. **生成** → 使用编译程序批量推理
2. **审核** → 人工评估预测质量
3. **筛选** → 提取高质量数据
4. **合并** → 与原数据集合并
5. **编译** → 重新训练优化
6. **对比** → 验证效果提升
7. **迭代** → 持续循环优化
