"""
推理路由

INPUT:  FastAPI, dspyui.api.schemas, dspyui.core.model_manager, dspyui.api.dependencies, MLflow
OUTPUT: POST /predict 端点
POS:    推理 API 端点，处理模型推理请求，集成 ModelManager 和 MLflow tracing

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import logging
import time
import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from dspyui.api.dependencies import get_model_manager
from dspyui.api.schemas import PredictRequest, PredictResponse
from dspyui.config import MLFLOW_ENABLED
from autodspy import ModelManager

# 可选导入 MLflow
try:
    import mlflow
    MLFLOW_INSTALLED = True
except ImportError:
    mlflow = None
    MLFLOW_INSTALLED = False

# 可选导入 dspy.asyncify
try:
    import dspy
    DSPY_ASYNCIFY_AVAILABLE = hasattr(dspy, 'asyncify')
except ImportError:
    dspy = None
    DSPY_ASYNCIFY_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_current_trace_id() -> str:
    """
    获取当前 MLflow trace ID
    
    Returns:
        trace_id: 当前 trace ID，如果不可用则生成降级 ID
    """
    if MLFLOW_ENABLED and MLFLOW_INSTALLED:
        try:
            # 尝试获取当前活跃的 span
            span = mlflow.get_current_active_span()
            if span and hasattr(span, 'request_id'):
                return span.request_id
            # 备选：从 trace 上下文获取
            trace = mlflow.get_last_active_trace()
            if trace:
                return trace.info.request_id
        except Exception as e:
            logger.warning(f"获取 trace_id 失败: {e}")
    
    # 降级：生成本地 trace_id
    return f"degraded-{uuid.uuid4().hex[:16]}"


def _extract_result(output: Any) -> Dict[str, Any]:
    """
    从 DSPy 程序输出中提取结果字典
    
    Args:
        output: DSPy 程序输出（可能是 Prediction 对象或字典）
        
    Returns:
        结果字典
    """
    if output is None:
        return {}
    
    # 如果已经是字典，直接返回
    if isinstance(output, dict):
        return output
    
    # DSPy Prediction 对象转换
    if hasattr(output, 'toDict'):
        return output.toDict()
    
    # 尝试获取所有属性
    if hasattr(output, '__dict__'):
        result = {}
        for key, value in output.__dict__.items():
            if not key.startswith('_'):
                result[key] = value
        return result
    
    # 最后尝试转换为字符串
    return {"output": str(output)}


@router.post("/predict", response_model=PredictResponse)
async def predict(
    request: PredictRequest,
    model_manager: ModelManager = Depends(get_model_manager)
) -> PredictResponse:
    """
    执行模型推理
    
    Args:
        request: 推理请求，包含模型名称和输入字段
        model_manager: 模型管理器（依赖注入）
        
    Returns:
        PredictResponse: 推理结果，包含输出、trace_id 和模型版本
        
    Raises:
        HTTPException: 404 模型不存在，500 推理失败
    """
    start_time = time.time()
    trace_id = None
    
    try:
        # 1. 加载模型
        logger.info(f"加载模型: {request.model}, stage={request.stage}, version={request.version}")
        
        try:
            program, model_version = model_manager.load_model(
                name=request.model,
                version=request.version,
                stage=request.stage if not request.version else None
            )
        except ValueError as e:
            error_msg = str(e)
            if "not found" in error_msg.lower() or "不存在" in error_msg:
                raise HTTPException(
                    status_code=404,
                    detail=f"模型 '{request.model}' 不存在: {error_msg}"
                )
            raise HTTPException(
                status_code=500,
                detail=f"加载模型失败: {error_msg}"
            )
        
        # 2. 执行推理（带 MLflow tracing）
        logger.info(f"执行推理: model={request.model}, version={model_version}")
        
        try:
            # 使用 MLflow tracing 包装推理
            if MLFLOW_ENABLED and MLFLOW_INSTALLED:
                # 设置 trace 标签
                with mlflow.start_span(name=f"predict_{request.model}") as span:
                    span.set_attributes({
                        "model_name": request.model,
                        "model_version": model_version,
                        "input_keys": list(request.inputs.keys()),
                    })
                    
                    # 执行推理
                    if DSPY_ASYNCIFY_AVAILABLE:
                        async_program = dspy.asyncify(program)
                        output = await async_program(**request.inputs)
                    else:
                        output = program(**request.inputs)
                    
                    # 获取 trace_id
                    trace_id = _get_current_trace_id()
            else:
                # 无 MLflow 时直接执行
                if DSPY_ASYNCIFY_AVAILABLE:
                    async_program = dspy.asyncify(program)
                    output = await async_program(**request.inputs)
                else:
                    output = program(**request.inputs)
                trace_id = _get_current_trace_id()
            
        except Exception as e:
            # 推理失败，仍然返回 trace_id
            trace_id = _get_current_trace_id()
            logger.error(f"推理失败: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"推理失败: {str(e)}",
                headers={"X-Trace-ID": trace_id}
            )
        
        # 3. 提取结果
        result = _extract_result(output)
        
        # 4. 计算延迟
        latency_ms = (time.time() - start_time) * 1000
        
        logger.info(f"推理完成: trace_id={trace_id}, latency={latency_ms:.2f}ms")
        
        return PredictResponse(
            result=result,
            trace_id=trace_id,
            model_version=model_version,
            latency_ms=latency_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        trace_id = trace_id or _get_current_trace_id()
        logger.error(f"预测端点错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"内部错误: {str(e)}",
            headers={"X-Trace-ID": trace_id}
        )
