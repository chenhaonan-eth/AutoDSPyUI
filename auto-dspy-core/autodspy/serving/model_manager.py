"""
模型加载和缓存管理器

INPUT:  MLflow Model Registry, dspyui.config.APIConfig
OUTPUT: ModelManager 类，提供 load_model(), invalidate_cache(), get_cache_stats() 方法
POS:    核心服务层，负责模型加载、缓存和版本管理，被 API 路由层调用

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import logging
import os
import pickle
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import dspy

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


@dataclass
class CachedModel:
    """缓存的模型实例"""
    program: Any              # DSPy program 实例
    version: str              # 模型版本号
    loaded_at: datetime       # 加载时间
    hit_count: int = 0        # 缓存命中次数
    
    def is_expired(self, ttl: int) -> bool:
        """检查缓存是否过期"""
        if ttl <= 0:
            return False  # TTL <= 0 表示永不过期
        elapsed = (datetime.now() - self.loaded_at).total_seconds()
        return elapsed > ttl


@dataclass
class CacheStats:
    """缓存统计信息"""
    total_loads: int = 0      # 总加载次数
    cache_hits: int = 0       # 缓存命中次数
    cache_misses: int = 0     # 缓存未命中次数
    invalidations: int = 0    # 缓存失效次数
    
    @property
    def hit_rate(self) -> float:
        """缓存命中率"""
        if self.total_loads == 0:
            return 0.0
        return self.cache_hits / self.total_loads


class ModelManager:
    """
    模型加载和缓存管理器
    
    支持三种模型加载方式:
    - 版本号: models:/name/3
    - 阶段: models:/name@Production
    - 别名: models:/name@champion
    
    提供模型缓存功能，避免重复加载相同版本的模型。
    
    Example:
        >>> manager = ModelManager(cache_enabled=True, cache_ttl=3600)
        >>> program, version = manager.load_model("joke-generator", stage="Production")
        >>> program(**inputs)
    """
    
    def __init__(
        self,
        cache_enabled: bool = True,
        cache_ttl: int = 3600
    ):
        """
        初始化 ModelManager
        
        Args:
            cache_enabled: 是否启用模型缓存
            cache_ttl: 缓存过期时间（秒），0 表示永不过期
        """
        self._cache: Dict[str, CachedModel] = {}
        self._cache_enabled = cache_enabled
        self._cache_ttl = cache_ttl
        self._stats = CacheStats()
        self._lock = threading.RLock()  # 线程安全锁
        
        logger.info(
            f"ModelManager 初始化: cache_enabled={cache_enabled}, cache_ttl={cache_ttl}s"
        )
    
    def _build_model_uri(
        self,
        name: str,
        version: Optional[str] = None,
        stage: Optional[str] = None,
        alias: Optional[str] = None
    ) -> str:
        """
        构建 MLflow 模型 URI
        
        Args:
            name: 模型名称
            version: 版本号 (e.g., "3")
            stage: 阶段 (e.g., "Production", "Staging")
            alias: 别名 (e.g., "champion", "challenger")
            
        Returns:
            MLflow 模型 URI
        """
        if version:
            return f"models:/{name}/{version}"
        elif alias:
            return f"models:/{name}@{alias}"
        elif stage:
            return f"models:/{name}@{stage}"
        else:
            # 默认使用 latest
            return f"models:/{name}/latest"
    
    def _get_cache_key(
        self,
        name: str,
        version: Optional[str] = None,
        stage: Optional[str] = None,
        alias: Optional[str] = None
    ) -> str:
        """
        生成缓存键
        
        对于 stage 和 alias，需要解析实际版本号作为缓存键
        """
        if version:
            return f"{name}:v{version}"
        elif alias:
            return f"{name}@{alias}"
        elif stage:
            return f"{name}@{stage}"
        else:
            return f"{name}:latest"
    
    def _resolve_version(
        self,
        name: str,
        stage: Optional[str] = None,
        alias: Optional[str] = None
    ) -> Optional[str]:
        """
        解析 stage 或 alias 对应的实际版本号
        
        Args:
            name: 模型名称
            stage: 阶段
            alias: 别名
            
        Returns:
            实际版本号，如果无法解析返回 None
        """
        config = get_config()
        if not config.mlflow_enabled or not MLFLOW_INSTALLED:
            return None
            
        try:
            client = MlflowClient()
            
            if alias:
                # 通过别名获取版本
                try:
                    model_version = client.get_model_version_by_alias(name, alias)
                    return model_version.version
                except Exception as e:
                    logger.warning(f"无法通过别名 {alias} 获取版本: {e}")
                    return None
                    
            elif stage:
                # 通过阶段获取最新版本
                versions = client.search_model_versions(f"name='{name}'")
                for v in versions:
                    if v.current_stage == stage:
                        return v.version
                return None
                
        except Exception as e:
            logger.warning(f"解析版本失败: {e}")
            return None
    
    def _load_from_mlflow(self, model_uri: str) -> Tuple[Any, str]:
        """
        从 MLflow 加载模型
        
        Args:
            model_uri: MLflow 模型 URI
            
        Returns:
            (program, version) 元组
            
        Raises:
            ValueError: 加载失败时
        """
        config = get_config()
        if not config.mlflow_enabled or not MLFLOW_INSTALLED:
            raise ValueError("MLflow 未启用或未安装")
        
        logger.info(f"正在从 MLflow 加载模型: {model_uri}")
        
        try:
            # 下载模型工件
            download_path = mlflow.artifacts.download_artifacts(model_uri)
            
            # 尝试加载 MLflow DSPy flavor (pickle 格式)
            model_file = os.path.join(download_path, "data", "model.pkl")
            if os.path.exists(model_file):
                with open(model_file, "rb") as f:
                    loaded = pickle.load(f)
                
                # MLflow 包装器：实际程序在 .model 属性中
                if hasattr(loaded, 'model'):
                    program = loaded.model
                else:
                    program = loaded
                
                # 从 URI 提取版本信息
                version = self._extract_version_from_uri(model_uri)
                logger.info(f"成功加载模型 (pickle): {model_uri}")
                return program, version
            
            # 备选：查找 program.json (dspy.save 格式)
            program_file = os.path.join(download_path, "program.json")
            if os.path.exists(program_file):
                program = dspy.load(program_file)
                version = self._extract_version_from_uri(model_uri)
                logger.info(f"成功加载模型 (json): {model_uri}")
                return program, version
            
            # 列出下载内容帮助调试
            files = []
            for root, dirs, filenames in os.walk(download_path):
                for f in filenames:
                    files.append(os.path.join(root, f))
            logger.error(f"找不到有效的模型文件，下载的文件: {files}")
            raise ValueError("找不到模型程序文件 (model.pkl 或 program.json)")
            
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            raise ValueError(f"加载模型失败: {e}")
    
    def _extract_version_from_uri(self, model_uri: str) -> str:
        """从模型 URI 提取版本信息"""
        # models:/name/3 -> "3"
        # models:/name@Production -> "Production"
        # models:/name@champion -> "champion"
        if "/" in model_uri:
            parts = model_uri.split("/")
            last_part = parts[-1]
            if "@" in last_part:
                return last_part.split("@")[-1]
            return last_part
        return "unknown"
    
    def load_model(
        self,
        name: str,
        version: Optional[str] = None,
        stage: Optional[str] = None,
        alias: Optional[str] = None
    ) -> Tuple[Any, str]:
        """
        加载模型，支持三种方式:
        - version: models:/name/3
        - stage: models:/name@Production
        - alias: models:/name@champion
        
        Args:
            name: 模型名称
            version: 指定版本号
            stage: 指定阶段 ("Staging", "Production", "Archived")
            alias: 指定别名 ("champion", "challenger" 等)
            
        Returns:
            (program, actual_version) 元组
            
        Raises:
            ValueError: 当模型不存在或加载失败时
            
        Example:
            >>> program, ver = manager.load_model("joke-generator", version="3")
            >>> program, ver = manager.load_model("joke-generator", stage="Production")
            >>> program, ver = manager.load_model("joke-generator", alias="champion")
        """
        with self._lock:
            self._stats.total_loads += 1
            
            # 生成缓存键
            cache_key = self._get_cache_key(name, version, stage, alias)
            
            # 检查缓存
            if self._cache_enabled and cache_key in self._cache:
                cached = self._cache[cache_key]
                
                # 检查是否过期
                if not cached.is_expired(self._cache_ttl):
                    cached.hit_count += 1
                    self._stats.cache_hits += 1
                    logger.debug(f"缓存命中: {cache_key}")
                    return cached.program, cached.version
                else:
                    # 缓存过期，删除
                    logger.debug(f"缓存过期: {cache_key}")
                    del self._cache[cache_key]
            
            # 缓存未命中，从 MLflow 加载
            self._stats.cache_misses += 1
            
            # 构建模型 URI
            model_uri = self._build_model_uri(name, version, stage, alias)
            
            # 加载模型
            program, actual_version = self._load_from_mlflow(model_uri)
            
            # 如果是通过 stage 或 alias 加载，尝试解析实际版本号
            if not version and (stage or alias):
                resolved_version = self._resolve_version(name, stage, alias)
                if resolved_version:
                    actual_version = resolved_version
            
            # 缓存模型
            if self._cache_enabled:
                self._cache[cache_key] = CachedModel(
                    program=program,
                    version=actual_version,
                    loaded_at=datetime.now()
                )
                logger.debug(f"已缓存模型: {cache_key}")
            
            return program, actual_version
    
    def invalidate_cache(self, name: str) -> int:
        """
        使指定模型的所有缓存失效
        
        Args:
            name: 模型名称
            
        Returns:
            被清除的缓存条目数量
        """
        with self._lock:
            keys_to_remove = [
                key for key in self._cache.keys()
                if key.startswith(f"{name}:")  or key.startswith(f"{name}@")
            ]
            
            for key in keys_to_remove:
                del self._cache[key]
                self._stats.invalidations += 1
            
            if keys_to_remove:
                logger.info(f"已清除模型 {name} 的 {len(keys_to_remove)} 个缓存条目")
            
            return len(keys_to_remove)
    
    def invalidate_all(self) -> int:
        """
        清除所有缓存
        
        Returns:
            被清除的缓存条目数量
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._stats.invalidations += count
            logger.info(f"已清除所有 {count} 个缓存条目")
            return count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            包含缓存统计的字典:
            - total_loads: 总加载次数
            - cache_hits: 缓存命中次数
            - cache_misses: 缓存未命中次数
            - hit_rate: 缓存命中率
            - cached_models: 当前缓存的模型数量
            - invalidations: 缓存失效次数
        """
        with self._lock:
            return {
                "total_loads": self._stats.total_loads,
                "cache_hits": self._stats.cache_hits,
                "cache_misses": self._stats.cache_misses,
                "hit_rate": self._stats.hit_rate,
                "cached_models": len(self._cache),
                "invalidations": self._stats.invalidations,
                "cache_enabled": self._cache_enabled,
                "cache_ttl": self._cache_ttl,
            }
    
    def get_cached_models(self) -> Dict[str, Dict[str, Any]]:
        """
        获取当前缓存的模型信息
        
        Returns:
            缓存模型信息字典，键为缓存键，值包含:
            - version: 模型版本
            - loaded_at: 加载时间
            - hit_count: 命中次数
            - is_expired: 是否已过期
        """
        with self._lock:
            result = {}
            for key, cached in self._cache.items():
                result[key] = {
                    "version": cached.version,
                    "loaded_at": cached.loaded_at.isoformat(),
                    "hit_count": cached.hit_count,
                    "is_expired": cached.is_expired(self._cache_ttl),
                }
            return result
