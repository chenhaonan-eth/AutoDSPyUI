"""
FastAPI 应用入口

INPUT:  dspyui.config (APIConfig), dspyui.core 模块, FastAPI, dspyui.api.routes
OUTPUT: FastAPI 应用实例, lifespan 管理, 超时中间件, 全局异常处理
POS:    API 服务主入口，负责应用初始化、路由注册和全局错误处理

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from dspyui.api.routes import (
    export_router,
    feedback_router,
    health_router,
    models_router,
    predict_router,
)
from dspyui.config import MLFLOW_ENABLED, get_api_config
from dspyui.core.data_exporter import DataExporter
from dspyui.core.feedback import FeedbackService
from dspyui.core.model_manager import ModelManager

# 可选导入
try:
    import dspy
    DSPY_INSTALLED = True
except ImportError:
    dspy = None
    DSPY_INSTALLED = False

try:
    import mlflow
    MLFLOW_INSTALLED = True
except ImportError:
    mlflow = None
    MLFLOW_INSTALLED = False

logger = logging.getLogger(__name__)


# ============================================================
# 全局异常处理器
# ============================================================

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    处理 HTTPException 异常
    
    统一处理 FastAPI 抛出的 HTTP 异常，返回标准化的 ErrorResponse 格式。
    支持从 headers 中提取 trace_id。
    
    Args:
        request: 请求对象
        exc: HTTP 异常
        
    Returns:
        JSONResponse: 标准化错误响应
    """
    # 尝试从异常 headers 中获取 trace_id
    trace_id = None
    if hasattr(exc, 'headers') and exc.headers:
        trace_id = exc.headers.get("X-Trace-ID")
    
    content = {"detail": exc.detail}
    if trace_id:
        content["trace_id"] = trace_id
    
    logger.warning(
        f"HTTP {exc.status_code}: {exc.detail} "
        f"[{request.method} {request.url.path}]"
        f"{f' trace_id={trace_id}' if trace_id else ''}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=content
    )


async def starlette_http_exception_handler(
    request: Request, 
    exc: StarletteHTTPException
) -> JSONResponse:
    """
    处理 Starlette HTTPException 异常
    
    处理来自 Starlette 中间件的 HTTP 异常（如 404 路由不存在）。
    
    Args:
        request: 请求对象
        exc: Starlette HTTP 异常
        
    Returns:
        JSONResponse: 标准化错误响应
    """
    logger.warning(
        f"HTTP {exc.status_code}: {exc.detail} "
        f"[{request.method} {request.url.path}]"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail)}
    )


async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """
    处理请求验证异常
    
    当请求体不符合 Pydantic 模型定义时触发。
    返回 400 Bad Request 和详细的验证错误信息。
    
    Args:
        request: 请求对象
        exc: 验证异常
        
    Returns:
        JSONResponse: 400 错误响应，包含验证错误详情
    """
    # 格式化验证错误信息
    errors = exc.errors()
    error_messages = []
    for error in errors:
        loc = " -> ".join(str(l) for l in error.get("loc", []))
        msg = error.get("msg", "Unknown error")
        error_messages.append(f"{loc}: {msg}")
    
    detail = f"Validation error: {'; '.join(error_messages)}"
    
    logger.warning(
        f"Validation error [{request.method} {request.url.path}]: {detail}"
    )
    
    return JSONResponse(
        status_code=400,
        content={"detail": detail}
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理未捕获的通用异常
    
    作为最后的异常处理器，捕获所有未被其他处理器处理的异常。
    返回 500 Internal Server Error。
    
    Args:
        request: 请求对象
        exc: 异常
        
    Returns:
        JSONResponse: 500 错误响应
    """
    logger.error(
        f"Unhandled exception [{request.method} {request.url.path}]: {exc}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    请求超时中间件
    
    当请求处理时间超过配置的超时阈值时，返回 504 Gateway Timeout 错误。
    """
    
    def __init__(self, app: FastAPI, timeout_seconds: int = 60):
        """
        初始化超时中间件
        
        Args:
            app: FastAPI 应用实例
            timeout_seconds: 超时时间（秒），默认 60 秒
        """
        super().__init__(app)
        self.timeout_seconds = timeout_seconds
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        处理请求，添加超时控制
        
        Args:
            request: 请求对象
            call_next: 下一个处理函数
            
        Returns:
            Response: 响应对象，超时时返回 504 错误
        """
        try:
            # 使用 asyncio.wait_for 添加超时控制
            response = await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout_seconds
            )
            return response
        except asyncio.TimeoutError:
            # 超时时返回 504 Gateway Timeout
            logger.warning(
                f"Request timeout after {self.timeout_seconds}s: "
                f"{request.method} {request.url.path}"
            )
            return JSONResponse(
                status_code=504,
                content={
                    "detail": f"Request timeout after {self.timeout_seconds}s"
                }
            )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    应用生命周期管理
    
    Startup:
    - 配置 DSPy LM
    - 配置 MLflow tracking
    - 初始化 ModelManager, FeedbackService, DataExporter
    
    Shutdown:
    - 清理资源
    """
    config = get_api_config()
    logger.info("API 服务启动中...")
    
    # === Startup ===
    
    # 1. 配置 DSPy
    if DSPY_INSTALLED:
        try:
            lm = dspy.LM(config.default_lm)
            dspy.configure(lm=lm, async_max_workers=config.async_workers)
            logger.info(f"DSPy 配置完成: lm={config.default_lm}, async_workers={config.async_workers}")
        except Exception as e:
            logger.warning(f"DSPy 配置失败: {e}")
    
    # 2. 配置 MLflow
    if MLFLOW_ENABLED and MLFLOW_INSTALLED:
        try:
            mlflow.set_tracking_uri(config.mlflow_tracking_uri)
            # 启用 DSPy autolog
            mlflow.dspy.autolog(log_traces=True)
            logger.info(f"MLflow 配置完成: tracking_uri={config.mlflow_tracking_uri}")
        except Exception as e:
            logger.warning(f"MLflow 配置失败: {e}")
    
    # 3. 初始化核心服务
    app.state.model_manager = ModelManager(
        cache_enabled=config.model_cache_enabled,
        cache_ttl=config.model_cache_ttl
    )
    logger.info("ModelManager 初始化完成")
    
    app.state.feedback_service = FeedbackService(
        feedback_enabled=config.feedback_enabled
    )
    logger.info("FeedbackService 初始化完成")
    
    app.state.data_exporter = DataExporter()
    logger.info("DataExporter 初始化完成")
    
    logger.info("API 服务启动完成")
    
    yield
    
    # === Shutdown ===
    logger.info("API 服务关闭中...")
    
    # 清理模型缓存
    if hasattr(app.state, 'model_manager'):
        app.state.model_manager.invalidate_all()
    
    logger.info("API 服务已关闭")


def create_app() -> FastAPI:
    """
    创建并配置 FastAPI 应用实例
    
    Returns:
        FastAPI: 配置好的应用实例
    """
    config = get_api_config()
    
    app = FastAPI(
        title="DSPyUI Serving API",
        description="DSPy 程序推理服务 API，支持模型部署、用户反馈收集和数据导出",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # 注册全局异常处理器
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    # 添加超时中间件
    app.add_middleware(
        TimeoutMiddleware,
        timeout_seconds=config.api_request_timeout
    )
    
    # 注册路由
    app.include_router(predict_router, tags=["Inference"])
    app.include_router(feedback_router, tags=["Feedback"])
    app.include_router(export_router, tags=["Export"])
    app.include_router(models_router, tags=["Models"])
    app.include_router(health_router, tags=["Health"])
    
    return app


# 默认应用实例
app = create_app()
