#!/bin/bash
# Next.js 前端启动脚本

echo "=================================="
echo "🚀 Next.js 前端启动脚本"
echo "=================================="
echo ""

# 进入前端目录
cd "$(dirname "$0")/l8-frontend" || exit 1

# 停止旧的 Next.js 进程
echo "🛑 停止旧的 Next.js 进程..."
pkill -f "l8-frontend.*next dev" 2>/dev/null
sleep 2

# 清理缓存和锁文件
echo "🧹 清理缓存..."
rm -rf .next/dev/lock 2>/dev/null
rm -rf .next 2>/dev/null

# 启动 Next.js（端口 3002）
echo "🌐 启动 Next.js 开发服务器（端口 3002）..."
PORT=3002 npm run dev &
NEXT_PID=$!

echo "   进程 ID: $NEXT_PID"
echo ""

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务是否启动成功
if lsof -i :3002 | grep LISTEN > /dev/null; then
    echo "✅ Next.js 启动成功！"
    echo ""
    echo "=================================="
    echo "✅ 所有服务已启动"
    echo "=================================="
    echo ""
    echo "🌐 访问地址："
    echo "   - Next.js 前端: http://localhost:3002"
    echo "   - 后端 API: http://localhost:5002"
    echo ""
    echo "📝 查看日志："
    echo "   tail -f l8-frontend/.next/dev/server.log"
    echo ""
    echo "🛑 停止服务："
    echo "   pkill -f 'l8-frontend.*next dev'"
    echo ""
else
    echo "❌ Next.js 启动失败！"
    echo "   检查日志: tail -50 nextjs_startup.log"
    exit 1
fi
