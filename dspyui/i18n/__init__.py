"""
国际化翻译模块

INPUT:  dspyui.config (语言配置)
OUTPUT: t() 翻译函数, set_language() 语言切换函数
POS:    全局翻译服务，为所有 UI 模块提供文本翻译

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

from typing import Dict, Any
from dspyui.config import DEFAULT_LANGUAGE


# 翻译字典缓存
_translations: Dict[str, Dict[str, Any]] = {}
# 当前语言
_current_language: str = DEFAULT_LANGUAGE


def _load_translations(lang: str) -> Dict[str, Any]:
    """
    加载指定语言的翻译字典。
    
    Args:
        lang: 语言代码 (zh_CN, en_US)
        
    Returns:
        翻译字典
    """
    if lang in _translations:
        return _translations[lang]
    
    try:
        if lang == "zh_CN":
            from .zh_CN import TRANSLATIONS
        elif lang == "en_US":
            from .en_US import TRANSLATIONS
        else:
            # 默认使用英文
            from .en_US import TRANSLATIONS
        
        _translations[lang] = TRANSLATIONS
        return TRANSLATIONS
    except ImportError:
        # 如果翻译文件不存在，返回空字典
        return {}


def set_language(lang: str) -> None:
    """
    设置当前语言。
    
    Args:
        lang: 语言代码 (zh_CN, en_US)
    """
    global _current_language
    _current_language = lang


def get_current_language() -> str:
    """
    获取当前语言。
    
    Returns:
        当前语言代码
    """
    return _current_language


def t(key: str, lang: str = None) -> str:
    """
    翻译函数。
    
    Args:
        key: 翻译键，支持点分隔的嵌套键 (如 "compile.buttons.add_input")
        lang: 语言代码，默认使用当前设置的语言
        
    Returns:
        翻译后的文本，如果找不到则返回原键
    """
    if lang is None:
        lang = _current_language
        
    translations = _load_translations(lang)
    
    # 支持嵌套键访问
    keys = key.split('.')
    value = translations
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            # 找不到翻译，返回原键
            return key
    
    return str(value) if value is not None else key