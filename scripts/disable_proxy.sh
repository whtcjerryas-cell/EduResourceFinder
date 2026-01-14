#!/bin/bash
# 禁用代理并重启服务器

echo "🔄 禁用代理..."
export HTTP_PROXY=""
export HTTPS_PROXY=""

echo "✅ 代理已禁用"
echo "🔄 重启服务器..."

# 停止旧服务器
pkill -f "python.*web_app"

# 等待2秒
sleep 2

# 启动新服务器
nohup python3 web_app.py > server.log 2>&1 &
NEW_PID=$!

echo "✅ 服务器已重启 (PID: $NEW_PID)"
echo "📊 检查服务器状态..."

sleep 3

# 检查服务器是否运行
if curl -s http://localhost:5001/api/system_metrics > /dev/null; then
    echo "✅ 服务器运行正常！"
    echo "🌐 访问: http://localhost:5001"
else
    echo "❌ 服务器启动失败，查看日志:"
    tail -20 server.log
fi
