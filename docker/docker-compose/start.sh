#!/bin/bash

# MLflow Docker 服务快速启动脚本

set -e

echo "========================================="
echo "  DSPyUI MLflow Docker 服务管理"
echo "========================================="
echo ""

# 检查 docker 和 docker-compose 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker 未安装"
    echo "请访问 https://docs.docker.com/get-docker/ 安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误: Docker Compose 未安装"
    echo "请访问 https://docs.docker.com/compose/install/ 安装 Docker Compose"
    exit 1
fi

# 显示帮助信息
show_help() {
    echo "用法: bash start.sh [命令]"
    echo ""
    echo "命令:"
    echo "  start    启动所有服务（默认）"
    echo "  stop     停止所有服务"
    echo "  restart  重启所有服务"
    echo "  status   查看服务状态"
    echo "  logs     查看服务日志"
    echo "  clean    停止服务并删除所有数据"
    echo "  help     显示此帮助信息"
    echo ""
}

# 启动服务
start_services() {
    echo "🚀 启动 MLflow Docker 服务..."
    echo ""
    
    # 检查 .env 文件
    if [ ! -f .env ]; then
        echo "⚠️  未找到 .env 文件，使用默认配置"
        cp .env.dev.example .env
    fi
    
    # 启动服务
    docker-compose up -d
    
    echo ""
    echo "⏳ 等待服务启动..."
    sleep 5
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        echo ""
        echo "✅ 服务启动成功！"
        echo ""
        echo "访问地址:"
        echo "  - MLflow UI:     http://localhost:5000"
        echo "  - MinIO 控制台:  http://localhost:9001"
        echo "    用户名: minio"
        echo "    密码: minio123"
        echo ""
        echo "查看日志: docker-compose logs -f"
        echo "停止服务: bash start.sh stop"
    else
        echo ""
        echo "❌ 服务启动失败，请查看日志:"
        echo "  docker-compose logs"
    fi
}

# 停止服务
stop_services() {
    echo "🛑 停止 MLflow Docker 服务..."
    docker-compose down
    echo "✅ 服务已停止"
}

# 重启服务
restart_services() {
    echo "🔄 重启 MLflow Docker 服务..."
    docker-compose restart
    echo "✅ 服务已重启"
}

# 查看状态
show_status() {
    echo "📊 服务状态:"
    echo ""
    docker-compose ps
}

# 查看日志
show_logs() {
    echo "📋 服务日志 (按 Ctrl+C 退出):"
    echo ""
    docker-compose logs -f
}

# 清理数据
clean_data() {
    echo "⚠️  警告: 此操作将删除所有 MLflow 数据（实验记录、模型等）"
    read -p "确认删除? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        echo "🗑️  停止服务并删除数据..."
        docker-compose down -v
        echo "✅ 数据已清理"
    else
        echo "❌ 操作已取消"
    fi
}

# 处理命令
case "${1:-start}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    clean)
        clean_data
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ 未知命令: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
