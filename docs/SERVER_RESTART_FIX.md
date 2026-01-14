# 服务器重启脚本修复

## 📅 更新日期
2025-12-29

## 🐛 问题

**现象**: 重启脚本执行后显示 "❌ 启动失败，请手动检查"

**原因分析**:
1. 端口5000被占用（可能是之前的进程或AirPlay）
2. 脚本检查逻辑不够完善
3. 日志输出被重定向到 `/dev/null`，无法查看错误信息

## ✅ 解决方案

### 1. 改进端口检查和处理

```bash
# 检查端口5000是否被占用
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "   ⚠️  端口5000仍被占用，尝试释放..."
    PORT_PID=$(lsof -Pi :5000 -sTCP:LISTEN -t)
    if [ -n "$PORT_PID" ]; then
        kill -9 $PORT_PID 2>/dev/null
        sleep 1
    fi
fi
```

### 2. 改进日志输出

- 不再使用 `/dev/null` 重定向
- 将输出保存到 `logs/web_app_restart.log`
- 启动失败时显示日志内容

### 3. 改进进程检查

- 检查进程是否运行
- 检查端口是否监听
- 提供详细的错误信息

## 📝 修改后的脚本

```bash
#!/bin/bash
# 重启Web应用（修复Debug日志API问题）

echo "🔄 正在重启Web应用..."

# 切换到脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 查找并终止现有进程
PID=$(ps aux | grep "[p]ython.*web_app.py" | grep -v grep | awk '{print $2}')
if [ -n "$PID" ]; then
    echo "   终止进程 PID: $PID"
    kill $PID 2>/dev/null
    sleep 2
    # 如果还在运行，强制终止
    if ps -p $PID > /dev/null 2>&1; then
        echo "   强制终止进程..."
        kill -9 $PID 2>/dev/null
    fi
else
    echo "   未找到运行中的进程"
fi

# 等待端口释放
sleep 1

# 检查端口5000是否被占用
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "   ⚠️  端口5000仍被占用，尝试释放..."
    PORT_PID=$(lsof -Pi :5000 -sTCP:LISTEN -t)
    if [ -n "$PORT_PID" ]; then
        kill -9 $PORT_PID 2>/dev/null
        sleep 1
    fi
fi

# 启动新进程
echo "   启动新进程..."
echo "   工作目录: $(pwd)"
echo "   Python路径: $(which python3)"

# 使用绝对路径启动，并重定向输出到日志文件
LOG_FILE="$SCRIPT_DIR/logs/web_app_restart.log"
mkdir -p "$(dirname "$LOG_FILE")"

# 启动进程（使用nohup确保后台运行）
nohup python3 "$SCRIPT_DIR/web_app.py" > "$LOG_FILE" 2>&1 &
NEW_PID=$!

sleep 4

# 检查是否启动成功（通过进程和端口）
if ps -p $NEW_PID > /dev/null 2>&1; then
    # 再检查端口是否监听
    if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "✅ Web应用已重启"
        echo "   访问地址: http://localhost:5000"
        echo "   进程ID: $NEW_PID"
        echo "   日志文件: $LOG_FILE"
        echo ""
        echo "   查看日志: tail -f $LOG_FILE"
        echo "   测试API: curl http://localhost:5000/api/debug_logs?lines=1"
    else
        echo "⚠️  进程已启动但端口未监听，请检查日志:"
        echo "   tail -30 $LOG_FILE"
        if [ -f "$LOG_FILE" ]; then
            echo ""
            echo "   最后30行日志:"
            tail -30 "$LOG_FILE"
        fi
    fi
else
    echo "❌ 启动失败，请检查日志:"
    echo "   tail -30 $LOG_FILE"
    if [ -f "$LOG_FILE" ]; then
        echo ""
        echo "   最后30行日志:"
        tail -30 "$LOG_FILE"
    fi
    exit 1
fi
```

## 🚀 使用方法

```bash
# 执行重启脚本
./restart_web_app_fix.sh

# 查看启动日志
tail -f logs/web_app_restart.log

# 测试API
curl http://localhost:5000/api/debug_logs?lines=1
```

## ✅ 验证清单

- [x] 端口占用检查和处理
- [x] 进程检查（进程ID和端口监听）
- [x] 日志文件输出（不再使用 `/dev/null`）
- [x] 详细的错误信息显示
- [x] 使用 `nohup` 确保后台运行

---

**更新完成日期**: 2025-12-29  
**状态**: ✅ 已修复并验证





