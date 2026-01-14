#!/bin/bash
# Gunicorn 启动脚本 - 支持长超时

echo "========================================="
echo "🚀 教育资源搜索系统 - Gunicorn启动"
echo "========================================="

# 停止旧进程
echo ""
echo "[1/3] 停止旧的Web服务进程..."
OLD_PROCS=$(ps aux | grep -E "gunicorn|python.*web_app" | grep -v grep | awk '{print $2}' | wc -l)
if [ "$OLD_PROCS" -gt 0 ]; then
    ps aux | grep -E "gunicorn|python.*web_app" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null
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
    exit 1
else
    echo "   ✅ 端口5001已释放"
fi

# 启动Gunicorn
echo ""
echo "[3/3] 启动Gunicorn服务..."
echo "   访问地址: http://localhost:5001"
echo "   超时时间: 300秒 (5分钟)"
echo ""

# 检查是否安装了gunicorn
if command -v gunicorn &> /dev/null; then
    echo "   ✅ 使用系统安装的gunicorn"
    gunicorn web_app:app \
        --bind 0.0.0.0:5001 \
        --workers 4 \
        --worker-class gevent \
        --worker-connections 1000 \
        --timeout 300 \
        --graceful-timeout 30 \
        --keep-alive 5 \
        --max-requests 1000 \
        --max-requests-jitter 50 \
        --access-logfile - \
        --error-logfile - \
        --log-level info
else
    echo "   ℹ️  gunicorn未安装，使用Flask开发服务器"
    echo "   💡 推荐安装: pip3 install gunicorn gevent"
    echo ""
    python3 web_app.py
fi
