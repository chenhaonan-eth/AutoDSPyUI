# DSPyUI API 模块

API 服务层，基于 FastAPI 提供 REST 接口。

⚠️ 一旦我所属的文件夹有所变化，请更新我。

## 文件清单

| 文件 | 功能 | 地位 |
|------|------|------|
| `__init__.py` | 模块入口，导出 create_app | 入口 |
| `app.py` | FastAPI 应用入口，lifespan 管理，超时中间件，全局异常处理 | 核心 |
| `schemas.py` | Pydantic 数据模型定义 | 数据层 |
| `dependencies.py` | 依赖注入函数 | 依赖管理 |
| `routes/` | API 路由子目录 | 路由层 |

## 全局异常处理

| 异常类型 | 处理器 | HTTP 状态码 | 说明 |
|----------|--------|-------------|------|
| `HTTPException` | `http_exception_handler` | 原状态码 | 处理 FastAPI HTTPException，支持 trace_id |
| `StarletteHTTPException` | `starlette_http_exception_handler` | 原状态码 | 处理 Starlette 中间件异常（如 404 路由不存在） |
| `RequestValidationError` | `validation_exception_handler` | 400 | 请求体验证失败 |
| `Exception` | `generic_exception_handler` | 500 | 未捕获的通用异常 |

### 错误响应格式

所有错误响应遵循统一的 `ErrorResponse` 格式：

```json
{
  "detail": "错误描述信息",
  "trace_id": "可选的追踪 ID"
}
```

## 中间件

| 中间件 | 功能 | 配置 |
|--------|------|------|
| `TimeoutMiddleware` | 请求超时控制，超时返回 504 | `API_REQUEST_TIMEOUT` 环境变量（默认 60 秒） |

## routes/ 子目录

| 文件 | 功能 | 端点 |
|------|------|------|
| `__init__.py` | 路由模块入口 | - |
| `predict.py` | 推理路由 | POST /predict |
| `feedback.py` | 反馈路由 | POST /feedback |
| `export.py` | 导出路由 | GET /export |
| `models.py` | 模型管理路由 | GET/POST /models/* |
| `health.py` | 健康检查路由 | GET /health, /metrics |
