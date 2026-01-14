# Homebrew 安装 FFmpeg 加速指南

**更新日期**: 2025-12-29

---

## 🐌 为什么安装慢？

Homebrew 默认从以下源下载：
- **GitHub**: 下载 formula 定义和源码
- **官方源**: 下载二进制文件（通常在国外服务器）

如果你的网络访问这些源较慢，安装就会很慢。

---

## 🚀 解决方案

### 方案1: 使用国内镜像源（推荐）

#### 1.1 使用中科大镜像（推荐）

```bash
# 替换 Homebrew 源
export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.ustc.edu.cn/brew.git"
export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.ustc.edu.cn/homebrew-core.git"
export HOMEBREW_BOTTLE_DOMAIN="https://mirrors.ustc.edu.cn/homebrew-bottles"

# 永久设置（添加到 ~/.zshrc 或 ~/.bash_profile）
echo 'export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.ustc.edu.cn/brew.git"' >> ~/.zshrc
echo 'export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.ustc.edu.cn/homebrew-core.git"' >> ~/.zshrc
echo 'export HOMEBREW_BOTTLE_DOMAIN="https://mirrors.ustc.edu.cn/homebrew-bottles"' >> ~/.zshrc

# 重新加载配置
source ~/.zshrc

# 更新 Homebrew
brew update

# 现在安装 ffmpeg（应该会快很多）
brew install ffmpeg
```

#### 1.2 使用清华大学镜像

```bash
# 替换 Homebrew 源
export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/brew.git"
export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/homebrew-core.git"
export HOMEBREW_BOTTLE_DOMAIN="https://mirrors.tuna.tsinghua.edu.cn/homebrew-bottles"

# 永久设置
echo 'export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/brew.git"' >> ~/.zshrc
echo 'export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/homebrew-core.git"' >> ~/.zshrc
echo 'export HOMEBREW_BOTTLE_DOMAIN="https://mirrors.tuna.tsinghua.edu.cn/homebrew-bottles"' >> ~/.zshrc

source ~/.zshrc
brew update
brew install ffmpeg
```

#### 1.3 使用阿里云镜像

```bash
export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.aliyun.com/homebrew/brew.git"
export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.aliyun.com/homebrew/homebrew-core.git"
export HOMEBREW_BOTTLE_DOMAIN="https://mirrors.aliyun.com/homebrew/homebrew-bottles"

echo 'export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.aliyun.com/homebrew/brew.git"' >> ~/.zshrc
echo 'export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.aliyun.com/homebrew/homebrew-core.git"' >> ~/.zshrc
echo 'export HOMEBREW_BOTTLE_DOMAIN="https://mirrors.aliyun.com/homebrew/homebrew-bottles"' >> ~/.zshrc

source ~/.zshrc
brew update
brew install ffmpeg
```

---

### 方案2: 只加速 Bottle 下载（不换 Git 源）

如果你只想加速二进制文件下载，可以只设置 `HOMEBREW_BOTTLE_DOMAIN`：

```bash
# 中科大镜像
export HOMEBREW_BOTTLE_DOMAIN="https://mirrors.ustc.edu.cn/homebrew-bottles"

# 添加到 ~/.zshrc
echo 'export HOMEBREW_BOTTLE_DOMAIN="https://mirrors.ustc.edu.cn/homebrew-bottles"' >> ~/.zshrc
source ~/.zshrc

# 安装 ffmpeg
brew install ffmpeg
```

---

### 方案3: 使用代理（如果你有 VPN）

```bash
# 设置代理（替换为你的代理地址和端口）
export http_proxy="http://127.0.0.1:7890"
export https_proxy="http://127.0.0.1:7890"

# 或者使用 socks5 代理
export http_proxy="socks5://127.0.0.1:7890"
export https_proxy="socks5://127.0.0.1:7890"

# 安装 ffmpeg
brew install ffmpeg
```

---

### 方案4: 直接下载预编译二进制（最快）

如果以上方法都不行，可以直接下载预编译的 FFmpeg：

#### macOS (Intel)

```bash
# 下载预编译版本
cd ~/Downloads
curl -O https://evermeet.cx/ffmpeg/ffmpeg-6.1.zip
unzip ffmpeg-6.1.zip

# 移动到系统路径
sudo mv ffmpeg /usr/local/bin/
sudo mv ffprobe /usr/local/bin/

# 验证安装
ffmpeg -version
```

#### macOS (Apple Silicon)

```bash
# 使用 Homebrew 但只下载二进制（不编译）
brew install --force-bottle ffmpeg
```

---

## 🔍 检查当前配置

```bash
# 查看当前 Git 远程地址
cd $(brew --repository)
git remote -v

# 查看 Bottle 域名
echo $HOMEBREW_BOTTLE_DOMAIN

# 查看所有 Homebrew 环境变量
env | grep HOMEBREW
```

---

## ⚡ 推荐操作（最快）

**推荐使用中科大镜像**，速度通常最快：

```bash
# 1. 设置镜像源（一次性操作）
cat >> ~/.zshrc << 'EOF'

# Homebrew 镜像源（中科大）
export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.ustc.edu.cn/brew.git"
export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.ustc.edu.cn/homebrew-core.git"
export HOMEBREW_BOTTLE_DOMAIN="https://mirrors.ustc.edu.cn/homebrew-bottles"
EOF

# 2. 重新加载配置
source ~/.zshrc

# 3. 更新 Homebrew
brew update

# 4. 安装 ffmpeg（现在应该快很多）
brew install ffmpeg
```

---

## 🛠️ 恢复默认源

如果需要恢复默认源：

```bash
# 移除镜像设置
sed -i '' '/HOMEBREW_BREW_GIT_REMOTE/d' ~/.zshrc
sed -i '' '/HOMEBREW_CORE_GIT_REMOTE/d' ~/.zshrc
sed -i '' '/HOMEBREW_BOTTLE_DOMAIN/d' ~/.zshrc

# 重新加载
source ~/.zshrc

# 恢复默认 Git 远程
cd $(brew --repository)
git remote set-url origin https://github.com/Homebrew/brew.git

cd $(brew --repository)/Library/Taps/homebrew/homebrew-core
git remote set-url origin https://github.com/Homebrew/homebrew-core.git
```

---

## 📊 速度对比

| 方案 | 预计时间 | 稳定性 |
|------|---------|--------|
| 默认源 | 10-30分钟 | ⭐⭐⭐ |
| 中科大镜像 | 2-5分钟 | ⭐⭐⭐⭐⭐ |
| 清华镜像 | 3-6分钟 | ⭐⭐⭐⭐ |
| 阿里云镜像 | 3-6分钟 | ⭐⭐⭐⭐ |
| 代理 | 取决于代理速度 | ⭐⭐⭐ |

---

## ✅ 验证安装

安装完成后验证：

```bash
# 检查版本
ffmpeg -version
ffprobe -version

# 测试功能
ffmpeg -f lavfi -i testsrc=duration=1:size=320x240:rate=1 test.mp4
```

---

## 💡 提示

1. **首次安装**: 如果这是第一次使用 Homebrew，可能需要先安装 Homebrew 本身
2. **网络问题**: 如果镜像源也慢，可能是网络问题，建议使用代理
3. **Apple Silicon**: 如果是 M1/M2 Mac，确保使用 Apple Silicon 版本的 Homebrew
4. **权限问题**: 如果遇到权限问题，可能需要 `sudo`（不推荐）或修复权限

---

**最后更新**: 2025-12-29





