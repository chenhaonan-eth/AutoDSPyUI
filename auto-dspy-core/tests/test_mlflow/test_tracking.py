"""
MLflow 追踪模块单元测试

INPUT:  autodspy.mlflow.tracking 模块
OUTPUT: 验证追踪模块核心功能的测试用例
POS:    确保 MLflow 集成功能正确性
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from autodspy import AutoDSPyConfig, set_config, reset_config

# 导入被测模块
from autodspy.mlflow.tracking import (
    truncate_param,
    compute_dataset_hash,
    get_mlflow_ui_url,
    init_mlflow,
    _serialize_value,
    track_compilation,
    log_compilation_metrics,
    log_compilation_artifacts,
    log_evaluation_table,
    log_dataset_metadata,
    register_model,
    transition_model_stage,
)


@pytest.fixture(autouse=True)
def reset_config_fixture():
    """每个测试前后重置配置"""
    reset_config()
    yield
    reset_config()


@pytest.mark.unit
class TestTruncateParam:
    """测试参数截断功能"""
    
    def test_short_string_unchanged(self):
        """短字符串应保持不变"""
        value = "short string"
        result = truncate_param(value)
        assert result == value
    
    def test_exact_limit_unchanged(self):
        """恰好达到限制的字符串应保持不变"""
        value = "a" * 500
        result = truncate_param(value)
        assert result == value
        assert len(result) == 500
    
    def test_long_string_truncated(self):
        """超长字符串应被截断并添加省略号"""
        value = "a" * 600
        result = truncate_param(value)
        assert len(result) == 500
        assert result.endswith("...")
        assert result == "a" * 497 + "..."
    
    def test_empty_string(self):
        """空字符串应保持不变"""
        result = truncate_param("")
        assert result == ""
    
    def test_custom_max_length(self):
        """自定义最大长度应生效"""
        value = "a" * 100
        result = truncate_param(value, max_length=50)
        assert len(result) == 50
        assert result.endswith("...")


@pytest.mark.unit
class TestComputeDatasetHash:
    """测试数据集哈希计算功能"""
    
    def test_same_data_same_hash(self):
        """相同数据应产生相同哈希"""
        df1 = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        df2 = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        
        hash1 = compute_dataset_hash(df1)
        hash2 = compute_dataset_hash(df2)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 哈希长度
    
    def test_different_data_different_hash(self):
        """不同数据应产生不同哈希"""
        df1 = pd.DataFrame({"a": [1, 2, 3]})
        df2 = pd.DataFrame({"a": [1, 2, 4]})
        
        hash1 = compute_dataset_hash(df1)
        hash2 = compute_dataset_hash(df2)
        
        assert hash1 != hash2
    
    def test_column_order_independent(self):
        """列顺序不应影响哈希（因为内部会排序）"""
        df1 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        df2 = pd.DataFrame({"b": [3, 4], "a": [1, 2]})
        
        hash1 = compute_dataset_hash(df1)
        hash2 = compute_dataset_hash(df2)
        
        assert hash1 == hash2
    
    def test_empty_dataframe(self):
        """空 DataFrame 应返回有效哈希"""
        df = pd.DataFrame()
        hash_value = compute_dataset_hash(df)
        
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64


@pytest.mark.unit
class TestGetMlflowUiUrl:
    """测试 MLflow UI URL 构造功能"""
    
    def test_local_path_default_url(self):
        """本地路径应使用默认服务器地址"""
        config = AutoDSPyConfig(mlflow_tracking_uri='./mlruns')
        set_config(config)
        
        url = get_mlflow_ui_url()
        assert url == "http://localhost:5000/#/experiments"
    
    def test_local_path_with_run_id(self):
        """本地路径带 run_id 应返回正确的 run 页面 URL"""
        config = AutoDSPyConfig(mlflow_tracking_uri='./mlruns')
        set_config(config)
        
        url = get_mlflow_ui_url("abc123")
        # experiment_id 默认为 0 或 None
        assert "abc123" in url
        assert "runs" in url
    
    def test_remote_server_url(self):
        """远程服务器应使用配置的 URI"""
        config = AutoDSPyConfig(mlflow_tracking_uri='http://mlflow.example.com:5000')
        set_config(config)
        
        url = get_mlflow_ui_url()
        assert url == "http://mlflow.example.com:5000/#/experiments"
    
    def test_model_name_url(self):
        """模型名称应返回模型注册页面 URL"""
        config = AutoDSPyConfig(mlflow_tracking_uri='./mlruns')
        set_config(config)
        
        url = get_mlflow_ui_url(model_name="joke-generator")
        assert url == "http://localhost:5000/#/models/joke-generator"
    
    def test_model_name_with_version_url(self):
        """模型名称和版本应返回特定版本页面 URL"""
        config = AutoDSPyConfig(mlflow_tracking_uri='./mlruns')
        set_config(config)
        
        url = get_mlflow_ui_url(model_name="joke-generator", model_version="1")
        assert url == "http://localhost:5000/#/models/joke-generator/versions/1"


@pytest.mark.unit
class TestInitMlflow:
    """测试 MLflow 初始化功能"""
    
    def test_disabled_returns_false(self):
        """MLflow 禁用时应返回 False"""
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        result = init_mlflow()
        assert result is False


@pytest.mark.unit
class TestSerializeValue:
    """测试值序列化功能"""
    
    def test_string_unchanged(self):
        """字符串应保持不变"""
        assert _serialize_value("hello") == "hello"
    
    def test_none_to_empty(self):
        """None 应转换为空字符串"""
        assert _serialize_value(None) == ""
    
    def test_dict_to_json(self):
        """字典应转换为 JSON 字符串"""
        result = _serialize_value({"key": "value"})
        assert '"key"' in result
        assert '"value"' in result
    
    def test_list_to_json(self):
        """列表应转换为 JSON 字符串"""
        result = _serialize_value([1, 2, 3])
        assert result == "[1, 2, 3]"
    
    def test_number_to_string(self):
        """数字应转换为字符串"""
        assert _serialize_value(42) == "42"
        assert _serialize_value(3.14) == "3.14"


@pytest.mark.integration
@pytest.mark.requires_mlflow
class TestTrackCompilation:
    """测试编译追踪上下文管理器"""
    
    def test_disabled_yields_none(self):
        """MLflow 禁用时应 yield None"""
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        with track_compilation("test_run", {"param": "value"}) as run:
            assert run is None


@pytest.mark.integration
@pytest.mark.requires_mlflow
class TestLogCompilationMetrics:
    """测试编译指标记录功能"""
    
    def test_disabled_does_nothing(self):
        """MLflow 禁用时应不执行任何操作"""
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        # 不应抛出异常
        log_compilation_metrics(0.5, 0.8, 100, 20)


@pytest.mark.integration
@pytest.mark.requires_mlflow
class TestLogCompilationArtifacts:
    """测试编译工件记录功能"""
    
    def test_disabled_does_nothing(self):
        """MLflow 禁用时应不执行任何操作"""
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        # 不应抛出异常
        log_compilation_artifacts("program.json", "prompt.json", "data.csv")


@pytest.mark.integration
@pytest.mark.requires_mlflow
class TestLogEvaluationTable:
    """测试评估结果记录功能"""
    
    def test_disabled_does_nothing(self):
        """MLflow 禁用时应不执行任何操作"""
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        results = [{"example_id": 0, "score": 0.9}]
        # 不应抛出异常
        log_evaluation_table(results)
    
    def test_empty_results_skipped(self):
        """空结果应被跳过"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        # 不应抛出异常
        log_evaluation_table([])


@pytest.mark.integration
@pytest.mark.requires_mlflow
class TestLogDatasetMetadata:
    """测试数据集元数据记录功能"""
    
    def test_disabled_does_nothing(self):
        """MLflow 禁用时应不执行任何操作"""
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        df = pd.DataFrame({"a": [1, 2, 3]})
        # 不应抛出异常
        log_dataset_metadata(df)


@pytest.mark.integration
@pytest.mark.requires_mlflow
class TestRegisterModel:
    """测试模型注册功能"""
    
    def test_disabled_returns_none(self):
        """MLflow 禁用时应返回 None"""
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        result = register_model("run123", "test-model")
        assert result is None
    
    def test_register_with_metadata(self):
        """带元数据的模型注册应正确处理"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        mock_result = MagicMock()
        mock_result.version = "1"
        
        with patch('autodspy.mlflow.tracking.mlflow') as mock_mlflow, \
             patch('autodspy.mlflow.tracking.MlflowClient') as mock_client_class, \
             patch('autodspy.mlflow.tracking.MLFLOW_INSTALLED', True):
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_mlflow.register_model.return_value = mock_result
            
            metadata = {
                "input_fields": "topic",
                "output_fields": "joke",
                "evaluation_score": 0.85,
                "instructions": "Generate a funny joke",
                "dspy_module": "ChainOfThought",
                "optimizer": "BootstrapFewShot"
            }
            
            result = register_model("run123", "test-model", metadata=metadata)
            
            assert result == "1"
            mock_mlflow.register_model.assert_called_once_with("runs:/run123/program", "test-model")
            # 验证元数据更新被调用
            mock_client.update_model_version.assert_called_once()


@pytest.mark.integration
@pytest.mark.requires_mlflow
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
        
        with patch('autodspy.mlflow.tracking.MLFLOW_INSTALLED', True):
            result = transition_model_stage("test-model", "1", "InvalidStage")
            assert result is False
    
    def test_valid_stages(self):
        """有效阶段应被接受"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        valid_stages = ["Staging", "Production", "Archived", "None"]
        
        for stage in valid_stages:
            with patch('autodspy.mlflow.tracking.MlflowClient') as mock_client_class, \
                 patch('autodspy.mlflow.tracking.MLFLOW_INSTALLED', True):
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                # 模拟 get_model_version 返回正确的阶段
                mock_version = MagicMock()
                mock_version.current_stage = stage
                mock_client.get_model_version.return_value = mock_version
                
                result = transition_model_stage("test-model", "1", stage)
                
                assert result is True
                mock_client.transition_model_version_stage.assert_called_once()
