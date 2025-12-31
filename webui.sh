#!/bin/bash

# Exit on error
set -e

# DSPyUI Web 界面启动脚本 - 支持语言选择参数

# 显示帮助信息
show_help() {
    echo "DSPyUI 启动脚本"
    echo ""
    echo "用法:"
    echo "  bash webui.sh                    # 使用默认语言"
    echo "  bash webui.sh --lang zh_CN       # 使用中文"
    echo "  bash webui.sh --lang en_US       # 使用英文"
    echo "  bash webui.sh --help             # 显示此帮助信息"
    echo ""
    echo "支持的语言:"
    echo "  zh_CN  中文"
    echo "  en_US  English"
    echo ""
    echo "环境变量:"
    echo "  DSPYUI_LANGUAGE  设置界面语言"
}

# 处理命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --lang)
            if [ -n "$2" ]; then
                export DSPYUI_LANGUAGE="$2"
                echo "设置语言为: $2"
                shift 2
            else
                echo "错误: --lang 参数需要指定语言代码"
                show_help
                exit 1
            fi
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# Function to cleanup and exit
cleanup() {
    echo "Cleaning up..."
    echo "Exited DSPy UI."
    exit
}

# Set up trap to call cleanup function on script exit
trap cleanup EXIT

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Reload shell to get uv in PATH
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Check for .env file and source it if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    set -a
    source .env
    set +a
else
    echo "No .env file found. Make sure to set any necessary environment variables manually."
fi

# Sync dependencies using uv
echo "Syncing dependencies with uv..."
uv sync

# Function to stop existing DSPy UI processes
stop_existing_processes() {
    echo "Checking for existing DSPy UI processes..."
    
    # Find processes running main.py or containing "DSPy UI" or "gradio"
    PIDS=$(ps aux | grep -E "(main\.py|DSPy UI|gradio.*main\.py)" | grep -v grep | grep -v "$$" | awk '{print $2}')
    
    if [ -n "$PIDS" ]; then
        echo "Found existing DSPy UI processes. Stopping them..."
        for PID in $PIDS; do
            echo "Stopping process $PID..."
            kill -TERM "$PID" 2>/dev/null || true
            # Wait a moment for graceful shutdown
            sleep 1
            # Force kill if still running
            if kill -0 "$PID" 2>/dev/null; then
                echo "Force stopping process $PID..."
                kill -KILL "$PID" 2>/dev/null || true
            fi
        done
        echo "Existing processes stopped."
        # Wait a moment before starting new process
        sleep 2
    else
        echo "No existing DSPy UI processes found."
    fi
}

# Stop any existing DSPy UI processes
stop_existing_processes

# Check if the Python script exists
if [ ! -f main.py ]; then
    echo "main.py not found. Please make sure the file exists in the current directory."
    exit 1
fi

# Launch the Gradio app using uv run
echo "Launching DSPy UI..."
echo "当前语言设置: ${DSPYUI_LANGUAGE:-zh_CN}"
uv run python main.py

# Note: The cleanup function will be called automatically when the script exits