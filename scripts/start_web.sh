#!/bin/bash
# Web服务启动脚本

echo "========================================="
echo "🚀 教育资源搜索系统 - 启动脚本"
echo "========================================="

# 停止旧进程
echo ""
echo "[1/3] 停止旧的Web服务进程..."
OLD_PROCS=$(ps aux | grep -E "python.*web_app|flask.*run" | grep -v grep | awk '{print $2}' | wc -l)
if [ "$OLD_PROCS" -gt 0 ]; then
    ps aux | grep -E "python.*web_app|flask.*run" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null
    echo "   ✅ 已停止 $OLD_PROCS 个旧进程"
else
    echo "   ℹ️  没有发现旧进程"
fi

# 清理端口
echo ""
echo "[2/3] 清理端口5001..."
lsof -ti:5001 | xargs kill -9 2>/dev/null
if lsof -i:5001 >/dev/null 2>&1; then
    echo "   ⚠️  端口5001仍被占用，尝试强制清理..."
    kill -9 $(lsof -ti:5001) 2>/dev/null
    sleep 1
fi

if lsof -i:5001 >/dev/null 2>&1; then
    echo "   ❌ 无法清理端口5001，请手动检查"
    echo "   查看占用进程: lsof -i:5001"
    exit 1
else
    echo "   ✅ 端口5001已释放"
fi

# 启动新服务
echo ""
echo "[3/3] 启动Web服务..."
echo "   访问地址: http://localhost:5001"
echo "   按 Ctrl+C 停止服务"
echo ""
echo "========================================="
echo ""

# 启动服务
python3 web_app.py
