# 🔄 Web 应用重启指南

## ⚠️ 重要提示

**日志功能需要在 Web 应用启动时初始化**。如果您在添加日志功能之前就已经启动了 Web 应用，**必须重启 Web 应用**才能看到日志。

## 📋 重启步骤

### 方法 1: 使用 Ctrl+C（推荐）

1. 找到运行 Web 应用的终端窗口
2. 按 `Ctrl + C` 停止应用
3. 重新运行启动命令：
   ```bash
   python3 web_app.py
   ```
   或
   ```bash
   ./start_web_app.sh
   ```

### 方法 2: 使用 kill 命令

如果找不到终端窗口，可以使用以下命令：

```bash
# 1. 查找 Web 应用进程
ps aux | grep "python.*web_app\|flask" | grep -v grep

# 2. 停止进程（替换 <PID> 为实际的进程ID）
kill <PID>

# 3. 重新启动
cd /Users/shmiwanghao8/Desktop/education/Indonesia
python3 web_app.py
```

### 方法 3: 使用 pkill（快速）

```bash
# 停止所有 Python Web 应用进程
pkill -f "web_app.py"

# 等待几秒后重新启动
cd /Users/shmiwanghao8/Desktop/education/Indonesia
python3 web_app.py
```

## ✅ 验证日志功能

重启后，您应该看到以下输出：

```
================================================================================
📝 日志系统启动 - 日志文件: /Users/shmiwanghao8/Desktop/education/Indonesia/search_system.log
================================================================================
🚀 启动 Web 应用
================================================================================
访问地址: http://localhost:5000
...
```

## 🔍 测试日志

重启后，执行以下操作：

1. **在浏览器中执行一次搜索**
2. **立即查看日志文件**：
   ```bash
   tail -50 search_system.log
   ```

您应该能看到详细的搜索日志，包括：
- 搜索请求信息
- 搜索词生成
- 混合搜索过程
- API 调用详情
- 结果处理过程

## 📝 实时查看日志（推荐）

在另一个终端窗口中运行：

```bash
tail -f search_system.log
```

这样您就可以实时看到所有日志输出，无需刷新。

## 🎯 如果仍然没有日志

1. **确认 Web 应用已重启**：检查启动输出中是否有日志系统初始化消息
2. **检查日志文件权限**：
   ```bash
   ls -lh search_system.log
   chmod 666 search_system.log  # 如果需要
   ```
3. **手动测试日志**：
   ```bash
   python3 -c "from logger_utils import get_logger; logger = get_logger('test'); logger.info('测试')"
   tail -3 search_system.log
   ```

## 📍 日志文件位置

**日志文件**: `search_system.log`  
**完整路径**: `/Users/shmiwanghao8/Desktop/education/Indonesia/search_system.log`

