#!/bin/bash
# Python 3.12 虚拟环境设置脚本
# 用途: 为项目创建独立的虚拟环境（推荐方式）

set -e  # 遇到错误立即退出

PROJECT_DIR="/Users/shmiwanghao8/Desktop/education/Indonesia"
VENV_DIR="$PROJECT_DIR/venv"
PYTHON_VERSION="python3.12"

echo "🚀 开始设置Python虚拟环境..."
echo ""

# 检查Python 3.12是否可用
if ! command -v $PYTHON_VERSION &> /dev/null; then
    echo "❌ Python 3.12 未找到，请先安装:"
    echo "   brew install python@3.12"
    exit 1
fi

echo "✅ 找到 $PYTHON_VERSION: $($PYTHON_VERSION --version)"
echo ""

# 检查是否已存在虚拟环境
if [ -d "$VENV_DIR" ]; then
    echo "⚠️  虚拟环境已存在: $VENV_DIR"
    read -p "是否重新创建？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  删除旧虚拟环境..."
        rm -rf "$VENV_DIR"
    else
        echo "✅ 使用现有虚拟环境"
        echo ""
        echo "📝 激活虚拟环境:"
        echo "   source $VENV_DIR/bin/activate"
        exit 0
    fi
fi

# 1. 配置pip国内源（如果未配置）
echo "📦 [1/5] 配置pip国内源..."
mkdir -p ~/.pip
if [ ! -f ~/.pip/pip.conf ]; then
    cat > ~/.pip/pip.conf << 'EOF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn

[install]
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF
    echo "✅ pip源配置完成（使用清华源）"
else
    echo "✅ pip源已配置"
fi
echo ""

# 2. 创建虚拟环境
echo "📦 [2/5] 创建虚拟环境..."
cd "$PROJECT_DIR"
$PYTHON_VERSION -m venv "$VENV_DIR"
echo "✅ 虚拟环境创建完成: $VENV_DIR"
echo ""

# 3. 激活虚拟环境并升级pip
echo "⬆️  [3/5] 升级pip和基础工具..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel --quiet
echo "✅ pip升级完成"
echo ""

# 4. 安装项目依赖
echo "📦 [4/5] 安装项目依赖..."
if [ -f "$PROJECT_DIR/requirements_v3.txt" ]; then
    pip install -r "$PROJECT_DIR/requirements_v3.txt" --quiet
    echo "✅ 项目依赖安装完成"
else
    echo "⚠️  requirements_v3.txt 不存在，跳过依赖安装"
fi
echo ""

# 5. 验证安装
echo "🔍 [5/5] 验证关键包..."
echo ""
python -c "import flask; print('✅ Flask', flask.__version__)" 2>/dev/null || echo "❌ Flask未安装"
python -c "import pydantic; print('✅ Pydantic', pydantic.__version__)" 2>/dev/null || echo "❌ Pydantic未安装"
python -c "import yt_dlp; print('✅ yt-dlp', yt_dlp.version.__version__)" 2>/dev/null || echo "❌ yt-dlp未安装"
python -c "import whisper; print('✅ Whisper', whisper.__version__)" 2>/dev/null || echo "❌ Whisper未安装"
python -c "import torch; print('✅ PyTorch', torch.__version__)" 2>/dev/null || echo "❌ PyTorch未安装"
python -c "import openai; print('✅ OpenAI', openai.__version__)" 2>/dev/null || echo "❌ OpenAI未安装"
echo ""

# 显示环境信息
echo "📊 虚拟环境信息："
echo "   Python版本: $(python --version)"
echo "   pip版本: $(pip --version | cut -d' ' -f2)"
echo "   虚拟环境路径: $VENV_DIR"
echo ""

# 创建激活脚本提示
echo "🎉 虚拟环境设置完成！"
echo ""
echo "📝 使用方法："
echo ""
echo "   1. 激活虚拟环境:"
echo "      source $VENV_DIR/bin/activate"
echo ""
echo "   2. 运行项目:"
echo "      python web_app.py"
echo ""
echo "   3. 退出虚拟环境:"
echo "      deactivate"
echo ""
echo "💡 提示: 每次打开新终端都需要激活虚拟环境"
echo "   或者将以下命令添加到 ~/.zshrc:"
echo "   alias activate-venv='source $VENV_DIR/bin/activate'"
echo ""





