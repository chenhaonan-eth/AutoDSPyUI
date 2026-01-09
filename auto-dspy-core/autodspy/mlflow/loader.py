"""
MLflow 模型加载器

INPUT:  MLflow Model Registry, Run Artifacts
OUTPUT: load_model_from_registry(), load_model_by_alias(), load_model_from_run(), 
        list_registered_models(), list_model_versions(), get_model_metadata() 函数
POS:    负责从 MLflow 加载模型的"读取"操作，被 runner.py 和 UI 层调用

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import logging
import warnings
import dspy
from typing import Any, Dict, List, Optional

from autodspy.config import get_config
from autodspy.mlflow.tracking import is_mlflow_available

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


def load_model_from_registry(
    model_name: str,
    version: Optional[str] = None,
    stage: Optional[str] = None,
    alias: Optional[str] = None
) -> Any:
    """
    从 MLflow Model Registry 加载模型。
    
    支持三种方式指定版本（优先级：version > alias > stage）：
    1. version: 指定具体版本号
    2. alias: 使用别名（推荐，如 "champion", "challenger"）
    3. stage: 使用阶段（已废弃，如 "Production", "Staging"）
    
    Args:
        model_name: 注册的模型名称
        version: 指定版本号
        alias: 指定别名（推荐方式）
        stage: 指定阶段（已废弃，建议使用 alias）
        
    Returns:
        加载的 DSPy 程序对象
        
    Raises:
        ValueError: 当 MLflow 未启用或模型未找到时
        
    Example:
        >>> # 推荐：使用别名
        >>> program = load_model_from_registry("joke-generator", alias="champion")
        >>> # 使用版本号
        >>> program = load_model_from_registry("joke-generator", version="1")
        >>> # 已废弃：使用阶段
        >>> program = load_model_from_registry("joke-generator", stage="Production")
    """
    import os
    import pickle
    
    config = get_config()
    if not config.mlflow_enabled or not MLFLOW_INSTALLED:
        raise ValueError("MLflow 未启用或未安装")
    
    # 如果使用 stage，发出废弃警告
    if stage and not version and not alias:
        warnings.warn(
            "stage 参数已废弃，MLflow 2.9.0 起推荐使用 alias 参数。"
            "例如: load_model_from_registry(model_name, alias='champion') "
            "替代 stage='Production'",
            DeprecationWarning,
            stacklevel=2
        )
        
    try:
        # 构建模型 URI（优先级：version > alias > stage）
        if version:
            model_uri = f"models:/{model_name}/{version}"
        elif alias:
            model_uri = f"models:/{model_name}@{alias}"
        elif stage:
            # 兼容旧的 stage 方式
            model_uri = f"models:/{model_name}/{stage}"
        else:
            model_uri = f"models:/{model_name}/latest"
        
        logger.info(f"正在加载模型: {model_uri}")
        
        # 下载模型工件到临时目录
        # 绕过 mlflow.dspy.load_model() 的 dspy.settings 线程锁问题
        download_path = mlflow.artifacts.download_artifacts(model_uri)
        
        # MLflow DSPy flavor 使用 pickle 格式保存模型
        # 优先查找 data/model.pkl (MLflow DSPy flavor)
        model_file = os.path.join(download_path, "data", "model.pkl")
        
        if os.path.exists(model_file):
            # 使用 pickle 加载 MLflow DSPy flavor 模型
            with open(model_file, "rb") as f:
                loaded = pickle.load(f)
            
            # MLflow 包装器：实际程序在 .model 属性中
            if hasattr(loaded, 'model'):
                program = loaded.model
            else:
                program = loaded
            
            logger.info(f"成功加载模型 (pickle): {model_name}")
            return program
        
        # 备选：查找 program.json (dspy.save 格式)
        program_file = os.path.join(download_path, "program.json")
        if os.path.exists(program_file):
            program = dspy.load(program_file)
            logger.info(f"成功加载模型 (json): {model_name}")
            return program
        
        # 列出下载内容帮助调试
        files = []
        for root, dirs, filenames in os.walk(download_path):
            for f in filenames:
                files.append(os.path.join(root, f))
        logger.error(f"找不到有效的模型文件，下载的文件: {files}")
        raise ValueError(f"找不到模型程序文件 (model.pkl 或 program.json)")
            
    except Exception as e:
        logger.error(f"加载模型失败: {e}")
        raise ValueError(f"加载模型 {model_name} 失败: {e}")


def load_model_by_alias(
    model_name: str,
    alias: str = "champion"
) -> Any:
    """
    通过别名加载模型（便捷函数）。
    
    这是 load_model_from_registry(model_name, alias=alias) 的简化版本。
    
    Args:
        model_name: 注册的模型名称
        alias: 别名，默认 "champion"（生产版本）
        
    Returns:
        加载的 DSPy 程序对象
        
    Example:
        >>> # 加载生产版本
        >>> program = load_model_by_alias("joke-generator")
        >>> # 加载候选版本
        >>> program = load_model_by_alias("joke-generator", "challenger")
    """
    return load_model_from_registry(model_name, alias=alias)


def load_model_from_run(
    run_id: str,
    artifact_path: str = "program"
) -> Any:
    """
    从 MLflow Run 的 Artifacts 加载模型。
    
    Args:
        run_id: MLflow Run ID
        artifact_path: 工件路径，默认 "program"
        
    Returns:
        加载的 DSPy 程序对象
        
    Raises:
        ValueError: 当加载失败时
    """
    import os
    import pickle
    
    config = get_config()
    if not config.mlflow_enabled or not MLFLOW_INSTALLED:
        raise ValueError("MLflow 未启用或未安装")
        
    try:
        model_uri = f"runs:/{run_id}/{artifact_path}"
        logger.info(f"正在从 Run 加载模型: {model_uri}")
        
        # 下载工件并手动加载，绕过 mlflow.dspy.load_model() 的线程锁问题
        download_path = mlflow.artifacts.download_artifacts(model_uri)
        
        # MLflow DSPy flavor 使用 pickle 格式
        model_file = os.path.join(download_path, "data", "model.pkl")
        if os.path.exists(model_file):
            with open(model_file, "rb") as f:
                loaded = pickle.load(f)
            
            # MLflow 包装器：实际程序在 .model 属性中
            if hasattr(loaded, 'model'):
                program = loaded.model
            else:
                program = loaded
            
            logger.info(f"成功从 Run {run_id} 加载模型 (pickle)")
            return program
        
        # 备选：查找 program.json
        program_file = os.path.join(download_path, "program.json")
        if os.path.exists(program_file):
            program = dspy.load(program_file)
            logger.info(f"成功从 Run {run_id} 加载模型 (json)")
            return program
        
        raise ValueError(f"找不到模型程序文件 (model.pkl 或 program.json)")
            
    except Exception as e:
        logger.error(f"从 Run 加载模型失败: {e}")
        raise ValueError(f"从 Run {run_id} 加载模型失败: {e}")


def list_registered_models() -> List[Dict[str, Any]]:
    """
    列出所有已注册的模型。
    
    Returns:
        模型信息列表，每个元素包含:
        - name: 模型名称
        - latest_versions: 最新版本列表
        - description: 模型描述
        
    Example:
        >>> models = list_registered_models()
        >>> for m in models:
        ...     print(f"{m['name']}: {len(m['latest_versions'])} versions")
    """
    config = get_config()
    if not config.mlflow_enabled or not MLFLOW_INSTALLED:
        return []
    
    # 快速检查连通性，防止卡死
    if not is_mlflow_available(timeout=0.5):
        logger.warning("MLflow 服务器不可用，跳过模型搜索")
        return []
    
    try:
        client = MlflowClient()
        models = client.search_registered_models()
        
        result = []
        for model in models:
            model_info = {
                "name": model.name,
                "description": model.description or "",
                "latest_versions": []
            }
            
            for version in model.latest_versions:
                model_info["latest_versions"].append({
                    "version": version.version,
                    "stage": version.current_stage,
                    "run_id": version.run_id,
                    "status": version.status,
                })
            
            result.append(model_info)
        
        logger.info(f"找到 {len(result)} 个已注册模型")
        return result
        
    except Exception as e:
        logger.warning(f"列出已注册模型失败: {e}")
        return []


def list_model_versions(model_name: str) -> List[Dict[str, Any]]:
    """
    列出指定模型的所有版本。
    
    Args:
        model_name: 模型名称
        
    Returns:
        版本信息列表，每个元素包含:
        - version: 版本号
        - stage: 当前阶段（已废弃，仅供参考）
        - aliases: 版本别名列表（推荐使用）
        - run_id: 关联的 Run ID
        - creation_timestamp: 创建时间戳
        - description: 版本描述
        - tags: 版本标签
    """
    config = get_config()
    if not config.mlflow_enabled or not MLFLOW_INSTALLED:
        return []
    
    # 快速检查连通性
    if not is_mlflow_available(timeout=0.5):
        return []
    
    try:
        client = MlflowClient()
        versions = client.search_model_versions(f"name='{model_name}'")
        
        result = []
        for v in versions:
            # 获取别名列表
            aliases = list(v.aliases) if hasattr(v, 'aliases') and v.aliases else []
            
            result.append({
                "version": v.version,
                "stage": v.current_stage,  # 保留兼容，但标记为废弃
                "aliases": aliases,  # 新增：别名列表
                "run_id": v.run_id,
                "creation_timestamp": v.creation_timestamp,
                "description": v.description or "",
                "tags": dict(v.tags) if v.tags else {},
            })
        
        # 按版本号降序排列
        result.sort(key=lambda x: int(x["version"]), reverse=True)
        
        logger.info(f"模型 {model_name} 有 {len(result)} 个版本")
        return result
        
    except Exception as e:
        logger.warning(f"列出模型版本失败: {e}")
        return []


def get_model_metadata(
    model_name: str,
    version: str
) -> Dict[str, Any]:
    """
    获取指定模型版本的元数据。
    
    Args:
        model_name: 模型名称
        version: 版本号
        
    Returns:
        元数据字典，包含:
        - version: 版本号
        - stage: 当前阶段（已废弃）
        - aliases: 版本别名列表（推荐使用）
        - run_id: 关联的 Run ID
        - input_fields: 输入字段（从 tags 获取）
        - output_fields: 输出字段（从 tags 获取）
        - evaluation_score: 评估分数
        - dspy_module: DSPy 模块类型
        - optimizer: 优化器类型
    """
    config = get_config()
    if not config.mlflow_enabled or not MLFLOW_INSTALLED:
        return {}
    
    if not is_mlflow_available(timeout=0.5):
        return {}
    
    try:
        client = MlflowClient()
        model_version = client.get_model_version(name=model_name, version=version)
        
        tags = dict(model_version.tags) if model_version.tags else {}
        
        # 获取别名列表
        aliases = list(model_version.aliases) if hasattr(model_version, 'aliases') and model_version.aliases else []
        
        metadata = {
            "version": model_version.version,
            "stage": model_version.current_stage,  # 保留兼容
            "aliases": aliases,  # 新增：别名列表
            "run_id": model_version.run_id,
            "description": model_version.description or "",
            "creation_timestamp": model_version.creation_timestamp,
            # 从 tags 提取训练时记录的元数据
            "input_fields": tags.get("input_fields", "").split(",") if tags.get("input_fields") else [],
            "output_fields": tags.get("output_fields", "").split(",") if tags.get("output_fields") else [],
            "evaluation_score": float(tags.get("evaluation_score", 0)) if tags.get("evaluation_score") else None,
            "dspy_module": tags.get("dspy_module", ""),
            "optimizer": tags.get("optimizer", ""),
            "signature": tags.get("signature", ""),
        }
        
        logger.info(f"获取模型 {model_name} v{version} 元数据成功")
        return metadata
        
    except Exception as e:
        logger.warning(f"获取模型元数据失败: {e}")
        return {}


def load_prompt_artifact(
    run_id: str,
    artifact_path: str = "prompt"
) -> Optional[Dict[str, Any]]:
    """
    从 MLflow Run 加载提示词工件。
    
    Args:
        run_id: MLflow Run ID
        artifact_path: 工件路径，默认 "prompt"
        
    Returns:
        提示词详情字典，如果加载失败则返回 None
    """
    import os
    import json
    
    config = get_config()
    if not config.mlflow_enabled or not MLFLOW_INSTALLED:
        return None
        
    try:
        # 1. 尝试加载专门的 prompt 工件
        metadata_uri = f"runs:/{run_id}/{artifact_path}"
        logger.info(f"正在从 Run 加载提示词工件: {metadata_uri}")
        
        try:
            download_path = mlflow.artifacts.download_artifacts(metadata_uri)
            for filename in os.listdir(download_path):
                if filename.endswith(".json"):
                    prompt_file = os.path.join(download_path, filename)
                    with open(prompt_file, "r", encoding="utf-8") as f:
                        prompt_data = json.load(f)
                    logger.info(f"成功从 prompt 工件加载提示词")
                    return prompt_data
        except Exception:
            logger.info("未找到 prompt 工件，尝试从 program 工件提取")
        
        # 2. 如果没有 prompt 工件，尝试从 program 工件提取
        program_uri = f"runs:/{run_id}/program"
        download_path = mlflow.artifacts.download_artifacts(program_uri)
        
        program_file = None
        for filename in os.listdir(download_path):
            if filename.endswith(".json"):
                program_file = os.path.join(download_path, filename)
                break
        
        if program_file and os.path.exists(program_file):
            with open(program_file, "r", encoding="utf-8") as f:
                program_data = json.load(f)
            
            # 提取基本信息
            # 这是一个典型的 DSPy compiled program JSON
            # 我们需要构造一个与 prompt_details 兼容的结构
            
            # 尝试从 tags 获取补充信息
            client = MlflowClient()
            run = client.get_run(run_id)
            tags = run.data.tags
            params = run.data.params
            
            input_fields = params.get("input_fields", "").split(",") if params.get("input_fields") else []
            output_fields = params.get("output_fields", "").split(",") if params.get("output_fields") else []
            
            # 从程序 JSON 提取指令
            instructions = ""
            if "predictor" in program_data and "signature" in program_data["predictor"]:
                instructions = program_data["predictor"]["signature"].get("instructions", "")
            
            # 构造兼容结构
            prompt_data = {
                "human_readable_id": params.get("human_readable_id", f"MLflow-{run_id[:8]}"),
                "input_fields": input_fields,
                "output_fields": output_fields,
                "dspy_module": params.get("dspy_module", "N/A"),
                "llm_model": params.get("llm_model", "N/A"),
                "teacher_model": params.get("teacher_model", "N/A"),
                "optimizer": params.get("optimizer", "N/A"),
                "instructions": instructions,
                "optimized_prompt": "Prompt extraction from program.json is limited. See MLflow UI for full details.",
                "evaluation_score": run.data.metrics.get("evaluation_score", "N/A"),
                "mlflow_run_id": run_id,
                "extracted_from_program": True
            }
            
            logger.info(f"成功从 program 工件提取基本提示词信息")
            return prompt_data
            
        return None
            
    except Exception as e:
        logger.error(f"从 Run {run_id} 加载提示词失败: {e}")
        return None


def get_registered_run_ids() -> set:
    """获取所有已注册模型版本关联的 Run ID 集合"""
    config = get_config()
    if not config.mlflow_enabled:
        return set()
    try:
        from mlflow import MlflowClient
        client = MlflowClient()
        models = client.search_registered_models()
        run_ids = set()
        for model in models:
            for version in model.latest_versions:
                if version.run_id:
                    run_ids.add(version.run_id)
        return run_ids
    except Exception as e:
        logger.error(f"获取已注册 Run ID 失败: {e}")
        return set()
