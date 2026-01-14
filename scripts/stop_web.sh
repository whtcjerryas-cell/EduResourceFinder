#!/bin/bash
# Web服务停止脚本

echo "========================================="
echo "🛑 停止教育资源搜索系统"
echo "========================================="

# 停止web_app进程
echo ""
echo "[1/2] 停止Web服务进程..."
PROCS=$(ps aux | grep -E "python.*web_app|flask.*run" | grep -v grep)
if [ -n "$PROCS" ]; then
    echo "$PROCS" | awk '{print $2}' | xargs kill -9 2>/dev/null
    COUNT=$(echo "$PROCS" | wc -l)
    echo "   ✅ 已停止 $COUNT 个进程"
else
    echo "   ℹ️  没有发现运行中的Web服务"
fi

# 清理Playwright浏览器进程
echo ""
echo "[2/2] 清理残留的浏览器进程..."
CHROME_PROCS=$(ps aux | grep "[m]s-playwright" | grep chrom)
if [ -n "$CHROME_PROCS" ]; then
    echo "$CHROME_PROCS" | awk '{print $2}' | xargs kill -9 2>/dev/null
    COUNT=$(echo "$CHROME_PROCS" | wc -l)
    echo "   ✅ 已清理 $COUNT 个浏览器进程"
else
    echo "   ✅ 没有残留的浏览器进程"
fi

echo ""
echo "========================================="
echo "✅ 清理完成"
echo "========================================="
