"""
ModelManager 模块单元测试

INPUT:  autodspy.serving.model_manager 模块
OUTPUT: 验证模型管理器功能的测试用例
POS:    确保模型缓存和加载功能正确性
"""

import pytest
from unittest.mock import patch, MagicMock

from autodspy.serving import ModelManager
from autodspy import AutoDSPyConfig, set_config, reset_config


@pytest.fixture(autouse=True)
def reset_config_fixture():
    """每个测试前后重置配置"""
    reset_config()
    yield
    reset_config()


@pytest.mark.unit
class TestModelManagerInit:
    """测试 ModelManager 初始化"""
    
    def test_default_init(self):
        """默认初始化应使用默认配置"""
        manager = ModelManager()
        
        assert manager._cache_enabled is True
        assert manager._cache_ttl > 0
    
    def test_custom_init(self):
        """自定义初始化应使用提供的配置"""
        manager = ModelManager(cache_enabled=False, cache_ttl=600)
        
        assert manager._cache_enabled is False
        assert manager._cache_ttl == 600
    
    def test_disabled_cache(self):
        """禁用缓存时应正确设置"""
        manager = ModelManager(cache_enabled=False)
        
        assert manager._cache_enabled is False


@pytest.mark.unit
class TestModelManagerLoadModel:
    """测试模型加载功能"""
    
    def test_load_by_version(self):
        """通过版本号加载模型应成功"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        manager = ModelManager()
        
        with patch.object(manager, '_load_from_mlflow') as mock_load:
            mock_program = MagicMock()
            mock_load.return_value = (mock_program, "1")
            
            result, version = manager.load_model("test-model", version="1")
            
            assert result is not None
            assert version == "1"
            mock_load.assert_called_once_with("models:/test-model/1")
    
    def test_load_by_stage(self):
        """通过阶段加载模型应成功"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        manager = ModelManager()
        
        with patch.object(manager, '_load_from_mlflow') as mock_load:
            mock_program = MagicMock()
            mock_load.return_value = (mock_program, "Production")
            
            result, version = manager.load_model("test-model", stage="Production")
            
            assert result is not None
            mock_load.assert_called_once_with("models:/test-model@Production")
    
    def test_cache_hit(self):
        """缓存命中时应返回缓存的模型"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        manager = ModelManager(cache_enabled=True)
        
        with patch.object(manager, '_load_from_mlflow') as mock_load:
            mock_program = MagicMock()
            mock_load.return_value = (mock_program, "1")
            
            # 第一次加载
            result1, _ = manager.load_model("test-model", version="1")
            assert result1 is not None
            
            # 第二次加载应使用缓存
            result2, _ = manager.load_model("test-model", version="1")
            assert result2 is not None
            
            # 验证只调用了一次加载
            assert mock_load.call_count == 1
    
    def test_cache_disabled(self):
        """禁用缓存时每次都应重新加载"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        manager = ModelManager(cache_enabled=False)
        
        with patch.object(manager, '_load_from_mlflow') as mock_load:
            mock_program = MagicMock()
            mock_load.return_value = (mock_program, "1")
            
            # 第一次加载
            result1, _ = manager.load_model("test-model", version="1")
            assert result1 is not None
            
            # 第二次加载应重新加载
            result2, _ = manager.load_model("test-model", version="1")
            assert result2 is not None
            
            # 验证调用了两次加载
            assert mock_load.call_count == 2
    
    def test_different_versions_separate_cache(self):
        """不同版本应使用独立缓存"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        manager = ModelManager(cache_enabled=True)
        
        with patch.object(manager, '_load_from_mlflow') as mock_load:
            mock_program_v1 = MagicMock()
            mock_program_v2 = MagicMock()
            
            def load_side_effect(uri):
                if "/1" in uri:
                    return (mock_program_v1, "1")
                elif "/2" in uri:
                    return (mock_program_v2, "2")
                return (None, "unknown")
            
            mock_load.side_effect = load_side_effect
            
            # 加载版本 1
            result1, _ = manager.load_model("test-model", version="1")
            assert result1 is mock_program_v1
            
            # 加载版本 2
            result2, _ = manager.load_model("test-model", version="2")
            assert result2 is mock_program_v2
            
            # 验证调用了两次加载
            assert mock_load.call_count == 2


@pytest.mark.unit
class TestModelManagerInvalidateCache:
    """测试缓存失效功能"""
    
    def test_invalidate_specific_model(self):
        """失效特定模型缓存应成功"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        manager = ModelManager(cache_enabled=True)
        
        with patch.object(manager, '_load_from_mlflow') as mock_load:
            mock_program = MagicMock()
            mock_load.return_value = (mock_program, "1")
            
            # 加载模型
            manager.load_model("test-model", version="1")
            assert mock_load.call_count == 1
            
            # 失效缓存
            manager.invalidate_cache("test-model")
            
            # 再次加载应重新加载
            manager.load_model("test-model", version="1")
            assert mock_load.call_count == 2
    
    def test_invalidate_all_cache(self):
        """失效所有缓存应成功"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        manager = ModelManager(cache_enabled=True)
        
        with patch.object(manager, '_load_from_mlflow') as mock_load:
            mock_program = MagicMock()
            mock_load.return_value = (mock_program, "1")
            
            # 加载多个模型
            manager.load_model("model-1", version="1")
            manager.load_model("model-2", version="1")
            assert mock_load.call_count == 2
            
            # 失效所有缓存
            manager.invalidate_all()
            
            # 再次加载应重新加载
            manager.load_model("model-1", version="1")
            manager.load_model("model-2", version="1")
            assert mock_load.call_count == 4


@pytest.mark.unit
class TestModelManagerGetCacheStats:
    """测试缓存统计功能"""
    
    def test_cache_stats(self):
        """缓存统计应正确记录"""
        config = AutoDSPyConfig(mlflow_enabled=True)
        set_config(config)
        
        manager = ModelManager(cache_enabled=True)
        
        with patch.object(manager, '_load_from_mlflow') as mock_load:
            mock_program = MagicMock()
            mock_load.return_value = (mock_program, "1")
            
            # 加载模型
            manager.load_model("test-model", version="1")
            manager.load_model("test-model", version="1")  # 缓存命中
            manager.load_model("test-model", version="2")  # 新版本
            
            stats = manager.get_cache_stats()
            
            assert "cached_models" in stats
            assert "cache_enabled" in stats
            assert stats["cache_enabled"] is True
            assert stats["total_loads"] == 3
            assert stats["cache_hits"] == 1
            assert stats["cache_misses"] == 2
