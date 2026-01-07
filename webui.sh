#!/bin/bash

# Exit on error
set -e

# DSPyUI Web 界面启动脚本 - 支持语言选择和 MLflow 服务器

# 显示帮助信息
show_help() {
    echo "DSPyUI 启动脚本"
    echo ""
    echo "用法:"
    echo "  bash webui.sh                    # 默认启动 (含 MLflow)"
    echo "  bash webui.sh --lang zh_CN       # 使用中文启动"
    echo "  bash webui.sh --lang en_US       # 使用英文启动"
    echo "  bash webui.sh --no-mlflow        # 不启动 MLflow 服务器"
    echo "  bash webui.sh --mlflow-only      # 仅启动 MLflow 服务器"
    echo "  bash webui.sh --help             # 显示此帮助信息"
    echo ""
    echo "支持的语言:"
    echo "  zh_CN  中文"
    echo "  en_US  English"
    echo ""
    echo "MLflow 选项:"
    echo "  --no-mlflow    不启动 MLflow 服务器 (默认会启动)"
    echo "  --mlflow-only  仅启动 MLflow 服务器"
    echo ""
    echo "环境变量:"
    echo "  DSPYUI_LANGUAGE     设置界面语言"
    echo "  MLFLOW_ENABLED      启用/禁用 MLflow 追踪 (true/false)"
    echo "  MLFLOW_TRACKING_URI MLflow 服务器地址"
}

# 默认参数
START_MLFLOW=true
MLFLOW_ONLY=false

# Check for .env file and source it if it exists
if [ -f .env ]; then
    echo "从 .env 文件加载环境变量..."
    set -a
    source .env
    set +a
else
    echo "未找到 .env 文件，请确保手动设置必要的环境变量"
fi

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
        --no-mlflow)
            START_MLFLOW=false
            export MLFLOW_ENABLED=false
            echo "将不启动 MLflow 服务器"
            shift
            ;;
        --mlflow-only)
            MLFLOW_ONLY=true
            echo "仅启动 MLflow 服务器"
            shift
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
    echo "正在清理进程..."
    
    # 停止 MLflow 服务器（如果由此脚本启动）
    if [ -n "$MLFLOW_PID" ]; then
        echo "停止 MLflow 服务器 (PID: $MLFLOW_PID)..."
        kill -TERM "$MLFLOW_PID" 2>/dev/null || true
        
        # 额外确保杀掉该端口上的所有 mlflow 相关进程（防止 worker 残留）
        if [ -n "$MLFLOW_PORT_ACTUAL" ]; then
             echo "清理端口 $MLFLOW_PORT_ACTUAL 上的残留进程..."
             pkill -f "mlflow server.*$MLFLOW_PORT_ACTUAL" 2>/dev/null || true
        fi

        sleep 1
        if kill -0 "$MLFLOW_PID" 2>/dev/null; then
            kill -KILL "$MLFLOW_PID" 2>/dev/null || true
        fi
    fi
    
    echo "已退出 DSPyUI"
    exit
}

# Set up trap to call cleanup function on script exit
trap cleanup EXIT

# 查找可用端口函数
find_available_port() {
    local port=$1
    while lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; do
        ((port++))
    done
    echo $port
}

# 启动 MLflow 服务器的函数
start_mlflow_server() {
    echo "检查 MLflow 服务器端口..."
    
    # 查找起始端口 5000 的可用端口
    MLFLOW_PORT=$(find_available_port 5000)
    
    echo "将在端口 $MLFLOW_PORT 上启动 MLflow 服务器..."
    
    # 在后台启动 MLflow 服务器
    # 使用环境变量配置存储路径，如果未设置则使用默认值
    BACKEND_STORE_URI=${MLFLOW_BACKEND_STORE_URI:-"sqlite:///data/mlflow.db"}
    ARTIFACT_ROOT=${MLFLOW_ARTIFACT_ROOT:-"./mlartifacts"}
    
    echo "使用后端存储: $BACKEND_STORE_URI"
    echo "使用工件根目录: $ARTIFACT_ROOT"

    # 日志文件路径，默认放在 data 目录
    MLFLOW_LOG_FILE=${MLFLOW_LOG_FILE:-"data/mlflow.log"}
    mkdir -p "$(dirname "$MLFLOW_LOG_FILE")"
    echo "MLflow 日志文件: $MLFLOW_LOG_FILE"

    uv run mlflow server \
        --host 0.0.0.0 \
        --port $MLFLOW_PORT \
        --backend-store-uri "$BACKEND_STORE_URI" \
        --default-artifact-root "$ARTIFACT_ROOT" > "$MLFLOW_LOG_FILE" 2>&1 &
    MLFLOW_PID=$!
    
    echo "MLflow 服务器已启动 (PID: $MLFLOW_PID)"
    echo "等待 MLflow 服务器就绪..."
    
    # 等待服务器启动（最多等待 30 秒）
    for i in {1..30}; do
        if curl -s http://localhost:$MLFLOW_PORT/health >/dev/null 2>&1; then
            echo "✅ MLflow 服务器已就绪: http://localhost:$MLFLOW_PORT"
            # 导出端口供后续使用
            export MLFLOW_PORT_ACTUAL=$MLFLOW_PORT
            return 0
        fi
        sleep 1
        echo -n "."
    done
    
    echo ""
    echo "⚠️  MLflow 服务器启动可能需要更多时间，请稍后访问 http://localhost:$MLFLOW_PORT"
    export MLFLOW_PORT_ACTUAL=$MLFLOW_PORT
    return 0
}

# 如果只启动 MLflow 服务器
if [ "$MLFLOW_ONLY" = true ]; then
    start_mlflow_server
    echo ""
    echo "MLflow 服务器正在运行，按 Ctrl+C 停止"
    echo "访问 http://localhost:$MLFLOW_PORT_ACTUAL 查看 MLflow UI"
    
    # 等待用户中断
    while true; do
        sleep 1
    done
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv 未安装，正在安装 uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Reload shell to get uv in PATH
    export PATH="$HOME/.cargo/bin:$PATH"
fi


# Sync dependencies using uv
echo "使用 uv 同步依赖..."
uv sync

# Function to stop existing DSPy UI processes
stop_existing_processes() {
    echo "检查现有 DSPy UI 进程..."
    
    # 使用 pgrep 查找运行 main.py 的进程，避开当前脚本进程
    PIDS=$(pgrep -f "python.*main.py" | grep -v "^$$$" || true)
    
    if [ -n "$PIDS" ]; then
        echo "发现现有 DSPy UI 进程，正在停止..."
        for PID in $PIDS; do
            echo "停止进程 $PID..."
            kill -TERM "$PID" 2>/dev/null || true
            # Wait a moment for graceful shutdown
            sleep 1
            # Force kill if still running
            if kill -0 "$PID" 2>/dev/null; then
                echo "强制停止进程 $PID..."
                kill -KILL "$PID" 2>/dev/null || true
            fi
        done
        echo "现有进程已停止"
        # Wait a moment before starting new process
        sleep 2
    else
        echo "未发现现有 DSPy UI 进程"
    fi

    # 检查是否有残留的 MLflow 进程（特别是如果我们要启动一个新的）
    if [ "$START_MLFLOW" = true ] || [ "$MLFLOW_ONLY" = true ]; then
        echo "检查现有 MLflow 进程..."
        # 查找 mlflow server 进程
        MLFLOW_PIDS=$(pgrep -f "mlflow server" | grep -v "^$$$" || true)
        if [ -n "$MLFLOW_PIDS" ]; then
            echo "发现现有 MLflow 进程，正在停止以避免冲突..."
            for PID in $MLFLOW_PIDS; do
                kill -TERM "$PID" 2>/dev/null || true
            done
            sleep 1
        fi
    fi
}

# 如果需要启动 MLflow 服务器
if [ "$START_MLFLOW" = true ]; then
    start_mlflow_server
    # 强制启用 MLflow 追踪，覆盖 .env 中的设置
    export MLFLOW_ENABLED=true
    export MLFLOW_TRACKING_URI="http://localhost:$MLFLOW_PORT_ACTUAL"
    export MLFLOW_UI_BASE_URL="http://localhost:$MLFLOW_PORT_ACTUAL"
    echo "MLflow Tracking URI set to: $MLFLOW_TRACKING_URI"
    echo ""
fi

# Stop any existing DSPy UI processes
stop_existing_processes

# Check if the Python script exists
if [ ! -f main.py ]; then
    echo "main.py 文件不存在，请确保文件在当前目录中"
    exit 1
fi

# Launch the Gradio app using uv run
echo "启动 DSPyUI..."
echo "当前语言设置: ${DSPYUI_LANGUAGE:-zh_CN}"

if [ "$START_MLFLOW" = true ]; then
    echo "MLflow UI: http://localhost:$MLFLOW_PORT_ACTUAL"
fi

echo "DSPyUI 启动中..."
uv run python main.py

# Note: The cleanup function will be called automatically when the script exits