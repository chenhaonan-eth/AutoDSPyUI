"""
用户反馈收集服务

INPUT:  MLflow Tracing API, trace_id
OUTPUT: FeedbackService 类，提供 record_feedback(), validate_trace_exists() 方法
POS:    核心服务层，负责收集和记录用户反馈，被 API 路由层调用

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from autodspy.config import get_config

# 可选导入 MLflow
try:
    import mlflow
    from mlflow import MlflowClient
    from mlflow.entities import AssessmentSource, AssessmentSourceType
    MLFLOW_INSTALLED = True
except ImportError:
    mlflow = None
    MlflowClient = None
    AssessmentSource = None
    AssessmentSourceType = None
    MLFLOW_INSTALLED = False

# 设置日志
logger = logging.getLogger(__name__)


@dataclass
class FeedbackRecord:
    """反馈记录数据类"""
    trace_id: str
    rating: str                              # "thumbs_up" 或 "thumbs_down"
    corrected_output: Optional[Dict[str, Any]] = None
    comment: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: str = ""
    feedback_id: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not self.feedback_id:
            self.feedback_id = f"fb-{uuid.uuid4().hex[:16]}"


class FeedbackService:
    """
    用户反馈收集服务
    
    使用 MLflow 的 log_feedback API 将用户反馈与推理 trace 关联。
    支持评分（thumbs_up/thumbs_down）、修正输出和评论。
    
    Example:
        >>> service = FeedbackService()
        >>> feedback_id = service.record_feedback(
        ...     trace_id="tr-abc123",
        ...     rating="thumbs_up",
        ...     comment="Great response!"
        ... )
    """
    
    def __init__(self, feedback_enabled: bool = True):
        """
        初始化 FeedbackService
        
        Args:
            feedback_enabled: 是否启用反馈收集
        """
        self._feedback_enabled = feedback_enabled
        self._feedback_history: List[FeedbackRecord] = []  # 本地历史记录
        
        logger.info(f"FeedbackService 初始化: feedback_enabled={feedback_enabled}")
    
    def _is_available(self) -> bool:
        """检查 MLflow 是否可用"""
        return get_config().mlflow_enabled and MLFLOW_INSTALLED and self._feedback_enabled
    
    def validate_trace_exists(self, trace_id: str) -> bool:
        """
        验证 trace_id 是否存在
        
        Args:
            trace_id: MLflow trace ID
            
        Returns:
            True 如果 trace 存在，否则 False
        """
        if not self._is_available():
            logger.warning("MLflow 不可用，无法验证 trace")
            return False
        
        try:
            client = MlflowClient()
            # 使用 search_traces 查找指定的 trace
            # MLflow 的 trace_id 格式通常是 "tr-xxxx" 或纯 UUID
            traces = client.search_traces(
                experiment_ids=[],  # 搜索所有实验
                filter_string=f"trace_id = '{trace_id}'",
                max_results=1
            )
            
            if traces:
                logger.debug(f"Trace {trace_id} 存在")
                return True
            
            # 如果 search_traces 不支持 trace_id 过滤，尝试直接获取
            try:
                trace = client.get_trace(trace_id)
                if trace:
                    logger.debug(f"Trace {trace_id} 存在 (via get_trace)")
                    return True
            except Exception:
                pass
            
            logger.debug(f"Trace {trace_id} 不存在")
            return False
            
        except Exception as e:
            logger.warning(f"验证 trace 失败: {e}")
            # 如果验证失败，假设 trace 存在以允许反馈记录
            # 这是一种降级策略
            return True
    
    def record_feedback(
        self,
        trace_id: str,
        rating: str,
        corrected_output: Optional[Dict[str, Any]] = None,
        comment: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        记录用户反馈到 MLflow
        
        使用 mlflow.log_feedback() 将反馈与 trace 关联。
        支持多种反馈类型：评分、修正输出、评论。
        
        Args:
            trace_id: MLflow trace ID
            rating: 评分，"thumbs_up" 或 "thumbs_down"
            corrected_output: 用户修正的输出（可选）
            comment: 用户评论（可选）
            user_id: 用户标识（可选）
            
        Returns:
            feedback_id: 反馈记录 ID
            
        Raises:
            ValueError: 当 rating 无效时
        """
        # 验证 rating
        valid_ratings = {"thumbs_up", "thumbs_down"}
        if rating not in valid_ratings:
            raise ValueError(f"无效的 rating: {rating}，有效值为: {valid_ratings}")
        
        # 创建反馈记录
        record = FeedbackRecord(
            trace_id=trace_id,
            rating=rating,
            corrected_output=corrected_output,
            comment=comment,
            user_id=user_id
        )
        
        # 保存到本地历史
        self._feedback_history.append(record)
        
        if not self._is_available():
            logger.warning("MLflow 不可用，反馈仅保存到本地")
            return record.feedback_id
        
        try:
            # 构建 AssessmentSource
            source = AssessmentSource(
                source_type=AssessmentSourceType.HUMAN,
                source_id=user_id or "anonymous"
            )
            
            # 1. 记录评分
            rating_value = rating == "thumbs_up"  # 转换为布尔值
            mlflow.log_feedback(
                trace_id=trace_id,
                name="user_rating",
                value=rating_value,
                source=source,
                rationale=f"User feedback: {rating}",
                metadata={
                    "feedback_id": record.feedback_id,
                    "timestamp": record.timestamp,
                    "rating_type": rating
                }
            )
            logger.info(f"已记录评分反馈: trace={trace_id}, rating={rating}")
            
            # 2. 记录修正输出（如果提供）
            if corrected_output:
                mlflow.log_feedback(
                    trace_id=trace_id,
                    name="corrected_output",
                    value=json.dumps(corrected_output, ensure_ascii=False),
                    source=source,
                    rationale="User provided corrected output",
                    metadata={
                        "feedback_id": record.feedback_id,
                        "timestamp": record.timestamp
                    }
                )
                logger.info(f"已记录修正输出: trace={trace_id}")
            
            # 3. 记录评论（如果提供）
            if comment:
                mlflow.log_feedback(
                    trace_id=trace_id,
                    name="user_comment",
                    value=comment,
                    source=source,
                    rationale="User comment on the response",
                    metadata={
                        "feedback_id": record.feedback_id,
                        "timestamp": record.timestamp
                    }
                )
                logger.info(f"已记录用户评论: trace={trace_id}")
            
            return record.feedback_id
            
        except Exception as e:
            logger.error(f"记录反馈到 MLflow 失败: {e}")
            # 即使 MLflow 记录失败，也返回本地生成的 feedback_id
            return record.feedback_id
    
    def get_feedback_history(
        self,
        trace_id: Optional[str] = None,
        limit: int = 100
    ) -> List[FeedbackRecord]:
        """
        获取反馈历史记录
        
        Args:
            trace_id: 过滤指定 trace 的反馈（可选）
            limit: 返回记录数量限制
            
        Returns:
            反馈记录列表
        """
        records = self._feedback_history
        
        if trace_id:
            records = [r for r in records if r.trace_id == trace_id]
        
        # 按时间倒序排列，返回最新的记录
        records = sorted(records, key=lambda r: r.timestamp, reverse=True)
        
        return records[:limit]
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """
        获取反馈统计信息
        
        Returns:
            统计信息字典:
            - total_feedbacks: 总反馈数
            - thumbs_up_count: 好评数
            - thumbs_down_count: 差评数
            - with_corrections: 包含修正的反馈数
            - with_comments: 包含评论的反馈数
        """
        total = len(self._feedback_history)
        thumbs_up = sum(1 for r in self._feedback_history if r.rating == "thumbs_up")
        thumbs_down = sum(1 for r in self._feedback_history if r.rating == "thumbs_down")
        with_corrections = sum(1 for r in self._feedback_history if r.corrected_output)
        with_comments = sum(1 for r in self._feedback_history if r.comment)
        
        return {
            "total_feedbacks": total,
            "thumbs_up_count": thumbs_up,
            "thumbs_down_count": thumbs_down,
            "thumbs_up_rate": thumbs_up / total if total > 0 else 0.0,
            "with_corrections": with_corrections,
            "with_comments": with_comments,
            "feedback_enabled": self._feedback_enabled,
        }
