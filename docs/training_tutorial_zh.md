# AutoDSPyUI 端到端训练（编译）教程

本教程将引导你使用 AutoDSPyUI 框架完成从任务定义到程序编译、评估和测试的完整流程。

## 核心流程概述

AutoDSPyUI 的核心工作流可以概括为以下四个步骤：
1. **定义任务 (Defining Task)**：确定输入和输出字段及任务指令。
2. **准备数据 (Preparing Data)**：提供少量的有标签示例。
3. **配置编译 (Configuring Compilation)**：选择模型、优化器和评估指标。
4. **执行并验证 (Execution & Verification)**：运行编译，查看优化后的提示词，并进行实时测试。

---

## 步骤详解

### 1. 定义任务 (Define Your Task)

在 **Compile Program** 标签页中，你需要定义任务的骨架：

*   **Task Instructions**: 简要描述你希望 AI 完成什么任务（例如：“将给定的笑话重写为脱口秀风格”）。
*   **Input Fields**: 定义输入的属性名和描述。
    *   点击 "Add Input" 添加字段。
    *   `Name`: 字段名（对应数据文件中的列名）。
    *   `Description`: (可选) 对该字段的详细描述，有助于 LLM 理解。
*   **Output Fields**: 定义你期望 AI 输出的属性名和描述。

### 2. 准备数据 (Prepare Your Data)

DSPy 需要通过示例来学习如何优化。你通常需要 10-50 条数据。

*   **手动输入**: 点击 "Enter Manually" 可以在表格中直接编辑数据。
*   **上传 CSV**: 推荐方式。准备一个 CSV 文件，其表头（Columns）必须与你定义的 `Input Fields` 和 `Output Fields` 的名称完全一致。
    *   例如：定义了输入 `joke` 和输出 `funny_score`，则 CSV 必须包含这两列。
*   **示例数据**: 你可以点击页面右上角的示例按钮（如 "Judging Jokes"）快速加载预设的配置和数据进行体验。

### 3. 配置编译设置 (Configure Settings)

*   **Models**:
    *   `LLM Model`: 最终运行程序所使用的模型（通常选较轻量的模型，如 `gpt-4o-mini`）。
    *   `Teacher Model`: 用于生成高质量示例或辅助优化的强模型（通常选 `gpt-4o`）。
*   **DSPy Module**:
    *   `Predict`: 直接预测。
    *   `ChainOfThought`: 增加思维链，通常效果更好。
*   **Optimizer**:
    *   `BootstrapFewShot`: 最基础的优化器，通过教师模型生成少样本示例。
    *   `BootstrapFewShotWithRandomSearch`: 在前者基础上增加随机搜索，通常能找到更好的示例组合。
*   **Metrics**:
    *   `Exact Match`: 严格匹配文本。
    *   `Cosine Similarity`: 计算向量相似度。
    *   `LLM-as-a-Judge`: 使用强模型（如 GPT-4）根据你提供的准则进行自动打分。

### 4. 执行编译与评估 (Compile & Evaluate)

点击 **"Compile"** 按钮，系统将开始：
1. 构建 DSPy 程序。
2. 使用优化器在你的数据集上进行迭代优化。
3. 计算 **Baseline Score** (优化前分值) 和 **Evaluation Score** (优化后分值)。

**查看结果**:
*   **Optimized Prompt**: 编译完成后，你可以在下方看到 DSPy 自动生成的优化后的提示词（包括筛选出的最佳示例）。
*   **MLflow Integration**: 如果配置了 MLflow，你可以点击 "View Experiment" 或 "View Run" 详细查看每一步优化的参数和曲线。

### 5. 实时测试 (Test Your Program)

编译成功后，页面底部会出现测试区域：
1. **Select Row**: 从你的数据集中选择一行，或者点击 "Select Random Row"。
2. **Generate**: 点击按钮，系统将使用刚刚编译好的“程序”针对输入生成结果。
3. **Verify**: 观察生成的输出是否符合预期。

---

## 如何在代码中调用编译好的模型

编译完成后，你可以脱离 GUI，在自己的 Python 脚本中调用这些优化后的程序。

### 1. 核心原理

AutoDSPyUI 在编译时会保存两个核心文件：
1.  **元数据 (`prompts/{ID}.json`)**: 包含输入输出字段、指令、模块类型等配置。
2.  **程序状态 (`programs/{ID}.json`)**: 包含 DSPy 优化后的权重（主要是 Few-shot 示例）。

### 2. 简易调用方式 (使用内置 Runner)

最快捷的方法是直接调用框架提供的 `generate_program_response` 函数：

```python
from dspyui.core.runner import generate_program_response

# 使用你在 UI 中看到的 ID (human_readable_id)
program_id = "JokeTopic:Funny-Gpt4oMini_ChainOfThought_BootstrapFewShot..."

# 准备输入数据
input_data = {
    "joke": "为什么程序员分不清万圣节和圣诞节？",
    "topic": "程序员幽默"
}

# 获取响应
response = generate_program_response(program_id, input_data)
print(response)
```

### 3. 底层调用方式 (原生 DSPy)

如果你想更灵活地控制流程，可以按照以下步骤手动加载：

```python
import dspy
import json
from dspyui.core.signatures import create_custom_signature
from dspyui.core.modules import create_dspy_module

# 1. 加载元数据
program_id = "你的程序ID"
with open(f"prompts/{program_id}.json", 'r') as f:
    meta = json.load(f)

# 2. 配置环境
lm = dspy.LM(f"openai/{meta['llm_model']}")
dspy.settings.configure(lm=lm)

# 3. 重构签名与模块
CustomSignature = create_custom_signature(
    meta['input_fields'], 
    meta['output_fields'], 
    meta['instructions']
)
module = create_dspy_module(meta['dspy_module'], CustomSignature)

# 4. 加载编译后的权重
module.load(f"programs/{program_id}.json")

# 5. 执行
result = module(joke="...", topic="...")
print(result.funny)
```

---

## 注意事项

*   **字段一致性**: 确保上传的 CSV 表头与定义的字段名严格匹配（大小写敏感）。
*   **数据质量**: DSPy 的核心是“少数高质量示例优于大量低质量示例”。
*   **API 密钥**: 确保你的 `.env` 文件中配置了正确的 `OPENAI_API_KEY` 或其他模型供应商密钥。

---

## 进阶

如果你想自定义复杂的评判逻辑，可以参考 [自定义指标流程 (Create Metric Flow)](./create_metric_flow.md) 文档。
