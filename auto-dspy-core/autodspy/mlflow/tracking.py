"""
MLflow 追踪模块

INPUT:  config.py 中的 MLflow 配置, 编译/运行参数
OUTPUT: init_mlflow(), truncate_param(), track_compilation(), log_compilation_metrics(), 
        log_compilation_artifacts(), log_dspy_model(), log_evaluation_table(), compute_dataset_hash(),
        log_dataset_metadata(), register_model(), set_model_alias(), delete_model_alias(),
        transition_model_stage() (deprecated), get_mlflow_ui_url(), _get_experiment_id_for_run(), 
        _serialize_value() 函数
POS:    MLflow 集成的核心模块，被 compiler.py 和 runner.py 调用

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import os
import hashlib
import logging
import json
import statistics
import warnings
from typing import Dict, Any, Optional, List, Generator
from contextlib import contextmanager

from autodspy.config import get_config

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

# MLflow 参数值最大长度限制
MLFLOW_PARAM_MAX_LENGTH = 500

# 模型描述和标签的最大长度
MODEL_DESCRIPTION_MAX_LENGTH = 200
MODEL_TAG_MAX_LENGTH = 250


def truncate_param(value: str, max_length: int = MLFLOW_PARAM_MAX_LENGTH) -> str:
    """
    截断参数值以符合 MLflow 的长度限制。
    
    如果字符串长度超过 max_length，截断至 max_length-3 并附加 "..."。
    
    Args:
        value: 原始参数值
        max_length: 最大允许长度，默认 500
        
    Returns:
        截断后的字符串（如果需要）或原始字符串
    """
    if len(value) > max_length:
        return value[:max_length - 3] + "..."
    return value


def is_mlflow_available(timeout: float = 1.0) -> bool:
    """
    检查 MLflow Tracking Server 是否可用。
    
    采用快速探测逻辑，防止因网络不通或服务器未启动导致的长时间卡死。
    
    Args:
        timeout: 超时时间（秒），默认 1.0
        
    Returns:
        bool: 服务器是否可用
    """
    config = get_config()
    if not config.mlflow_enabled or not MLFLOW_INSTALLED:
        return False
        
    # 本地 SQLite / File 存储始终认为可用
    if config.mlflow_tracking_uri.startswith("sqlite") or config.mlflow_tracking_uri.startswith("file"):
        return True
    
    # HTTP/HTTPS 需要发送请求确认
    try:
        import requests
        # 发送简单的 GET 请求，带上短超时
        response = requests.get(config.mlflow_tracking_uri, timeout=timeout)
        # 只要不是 5xx 错误，通常认为 API 服务是存在的
        return response.status_code < 500
    except Exception:
        return False


def init_mlflow() -> bool:
    """
    初始化 MLflow 配置和 DSPy autolog。
    
    根据配置设置 MLflow tracking URI、experiment，并启用 DSPy autolog。
    如果 mlflow_enabled 为 False，则禁用 autolog 并跳过所有追踪操作。
    
    Returns:
        bool: 是否成功初始化。如果 MLflow 被禁用或初始化失败，返回 False。
    """
    config = get_config()
    
    if not config.mlflow_enabled:
        logger.info("MLflow 追踪已禁用 (mlflow_enabled=false)")
        if MLFLOW_INSTALLED:
            try:
                mlflow.dspy.autolog(disable=True)
            except Exception as e:
                logger.debug(f"禁用 autolog 时出错（可忽略）: {e}")
        return False
    
    if not MLFLOW_INSTALLED:
        logger.warning("MLflow 未安装，追踪功能不可用")
        return False
    
    # 增加可用性检查，防止连接失败导致脚本卡死
    if not is_mlflow_available(timeout=1.0):
        logger.warning(f"MLflow 服务器连接失败 ({config.mlflow_tracking_uri})，将禁用本轮追踪")
        return False
    
    try:
        # 设置 tracking URI
        mlflow.set_tracking_uri(config.mlflow_tracking_uri)
        logger.info(f"MLflow tracking URI: {config.mlflow_tracking_uri}")
        
        # 设置或创建 experiment
        mlflow.set_experiment(config.mlflow_experiment_name)
        logger.info(f"MLflow experiment: {config.mlflow_experiment_name}")
        
        # 启用 DSPy autolog
        mlflow.dspy.autolog(
            log_traces=config.mlflow_log_traces,
            log_traces_from_compile=config.mlflow_log_traces_from_compile,
            log_traces_from_eval=config.mlflow_log_traces_from_eval,
            log_compiles=config.mlflow_log_compiles,
            log_evals=config.mlflow_log_evals,
        )
        logger.info(
            f"MLflow DSPy autolog 已启用: "
            f"log_traces={config.mlflow_log_traces}, "
            f"log_traces_from_compile={config.mlflow_log_traces_from_compile}, "
            f"log_traces_from_eval={config.mlflow_log_traces_from_eval}, "
            f"log_compiles={config.mlflow_log_compiles}, "
            f"log_evals={config.mlflow_log_evals}"
        )
        
        return True
        
    except ImportError:
        logger.warning("MLflow 未安装，追踪功能不可用")
        return False
    except Exception as e:
        logger.warning(f"MLflow 初始化失败，将禁用追踪: {e}")
        return False


@contextmanager
def track_compilation(
    run_name: str,
    params: Dict[str, Any],
    tags: Optional[Dict[str, str]] = None
) -> Generator[Optional[Any], None, None]:
    """
    编译追踪上下文管理器。
    
    创建一个 MLflow Run 来追踪编译过程，记录参数，并在退出时正确结束 Run。
    如果 MLflow 被禁用，则直接 yield None 而不进行任何追踪操作。
    
    Args:
        run_name: MLflow Run 名称，用于标识此次编译
        params: 编译参数字典，将被记录到 MLflow
        tags: 可选的标签字典，用于分类和过滤 Run
        
    Yields:
        MLflow Run 对象，如果 MLflow 禁用则为 None
        
    Example:
        >>> with track_compilation("MyModule_BootstrapFewShot_gpt-4", params) as run:
        ...     # 执行编译逻辑
        ...     if run:
        ...         print(f"Run ID: {run.info.run_id}")
    """
    config = get_config()
    if not config.mlflow_enabled or not MLFLOW_INSTALLED:
        yield None
        return
    
    try:
        # 开始新的 Run
        with mlflow.start_run(run_name=run_name) as run:
            # 记录标签
            if tags:
                mlflow.set_tags(tags)
            
            # 记录参数（处理截断和类型转换）
            for key, value in params.items():
                try:
                    # 转换为字符串并截断
                    str_value = str(value) if value is not None else ""
                    truncated_value = truncate_param(str_value)
                    mlflow.log_param(key, truncated_value)
                except Exception as e:
                    logger.warning(f"记录参数 '{key}' 失败: {e}")
            
            yield run
            
    except Exception as e:
        logger.warning(f"MLflow 追踪失败: {e}")
        # 不需要再次 yield，因为上下文管理器如果已经 yielded，就不能再次 yielded 
        # 抛出异常由上层处理
        raise


def log_compilation_metrics(
    baseline_score: float,
    evaluation_score: float,
    trainset_size: int,
    devset_size: int
) -> None:
    """
    记录编译评估指标到当前活跃的 MLflow Run。
    
    Args:
        baseline_score: 基线评估分数（编译前）
        evaluation_score: 编译后评估分数
        trainset_size: 训练集大小
        devset_size: 验证集大小
    """
    config = get_config()
    if not config.mlflow_enabled:
        return
    
    try:
        if not mlflow.active_run():
            logger.warning("没有活跃的 MLflow Run，跳过指标记录")
            return
        
        # 计算分数提升
        score_improvement = evaluation_score - baseline_score
        
        # 记录指标
        mlflow.log_metrics({
            "baseline_score": baseline_score,
            "evaluation_score": evaluation_score,
            "score_improvement": score_improvement,
            "trainset_size": trainset_size,
            "devset_size": devset_size,
        })
        
        logger.info(
            f"已记录编译指标: baseline={baseline_score:.4f}, "
            f"evaluation={evaluation_score:.4f}, improvement={score_improvement:.4f}"
        )
        
    except Exception as e:
        logger.warning(f"记录编译指标失败: {e}")


def log_compilation_artifacts(
    program_path: str,
    prompt_path: Optional[str] = None,
    dataset_path: Optional[str] = None
) -> None:
    """
    记录编译产出的工件到当前活跃的 MLflow Run。
    
    Args:
        program_path: 编译后程序 JSON 文件路径
        prompt_path: 优化后提示词 JSON 文件路径（可选）
        dataset_path: 数据集 CSV 文件路径（可选）
    """
    config = get_config()
    if not config.mlflow_enabled:
        return
    
    try:
        import mlflow
        
        if not mlflow.active_run():
            logger.warning("没有活跃的 MLflow Run，跳过工件记录")
            return
        
        # 记录程序文件
        if program_path and os.path.exists(program_path):
            mlflow.log_artifact(program_path, artifact_path="program")
            logger.info(f"已记录程序工件: {program_path}")
        elif program_path:
            logger.warning(f"程序文件不存在: {program_path}")
        
        # 记录提示词文件
        if prompt_path and os.path.exists(prompt_path):
            mlflow.log_artifact(prompt_path, artifact_path="prompt")
            logger.info(f"已记录提示词工件: {prompt_path}")
        elif prompt_path:
            logger.warning(f"提示词文件不存在: {prompt_path}")
        
        # 记录数据集文件
        if dataset_path and os.path.exists(dataset_path):
            mlflow.log_artifact(dataset_path, artifact_path="dataset")
            logger.info(f"已记录数据集工件: {dataset_path}")
        elif dataset_path:
            logger.warning(f"数据集文件不存在: {dataset_path}")
        
    except Exception as e:
        logger.warning(f"记录编译工件失败: {e}")


def log_dspy_model(
    compiled_program: Any,
    artifact_path: str = "program"
) -> None:
    """
    使用 mlflow.dspy.log_model 记录 DSPy 程序模型。
    
    这是将模型注册到 Model Registry 的先决条件。
    
    Args:
        compiled_program: 编译后的 DSPy 程序对象
        artifact_path: 工件路径，默认为 "program"
    """
    config = get_config()
    if not config.mlflow_enabled or not MLFLOW_INSTALLED:
        return
    
    try:
        if not mlflow.active_run():
            logger.warning("没有活跃的 MLflow Run，跳过模型记录")
            return
        
        # 记录 DSPy 模型
        # 注意：这需要较新版本的 MLflow (2.12.2+)
        if hasattr(mlflow, "dspy"):
            mlflow.dspy.log_model(compiled_program, artifact_path)
            logger.info(f"已记录 DSPy 模型到路径: {artifact_path}")
        else:
            # 如果不支持 dspy flavor，尝试通用 log_model (通常不推荐用于 dspy)
            logger.warning("当前 MLflow 版本不支持 dspy flavor，无法正确记录模型以供注册")
            
    except Exception as e:
        logger.warning(f"记录 DSPy 模型失败: {e}")


def log_evaluation_table(
    eval_results: List[Dict[str, Any]],
    artifact_name: str = "eval_results.json",
    metric_name: Optional[str] = None,
    metric_config: Optional[Dict[str, Any]] = None
) -> None:
    """
    使用 mlflow.log_table() 记录详细评估结果。
    
    记录 per-example 评估结果，包含输入、期望输出、实际输出和评分。
    同时记录聚合指标（mean, std）到 MLflow metrics。
    
    Args:
        eval_results: 评估结果列表，每个元素应包含:
            - example_id (int): 示例 ID
            - input (str): 输入内容（JSON 序列化）
            - expected_output (str): 期望输出
            - actual_output (str): 实际输出
            - score (float): 单条评分
            - metric_name (str, optional): 使用的指标名称
        artifact_name: 工件文件名，默认为 "eval_results.json"
        metric_name: 评估指标名称，将添加到每条记录中
        metric_config: 评估指标配置，将作为参数记录
        
    Note:
        - 如果 eval_results 中的记录缺少 example_id，将自动生成
        - 如果 eval_results 中的记录缺少 metric_name，将使用参数中的 metric_name
        - 聚合指标 (mean, std) 将记录到 MLflow metrics
    """
    config = get_config()
    if not config.mlflow_enabled or not MLFLOW_INSTALLED:
        return
    
    if not eval_results:
        logger.warning("评估结果为空，跳过记录")
        return
    
    try:
        if not mlflow.active_run():
            logger.warning("没有活跃的 MLflow Run，跳过评估结果记录")
            return
        
        # 标准化评估结果，确保包含所有必需字段
        # Note: mlflow.log_table 对 data 参数要求严格，使用字典列表可能在某些版本报错
        # 推荐使用：字典（键为列名，值为列表）
        table_data = {
            "example_id": [],
            "input": [],
            "expected_output": [],
            "actual_output": [],
            "score": [],
            "metric_name": [],
        }
        
        scores = []
        for idx, result in enumerate(eval_results):
            score = float(result.get("score", 0.0))
            table_data["example_id"].append(result.get("example_id", idx))
            table_data["input"].append(_serialize_value(result.get("input", "")))
            table_data["expected_output"].append(_serialize_value(result.get("expected_output", "")))
            table_data["actual_output"].append(_serialize_value(result.get("actual_output", "")))
            table_data["score"].append(score)
            table_data["metric_name"].append(result.get("metric_name", metric_name or "unknown"))
            scores.append(score)
        
        # 使用 log_table 记录评估结果
        mlflow.log_table(
            data=table_data,
            artifact_file=artifact_name
        )
        
        logger.info(f"已记录 {len(scores)} 条评估结果到 {artifact_name}")
        
        if scores:
            mean_score = statistics.mean(scores)
            mlflow.log_metric("eval_score_mean", mean_score)
            
            if len(scores) > 1:
                std_score = statistics.stdev(scores)
                mlflow.log_metric("eval_score_std", std_score)
            
            mlflow.log_metric("eval_example_count", len(scores))
            
            logger.info(f"已记录聚合指标: mean={mean_score:.4f}, count={len(scores)}")
        
        # 记录指标配置（如果提供）
        if metric_config:
            config_str = truncate_param(json.dumps(metric_config, ensure_ascii=False))
            mlflow.log_param("eval_metric_config", config_str)
        
        if metric_name:
            mlflow.log_param("eval_metric_name", metric_name)
        
    except Exception as e:
        logger.warning(f"记录评估结果失败: {e}")


def _serialize_value(value: Any) -> str:
    """
    将值序列化为字符串，用于评估结果记录。
    
    Args:
        value: 任意值
        
    Returns:
        序列化后的字符串
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(value)
    return str(value)


def compute_dataset_hash(data: "pd.DataFrame") -> str:
    """
    计算数据集的 MD5 哈希值用于版本追踪。
    
    相同内容的 DataFrame 将产生相同的哈希值，用于验证数据集的一致性。
    使用排序后的列名和固定的 CSV 格式确保确定性。
    
    Args:
        data: pandas DataFrame 数据集
        
    Returns:
        MD5 哈希值字符串（32 位十六进制），如果计算失败返回空字符串
    """
    try:
        # 确保列顺序一致（按列名排序）
        sorted_columns = sorted(data.columns.tolist())
        sorted_data = data[sorted_columns]
        
        # 将 DataFrame 转换为 CSV 字符串
        # 使用固定参数确保一致性：
        # - index=False: 不包含行索引
        # - lineterminator='\n': 统一换行符
        csv_string = sorted_data.to_csv(index=False, lineterminator='\n')
        
        # 计算 SHA-256 哈希 (取代不安全的 MD5)
        hash_obj = hashlib.sha256(csv_string.encode('utf-8'))
        return hash_obj.hexdigest()
        
    except Exception as e:
        logger.warning(f"计算数据集哈希失败: {e}")
        return ""


def log_dataset_metadata(
    data: "pd.DataFrame",
    dataset_name: str = "training_data"
) -> None:
    """
    记录数据集元数据到当前活跃的 MLflow Run。
    
    Args:
        data: pandas DataFrame 数据集
        dataset_name: 数据集名称，用于参数前缀
    """
    config = get_config()
    if not config.mlflow_enabled:
        return
    
    try:
        import mlflow
        
        if not mlflow.active_run():
            logger.warning("没有活跃的 MLflow Run，跳过数据集元数据记录")
            return
        
        # 计算哈希
        file_hash = compute_dataset_hash(data)
        
        # 记录元数据
        mlflow.log_params({
            f"{dataset_name}_row_count": len(data),
            f"{dataset_name}_column_names": truncate_param(",".join(data.columns.tolist())),
            f"{dataset_name}_file_hash": file_hash,
        })
        
        logger.info(f"已记录数据集元数据: rows={len(data)}, hash={file_hash[:8]}...")
        
    except Exception as e:
        logger.warning(f"记录数据集元数据失败: {e}")


def register_model(
    run_id: str,
    model_name: str,
    artifact_path: str = "program",
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    将编译后的程序注册到 MLflow Model Registry。
    
    根据 Requirements 5.1, 5.2，注册模型时需要包含元数据信息。
    
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
        ...         "instructions": "Generate a funny joke"
        ...     }
        ... )
    """
    config = get_config()
    if not config.mlflow_enabled or not MLFLOW_INSTALLED:
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
                # 截断指令以避免过长
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
                tags_to_set["input_fields"] = truncate_param(str(metadata["input_fields"]), MODEL_TAG_MAX_LENGTH)
            if "output_fields" in metadata:
                tags_to_set["output_fields"] = truncate_param(str(metadata["output_fields"]), MODEL_TAG_MAX_LENGTH)
            if "evaluation_score" in metadata:
                tags_to_set["evaluation_score"] = str(metadata["evaluation_score"])
            if "dspy_module" in metadata:
                tags_to_set["dspy_module"] = str(metadata["dspy_module"])
            if "optimizer" in metadata:
                tags_to_set["optimizer"] = str(metadata["optimizer"])
            if "signature" in metadata:
                tags_to_set["signature"] = truncate_param(str(metadata["signature"]), MODEL_TAG_MAX_LENGTH)
            
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
    
    .. deprecated:: 0.2.0
        MLflow 2.9.0 起废弃 Stage API，请使用 `set_model_alias()` 替代。
        - "Production" -> set_model_alias(model_name, "champion", version)
        - "Staging" -> set_model_alias(model_name, "challenger", version)
    
    Args:
        model_name: 模型名称
        version: 模型版本号
        stage: 目标阶段，有效值:
            - "Staging": 预发布/测试阶段
            - "Production": 生产阶段
            - "Archived": 归档阶段
            - "None": 移除阶段标记
        archive_existing: 是否归档当前处于目标阶段的其他版本，默认 False
        
    Returns:
        是否成功更新
    """
    warnings.warn(
        "transition_model_stage() 已废弃，MLflow 2.9.0 起推荐使用 set_model_alias()。"
        "例如: set_model_alias(model_name, 'champion', version) 替代 stage='Production'",
        DeprecationWarning,
        stacklevel=2
    )
    
    config = get_config()
    if not config.mlflow_enabled or not MLFLOW_INSTALLED:
        return False
    
    # 将 Stage 映射到 Alias（新方式）
    stage_to_alias = {
        "Production": config.mlflow_production_alias,
        "Staging": config.mlflow_staging_alias,
    }
    
    if stage in stage_to_alias:
        # 使用新的 Alias API
        alias = stage_to_alias[stage]
        return set_model_alias(model_name, alias, version)
    elif stage == "Archived" or stage == "None":
        # 对于 Archived/None，删除所有别名
        try:
            client = MlflowClient()
            # 获取当前版本的别名并删除
            model_version = client.get_model_version(name=model_name, version=version)
            if hasattr(model_version, 'aliases') and model_version.aliases:
                for alias in model_version.aliases:
                    delete_model_alias(model_name, alias)
            logger.info(f"已清除模型 {model_name} 版本 {version} 的所有别名")
            return True
        except Exception as e:
            logger.warning(f"清除模型别名失败: {e}")
            return False
    else:
        logger.error(f"无效的阶段: {stage}")
        return False


def set_model_alias(
    model_name: str,
    alias: str,
    version: str
) -> bool:
    """
    为模型版本设置别名。
    
    别名是 MLflow 2.9.0+ 推荐的模型版本管理方式，替代废弃的 Stage API。
    常用别名:
    - "champion": 生产环境当前版本（替代 Production stage）
    - "challenger": 待验证的候选版本（替代 Staging stage）
    
    Args:
        model_name: 模型名称
        alias: 别名（如 "champion", "challenger", "v1-stable"）
        version: 模型版本号
        
    Returns:
        是否成功设置
        
    Example:
        >>> # 将版本 2 设为生产版本
        >>> set_model_alias("joke-generator", "champion", "2")
        True
        >>> # 加载时使用: models:/joke-generator@champion
    """
    config = get_config()
    if not config.mlflow_enabled or not MLFLOW_INSTALLED:
        return False
    
    try:
        client = MlflowClient()
        client.set_registered_model_alias(
            name=model_name,
            alias=alias,
            version=version
        )
        logger.info(f"已设置模型 {model_name} 版本 {version} 的别名: @{alias}")
        return True
        
    except Exception as e:
        logger.warning(f"设置模型别名失败: {e}")
        return False


def delete_model_alias(
    model_name: str,
    alias: str
) -> bool:
    """
    删除模型的别名。
    
    Args:
        model_name: 模型名称
        alias: 要删除的别名
        
    Returns:
        是否成功删除
        
    Example:
        >>> delete_model_alias("joke-generator", "challenger")
        True
    """
    config = get_config()
    if not config.mlflow_enabled or not MLFLOW_INSTALLED:
        return False
    
    try:
        client = MlflowClient()
        client.delete_registered_model_alias(
            name=model_name,
            alias=alias
        )
        logger.info(f"已删除模型 {model_name} 的别名: @{alias}")
        return True
        
    except Exception as e:
        logger.warning(f"删除模型别名失败: {e}")
        return False


def get_model_version_by_alias(
    model_name: str,
    alias: str
) -> Optional[str]:
    """
    根据别名获取模型版本号。
    
    Args:
        model_name: 模型名称
        alias: 别名（如 "champion", "challenger"）
        
    Returns:
        版本号，如果别名不存在返回 None
        
    Example:
        >>> version = get_model_version_by_alias("joke-generator", "champion")
        >>> print(version)  # "2"
    """
    config = get_config()
    if not config.mlflow_enabled or not MLFLOW_INSTALLED:
        return None
    
    try:
        client = MlflowClient()
        model_version = client.get_model_version_by_alias(
            name=model_name,
            alias=alias
        )
        return model_version.version
        
    except Exception as e:
        logger.debug(f"获取模型别名版本失败: {e}")
        return None


def get_mlflow_ui_url(
    run_id: Optional[str] = None,
    experiment_id: Optional[str] = None,
    model_name: Optional[str] = None,
    model_version: Optional[str] = None
) -> str:
    """
    获取 MLflow UI 的 URL。
    
    根据 Requirements 3.4，构造指向 MLflow UI 中对应页面的 URL。
    
    Args:
        run_id: 可选的 Run ID，如果提供则返回该 Run 的详情页 URL
        experiment_id: 可选的 Experiment ID，如果提供则返回该实验的页面 URL
        model_name: 可选的模型名称，如果提供则返回模型注册页面 URL
        model_version: 可选的模型版本，与 model_name 一起使用返回特定版本页面
        
    Returns:
        MLflow UI URL 字符串
        
    Example:
        >>> # 获取实验列表页面
        >>> get_mlflow_ui_url()
        'http://localhost:5000/#/experiments'
        
        >>> # 获取特定 Run 页面
        >>> get_mlflow_ui_url(run_id="abc123")
        'http://localhost:5000/#/experiments/0/runs/abc123'
        
        >>> # 获取模型注册页面
        >>> get_mlflow_ui_url(model_name="joke-generator")
        'http://localhost:5000/#/models/joke-generator'
        
        >>> # 获取特定模型版本页面
        >>> get_mlflow_ui_url(model_name="joke-generator", model_version="1")
        'http://localhost:5000/#/models/joke-generator/versions/1'
    """
    # 解析 tracking URI 获取基础 URL
    config = get_config()
    tracking_uri = config.mlflow_tracking_uri
    
    # 默认回退 URL
    default_fallback = "http://localhost:5000"
    
    # 如果是本地文件路径，使用配置的 UI URL 或默认值
    if tracking_uri.startswith("./") or tracking_uri.startswith("/"):
        base_url = config.mlflow_ui_base_url or default_fallback
    elif tracking_uri.startswith("file://"):
        base_url = config.mlflow_ui_base_url or default_fallback
    elif tracking_uri.startswith("http://") or tracking_uri.startswith("https://"):
        # 远程服务器，直接使用 tracking URI
        base_url = tracking_uri.rstrip("/")
    else:
        # 其他情况（如 databricks://），使用配置的 UI URL 或默认值
        base_url = config.mlflow_ui_base_url or default_fallback
    
    # 根据参数构造不同的 URL
    if model_name:
        # 模型注册页面
        if model_version:
            return f"{base_url}/#/models/{model_name}/versions/{model_version}"
        else:
            return f"{base_url}/#/models/{model_name}"
    elif run_id:
        # Run 详情页面
        # 尝试获取实际的 experiment_id
        exp_id = experiment_id or _get_experiment_id_for_run(run_id) or "0"
        return f"{base_url}/#/experiments/{exp_id}/runs/{run_id}"
    elif experiment_id:
        # 实验页面
        return f"{base_url}/#/experiments/{experiment_id}"
    else:
        # 默认返回实验列表页面
        return f"{base_url}/#/experiments"


def _get_experiment_id_for_run(run_id: str) -> Optional[str]:
    """
    获取 Run 所属的 Experiment ID。
    
    Args:
        run_id: MLflow Run ID
        
    Returns:
        Experiment ID，如果获取失败返回 None
    """
    config = get_config()
    if not config.mlflow_enabled or not MLFLOW_INSTALLED:
        return None
    
    try:
        client = MlflowClient()
        run = client.get_run(run_id)
        return run.info.experiment_id
        
    except Exception:
        # 静默失败，返回 None
        return None
