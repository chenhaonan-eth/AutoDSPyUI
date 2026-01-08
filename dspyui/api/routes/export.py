"""
数据导出路由

INPUT:  FastAPI, dspyui.api.schemas, dspyui.core.data_exporter, dspyui.api.dependencies
OUTPUT: GET /export 端点
POS:    导出 API 端点，处理高质量训练数据导出，支持 CSV/JSON 流式响应

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import logging
from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from dspyui.api.dependencies import get_data_exporter
from dspyui.core.data_exporter import DataExporter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/export")
async def export_data(
    model: str = Query(..., description="模型名称"),
    rating: Literal["thumbs_up", "thumbs_down"] = Query("thumbs_up", description="反馈评分过滤"),
    format: Literal["csv", "json"] = Query("csv", description="导出格式"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    limit: int = Query(1000, le=10000, ge=1, description="最大导出数量"),
    data_exporter: DataExporter = Depends(get_data_exporter)
) -> StreamingResponse:
    """
    导出高质量训练数据
    
    从 MLflow 查询带有指定反馈评分的 traces，并导出为训练数据格式。
    支持按日期范围过滤，以及 CSV/JSON 格式导出。
    
    Args:
        model: 模型名称
        rating: 反馈评分过滤条件 (thumbs_up/thumbs_down)
        format: 导出格式 (csv/json)
        start_date: 开始日期过滤
        end_date: 结束日期过滤
        limit: 最大导出数量
        data_exporter: 数据导出器（依赖注入）
        
    Returns:
        StreamingResponse: 流式响应，包含导出数据
        
    Raises:
        HTTPException: 500 导出失败
    """
    logger.info(
        f"导出请求: model={model}, rating={rating}, format={format}, "
        f"start_date={start_date}, end_date={end_date}, limit={limit}"
    )
    
    try:
        # 1. 查询带反馈的 traces
        traces_df = data_exporter.query_traces_with_feedback(
            model_name=model,
            rating=rating,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        logger.info(f"查询到 {len(traces_df)} 条 traces")
        
        # 2. 设置响应头
        if format == "csv":
            media_type = "text/csv"
            filename = f"{model}_training_data_{rating}.csv"
        else:
            media_type = "application/json"
            filename = f"{model}_training_data_{rating}.json"
        
        # 3. 流式导出
        def generate_stream():
            """生成流式数据"""
            for chunk in data_exporter.export_streaming(
                traces_df=traces_df,
                format=format,
                use_corrected_output=True,
                chunk_size=100
            ):
                yield chunk
        
        return StreamingResponse(
            generate_stream(),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Total-Records": str(len(traces_df)),
            }
        )
        
    except Exception as e:
        logger.error(f"导出失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"导出失败: {str(e)}"
        )
