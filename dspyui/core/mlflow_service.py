"""
MLflow 模型注册服务层

INPUT:  run_id, model_name, prompt_details
OUTPUT: ModelRegistrationResult
POS:    业务逻辑层，提供模型注册的高层接口
"""

import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

from dspyui.config import MLFLOW_ENABLED
from dspyui.core.mlflow_registry import register_model
from dspyui.core.mlflow_tracking import get_mlflow_ui_url

logger = logging.getLogger(__name__)


@dataclass
class ModelRegistrationResult:
    """模型注册结果数据类"""
    success: bool
    version: Optional[str] = None
    model_name: Optional[str] = None
    error_message: Optional[str] = None
    model_url: Optional[str] = None
    error_code: Optional[str] = None  # 用于 UI 层定位错误消息


def validate_model_name(model_name: str) -> tuple[bool, Optional[str]]:
    """
    验证模型名称
    
    Args:
        model_name: 待验证的模型名称
        
    Returns:
        (is_valid, error_code) 
        error_code 可能的值: "empty_name", None
    """
    if not model_name or not model_name.strip():
        return False, "empty_name"
    
    # 后续可以添加更多验证规则，例如正则表达式检查
    return True, None


def register_compiled_model(
    run_id: str,
    model_name: str,
    prompt_details: Dict[str, Any],
    artifact_path: str = "program"
) -> ModelRegistrationResult:
    """
    注册编译好的模型到 MLflow Model Registry
    
    Args:
        run_id: MLflow Run ID
        model_name: 模型注册名称
        prompt_details: 包含相关参数和指标的字典
        artifact_path: 工件路径，默认 "program"
        
    Returns:
        ModelRegistrationResult 包含注册结果
    """
    # 检查 MLflow 是否启用
    if not MLFLOW_ENABLED:
        return ModelRegistrationResult(
            success=False,
            error_message="MLflow is not enabled",
            error_code="mlflow_disabled"
        )
    
    # 验证模型名称
    is_valid, error_code = validate_model_name(model_name)
    if not is_valid:
        return ModelRegistrationResult(
            success=False,
            error_code=error_code
        )
    
    # 验证 run_id
    if not run_id:
        return ModelRegistrationResult(
            success=False,
            error_code="no_run_id"
        )
    
    try:
        # 准备模型元数据
        metadata = _prepare_model_metadata(prompt_details)
        
        # 注册模型
        version = register_model(
            run_id=run_id,
            model_name=model_name.strip(),
            artifact_path=artifact_path,
            metadata=metadata
        )
        
        if version:
            # 获取模型 URL
            model_url = get_mlflow_ui_url(
                model_name=model_name.strip(),
                model_version=version
            )
            
            logger.info(f"Successfully registered model: {model_name} version {version}")
            
            return ModelRegistrationResult(
                success=True,
                version=version,
                model_name=model_name.strip(),
                model_url=model_url
            )
        else:
            logger.warning(f"Model registration returned None version for model: {model_name}")
            return ModelRegistrationResult(
                success=False,
                error_code="registration_failed"
            )
    
    except Exception as e:
        logger.error(f"Error registering model {model_name}: {e}", exc_info=True)
        return ModelRegistrationResult(
            success=False,
            error_message=str(e),
            error_code="exception"
        )


def _prepare_model_metadata(prompt_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    从 prompt details 准备模型元数据
    """
    return {
        "input_fields": ",".join(prompt_details.get('input_fields', [])),
        "output_fields": ",".join(prompt_details.get('output_fields', [])),
        "instructions": prompt_details.get('instructions', ''),
        "evaluation_score": prompt_details.get('evaluation_score', 0.0),
        "signature": prompt_details.get('signature', ''),
        "dspy_module": prompt_details.get('dspy_module', ''),
        "optimizer": prompt_details.get('optimizer', '')
    }
