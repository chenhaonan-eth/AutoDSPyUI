<!-- 一旦我所属的文件夹有所变化，请更新我 -->

# tabs

Gradio Tab 页面模块。
包含编译程序、测试模型、浏览提示词三个主要功能页面。

## 文件清单

| 文件 | 地位 | 功能 |
|-----|------|------|
| `__init__.py` | 入口 | 导出各 Tab 创建函数 |
| `compile_tab.py` | 核心 | Compile Program Tab |
| `test_tab.py` | 核心 | Test Model Tab - 从 MLflow 加载模型进行推理测试 |
| `browse_tab.py` | 核心 | Browse Prompts Tab |

