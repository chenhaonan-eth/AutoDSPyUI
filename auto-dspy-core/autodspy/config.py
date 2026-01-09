"""
Auto-DSPy-Core 配置管理

INPUT:  环境变量, 配置文件 (YAML/TOML)
OUTPUT: AutoDSPyConfig 类, get_config(), set_config(), load_config() 函数
POS:    配置管理模块，被所有其他模块依赖

支持三种配置方式（优先级从高到低）：
1. 环境变量
2. 配置文件（YAML/TOML）
3. 默认值
"""

import os
import logging
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class AutoDSPyConfig:
    """Auto-DSPy 核心配置"""
    
    # ============ DSPy 配置 ============
    cache_enabled: bool = True
    num_threads: int = 1
    
    # 支持的模型列表
    supported_groq_models: List[str] = field(default_factory=lambda: [
        "mixtral-8x7b-32768",
        "gemma-7b-it",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "gemma2-9b-it"
    ])
    
    supported_google_models: List[str] = field(default_factory=lambda: [
        "gemini-1.5-flash-8b",
        "gemini-1.5-flash",
        "gemini-1.5-pro"
    ])
    
    supported_deepseek_models: List[str] = field(default_factory=lambda: [
        "deepseek-chat"
    ])
    
    # ============ 优化器参数 ============
    # MIPROv2
    mipro_num_candidates: int = 10
    mipro_init_temperature: float = 1.0
    mipro_num_batches: int = 30
    mipro_max_bootstrapped_demos: int = 8
    mipro_max_labeled_demos: int = 16
    
    # BootstrapFewShot
    bootstrap_max_bootstrapped_demos: int = 4
    bootstrap_max_labeled_demos: int = 4
    
    # ============ MLflow 配置 ============
    mlflow_enabled: bool = True
    mlflow_tracking_uri: str = "http://localhost:5000"
    mlflow_experiment_name: str = "autodspy-experiments"
    mlflow_ui_base_url: str = ""
    
    # MLflow Autolog
    mlflow_log_traces: bool = True
    mlflow_log_traces_from_compile: bool = False
    mlflow_log_traces_from_eval: bool = True
    mlflow_log_compiles: bool = True
    mlflow_log_evals: bool = True
    
    # MLflow Model Alias (替代废弃的 Stage API)
    mlflow_production_alias: str = "champion"
    mlflow_staging_alias: str = "challenger"
    
    # ============ Serving 配置 ============
    model_cache_enabled: bool = True
    model_cache_ttl: int = 3600
    feedback_enabled: bool = True
    
    @classmethod
    def from_env(cls) -> "AutoDSPyConfig":
        """从环境变量加载配置"""
        return cls(
            # DSPy
            cache_enabled=os.getenv("DSPY_CACHE_ENABLED", "true").lower() == "true",
            num_threads=int(os.getenv("DSPY_NUM_THREADS", "1")),
            
            # 优化器
            mipro_num_candidates=int(os.getenv("MIPRO_NUM_CANDIDATES", "10")),
            mipro_init_temperature=float(os.getenv("MIPRO_INIT_TEMPERATURE", "1.0")),
            mipro_num_batches=int(os.getenv("MIPRO_NUM_BATCHES", "30")),
            mipro_max_bootstrapped_demos=int(os.getenv("MIPRO_MAX_BOOTSTRAPPED_DEMOS", "8")),
            mipro_max_labeled_demos=int(os.getenv("MIPRO_MAX_LABELED_DEMOS", "16")),
            bootstrap_max_bootstrapped_demos=int(os.getenv("BOOTSTRAP_MAX_BOOTSTRAPPED_DEMOS", "4")),
            bootstrap_max_labeled_demos=int(os.getenv("BOOTSTRAP_MAX_LABELED_DEMOS", "4")),
            
            # MLflow
            mlflow_enabled=os.getenv("MLFLOW_ENABLED", "true").lower() == "true",
            mlflow_tracking_uri=os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"),
            mlflow_experiment_name=os.getenv("MLFLOW_EXPERIMENT_NAME", "autodspy-experiments"),
            mlflow_ui_base_url=os.getenv("MLFLOW_UI_BASE_URL", ""),
            mlflow_log_traces=os.getenv("MLFLOW_LOG_TRACES", "true").lower() == "true",
            mlflow_log_traces_from_compile=os.getenv("MLFLOW_LOG_TRACES_FROM_COMPILE", "false").lower() == "true",
            mlflow_log_traces_from_eval=os.getenv("MLFLOW_LOG_TRACES_FROM_EVAL", "true").lower() == "true",
            mlflow_log_compiles=os.getenv("MLFLOW_LOG_COMPILES", "true").lower() == "true",
            mlflow_log_evals=os.getenv("MLFLOW_LOG_EVALS", "true").lower() == "true",
            mlflow_production_alias=os.getenv("MLFLOW_PRODUCTION_ALIAS", "champion"),
            mlflow_staging_alias=os.getenv("MLFLOW_STAGING_ALIAS", "challenger"),
            
            # Serving
            model_cache_enabled=os.getenv("MODEL_CACHE_ENABLED", "true").lower() == "true",
            model_cache_ttl=int(os.getenv("MODEL_CACHE_TTL", "3600")),
            feedback_enabled=os.getenv("FEEDBACK_ENABLED", "true").lower() == "true",
        )
    
    @classmethod
    def from_file(cls, config_path: Path) -> "AutoDSPyConfig":
        """从配置文件加载（支持 YAML）"""
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # 扁平化嵌套配置
            flat_data = {}
            if 'dspy' in data:
                flat_data['cache_enabled'] = data['dspy'].get('cache_enabled', True)
                flat_data['num_threads'] = data['dspy'].get('num_threads', 1)
            
            if 'optimizer' in data:
                if 'mipro' in data['optimizer']:
                    mipro = data['optimizer']['mipro']
                    flat_data['mipro_num_candidates'] = mipro.get('num_candidates', 10)
                    flat_data['mipro_init_temperature'] = mipro.get('init_temperature', 1.0)
                    flat_data['mipro_num_batches'] = mipro.get('num_batches', 30)
                    flat_data['mipro_max_bootstrapped_demos'] = mipro.get('max_bootstrapped_demos', 8)
                    flat_data['mipro_max_labeled_demos'] = mipro.get('max_labeled_demos', 16)
                
                if 'bootstrap' in data['optimizer']:
                    bootstrap = data['optimizer']['bootstrap']
                    flat_data['bootstrap_max_bootstrapped_demos'] = bootstrap.get('max_bootstrapped_demos', 4)
                    flat_data['bootstrap_max_labeled_demos'] = bootstrap.get('max_labeled_demos', 4)
            
            if 'mlflow' in data:
                mlflow_cfg = data['mlflow']
                flat_data['mlflow_enabled'] = mlflow_cfg.get('enabled', True)
                flat_data['mlflow_tracking_uri'] = mlflow_cfg.get('tracking_uri', 'http://localhost:5000')
                flat_data['mlflow_experiment_name'] = mlflow_cfg.get('experiment_name', 'autodspy-experiments')
                flat_data['mlflow_ui_base_url'] = mlflow_cfg.get('ui_base_url', '')
                
                if 'autolog' in mlflow_cfg:
                    autolog = mlflow_cfg['autolog']
                    flat_data['mlflow_log_traces'] = autolog.get('log_traces', True)
                    flat_data['mlflow_log_traces_from_compile'] = autolog.get('log_traces_from_compile', False)
                    flat_data['mlflow_log_traces_from_eval'] = autolog.get('log_traces_from_eval', True)
                    flat_data['mlflow_log_compiles'] = autolog.get('log_compiles', True)
                    flat_data['mlflow_log_evals'] = autolog.get('log_evals', True)
            
            if 'serving' in data:
                serving = data['serving']
                flat_data['model_cache_enabled'] = serving.get('model_cache_enabled', True)
                flat_data['model_cache_ttl'] = serving.get('model_cache_ttl', 3600)
                flat_data['feedback_enabled'] = serving.get('feedback_enabled', True)
            
            # 创建配置实例，使用默认值填充未提供的字段
            config = cls()
            for key, value in flat_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            return config
            
        except ImportError:
            logger.warning("PyYAML 未安装，无法加载 YAML 配置文件")
            return cls()
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}")
            return cls()
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "AutoDSPyConfig":
        """
        加载配置（优先级：环境变量 > 配置文件 > 默认值）
        
        Args:
            config_path: 配置文件路径（可选）
        
        Returns:
            配置实例
        """
        # 1. 从配置文件加载（如果提供）
        if config_path and config_path.exists():
            config = cls.from_file(config_path)
            logger.info(f"已从配置文件加载: {config_path}")
        else:
            config = cls()
        
        # 2. 环境变量覆盖
        env_config = cls.from_env()
        
        # 合并配置（环境变量优先）
        for key in asdict(config).keys():
            env_value = getattr(env_config, key)
            default_value = getattr(cls(), key)
            # 如果环境变量值不是默认值，则使用环境变量
            if env_value != default_value:
                setattr(config, key, env_value)
        
        return config
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)


# 全局配置实例
_config: Optional[AutoDSPyConfig] = None


def get_config() -> AutoDSPyConfig:
    """
    获取全局配置实例（单例模式）
    
    Returns:
        配置实例
    """
    global _config
    if _config is None:
        _config = AutoDSPyConfig.load()
    return _config


def set_config(config: AutoDSPyConfig):
    """
    设置全局配置
    
    Args:
        config: 配置实例
    """
    global _config
    _config = config


def load_config(config_path: Path) -> AutoDSPyConfig:
    """
    从文件加载配置并设置为全局配置
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        配置实例
    """
    config = AutoDSPyConfig.load(config_path)
    set_config(config)
    return config


def reset_config():
    """重置全局配置（用于测试）"""
    global _config
    _config = None
