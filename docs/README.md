# docs 文件夹

项目文档集合，包含流程说明和操作指南。

⚠️ 一旦我所属的文件夹有所变化，请更新我。

## 文件清单

| 文件 | 功能 | 说明 |
|------|------|------|
| `architecture.md` | 系统架构 | DSPyUI 整体系统架构说明（UML 图、类图、流程图） |
| `create_metric_flow.md` | 流程文档 | 评估指标创建流程详解，包含 LLM-as-a-Judge 实现细节 |
| `mlflow_integration.md` | 集成指南 | MLflow 实验追踪和模型管理完整指南（包含 Docker 部署、迁移指南） |
| `optimizer_dataset_requirements.md` | 参考文档 | 各优化器数据集数量需求，选型建议 |
| `serving_and_feedback.md` | 部署方案 | 模型部署、推理服务、用户反馈和数据飞轮闭环方案 |
| `training_tutorial_zh.md` | 教程文档 | 端到端训练（编译）教程，从任务定义到程序测试 |

## 文档索引

### 快速开始
- [端到端训练教程](training_tutorial_zh.md) - 从零开始使用 DSPyUI 编译和测试程序

### 核心概念
- [系统架构](architecture.md) - 理解 DSPyUI 的整体设计和模块依赖
- [评估指标创建流程](create_metric_flow.md) - 了解 Exact Match / Cosine Similarity / LLM-as-a-Judge 的实现
- [优化器数据集需求](optimizer_dataset_requirements.md) - 选择合适的优化器和准备数据

### 集成与部署
- [MLflow 集成指南](mlflow_integration.md) - 实验追踪、模型注册、Docker 部署和迁移指南
- [模型部署与数据飞轮](serving_and_feedback.md) - 推理服务、用户反馈收集和数据飞轮闭环
