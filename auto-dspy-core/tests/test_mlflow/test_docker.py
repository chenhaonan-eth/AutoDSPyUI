"""
测试 auto-dspy-core 与 Docker MLflow 的集成

INPUT:  autodspy 配置, Docker MLflow 服务
OUTPUT: 测试报告，验证 MLflow 连接、追踪和模型注册功能
POS:    集成测试，验证 auto-dspy-core 与 MLflow Docker 服务的完整工作流

测试内容:
1. 环境变量配置检查
2. MLflow 服务器连接测试
3. autodspy 配置初始化测试
4. MLflow 追踪功能测试
5. 模型注册功能测试

运行方式:
    # 需要先启动 MLflow Docker 服务
    cd docker/docker-compose && bash start.sh && cd ../..
    
    # 运行测试
    cd auto-dspy-core
    uv run pytest tests/test_mlflow/test_docker.py -v -m integration

⚠️ 一旦我被更新，务必更新我的开头注释
"""

import os
import sys
from pathlib import Path

import pytest

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 检查 mlflow 是否安装
try:
    import mlflow
    MLFLOW_INSTALLED = True
except ImportError:
    MLFLOW_INSTALLED = False


def is_mlflow_server_available(uri: str) -> bool:
    """检查 MLflow 服务器是否可用"""
    try:
        import requests
        response = requests.get(f"{uri}/health", timeout=5)
        return response.status_code == 200
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


@pytest.mark.integration
@pytest.mark.requires_mlflow
class TestMlflowDockerConnection:
    """测试 MLflow Docker 连接"""
    
    def test_environment_variables(self, mlflow_config):
        """测试环境变量配置"""
        assert mlflow_config["tracking_uri"], "MLFLOW_TRACKING_URI 未配置"
        assert mlflow_config["experiment_name"], "MLFLOW_EXPERIMENT_NAME 未配置"
        
        print(f"\n配置信息:")
        print(f"  MLFLOW_ENABLED: {mlflow_config['enabled']}")
        print(f"  MLFLOW_TRACKING_URI: {mlflow_config['tracking_uri']}")
        print(f"  MLFLOW_EXPERIMENT_NAME: {mlflow_config['experiment_name']}")
    
    def test_server_health(self, mlflow_config):
        """测试 MLflow 服务器健康状态"""
        if not mlflow_config["enabled"]:
            pytest.skip("MLflow 未启用")
        
        uri = mlflow_config["tracking_uri"]
        
        if not is_mlflow_server_available(uri):
            pytest.skip(f"MLflow 服务器不可用: {uri}")
        
        import requests
        response = requests.get(f"{uri}/health", timeout=5)
        assert response.status_code == 200, f"MLflow 服务器响应异常: {response.status_code}"
        
        print(f"\n✅ MLflow 服务器连接成功: {uri}")
    
    def test_mlflow_client_connection(self, mlflow_config):
        """测试 MLflow 客户端连接"""
        if not mlflow_config["enabled"]:
            pytest.skip("MLflow 未启用")
        
        if not MLFLOW_INSTALLED:
            pytest.skip("mlflow 未安装")
        
        uri = mlflow_config["tracking_uri"]
        
        if not is_mlflow_server_available(uri):
            pytest.skip(f"MLflow 服务器不可用: {uri}")
        
        import mlflow
        mlflow.set_tracking_uri(uri)
        
        # 获取或创建实验
        experiment_name = mlflow_config["experiment_name"]
        experiment = mlflow.get_experiment_by_name(experiment_name)
        
        if experiment is None:
            experiment_id = mlflow.create_experiment(experiment_name)
            print(f"\n✅ 创建实验: {experiment_name} (ID: {experiment_id})")
        else:
            print(f"\n✅ 实验已存在: {experiment_name} (ID: {experiment.experiment_id})")
        
        # 列出所有实验
        experiments = mlflow.search_experiments()
        print(f"✅ 共有 {len(experiments)} 个实验")
        assert len(experiments) > 0


@pytest.mark.integration
@pytest.mark.requires_mlflow
class TestAutoDSPyMlflowIntegration:
    """测试 autodspy 与 MLflow 的集成"""
    
    def test_autodspy_config_with_mlflow(self, mlflow_config):
        """测试 autodspy 配置初始化"""
        if not mlflow_config["enabled"]:
            pytest.skip("MLflow 未启用")
        
        uri = mlflow_config["tracking_uri"]
        
        if not is_mlflow_server_available(uri):
            pytest.skip(f"MLflow 服务器不可用: {uri}")
        
        from autodspy import AutoDSPyConfig, set_config, get_config
        
        config = AutoDSPyConfig(
            mlflow_enabled=True,
            mlflow_tracking_uri=uri,
            mlflow_experiment_name=mlflow_config["experiment_name"],
        )
        set_config(config)
        
        current_config = get_config()
        assert current_config.mlflow_enabled is True
        assert current_config.mlflow_tracking_uri == uri
        
        print(f"\n✅ autodspy 配置初始化成功")
        print(f"  mlflow_enabled: {current_config.mlflow_enabled}")
        print(f"  mlflow_tracking_uri: {current_config.mlflow_tracking_uri}")
    
    def test_init_mlflow(self, mlflow_config):
        """测试 MLflow 初始化"""
        if not mlflow_config["enabled"]:
            pytest.skip("MLflow 未启用")
        
        if not MLFLOW_INSTALLED:
            pytest.skip("mlflow 未安装")
        
        uri = mlflow_config["tracking_uri"]
        
        if not is_mlflow_server_available(uri):
            pytest.skip(f"MLflow 服务器不可用: {uri}")
        
        from autodspy import AutoDSPyConfig, set_config
        from autodspy.mlflow.tracking import init_mlflow
        
        config = AutoDSPyConfig(
            mlflow_enabled=True,
            mlflow_tracking_uri=uri,
            mlflow_experiment_name=mlflow_config["experiment_name"],
        )
        set_config(config)
        
        result = init_mlflow()
        assert result is True, "MLflow 初始化失败"
        
        print(f"\n✅ MLflow 初始化成功")
    
    def test_track_compilation_context(self, mlflow_config):
        """测试编译追踪上下文管理器"""
        if not mlflow_config["enabled"]:
            pytest.skip("MLflow 未启用")
        
        if not MLFLOW_INSTALLED:
            pytest.skip("mlflow 未安装")
        
        uri = mlflow_config["tracking_uri"]
        
        if not is_mlflow_server_available(uri):
            pytest.skip(f"MLflow 服务器不可用: {uri}")
        
        from autodspy import AutoDSPyConfig, set_config
        from autodspy.mlflow.tracking import init_mlflow, track_compilation
        
        config = AutoDSPyConfig(
            mlflow_enabled=True,
            mlflow_tracking_uri=uri,
            mlflow_experiment_name=mlflow_config["experiment_name"],
        )
        set_config(config)
        init_mlflow()
        
        params = {
            "model": "test-model",
            "optimizer": "BootstrapFewShot",
            "test_param": "test_value",
        }
        
        with track_compilation("docker_test_run", params) as run:
            assert run is not None, "track_compilation 应返回有效的 run 对象"
            
            run_id = run.info.run_id
            print(f"\n✅ 创建追踪 Run: {run_id}")
            
            # 验证 run 状态
            assert run.info.status == "RUNNING"
        
        # 验证 run 已结束
        import mlflow
        finished_run = mlflow.get_run(run_id)
        assert finished_run.info.status == "FINISHED"
        
        print(f"✅ Run 已完成: {run_id}")


@pytest.mark.integration
@pytest.mark.requires_mlflow
class TestMlflowModelRegistry:
    """测试 MLflow 模型注册功能"""
    
    def test_list_registered_models(self, mlflow_config):
        """测试列出已注册模型"""
        if not mlflow_config["enabled"]:
            pytest.skip("MLflow 未启用")
        
        if not MLFLOW_INSTALLED:
            pytest.skip("mlflow 未安装")
        
        uri = mlflow_config["tracking_uri"]
        
        if not is_mlflow_server_available(uri):
            pytest.skip(f"MLflow 服务器不可用: {uri}")
        
        import mlflow
        from mlflow import MlflowClient
        
        mlflow.set_tracking_uri(uri)
        client = MlflowClient()
        
        registered_models = client.search_registered_models()
        
        print(f"\n已注册模型数量: {len(registered_models)}")
        
        for model in registered_models[:5]:  # 只显示前 5 个
            print(f"  - {model.name}")
            
            # 获取最新版本
            versions = client.search_model_versions(f"name='{model.name}'")
            if versions:
                latest = max(versions, key=lambda v: int(v.version))
                print(f"    最新版本: {latest.version}, 阶段: {latest.current_stage}")
    
    def test_get_mlflow_ui_url(self, mlflow_config):
        """测试获取 MLflow UI URL"""
        if not mlflow_config["enabled"]:
            pytest.skip("MLflow 未启用")
        
        uri = mlflow_config["tracking_uri"]
        
        if not is_mlflow_server_available(uri):
            pytest.skip(f"MLflow 服务器不可用: {uri}")
        
        from autodspy import AutoDSPyConfig, set_config
        from autodspy.mlflow.tracking import get_mlflow_ui_url
        
        config = AutoDSPyConfig(
            mlflow_enabled=True,
            mlflow_tracking_uri=uri,
        )
        set_config(config)
        
        # 测试基础 URL
        base_url = get_mlflow_ui_url()
        assert uri.rstrip('/') in base_url or "localhost" in base_url
        print(f"\n基础 URL: {base_url}")
        
        # 测试模型 URL
        model_url = get_mlflow_ui_url(model_name="test-model")
        assert "models" in model_url
        assert "test-model" in model_url
        print(f"模型 URL: {model_url}")
        
        # 测试版本 URL
        version_url = get_mlflow_ui_url(model_name="test-model", model_version="1")
        assert "versions" in version_url
        print(f"版本 URL: {version_url}")


def run_docker_tests():
    """手动运行 Docker 测试的入口函数"""
    print("=" * 60)
    print("测试 auto-dspy-core 与 MLflow Docker 集成")
    print("=" * 60)
    print()
    
    # 0. 检查 mlflow 是否安装
    if not MLFLOW_INSTALLED:
        print("❌ mlflow 未安装，请先安装: uv add mlflow")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    # 1. 检查环境变量
    print("1. 检查环境变量配置")
    print("-" * 60)
    
    mlflow_enabled = os.getenv("MLFLOW_ENABLED", "true")
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")
    mlflow_experiment = os.getenv("MLFLOW_EXPERIMENT_NAME", "autodspy-tests")
    
    print(f"  MLFLOW_ENABLED: {mlflow_enabled}")
    print(f"  MLFLOW_TRACKING_URI: {mlflow_uri}")
    print(f"  MLFLOW_EXPERIMENT_NAME: {mlflow_experiment}")
    print()
    
    if mlflow_enabled.lower() != "true":
        print("❌ MLflow 未启用")
        return False
    
    # 2. 测试服务器连接
    print("2. 测试 MLflow 服务器连接")
    print("-" * 60)
    
    if not is_mlflow_server_available(mlflow_uri):
        print(f"  ❌ 无法连接到 MLflow 服务器: {mlflow_uri}")
        print()
        print("请先启动 MLflow Docker 服务:")
        print("  cd docker/docker-compose && bash start.sh")
        return False
    
    print(f"  ✅ MLflow 服务器连接成功: {mlflow_uri}")
    print()
    
    # 3. 测试 autodspy 配置
    print("3. 测试 autodspy 配置")
    print("-" * 60)
    
    try:
        from autodspy import AutoDSPyConfig, set_config, get_config
        from autodspy.mlflow.tracking import init_mlflow, track_compilation
        
        config = AutoDSPyConfig(
            mlflow_enabled=True,
            mlflow_tracking_uri=mlflow_uri,
            mlflow_experiment_name=mlflow_experiment,
        )
        set_config(config)
        
        print(f"  ✅ autodspy 配置初始化成功")
        
        result = init_mlflow()
        if result:
            print(f"  ✅ MLflow 初始化成功")
        else:
            print(f"  ❌ MLflow 初始化失败")
            return False
            
    except Exception as e:
        print(f"  ❌ autodspy 配置失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()
    
    # 4. 测试追踪功能
    print("4. 测试追踪功能")
    print("-" * 60)
    
    try:
        params = {
            "model": "docker-test-model",
            "optimizer": "BootstrapFewShot",
            "test_source": "test_docker.py",
        }
        
        with track_compilation("docker_integration_test", params) as run:
            if run:
                print(f"  ✅ 创建追踪 Run: {run.info.run_id}")
            else:
                print(f"  ❌ 追踪 Run 创建失败")
                return False
                
    except Exception as e:
        print(f"  ❌ 追踪测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()
    
    # 5. 列出已注册模型
    print("5. 列出已注册模型")
    print("-" * 60)
    
    try:
        import mlflow
        from mlflow import MlflowClient
        
        mlflow.set_tracking_uri(mlflow_uri)
        client = MlflowClient()
        
        registered_models = client.search_registered_models()
        print(f"  ✅ 发现 {len(registered_models)} 个已注册模型")
        
        for model in registered_models[:5]:
            print(f"    - {model.name}")
            
    except Exception as e:
        print(f"  ⚠️  列出模型失败: {e}")
    print()
    
    # 总结
    print("=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)
    print()
    print("auto-dspy-core 与 MLflow Docker 服务集成正常。")
    print()
    print("访问地址:")
    print(f"  - MLflow UI: {mlflow_uri}")
    print(f"  - MinIO 控制台: http://localhost:9001")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = run_docker_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
