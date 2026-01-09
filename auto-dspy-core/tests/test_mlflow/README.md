# MLflow 集成测试

本目录包含 autodspy.mlflow 模块的测试用例。

## 文件清单

| 文件名 | 层级定位 | 核心功能 |
|--------|----------|----------|
| `__init__.py` | 模块初始化 | 标识测试包 |
| `test_tracking.py` | 单元测试 | 测试 MLflow 追踪功能 |
| `test_registry.py` | 集成测试 | 测试模型注册表功能 |
| `test_loader.py` | 集成测试 | 测试模型加载功能 |
| `test_service.py` | 单元测试 | 测试模型注册服务 |
| `test_docker.py` | 集成测试 | 测试与 Docker MLflow 服务的集成 |
| `test_e2e_model_inference.py` | 端到端测试 | 测试模型加载 → 推理 → 评分完整流程 |

## 测试覆盖

- ✅ 参数截断和序列化
- ✅ 数据集哈希计算
- ✅ MLflow UI URL 构造
- ✅ MLflow 初始化
- ✅ 编译追踪上下文管理器
- ✅ 指标和工件记录
- ✅ 模型注册和阶段转换
- ✅ 模型列表和版本查询
- ✅ 模型加载和提示词工件
- ✅ Docker MLflow 服务连接
- ✅ autodspy 与 Docker MLflow 集成
- ✅ 端到端模型加载、推理、评分流程

## 运行 Docker 集成测试

```bash
# 1. 启动 MLflow Docker 服务
cd docker/docker-compose && bash start.sh && cd ../..

# 2. 运行 Docker 集成测试
cd auto-dspy-core
uv run pytest tests/test_mlflow/test_docker.py -v -m integration

# 3. 或直接运行测试脚本
uv run python tests/test_mlflow/test_docker.py
```

## 运行端到端推理测试

```bash
# 需要：MLflow Docker 服务 + LLM API Key

# 1. 启动 MLflow Docker 服务
cd docker/docker-compose && bash start.sh && cd ../..

# 2. 确保 .env 中配置了 LLM API Key
# OPENAI_API_KEY=xxx 或 DEEPSEEK_API_KEY=xxx

# 3. 运行端到端测试
cd auto-dspy-core
uv run pytest tests/test_mlflow/test_e2e_model_inference.py -v -s

# 4. 或直接运行测试脚本
uv run python tests/test_mlflow/test_e2e_model_inference.py
```
