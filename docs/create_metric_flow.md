# create_metric 评估指标创建流程详解

## 流程图

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           create_metric() 入口                                   │
│  参数: metric_type, output_fields, judge_prompt_id, use_compiled_judge=False    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
                    ┌───────────────────┴───────────────────┐
                    │           metric_type 分支判断          │
                    └───────────────────┬───────────────────┘
                                        │
          ┌─────────────────────────────┼─────────────────────────────┐
          │                             │                             │
          ▼                             ▼                             ▼
┌─────────────────┐         ┌─────────────────────┐       ┌─────────────────────┐
│  Exact Match    │         │  Cosine Similarity  │       │  LLM-as-a-Judge     │
│  精确匹配指标    │         │    余弦相似度指标     │       │   LLM 评判指标       │
└────────┬────────┘         └──────────┬──────────┘       └──────────┬──────────┘
         │                             │                             │
         ▼                             ▼                             ▼
┌─────────────────┐         ┌─────────────────────┐       ┌─────────────────────┐
│ 直接比较字段值   │         │ 1. 调用 OpenAI      │       │ 1. 加载 judge 配置   │
│ gold[field] ==  │         │    Embedding API    │       │    (prompts/*.json) │
│ pred.field      │         │ 2. 计算向量余弦相似度│       │ 2. 创建 JudgeSignature│
│                 │         │                     │       │ 3. 创建 judge_program│
│ 返回: 0 或 1    │         │ 返回: 0.0 ~ 1.0     │       │ 4. (可选)加载编译程序 │
└─────────────────┘         └─────────────────────┘       │ 5. 运行评判并返回分数 │
                                                          │                     │
                                                          │ 返回: 0.0 ~ 1.0     │
                                                          └─────────────────────┘
```

## LLM-as-a-Judge 详细流程

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    create_llm_judge_metric() 详细流程                            │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Step 1: 加载评判提示词配置                                                        │
│ ─────────────────────────────────────────────────────────────────────────────── │
│ 路径: prompts/{judge_prompt_id}.json                                            │
│                                                                                 │
│ JSON 结构示例:                                                                   │
│ {                                                                               │
│   "input_fields": ["OriginalContent", "RewrittenContent"],                     │
│   "input_descs": ["原始内容", "改写后的内容"],                                    │
│   "output_fields": ["Score"],                                                   │
│   "output_descs": ["评分 0-1"],                                                 │
│   "dspy_module": "ChainOfThought",                                             │
│   "instructions": "评估改写质量...",                                             │
│   "human_readable_id": "XiaohongshuRewriteJudge-Gpt4oMini_ChainOfThought"      │
│ }                                                                               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Step 2: 创建 JudgeSignature (调用 create_custom_signature)                       │
│ ─────────────────────────────────────────────────────────────────────────────── │
│                                                                                 │
│   create_custom_signature(                                                      │
│       judge_input_fields,    # ["OriginalContent", "RewrittenContent"]         │
│       judge_output_fields,   # ["Score"]                                        │
│       judge_instructions,    # "评估改写质量..."                                 │
│       judge_input_descs,     # ["原始内容", "改写后的内容"]                       │
│       judge_output_descs     # ["评分 0-1"]                                     │
│   )                                                                             │
│                                                                                 │
│   返回: 动态创建的 dspy.Signature 子类                                           │
│                                                                                 │
│   class JudgeSignature(dspy.Signature):                                         │
│       """评估改写质量..."""                                                      │
│       OriginalContent: str = InputField(desc="原始内容")                        │
│       RewrittenContent: str = InputField(desc="改写后的内容")                   │
│       Score: str = OutputField(desc="评分 0-1")                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Step 3: 创建 judge_program (调用 create_dspy_module)                             │
│ ─────────────────────────────────────────────────────────────────────────────── │
│                                                                                 │
│   create_dspy_module(                                                           │
│       "ChainOfThought",      # 或 "Predict"                                     │
│       JudgeSignature                                                            │
│   )                                                                             │
│                                                                                 │
│   返回: dspy.Module 实例                                                         │
│                                                                                 │
│   class CustomChainOfThoughtModule(dspy.Module):                                │
│       def __init__(self):                                                       │
│           self.cot = dspy.ChainOfThought(JudgeSignature)                        │
│       def forward(self, **kwargs):                                              │
│           return self.cot(**kwargs)                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Step 4: 是否加载编译好的评判程序? (use_compiled_judge 参数)                        │
│ ─────────────────────────────────────────────────────────────────────────────── │
│                                                                                 │
│   if use_compiled_judge == True:                                                │
│       ┌─────────────────────────────────────────────────────────────────────┐   │
│       │ 加载 programs/{human_readable_id}.json                              │   │
│       │ judge_program.load(judge_program_path)                              │   │
│       │                                                                     │   │
│       │ 编译后的程序包含:                                                    │   │
│       │ - 优化后的 few-shot 示例                                            │   │
│       │ - 更好的 prompt 模板                                                │   │
│       └─────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│   if use_compiled_judge == False (默认):                                        │
│       ┌─────────────────────────────────────────────────────────────────────┐   │
│       │ 使用 Zero-Shot 模式                                                 │   │
│       │ - 不加载任何预训练的示例                                             │   │
│       │ - 直接使用 Signature 中的 instructions                              │   │
│       │ - 避免循环依赖 (评判程序需要先编译才能用于编译)                        │   │
│       └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Step 5: 返回 metric 函数 (闭包)                                                  │
│ ─────────────────────────────────────────────────────────────────────────────── │
│                                                                                 │
│   def metric(gold, pred, trace=None) -> float:                                  │
│       # 1. 准备评判输入                                                          │
│       judge_input = {}                                                          │
│       for field in judge_input_fields:                                          │
│           if field in gold:                                                     │
│               judge_input[field] = gold[field]                                  │
│           elif field in pred:                                                   │
│               judge_input[field] = pred[field]                                  │
│                                                                                 │
│       # 2. 运行评判程序                                                          │
│       result = judge_program(**judge_input)                                     │
│                                                                                 │
│       # 3. 提取分数                                                              │
│       score = getattr(result, judge_output_fields[0])  # 如 "Score"            │
│       return float(score)                                                       │
│                                                                                 │
│   return metric                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 在 compile_program 中的调用时序

```
compile_program()
        │
        ├── 1. 创建 LM 实例 (_create_lm)
        │
        ├── 2. 创建主程序 Signature (create_custom_signature)
        │
        ├── 3. 创建主程序 Module (create_dspy_module)
        │
        ├── 4. 准备训练/验证数据集
        │
        ├── 5. 创建评估指标 ◄─────────────────────────────────────────────┐
        │       │                                                         │
        │       │   metric = create_metric(                               │
        │       │       metric_type,           # "LLM-as-a-Judge"         │
        │       │       output_fields,         # 主程序的输出字段          │
        │       │       judge_prompt_id,       # 评判程序的配置 ID         │
        │       │       use_compiled_judge=False  # 使用 zero-shot        │
        │       │   )                                                     │
        │       │                                                         │
        │       └── 返回: metric 函数                                      │
        │                                                                 │
        ├── 6. 基线评估                                                    │
        │       baseline_evaluate = Evaluate(metric=metric, devset=devset)│
        │       baseline_score = baseline_evaluate(module)                │
        │                                                                 │
        ├── 7. 优化器编译                                                  │
        │       teleprompter = BootstrapFewShot(metric=metric, ...)       │
        │       compiled_program = teleprompter.compile(module, trainset) │
        │                                                                 │
        │       ┌─────────────────────────────────────────────────────┐   │
        │       │ 优化过程中会多次调用 metric 函数:                     │   │
        │       │                                                     │   │
        │       │ for example in trainset:                            │   │
        │       │     pred = module(**example.inputs())               │   │
        │       │     score = metric(example, pred)  ◄── 调用评判程序  │   │
        │       │     if score > threshold:                           │   │
        │       │         add_to_demos(example, pred)                 │   │
        │       └─────────────────────────────────────────────────────┘   │
        │                                                                 │
        ├── 8. 最终评估                                                    │
        │       evaluate = Evaluate(metric=metric, devset=devset)         │
        │       score = evaluate(compiled_program)                        │
        │                                                                 │
        └── 9. 保存结果并返回
```

## 为什么默认 use_compiled_judge=False?

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           避免循环依赖问题                                        │
└─────────────────────────────────────────────────────────────────────────────────┘

问题场景:
┌─────────────────┐     需要      ┌─────────────────┐
│  编译主程序 A    │ ──────────► │  评判程序 B      │
│                 │              │  (已编译版本)    │
└─────────────────┘              └─────────────────┘
                                         │
                                         │ 但是...
                                         ▼
                                 ┌─────────────────┐
                                 │  评判程序 B      │
                                 │  也需要先编译    │
                                 │  才能使用!       │
                                 └─────────────────┘

解决方案:
┌─────────────────┐     使用      ┌─────────────────┐
│  编译主程序 A    │ ──────────► │  评判程序 B      │
│                 │              │  (Zero-Shot)    │
└─────────────────┘              └─────────────────┘
                                         │
                                         │ Zero-Shot 模式
                                         │ 不需要预先编译
                                         ▼
                                 ┌─────────────────┐
                                 │  直接使用       │
                                 │  Signature 中的 │
                                 │  instructions   │
                                 └─────────────────┘

优点:
1. 无需预先准备编译好的评判程序
2. 简化工作流程
3. 对于简单的评判任务，zero-shot 效果已经足够
4. 如果需要更高质量的评判，可以:
   - 先单独编译评判程序
   - 然后设置 use_compiled_judge=True
```

## 三种指标类型对比

| 指标类型 | 实现方式 | 返回值 | 适用场景 | 成本 |
|---------|---------|--------|---------|------|
| Exact Match | 字符串精确比较 | 0 或 1 | 分类、固定答案 | 无 |
| Cosine Similarity | OpenAI Embedding + 向量计算 | 0.0 ~ 1.0 | 语义相似度 | API 调用 |
| LLM-as-a-Judge | LLM 评判程序 | 0.0 ~ 1.0 | 复杂质量评估 | API 调用 |
