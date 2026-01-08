"""
模型版本切换流程集成测试

INPUT:  FastAPI 应用, MLflow Model Registry, ModelManager
OUTPUT: 验证模型版本注册、阶段切换、缓存失效的集成测试用例
POS:    确保模型生命周期管理的端到端流程正确性

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from dspyui.api.app import create_app


class TestModelLifecycleFlow:
    """测试完整的模型生命周期管理流程"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        app = create_app()
        
        # 手动初始化应用状态（模拟 lifespan startup）
        from dspyui.core.model_manager import ModelManager
        from dspyui.core.feedback import FeedbackService
        from dspyui.core.data_exporter import DataExporter
        from dspyui.config import get_api_config
        
        config = get_api_config()
        app.state.model_manager = ModelManager(
            cache_enabled=config.model_cache_enabled,
            cache_ttl=config.model_cache_ttl
        )
        app.state.feedback_service = FeedbackService(
            feedback_enabled=config.feedback_enabled
        )
        app.state.data_exporter = DataExporter()
        
        return TestClient(app)
    
    @pytest.fixture
    def mock_mlflow_registry(self):
        """模拟 MLflow Model Registry"""
        with patch('dspyui.core.model_manager.mlflow') as mock_mlflow, \
             patch('dspyui.api.routes.models.MlflowClient') as mock_client_class:
            
            # 模拟注册的模型列表
            mock_registered_models = [
                MagicMock(
                    name="joke-generator",
                    latest_versions=[
                        MagicMock(version="1", current_stage="Staging"),
                        MagicMock(version="2", current_stage="Production"),
                        MagicMock(version="3", current_stage="None")
                    ],
                    description="A joke generation model",
                    tags={"task": "text-generation", "domain": "humor"}
                ),
                MagicMock(
                    name="sentiment-analyzer",
                    latest_versions=[
                        MagicMock(version="1", current_stage="Production")
                    ],
                    description="Sentiment analysis model",
                    tags={"task": "classification"}
                )
            ]
            
            # 模拟 search_registered_models
            mock_mlflow.search_registered_models.return_value = mock_registered_models
            
            # 模拟 get_registered_model
            def mock_get_registered_model(name):
                for model in mock_registered_models:
                    if model.name == name:
                        return model
                raise Exception(f"Model {name} not found")
            
            mock_mlflow.get_registered_model.side_effect = mock_get_registered_model
            
            # 模拟 MlflowClient
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_mlflow.MlflowClient.return_value = mock_client
            
            # 模拟模型版本详情
            def mock_get_model_version(name, version):
                return MagicMock(
                    name=name,
                    version=version,
                    current_stage="Staging" if version == "1" else "Production",
                    creation_timestamp=int(time.time() * 1000),
                    run_id=f"run-{name}-{version}",
                    tags={"evaluation_score": "0.85"}
                )
            
            mock_client.get_model_version.side_effect = mock_get_model_version
            
            # 模拟阶段转换
            def mock_transition_stage(name, version, stage, archive_existing_versions=False):
                return MagicMock(
                    name=name,
                    version=version,
                    current_stage=stage
                )
            
            mock_client.transition_model_version_stage.side_effect = mock_transition_stage
            
            # 模拟模型加载
            mock_program_v1 = MagicMock()
            mock_program_v1.return_value = {"joke": "Version 1 joke"}
            mock_program_v2 = MagicMock()
            mock_program_v2.return_value = {"joke": "Version 2 joke - much funnier!"}
            
            def mock_load_model(model_uri):
                if "joke-generator/1" in model_uri or "joke-generator@Staging" in model_uri:
                    return mock_program_v1
                elif "joke-generator/2" in model_uri or "joke-generator@Production" in model_uri:
                    return mock_program_v2
                else:
                    raise Exception(f"Model not found: {model_uri}")
            
            mock_mlflow.dspy.load_model.side_effect = mock_load_model
            
            # 模拟 trace_id 生成
            mock_mlflow.get_current_active_span.return_value.trace_id = "model-test-trace"
            
            yield {
                'mlflow': mock_mlflow,
                'client_class': mock_client_class,
                'client': mock_client,
                'registered_models': mock_registered_models
            }
    
    @pytest.fixture
    def mock_dspy_setup(self):
        """模拟 DSPy 环境设置"""
        with patch('dspyui.api.app.dspy') as mock_dspy:
            mock_dspy.LM.return_value = MagicMock()
            mock_dspy.configure = MagicMock()
            mock_dspy.asyncify = lambda x: x
            yield mock_dspy
    
    def test_complete_model_lifecycle_flow(self, client, mock_mlflow_registry, mock_dspy_setup):
        """
        测试完整的模型生命周期流程：列表 → 版本查询 → 阶段切换 → 缓存失效 → 推理验证
        
        验证：
        1. 列出所有注册模型
        2. 查询特定模型的版本信息
        3. 切换模型版本到新阶段
        4. 验证缓存失效和新版本加载
        
        **Validates: Requirements 2.3, 2.5**
        """
        # === Step 1: 列出所有注册模型 ===
        models_response = client.get("/models")
        
        assert models_response.status_code == 200
        models_data = models_response.json()
        
        # 验证模型列表结构
        assert len(models_data) == 2
        joke_model = next(m for m in models_data if m["name"] == "joke-generator")
        assert joke_model["latest_version"] == "3"  # 最新版本
        assert joke_model["current_stage"] == "Production"  # 当前 Production 版本是 v2
        
        # === Step 2: 查询特定模型的版本信息 ===
        versions_response = client.get("/models/joke-generator/versions")
        
        assert versions_response.status_code == 200
        versions_data = versions_response.json()
        
        # 验证版本列表结构
        assert len(versions_data) >= 2
        version_1 = next(v for v in versions_data if v["version"] == "1")
        version_2 = next(v for v in versions_data if v["version"] == "2")
        
        assert version_1["stage"] == "Staging"
        assert version_2["stage"] == "Production"
        
        # === Step 3: 使用当前 Production 版本进行推理 ===
        predict_request_v2 = {
            "model": "joke-generator",
            "inputs": {"topic": "chicken"},
            "stage": "Production"
        }
        
        predict_response_v2 = client.post("/predict", json=predict_request_v2)
        
        assert predict_response_v2.status_code == 200
        predict_data_v2 = predict_response_v2.json()
        assert predict_data_v2["result"]["joke"] == "Version 2 joke - much funnier!"
        assert predict_data_v2["model_version"] == "2"
        
        # === Step 4: 切换版本 1 到 Production 阶段 ===
        stage_transition_request = {
            "version": "1",
            "stage": "Production"
        }
        
        transition_response = client.post(
            "/models/joke-generator/stage",
            json=stage_transition_request
        )
        
        assert transition_response.status_code == 200
        transition_data = transition_response.json()
        assert transition_data["status"] == "success"
        assert transition_data["message"] == "Model joke-generator version 1 transitioned to Production"
        
        # 验证 MLflow 阶段转换被调用
        mock_mlflow_registry['client'].transition_model_version_stage.assert_called_with(
            name="joke-generator",
            version="1",
            stage="Production",
            archive_existing_versions=False
        )
        
        # === Step 5: 验证缓存失效和新版本加载 ===
        # 再次使用 Production 阶段进行推理，应该使用版本 1
        predict_request_after_switch = {
            "model": "joke-generator",
            "inputs": {"topic": "chicken"},
            "stage": "Production"
        }
        
        predict_response_after_switch = client.post("/predict", json=predict_request_after_switch)
        
        assert predict_response_after_switch.status_code == 200
        predict_data_after_switch = predict_response_after_switch.json()
        
        # 验证现在使用的是版本 1 的输出
        assert predict_data_after_switch["result"]["joke"] == "Version 1 joke"
        assert predict_data_after_switch["model_version"] == "1"
    
    def test_model_version_loading_flexibility(self, client, mock_mlflow_registry, mock_dspy_setup):
        """
        测试模型加载的灵活性：版本号、阶段、别名
        
        验证：
        1. 通过版本号加载模型
        2. 通过阶段加载模型
        3. 不同加载方式返回正确的模型版本
        
        **Validates: Requirements 2.4**
        """
        # === 测试通过版本号加载 ===
        predict_by_version = {
            "model": "joke-generator",
            "inputs": {"topic": "test"},
            "version": "1"  # 明确指定版本号
        }
        
        response_v1 = client.post("/predict", json=predict_by_version)
        
        assert response_v1.status_code == 200
        data_v1 = response_v1.json()
        assert data_v1["result"]["joke"] == "Version 1 joke"
        assert data_v1["model_version"] == "1"
        
        # === 测试通过阶段加载 ===
        predict_by_stage = {
            "model": "joke-generator",
            "inputs": {"topic": "test"},
            "stage": "Staging"  # 使用 Staging 阶段
        }
        
        response_staging = client.post("/predict", json=predict_by_stage)
        
        assert response_staging.status_code == 200
        data_staging = response_staging.json()
        assert data_staging["result"]["joke"] == "Version 1 joke"  # Staging 对应版本 1
        assert data_staging["model_version"] == "1"
        
        # === 测试通过 Production 阶段加载 ===
        predict_by_production = {
            "model": "joke-generator",
            "inputs": {"topic": "test"},
            "stage": "Production"  # 使用 Production 阶段
        }
        
        response_production = client.post("/predict", json=predict_by_production)
        
        assert response_production.status_code == 200
        data_production = response_production.json()
        assert data_production["result"]["joke"] == "Version 2 joke - much funnier!"  # Production 对应版本 2
        assert data_production["model_version"] == "2"
    
    def test_model_cache_efficiency(self, client, mock_mlflow_registry, mock_dspy_setup):
        """
        测试模型缓存效率
        
        验证：
        1. 相同模型版本的重复加载使用缓存
        2. 缓存命中时不调用 MLflow 加载
        3. 缓存统计信息正确更新
        
        **Validates: Requirements 1.6**
        """
        predict_request = {
            "model": "joke-generator",
            "inputs": {"topic": "test"},
            "stage": "Production"
        }
        
        # === 第一次请求：应该加载模型 ===
        response_1 = client.post("/predict", json=predict_request)
        assert response_1.status_code == 200
        
        # 记录第一次调用的次数
        first_call_count = mock_mlflow_registry['mlflow'].dspy.load_model.call_count
        
        # === 第二次请求：应该使用缓存 ===
        response_2 = client.post("/predict", json=predict_request)
        assert response_2.status_code == 200
        
        # 验证两次响应一致
        data_1 = response_1.json()
        data_2 = response_2.json()
        assert data_1["result"] == data_2["result"]
        assert data_1["model_version"] == data_2["model_version"]
        
        # 验证第二次请求没有增加 MLflow 加载调用次数（使用了缓存）
        second_call_count = mock_mlflow_registry['mlflow'].dspy.load_model.call_count
        assert second_call_count == first_call_count  # 没有额外的加载调用
        
        # === 第三次请求不同版本：应该重新加载 ===
        predict_different_version = {
            "model": "joke-generator",
            "inputs": {"topic": "test"},
            "version": "1"  # 不同版本
        }
        
        response_3 = client.post("/predict", json=predict_different_version)
        assert response_3.status_code == 200
        
        # 验证第三次请求增加了加载调用次数（新版本）
        third_call_count = mock_mlflow_registry['mlflow'].dspy.load_model.call_count
        assert third_call_count > second_call_count
    
    def test_invalid_stage_transition(self, client, mock_mlflow_registry, mock_dspy_setup):
        """
        测试无效的阶段转换
        
        验证：
        1. 无效阶段名称应返回 400 错误
        2. 不存在的模型应返回 404 错误
        3. 不存在的版本应返回 404 错误
        
        **Validates: Requirements 2.3**
        """
        # === 测试无效阶段名称 ===
        invalid_stage_request = {
            "version": "1",
            "stage": "InvalidStage"  # 无效阶段
        }
        
        response_invalid_stage = client.post(
            "/models/joke-generator/stage",
            json=invalid_stage_request
        )
        
        assert response_invalid_stage.status_code == 400
        error_data = response_invalid_stage.json()
        assert "invalid stage" in error_data["detail"].lower()
        
        # === 测试不存在的模型 ===
        valid_stage_request = {
            "version": "1",
            "stage": "Production"
        }
        
        # 模拟模型不存在
        mock_mlflow_registry['mlflow'].get_registered_model.side_effect = Exception("Model not found")
        
        response_model_not_found = client.post(
            "/models/nonexistent-model/stage",
            json=valid_stage_request
        )
        
        assert response_model_not_found.status_code == 404
        error_data = response_model_not_found.json()
        assert "not found" in error_data["detail"].lower()
    
    def test_model_listing_completeness(self, client, mock_mlflow_registry, mock_dspy_setup):
        """
        测试模型列表的完整性
        
        验证：
        1. 所有注册模型都包含在列表中
        2. 每个模型包含必要的字段
        3. 模型版本信息正确
        
        **Validates: Requirements 2.1, 2.2**
        """
        # === 测试模型列表 ===
        models_response = client.get("/models")
        
        assert models_response.status_code == 200
        models_data = models_response.json()
        
        # 验证所有模型都在列表中
        model_names = [m["name"] for m in models_data]
        assert "joke-generator" in model_names
        assert "sentiment-analyzer" in model_names
        
        # 验证每个模型的字段完整性
        for model in models_data:
            assert "name" in model
            assert "latest_version" in model
            assert "current_stage" in model
            assert "description" in model
            assert "tags" in model
        
        # === 测试特定模型的版本列表 ===
        versions_response = client.get("/models/joke-generator/versions")
        
        assert versions_response.status_code == 200
        versions_data = versions_response.json()
        
        # 验证版本信息完整性
        for version in versions_data:
            assert "version" in version
            assert "stage" in version
            assert "created_at" in version
            assert "run_id" in version
        
        # === 测试不存在模型的版本查询 ===
        mock_mlflow_registry['mlflow'].get_registered_model.side_effect = Exception("Model not found")
        
        nonexistent_versions_response = client.get("/models/nonexistent-model/versions")
        
        assert nonexistent_versions_response.status_code == 404
        error_data = nonexistent_versions_response.json()
        assert "not found" in error_data["detail"].lower()


class TestModelCacheInvalidation:
    """测试模型缓存失效机制"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        app = create_app()
        
        # 手动初始化应用状态（模拟 lifespan startup）
        from dspyui.core.model_manager import ModelManager
        from dspyui.core.feedback import FeedbackService
        from dspyui.core.data_exporter import DataExporter
        from dspyui.config import get_api_config
        
        config = get_api_config()
        app.state.model_manager = ModelManager(
            cache_enabled=config.model_cache_enabled,
            cache_ttl=config.model_cache_ttl
        )
        app.state.feedback_service = FeedbackService(
            feedback_enabled=config.feedback_enabled
        )
        app.state.data_exporter = DataExporter()
        
        return TestClient(app)
    
    @pytest.fixture
    def mock_setup(self):
        """模拟环境设置"""
        with patch('dspyui.core.model_manager.mlflow') as mock_mlflow, \
             patch('dspyui.api.routes.models.MlflowClient') as mock_client_class, \
             patch('dspyui.api.app.dspy') as mock_dspy:
            
            # 模拟模型注册
            mock_model = MagicMock(
                name="test-model",
                latest_versions=[MagicMock(version="1", current_stage="Production")]
            )
            mock_mlflow.get_registered_model.return_value = mock_model
            
            # 模拟 MlflowClient
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_mlflow.MlflowClient.return_value = mock_client
            
            # 模拟版本信息
            mock_client.get_model_version.return_value = MagicMock(
                name="test-model",
                version="1",
                current_stage="Production"
            )
            
            # 模拟阶段转换
            mock_client.transition_model_version_stage.return_value = MagicMock(
                name="test-model",
                version="1",
                current_stage="Staging"
            )
            
            # 模拟模型加载
            mock_program = MagicMock()
            mock_program.return_value = {"output": "test result"}
            mock_mlflow.dspy.load_model.return_value = mock_program
            
            # 模拟 DSPy
            mock_dspy.LM.return_value = MagicMock()
            mock_dspy.configure = MagicMock()
            mock_dspy.asyncify = lambda x: x
            
            # 模拟 trace_id
            mock_mlflow.get_current_active_span.return_value.trace_id = "cache-test-trace"
            
            yield {
                'mlflow': mock_mlflow,
                'client_class': mock_client_class,
                'client': mock_client
            }
    
    def test_cache_invalidation_on_stage_transition(self, client, mock_setup):
        """
        测试阶段转换时的缓存失效
        
        验证：
        1. 阶段转换前模型被缓存
        2. 阶段转换后缓存被失效
        3. 后续请求重新加载模型
        
        **Validates: Requirements 2.5**
        """
        # === Step 1: 首次推理，建立缓存 ===
        predict_request = {
            "model": "test-model",
            "inputs": {"input": "test"},
            "stage": "Production"
        }
        
        response_1 = client.post("/predict", json=predict_request)
        assert response_1.status_code == 200
        
        # 记录首次加载调用次数
        initial_load_count = mock_setup['mlflow'].dspy.load_model.call_count
        
        # === Step 2: 再次推理，使用缓存 ===
        response_2 = client.post("/predict", json=predict_request)
        assert response_2.status_code == 200
        
        # 验证使用了缓存（没有额外的加载调用）
        cached_load_count = mock_setup['mlflow'].dspy.load_model.call_count
        assert cached_load_count == initial_load_count
        
        # === Step 3: 执行阶段转换 ===
        stage_transition_request = {
            "version": "1",
            "stage": "Staging"
        }
        
        transition_response = client.post(
            "/models/test-model/stage",
            json=stage_transition_request
        )
        
        assert transition_response.status_code == 200
        
        # === Step 4: 阶段转换后再次推理，应该重新加载 ===
        response_3 = client.post("/predict", json=predict_request)
        assert response_3.status_code == 200
        
        # 验证缓存被失效，重新加载了模型
        post_transition_load_count = mock_setup['mlflow'].dspy.load_model.call_count
        assert post_transition_load_count > cached_load_count
    
    def test_cache_isolation_between_models(self, client, mock_setup):
        """
        测试不同模型间的缓存隔离
        
        验证：
        1. 不同模型使用独立的缓存
        2. 一个模型的缓存失效不影响其他模型
        
        **Validates: Requirements 2.5**
        """
        # 模拟两个不同的模型
        def mock_get_registered_model(name):
            if name == "model-a":
                return MagicMock(name="model-a", latest_versions=[])
            elif name == "model-b":
                return MagicMock(name="model-b", latest_versions=[])
            else:
                raise Exception(f"Model {name} not found")
        
        mock_setup['mlflow'].get_registered_model.side_effect = mock_get_registered_model
        mock_setup['models_mlflow'].get_registered_model.side_effect = mock_get_registered_model
        
        # 模拟不同模型的程序
        def mock_load_model(model_uri):
            if "model-a" in model_uri:
                program = MagicMock()
                program.return_value = {"output": "result from model A"}
                return program
            elif "model-b" in model_uri:
                program = MagicMock()
                program.return_value = {"output": "result from model B"}
                return program
            else:
                raise Exception(f"Model not found: {model_uri}")
        
        mock_setup['mlflow'].dspy.load_model.side_effect = mock_load_model
        
        # === 加载模型 A ===
        predict_a = {
            "model": "model-a",
            "inputs": {"input": "test"},
            "stage": "Production"
        }
        
        response_a1 = client.post("/predict", json=predict_a)
        assert response_a1.status_code == 200
        assert response_a1.json()["result"]["output"] == "result from model A"
        
        # === 加载模型 B ===
        predict_b = {
            "model": "model-b",
            "inputs": {"input": "test"},
            "stage": "Production"
        }
        
        response_b1 = client.post("/predict", json=predict_b)
        assert response_b1.status_code == 200
        assert response_b1.json()["result"]["output"] == "result from model B"
        
        # 记录当前加载次数
        load_count_before = mock_setup['mlflow'].dspy.load_model.call_count
        
        # === 对模型 A 执行阶段转换 ===
        stage_transition_a = {
            "version": "1",
            "stage": "Staging"
        }
        
        transition_response_a = client.post(
            "/models/model-a/stage",
            json=stage_transition_a
        )
        assert transition_response_a.status_code == 200
        
        # === 再次使用模型 A（应该重新加载）===
        response_a2 = client.post("/predict", json=predict_a)
        assert response_a2.status_code == 200
        
        # === 再次使用模型 B（应该使用缓存）===
        response_b2 = client.post("/predict", json=predict_b)
        assert response_b2.status_code == 200
        
        # 验证只有模型 A 被重新加载，模型 B 使用了缓存
        load_count_after = mock_setup['mlflow'].dspy.load_model.call_count
        # 应该只增加了 1 次加载（模型 A 的重新加载）
        assert load_count_after == load_count_before + 1