# DSPyUI

A Gradio user interface for DSPy - DSPy程序的可视化编译与测试平台。

> [!CAUTION]
> **文档同步要求**：任何功能、架构、写法更新，必须在工作结束后更新相关目录的子文档！

## Quick Start

### 基本启动

```bash
# 使用 uv (推荐)
bash webui.sh

# 或手动执行
uv sync
uv run python main.py
```

### 语言选择

DSPyUI 支持中英文界面，提供多种语言切换方式：

#### 方式 1：启动时指定语言（推荐）

```bash
# 中文界面（默认）
bash webui.sh --lang zh_CN

# 英文界面
bash webui.sh --lang en_US

# 查看帮助
bash webui.sh --help
```

#### 方式 2：环境变量

```bash
# 设置为英文
export DSPYUI_LANGUAGE=en_US
bash webui.sh

# 设置为中文
export DSPYUI_LANGUAGE=zh_CN
bash webui.sh
```

#### 方式 3：界面切换

- 在运行的应用中使用右上角的语言选择器
- 切换后按提示重启应用即可生效

### 支持的语言

- `zh_CN` - 中文（简体）
- `en_US` - English

## 项目结构

```
DSPyUI/
├── dspyui/              # 主包
│   ├── config.py        # 配置常量（含国际化配置）
│   ├── core/            # 核心业务逻辑
│   ├── utils/           # 工具函数
│   ├── i18n/            # 国际化翻译模块
│   └── ui/              # Gradio UI 组件（已适配中文）
├── main.py              # 应用入口
├── datasets/            # 数据集
├── example_data/        # 示例数据
├── programs/            # 编译后的程序
└── prompts/             # 提示词
```

## 功能

- **Compile Program**: 编译 DSPy 程序（中文界面）
- **Browse Prompts**: 浏览已保存的提示词（中文界面）
- **Test Program**: 测试编译后的程序
- **多语言支持**: 支持中英文界面切换，提供完整的国际化体验

## 特性

- 🌐 **多语言界面**: 支持中文和英文，可随时切换
- 🎯 **简洁易用**: 直观的 Gradio 界面，操作简单
- 🔧 **灵活配置**: 支持多种语言切换方式
- 📊 **数据管理**: 完整的数据导入导出功能

---

<img width="1561" alt="Screenshot 2025-05-23 at 09 53 48" src="https://github.com/user-attachments/assets/df95d7ee-c605-47cc-a389-19cdd67f7a02" />
<img width="1561" alt="Screenshot 2025-05-23 at 09 54 33" src="https://github.com/user-attachments/assets/e3cea6f3-68eb-4c48-bb6d-c5ef01eba827" />
<img width="1561" alt="Screenshot 2025-05-23 at 09 53 58" src="https://github.com/user-attachments/assets/ea9d73bb-027e-4f3f-ae0d-b27fedaaf61d" />
<img width="1561" alt="Screenshot 2025-05-23 at 09 54 08" src="https://github.com/user-attachments/assets/f34858ca-14d8-4091-aa78-05ff8150defe" />
