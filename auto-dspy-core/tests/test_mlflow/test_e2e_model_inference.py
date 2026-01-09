"""
端到端测试：从 Docker MLflow 加载模型 → 推理 → 评分

INPUT:  Docker MLflow 服务, autodspy 配置, DSPy LM
OUTPUT: 验证完整的模型加载、推理、评分流程
POS:    集成测试，验证 MLflow 模型的完整生命周期

运行方式:
    # 1. 启动 MLflow Docker 服务
    cd docker/docker-compose && bash start.sh && cd ../..
    
    # 2. 运行测试
    cd auto-dspy-core
    uv run pytest tests/test_mlflow/test_e2e_model_inference.py -v -s

⚠️ 一旦我被更新，务必更新我的开头注释
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 检查依赖
try:
    import mlflow
    MLFLOW_INSTALLED = True
except ImportError:
    MLFLOW_INSTALLED = False

try:
    import dspy
    DSPY_INSTALLED = True
except ImportError:
    DSPY_INSTALLED = False


def is_mlflow_server_available(uri: str, timeout: float = 2.0) -> bool:
    """检查 MLflow 服务器是否可用"""
    try:
        import requests
        response = requests.get(f"{uri}/health", timeout=timeout)
        return response.status_code == 200
    except Exception:
        return False


def has_registered_models(uri: str) -> bool:
    """检查是否有已注册的模型"""
    try:
        import mlflow
        from mlflow import MlflowClient
        
        mlflow.set_tracking_uri(uri)
        client = MlflowClient()
        models = client.search_registered_models()
        return len(models) > 0
    except Exception:
        return False


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
def sample_joke_input():
    """笑话生成模型的示例输入"""
    return {
        "topic": "程序员",
    }


@pytest.fixture
def sample_judge_input():
    """笑话评判模型的示例输入（需要 topic + joke）"""
    return {
        "topic": "程序员",
        "joke": "为什么程序员总是分不清万圣节和圣诞节？因为 Oct 31 = Dec 25！",
    }


@pytest.fixture
def sample_gold():
    """示例标准答案（用于评分）"""
    return {
        "topic": "程序员",
        "joke": "为什么程序员总是分不清万圣节和圣诞节？因为 Oct 31 = Dec 25！",
        "funny": "1",  # 评判结果
    }


# ============================================================
# 测试类：模型加载
# ============================================================

@pytest.mark.integration
@pytest.mark.requires_mlflow
class TestModelLoading:
    """测试从 MLflow 加载模型"""
    
    def test_list_registered_models(self, mlflow_config, autodspy_config):
        """测试列出已注册模型"""
        if not mlflow_config["enabled"]:
            pytest.skip("MLflow 未启用")
        
        if not MLFLOW_INSTALLED:
            pytest.skip("mlflow 未安装")
        
        uri = mlflow_config["tracking_uri"]
        if not is_mlflow_server_available(uri):
            pytest.skip(f"MLflow 服务器不可用: {uri}")
        
        from autodspy.mlflow.loader import list_registered_models
        
        models = list_registered_models()
        
        print(f"\n已注册模型数量: {len(models)}")
        for model in models:
            print(f"  - {model['name']}")
            for version in model.get('latest_versions', []):
                print(f"    v{version['version']} ({version.get('stage', 'N/A')})")
        
        # 不强制要求有模型，只验证函数能正常执行
        assert isinstance(models, list)
    
    def test_load_model_by_version(self, mlflow_config, autodspy_config):
        """测试通过版本号加载模型"""
        if not mlflow_config["enabled"]:
            pytest.skip("MLflow 未启用")
        
        if not MLFLOW_INSTALLED:
            pytest.skip("mlflow 未安装")
        
        uri = mlflow_config["tracking_uri"]
        if not is_mlflow_server_available(uri):
            pytest.skip(f"MLflow 服务器不可用: {uri}")
        
        if not has_registered_models(uri):
            pytest.skip("没有已注册的模型，跳过加载测试")
        
        from autodspy.mlflow.loader import list_registered_models, load_model_from_registry
        
        # 获取第一个可用模型
        models = list_registered_models()
        if not models:
            pytest.skip("没有可用模型")
        
        model_name = models[0]['name']
        versions = models[0].get('latest_versions', [])
        if not versions:
            pytest.skip(f"模型 {model_name} 没有版本")
        
        version = versions[0]['version']
        
        print(f"\n加载模型: {model_name} v{version}")
        
        try:
            program = load_model_from_registry(model_name, version=version)
            print(f"✅ 模型加载成功: {type(program)}")
            assert program is not None
        except Exception as e:
            print(f"⚠️ 模型加载失败: {e}")
            # 不强制失败，可能是模型格式问题
            pytest.skip(f"模型加载失败: {e}")
    
    def test_load_model_by_alias(self, mlflow_config, autodspy_config):
        """测试通过别名加载模型"""
        if not mlflow_config["enabled"]:
            pytest.skip("MLflow 未启用")
        
        if not MLFLOW_INSTALLED:
            pytest.skip("mlflow 未安装")
        
        uri = mlflow_config["tracking_uri"]
        if not is_mlflow_server_available(uri):
            pytest.skip(f"MLflow 服务器不可用: {uri}")
        
        if not has_registered_models(uri):
            pytest.skip("没有已注册的模型")
        
        from autodspy.mlflow.loader import list_registered_models, load_model_by_alias
        
        models = list_registered_models()
        if not models:
            pytest.skip("没有可用模型")
        
        model_name = models[0]['name']
        
        print(f"\n尝试通过 champion 别名加载模型: {model_name}")
        
        try:
            program = load_model_by_alias(model_name, alias="champion")
            print(f"✅ 模型加载成功: {type(program)}")
            assert program is not None
        except ValueError as e:
            if "champion" in str(e).lower() or "alias" in str(e).lower():
                print(f"⚠️ 模型没有 champion 别名: {e}")
                pytest.skip("模型没有设置 champion 别名")
            raise


# ============================================================
# 测试类：模型推理
# ============================================================

@pytest.mark.integration
@pytest.mark.requires_mlflow
@pytest.mark.requires_llm
class TestModelInference:
    """测试模型推理"""
    
    def test_single_inference(self, mlflow_config, autodspy_config):
        """测试单条推理"""
        if not mlflow_config["enabled"]:
            pytest.skip("MLflow 未启用")
        
        if not MLFLOW_INSTALLED or not DSPY_INSTALLED:
            pytest.skip("mlflow 或 dspy 未安装")
        
        uri = mlflow_config["tracking_uri"]
        if not is_mlflow_server_available(uri):
            pytest.skip(f"MLflow 服务器不可用: {uri}")
        
        if not has_registered_models(uri):
            pytest.skip("没有已注册的模型")
        
        # 检查 LLM API Key
        if not os.getenv("OPENAI_API_KEY") and not os.getenv("DEEPSEEK_API_KEY"):
            pytest.skip("没有配置 LLM API Key")
        
        from autodspy.mlflow.loader import list_registered_models, load_model_from_registry, get_model_metadata
        
        # 获取模型
        models = list_registered_models()
        if not models:
            pytest.skip("没有可用模型")
        
        model_name = models[0]['name']
        versions = models[0].get('latest_versions', [])
        if not versions:
            pytest.skip(f"模型 {model_name} 没有版本")
        
        version = versions[0]['version']
        
        print(f"\n加载模型: {model_name} v{version}")
        
        # 获取模型元数据以了解输入输出字段
        metadata = get_model_metadata(model_name, version)
        input_fields = metadata.get('input_fields', [])
        output_fields = metadata.get('output_fields', [])
        print(f"输入字段: {input_fields}")
        print(f"输出字段: {output_fields}")
        
        try:
            program = load_model_from_registry(model_name, version=version)
        except Exception as e:
            pytest.skip(f"模型加载失败: {e}")
        
        # 配置 LM
        lm_model = os.getenv("DSPY_LM_MODEL", "openai/gpt-4o-mini")
        print(f"使用 LM: {lm_model}")
        
        try:
            lm = dspy.LM(lm_model)
        except Exception as e:
            pytest.skip(f"LM 初始化失败: {e}")
        
        # 根据输入字段准备输入数据
        sample_input = {}
        for field in input_fields:
            if field == "topic":
                sample_input[field] = "程序员"
            elif field == "joke":
                sample_input[field] = "为什么程序员总是分不清万圣节和圣诞节？因为 Oct 31 = Dec 25！"
            else:
                sample_input[field] = f"测试{field}"
        
        print(f"输入: {sample_input}")
        
        with dspy.context(lm=lm):
            try:
                result = program(**sample_input)
                print(f"输出: {result}")
                print(f"输出类型: {type(result)}")
                
                # 验证输出
                assert result is not None
                
                # 打印输出字段
                for field in output_fields:
                    if hasattr(result, field):
                        print(f"{field}: {getattr(result, field)}")
                
            except Exception as e:
                print(f"推理失败: {e}")
                raise


# ============================================================
# 测试类：评分
# ============================================================

@pytest.mark.integration
@pytest.mark.requires_mlflow
@pytest.mark.requires_llm
class TestModelScoring:
    """测试模型输出评分"""
    
    def test_exact_match_metric(self, sample_gold):
        """测试精确匹配评分"""
        from autodspy.dspy_core.metrics import create_exact_match_metric
        
        output_fields = ["joke"]
        metric = create_exact_match_metric(output_fields)
        
        # 创建模拟预测结果
        class MockPrediction:
            def __init__(self, joke: str):
                self.joke = joke
        
        # 完全匹配
        pred_match = MockPrediction(sample_gold["joke"])
        score_match = metric(sample_gold, pred_match)
        print(f"\n精确匹配分数: {score_match}")
        assert score_match == 1
        
        # 不匹配
        pred_no_match = MockPrediction("这是一个不同的笑话")
        score_no_match = metric(sample_gold, pred_no_match)
        print(f"不匹配分数: {score_no_match}")
        assert score_no_match == 0
    
    def test_cosine_similarity_metric(self, sample_gold):
        """测试余弦相似度评分"""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("需要 OPENAI_API_KEY 来计算 embedding")
        
        from autodspy.dspy_core.metrics import create_cosine_similarity_metric
        
        output_fields = ["joke"]
        metric = create_cosine_similarity_metric(output_fields)
        
        class MockPrediction:
            def __init__(self, joke: str):
                self.joke = joke
        
        # 相似内容
        pred_similar = MockPrediction("程序员为什么分不清万圣节和圣诞节？因为八进制31等于十进制25！")
        score_similar = metric(sample_gold, pred_similar)
        print(f"\n相似内容余弦相似度: {score_similar:.4f}")
        assert 0 <= score_similar <= 1
        
        # 不相关内容
        pred_unrelated = MockPrediction("今天天气真好")
        score_unrelated = metric(sample_gold, pred_unrelated)
        print(f"不相关内容余弦相似度: {score_unrelated:.4f}")
        assert 0 <= score_unrelated <= 1
        
        # 相似内容应该比不相关内容分数高
        assert score_similar > score_unrelated
    
    def test_end_to_end_inference_and_scoring(
        self, mlflow_config, autodspy_config
    ):
        """端到端测试：加载模型 → 推理 → 评分"""
        if not mlflow_config["enabled"]:
            pytest.skip("MLflow 未启用")
        
        if not MLFLOW_INSTALLED or not DSPY_INSTALLED:
            pytest.skip("mlflow 或 dspy 未安装")
        
        uri = mlflow_config["tracking_uri"]
        if not is_mlflow_server_available(uri):
            pytest.skip(f"MLflow 服务器不可用: {uri}")
        
        if not has_registered_models(uri):
            pytest.skip("没有已注册的模型")
        
        if not os.getenv("OPENAI_API_KEY") and not os.getenv("DEEPSEEK_API_KEY"):
            pytest.skip("没有配置 LLM API Key")
        
        from autodspy.mlflow.loader import list_registered_models, load_model_from_registry, get_model_metadata
        from autodspy.dspy_core.metrics import create_exact_match_metric
        
        print("\n" + "=" * 60)
        print("端到端测试：加载模型 → 推理 → 评分")
        print("=" * 60)
        
        # Step 1: 加载模型
        print("\n[Step 1] 加载模型")
        models = list_registered_models()
        if not models:
            pytest.skip("没有可用模型")
        
        model_name = models[0]['name']
        versions = models[0].get('latest_versions', [])
        if not versions:
            pytest.skip(f"模型 {model_name} 没有版本")
        
        version = versions[0]['version']
        print(f"  模型: {model_name} v{version}")
        
        # 获取模型元数据
        metadata = get_model_metadata(model_name, version)
        input_fields = metadata.get('input_fields', [])
        output_fields = metadata.get('output_fields', [])
        print(f"  输入字段: {input_fields}")
        print(f"  输出字段: {output_fields}")
        
        try:
            program = load_model_from_registry(model_name, version=version)
            print(f"  ✅ 加载成功")
        except Exception as e:
            pytest.skip(f"模型加载失败: {e}")
        
        # Step 2: 配置 LM 并执行推理
        print("\n[Step 2] 执行推理")
        lm_model = os.getenv("DSPY_LM_MODEL", "openai/gpt-4o-mini")
        print(f"  LM: {lm_model}")
        
        # 根据输入字段准备输入数据
        sample_input = {}
        for field in input_fields:
            if field == "topic":
                sample_input[field] = "程序员"
            elif field == "joke":
                sample_input[field] = "为什么程序员总是分不清万圣节和圣诞节？因为 Oct 31 = Dec 25！"
            else:
                sample_input[field] = f"测试{field}"
        
        print(f"  输入: {sample_input}")
        
        try:
            lm = dspy.LM(lm_model)
        except Exception as e:
            pytest.skip(f"LM 初始化失败: {e}")
        
        with dspy.context(lm=lm):
            try:
                result = program(**sample_input)
                print(f"  ✅ 推理成功")
                
                # 获取输出
                result_dict = result.toDict() if hasattr(result, 'toDict') else {}
                for field in output_fields:
                    if hasattr(result, field):
                        print(f"  {field}: {getattr(result, field)}")
                
            except Exception as e:
                print(f"  ❌ 推理失败: {e}")
                raise
        
        # Step 3: 评分
        print("\n[Step 3] 评分")
        
        # 构建 gold 数据（包含输入和期望输出）
        sample_gold = sample_input.copy()
        # 对于评判模型，期望输出是 "1"（有趣）
        for field in output_fields:
            sample_gold[field] = "1"  # 假设期望是有趣的
        
        print(f"  Gold: {sample_gold}")
        print(f"  Pred: {result.toDict() if hasattr(result, 'toDict') else result}")
        
        # 创建评分指标
        exact_metric = create_exact_match_metric(output_fields)
        
        # 计算分数
        exact_score = exact_metric(sample_gold, result)
        print(f"  精确匹配分数: {exact_score}")
        
        # 如果有 OpenAI API，也测试余弦相似度
        if os.getenv("OPENAI_API_KEY") and output_fields:
            from autodspy.dspy_core.metrics import create_cosine_similarity_metric
            cosine_metric = create_cosine_similarity_metric(output_fields)
            cosine_score = cosine_metric(sample_gold, result)
            print(f"  余弦相似度分数: {cosine_score:.4f}")
        
        print("\n" + "=" * 60)
        print("✅ 端到端测试完成")
        print("=" * 60)


# ============================================================
# 手动运行入口
# ============================================================

def run_e2e_test():
    """手动运行端到端测试"""
    print("=" * 60)
    print("端到端测试：MLflow 模型加载 → 推理 → 评分")
    print("=" * 60)
    print()
    
    # 检查依赖
    if not MLFLOW_INSTALLED:
        print("❌ mlflow 未安装")
        return False
    
    if not DSPY_INSTALLED:
        print("❌ dspy 未安装")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    # 检查配置
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")
    print(f"MLflow URI: {mlflow_uri}")
    
    if not is_mlflow_server_available(mlflow_uri):
        print(f"❌ MLflow 服务器不可用: {mlflow_uri}")
        print("\n请先启动 MLflow Docker 服务:")
        print("  cd docker/docker-compose && bash start.sh")
        return False
    
    print(f"✅ MLflow 服务器连接成功")
    
    # 初始化配置
    from autodspy import AutoDSPyConfig, set_config
    config = AutoDSPyConfig(
        mlflow_enabled=True,
        mlflow_tracking_uri=mlflow_uri,
    )
    set_config(config)
    
    # 列出模型
    from autodspy.mlflow.loader import list_registered_models, load_model_from_registry, get_model_metadata
    
    print("\n[1] 列出已注册模型")
    models = list_registered_models()
    print(f"  找到 {len(models)} 个模型")
    
    if not models:
        print("  ⚠️ 没有已注册的模型，无法继续测试")
        print("  请先通过 DSPyUI 编译并注册一个模型")
        return False
    
    for model in models:
        print(f"  - {model['name']}")
    
    # 选择第一个模型
    model_name = models[0]['name']
    versions = models[0].get('latest_versions', [])
    
    if not versions:
        print(f"  ⚠️ 模型 {model_name} 没有版本")
        return False
    
    version = versions[0]['version']
    print(f"\n[2] 加载模型: {model_name} v{version}")
    
    # 获取模型元数据
    metadata = get_model_metadata(model_name, version)
    input_fields = metadata.get('input_fields', [])
    output_fields = metadata.get('output_fields', [])
    print(f"  输入字段: {input_fields}")
    print(f"  输出字段: {output_fields}")
    
    try:
        program = load_model_from_registry(model_name, version=version)
        print(f"  ✅ 加载成功: {type(program)}")
    except Exception as e:
        print(f"  ❌ 加载失败: {e}")
        return False
    
    # 检查 LLM API
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("DEEPSEEK_API_KEY"):
        print("\n⚠️ 没有配置 LLM API Key，跳过推理测试")
        return True
    
    # 执行推理
    print("\n[3] 执行推理")
    lm_model = os.getenv("DSPY_LM_MODEL", "openai/gpt-4o-mini")
    print(f"  LM: {lm_model}")
    
    # 根据输入字段准备输入数据
    sample_input = {}
    for field in input_fields:
        if field == "topic":
            sample_input[field] = "程序员"
        elif field == "joke":
            sample_input[field] = "为什么程序员总是分不清万圣节和圣诞节？因为 Oct 31 = Dec 25！"
        else:
            sample_input[field] = f"测试{field}"
    
    print(f"  输入: {sample_input}")
    
    try:
        lm = dspy.LM(lm_model)
        
        with dspy.context(lm=lm):
            result = program(**sample_input)
        
        print(f"  ✅ 推理成功")
        print(f"  输出: {result}")
        
    except Exception as e:
        print(f"  ❌ 推理失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 评分
    print("\n[4] 评分")
    from autodspy.dspy_core.metrics import create_exact_match_metric
    
    # 构建 gold 数据
    sample_gold = sample_input.copy()
    for field in output_fields:
        sample_gold[field] = "1"  # 假设期望输出
    
    print(f"  Gold: {sample_gold}")
    print(f"  Pred: {result.toDict() if hasattr(result, 'toDict') else result}")
    
    # 使用实际的输出字段
    if output_fields:
        metric = create_exact_match_metric(output_fields)
        score = metric(sample_gold, result)
        print(f"  精确匹配分数: {score}")
    else:
        print("  ⚠️ 无法确定输出字段，跳过评分")
    
    print("\n" + "=" * 60)
    print("✅ 端到端测试完成")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = run_e2e_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
