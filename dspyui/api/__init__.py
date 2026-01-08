"""
DSPyUI API 模块

INPUT:  FastAPI, dspyui.core 模块
OUTPUT: FastAPI 应用实例, API 路由
POS:    API 服务层，提供 REST 接口供外部调用

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

from dspyui.api.app import create_app

__all__ = ["create_app"]
