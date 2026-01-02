# DSPy 优化器数据集需求指南

> 一旦我所属的文件夹有所变化，请更新我。

本文档描述 DSPyUI 支持的各优化器对训练数据集数量的要求。

## 支持的优化器

| 优化器 | 最小数据量 | 推荐数据量 | 说明 |
|--------|-----------|-----------|------|
| **BootstrapFewShot** | 10-20 条 | 50-100 条 | 轻量级，适合快速迭代 |
| **BootstrapFewShotWithRandomSearch** | 50 条 | 100-200 条 | 需要额外验证集 |
| **COPRO** | 20-50 条 | 100+ 条 | 指令优化，数据质量比数量重要 |
| **MIPROv2** | 100 条 | 200-500 条 | 重量级优化，数据越多效果越好 |

## 详细说明

### BootstrapFewShot

最基础的 few-shot 优化器，通过 teacher 模型生成示例。

- **工作原理**: 从训练集采样，用 teacher 模型生成完整示例
- **关键参数**:
  - `max_bootstrapped_demos`: 自动生成的示例数 (默认 4)
  - `max_labeled_demos`: 使用的标注示例数 (默认 4)
- **数据要求**: 至少需要 `max_bootstrapped_demos + max_labeled_demos` 条数据

### BootstrapFewShotWithRandomSearch

在 BootstrapFewShot 基础上增加随机搜索。

- **工作原理**: 多次运行 BootstrapFewShot，选择最佳结果
- **关键参数**:
  - `num_candidate_programs`: 候选程序数量 (默认 10)
- **数据要求**: 需要训练集 + 验证集，建议各 50 条以上

### COPRO

专注于优化指令/提示词的优化器。

- **工作原理**: 迭代优化 prompt 中的指令部分
- **特点**: 对数据质量敏感，高质量少量数据优于低质量大量数据
- **数据要求**: 20-50 条高质量标注数据即可

### MIPROv2

最强大的优化器，同时优化指令和 few-shot 示例。

- **工作原理**: 
  1. 生成候选指令
  2. Bootstrap few-shot 示例
  3. 贝叶斯优化选择最佳组合
- **优化级别**:
  - `light`: 快速优化，适合 100+ 条数据
  - `medium`: 平衡模式，适合 200+ 条数据
  - `heavy`: 深度优化，适合 500+ 条数据
- **关键参数**:
  - `num_candidates`: 候选数量
  - `max_bootstrapped_demos`: 自动生成示例数
  - `max_labeled_demos`: 标注示例数

## 数据集拆分

DSPyUI 默认按 **80/20** 比例拆分训练集和验证集：

```
总数据量 = 训练集 (80%) + 验证集 (20%)
```

例如：100 条数据 → 80 条训练 + 20 条验证

## 选择建议

| 场景 | 推荐优化器 | 数据量 |
|------|-----------|--------|
| 快速原型验证 | BootstrapFewShot | 20-50 条 |
| 生产环境优化 | MIPROv2 (medium) | 200+ 条 |
| 指令调优 | COPRO | 50-100 条 |
| 资源有限 | BootstrapFewShot | 10-20 条 |

## 参考资料

- [DSPy 官方文档 - Optimizers](https://dspy.ai/learn/optimization/optimizers)
- [MIPROv2 API 文档](https://dspy.ai/api/optimizers/MIPROv2)

---

*Content was rephrased for compliance with licensing restrictions*
