#!/bin/bash
# Homebrew 镜像源快速配置脚本

echo ""
echo "🚀 正在配置 Homebrew 镜像源（中科大）..."
echo ""

# 检查是否已配置
if grep -q "HOMEBREW_BREW_GIT_REMOTE" ~/.zshrc 2>/dev/null; then
    echo "⚠️  检测到已有镜像配置，跳过..."
else
    echo "" >> ~/.zshrc
    echo "# Homebrew 镜像源（中科大）" >> ~/.zshrc
    echo 'export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.ustc.edu.cn/brew.git"' >> ~/.zshrc
    echo 'export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.ustc.edu.cn/homebrew-core.git"' >> ~/.zshrc
    echo 'export HOMEBREW_BOTTLE_DOMAIN="https://mirrors.ustc.edu.cn/homebrew-bottles"' >> ~/.zshrc
    echo "✅ 镜像源配置已添加到 ~/.zshrc"
fi

# 立即生效
export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.ustc.edu.cn/brew.git"
export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.ustc.edu.cn/homebrew-core.git"
export HOMEBREW_BOTTLE_DOMAIN="https://mirrors.ustc.edu.cn/homebrew-bottles"

echo "✅ 当前会话已生效"
echo ""
echo "📝 下一步操作："
echo "   1. 运行: source ~/.zshrc  (或重新打开终端)"
echo "   2. 运行: brew update"
echo "   3. 运行: brew install ffmpeg"
echo ""





