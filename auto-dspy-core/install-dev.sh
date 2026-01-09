#!/bin/bash
# Auto-DSPy-Core 开发模式安装脚本

set -e

echo "=== 安装 Auto-DSPy-Core (开发模式) ==="

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "错误: uv 未安装"
    echo "请访问 https://docs.astral.sh/uv/getting-started/installation/ 安装 uv"
    exit 1
fi

# 安装包（开发模式）
echo "正在安装 auto-dspy-core[all]..."
uv pip install -e ".[all]"

echo ""
echo "✅ 安装完成！"
echo ""
echo "使用示例:"
echo "  python -c 'import autodspy; print(autodspy.__version__)'"
echo ""
