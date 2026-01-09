#!/bin/bash
# 测试运行脚本
#
# INPUT:  pytest 配置和测试文件
# OUTPUT: 测试结果报告
# POS:    测试执行入口

set -e

echo "=========================================="
echo "Auto-DSPy-Core 测试套件"
echo "=========================================="
echo ""

# 检查是否在正确的目录
if [ ! -f "pyproject.toml" ]; then
    echo "错误: 请在 auto-dspy-core 目录下运行此脚本"
    exit 1
fi

# 解析命令行参数
TEST_PATH="${1:-tests/}"
MARKERS="${2:-}"
VERBOSE="${3:--v}"

echo "测试路径: $TEST_PATH"
if [ -n "$MARKERS" ]; then
    echo "测试标记: $MARKERS"
fi
echo ""

# 运行测试
if [ -n "$MARKERS" ]; then
    echo "运行带标记的测试: $MARKERS"
    uv run pytest "$TEST_PATH" -m "$MARKERS" "$VERBOSE"
else
    echo "运行所有测试"
    uv run pytest "$TEST_PATH" "$VERBOSE"
fi

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
