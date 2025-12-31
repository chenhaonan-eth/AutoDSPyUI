# DSPyUI

> [中文文档](README_zh.md)

A Gradio-based visual interface for DSPy - compile, test, and manage DSPy programs with ease.

## ✨ Features

- 🎯 **Visual Compilation**: Compile DSPy programs through an intuitive UI
- 📝 **Prompt Browser**: Browse and manage saved prompts
- 🧪 **Program Testing**: Test compiled programs with custom inputs
- 🌐 **Multi-language**: Full support for English and Chinese interfaces
- 🔧 **Flexible LLM Support**: OpenAI, Anthropic, Groq, Google Gemini models
- 📊 **Data Management**: Import/export datasets easily

## 🚀 Quick Start

### Prerequisites

- Python >= 3.11
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/DSPyUI.git
cd DSPyUI

# Copy environment file and add your API keys
cp .env.example .env
```

### Running

```bash
# Using uv (recommended)
bash webui.sh

# Or manually
uv sync
uv run python main.py
```

## 🌍 Language Selection

DSPyUI supports both English and Chinese interfaces:

### Option 1: Command Line (Recommended)

```bash
# English interface
bash webui.sh --lang en_US

# Chinese interface (default)
bash webui.sh --lang zh_CN
```

### Option 2: Environment Variable

```bash
export DSPYUI_LANGUAGE=en_US
bash webui.sh
```

### Option 3: In-App Switcher

Use the language selector in the top-right corner of the running application.

## 🤖 Supported Models

| Provider | Models |
|----------|--------|
| OpenAI | gpt-3.5-turbo, gpt-4, gpt-4o, gpt-4o-mini |
| Anthropic | claude-3-5-sonnet, claude-3-opus |
| Groq | mixtral-8x7b, llama3-70b, llama3-8b, gemma2-9b |
| Google | gemini-1.5-flash, gemini-1.5-pro |

## 📁 Project Structure

```
DSPyUI/
├── dspyui/              # Main package
│   ├── config.py        # Configuration (LLM options, i18n)
│   ├── core/            # Core business logic
│   ├── utils/           # Utility functions
│   ├── i18n/            # Internationalization
│   └── ui/              # Gradio UI components
├── main.py              # Application entry point
├── datasets/            # User datasets
├── example_data/        # Example data files
├── programs/            # Compiled programs
└── prompts/             # Saved prompts
```

## 📸 Screenshots

<img width="1561" alt="Compile Tab" src="https://github.com/user-attachments/assets/df95d7ee-c605-47cc-a389-19cdd67f7a02" />
<img width="1561" alt="Browse Prompts" src="https://github.com/user-attachments/assets/e3cea6f3-68eb-4c48-bb6d-c5ef01eba827" />
<img width="1561" alt="Test Program" src="https://github.com/user-attachments/assets/ea9d73bb-027e-4f3f-ae0d-b27fedaaf61d" />
<img width="1561" alt="Settings" src="https://github.com/user-attachments/assets/f34858ca-14d8-4091-aa78-05ff8150defe" />

## 📄 License

MIT License
