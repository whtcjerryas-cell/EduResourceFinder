#!/bin/bash
# Indonesia 项目启动脚本（端口 5002）
# 前后端统一使用端口 5002

echo "=================================="
echo "🚀 Indonesia 项目启动脚本"
echo "=================================="
echo ""

# 停止旧的 web_app.py 进程
echo "🛑 停止旧的 web_app.py 进程..."
pkill -f "python.*web_app.py" 2>/dev/null
sleep 2

# 启动 web_app.py（使用虚拟环境，端口 5002）
echo "🌐 启动 web_app.py（端口 5002）..."
FLASK_PORT=5002 nohup ./venv/bin/python web_app.py > web_app_startup.log 2>&1 &
WEB_PID=$!

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务是否启动成功
if lsof -i :5002 | grep LISTEN > /dev/null; then
    echo "✅ web_app.py 启动成功！"
    echo "   📌 后端地址: http://localhost:5002"
    echo "   📄 进程 ID: $WEB_PID"
    echo "   📋 启动日志: web_app_startup.log"
    echo ""
    echo "=================================="
    echo "✅ 所有服务已启动"
    echo "=================================="
    echo ""
    echo "🌐 访问地址："
    echo "   - 后端 API: http://localhost:5002"
    echo "   - Next.js 前端: http://localhost:3000（需要单独启动）"
    echo ""
    echo "📝 查看日志："
    echo "   tail -f web_app_startup.log"
    echo "   tail -f search_system.log"
    echo ""
    echo "🛑 停止服务："
    echo "   pkill -f 'python.*web_app.py'"
else
    echo "❌ web_app.py 启动失败！"
    echo "   查看日志: tail -50 web_app_startup.log"
    exit 1
fi
