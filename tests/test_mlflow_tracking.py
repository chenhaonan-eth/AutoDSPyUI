"""
MLflow 追踪模块单元测试

INPUT:  dspyui.core.mlflow_tracking 模块
OUTPUT: 验证追踪模块核心功能的测试用例
POS:    确保 MLflow 集成功能正确性

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import os
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

# 检查 MLflow 是否可用
try:
    import mlflow
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

# 整个模块需要 MLflow
pytestmark = pytest.mark.skipif(
    not MLFLOW_AVAILABLE,
    reason="MLflow 未安装，跳过 MLflow 追踪模块测试"
)

# 导入被测模块
from autodspy import (
    get_mlflow_ui_url,
    init_mlflow,
    track_compilation,
    log_compilation_metrics,
    log_compilation_artifacts,
    log_evaluation_table,
    register_model,
    transition_model_stage,
)
from autodspy.mlflow.tracking import (
    truncate_param,
    compute_dataset_hash,
    _serialize_value,
    log_dataset_metadata,
)


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


class TestGetMlflowUiUrl:
    """测试 MLflow UI URL 构造功能"""
    
    @patch('dspyui.core.mlflow_tracking.MLFLOW_TRACKING_URI', './mlruns')
    def test_local_path_default_url(self):
        """本地路径应使用默认服务器地址"""
        url = get_mlflow_ui_url()
        assert url == "http://localhost:5000/#/experiments"
    
    @patch('dspyui.core.mlflow_tracking.MLFLOW_TRACKING_URI', './mlruns')
    def test_local_path_with_run_id(self):
        """本地路径带 run_id 应返回正确的 run 页面 URL"""
        url = get_mlflow_ui_url("abc123")
        assert url == "http://localhost:5000/#/experiments/0/runs/abc123"
    
    @patch('dspyui.core.mlflow_tracking.MLFLOW_TRACKING_URI', 'http://mlflow.example.com:5000')
    def test_remote_server_url(self):
        """远程服务器应使用配置的 URI"""
        url = get_mlflow_ui_url()
        assert url == "http://mlflow.example.com:5000/#/experiments"
    
    @patch('dspyui.core.mlflow_tracking.MLFLOW_TRACKING_URI', 'http://mlflow.example.com:5000/')
    def test_remote_server_trailing_slash(self):
        """远程服务器 URI 末尾斜杠应被处理"""
        url = get_mlflow_ui_url()
        assert url == "http://mlflow.example.com:5000/#/experiments"


class TestInitMlflow:
    """测试 MLflow 初始化功能"""
    
    @patch('dspyui.core.mlflow_tracking.MLFLOW_ENABLED', False)
    def test_disabled_returns_false(self):
        """MLflow 禁用时应返回 False"""
        result = init_mlflow()
        assert result is False
    
    def test_enabled_with_mlflow_installed(self):
        """MLflow 启用且已安装时应正确初始化"""
        # 这个测试验证当 MLflow 已安装时的行为
        # 由于 MLflow 已作为依赖安装，我们可以直接测试
        with patch('dspyui.core.mlflow_tracking.MLFLOW_ENABLED', True):
            with patch('mlflow.set_tracking_uri') as mock_set_uri:
                with patch('mlflow.set_experiment') as mock_set_exp:
                    with patch('mlflow.dspy.autolog') as mock_autolog:
                        result = init_mlflow()
                        # 验证 MLflow 函数被调用
                        mock_set_uri.assert_called_once()
                        mock_set_exp.assert_called_once()
                        mock_autolog.assert_called_once()
                        assert result is True


class TestTrackCompilation:
    """测试编译追踪上下文管理器"""
    
    @patch('dspyui.core.mlflow_tracking.MLFLOW_ENABLED', False)
    def test_disabled_yields_none(self):
        """MLflow 禁用时应 yield None"""
        with track_compilation("test_run", {"param": "value"}) as run:
            assert run is None


class TestLogCompilationMetrics:
    """测试编译指标记录功能"""
    
    @patch('dspyui.core.mlflow_tracking.MLFLOW_ENABLED', False)
    def test_disabled_does_nothing(self):
        """MLflow 禁用时应不执行任何操作"""
        # 不应抛出异常
        log_compilation_metrics(0.5, 0.8, 100, 20)


class TestLogCompilationArtifacts:
    """测试编译工件记录功能"""
    
    @patch('dspyui.core.mlflow_tracking.MLFLOW_ENABLED', False)
    def test_disabled_does_nothing(self):
        """MLflow 禁用时应不执行任何操作"""
        # 不应抛出异常
        log_compilation_artifacts("program.json", "prompt.json", "data.csv")


class TestLogEvaluationTable:
    """测试评估结果记录功能"""
    
    @patch('dspyui.core.mlflow_tracking.MLFLOW_ENABLED', False)
    def test_disabled_does_nothing(self):
        """MLflow 禁用时应不执行任何操作"""
        results = [{"example_id": 0, "score": 0.9}]
        # 不应抛出异常
        log_evaluation_table(results)
    
    @patch('dspyui.core.mlflow_tracking.MLFLOW_ENABLED', True)
    def test_empty_results_skipped(self):
        """空结果应被跳过"""
        # 不应抛出异常
        log_evaluation_table([])


class TestLogDatasetMetadata:
    """测试数据集元数据记录功能"""
    
    @patch('dspyui.core.mlflow_tracking.MLFLOW_ENABLED', False)
    def test_disabled_does_nothing(self):
        """MLflow 禁用时应不执行任何操作"""
        df = pd.DataFrame({"a": [1, 2, 3]})
        # 不应抛出异常
        log_dataset_metadata(df)


class TestGetMlflowUiUrlEnhanced:
    """测试增强后的 MLflow UI URL 构造功能"""
    
    @patch('dspyui.core.mlflow_tracking.MLFLOW_TRACKING_URI', './mlruns')
    def test_model_name_url(self):
        """模型名称应返回模型注册页面 URL"""
        url = get_mlflow_ui_url(model_name="joke-generator")
        assert url == "http://localhost:5000/#/models/joke-generator"
    
    @patch('dspyui.core.mlflow_tracking.MLFLOW_TRACKING_URI', './mlruns')
    def test_model_name_with_version_url(self):
        """模型名称和版本应返回特定版本页面 URL"""
        url = get_mlflow_ui_url(model_name="joke-generator", model_version="1")
        assert url == "http://localhost:5000/#/models/joke-generator/versions/1"
    
    @patch('dspyui.core.mlflow_tracking.MLFLOW_TRACKING_URI', './mlruns')
    def test_experiment_id_url(self):
        """实验 ID 应返回实验页面 URL"""
        url = get_mlflow_ui_url(experiment_id="123")
        assert url == "http://localhost:5000/#/experiments/123"
    
    @patch('dspyui.core.mlflow_tracking.MLFLOW_TRACKING_URI', 'https://mlflow.example.com')
    def test_https_remote_server(self):
        """HTTPS 远程服务器应正确处理"""
        url = get_mlflow_ui_url()
        assert url == "https://mlflow.example.com/#/experiments"
    
    @patch('dspyui.core.mlflow_tracking.MLFLOW_TRACKING_URI', 'file:///path/to/mlruns')
    def test_file_uri_uses_localhost(self):
        """file:// URI 应使用本地服务器地址"""
        url = get_mlflow_ui_url()
        assert url == "http://localhost:5000/#/experiments"


class TestRegisterModel:
    """测试模型注册功能"""
    
    @patch('dspyui.core.mlflow_tracking.MLFLOW_ENABLED', False)
    def test_disabled_returns_none(self):
        """MLflow 禁用时应返回 None"""
        result = register_model("run123", "test-model")
        assert result is None
    
    @patch('dspyui.core.mlflow_tracking.MLFLOW_ENABLED', True)
    def test_register_with_metadata(self):
        """带元数据的模型注册应正确处理"""
        mock_result = MagicMock()
        mock_result.version = "1"
        
        # 设置为已安装状态以通过检查
        with patch('dspyui.core.mlflow_tracking.MLFLOW_INSTALLED', True):
            with patch('dspyui.core.mlflow_tracking.MlflowClient') as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                with patch('dspyui.core.mlflow_tracking.mlflow') as mock_mlflow_internal:
                    mock_mlflow_internal.register_model.return_value = mock_result
                    
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
                    mock_mlflow_internal.register_model.assert_called_once_with("runs:/run123/program", "test-model")
                    # 验证元数据更新被调用
                    mock_client.update_model_version.assert_called_once()


class TestTransitionModelStage:
    """测试模型阶段转换功能"""
    
    @patch('dspyui.core.mlflow_tracking.MLFLOW_ENABLED', False)
    def test_disabled_returns_false(self):
        """MLflow 禁用时应返回 False"""
        result = transition_model_stage("test-model", "1", "Staging")
        assert result is False
    
    @patch('dspyui.core.mlflow_tracking.MLFLOW_ENABLED', True)
    def test_invalid_stage_returns_false(self):
        """无效阶段应返回 False"""
        result = transition_model_stage("test-model", "1", "InvalidStage")
        assert result is False
    
    @patch('dspyui.core.mlflow_tracking.MLFLOW_ENABLED', True)
    def test_valid_stages(self):
        """有效阶段应被接受"""
        valid_stages = ["Staging", "Production", "Archived", "None"]
        
        for stage in valid_stages:
            with patch('dspyui.core.mlflow_tracking.MlflowClient') as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                # 模拟 get_model_version 返回正确的阶段
                mock_version = MagicMock()
                mock_version.current_stage = stage
                mock_client.get_model_version.return_value = mock_version
                
                # 设置为已安装状态以通过检查
                with patch('dspyui.core.mlflow_tracking.MLFLOW_INSTALLED', True):
                    result = transition_model_stage("test-model", "1", stage)
                
                assert result is True
                mock_client.transition_model_version_stage.assert_called_once()
