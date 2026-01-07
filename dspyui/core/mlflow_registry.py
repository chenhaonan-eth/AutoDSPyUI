"""
MLflow 模型注册管理

INPUT:  MLflow Run ID, 模型元数据
OUTPUT: register_model(), transition_model_stage() 函数
POS:    负责"写入" Model Registry 的操作，被 mlflow_service.py 和 browse_tab.py 调用

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import logging
from typing import Any, Dict, Optional

from dspyui.config import MLFLOW_ENABLED

# 可选导入 MLflow
try:
    import mlflow
    from mlflow import MlflowClient
    MLFLOW_INSTALLED = True
except ImportError:
    mlflow = None
    MlflowClient = None
    MLFLOW_INSTALLED = False

# 设置日志
logger = logging.getLogger(__name__)

# 模型描述和标签的最大长度
MODEL_DESCRIPTION_MAX_LENGTH = 200
MODEL_TAG_MAX_LENGTH = 250


def _truncate_param(value: str, max_length: int = 500) -> str:
    """截断参数值以符合长度限制。"""
    if len(value) > max_length:
        return value[:max_length - 3] + "..."
    return value


def register_model(
    run_id: str,
    model_name: str,
    artifact_path: str = "program",
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    将编译后的程序注册到 MLflow Model Registry。
    
    Args:
        run_id: MLflow Run ID
        model_name: 模型注册名称
        artifact_path: 工件路径，默认为 "program"
        metadata: 模型元数据字典，可包含:
            - input_fields (str): 输入字段，逗号分隔
            - output_fields (str): 输出字段，逗号分隔
            - instructions (str): 任务指令
            - evaluation_score (float): 评估分数
            - signature (str): 模型签名描述
            - dspy_module (str): DSPy 模块类型
            - optimizer (str): 优化器类型
        
    Returns:
        注册的模型版本号，如果失败返回 None
        
    Example:
        >>> version = register_model(
        ...     run_id="abc123",
        ...     model_name="joke-generator",
        ...     metadata={
        ...         "input_fields": "topic",
        ...         "output_fields": "joke",
        ...         "evaluation_score": 0.85,
        ...     }
        ... )
    """
    if not MLFLOW_ENABLED or not MLFLOW_INSTALLED:
        return None
    
    try:
        model_uri = f"runs:/{run_id}/{artifact_path}"
        result = mlflow.register_model(model_uri, model_name)
        version = result.version
        
        logger.info(f"已注册模型: {model_name} 版本 {version}")
        
        # 如果提供了元数据，更新模型版本描述
        if metadata:
            client = MlflowClient()
            
            # 构建描述信息
            description_parts = []
            
            if "input_fields" in metadata:
                description_parts.append(f"Input: {metadata['input_fields']}")
            if "output_fields" in metadata:
                description_parts.append(f"Output: {metadata['output_fields']}")
            if "dspy_module" in metadata:
                description_parts.append(f"Module: {metadata['dspy_module']}")
            if "optimizer" in metadata:
                description_parts.append(f"Optimizer: {metadata['optimizer']}")
            if "evaluation_score" in metadata:
                score = metadata['evaluation_score']
                description_parts.append(f"Score: {score:.4f}" if isinstance(score, float) else f"Score: {score}")
            if "instructions" in metadata:
                instructions = metadata['instructions']
                if len(instructions) > MODEL_DESCRIPTION_MAX_LENGTH:
                    instructions = instructions[:MODEL_DESCRIPTION_MAX_LENGTH - 3] + "..."
                description_parts.append(f"Instructions: {instructions}")
            
            description = "\n".join(description_parts)
            
            # 更新模型版本描述
            client.update_model_version(
                name=model_name,
                version=version,
                description=description
            )
            
            # 设置模型版本标签（用于搜索和过滤）
            tags_to_set = {}
            if "input_fields" in metadata:
                tags_to_set["input_fields"] = _truncate_param(str(metadata["input_fields"]), MODEL_TAG_MAX_LENGTH)
            if "output_fields" in metadata:
                tags_to_set["output_fields"] = _truncate_param(str(metadata["output_fields"]), MODEL_TAG_MAX_LENGTH)
            if "evaluation_score" in metadata:
                tags_to_set["evaluation_score"] = str(metadata["evaluation_score"])
            if "dspy_module" in metadata:
                tags_to_set["dspy_module"] = str(metadata["dspy_module"])
            if "optimizer" in metadata:
                tags_to_set["optimizer"] = str(metadata["optimizer"])
            if "signature" in metadata:
                tags_to_set["signature"] = _truncate_param(str(metadata["signature"]), MODEL_TAG_MAX_LENGTH)
            
            for tag_key, tag_value in tags_to_set.items():
                try:
                    client.set_model_version_tag(
                        name=model_name,
                        version=version,
                        key=tag_key,
                        value=tag_value
                    )
                except Exception as tag_error:
                    logger.warning(f"设置模型标签 '{tag_key}' 失败: {tag_error}")
            
            logger.info(f"已更新模型 {model_name} 版本 {version} 的元数据")
        
        return version
        
    except Exception as e:
        logger.warning(f"模型注册失败: {e}")
        return None


def transition_model_stage(
    model_name: str,
    version: str,
    stage: str,
    archive_existing: bool = False
) -> bool:
    """
    更新模型版本的阶段。
    
    Args:
        model_name: 模型名称
        version: 模型版本号
        stage: 目标阶段，有效值:
            - "Staging": 预发布/测试阶段
            - "Production": 生产阶段
            - "Archived": 归档阶段
            - "None": 移除阶段标记
        archive_existing: 是否归档当前处于目标阶段的其他版本
        
    Returns:
        是否成功更新
        
    Example:
        >>> transition_model_stage("joke-generator", "1", "Staging")
        True
        >>> transition_model_stage("joke-generator", "2", "Production", archive_existing=True)
        True
    """
    if not MLFLOW_ENABLED or not MLFLOW_INSTALLED:
        return False
    
    valid_stages = {"Staging", "Production", "Archived", "None"}
    if stage not in valid_stages:
        logger.error(f"无效的阶段: {stage}，有效值为: {valid_stages}")
        return False
    
    try:
        client = MlflowClient()
        
        # 执行阶段转换
        client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage=stage,
            archive_existing_versions=archive_existing
        )
        
        logger.info(f"已更新模型 {model_name} 版本 {version} 到阶段 {stage}")
        
        # 验证转换是否成功
        updated_version = client.get_model_version(name=model_name, version=version)
        if updated_version.current_stage == stage:
            logger.debug(f"阶段转换验证成功: {updated_version.current_stage}")
            return True
        else:
            logger.warning(
                f"阶段转换可能未完全生效: 期望 {stage}, 实际 {updated_version.current_stage}"
            )
            return True  # API 调用成功，但状态可能有延迟
        
    except Exception as e:
        logger.warning(f"模型阶段转换失败: {e}")
        return False
