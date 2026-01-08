<!-- 一旦我所属的文件夹有所变化，请更新我 -->

# dspyui

DSPyUI 主包，提供 DSPy 程序编译、测试的核心功能、Gradio UI 和 REST API 服务。
包含配置、核心逻辑、工具函数、UI 组件和 API 服务五大模块。

## 文件清单

| 文件 | 地位 | 功能 |
|-----|------|------|
| `__init__.py` | 入口 | 包初始化，导出公共 API |
| `config.py` | 配置 | LLM 模型列表、默认配置和 API 服务配置 |
| `core/` | 核心 | 核心业务逻辑模块 |
| `utils/` | 辅助 | 工具函数模块 |
| `ui/` | 界面 | Gradio UI 组件模块 |
| `api/` | API | FastAPI REST 服务模块 |
