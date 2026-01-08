"""
Pydantic 数据模型定义

INPUT:  pydantic
OUTPUT: Request/Response 模型 (PredictRequest, FeedbackRequest, etc.)
POS:    API 数据验证层，定义所有请求和响应的数据结构

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ============================================================
# Predict 相关模型
# ============================================================

class PredictRequest(BaseModel):
    """推理请求"""
    model: str = Field(..., description="模型名称")
    inputs: Dict[str, Any] = Field(..., description="输入字段")
    version: Optional[str] = Field(None, description="指定版本号")
    stage: str = Field("Production", description="模型阶段")


class PredictResponse(BaseModel):
    """推理响应"""
    result: Dict[str, Any] = Field(..., description="输出字段")
    trace_id: str = Field(..., description="用于反馈关联的追踪 ID")
    model_version: str = Field(..., description="实际使用的模型版本")
    latency_ms: float = Field(..., description="推理耗时（毫秒）")


# ============================================================
# Feedback 相关模型
# ============================================================

class FeedbackRequest(BaseModel):
    """反馈请求"""
    trace_id: str = Field(..., description="关联的追踪 ID")
    rating: Literal["thumbs_up", "thumbs_down"] = Field(..., description="评分")
    corrected_output: Optional[Dict[str, Any]] = Field(None, description="修正后的输出")
    comment: Optional[str] = Field(None, description="评论")
    user_id: Optional[str] = Field(None, description="用户 ID")


class FeedbackResponse(BaseModel):
    """反馈响应"""
    status: str = Field(..., description="状态")
    feedback_id: str = Field(..., description="反馈 ID")


# ============================================================
# Models 相关模型
# ============================================================

class ModelInfo(BaseModel):
    """模型信息"""
    name: str = Field(..., description="模型名称")
    latest_version: str = Field(..., description="最新版本")
    current_stage: str = Field(..., description="当前阶段")
    description: Optional[str] = Field(None, description="描述")
    evaluation_score: Optional[float] = Field(None, description="评估分数")
    tags: Dict[str, str] = Field(default_factory=dict, description="标签")


class ModelVersion(BaseModel):
    """模型版本信息"""
    version: str = Field(..., description="版本号")
    stage: str = Field(..., description="阶段")
    created_at: datetime = Field(..., description="创建时间")
    evaluation_score: Optional[float] = Field(None, description="评估分数")
    run_id: Optional[str] = Field(None, description="关联的运行 ID")


class StageTransitionRequest(BaseModel):
    """阶段切换请求"""
    version: str = Field(..., description="版本号")
    stage: Literal["Staging", "Production", "Archived"] = Field(..., description="目标阶段")


# ============================================================
# Health 相关模型
# ============================================================

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    mlflow_connected: bool = Field(..., description="MLflow 连接状态")
    loaded_models_count: int = Field(..., description="已加载模型数量")
    uptime_seconds: float = Field(..., description="服务运行时间（秒）")


class MetricsResponse(BaseModel):
    """指标响应"""
    request_count: int = Field(..., description="请求总数")
    error_count: int = Field(..., description="错误总数")
    average_latency_ms: float = Field(..., description="平均延迟（毫秒）")
    models_served: List[str] = Field(default_factory=list, description="已服务的模型列表")


# ============================================================
# Export 相关模型
# ============================================================

class ExportParams(BaseModel):
    """导出参数"""
    model: str = Field(..., description="模型名称")
    rating: Literal["thumbs_up", "thumbs_down"] = Field("thumbs_up", description="反馈评分过滤")
    format: Literal["csv", "json"] = Field("csv", description="导出格式")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    limit: int = Field(1000, le=10000, description="最大导出数量")


# ============================================================
# 错误响应模型
# ============================================================

class ErrorResponse(BaseModel):
    """错误响应"""
    detail: str = Field(..., description="错误详情")
    trace_id: Optional[str] = Field(None, description="追踪 ID（如果可用）")
