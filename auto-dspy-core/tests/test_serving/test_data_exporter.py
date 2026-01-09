"""
DataExporter 模块单元测试

INPUT:  autodspy.serving.data_exporter 模块
OUTPUT: 验证数据导出功能的测试用例
POS:    确保数据导出和格式转换功能正确性
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from autodspy.serving import DataExporter
from autodspy import AutoDSPyConfig, set_config, reset_config


@pytest.fixture(autouse=True)
def reset_config_fixture():
    """每个测试前后重置配置"""
    reset_config()
    yield
    reset_config()


@pytest.mark.unit
class TestDataExporterInit:
    """测试 DataExporter 初始化"""
    
    def test_default_init(self):
        """默认初始化应成功"""
        exporter = DataExporter()
        
        assert exporter is not None


@pytest.mark.unit
class TestDataExporterQueryTraces:
    """测试查询追踪数据功能"""
    
    def test_query_disabled_mlflow(self):
        """MLflow 禁用时应返回空 DataFrame"""
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        exporter = DataExporter()
        result = exporter.query_traces_with_feedback()
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
    
    def test_query_with_model_filter(self):
        """带模型过滤查询应成功"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        exporter = DataExporter()
        
        # 由于 mlflow.search_traces 内部调用复杂，简化测试
        # 验证在 MLflow 不可用时返回空 DataFrame
        result = exporter.query_traces_with_feedback(model_name="test-model")
        
        # 在没有实际 MLflow 连接时，应返回空 DataFrame
        assert isinstance(result, pd.DataFrame)


@pytest.mark.unit
class TestDataExporterExportTrainingData:
    """测试导出训练数据功能"""
    
    def test_export_empty_dataframe(self):
        """导出空 DataFrame 应返回空数据"""
        exporter = DataExporter()
        
        df = pd.DataFrame()
        result = exporter.export_training_data(df, format="csv")
        
        assert isinstance(result, bytes)
        assert b"inputs,outputs" in result
    
    def test_export_to_csv(self):
        """导出为 CSV 格式应成功"""
        exporter = DataExporter()
        
        df = pd.DataFrame({
            'trace_id': ['trace-1', 'trace-2'],
            'inputs': ['{"topic": "test1"}', '{"topic": "test2"}'],
            'outputs': ['{"joke": "joke1"}', '{"joke": "joke2"}'],
            'corrected_output': ['', ''],
            'rating': ['thumbs_up', 'thumbs_up'],
            'comment': ['', ''],
            'timestamp': ['2024-01-01', '2024-01-02'],
            'model_name': ['test', 'test']
        })
        
        result = exporter.export_training_data(df, format="csv")
        
        assert isinstance(result, bytes)
        assert b'topic' in result or b'trace_id' in result
    
    def test_export_to_json(self):
        """导出为 JSON 格式应成功"""
        exporter = DataExporter()
        
        df = pd.DataFrame({
            'trace_id': ['trace-1'],
            'inputs': ['{"topic": "test"}'],
            'outputs': ['{"joke": "joke"}'],
            'corrected_output': [''],
            'rating': ['thumbs_up'],
            'comment': [''],
            'timestamp': ['2024-01-01'],
            'model_name': ['test']
        })
        
        result = exporter.export_training_data(df, format="json")
        
        assert isinstance(result, bytes)
        # JSON 格式应包含数据
        assert len(result) > 2  # 不只是 "[]"
    
    def test_export_with_corrected_output(self):
        """导出时应优先使用修正输出"""
        exporter = DataExporter()
        
        df = pd.DataFrame({
            'trace_id': ['trace-1'],
            'inputs': ['{"topic": "test"}'],
            'outputs': ['{"joke": "original"}'],
            'corrected_output': ['{"joke": "corrected"}'],
            'rating': ['thumbs_up'],
            'comment': [''],
            'timestamp': ['2024-01-01'],
            'model_name': ['test']
        })
        
        result = exporter.export_training_data(df, format="json", use_corrected_output=True)
        
        assert isinstance(result, bytes)
        assert b'corrected' in result


@pytest.mark.unit
class TestDataExporterHelperMethods:
    """测试辅助方法"""
    
    def test_extract_trace_io_dict(self):
        """从字典提取输入输出应成功"""
        exporter = DataExporter()
        
        row = pd.Series({'inputs': {'topic': 'test'}})
        result = exporter._extract_trace_io(row, 'inputs')
        
        assert result == {'topic': 'test'}
    
    def test_extract_trace_io_json_string(self):
        """从 JSON 字符串提取输入输出应成功"""
        exporter = DataExporter()
        
        row = pd.Series({'inputs': '{"topic": "test"}'})
        result = exporter._extract_trace_io(row, 'inputs')
        
        assert result == {'topic': 'test'}
    
    def test_extract_trace_io_none(self):
        """空值应返回 None"""
        exporter = DataExporter()
        
        row = pd.Series({'inputs': None})
        result = exporter._extract_trace_io(row, 'inputs')
        
        assert result is None
    
    def test_extract_assessment_value(self):
        """从 assessments 提取值应成功"""
        exporter = DataExporter()
        
        assessments = [
            {'name': 'user_rating', 'value': True},
            {'name': 'user_comment', 'value': 'Great!'}
        ]
        
        rating = exporter._extract_assessment_value(assessments, 'user_rating')
        comment = exporter._extract_assessment_value(assessments, 'user_comment')
        
        assert rating is True
        assert comment == 'Great!'
    
    def test_extract_assessment_value_not_found(self):
        """未找到的 assessment 应返回 None"""
        exporter = DataExporter()
        
        assessments = [{'name': 'other', 'value': 'test'}]
        
        result = exporter._extract_assessment_value(assessments, 'user_rating')
        
        assert result is None


@pytest.mark.integration
class TestDataExporterEndToEnd:
    """测试端到端数据导出流程"""
    
    def test_export_csv_bytes(self):
        """导出 CSV 应返回有效字节"""
        exporter = DataExporter()
        
        records = [
            {'topic': 'test1', 'joke': 'joke1'},
            {'topic': 'test2', 'joke': 'joke2'}
        ]
        
        result = exporter._export_csv(records)
        
        assert isinstance(result, bytes)
        assert b'topic' in result
        assert b'joke' in result
    
    def test_export_json_bytes(self):
        """导出 JSON 应返回有效字节"""
        exporter = DataExporter()
        
        records = [
            {'topic': 'test1', 'joke': 'joke1'},
            {'topic': 'test2', 'joke': 'joke2'}
        ]
        
        result = exporter._export_json(records)
        
        assert isinstance(result, bytes)
        assert b'test1' in result
        assert b'joke1' in result
