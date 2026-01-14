# Python 3.12 虚拟环境快速指南

## 🎯 问题说明

Python 3.12 (Homebrew) 使用 **PEP 668** 外部管理环境保护机制，不允许直接使用 `pip install` 安装包到系统Python。

**错误提示**:
```
error: externally-managed-environment
× This environment is externally managed
```

**解决方案**: 使用虚拟环境（推荐）✅

---

## 🚀 快速开始（3步）

### 步骤1: 创建虚拟环境

```bash
cd /Users/shmiwanghao8/Desktop/education/Indonesia
bash scripts/setup_venv.sh
```

这个脚本会：
- ✅ 配置pip国内源（清华源）
- ✅ 创建Python 3.12虚拟环境
- ✅ 升级pip和基础工具
- ✅ 安装项目所有依赖包
- ✅ 验证关键包安装

### 步骤2: 激活虚拟环境

```bash
source venv/bin/activate
```

激活后，终端提示符会显示 `(venv)`，表示虚拟环境已激活。

### 步骤3: 运行项目

```bash
python web_app.py
```

---

## 📝 日常使用

### 每次使用前

```bash
# 进入项目目录
cd /Users/shmiwanghao8/Desktop/education/Indonesia

# 激活虚拟环境
source venv/bin/activate

# 运行项目
python web_app.py
```

### 使用完毕后

```bash
# 退出虚拟环境
deactivate
```

---

## 🔧 便捷设置（可选）

### 添加到 ~/.zshrc（推荐）

```bash
# 编辑 ~/.zshrc
nano ~/.zshrc

# 添加以下内容
alias activate-venv='source /Users/shmiwanghao8/Desktop/education/Indonesia/venv/bin/activate'
alias deactivate-venv='deactivate'

# 重新加载配置
source ~/.zshrc
```

之后每次只需运行: `activate-venv`

---

## 📋 常用命令

| 操作 | 命令 |
|------|------|
| 创建虚拟环境 | `bash scripts/setup_venv.sh` |
| 激活虚拟环境 | `source venv/bin/activate` |
| 退出虚拟环境 | `deactivate` |
| 查看已安装包 | `pip list` |
| 安装新包 | `pip install 包名` |
| 更新包 | `pip install --upgrade 包名` |
| 卸载包 | `pip uninstall 包名` |
| 查看Python版本 | `python --version` |
| 查看pip版本 | `pip --version` |

---

## ⚠️ 常见问题

### Q1: 忘记激活虚拟环境

**症状**: 运行 `python web_app.py` 报错 `ModuleNotFoundError`

**解决**: 
```bash
source venv/bin/activate
```

### Q2: 虚拟环境损坏

**解决**: 删除并重新创建
```bash
rm -rf venv
bash scripts/setup_venv.sh
```

### Q3: 需要安装新包

**解决**: 在虚拟环境激活状态下安装
```bash
source venv/bin/activate
pip install 新包名
```

### Q4: 虚拟环境占用空间太大

**解决**: 虚拟环境可以安全删除，需要时重新创建
```bash
rm -rf venv
```

---

## 📊 验证环境

运行以下命令验证虚拟环境是否正确设置：

```bash
# 激活虚拟环境
source venv/bin/activate

# 检查Python版本（应该是3.12.x）
python --version

# 检查关键包
python -c "import flask; print('Flask:', flask.__version__)"
python -c "import pydantic; print('Pydantic:', pydantic.__version__)"
python -c "import yt_dlp; print('yt-dlp:', yt_dlp.version.__version__)"
python -c "import whisper; print('Whisper:', whisper.__version__)"
```

---

## 🎯 最佳实践

1. ✅ **总是使用虚拟环境** - 隔离项目依赖
2. ✅ **每次使用前激活** - 确保使用正确的Python环境
3. ✅ **使用后退出** - 避免影响其他项目
4. ✅ **定期更新依赖** - `pip install --upgrade -r requirements_v3.txt`
5. ✅ **不要提交venv** - 将 `venv/` 添加到 `.gitignore`

---

## 📚 相关文档

- 完整环境评估: `docs/ENVIRONMENT_ASSESSMENT.md`
- 环境检查脚本: `scripts/check_environment.sh`
- 虚拟环境设置脚本: `scripts/setup_venv.sh`

---

**最后更新**: 2025-12-30  
**状态**: ✅ 推荐使用虚拟环境





