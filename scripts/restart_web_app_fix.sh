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

python3 "$SCRIPT_DIR/web_app.py" > "$LOG_FILE" 2>&1 &
NEW_PID=$!

sleep 3

# 检查是否启动成功
if ps -p $NEW_PID > /dev/null 2>&1; then
    echo "✅ Web应用已重启"
    echo "   访问地址: http://localhost:5000"
    echo "   进程ID: $NEW_PID"
    echo "   日志文件: $LOG_FILE"
    echo ""
    echo "   查看日志: tail -f $LOG_FILE"
else
    echo "❌ 启动失败，请检查日志:"
    echo "   tail -20 $LOG_FILE"
    if [ -f "$LOG_FILE" ]; then
        echo ""
        echo "   最后20行日志:"
        tail -20 "$LOG_FILE"
    fi
    exit 1
fi
