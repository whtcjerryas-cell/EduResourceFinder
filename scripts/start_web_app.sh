#!/bin/bash
# 启动 Web 应用脚本

echo "=========================================="
echo "🚀 启动教育视频搜索系统 V2"
echo "=========================================="

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️  警告: Flask 未安装，正在安装..."
    pip3 install -r requirements_web.txt
fi

# 检查环境变量
if [ -z "$AI_BUILDER_TOKEN" ]; then
    echo "⚠️  警告: AI_BUILDER_TOKEN 环境变量未设置"
    echo "   请设置环境变量或创建 .env 文件"
fi

# 启动应用
echo ""
echo "🌐 启动 Web 应用..."
echo "   访问地址: http://localhost:5000"
echo "   按 Ctrl+C 停止应用"
echo ""

python3 web_app.py





