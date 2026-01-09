"""
真实环境推理测试脚本

INPUT:  Docker MLflow 服务, LLM API Key, 已注册模型
OUTPUT: 验证 generate_response_from_mlflow 在真实环境下的推理效果
POS:    手动测试脚本，用于验证端到端推理流程

运行方式:
    cd auto-dspy-core
    uv run python tests/test_mlflow/test_real_inference.py

⚠️ 需要先启动 MLflow Docker 服务并配置 LLM API Key
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()


def check_prerequisites():
    """检查前置条件"""
    print("=" * 60)
    print("检查前置条件")
    print("=" * 60)
    
    # 检查 MLflow 服务
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")
    print(f"\n1. MLflow 服务: {tracking_uri}")
    
    try:
        import requests
        response = requests.get(f"{tracking_uri}/health", timeout=3)
        if response.status_code == 200:
            print("   ✅ MLflow 服务可用")
        else:
            print(f"   ❌ MLflow 服务返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ MLflow 服务不可用: {e}")
        return False
    
    # 检查 LLM API Key
    print("\n2. LLM API Key:")
    llm_keys = {
        "DEEPSEEK_API_KEY": "deepseek-chat",
        "OPENAI_API_KEY": "gpt-4o-mini",
        "ANTHROPIC_API_KEY": "claude-3-haiku-20240307",
        "GROQ_API_KEY": "llama-3.1-8b-instant",
        "GOOGLE_API_KEY": "gemini-1.5-flash",
    }
    
    available_llm = None
    for key, model in llm_keys.items():
        if os.getenv(key):
            print(f"   ✅ {key} 已配置 -> 使用 {model}")
            if not available_llm:
                available_llm = model
        else:
            print(f"   ⚪ {key} 未配置")
    
    if not available_llm:
        print("   ❌ 没有配置任何 LLM API Key")
        return False
    
    return True, available_llm


def list_available_models():
    """列出可用模型"""
    print("\n" + "=" * 60)
    print("可用模型列表")
    print("=" * 60)
    
    from autodspy import AutoDSPyConfig, set_config
    from autodspy.mlflow.loader import list_registered_models, list_model_versions, get_model_metadata
    
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")
    config = AutoDSPyConfig(
        mlflow_enabled=True,
        mlflow_tracking_uri=tracking_uri,
    )
    set_config(config)
    
    models = list_registered_models()
    
    if not models:
        print("\n❌ 没有找到已注册的模型")
        return None
    
    print(f"\n找到 {len(models)} 个模型:\n")
    
    model_info = []
    for i, m in enumerate(models, 1):
        name = m['name']
        versions = list_model_versions(name)
        
        print(f"{i}. {name}")
        
        for v in versions[:3]:  # 只显示前3个版本
            metadata = get_model_metadata(name, v['version'])
            input_fields = metadata.get('input_fields', [])
            output_fields = metadata.get('output_fields', [])
            score = metadata.get('evaluation_score', 'N/A')
            
            print(f"   v{v['version']}: {input_fields} -> {output_fields} (score: {score})")
            
            model_info.append({
                'name': name,
                'version': v['version'],
                'input_fields': input_fields,
                'output_fields': output_fields,
            })
        
        if len(versions) > 3:
            print(f"   ... 还有 {len(versions) - 3} 个版本")
        print()
    
    return model_info


def test_single_inference(model_name: str, version: str, input_data: dict, llm_model: str):
    """测试单条推理"""
    print("\n" + "=" * 60)
    print("单条推理测试")
    print("=" * 60)
    
    from autodspy.dspy_core.runner import generate_response_from_mlflow
    
    print(f"\n模型: {model_name} v{version}")
    print(f"LLM: {llm_model}")
    print(f"输入: {input_data}")
    print("\n正在推理...")
    
    try:
        result = generate_response_from_mlflow(
            model_name=model_name,
            version=version,
            row_data=input_data,
            llm_model=llm_model
        )
        
        print("\n" + "-" * 40)
        print("推理结果:")
        print("-" * 40)
        print(result)
        print("-" * 40)
        print("\n✅ 推理成功!")
        return True
        
    except Exception as e:
        print(f"\n❌ 推理失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_inference(model_name: str, version: str, batch_data: list, llm_model: str):
    """测试批量推理"""
    print("\n" + "=" * 60)
    print("批量推理测试")
    print("=" * 60)
    
    import pandas as pd
    from autodspy.dspy_core.runner import run_batch_inference_from_mlflow
    
    df = pd.DataFrame(batch_data)
    
    print(f"\n模型: {model_name} v{version}")
    print(f"LLM: {llm_model}")
    print(f"批量数据 ({len(df)} 条):")
    print(df.to_string(index=False))
    print("\n正在批量推理...")
    
    def progress_callback(current, total):
        print(f"  进度: {current}/{total}")
    
    try:
        result_df = run_batch_inference_from_mlflow(
            model_name=model_name,
            version=version,
            data=df,
            llm_model=llm_model,
            progress_callback=progress_callback
        )
        
        print("\n" + "-" * 40)
        print("批量推理结果:")
        print("-" * 40)
        print(result_df.to_string(index=False))
        print("-" * 40)
        
        success_count = (result_df['_status'] == 'success').sum()
        print(f"\n✅ 批量推理完成: {success_count}/{len(result_df)} 成功")
        return True
        
    except Exception as e:
        print(f"\n❌ 批量推理失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def interactive_test(model_info: list, llm_model: str):
    """交互式测试"""
    print("\n" + "=" * 60)
    print("交互式测试")
    print("=" * 60)
    
    # 选择模型
    if len(model_info) == 1:
        selected = model_info[0]
        print(f"\n自动选择唯一模型: {selected['name']} v{selected['version']}")
    else:
        print("\n请选择要测试的模型 (输入序号):")
        for i, m in enumerate(model_info, 1):
            print(f"  {i}. {m['name']} v{m['version']}")
        
        try:
            choice = int(input("\n选择: ")) - 1
            selected = model_info[choice]
        except (ValueError, IndexError):
            print("无效选择，使用第一个模型")
            selected = model_info[0]
    
    model_name = selected['name']
    version = selected['version']
    input_fields = selected['input_fields']
    
    print(f"\n已选择: {model_name} v{version}")
    print(f"输入字段: {input_fields}")
    
    # 收集输入
    print("\n请输入测试数据:")
    input_data = {}
    for field in input_fields:
        value = input(f"  {field}: ")
        input_data[field] = value if value else f"测试{field}"
    
    # 执行推理
    test_single_inference(model_name, version, input_data, llm_model)
    
    # 询问是否继续
    again = input("\n是否继续测试? (y/n): ")
    if again.lower() == 'y':
        interactive_test(model_info, llm_model)


def run_preset_tests(model_info: list, llm_model: str):
    """运行预设测试"""
    if not model_info:
        print("没有可用模型")
        return
    
    # 使用第一个模型
    selected = model_info[0]
    model_name = selected['name']
    version = selected['version']
    input_fields = selected['input_fields']
    
    print(f"\n使用模型: {model_name} v{version}")
    print(f"输入字段: {input_fields}")
    
    # 预设测试数据
    test_cases = [
        {field: "程序员" for field in input_fields},
        {field: "猫咪" for field in input_fields},
        {field: "咖啡" for field in input_fields},
    ]
    
    # 单条推理测试
    print("\n" + "=" * 60)
    print("预设单条推理测试")
    print("=" * 60)
    
    for i, test_data in enumerate(test_cases, 1):
        print(f"\n--- 测试 {i} ---")
        test_single_inference(model_name, version, test_data, llm_model)
    
    # 批量推理测试
    test_batch_inference(model_name, version, test_cases, llm_model)


def main():
    print("\n" + "=" * 60)
    print("  MLflow 模型真实环境推理测试")
    print("=" * 60)
    
    # 检查前置条件
    result = check_prerequisites()
    if not result:
        print("\n❌ 前置条件检查失败，请确保:")
        print("   1. MLflow Docker 服务已启动")
        print("   2. 至少配置了一个 LLM API Key")
        return
    
    _, llm_model = result
    
    # 列出可用模型
    model_info = list_available_models()
    if not model_info:
        print("\n❌ 没有可用模型，请先编译并注册模型到 MLflow")
        return
    
    # 选择测试模式
    print("\n" + "=" * 60)
    print("选择测试模式")
    print("=" * 60)
    print("\n1. 运行预设测试 (自动)")
    print("2. 交互式测试 (手动输入)")
    print("3. 退出")
    
    try:
        mode = input("\n选择模式 (1/2/3): ")
    except EOFError:
        mode = "1"  # 非交互模式默认运行预设测试
    
    if mode == "1":
        run_preset_tests(model_info, llm_model)
    elif mode == "2":
        interactive_test(model_info, llm_model)
    else:
        print("\n退出测试")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
