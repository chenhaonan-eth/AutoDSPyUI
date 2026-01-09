# DSPy 核心功能测试

本目录包含 autodspy.dspy_core 模块的测试用例。

## 文件清单

| 文件名 | 层级定位 | 核心功能 |
|--------|----------|----------|
| `__init__.py` | 模块初始化 | 标识测试包 |
| `test_signatures.py` | 单元测试 | 测试 Signature 创建 ✅ |
| `test_modules.py` | 单元测试 | 测试 Module 定义（待创建）|
| `test_metrics.py` | 单元测试 | 测试评估指标（待创建）|
| `test_compiler.py` | 集成测试 | 测试编译逻辑（待创建）|
| `test_runner.py` | 集成测试 | 测试程序执行（待创建）|

## 测试覆盖

### Signatures
- ✅ 简单 Signature 创建
- ✅ 多输入/输出字段
- ✅ 字段描述
- ✅ 输入验证

### Modules（待实现）
- 模块类型选择
- 参数配置
- 模块实例化

### Metrics（待实现）
- 精确匹配
- 余弦相似度
- LLM Judge
- 自定义指标

### Compiler（待实现）
- 优化器选择
- 编译流程
- 评估集成

### Runner（待实现）
- 单条推理
- 批量推理
- 错误处理
