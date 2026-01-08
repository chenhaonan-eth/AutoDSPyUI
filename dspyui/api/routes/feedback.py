"""
反馈路由

INPUT:  FastAPI, dspyui.api.schemas, dspyui.core.feedback, dspyui.api.dependencies
OUTPUT: POST /feedback 端点
POS:    反馈 API 端点，处理用户反馈提交，集成 FeedbackService

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from dspyui.api.dependencies import get_feedback_service
from dspyui.api.schemas import FeedbackRequest, FeedbackResponse
from dspyui.core.feedback import FeedbackService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    feedback_service: FeedbackService = Depends(get_feedback_service)
) -> FeedbackResponse:
    """
    提交用户反馈
    
    将用户反馈（评分、修正输出、评论）与推理 trace 关联。
    使用 MLflow log_feedback API 记录反馈数据。
    
    Args:
        request: 反馈请求，包含 trace_id、评分和可选的修正输出
        feedback_service: 反馈服务（依赖注入）
        
    Returns:
        FeedbackResponse: 反馈提交结果
        
    Raises:
        HTTPException: 404 trace_id 不存在，400 无效请求
    """
    logger.info(f"收到反馈请求: trace_id={request.trace_id}, rating={request.rating}")
    
    try:
        # 1. 验证 trace_id 是否存在
        # 注意：对于降级模式生成的 trace_id (degraded-xxx)，跳过验证
        if not request.trace_id.startswith("degraded-"):
            trace_exists = feedback_service.validate_trace_exists(request.trace_id)
            if not trace_exists:
                logger.warning(f"Trace 不存在: {request.trace_id}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Trace '{request.trace_id}' 不存在"
                )
        
        # 2. 记录反馈
        feedback_id = feedback_service.record_feedback(
            trace_id=request.trace_id,
            rating=request.rating,
            corrected_output=request.corrected_output,
            comment=request.comment,
            user_id=request.user_id
        )
        
        logger.info(f"反馈记录成功: feedback_id={feedback_id}")
        
        return FeedbackResponse(
            status="success",
            feedback_id=feedback_id
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        # 无效的 rating 等参数错误
        logger.warning(f"反馈参数无效: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"反馈提交失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"反馈提交失败: {str(e)}"
        )
