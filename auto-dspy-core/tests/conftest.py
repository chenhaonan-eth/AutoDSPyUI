"""
Pytest 配置和共享 fixtures

INPUT:  pytest
OUTPUT: 测试配置和共享 fixtures
POS:    测试基础设施
"""

import os
import pytest
from unittest.mock import MagicMock

# 配置 pytest 标记
def pytest_configure(config):
    """配置 pytest 标记"""
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "e2e: 端到端测试")
    config.addinivalue_line("markers", "requires_mlflow: 需要 MLflow 服务")
    config.addinivalue_line("markers", "requires_llm: 需要 LLM API")
    config.addinivalue_line("markers", "slow: 慢速测试")


@pytest.fixture
def mock_config():
    """模拟配置对象"""
    from autodspy import AutoDSPyConfig
    
    return AutoDSPyConfig(
        mlflow_enabled=False,
        cache_enabled=True,
        num_threads=1
    )


@pytest.fixture
def mock_mlflow():
    """模拟 MLflow 模块"""
    with pytest.mock.patch('autodspy.mlflow.tracking.mlflow') as mock:
        # 模拟基本的 MLflow 功能
        mock.set_tracking_uri = MagicMock()
        mock.set_experiment = MagicMock()
        mock.start_run = MagicMock()
        mock.log_param = MagicMock()
        mock.log_metric = MagicMock()
        mock.log_artifact = MagicMock()
        mock.end_run = MagicMock()
        
        yield mock


@pytest.fixture
def temp_dir(tmp_path):
    """创建临时目录"""
    return tmp_path


@pytest.fixture
def sample_dataframe():
    """创建示例 DataFrame"""
    import pandas as pd
    
    return pd.DataFrame({
        "question": ["What is Python?", "What is DSPy?"],
        "answer": ["A programming language", "A framework for LLMs"]
    })


@pytest.fixture(autouse=True)
def reset_config():
    """每个测试后重置配置"""
    yield
    # 测试后重置为默认配置
    from autodspy import reset_config
    reset_config()


@pytest.fixture
def mock_dspy():
    """模拟 DSPy 模块"""
    with pytest.mock.patch('dspy') as mock:
        # 模拟 LM 配置
        mock.LM = MagicMock()
        mock.configure = MagicMock()
        
        # 模拟 Signature
        mock.Signature = type('Signature', (), {})
        mock.InputField = MagicMock()
        mock.OutputField = MagicMock()
        
        # 模拟 Module
        mock.Module = type('Module', (), {})
        mock.Predict = MagicMock()
        mock.ChainOfThought = MagicMock()
        
        yield mock
