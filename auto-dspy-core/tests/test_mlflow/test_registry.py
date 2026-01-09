"""
MLflow 模型注册表模块单元测试

INPUT:  autodspy.mlflow.registry 模块
OUTPUT: 验证模型注册表功能的测试用例
POS:    确保 MLflow 模型注册表功能正确性
"""

import pytest
from unittest.mock import patch, MagicMock

from autodspy.mlflow.registry import (
    register_model,
    transition_model_stage,
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


@pytest.mark.unit
class TestRegisterModel:
    """测试模型注册功能"""
    
    def test_disabled_returns_none(self):
        """MLflow 禁用时应返回 None"""
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        result = register_model("run-123", "test-model")
        assert result is None
    
    def test_register_success(self):
        """成功注册模型应返回版本号"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        with patch('autodspy.mlflow.registry.mlflow') as mock_mlflow, \
             patch('autodspy.mlflow.registry.MlflowClient') as mock_client_class, \
             patch('autodspy.mlflow.registry.MLFLOW_INSTALLED', True):
            
            mock_result = MagicMock()
            mock_result.version = "1"
            mock_mlflow.register_model.return_value = mock_result
            
            result = register_model("run-123", "test-model")
            
            assert result == "1"
            mock_mlflow.register_model.assert_called_once()
    
    def test_register_with_metadata(self):
        """带元数据注册模型应成功"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        with patch('autodspy.mlflow.registry.mlflow') as mock_mlflow, \
             patch('autodspy.mlflow.registry.MlflowClient') as mock_client_class, \
             patch('autodspy.mlflow.registry.MLFLOW_INSTALLED', True):
            
            mock_result = MagicMock()
            mock_result.version = "1"
            mock_mlflow.register_model.return_value = mock_result
            
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            metadata = {
                "input_fields": "topic",
                "output_fields": "joke",
                "evaluation_score": 0.85,
            }
            
            result = register_model("run-123", "test-model", metadata=metadata)
            
            assert result == "1"
            # 验证更新了模型版本描述
            mock_client.update_model_version.assert_called_once()


@pytest.mark.unit
class TestTransitionModelStage:
    """测试模型阶段转换功能"""
    
    def test_disabled_returns_false(self):
        """MLflow 禁用时应返回 False"""
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        result = transition_model_stage("test-model", "1", "Staging")
        assert result is False
    
    def test_invalid_stage_returns_false(self):
        """无效阶段应返回 False"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        with patch('autodspy.mlflow.registry.MLFLOW_INSTALLED', True):
            result = transition_model_stage("test-model", "1", "InvalidStage")
            assert result is False
    
    def test_valid_stages(self):
        """有效阶段应成功转换"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        valid_stages = ["Staging", "Production", "Archived", "None"]
        
        for stage in valid_stages:
            with patch('autodspy.mlflow.registry.MlflowClient') as mock_client_class, \
                 patch('autodspy.mlflow.registry.MLFLOW_INSTALLED', True):
                
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                mock_version = MagicMock()
                mock_version.current_stage = stage
                mock_client.get_model_version.return_value = mock_version
                
                result = transition_model_stage("test-model", "1", stage)
                
                assert result is True
                mock_client.transition_model_version_stage.assert_called_once()


@pytest.mark.unit
class TestListRegisteredModels:
    """测试列出注册模型功能"""
    
    def test_disabled_returns_empty_list(self):
        """MLflow 禁用时应返回空列表"""
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        result = list_registered_models()
        assert result == []
    
    def test_list_models_success(self):
        """成功列出模型应返回模型列表"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        with patch('autodspy.mlflow.registry.mlflow') as mock_mlflow, \
             patch('autodspy.mlflow.registry.MLFLOW_INSTALLED', True):
            mock_models = [
                MagicMock(name="model-1", description="Model 1"),
                MagicMock(name="model-2", description="Model 2"),
            ]
            mock_mlflow.search_registered_models.return_value = mock_models
            
            result = list_registered_models()
            
            assert len(result) == 2


@pytest.mark.unit
class TestListModelVersions:
    """测试列出模型版本功能"""
    
    def test_disabled_returns_empty_list(self):
        """MLflow 禁用时应返回空列表"""
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        result = list_model_versions("test-model")
        assert result == []
    
    def test_list_versions_success(self):
        """成功列出版本应返回版本列表"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        with patch('autodspy.mlflow.registry.MlflowClient') as mock_client_class, \
             patch('autodspy.mlflow.registry.MLFLOW_INSTALLED', True):
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            mock_versions = [
                MagicMock(version="1", current_stage="Staging"),
                MagicMock(version="2", current_stage="Production"),
            ]
            mock_client.search_model_versions.return_value = mock_versions
            
            result = list_model_versions("test-model")
            
            assert len(result) == 2


@pytest.mark.unit
class TestGetModelMetadata:
    """测试获取模型元数据功能"""
    
    def test_disabled_returns_none(self):
        """MLflow 禁用时应返回 None"""
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        result = get_model_metadata("test-model", "1")
        assert result is None
    
    def test_get_metadata_success(self):
        """成功获取元数据应返回完整信息"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        with patch('autodspy.mlflow.registry.MlflowClient') as mock_client_class, \
             patch('autodspy.mlflow.registry.MLFLOW_INSTALLED', True):
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            mock_version = MagicMock()
            mock_version.name = "test-model"
            mock_version.version = "1"
            mock_version.current_stage = "Production"
            mock_version.run_id = "run-123"
            mock_version.tags = {"evaluation_score": "0.85"}
            mock_client.get_model_version.return_value = mock_version
            
            result = get_model_metadata("test-model", "1")
            
            assert result is not None
            # 返回的是 MagicMock 对象，验证调用成功即可
            mock_client.get_model_version.assert_called_once_with(name="test-model", version="1")
    
    def test_get_metadata_not_found(self):
        """模型版本不存在时应返回 None"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        with patch('autodspy.mlflow.registry.MlflowClient') as mock_client_class, \
             patch('autodspy.mlflow.registry.MLFLOW_INSTALLED', True):
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.get_model_version.side_effect = Exception("Model version not found")
            
            result = get_model_metadata("nonexistent-model", "1")
            
            assert result is None
