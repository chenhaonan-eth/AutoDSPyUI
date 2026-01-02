# scripts 文件夹

数据回收再利用工作流的辅助脚本集合。

⚠️ 一旦我所属的文件夹有所变化，请更新我。

## 文件清单

| 文件 | 功能 | 用途 |
|------|------|------|
| `filter_quality_data.py` | 数据筛选 | 从审核后的预测结果中筛选高质量数据 |
| `merge_datasets.py` | 数据合并 | 将新数据与原始训练集合并 |
| `compare_programs.py` | 程序对比 | 对比两个编译程序的结构差异 |

## 快速使用

```bash
# 1. 筛选高质量数据
python scripts/filter_quality_data.py \
    --input results_reviewed.csv \
    --output high_quality_data.csv \
    --quality excellent

# 2. 合并数据集
python scripts/merge_datasets.py \
    --original example_data/original.csv \
    --new high_quality_data.csv \
    --output example_data/merged.csv \
    --dedupe

# 3. 对比程序版本
python scripts/compare_programs.py \
    --program1 programs/v1.json \
    --program2 programs/v2.json
```

## 相关文档

详细使用指南请参考: [docs/data_recycling_guide.md](../docs/data_recycling_guide.md)
