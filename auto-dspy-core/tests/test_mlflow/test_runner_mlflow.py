"""
测试 runner.py 中的 MLflow 相关函数

INPUT:  Docker MLflow 服务, autodspy 配置, DSPy LM
OUTPUT: 验证 generate_response_from_mlflow 和 run_batch_inference_from_mlflow 函数
POS:    单元测试 + 集成测试，验证从 MLflow 加载模型并推理的功能

运行方式:
    # 1. 启动 MLflow Docker 服务
    cd docker/docker-compose && bash start.sh && cd ../..
    
    # 2. 运行测试
    cd auto-dspy-core
    uv run pytest tests/test_mlflow/test_runner_mlflow.py -v -s

⚠️ 一旦我被更新，务必更新我的开头注释
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
import pandas as pd

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def mlflow_config():
    """获取 MLflow 配置"""
    from dotenv import load_dotenv
    load_dotenv()
    
    return {
        "enabled": os.getenv("MLFLOW_ENABLED", "true").lower() == "true",
        "tracking_uri": os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001"),
        "experiment_name": os.getenv("MLFLOW_EXPERIMENT_NAME", "autodspy-tests"),
    }


@pytest.fixture
def autodspy_config(mlflow_config):
    """初始化 autodspy 配置"""
    from autodspy import AutoDSPyConfig, set_config
    
    config = AutoDSPyConfig(
        mlflow_enabled=True,
        mlflow_tracking_uri=mlflow_config["tracking_uri"],
        mlflow_experiment_name=mlflow_config["experiment_name"],
    )
    set_config(config)
    return config


@pytest.fixture
def sample_input():
    """示例输入数据"""
    return {"topic": "程序员"}


@pytest.fixture
def sample_batch_data():
    """批量推理示例数据"""
    return pd.DataFrame({
        "topic": ["程序员", "猫咪", "咖啡"]
    })


# ============================================================
# 辅助函数
# ============================================================

def is_mlflow_server_available(uri: str, timeout: float = 2.0) -> bool:
    """检查 MLflow 服务器是否可用"""
    try:
        import requests
        response = requests.get(f"{uri}/health", timeout=timeout)
        return response.status_code == 200
    except Exception:
        return False


def get_first_available_model(uri: str):
    """获取第一个可用的已注册模型"""
    try:
        import mlflow
        from mlflow import MlflowClient
        
        mlflow.set_tracking_uri(uri)
        client = MlflowClient()
        models = client.search_registered_models()
        
        if not models:
            return None, None
        
        model = models[0]
        if model.latest_versions:
            return model.name, model.latest_versions[0].version
        return model.name, "1"
    except Exception:
        return None, None


def has_llm_api_key() -> bool:
    """检查是否配置了 LLM API Key"""
    keys = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "DEEPSEEK_API_KEY",
        "GROQ_API_KEY",
        "GOOGLE_API_KEY",
    ]
    return any(os.getenv(k) for k in keys)


def get_available_llm_model() -> str:
    """获取可用的 LLM 模型"""
    if os.getenv("DEEPSEEK_API_KEY"):
        return "deepseek-chat"
    if os.getenv("OPENAI_API_KEY"):
        return "gpt-4o-mini"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "claude-3-haiku-20240307"
    if os.getenv("GROQ_API_KEY"):
        return "llama-3.1-8b-instant"
    if os.getenv("GOOGLE_API_KEY"):
        return "gemini-1.5-flash"
    return "gpt-4o-mini"


# ============================================================
# 单元测试 (Mock)
# ============================================================

class TestGenerateResponseFromMlflowUnit:
    """generate_response_from_mlflow 单元测试（使用 Mock）"""
    
    def test_missing_metadata_fields(self, autodspy_config):
        """测试元数据缺少必需字段时抛出异常"""
        from autodspy.dspy_core.runner import generate_response_from_mlflow
        
        with patch('autodspy.mlflow.loader.get_model_metadata') as mock_metadata:
            mock_metadata.return_value = {
                "input_fields": [],  # 空字段
                "output_fields": [],
            }
            
            with pytest.raises(ValueError, match="元数据不完整"):
                generate_response_from_mlflow(
                    model_name="test-model",
                    version="1",
                    row_data={"topic": "test"},
                    llm_model="gpt-4o-mini"
                )
    
    def test_successful_inference_mock(self, autodspy_config):
        """测试成功推理（Mock 所有依赖）"""
        from autodspy.dspy_core.runner import generate_response_from_mlflow
        
        # Mock 所有依赖
        mock_program = MagicMock()
        mock_result = MagicMock()
        mock_result.joke = "为什么程序员喜欢黑暗？因为 Light 吸引 bugs！"
        mock_program.return_value = mock_result
        
        with patch('autodspy.mlflow.loader.get_model_metadata') as mock_metadata, \
             patch('autodspy.mlflow.loader.load_model_from_registry') as mock_load, \
             patch('autodspy.dspy_core.compiler._create_lm') as mock_lm, \
             patch('dspy.context'):
            
            mock_metadata.return_value = {
                "input_fields": ["topic"],
                "output_fields": ["joke"],
            }
            mock_load.return_value = mock_program
            mock_lm.return_value = MagicMock()
            
            result = generate_response_from_mlflow(
                model_name="joke-generator",
                version="1",
                row_data={"topic": "程序员"},
                llm_model="gpt-4o-mini"
            )
            
            assert "Input:" in result
            assert "topic: 程序员" in result
            assert "Output:" in result
            assert "joke:" in result
    
    def test_missing_input_field_warning(self, autodspy_config):
        """测试输入字段缺失时的警告处理"""
        from autodspy.dspy_core.runner import generate_response_from_mlflow
        
        mock_program = MagicMock()
        mock_result = MagicMock()
        mock_result.joke = "测试笑话"
        mock_program.return_value = mock_result
        
        with patch('autodspy.mlflow.loader.get_model_metadata') as mock_metadata, \
             patch('autodspy.mlflow.loader.load_model_from_registry') as mock_load, \
             patch('autodspy.dspy_core.compiler._create_lm') as mock_lm, \
             patch('dspy.context'):
            
            mock_metadata.return_value = {
                "input_fields": ["topic", "style"],  # 需要两个字段
                "output_fields": ["joke"],
            }
            mock_load.return_value = mock_program
            mock_lm.return_value = MagicMock()
            
            # 只提供一个字段
            result = generate_response_from_mlflow(
                model_name="joke-generator",
                version="1",
                row_data={"topic": "程序员"},  # 缺少 style
                llm_model="gpt-4o-mini"
            )
            
            # 应该成功执行，缺失字段使用空字符串
            assert "Input:" in result
            assert "style:" in result  # 缺失字段应该存在


# ============================================================
# 集成测试 (需要真实 MLflow 服务)
# ============================================================

@pytest.mark.integration
class TestGenerateResponseFromMlflowIntegration:
    """generate_response_from_mlflow 集成测试（需要真实 MLflow 服务和 LLM API）"""
    
    def test_real_model_inference(self, mlflow_config, autodspy_config):
        """测试从真实 MLflow 加载模型并推理"""
        if not is_mlflow_server_available(mlflow_config["tracking_uri"]):
            pytest.skip("MLflow 服务器不可用")
        
        if not has_llm_api_key():
            pytest.skip("没有配置 LLM API Key")
        
        model_name, version = get_first_available_model(mlflow_config["tracking_uri"])
        if not model_name:
            pytest.skip("没有已注册的模型")
        
        from autodspy.dspy_core.runner import generate_response_from_mlflow
        from autodspy.mlflow.loader import get_model_metadata
        
        # 获取模型元数据以确定输入字段
        metadata = get_model_metadata(model_name, version)
        input_fields = metadata.get("input_fields", [])
        
        if not input_fields:
            pytest.skip(f"模型 {model_name} 没有定义输入字段")
        
        # 构造输入数据
        row_data = {field: "测试输入" for field in input_fields}
        
        llm_model = get_available_llm_model()
        print(f"\n使用模型: {model_name} v{version}")
        print(f"LLM: {llm_model}")
        print(f"输入: {row_data}")
        
        try:
            result = generate_response_from_mlflow(
                model_name=model_name,
                version=version,
                row_data=row_data,
                llm_model=llm_model
            )
            
            print(f"结果:\n{result}")
            
            assert "Input:" in result
            assert "Output:" in result
            
        except Exception as e:
            pytest.fail(f"推理失败: {e}")


@pytest.mark.integration
class TestRunBatchInferenceFromMlflowIntegration:
    """run_batch_inference_from_mlflow 集成测试"""
    
    def test_batch_inference(self, mlflow_config, autodspy_config):
        """测试批量推理"""
        if not is_mlflow_server_available(mlflow_config["tracking_uri"]):
            pytest.skip("MLflow 服务器不可用")
        
        if not has_llm_api_key():
            pytest.skip("没有配置 LLM API Key")
        
        model_name, version = get_first_available_model(mlflow_config["tracking_uri"])
        if not model_name:
            pytest.skip("没有已注册的模型")
        
        from autodspy.dspy_core.runner import run_batch_inference_from_mlflow
        from autodspy.mlflow.loader import get_model_metadata
        
        # 获取模型元数据
        metadata = get_model_metadata(model_name, version)
        input_fields = metadata.get("input_fields", [])
        
        if not input_fields:
            pytest.skip(f"模型 {model_name} 没有定义输入字段")
        
        # 构造批量数据
        batch_data = pd.DataFrame({
            field: ["测试1", "测试2"] for field in input_fields
        })
        
        llm_model = get_available_llm_model()
        print(f"\n使用模型: {model_name} v{version}")
        print(f"LLM: {llm_model}")
        print(f"批量数据:\n{batch_data}")
        
        try:
            result_df = run_batch_inference_from_mlflow(
                model_name=model_name,
                version=version,
                data=batch_data,
                llm_model=llm_model
            )
            
            print(f"结果:\n{result_df}")
            
            assert len(result_df) == 2
            assert "_status" in result_df.columns
            
        except Exception as e:
            pytest.fail(f"批量推理失败: {e}")
    
    def test_batch_inference_with_progress(self, mlflow_config, autodspy_config):
        """测试批量推理的进度回调"""
        if not is_mlflow_server_available(mlflow_config["tracking_uri"]):
            pytest.skip("MLflow 服务器不可用")
        
        if not has_llm_api_key():
            pytest.skip("没有配置 LLM API Key")
        
        model_name, version = get_first_available_model(mlflow_config["tracking_uri"])
        if not model_name:
            pytest.skip("没有已注册的模型")
        
        from autodspy.dspy_core.runner import run_batch_inference_from_mlflow
        from autodspy.mlflow.loader import get_model_metadata
        
        metadata = get_model_metadata(model_name, version)
        input_fields = metadata.get("input_fields", [])
        
        if not input_fields:
            pytest.skip(f"模型 {model_name} 没有定义输入字段")
        
        batch_data = pd.DataFrame({
            field: ["数据1", "数据2", "数据3"] for field in input_fields
        })
        
        # 记录进度回调
        progress_records = []
        def progress_callback(current, total):
            progress_records.append((current, total))
            print(f"  进度: {current}/{total}")
        
        llm_model = get_available_llm_model()
        print(f"\n测试进度回调")
        
        result_df = run_batch_inference_from_mlflow(
            model_name=model_name,
            version=version,
            data=batch_data,
            llm_model=llm_model,
            progress_callback=progress_callback
        )
        
        # 验证进度回调被正确调用
        assert len(progress_records) == 3
        assert progress_records[-1] == (3, 3)
        print(f"✅ 进度回调验证通过: {progress_records}")


@pytest.mark.integration
class TestMlflowModelMetadataIntegration:
    """MLflow 模型元数据集成测试"""
    
    def test_get_model_metadata(self, mlflow_config, autodspy_config):
        """测试获取模型元数据"""
        if not is_mlflow_server_available(mlflow_config["tracking_uri"]):
            pytest.skip("MLflow 服务器不可用")
        
        model_name, version = get_first_available_model(mlflow_config["tracking_uri"])
        if not model_name:
            pytest.skip("没有已注册的模型")
        
        from autodspy.mlflow.loader import get_model_metadata
        
        metadata = get_model_metadata(model_name, version)
        
        print(f"\n模型: {model_name} v{version}")
        print(f"元数据: {metadata}")
        
        # 验证基本字段存在
        assert "version" in metadata
        assert "input_fields" in metadata
        assert "output_fields" in metadata
        
    def test_list_registered_models(self, mlflow_config, autodspy_config):
        """测试列出已注册模型"""
        if not is_mlflow_server_available(mlflow_config["tracking_uri"]):
            pytest.skip("MLflow 服务器不可用")
        
        from autodspy.mlflow.loader import list_registered_models
        
        models = list_registered_models()
        
        print(f"\n已注册模型数量: {len(models)}")
        for m in models:
            print(f"  - {m['name']}: {len(m.get('latest_versions', []))} 个版本")
        
        # 至少应该能调用成功
        assert isinstance(models, list)
    
    def test_list_model_versions(self, mlflow_config, autodspy_config):
        """测试列出模型版本"""
        if not is_mlflow_server_available(mlflow_config["tracking_uri"]):
            pytest.skip("MLflow 服务器不可用")
        
        model_name, _ = get_first_available_model(mlflow_config["tracking_uri"])
        if not model_name:
            pytest.skip("没有已注册的模型")
        
        from autodspy.mlflow.loader import list_model_versions
        
        versions = list_model_versions(model_name)
        
        print(f"\n模型 {model_name} 的版本:")
        for v in versions:
            print(f"  - v{v['version']}: stage={v.get('stage')}, aliases={v.get('aliases', [])}")
        
        assert isinstance(versions, list)
        assert len(versions) > 0


@pytest.mark.integration
class TestMlflowModelLoadingIntegration:
    """MLflow 模型加载集成测试"""
    
    def test_load_model_by_version(self, mlflow_config, autodspy_config):
        """测试按版本号加载模型"""
        if not is_mlflow_server_available(mlflow_config["tracking_uri"]):
            pytest.skip("MLflow 服务器不可用")
        
        model_name, version = get_first_available_model(mlflow_config["tracking_uri"])
        if not model_name:
            pytest.skip("没有已注册的模型")
        
        from autodspy.mlflow.loader import load_model_from_registry
        
        print(f"\n加载模型: {model_name} v{version}")
        
        program = load_model_from_registry(model_name, version=version)
        
        assert program is not None
        print(f"✅ 模型加载成功: {type(program)}")
    
    def test_load_model_by_alias(self, mlflow_config, autodspy_config):
        """测试按别名加载模型"""
        if not is_mlflow_server_available(mlflow_config["tracking_uri"]):
            pytest.skip("MLflow 服务器不可用")
        
        from autodspy.mlflow.loader import list_registered_models, load_model_by_alias
        from mlflow import MlflowClient
        import mlflow
        
        mlflow.set_tracking_uri(mlflow_config["tracking_uri"])
        client = MlflowClient()
        
        # 查找有别名的模型
        models = list_registered_models()
        model_with_alias = None
        alias_name = None
        
        for m in models:
            try:
                versions = client.search_model_versions(f"name='{m['name']}'")
                for v in versions:
                    if hasattr(v, 'aliases') and v.aliases:
                        model_with_alias = m['name']
                        alias_name = list(v.aliases)[0]
                        break
            except Exception:
                continue
            if model_with_alias:
                break
        
        if not model_with_alias:
            pytest.skip("没有设置别名的模型")
        
        print(f"\n加载模型: {model_with_alias}@{alias_name}")
        
        program = load_model_by_alias(model_with_alias, alias_name)
        
        assert program is not None
        print(f"✅ 按别名加载成功: {type(program)}")


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """错误处理集成测试"""
    
    def test_invalid_model_name(self, mlflow_config, autodspy_config):
        """测试无效模型名称"""
        if not is_mlflow_server_available(mlflow_config["tracking_uri"]):
            pytest.skip("MLflow 服务器不可用")
        
        from autodspy.mlflow.loader import load_model_from_registry
        
        with pytest.raises(ValueError, match="加载模型.*失败"):
            load_model_from_registry("nonexistent-model-12345", version="1")
    
    def test_invalid_csv_headers(self, mlflow_config, autodspy_config):
        """测试 CSV 头部验证失败"""
        if not is_mlflow_server_available(mlflow_config["tracking_uri"]):
            pytest.skip("MLflow 服务器不可用")
        
        if not has_llm_api_key():
            pytest.skip("没有配置 LLM API Key")
        
        model_name, version = get_first_available_model(mlflow_config["tracking_uri"])
        if not model_name:
            pytest.skip("没有已注册的模型")
        
        from autodspy.dspy_core.runner import run_batch_inference_from_mlflow
        from autodspy.mlflow.loader import get_model_metadata
        
        metadata = get_model_metadata(model_name, version)
        input_fields = metadata.get("input_fields", [])
        
        if not input_fields:
            pytest.skip("模型没有定义输入字段")
        
        # 构造错误的 CSV 数据（缺少必需字段）
        wrong_data = pd.DataFrame({
            "wrong_field": ["test1", "test2"]
        })
        
        llm_model = get_available_llm_model()
        
        with pytest.raises(ValueError, match="CSV 缺少必需字段"):
            run_batch_inference_from_mlflow(
                model_name=model_name,
                version=version,
                data=wrong_data,
                llm_model=llm_model
            )


# ============================================================
# 运行入口
# ============================================================

if __name__ == "__main__":
    # 运行单元测试
    print("=" * 60)
    print("运行单元测试 (Mock)")
    print("=" * 60)
    pytest.main([__file__, "-v", "-s", "-k", "Unit", "--tb=short"])
    
    # 运行集成测试
    print("\n" + "=" * 60)
    print("运行集成测试 (需要 MLflow 服务)")
    print("=" * 60)
    pytest.main([__file__, "-v", "-s", "-m", "integration", "--tb=short"])
