"""
FeedbackService 模块单元测试

INPUT:  autodspy.serving.feedback 模块
OUTPUT: 验证反馈服务功能的测试用例
POS:    确保反馈收集和记录功能正确性
"""

import pytest
from unittest.mock import patch, MagicMock

from autodspy.serving import FeedbackService, FeedbackRecord
from autodspy import AutoDSPyConfig, set_config, reset_config


@pytest.fixture(autouse=True)
def reset_config_fixture():
    """每个测试前后重置配置"""
    reset_config()
    yield
    reset_config()


@pytest.mark.unit
class TestFeedbackServiceInit:
    """测试 FeedbackService 初始化"""
    
    def test_default_init(self):
        """默认初始化应使用默认配置"""
        service = FeedbackService()
        
        assert service._feedback_enabled is True
    
    def test_custom_init(self):
        """自定义初始化应使用提供的配置"""
        service = FeedbackService(feedback_enabled=False)
        
        assert service._feedback_enabled is False


@pytest.mark.unit
class TestFeedbackServiceSubmit:
    """测试反馈提交功能"""
    
    def test_submit_disabled(self):
        """禁用反馈时应返回本地 feedback_id"""
        config = AutoDSPyConfig(mlflow_enabled=False)
        set_config(config)
        
        service = FeedbackService(feedback_enabled=False)
        
        result = service.record_feedback(
            trace_id="test-trace",
            rating="thumbs_up"
        )
        
        # 即使禁用也会返回本地生成的 feedback_id
        assert result is not None
        assert result.startswith("fb-")
    
    def test_submit_success(self):
        """成功提交反馈应返回 feedback_id"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        service = FeedbackService(feedback_enabled=True)
        
        with patch('autodspy.serving.feedback.mlflow') as mock_mlflow, \
             patch('autodspy.serving.feedback.MLFLOW_INSTALLED', True), \
             patch('autodspy.serving.feedback.AssessmentSource') as mock_source, \
             patch('autodspy.serving.feedback.AssessmentSourceType') as mock_source_type:
            
            mock_source_type.HUMAN = "HUMAN"
            
            result = service.record_feedback(
                trace_id="test-trace",
                rating="thumbs_up",
                comment="Great result!"
            )
            
            assert result is not None
            assert result.startswith("fb-")
    
    def test_submit_with_corrected_output(self):
        """提交带修正输出的反馈应成功"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        service = FeedbackService(feedback_enabled=True)
        
        with patch('autodspy.serving.feedback.mlflow') as mock_mlflow, \
             patch('autodspy.serving.feedback.MLFLOW_INSTALLED', True), \
             patch('autodspy.serving.feedback.AssessmentSource') as mock_source, \
             patch('autodspy.serving.feedback.AssessmentSourceType') as mock_source_type:
            
            mock_source_type.HUMAN = "HUMAN"
            corrected_output = {"joke": "Better joke here"}
            
            result = service.record_feedback(
                trace_id="test-trace",
                rating="thumbs_down",
                corrected_output=corrected_output,
                comment="Output needs improvement"
            )
            
            assert result is not None
    
    def test_submit_with_user_id(self):
        """提交带用户 ID 的反馈应成功"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        service = FeedbackService(feedback_enabled=True)
        
        with patch('autodspy.serving.feedback.mlflow') as mock_mlflow, \
             patch('autodspy.serving.feedback.MLFLOW_INSTALLED', True), \
             patch('autodspy.serving.feedback.AssessmentSource') as mock_source, \
             patch('autodspy.serving.feedback.AssessmentSourceType') as mock_source_type:
            
            mock_source_type.HUMAN = "HUMAN"
            
            result = service.record_feedback(
                trace_id="test-trace",
                rating="thumbs_up",
                user_id="user-456"
            )
            
            assert result is not None
    
    def test_submit_invalid_rating(self):
        """无效评分应抛出异常"""
        service = FeedbackService(feedback_enabled=True)
        
        with pytest.raises(ValueError, match="无效的 rating"):
            service.record_feedback(
                trace_id="test-trace",
                rating="invalid_rating"
            )


@pytest.mark.unit
class TestFeedbackServiceGetFeedback:
    """测试获取反馈功能"""
    
    def test_get_feedback_history_empty(self):
        """初始状态应返回空列表"""
        service = FeedbackService(feedback_enabled=True)
        
        result = service.get_feedback_history()
        
        assert result == []
    
    def test_get_feedback_by_trace_id(self):
        """通过 trace_id 获取反馈应成功"""
        service = FeedbackService(feedback_enabled=True)
        
        # 先记录一些反馈
        service.record_feedback(trace_id="trace-1", rating="thumbs_up")
        service.record_feedback(trace_id="trace-2", rating="thumbs_down")
        service.record_feedback(trace_id="trace-1", rating="thumbs_down")
        
        # 按 trace_id 过滤
        result = service.get_feedback_history(trace_id="trace-1")
        
        assert len(result) == 2
        assert all(r.trace_id == "trace-1" for r in result)
    
    def test_get_feedback_stats(self):
        """获取反馈统计应正确"""
        service = FeedbackService(feedback_enabled=True)
        
        # 记录一些反馈
        service.record_feedback(trace_id="trace-1", rating="thumbs_up")
        service.record_feedback(trace_id="trace-2", rating="thumbs_up")
        service.record_feedback(trace_id="trace-3", rating="thumbs_down", comment="Bad")
        
        stats = service.get_feedback_stats()
        
        assert stats["total_feedbacks"] == 3
        assert stats["thumbs_up_count"] == 2
        assert stats["thumbs_down_count"] == 1
        assert stats["with_comments"] == 1


@pytest.mark.unit
class TestFeedbackRecord:
    """测试 FeedbackRecord 数据类"""
    
    def test_feedback_record_creation(self):
        """创建反馈记录应成功"""
        record = FeedbackRecord(
            trace_id="test-trace",
            rating="thumbs_up",
            comment="Great!",
            corrected_output={"joke": "Better joke"},
            user_id="user-123"
        )
        
        assert record.trace_id == "test-trace"
        assert record.rating == "thumbs_up"
        assert record.comment == "Great!"
        assert record.corrected_output == {"joke": "Better joke"}
        assert record.user_id == "user-123"
        assert record.feedback_id.startswith("fb-")
        assert record.timestamp != ""
    
    def test_feedback_record_minimal(self):
        """最小反馈记录应成功"""
        record = FeedbackRecord(
            trace_id="test-trace",
            rating="thumbs_up"
        )
        
        assert record.trace_id == "test-trace"
        assert record.rating == "thumbs_up"
        assert record.comment is None
        assert record.corrected_output is None
        assert record.user_id is None
