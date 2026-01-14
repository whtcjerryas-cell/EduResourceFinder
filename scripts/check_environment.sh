#!/bin/bash
# 环境检查脚本
# 用途: 快速检查Python环境和依赖包状态

echo "🔍 Python AI编程环境检查"
echo "================================"
echo ""

# 1. Python版本
echo "📌 Python版本:"
python3 --version
echo ""

# 2. pip配置
echo "📌 pip配置:"
if [ -f ~/.pip/pip.conf ]; then
    echo "✅ pip配置文件存在"
    echo "   源地址: $(pip3 config get global.index-url 2>/dev/null || echo '未配置')"
else
    echo "⚠️  pip配置文件不存在（建议配置国内源）"
fi
echo "   pip版本: $(pip3 --version | cut -d' ' -f2)"
echo ""

# 3. 关键包检查
echo "📌 关键依赖包:"
echo ""

check_package() {
    local package=$1
    local import_name=$2
    local version_cmd=$3
    
    if python3 -c "import $import_name" 2>/dev/null; then
        if [ -n "$version_cmd" ]; then
            local version=$(python3 -c "$version_cmd" 2>/dev/null || echo "未知")
            echo "   ✅ $package: $version"
        else
            echo "   ✅ $package: 已安装"
        fi
    else
        echo "   ❌ $package: 未安装"
    fi
}

check_package "Flask" "flask" "import flask; print(flask.__version__)"
check_package "Pydantic" "pydantic" "import pydantic; print(pydantic.__version__)"
check_package "yt-dlp" "yt_dlp" "import yt_dlp; print(yt_dlp.version.__version__)"
check_package "Whisper" "whisper" "import whisper; print(whisper.__version__)"
check_package "PyTorch" "torch" "import torch; print(torch.__version__)"
check_package "OpenAI" "openai" "import openai; print(openai.__version__)"
check_package "ffmpeg-python" "ffmpeg" "已安装"
check_package "requests" "requests" "import requests; print(requests.__version__)"
check_package "pandas" "pandas" "import pandas; print(pandas.__version__)"
echo ""

# 4. 系统工具
echo "📌 系统工具:"
if command -v ffmpeg &> /dev/null; then
    echo "   ✅ ffmpeg: $(ffmpeg -version | head -1 | cut -d' ' -f3)"
else
    echo "   ❌ ffmpeg: 未安装"
fi
echo ""

# 5. 过时的包
echo "📌 过时的包（前10个）:"
pip3 list --outdated 2>/dev/null | head -11 | tail -10 || echo "   无过时包"
echo ""

# 6. 项目依赖检查
echo "📌 项目依赖检查:"
if [ -f "requirements_v3.txt" ]; then
    echo "   ✅ requirements_v3.txt 存在"
    missing=$(pip3 check 2>&1 | grep -c "not installed" || echo "0")
    if [ "$missing" -gt 0 ]; then
        echo "   ⚠️  发现缺失的依赖包"
    else
        echo "   ✅ 所有依赖包已安装"
    fi
else
    echo "   ⚠️  requirements_v3.txt 不存在"
fi
echo ""

# 7. 总结
echo "================================"
echo "📊 环境状态总结:"
python_version=$(python3 --version | cut -d' ' -f2)
major_version=$(echo $python_version | cut -d'.' -f1)
minor_version=$(echo $python_version | cut -d'.' -f2 | cut -d'.' -f1)

if [ "$major_version" -eq 3 ] && [ "$minor_version" -lt 11 ]; then
    echo "   ⚠️  Python版本较旧 ($python_version)，建议升级到3.11或3.12"
else
    echo "   ✅ Python版本正常 ($python_version)"
fi

if [ ! -f ~/.pip/pip.conf ]; then
    echo "   ⚠️  未配置pip国内源，建议运行: scripts/setup_environment.sh"
else
    echo "   ✅ pip源已配置"
fi

echo ""
echo "💡 提示: 运行 'scripts/setup_environment.sh' 可以自动配置环境"

