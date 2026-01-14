#!/bin/bash
# 停止Flask服务器脚本
# 用途: 查找并停止占用端口5000的web_app.py进程

echo "🔍 查找占用端口5000的进程..."

# 查找占用端口5000的进程
PID=$(lsof -ti :5000)

if [ -z "$PID" ]; then
    echo "✅ 端口5000未被占用"
    exit 0
fi

echo "📋 找到进程:"
lsof -i :5000

echo ""
read -p "是否停止这些进程？(y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🛑 停止进程 $PID..."
    kill $PID
    sleep 1
    
    # 检查是否还在运行
    if lsof -ti :5000 > /dev/null 2>&1; then
        echo "⚠️  进程仍在运行，强制停止..."
        kill -9 $PID
        sleep 1
    fi
    
    if lsof -ti :5000 > /dev/null 2>&1; then
        echo "❌ 无法停止进程，请手动处理"
        exit 1
    else
        echo "✅ 端口5000已释放"
    fi
else
    echo "❌ 取消操作"
    exit 0
fi





