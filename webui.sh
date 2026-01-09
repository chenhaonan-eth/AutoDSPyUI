#!/bin/bash

# Exit on error
set -e

# DSPyUI Web 界面启动脚本

# 显示帮助信息
show_help() {
    echo "DSPyUI 启动脚本"
    echo ""
    echo "用法:"
    echo "  bash webui.sh                    # 启动 Gradio UI"
    echo "  bash webui.sh --lang zh_CN       # 使用中文启动"
    echo "  bash webui.sh --lang en_US       # 使用英文启动"
    echo "  bash webui.sh --api              # 同时启动 Gradio UI 和 API 服务"
    echo "  bash webui.sh --api-only         # 仅启动 API 服务"
    echo "  bash webui.sh --help             # 显示此帮助信息"
    echo ""
    echo "支持的语言:"
    echo "  zh_CN  中文"
    echo "  en_US  English"
    echo ""
    echo "API 服务选项:"
    echo "  --api          同时启动 Gradio UI 和 API 服务"
    echo "  --api-only     仅启动 API 服务 (不启动 Gradio UI)"
    echo "  --api-port     API 服务端口 (默认: 8000)"
    echo ""
    echo "MLflow 服务:"
    echo "  MLflow 现在通过 Docker Compose 运行"
    echo "  启动命令: cd docker/docker-compose && docker-compose up -d"
    echo "  停止命令: cd docker/docker-compose && docker-compose down"
    echo ""
    echo "环境变量:"
    echo "  DSPYUI_LANGUAGE     设置界面语言"
    echo "  MLFLOW_ENABLED      启用/禁用 MLflow 追踪 (true/false)"
    echo "  MLFLOW_TRACKING_URI MLflow 服务器地址 (默认: http://localhost:5000)"
    echo "  API_HOST            API 服务监听地址 (默认: 0.0.0.0)"
    echo "  API_PORT            API 服务监听端口 (默认: 8000)"
}

# 默认参数
START_API=false
API_ONLY=false
API_PORT_ARG=""

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
        --api)
            START_API=true
            echo "将同时启动 API 服务"
            shift
            ;;
        --api-only)
            API_ONLY=true
            START_API=true
            echo "仅启动 API 服务"
            shift
            ;;
        --api-port)
            if [ -n "$2" ]; then
                API_PORT_ARG="$2"
                echo "API 服务端口设置为: $2"
                shift 2
            else
                echo "错误: --api-port 参数需要指定端口号"
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
    echo "正在清理进程..."
    
    # 停止 API 服务器（如果由此脚本启动）
    if [ -n "$API_PID" ]; then
        echo "停止 API 服务器 (PID: $API_PID)..."
        kill -TERM "$API_PID" 2>/dev/null || true
        sleep 1
        if kill -0 "$API_PID" 2>/dev/null; then
            kill -KILL "$API_PID" 2>/dev/null || true
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

# 检查 Docker MLflow 服务是否运行
check_mlflow_docker() {
    echo "检查 MLflow Docker 服务..."
    
    # 获取 MLflow URI，默认为 localhost:5000
    MLFLOW_URI=${MLFLOW_TRACKING_URI:-"http://localhost:5000"}
    
    # 提取主机和端口
    MLFLOW_HOST=$(echo $MLFLOW_URI | sed -E 's|https?://([^:/]+).*|\1|')
    MLFLOW_PORT=$(echo $MLFLOW_URI | sed -E 's|https?://[^:]+:([0-9]+).*|\1|')
    
    # 如果没有提取到端口，使用默认值
    if [ "$MLFLOW_PORT" = "$MLFLOW_URI" ]; then
        MLFLOW_PORT=5000
    fi
    
    # 检查 MLflow 是否可访问
    if curl -s -f "$MLFLOW_URI/health" >/dev/null 2>&1; then
        echo "✅ MLflow 服务运行正常: $MLFLOW_URI"
        return 0
    else
        echo "⚠️  警告: 无法连接到 MLflow 服务 ($MLFLOW_URI)"
        echo ""
        echo "请确保 MLflow Docker 服务已启动:"
        echo "  cd docker/docker-compose"
        echo "  docker-compose up -d"
        echo ""
        echo "或者在 .env 中设置 MLFLOW_ENABLED=false 禁用 MLflow"
        echo ""
        
        # 询问用户是否继续
        read -p "是否继续启动 DSPyUI? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
        
        # 禁用 MLflow
        export MLFLOW_ENABLED=false
        echo "已禁用 MLflow 集成"
        return 1
    fi
}

# 启动 API 服务器的函数
start_api_server() {
    echo "启动 API 服务器..."
    
    # 确定 API 端口
    if [ -n "$API_PORT_ARG" ]; then
        API_PORT=$API_PORT_ARG
    else
        API_PORT=${API_PORT:-8000}
    fi
    
    # 检查端口是否被占用
    if lsof -Pi :$API_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  端口 $API_PORT 已被占用，尝试查找可用端口..."
        API_PORT=$(find_available_port $API_PORT)
    fi
    
    echo "将在端口 $API_PORT 上启动 API 服务器..."
    
    # API 日志文件
    API_LOG_FILE=${API_LOG_FILE:-"data/api.log"}
    mkdir -p "$(dirname "$API_LOG_FILE")"
    echo "API 日志文件: $API_LOG_FILE"
    
    # 在后台启动 API 服务器
    uv run python serve.py --port $API_PORT --log-level info > "$API_LOG_FILE" 2>&1 &
    API_PID=$!
    
    echo "API 服务器已启动 (PID: $API_PID)"
    echo "等待 API 服务器就绪..."
    
    # 等待服务器启动（最多等待 30 秒）
    for i in {1..30}; do
        if curl -s http://localhost:$API_PORT/health >/dev/null 2>&1; then
            echo "✅ API 服务器已就绪: http://localhost:$API_PORT"
            echo "   API 文档: http://localhost:$API_PORT/docs"
            export API_PORT_ACTUAL=$API_PORT
            return 0
        fi
        sleep 1
        echo -n "."
    done
    
    echo ""
    echo "⚠️  API 服务器启动可能需要更多时间，请稍后访问 http://localhost:$API_PORT"
    export API_PORT_ACTUAL=$API_PORT
    return 0
}

# Function to stop existing DSPy UI processes
stop_existing_processes() {
    echo "检查现有 DSPy UI 进程..."
    
    # 使用 pgrep 查找运行 main.py 的进程，避开当前脚本进程
    PIDS=$(pgrep -f "python.*main.py" | grep -v "^$$" || true)
    
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
}

# 如果只启动 API 服务器
if [ "$API_ONLY" = true ]; then
    # 检查 MLflow 服务（如果启用）
    if [ "${MLFLOW_ENABLED:-true}" = "true" ]; then
        check_mlflow_docker
    fi
    
    # 检查 serve.py 是否存在
    if [ ! -f serve.py ]; then
        echo "serve.py 文件不存在，请确保文件在当前目录中"
        exit 1
    fi
    
    # 确定 API 端口
    if [ -n "$API_PORT_ARG" ]; then
        API_PORT=$API_PORT_ARG
    else
        API_PORT=${API_PORT:-8000}
    fi
    
    echo ""
    echo "API 服务器正在启动..."
    echo "访问 http://localhost:$API_PORT 使用 API"
    echo "访问 http://localhost:$API_PORT/docs 查看 API 文档"
    if [ "${MLFLOW_ENABLED:-true}" = "true" ]; then
        echo "访问 ${MLFLOW_TRACKING_URI:-http://localhost:5000} 查看 MLflow UI"
    fi
    echo "按 Ctrl+C 停止"
    echo ""
    
    # 前台运行 API 服务器
    uv run python serve.py --port $API_PORT --log-level info
    exit 0
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

# 检查 MLflow 服务（如果启用）
if [ "${MLFLOW_ENABLED:-true}" = "true" ]; then
    check_mlflow_docker
fi

# Stop any existing DSPy UI processes
stop_existing_processes

# Check if the Python script exists
if [ ! -f main.py ]; then
    echo "main.py 文件不存在，请确保文件在当前目录中"
    exit 1
fi

# 如果需要同时启动 API 服务器
if [ "$START_API" = true ]; then
    # 检查 serve.py 是否存在
    if [ ! -f serve.py ]; then
        echo "serve.py 文件不存在，请确保文件在当前目录中"
        exit 1
    fi
    start_api_server
    echo "API 服务: http://localhost:$API_PORT_ACTUAL"
    echo "API 文档: http://localhost:$API_PORT_ACTUAL/docs"
fi

# Launch the Gradio app using uv run
echo "启动 DSPyUI..."
echo "当前语言设置: ${DSPYUI_LANGUAGE:-zh_CN}"

if [ "${MLFLOW_ENABLED:-true}" = "true" ]; then
    echo "MLflow UI: ${MLFLOW_TRACKING_URI:-http://localhost:5000}"
fi

echo "DSPyUI 启动中..."
uv run python main.py

# Note: The cleanup function will be called automatically when the script exits
