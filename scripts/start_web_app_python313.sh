#!/bin/bash
# 启动Web应用 - Python 3.13版本
# 使用新的虚拟环境

cd "$(dirname "$0")"

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行: python3.13 -m venv venv"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查Python版本
PYTHON_VERSION=$(python --version 2>&1)
echo "📌 使用Python版本: $PYTHON_VERSION"

# 检查依赖是否安装
if ! python -c "import flask" 2>/dev/null; then
    echo "❌ Flask未安装，正在安装依赖..."
    pip install -r requirements.txt
fi

# 启动应用
echo "🚀 启动Web应用..."
python web_app.py

