"""
FastAPI 依赖注入

INPUT:  dspyui.core 模块 (ModelManager, FeedbackService, DataExporter)
OUTPUT: 依赖注入函数 (get_model_manager, get_feedback_service, get_data_exporter)
POS:    依赖管理层，提供核心服务的依赖注入

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

from typing import TYPE_CHECKING

from fastapi import Request

if TYPE_CHECKING:
    # 类型提示用，实际模块将在后续任务中实现
    pass


async def get_model_manager(request: Request):
    """
    获取 ModelManager 实例
    
    Args:
        request: FastAPI 请求对象
        
    Returns:
        ModelManager: 模型管理器实例
    """
    return request.app.state.model_manager


async def get_feedback_service(request: Request):
    """
    获取 FeedbackService 实例
    
    Args:
        request: FastAPI 请求对象
        
    Returns:
        FeedbackService: 反馈服务实例
    """
    return request.app.state.feedback_service


async def get_data_exporter(request: Request):
    """
    获取 DataExporter 实例
    
    Args:
        request: FastAPI 请求对象
        
    Returns:
        DataExporter: 数据导出器实例
    """
    return request.app.state.data_exporter
