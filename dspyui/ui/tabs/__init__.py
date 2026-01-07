"""
Tabs 模块入口

INPUT:  compile_tab, browse_tab, test_tab 子模块
OUTPUT: create_compile_tab, create_browse_tab, create_test_tab 等
POS:    Tab 页面入口，被 app.py 调用

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

from dspyui.ui.tabs.compile_tab import create_compile_tab
from dspyui.ui.tabs.browse_tab import create_browse_tab
from dspyui.ui.tabs.test_tab import create_test_tab

__all__ = [
    "create_compile_tab",
    "create_browse_tab",
    "create_test_tab",
]

