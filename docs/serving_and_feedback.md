# 模型部署与数据飞轮方案

本文档描述 DSPyUI 的模型部署、推理服务、用户反馈收集和数据飞轮闭环方案。

## 快速开始

### 启动 API 服务

```bash
# 方式一：仅启动 API 服务（推荐用于生产）
bash webui.sh --api-only

# 方式二：同时启动 Gradio UI 和 API 服务
bash webui.sh --api

# 方式三：直接使用 Python 启动
uv run python serve.py

# 方式四：使用 uvicorn 启动（支持更多配置）
uv run uvicorn dspyui.api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### 验证服务状态

```bash
# 健康检查
curl http://localhost:8000/health

# 查看 API 文档
open http://localhost:8000/docs
```

## 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        数据飞轮闭环                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│   │  训练    │───▶│  注册    │───▶│  部署    │───▶│  推理    │ │
│   │ Compile  │    │ Registry │    │  Serve   │    │ Predict  │ │
│   └──────────┘    └──────────┘    └──────────┘    └────┬─────┘ │
│        ▲                                               │       │
│        │                                               ▼       │
│   ┌────┴─────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│   │ 数据导出 │◀───│  评估    │◀───│  存储    │◀───│  反馈    │ │
│   │  Export  │    │ Evaluate │    │ MLflow   │    │ 👍👎💬   │ │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## MLflow 全能力利用

| MLflow 能力 | 应用场景 | API |
|------------|---------|-----|
| Dataset Tracking | 训练数据版本管理 | `mlflow.log_input()`, `mlflow.data.from_pandas()` |
| Experiment Tracking | 编译参数/指标记录 | `mlflow.log_param()`, `mlflow.log_metric()` |
| Model Registry | 模型版本管理 | `mlflow.register_model()` |
| Model Serving | 部署推理服务 | `mlflow models serve` |
| Tracing | 推理请求追踪 | `mlflow.start_span()`, 自动追踪 |
| Feedback/Assessment | 用户反馈收集 | `mlflow.log_feedback()` |
| GenAI Evaluate | 基于反馈评估 | `mlflow.genai.evaluate()` |

---

## 1. 模型部署

### 1.1 部署方式

#### 方式一：FastAPI 部署（推荐）

DSPyUI 内置了完整的 FastAPI 服务，支持异步高并发：

```bash
# 启动 API 服务
uv run python serve.py

# 或使用 webui.sh
bash webui.sh --api-only
```

服务启动后可访问：
- API 端点: http://localhost:8000
- Swagger 文档: http://localhost:8000/docs
- ReDoc 文档: http://localhost:8000/redoc

#### 方式二：MLflow Model Serving

标准化部署，支持 Docker/Kubernetes：

```bash
# 本地部署
mlflow models serve -m "models:/joke-generator@Production" -p 6000

# 构建 Docker 镜像
mlflow models build-docker -m "models:/joke-generator/3" -n "dspy-program"

# 调用
curl -X POST http://localhost:6000/invocations \
  -H "Content-Type: application/json" \
  -d '{"inputs": {"topic": "猫"}}'
```

### 1.2 API 端点一览

| 端点 | 方法 | 描述 |
|------|------|------|
| `/predict` | POST | 执行模型推理 |
| `/feedback` | POST | 提交用户反馈 |
| `/export` | GET | 导出训练数据 |
| `/models` | GET | 列出所有模型 |
| `/models/{name}/versions` | GET | 列出模型版本 |
| `/models/{name}/stage` | POST | 切换模型阶段 |
| `/health` | GET | 健康检查 |
| `/metrics` | GET | 服务指标 |

---

## 2. 模型版本切换

### 2.1 切换策略

#### 基于版本号（精确控制）

```python
model_uri = "models:/joke-generator/3"  # 指定版本 3
```

#### 基于阶段（推荐生产使用）

```python
model_uri = "models:/joke-generator@Production"  # 生产版本
model_uri = "models:/joke-generator@Staging"     # 测试版本
```

#### 基于别名（MLflow 2.x）

```python
# 设置别名
client.set_registered_model_alias("joke-generator", "champion", "3")

# 使用别名
model_uri = "models:/joke-generator@champion"
```

### 2.2 阶段流转

```
None → Staging → Production → Archived
       (测试)     (生产)       (归档)
```

切换方式：
- **MLflow UI**：Models → 选择版本 → Stage 下拉框
- **API 调用**：`POST /models/{name}/stage`
- **CLI**：`mlflow models transition-stage`

### 2.3 切换流程示例

```
T1: Version 3 @ Production (线上服务)
    ↓
T2: 训练完成 Version 4，注册为 None
    ↓
T3: 测试通过，Version 4 → Staging
    ↓
T4: 验证 OK，Version 4 → Production (Version 3 自动归档)
    ↓
T5: 下一次请求自动使用 Version 4 (无需重启！)
```

---

## 3. 用户反馈收集

### 3.1 存储位置

反馈直接存入 **MLflow Tracking Store**，与 Trace 关联：

```
mlruns/
├── experiments/{experiment_id}/{run_id}/
│   └── traces/{trace_id}/
│       ├── spans/           # 调用链
│       └── assessments/     # 反馈数据 ✨
│           ├── user_rating
│           ├── corrected_output
│           └── comment
```

### 3.2 反馈 API

```
POST /feedback
  请求: {
    "trace_id": "xxx",
    "rating": "thumbs_up",           # thumbs_up / thumbs_down
    "corrected_output": "...",       # 可选：用户修正
    "comment": "很有趣"              # 可选：评论
  }
```

### 3.3 反馈类型

| 类型 | 字段 | 说明 |
|------|------|------|
| 评分 | `user_rating` | thumbs_up / thumbs_down |
| 修正 | `corrected_output` | 用户提供的正确输出 |
| 评论 | `comment` | 文字反馈 |

### 3.4 代码实现

```python
import mlflow
from mlflow.entities import AssessmentSource, AssessmentSourceType

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    # 记录用户评分
    mlflow.log_feedback(
        trace_id=request.trace_id,
        name="user_rating",
        value=request.rating,
        source=AssessmentSource(
            source_type=AssessmentSourceType.HUMAN,
            source_id=request.user_id or "anonymous"
        )
    )
    
    # 记录用户修正（如果有）
    if request.corrected_output:
        mlflow.log_feedback(
            trace_id=request.trace_id,
            name="corrected_output",
            value=request.corrected_output,
            source=AssessmentSource(source_type=AssessmentSourceType.HUMAN)
        )
    
    # 记录评论（如果有）
    if request.comment:
        mlflow.log_feedback(
            trace_id=request.trace_id,
            name="comment",
            value=request.comment,
            source=AssessmentSource(source_type=AssessmentSourceType.HUMAN)
        )
    
    return {"status": "success"}
```

---

## 4. 数据导出与飞轮闭环

### 4.1 导出高质量数据

```python
@app.get("/export")
async def export_training_data(
    model_name: str,
    rating: str = "thumbs_up",
    format: str = "csv"
):
    # 查询带正向反馈的 traces
    traces_df = mlflow.search_traces(
        filter_string=f"assessments.name = 'user_rating' AND assessments.value = '{rating}'"
    )
    
    # 转换为训练数据格式
    training_data = []
    for _, trace in traces_df.iterrows():
        # 优先使用用户修正，否则用原始输出
        corrected = get_assessment_value(trace, "corrected_output")
        training_data.append({
            **trace.inputs,
            **{k: corrected.get(k) or v for k, v in trace.outputs.items()}
        })
    
    df = pd.DataFrame(training_data)
    
    if format == "csv":
        return Response(df.to_csv(index=False), media_type="text/csv")
    else:
        return df.to_dict(orient="records")
```

### 4.2 数据飞轮流程

```
1. 部署模型 → 用户使用
2. 收集反馈 → 存入 MLflow
3. 导出数据 → 过滤高质量样本
4. 重新训练 → 使用 DSPyUI Compile
5. 注册新版 → 提升到 Production
6. 循环迭代
```

### 4.3 导出 API

```
GET /export?model=joke-generator&rating=thumbs_up&format=csv

响应: CSV 文件，包含输入输出字段
```

---

## 5. 文件结构

```
dspyui/
├── core/
│   ├── serving.py       # 推理服务核心逻辑
│   ├── feedback.py      # 反馈收集（封装 mlflow.log_feedback）
│   └── model_manager.py # 模型加载和版本管理
├── api/
│   ├── __init__.py
│   ├── app.py           # FastAPI 应用
│   ├── schemas.py       # Pydantic 模型
│   └── routes/
│       ├── predict.py   # 推理路由
│       ├── models.py    # 模型管理路由
│       ├── feedback.py  # 反馈路由
│       └── export.py    # 数据导出路由
serve.py                 # API 服务入口
```

---

## 6. 环境变量

在 `.env` 中添加：

```bash
# API 服务配置
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# 模型默认配置
DEFAULT_MODEL_STAGE=Production
MODEL_CACHE_ENABLED=true

# 反馈配置
FEEDBACK_ENABLED=true
```

---

## 7. 启动服务

```bash
# 启动 API 服务
uv run python serve.py

# 或使用 uvicorn
uv run uvicorn dspyui.api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 8. 使用示例

### 8.1 完整数据飞轮流程

```bash
# 1. 启动服务（包含 MLflow）
bash webui.sh --api-only

# 2. 执行推理
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "model": "joke-generator",
    "inputs": {"topic": "猫"},
    "stage": "Production"
  }'

# 响应示例:
# {
#   "result": {"joke": "为什么猫不玩扑克？因为它总是在桌子上睡觉！"},
#   "trace_id": "tr-abc123def456",
#   "model_version": "3",
#   "latency_ms": 1234.56
# }

# 3. 提交用户反馈（正向）
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "tr-abc123def456",
    "rating": "thumbs_up",
    "comment": "很有趣的笑话！"
  }'

# 4. 提交用户反馈（负向 + 修正）
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "tr-xyz789",
    "rating": "thumbs_down",
    "corrected_output": {"joke": "更好的笑话内容..."},
    "comment": "原来的不够有趣"
  }'

# 5. 导出高质量训练数据
curl "http://localhost:8000/export?model=joke-generator&rating=thumbs_up&format=csv" \
  -o training_data.csv

# 6. 查看模型列表
curl http://localhost:8000/models

# 7. 查看模型版本
curl http://localhost:8000/models/joke-generator/versions

# 8. 切换模型到 Production
curl -X POST http://localhost:8000/models/joke-generator/stage \
  -H "Content-Type: application/json" \
  -d '{"version": "4", "stage": "Production"}'

# 9. 健康检查
curl http://localhost:8000/health

# 响应示例:
# {
#   "status": "healthy",
#   "mlflow_connected": true,
#   "loaded_models_count": 2,
#   "uptime_seconds": 3600.5
# }

# 10. 查看服务指标
curl http://localhost:8000/metrics

# 响应示例:
# {
#   "request_count": 150,
#   "error_count": 3,
#   "average_latency_ms": 1456.78,
#   "models_served": ["joke-generator", "text-rewriter"]
# }
```

### 8.2 Python SDK 使用示例

```python
import requests

API_BASE = "http://localhost:8000"

# 推理
def predict(model: str, inputs: dict, stage: str = "Production"):
    response = requests.post(
        f"{API_BASE}/predict",
        json={"model": model, "inputs": inputs, "stage": stage}
    )
    return response.json()

# 提交反馈
def submit_feedback(trace_id: str, rating: str, corrected_output: dict = None, comment: str = None):
    payload = {"trace_id": trace_id, "rating": rating}
    if corrected_output:
        payload["corrected_output"] = corrected_output
    if comment:
        payload["comment"] = comment
    
    response = requests.post(f"{API_BASE}/feedback", json=payload)
    return response.json()

# 使用示例
result = predict("joke-generator", {"topic": "程序员"})
print(f"笑话: {result['result']['joke']}")
print(f"Trace ID: {result['trace_id']}")

# 用户觉得好笑，提交正向反馈
submit_feedback(result['trace_id'], "thumbs_up", comment="哈哈太真实了")
```

### 8.3 异步批量推理

```python
import asyncio
import aiohttp

async def batch_predict(inputs_list: list, model: str = "joke-generator"):
    """批量异步推理"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for inputs in inputs_list:
            task = session.post(
                "http://localhost:8000/predict",
                json={"model": model, "inputs": inputs}
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        results = [await r.json() for r in responses]
        return results

# 使用示例
topics = [{"topic": "猫"}, {"topic": "狗"}, {"topic": "程序员"}]
results = asyncio.run(batch_predict(topics))
for r in results:
    print(f"Topic: {r['result']}, Trace: {r['trace_id']}")
```

---

## 9. 优势总结

| 特性 | 说明 |
|------|------|
| 零额外存储 | 反馈直接存 MLflow，无需额外数据库 |
| 完整血缘 | trace_id 关联 输入→输出→反馈 |
| 原生查询 | 用 MLflow API 过滤高质量数据 |
| UI 可视化 | MLflow UI 直接查看反馈 |
| 动态切换 | 模型版本即时切换，无需重启 |
| 闭环迭代 | 数据飞轮自动化 |
| 异步高并发 | 支持 asyncify 和多 worker |
| 超时保护 | 可配置请求超时，防止阻塞 |
| 优雅降级 | MLflow 不可用时仍可服务 |

---

## 10. 故障排查

### 常见问题

**Q: API 服务启动失败？**
```bash
# 检查端口是否被占用
lsof -i :8000

# 检查 MLflow 连接
curl http://localhost:5001/health
```

**Q: 推理返回 404 Model not found？**
```bash
# 确认模型已注册
curl http://localhost:8000/models

# 检查模型阶段
curl http://localhost:8000/models/your-model/versions
```

**Q: 反馈提交返回 404 Trace not found？**
- 确保 trace_id 来自最近的推理响应
- 检查 MLflow 追踪是否启用 (`MLFLOW_ENABLED=true`)

**Q: 导出数据为空？**
- 确认有对应 rating 的反馈数据
- 检查日期范围过滤条件
