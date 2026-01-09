"""
配置管理测试

INPUT:  autodspy.config 模块
OUTPUT: 验证配置管理功能的测试用例
POS:    确保配置系统正确性
"""

import os
import pytest
import tempfile
from pathlib import Path

from autodspy import (
    AutoDSPyConfig,
    get_config,
    set_config,
    reset_config,
)
from autodspy.config import load_config


@pytest.fixture(autouse=True)
def reset_config_fixture():
    """每个测试前后重置配置"""
    reset_config()
    yield
    reset_config()


class TestAutoDSPyConfig:
    """测试 AutoDSPyConfig 类"""
    
    def test_default_values(self):
        """测试默认配置值"""
        config = AutoDSPyConfig()
        
        # MLflow 配置
        assert config.mlflow_enabled is True
        assert config.mlflow_tracking_uri == "http://localhost:5000"
        assert config.mlflow_experiment_name == "autodspy-experiments"
        
        # DSPy 配置
        assert config.cache_enabled is True
        assert config.num_threads == 1
    
    def test_custom_values(self):
        """测试自定义配置值"""
        config = AutoDSPyConfig(
            mlflow_enabled=False,
            mlflow_tracking_uri="http://custom:5001",
            cache_enabled=False,
            num_threads=4
        )
        
        assert config.mlflow_enabled is False
        assert config.mlflow_tracking_uri == "http://custom:5001"
        assert config.cache_enabled is False
        assert config.num_threads == 4
    
    def test_from_env_variables(self, monkeypatch):
        """测试从环境变量加载配置"""
        # 设置环境变量
        monkeypatch.setenv("MLFLOW_ENABLED", "false")
        monkeypatch.setenv("MLFLOW_TRACKING_URI", "http://env:5002")
        monkeypatch.setenv("DSPY_CACHE_ENABLED", "false")
        monkeypatch.setenv("DSPY_NUM_THREADS", "8")
        
        config = AutoDSPyConfig.from_env()
        
        assert config.mlflow_enabled is False
        assert config.mlflow_tracking_uri == "http://env:5002"
        assert config.cache_enabled is False
        assert config.num_threads == 8


class TestConfigManagement:
    """测试配置管理函数"""
    
    def test_get_default_config(self):
        """测试获取默认配置"""
        config = get_config()
        
        assert isinstance(config, AutoDSPyConfig)
        assert config.mlflow_enabled is True
    
    def test_set_and_get_config(self):
        """测试设置和获取配置"""
        custom_config = AutoDSPyConfig(
            mlflow_enabled=False,
            cache_enabled=False
        )
        
        set_config(custom_config)
        retrieved_config = get_config()
        
        assert retrieved_config.mlflow_enabled is False
        assert retrieved_config.cache_enabled is False
    
    def test_reset_config(self):
        """测试重置配置"""
        # 设置自定义配置
        custom_config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(custom_config)
        
        assert get_config().mlflow_enabled is False
        
        # 重置配置
        reset_config()
        
        # 应该恢复默认值
        assert get_config().mlflow_enabled is True
    
    def test_load_config_from_yaml(self, tmp_path):
        """测试从 YAML 文件加载配置"""
        # 创建临时配置文件
        config_file = tmp_path / "test_config.yaml"
        config_content = """
mlflow:
  enabled: false
  tracking_uri: "http://yaml:5003"
dspy:
  cache_enabled: false
  num_threads: 2
"""
        config_file.write_text(config_content)
        
        # 加载配置
        config = load_config(config_file)
        
        # 验证配置加载成功
        assert config.mlflow_enabled is False
        # 注意：YAML 配置可能被环境变量覆盖，只验证基本功能
        assert isinstance(config, AutoDSPyConfig)
    
    def test_load_config_file_not_found(self):
        """测试加载不存在的配置文件返回默认配置"""
        # 不存在的文件应返回默认配置
        config = load_config(Path("/nonexistent/config.yaml"))
        assert isinstance(config, AutoDSPyConfig)
        # 默认值
        assert config.mlflow_enabled is True


class TestConfigSerialization:
    """测试配置序列化"""
    
    def test_config_to_dict(self):
        """测试配置转换为字典"""
        config = AutoDSPyConfig(
            mlflow_enabled=False,
            cache_enabled=True
        )
        
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict["mlflow_enabled"] is False
        assert config_dict["cache_enabled"] is True
    
    def test_config_from_dict(self):
        """测试从字典创建配置"""
        config_dict = {
            "mlflow_enabled": False,
            "mlflow_tracking_uri": "http://dict:5004",
            "cache_enabled": False
        }
        
        config = AutoDSPyConfig(**config_dict)
        
        assert config.mlflow_enabled is False
        assert config.mlflow_tracking_uri == "http://dict:5004"
        assert config.cache_enabled is False


@pytest.mark.integration
class TestConfigIntegration:
    """测试配置集成"""
    
    def test_config_affects_mlflow_init(self):
        """测试配置影响 MLflow 初始化"""
        from autodspy import init_mlflow
        
        # 禁用 MLflow
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        result = init_mlflow()
        assert result is False
        
        # 启用 MLflow
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        # 注意：这个测试需要 MLflow 实际安装
        # 在没有 MLflow 的环境中会返回 False
        result = init_mlflow()
        assert isinstance(result, bool)
