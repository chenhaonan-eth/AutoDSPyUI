"""
DSPy Signature 创建模块单元测试

INPUT:  autodspy.dspy_core.signatures 模块
OUTPUT: 验证 Signature 创建功能的测试用例
POS:    确保 DSPy Signature 定义正确性
"""

import pytest

from autodspy.dspy_core.signatures import create_custom_signature


@pytest.mark.unit
class TestCreateCustomSignature:
    """测试自定义 Signature 创建功能"""
    
    def test_create_simple_signature(self):
        """创建简单 Signature 应成功"""
        result = create_custom_signature(
            input_fields=["topic"],
            output_fields=["joke"],
            instructions="Generate a funny joke",
            input_descs=["The topic to joke about"],
            output_descs=["The generated joke"]
        )
        
        assert result is not None
        # 验证是 dspy.Signature 的子类
        import dspy
        assert issubclass(result, dspy.Signature)
    
    def test_create_signature_with_multiple_inputs(self):
        """创建多输入 Signature 应成功"""
        result = create_custom_signature(
            input_fields=["topic", "style", "length"],
            output_fields=["joke"],
            instructions="Generate a joke",
            input_descs=["Topic", "Style", "Length"],
            output_descs=["The joke"]
        )
        
        assert result is not None
    
    def test_create_signature_with_multiple_outputs(self):
        """创建多输出 Signature 应成功"""
        result = create_custom_signature(
            input_fields=["topic"],
            output_fields=["joke", "explanation", "rating"],
            instructions="Generate and explain a joke",
            input_descs=["Topic"],
            output_descs=["Joke", "Explanation", "Rating"]
        )
        
        assert result is not None
    
    def test_create_signature_with_empty_descs(self):
        """空描述列表应成功（使用默认描述）"""
        result = create_custom_signature(
            input_fields=["topic"],
            output_fields=["joke"],
            instructions="Generate a joke",
            input_descs=[],
            output_descs=[]
        )
        
        assert result is not None
    
    def test_create_signature_with_partial_descs(self):
        """部分描述应成功"""
        result = create_custom_signature(
            input_fields=["topic", "style"],
            output_fields=["joke"],
            instructions="Generate a joke",
            input_descs=["The topic"],  # 只有一个描述
            output_descs=["The joke"]
        )
        
        assert result is not None
    
    def test_create_signature_docstring(self):
        """Signature 应包含正确的 docstring"""
        instructions = "Generate a funny joke about the given topic"
        result = create_custom_signature(
            input_fields=["topic"],
            output_fields=["joke"],
            instructions=instructions,
            input_descs=["Topic"],
            output_descs=["Joke"]
        )
        
        assert result is not None
        assert instructions in result.__doc__
