# API 路由模块

⚠️ 一旦我所属的文件夹有所变化，请更新我。

## 文件清单

| 文件 | 地位 | 功能 |
|------|------|------|
| `__init__.py` | 模块入口 | 导出所有路由 |
| `predict.py` | 核心路由 | POST /predict 推理端点 |
| `feedback.py` | 核心路由 | POST /feedback 反馈端点 |
| `export.py` | 核心路由 | GET /export 数据导出端点 |
| `models.py` | 核心路由 | 模型管理端点 (GET /models, GET /models/{name}/versions, POST /models/{name}/stage) |
| `health.py` | 辅助路由 | GET /health, GET /metrics 健康检查端点 |

## 依赖关系

```
routes/
├── predict.py    → ModelManager, MLflow tracing
├── feedback.py   → FeedbackService
├── export.py     → DataExporter
├── models.py     → MLflow Model Registry, ModelManager
└── health.py     → ModelManager, MLflow
```
