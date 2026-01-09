# DSPyUI

> [English](README.md)

基于 Gradio 的 DSPy 可视化界面 - 轻松编译、测试和管理 DSPy 程序。

## ✨ 功能特性

- 🎯 **可视化编译**: 通过直观的 UI 编译 DSPy 程序
- 📝 **提示词浏览**: 浏览和管理已保存的提示词
- 🧪 **程序测试**: 使用自定义输入测试编译后的程序
- 🌐 **多语言支持**: 完整支持中英文界面
- 🔧 **灵活的 LLM 支持**: OpenAI、Anthropic、Groq、Google Gemini 模型
- 📊 **数据管理**: 便捷的数据集导入导出功能
- 📈 **MLflow 集成**: 实验追踪、模型注册和程序生命周期管理

## 🚀 快速开始

### 环境要求

- Python >= 3.11
- [uv](https://github.com/astral-sh/uv)（推荐）或 pip

### 安装

```bash
# 克隆仓库
git clone https://github.com/your-username/DSPyUI.git
cd DSPyUI

# 复制环境配置文件并添加 API 密钥
cp .env.example .env
```

### 运行

```bash
# 1. 启动 MLflow Docker 服务（首次使用）
cd docker/docker-compose
docker-compose up -d
cd ../..

# 2. 启动 DSPyUI
# 基础启动（中文界面）
bash webui.sh

# 英文界面
bash webui.sh --lang en_US

# 同时启动 API 服务
bash webui.sh --api

# 仅启动 API 服务
bash webui.sh --api-only

# 或手动执行（不推荐）
uv sync
uv run python main.py
```

### MLflow 集成

DSPyUI 使用 Docker Compose 运行 MLflow 服务（包含 PostgreSQL + MinIO + MLflow Server）：

```bash
# 启动 MLflow 服务
cd docker/docker-compose
docker-compose up -d

# 查看服务状态
docker-compose ps

# 停止服务
docker-compose down

# 停止并删除所有数据
docker-compose down -v
```

访问服务：
- **MLflow UI**: `http://localhost:5000` - 查看实验结果、比较运行记录和管理模型版本
- **MinIO 控制台**: `http://localhost:9001` - 查看存储的模型工件（用户名: `minio`, 密码: `minio123`）

**MLflow 功能特性：**
- 📊 自动追踪编译参数和评估指标
- 🏷️ 模型注册和版本管理
- 📈 实验比较和可视化
- 🔍 详细的 LLM 调用追踪
- 💾 PostgreSQL 存储元数据
- 📦 MinIO (S3 兼容) 存储模型工件

**配置 MLflow**:

在 `.env` 文件中：

```bash
# 启用 MLflow
MLFLOW_ENABLED=true
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=dspyui-experiments

# 禁用 MLflow（如果不需要）
MLFLOW_ENABLED=false
```

## 🌍 语言选择

DSPyUI 支持中英文界面切换：

### 方式 1：命令行参数（推荐）

```bash
# 中文界面（默认）
bash webui.sh --lang zh_CN

# 英文界面
bash webui.sh --lang en_US

# 同时启动 API 服务
bash webui.sh --api

# 仅启动 API 服务
bash webui.sh --api-only
```

### 方式 2：环境变量

```bash
export DSPYUI_LANGUAGE=zh_CN
bash webui.sh
```

### 方式 3：界面内切换

在运行的应用中使用右上角的语言选择器。

## 🤖 支持的模型

| 提供商 | 模型 |
|--------|------|
| OpenAI | gpt-3.5-turbo, gpt-4, gpt-4o, gpt-4o-mini |
| Anthropic | claude-3-5-sonnet, claude-3-opus |
| Groq | mixtral-8x7b, llama3-70b, llama3-8b, gemma2-9b |
| Google | gemini-1.5-flash, gemini-1.5-pro |

## 📁 项目结构

```
DSPyUI/
├── dspyui/              # 主包
│   ├── config.py        # 配置（LLM 选项、国际化）
│   ├── core/            # 核心业务逻辑
│   ├── utils/           # 工具函数
│   ├── i18n/            # 国际化翻译
│   └── ui/              # Gradio UI 组件
├── main.py              # 应用入口
├── datasets/            # 用户数据集
├── example_data/        # 示例数据
├── programs/            # 编译后的程序
└── prompts/             # 保存的提示词
```

## 📸 截图

<img width="1561" alt="编译标签页" src="https://github.com/user-attachments/assets/df95d7ee-c605-47cc-a389-19cdd67f7a02" />
<img width="1561" alt="浏览提示词" src="https://github.com/user-attachments/assets/e3cea6f3-68eb-4c48-bb6d-c5ef01eba827" />
<img width="1561" alt="测试程序" src="https://github.com/user-attachments/assets/ea9d73bb-027e-4f3f-ae0d-b27fedaaf61d" />
<img width="1561" alt="设置" src="https://github.com/user-attachments/assets/f34858ca-14d8-4091-aa78-05ff8150defe" />

## 📄 许可证

MIT License
