# docs 文件夹

项目文档集合，包含流程说明和操作指南。

⚠️ 一旦我所属的文件夹有所变化，请更新我。

## 文件清单

| 文件 | 功能 | 说明 |
|------|------|------|
| `create_metric_flow.md` | 流程文档 | 评估指标创建流程详解，包含 LLM-as-a-Judge 实现细节 |
| `data_recycling_guide.md` | 操作指南 | 数据回收再利用实操指南，包含完整工作流和脚本使用说明 |
| `optimizer_dataset_requirements.md` | 参考文档 | 各优化器数据集数量需求，选型建议 |
| `mlflow_integration.md` | 集成指南 | MLflow 实验追踪和模型管理集成说明 |
| `serving_and_feedback.md` | 部署方案 | 模型部署、推理服务、用户反馈和数据飞轮闭环方案 |

## 文档索引

### 核心流程
- [评估指标创建流程](create_metric_flow.md) - 了解 Exact Match / Cosine Similarity / LLM-as-a-Judge 的实现

### 操作指南
- [数据回收再利用指南](data_recycling_guide.md) - 如何将预测数据回收用于持续优化

### 集成指南
- [MLflow 集成指南](mlflow_integration.md) - 实验追踪、模型注册和程序生命周期管理

### 部署方案
- [模型部署与数据飞轮](serving_and_feedback.md) - 推理服务、用户反馈收集和数据飞轮闭环
