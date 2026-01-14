#!/bin/bash
# 快速激活虚拟环境脚本
# 用途: 快速激活项目虚拟环境

VENV_DIR="/Users/shmiwanghao8/Desktop/education/Indonesia/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "❌ 虚拟环境不存在，请先运行:"
    echo "   bash scripts/setup_venv.sh"
    exit 1
fi

echo "🔌 激活虚拟环境..."
source "$VENV_DIR/bin/activate"
echo "✅ 虚拟环境已激活"
echo ""
echo "📊 当前Python: $(which python)"
echo "📊 Python版本: $(python --version)"
echo ""
echo "💡 提示: 运行 'deactivate' 退出虚拟环境"





