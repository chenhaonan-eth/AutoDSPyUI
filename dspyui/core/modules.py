"""
DSPy Module 创建模块

INPUT:  dspy_module 类型, CustomSignature 类, hint (可选)
OUTPUT: create_dspy_module() 函数，返回 DSPy Module 实例
POS:    核心模块，被 compiler 和 runner 调用创建可执行模块

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

from typing import Type, Optional

import dspy


def create_dspy_module(
    dspy_module: str,
    CustomSignature: Type[dspy.Signature],
    hint: Optional[str] = None
) -> dspy.Module:
    """
    创建 DSPy Module 实例。

    根据指定的模块类型和 Signature 创建对应的 DSPy Module。

    Args:
        dspy_module: 模块类型，支持 "Predict", "ChainOfThought", "ChainOfThoughtWithHint"
        CustomSignature: 自定义的 DSPy Signature 类
        hint: 可选的提示信息，仅在 ChainOfThoughtWithHint 时使用

    Returns:
        创建好的 DSPy Module 实例

    Raises:
        ValueError: 当指定不支持的模块类型时

    Example:
        >>> module = create_dspy_module("Predict", MySignature)
        >>> result = module(input_field="value")
    """
    if dspy_module == "Predict":
        class CustomPredictModule(dspy.Module):
            """基于 Predict 的自定义模块"""
            
            def __init__(self):
                super().__init__()
                self.predictor = dspy.Predict(CustomSignature)
            
            def forward(self, **kwargs):
                result = self.predictor(**kwargs)
                return result
        
        return CustomPredictModule()
    
    elif dspy_module == "ChainOfThought":
        class CustomChainOfThoughtModule(dspy.Module):
            """基于 ChainOfThought 的自定义模块"""
            
            def __init__(self):
                super().__init__()
                self.cot = dspy.ChainOfThought(CustomSignature)
            
            def forward(self, **kwargs):
                return self.cot(**kwargs)
        
        return CustomChainOfThoughtModule()
    
    elif dspy_module == "ChainOfThoughtWithHint":
        class CustomChainOfThoughtWithHintModule(dspy.Module):
            """基于 ChainOfThought 并带有提示的自定义模块"""
            
            def __init__(self):
                super().__init__()
                self.cot_with_hint = dspy.ChainOfThought(CustomSignature)
                self.hint = hint
            
            def forward(self, **kwargs):
                # 将提示注入 kwargs
                kwargs['hint'] = self.hint
                return self.cot_with_hint(**kwargs)
        
        return CustomChainOfThoughtWithHintModule()
    
    else:
        raise ValueError(f"Unsupported DSPy module: {dspy_module}")
