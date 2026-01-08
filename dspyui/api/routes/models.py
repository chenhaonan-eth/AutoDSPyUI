"""
模型管理路由

INPUT:  FastAPI, dspyui.api.schemas, MLflow Model Registry, dspyui.api.dependencies
OUTPUT: GET /models, GET /models/{name}/versions, POST /models/{name}/stage 端点
POS:    模型管理 API 端点，处理模型列表、版本查询和阶段切换

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from dspyui.api.dependencies import get_model_manager
from dspyui.api.schemas import ModelInfo, ModelVersion, StageTransitionRequest
from dspyui.config import MLFLOW_ENABLED
from dspyui.core.model_manager import ModelManager

# 可选导入 MLflow
try:
    from mlflow import MlflowClient
    MLFLOW_INSTALLED = True
except ImportError:
    MlflowClient = None
    MLFLOW_INSTALLED = False

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_mlflow_client():
    """获取 MLflow 客户端"""
    if not MLFLOW_ENABLED or not MLFLOW_INSTALLED:
        raise HTTPException(
            status_code=503,
            detail="MLflow 未启用或未安装"
        )
    return MlflowClient()


@router.get("/models", response_model=List[ModelInfo])
async def list_models() -> List[ModelInfo]:
    """
    列出所有注册模型
    
    从 MLflow Model Registry 获取所有已注册的模型信息。
    
    Returns:
        List[ModelInfo]: 模型信息列表，包含名称、最新版本、当前阶段等
        
    Raises:
        HTTPException: 503 MLflow 不可用
    """
    logger.info("获取模型列表")
    
    try:
        client = _get_mlflow_client()
        
        # 获取所有注册模型
        registered_models = client.search_registered_models()
        
        models = []
        for rm in registered_models:
            # 获取最新版本信息
            latest_version = "0"
            current_stage = "None"
            evaluation_score = None
            
            if rm.latest_versions:
                # 找到最新版本
                latest = max(rm.latest_versions, key=lambda v: int(v.version))
                latest_version = latest.version
                current_stage = latest.current_stage
                
                # 尝试获取评估分数
                if latest.run_id:
                    try:
                        run = client.get_run(latest.run_id)
                        evaluation_score = run.data.metrics.get("evaluation_score")
                    except Exception:
                        pass
            
            # 获取标签
            tags = {}
            if hasattr(rm, 'tags') and rm.tags:
                tags = {tag.key: tag.value for tag in rm.tags}
            
            models.append(ModelInfo(
                name=rm.name,
                latest_version=latest_version,
                current_stage=current_stage,
                description=rm.description,
                evaluation_score=evaluation_score,
                tags=tags
            ))
        
        logger.info(f"返回 {len(models)} 个模型")
        return models
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取模型列表失败: {str(e)}"
        )


@router.get("/models/{name}/versions", response_model=List[ModelVersion])
async def list_versions(name: str) -> List[ModelVersion]:
    """
    列出模型所有版本
    
    Args:
        name: 模型名称
        
    Returns:
        List[ModelVersion]: 版本信息列表
        
    Raises:
        HTTPException: 404 模型不存在，503 MLflow 不可用
    """
    logger.info(f"获取模型版本: {name}")
    
    try:
        client = _get_mlflow_client()
        
        # 搜索指定模型的所有版本
        versions = client.search_model_versions(f"name='{name}'")
        
        if not versions:
            raise HTTPException(
                status_code=404,
                detail=f"模型 '{name}' 不存在或没有版本"
            )
        
        result = []
        for v in versions:
            # 尝试获取评估分数
            evaluation_score = None
            if v.run_id:
                try:
                    run = client.get_run(v.run_id)
                    evaluation_score = run.data.metrics.get("evaluation_score")
                except Exception:
                    pass
            
            # 解析创建时间
            created_at = datetime.fromtimestamp(v.creation_timestamp / 1000)
            
            result.append(ModelVersion(
                version=v.version,
                stage=v.current_stage,
                created_at=created_at,
                evaluation_score=evaluation_score,
                run_id=v.run_id
            ))
        
        # 按版本号降序排列
        result.sort(key=lambda x: int(x.version), reverse=True)
        
        logger.info(f"返回 {len(result)} 个版本")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取模型版本失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取模型版本失败: {str(e)}"
        )


@router.post("/models/{name}/stage")
async def transition_stage(
    name: str,
    request: StageTransitionRequest,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """
    切换模型阶段
    
    将指定版本的模型切换到目标阶段（Staging/Production/Archived）。
    切换后会自动使该模型的缓存失效。
    
    Args:
        name: 模型名称
        request: 阶段切换请求，包含版本号和目标阶段
        model_manager: 模型管理器（依赖注入）
        
    Returns:
        dict: 切换结果
        
    Raises:
        HTTPException: 404 模型/版本不存在，400 无效阶段
    """
    logger.info(f"切换模型阶段: {name} v{request.version} -> {request.stage}")
    
    try:
        client = _get_mlflow_client()
        
        # 验证模型和版本存在
        try:
            model_version = client.get_model_version(name, request.version)
        except Exception:
            raise HTTPException(
                status_code=404,
                detail=f"模型 '{name}' 版本 '{request.version}' 不存在"
            )
        
        # 记录旧阶段
        old_stage = model_version.current_stage
        
        # 执行阶段切换
        client.transition_model_version_stage(
            name=name,
            version=request.version,
            stage=request.stage,
            archive_existing_versions=False  # 不自动归档其他版本
        )
        
        # 使模型缓存失效
        invalidated_count = model_manager.invalidate_cache(name)
        
        logger.info(
            f"阶段切换成功: {name} v{request.version} {old_stage} -> {request.stage}, "
            f"清除 {invalidated_count} 个缓存条目"
        )
        
        return {
            "status": "success",
            "model": name,
            "version": request.version,
            "old_stage": old_stage,
            "new_stage": request.stage,
            "cache_invalidated": invalidated_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"阶段切换失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"阶段切换失败: {str(e)}"
        )
