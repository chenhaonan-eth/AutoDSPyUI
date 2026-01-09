"""
MLflow 服务模块单元测试

INPUT:  autodspy.mlflow.service 模块
OUTPUT: 验证模型注册服务功能的测试用例
POS:    确保 MLflow 服务层功能正确性
"""

import pytest
from unittest.mock import patch, MagicMock

from autodspy.mlflow.service import (
    register_compiled_model,
    validate_model_name,
    ModelRegistrationResult,
)


@pytest.mark.unit
class TestValidateModelName:
    """测试模型名称验证功能"""
    
    def test_empty_name(self):
        """空名称应返回 False"""
        is_valid, error_code = validate_model_name("")
        assert is_valid is False
        assert error_code == "empty_name"
    
    def test_whitespace_only_name(self):
        """仅空格的名称应返回 False"""
        is_valid, error_code = validate_model_name("   ")
        assert is_valid is False
        assert error_code == "empty_name"
    
    def test_valid_name(self):
        """有效名称应返回 True"""
        is_valid, error_code = validate_model_name("valid-model")
        assert is_valid is True
        assert error_code is None
    
    def test_valid_name_with_underscores(self):
        """带下划线的有效名称应返回 True"""
        is_valid, error_code = validate_model_name("valid_model_name")
        assert is_valid is True
        assert error_code is None
    
    def test_valid_name_with_numbers(self):
        """带数字的有效名称应返回 True"""
        is_valid, error_code = validate_model_name("model-v1")
        assert is_valid is True
        assert error_code is None


@pytest.mark.unit
class TestRegisterCompiledModel:
    """测试编译模型注册功能"""
    
    def test_disabled_mlflow(self):
        """MLflow 禁用时应返回失败结果"""
        from autodspy import AutoDSPyConfig, set_config
        
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        result = register_compiled_model("run_id", "name", {})
        assert result.success is False
        assert result.error_code == "mlflow_disabled"
    
    def test_no_run_id(self):
        """无 run_id 时应返回失败结果"""
        from autodspy import AutoDSPyConfig, set_config
        
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        result = register_compiled_model(None, "name", {})
        assert result.success is False
        assert result.error_code == "no_run_id"
    
    def test_empty_run_id(self):
        """空 run_id 时应返回失败结果"""
        from autodspy import AutoDSPyConfig, set_config
        
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        result = register_compiled_model("", "name", {})
        assert result.success is False
        assert result.error_code == "no_run_id"
    
    def test_invalid_model_name(self):
        """无效模型名称应返回失败结果"""
        from autodspy import AutoDSPyConfig, set_config
        
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        result = register_compiled_model("run-123", "", {})
        assert result.success is False
        assert result.error_code == "empty_name"
    
    def test_successful_registration(self):
        """成功注册应返回正确结果"""
        from autodspy import AutoDSPyConfig, set_config
        
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        with patch('autodspy.mlflow.service.register_model') as mock_register:
            with patch('autodspy.mlflow.service.get_mlflow_ui_url') as mock_url:
                mock_register.return_value = "1"
                mock_url.return_value = "http://mlflow/model/1"
                
                prompt_details = {
                    "input_fields": ["a"],
                    "output_fields": ["b"],
                    "instructions": "do it",
                    "evaluation_score": 0.9
                }
                
                result = register_compiled_model("run-123", "test-model", prompt_details)
                
                assert result.success is True
                assert result.version == "1"
                assert result.model_url == "http://mlflow/model/1"
                mock_register.assert_called_once()
    
    def test_registration_failure(self):
        """注册失败应返回失败结果"""
        from autodspy import AutoDSPyConfig, set_config
        
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        with patch('autodspy.mlflow.service.register_model') as mock_register:
            mock_register.return_value = None
            
            result = register_compiled_model("run-123", "test-model", {})
            assert result.success is False
            assert result.error_code == "registration_failed"
    
    def test_registration_exception(self):
        """注册异常应返回失败结果"""
        from autodspy import AutoDSPyConfig, set_config
        
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        with patch('autodspy.mlflow.service.register_model') as mock_register:
            mock_register.side_effect = Exception("MLflow error")
            
            result = register_compiled_model("run-123", "test-model", {})
            assert result.success is False
            assert result.error_code == "exception"
            assert "MLflow error" in result.error_message


@pytest.mark.unit
class TestModelRegistrationResult:
    """测试模型注册结果数据类"""
    
    def test_success_result(self):
        """成功结果应包含所有必要字段"""
        result = ModelRegistrationResult(
            success=True,
            version="1",
            model_url="http://mlflow/model/1"
        )
        
        assert result.success is True
        assert result.version == "1"
        assert result.model_url == "http://mlflow/model/1"
        assert result.error_code is None
        assert result.error_message is None
    
    def test_failure_result(self):
        """失败结果应包含错误信息"""
        result = ModelRegistrationResult(
            success=False,
            error_code="test_error",
            error_message="Test error message"
        )
        
        assert result.success is False
        assert result.error_code == "test_error"
        assert result.error_message == "Test error message"
        assert result.version is None
        assert result.model_url is None
