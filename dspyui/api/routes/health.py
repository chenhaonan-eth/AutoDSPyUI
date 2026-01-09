"""
健康检查路由

INPUT:  FastAPI, dspyui.api.schemas, dspyui.api.dependencies, MLflow
OUTPUT: GET /health, GET /metrics 端点
POS:    健康检查 API 端点，提供服务状态和监控指标

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import logging
import time
from typing import Dict, List

from fastapi import APIRouter, Depends, Request

from dspyui.api.dependencies import get_model_manager
from dspyui.api.schemas import HealthResponse, MetricsResponse
from dspyui.config import MLFLOW_ENABLED
from autodspy import ModelManager

# 可选导入 MLflow
try:
    import mlflow
    MLFLOW_INSTALLED = True
except ImportError:
    mlflow = None
    MLFLOW_INSTALLED = False

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局指标存储（简单实现，生产环境应使用 Prometheus 等）
_metrics: Dict[str, float] = {
    "request_count": 0,
    "error_count": 0,
    "total_latency_ms": 0.0,
}
_models_served: List[str] = []
_start_time: float = time.time()


def record_request(model_name: str = None, latency_ms: float = 0.0, is_error: bool = False):
    """
    记录请求指标
    
    Args:
        model_name: 模型名称（可选）
        latency_ms: 请求延迟（毫秒）
        is_error: 是否为错误请求
    """
    global _metrics, _models_served
    
    _metrics["request_count"] += 1
    _metrics["total_latency_ms"] += latency_ms
    
    if is_error:
        _metrics["error_count"] += 1
    
    if model_name and model_name not in _models_served:
        _models_served.append(model_name)


def _check_mlflow_connection() -> bool:
    """
    检查 MLflow 连接状态
    
    Returns:
        True 如果连接正常，否则 False
    """
    if not MLFLOW_ENABLED or not MLFLOW_INSTALLED:
        return False
    
    try:
        # 尝试获取 tracking URI 来验证连接
        uri = mlflow.get_tracking_uri()
        
        # 如果是远程 URI，尝试简单的 API 调用
        if uri.startswith("http"):
            from mlflow import MlflowClient
            client = MlflowClient()
            # 尝试列出实验（轻量级操作）
            client.search_experiments(max_results=1)
        
        return True
    except Exception as e:
        logger.warning(f"MLflow 连接检查失败: {e}")
        return False


@router.get("/health", response_model=HealthResponse)
async def health_check(
    request: Request,
    model_manager: ModelManager = Depends(get_model_manager)
) -> HealthResponse:
    """
    健康检查
    
    返回服务健康状态，包括 MLflow 连接状态和已加载模型数量。
    
    Args:
        request: FastAPI 请求对象
        model_manager: 模型管理器（依赖注入）
        
    Returns:
        HealthResponse: 服务健康状态
    """
    # 检查 MLflow 连接
    mlflow_connected = _check_mlflow_connection()
    
    # 获取已加载模型数量
    cache_stats = model_manager.get_cache_stats()
    loaded_models_count = cache_stats.get("cached_models", 0)
    
    # 计算运行时间
    uptime_seconds = time.time() - _start_time
    
    # 确定服务状态
    if mlflow_connected:
        status = "healthy"
    else:
        status = "degraded"  # MLflow 不可用时为降级状态
    
    return HealthResponse(
        status=status,
        mlflow_connected=mlflow_connected,
        loaded_models_count=loaded_models_count,
        uptime_seconds=uptime_seconds
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    """
    获取服务指标
    
    返回服务运行指标，包括请求数、错误数、平均延迟等。
    
    Returns:
        MetricsResponse: 服务运行指标
    """
    global _metrics, _models_served
    
    # 计算平均延迟
    request_count = int(_metrics["request_count"])
    if request_count > 0:
        average_latency_ms = _metrics["total_latency_ms"] / request_count
    else:
        average_latency_ms = 0.0
    
    return MetricsResponse(
        request_count=request_count,
        error_count=int(_metrics["error_count"]),
        average_latency_ms=average_latency_ms,
        models_served=_models_served.copy()
    )


def reset_metrics():
    """
    重置指标（用于测试）
    """
    global _metrics, _models_served, _start_time
    _metrics = {
        "request_count": 0,
        "error_count": 0,
        "total_latency_ms": 0.0,
    }
    _models_served = []
    _start_time = time.time()
