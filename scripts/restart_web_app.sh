#!/bin/bash
# Web 应用重启脚本

echo "=========================================="
echo "🔄 重启 Web 应用"
echo "=========================================="

# 查找并停止现有的 Web 应用进程
echo "1. 查找现有进程..."
PIDS=$(ps aux | grep "python.*web_app.py" | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "   ✅ 没有找到运行中的 Web 应用进程"
else
    echo "   📋 找到进程: $PIDS"
    echo "2. 停止现有进程..."
    for PID in $PIDS; do
        echo "   停止进程 $PID..."
        kill $PID 2>/dev/null
    done
    sleep 2
    
    # 检查是否还有进程
    REMAINING=$(ps aux | grep "python.*web_app.py" | grep -v grep | awk '{print $2}')
    if [ ! -z "$REMAINING" ]; then
        echo "   ⚠️ 强制停止剩余进程..."
        for PID in $REMAINING; do
            kill -9 $PID 2>/dev/null
        done
    fi
    echo "   ✅ 进程已停止"
fi

# 等待端口释放
echo "3. 等待端口释放..."
sleep 2

# 重新启动 Web 应用
echo "4. 启动 Web 应用..."
cd "$(dirname "$0")"
python3 web_app.py





