#!/bin/bash
# Python AI编程环境配置脚本
# 用途: 配置pip国内源、升级关键包、验证环境

set -e  # 遇到错误立即退出

echo "🚀 开始配置Python AI编程环境..."
echo ""

# 1. 配置pip国内源
echo "📦 [1/4] 配置pip国内源..."
mkdir -p ~/.pip
if [ -f ~/.pip/pip.conf ]; then
    echo "⚠️  pip配置文件已存在，备份为 ~/.pip/pip.conf.bak"
    cp ~/.pip/pip.conf ~/.pip/pip.conf.bak
fi

cat > ~/.pip/pip.conf << 'EOF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn

[install]
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF
echo "✅ pip源配置完成（使用清华源）"
echo ""

# 2. 升级pip和基础工具
echo "⬆️  [2/4] 升级pip和基础工具..."
pip3 install --upgrade pip setuptools wheel --quiet
echo "✅ pip升级完成"
echo ""

# 3. 更新关键包
echo "📦 [3/4] 更新关键包..."
pip3 install --upgrade protobuf urllib3 requests --quiet
echo "✅ 关键包更新完成"
echo ""

# 4. 验证关键包
echo "🔍 [4/4] 验证关键包..."
echo ""
python3 -c "import flask; print('✅ Flask', flask.__version__)" 2>/dev/null || echo "❌ Flask未安装"
python3 -c "import pydantic; print('✅ Pydantic', pydantic.__version__)" 2>/dev/null || echo "❌ Pydantic未安装"
python3 -c "import yt_dlp; print('✅ yt-dlp', yt_dlp.version.__version__)" 2>/dev/null || echo "❌ yt-dlp未安装"
python3 -c "import whisper; print('✅ Whisper', whisper.__version__)" 2>/dev/null || echo "❌ Whisper未安装"
python3 -c "import torch; print('✅ PyTorch', torch.__version__)" 2>/dev/null || echo "❌ PyTorch未安装"
python3 -c "import openai; print('✅ OpenAI', openai.__version__)" 2>/dev/null || echo "❌ OpenAI未安装"
echo ""

# 5. 显示环境信息
echo "📊 环境信息："
echo "   Python版本: $(python3 --version)"
echo "   pip版本: $(pip3 --version | cut -d' ' -f2)"
echo "   pip源: $(pip3 config get global.index-url 2>/dev/null || echo '未配置')"
echo ""

echo "🎉 环境配置完成！"
echo ""
echo "📝 下一步建议："
echo "   1. 查看完整评估报告: docs/ENVIRONMENT_ASSESSMENT.md"
echo "   2. 考虑升级到Python 3.11或3.12（使用Homebrew）"
echo "   3. 测试项目运行: python3 web_app.py"
echo ""





