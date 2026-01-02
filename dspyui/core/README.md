<!-- 一旦我所属的文件夹有所变化，请更新我 -->

# core

DSPy 程序编译的核心业务逻辑。
包含 Signature 创建、Module 定义、指标计算、编译器和程序运行器。

## 文件清单

| 文件 | 地位 | 功能 |
|-----|------|------|
| `__init__.py` | 入口 | 导出核心 API |
| `signatures.py` | 核心 | 创建自定义 DSPy Signature |
| `modules.py` | 核心 | 创建 DSPy Module (Predict/CoT) |
| `metrics.py` | 核心 | 评估指标 (精确匹配/余弦/LLM Judge)，支持 zero-shot 评判 |
| `compiler.py` | 核心 | 程序编译主逻辑，默认使用 zero-shot 评判 |
| `runner.py` | 核心 | 程序执行逻辑 |

## 最近更新 (2024-12-31)

- `metrics.py`: 新增 `use_compiled` 参数，支持 zero-shot 评判模式
- `compiler.py`: 默认使用 zero-shot 评判，简化训练流程
