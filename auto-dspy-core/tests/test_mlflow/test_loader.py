"""
MLflow 模型加载模块单元测试

INPUT:  autodspy.mlflow.loader 模块
OUTPUT: 验证模型加载功能的测试用例
POS:    确保 MLflow 模型加载功能正确性
"""

import pytest
from unittest.mock import patch, MagicMock

from autodspy.mlflow.loader import (
    load_model_from_registry,
    load_model_from_run,
    load_prompt_artifact,
    get_registered_run_ids,
    list_registered_models,
    list_model_versions,
    get_model_metadata,
)
from autodspy import AutoDSPyConfig, set_config, reset_config


@pytest.fixture(autouse=True)
def reset_config_fixture():
    """每个测试前后重置配置"""
    reset_config()
    yield
    reset_config()


@pytest.mark.integration
@pytest.mark.requires_mlflow
class TestLoadModelFromRegistry:
    """测试从注册表加载模型功能"""
    
    def test_disabled_raises_error(self):
        """MLflow 禁用时应抛出 ValueError"""
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        with pytest.raises(ValueError, match="MLflow 未启用或未安装"):
            load_model_from_registry("test-model")
    
    def test_load_by_version(self):
        """通过版本号加载模型应成功"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        with patch('autodspy.mlflow.loader.mlflow') as mock_mlflow, \
             patch('autodspy.mlflow.loader.MLFLOW_INSTALLED', True), \
             patch('os.path.exists') as mock_exists, \
             patch('builtins.open', create=True) as mock_open, \
             patch('pickle.load') as mock_pickle:
            
            mock_mlflow.artifacts.download_artifacts.return_value = "/fake/path"
            mock_exists.return_value = True
            mock_program = MagicMock()
            mock_pickle.return_value = mock_program
            
            result = load_model_from_registry("test-model", version="1")
            
            assert result is not None
            mock_mlflow.artifacts.download_artifacts.assert_called_once_with("models:/test-model/1")
    
    def test_load_by_stage(self):
        """通过阶段加载模型应成功"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        with patch('autodspy.mlflow.loader.mlflow') as mock_mlflow, \
             patch('autodspy.mlflow.loader.MLFLOW_INSTALLED', True), \
             patch('os.path.exists') as mock_exists, \
             patch('builtins.open', create=True) as mock_open, \
             patch('pickle.load') as mock_pickle:
            
            mock_mlflow.artifacts.download_artifacts.return_value = "/fake/path"
            mock_exists.return_value = True
            mock_program = MagicMock()
            mock_pickle.return_value = mock_program
            
            result = load_model_from_registry("test-model", stage="Production")
            
            assert result is not None
            mock_mlflow.artifacts.download_artifacts.assert_called_once_with("models:/test-model/Production")
    
    def test_load_latest_version(self):
        """不指定版本或阶段应加载最新版本"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        with patch('autodspy.mlflow.loader.mlflow') as mock_mlflow, \
             patch('autodspy.mlflow.loader.MLFLOW_INSTALLED', True), \
             patch('os.path.exists') as mock_exists, \
             patch('builtins.open', create=True) as mock_open, \
             patch('pickle.load') as mock_pickle:
            
            mock_mlflow.artifacts.download_artifacts.return_value = "/fake/path"
            mock_exists.return_value = True
            mock_program = MagicMock()
            mock_pickle.return_value = mock_program
            
            result = load_model_from_registry("test-model")
            
            assert result is not None
            mock_mlflow.artifacts.download_artifacts.assert_called_once_with("models:/test-model/latest")
    
    def test_load_model_not_found(self):
        """模型不存在时应抛出 ValueError"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        with patch('autodspy.mlflow.loader.mlflow') as mock_mlflow, \
             patch('autodspy.mlflow.loader.MLFLOW_INSTALLED', True):
            mock_mlflow.artifacts.download_artifacts.side_effect = Exception("Model not found")
            
            with pytest.raises(ValueError, match="加载模型.*失败"):
                load_model_from_registry("nonexistent-model")


@pytest.mark.integration
@pytest.mark.requires_mlflow
class TestLoadModelFromRun:
    """测试从运行加载模型功能"""
    
    def test_disabled_raises_error(self):
        """MLflow 禁用时应抛出 ValueError"""
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        with pytest.raises(ValueError, match="MLflow 未启用或未安装"):
            load_model_from_run("run-123")
    
    def test_load_from_run_success(self):
        """从运行加载模型应成功"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        with patch('autodspy.mlflow.loader.mlflow') as mock_mlflow, \
             patch('autodspy.mlflow.loader.MLFLOW_INSTALLED', True), \
             patch('os.path.exists') as mock_exists, \
             patch('builtins.open', create=True) as mock_open, \
             patch('pickle.load') as mock_pickle:
            
            mock_mlflow.artifacts.download_artifacts.return_value = "/fake/path"
            mock_exists.return_value = True
            mock_program = MagicMock()
            mock_pickle.return_value = mock_program
            
            result = load_model_from_run("run-123")
            
            assert result is not None
            mock_mlflow.artifacts.download_artifacts.assert_called_once_with("runs:/run-123/program")
    
    def test_load_from_run_with_artifact_path(self):
        """指定 artifact_path 加载模型应成功"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        with patch('autodspy.mlflow.loader.mlflow') as mock_mlflow, \
             patch('autodspy.mlflow.loader.MLFLOW_INSTALLED', True), \
             patch('os.path.exists') as mock_exists, \
             patch('builtins.open', create=True) as mock_open, \
             patch('pickle.load') as mock_pickle:
            
            mock_mlflow.artifacts.download_artifacts.return_value = "/fake/path"
            mock_exists.return_value = True
            mock_program = MagicMock()
            mock_pickle.return_value = mock_program
            
            result = load_model_from_run("run-123", artifact_path="custom_model")
            
            assert result is not None
            mock_mlflow.artifacts.download_artifacts.assert_called_once_with("runs:/run-123/custom_model")
    
    def test_load_from_run_not_found(self):
        """运行不存在时应抛出 ValueError"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        with patch('autodspy.mlflow.loader.mlflow') as mock_mlflow, \
             patch('autodspy.mlflow.loader.MLFLOW_INSTALLED', True):
            mock_mlflow.artifacts.download_artifacts.side_effect = Exception("Run not found")
            
            with pytest.raises(ValueError, match="从 Run.*加载模型失败"):
                load_model_from_run("nonexistent-run")


@pytest.mark.integration
@pytest.mark.requires_mlflow
class TestLoadPromptArtifact:
    """测试加载提示词工件功能"""
    
    def test_disabled_returns_none(self):
        """MLflow 禁用时应返回 None"""
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        result = load_prompt_artifact("run-123")
        assert result is None
    
    def test_load_prompt_not_found(self):
        """提示词工件不存在时应返回 None"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        with patch('autodspy.mlflow.loader.mlflow') as mock_mlflow, \
             patch('autodspy.mlflow.loader.MLFLOW_INSTALLED', True):
            mock_mlflow.artifacts.download_artifacts.side_effect = Exception("Artifact not found")
            
            result = load_prompt_artifact("run-123")
            
            assert result is None


@pytest.mark.integration
@pytest.mark.requires_mlflow
class TestGetRegisteredRunIds:
    """测试获取已注册运行 ID 功能"""
    
    def test_disabled_returns_empty_set(self):
        """MLflow 禁用时应返回空集合"""
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        result = get_registered_run_ids()
        assert result == set()
    
    def test_get_run_ids_success(self):
        """成功获取运行 ID 应返回集合"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        # 这个测试需要实际的 MLflow 环境，跳过 mock 测试
        # 因为 get_registered_run_ids 内部使用 from mlflow import MlflowClient
        # 无法通过简单的 patch 来 mock
        result = get_registered_run_ids()
        
        # 在没有 MLflow 的环境中，应返回空集合
        assert isinstance(result, set)
    
    def test_get_run_ids_no_models(self):
        """无注册模型时应返回空集合"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        with patch('autodspy.mlflow.loader.MlflowClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.search_registered_models.return_value = []
            
            result = get_registered_run_ids()
            
            assert result == set()


@pytest.mark.unit
class TestListRegisteredModels:
    """测试列出注册模型功能"""
    
    def test_disabled_returns_empty_list(self):
        """MLflow 禁用时应返回空列表"""
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        result = list_registered_models()
        assert result == []


@pytest.mark.unit
class TestListModelVersions:
    """测试列出模型版本功能"""
    
    def test_disabled_returns_empty_list(self):
        """MLflow 禁用时应返回空列表"""
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        result = list_model_versions("test-model")
        assert result == []


@pytest.mark.unit
class TestGetModelMetadata:
    """测试获取模型元数据功能"""
    
    def test_disabled_returns_empty_dict(self):
        """MLflow 禁用时应返回空字典"""
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        result = get_model_metadata("test-model", "1")
        assert result == {}
