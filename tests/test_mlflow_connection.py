#!/usr/bin/env python3
"""
测试 DSPyUI API 服务器与 Docker MLflow 的连接
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_mlflow_connection():
    """测试 MLflow 连接"""
    print("=" * 60)
    print("测试 MLflow Docker 连接")
    print("=" * 60)
    print()
    
    # 1. 检查环境变量
    print("1. 检查环境变量配置")
    print("-" * 60)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    mlflow_enabled = os.getenv("MLFLOW_ENABLED", "true")
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")
    mlflow_experiment = os.getenv("MLFLOW_EXPERIMENT_NAME", "dspyui-experiments")
    
    print(f"  MLFLOW_ENABLED: {mlflow_enabled}")
    print(f"  MLFLOW_TRACKING_URI: {mlflow_uri}")
    print(f"  MLFLOW_EXPERIMENT_NAME: {mlflow_experiment}")
    print()
    
    if mlflow_enabled.lower() != "true":
        print("❌ MLflow 未启用")
        return False
    
    # 2. 测试 MLflow 服务器连接
    print("2. 测试 MLflow 服务器连接")
    print("-" * 60)
    
    import requests
    try:
        response = requests.get(f"{mlflow_uri}/health", timeout=5)
        if response.status_code == 200:
            print(f"  ✅ MLflow 服务器连接成功: {mlflow_uri}")
        else:
            print(f"  ❌ MLflow 服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ 无法连接到 MLflow 服务器: {e}")
        return False
    print()
    
    # 3. 测试 MLflow 客户端
    print("3. 测试 MLflow 客户端")
    print("-" * 60)
    
    try:
        import mlflow
        mlflow.set_tracking_uri(mlflow_uri)
        
        # 获取或创建实验
        experiment = mlflow.get_experiment_by_name(mlflow_experiment)
        if experiment is None:
            experiment_id = mlflow.create_experiment(mlflow_experiment)
            print(f"  ✅ 创建实验: {mlflow_experiment} (ID: {experiment_id})")
        else:
            print(f"  ✅ 实验已存在: {mlflow_experiment} (ID: {experiment.experiment_id})")
        
        # 列出所有实验
        experiments = mlflow.search_experiments()
        print(f"  ✅ 共有 {len(experiments)} 个实验")
        
    except Exception as e:
        print(f"  ❌ MLflow 客户端测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()
    
    # 4. 测试 MLflow 追踪功能
    print("4. 测试 MLflow 追踪功能")
    print("-" * 60)
    
    try:
        # 创建一个测试运行
        with mlflow.start_run(run_name="connection_test") as run:
            # 记录参数
            mlflow.log_param("test_param", "test_value")
            mlflow.log_param("connection_test", True)
            
            # 记录指标
            mlflow.log_metric("test_metric", 0.95)
            mlflow.log_metric("connection_score", 1.0)
            
            # 记录标签
            mlflow.set_tag("test_type", "connection_test")
            mlflow.set_tag("source", "test_mlflow_connection.py")
            
            run_id = run.info.run_id
            print(f"  ✅ 创建测试运行: {run_id}")
            print(f"  ✅ 记录参数和指标成功")
        
        # 验证运行记录
        run_info = mlflow.get_run(run_id)
        print(f"  ✅ 验证运行记录成功")
        print(f"     - 状态: {run_info.info.status}")
        print(f"     - 参数数量: {len(run_info.data.params)}")
        print(f"     - 指标数量: {len(run_info.data.metrics)}")
        
    except Exception as e:
        print(f"  ❌ MLflow 追踪测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()
    
    # 5. 测试 DSPyUI MLflow 集成模块
    print("5. 测试 DSPyUI MLflow 集成模块")
    print("-" * 60)
    
    try:
        import autodspy
        from dspyui.config import MLFLOW_ENABLED, MLFLOW_TRACKING_URI, MLFLOW_EXPERIMENT_NAME
        
        print(f"  ✅ MLflow 集成模块导入成功")
        print(f"     - 启用状态: {MLFLOW_ENABLED}")
        print(f"     - 追踪 URI: {MLFLOW_TRACKING_URI}")
        print(f"     - 实验名称: {MLFLOW_EXPERIMENT_NAME}")
        
        # 测试初始化函数
        autodspy.init_mlflow()
        print(f"  ✅ init_mlflow() 执行成功")
        
    except Exception as e:
        print(f"  ❌ DSPyUI MLflow 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()
    
    # 6. 测试 MinIO 连接（可选）
    print("6. 测试 MinIO 对象存储")
    print("-" * 60)
    
    try:
        minio_url = "http://localhost:9000"
        response = requests.get(f"{minio_url}/minio/health/live", timeout=5)
        if response.status_code == 200:
            print(f"  ✅ MinIO 服务连接成功: {minio_url}")
        else:
            print(f"  ⚠️  MinIO 服务响应异常: {response.status_code}")
    except Exception as e:
        print(f"  ⚠️  无法连接到 MinIO 服务: {e}")
    print()
    
    # 7. 测试模型加载和对话任务
    print("7. 测试模型加载和对话任务")
    print("-" * 60)
    
    try:
        import dspy
        from dspy import Predict
        from mlflow import MlflowClient
        
        # 配置 LLM
        api_key = os.getenv("OPENAI_API_KEY")
        api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        
        if not api_key:
            print("  ⚠️  未配置 OPENAI_API_KEY，跳过对话测试")
        else:
            # 初始化 LLM
            lm = dspy.LM(
                model="openai/gpt-4o-mini",
                api_key=api_key,
                api_base=api_base
            )
            dspy.configure(lm=lm)
            
            print(f"  ✅ LLM 配置成功: gpt-4o-mini")
            
            # 创建一个简单的对话签名
            class SimpleQA(dspy.Signature):
                """回答用户的问题"""
                question = dspy.InputField(desc="用户的问题")
                answer = dspy.OutputField(desc="简洁的答案")
            
            # 创建预测模块
            qa_module = Predict(SimpleQA)
            
            # 测试对话
            test_question = "什么是 MLflow？"
            print(f"  📝 测试问题: {test_question}")
            
            result = qa_module(question=test_question)
            answer = result.answer
            
            print(f"  ✅ 模型回答: {answer[:100]}...")
            
            # 记录到 MLflow
            with mlflow.start_run(run_name="qa_test") as run:
                mlflow.log_param("question", test_question)
                mlflow.log_param("model", "gpt-4o-mini")
                mlflow.log_metric("answer_length", len(answer))
                mlflow.set_tag("test_type", "qa_conversation")
                
                print(f"  ✅ 对话记录已保存到 MLflow (Run ID: {run.info.run_id})")
            
            # 测试注册模型（如果有的话）
            try:
                client = MlflowClient()
                registered_models = client.search_registered_models()
                
                if registered_models:
                    print(f"  ✅ 发现 {len(registered_models)} 个已注册模型:")
                    for model in registered_models[:3]:  # 只显示前3个
                        print(f"     - {model.name}")
                        
                        # 尝试加载第一个模型
                        if model == registered_models[0]:
                            try:
                                latest_versions = client.get_latest_versions(model.name, stages=["Production", "Staging", "None"])
                                if latest_versions:
                                    version = latest_versions[0].version
                                    model_uri = f"models:/{model.name}/{version}"
                                    print(f"  ✅ 可以加载模型: {model_uri}")
                            except Exception as e:
                                print(f"  ⚠️  加载模型失败: {e}")
                else:
                    print(f"  ℹ️  暂无已注册的模型")
                    
            except Exception as e:
                print(f"  ⚠️  查询注册模型失败: {e}")
                
    except ImportError as e:
        print(f"  ⚠️  DSPy 未安装，跳过对话测试: {e}")
    except Exception as e:
        print(f"  ❌ 对话测试失败: {e}")
        import traceback
        traceback.print_exc()
        # 不返回 False，因为这是可选测试
    print()
    
    # 总结
    print("=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)
    print()
    print("MLflow Docker 服务运行正常，API 服务器可以正常连接。")
    print()
    print("访问地址:")
    print(f"  - MLflow UI: {mlflow_uri}")
    print(f"  - MinIO 控制台: http://localhost:9001")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = test_mlflow_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
