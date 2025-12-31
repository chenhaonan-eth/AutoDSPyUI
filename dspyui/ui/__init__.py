"""
UI 模块入口

INPUT:  styles, components, tabs, app 子模块
OUTPUT: create_app, CUSTOM_CSS 等
POS:    UI 层入口，被 main.py 调用

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

from dspyui.ui.styles import CUSTOM_CSS
from dspyui.ui.components import add_field, remove_last_field, load_csv
from dspyui.ui.app import create_app, demo

__all__ = [
    "CUSTOM_CSS",
    "add_field",
    "remove_last_field",
    "load_csv",
    "create_app",
    "demo",
]
