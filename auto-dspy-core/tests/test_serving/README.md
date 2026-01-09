# Serving 功能测试

本目录包含 autodspy.serving 模块的测试用例。

## 文件清单

| 文件名 | 层级定位 | 核心功能 |
|--------|----------|----------|
| `__init__.py` | 模块初始化 | 标识测试包 |
| `test_model_manager.py` | 单元测试 | 测试模型管理器和缓存 |
| `test_feedback.py` | 单元测试 | 测试反馈服务 |
| `test_data_exporter.py` | 单元/集成测试 | 测试数据导出功能 |

## 测试覆盖

### ModelManager
- ✅ 模型加载（按版本/阶段）
- ✅ 缓存命中和失效
- ✅ 缓存统计
- ✅ 多版本隔离

### FeedbackService
- ✅ 反馈提交
- ✅ 反馈查询
- ✅ 评分验证
- ✅ 修正输出处理

### DataExporter
- ✅ 追踪数据导出
- ✅ 数据扁平化
- ✅ 格式转换（JSON/CSV/Excel）
- ✅ 修正输出优先级
