#!/bin/bash

# 规则搜索引擎 - 一键集成和启动脚本

echo "========================================"
echo "🚀 规则搜索引擎 - 快速启动"
echo "========================================"
echo ""

# Step 1: 检查web_app.py是否存在
if [ ! -f "web_app.py" ]; then
    echo "❌ 错误: 找不到 web_app.py"
    echo "请在项目根目录运行此脚本"
    exit 1
fi

# Step 2: 集成规则搜索API
echo "📦 步骤 1/3: 集成规则搜索API..."
if [ ! -f "web_app_backup_before_rule_based_search.py" ]; then
    python3 integrate_rule_based_search.py

    if [ $? -eq 0 ]; then
        echo "✅ API集成成功"
    else
        echo "❌ API集成失败"
        exit 1
    fi
else
    echo "⏭️  已集成，跳过此步骤"
fi

# Step 3: 检查服务器是否运行
echo ""
echo "🔍 步骤 2/3: 检查服务器状态..."
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  检测到端口5000已被占用"
    echo "   请先关闭现有服务器或使用其他端口"
    echo ""
    read -p "是否尝试自动关闭现有服务器? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "   关闭现有服务器..."
        lsof -ti:5000 | xargs kill -9 2>/dev/null
        sleep 2
    else
        echo "   取消启动"
        exit 1
    fi
fi

# Step 4: 启动服务器
echo ""
echo "🚀 步骤 3/3: 启动Flask服务器..."
echo "   访问地址: http://localhost:5000"
echo "   演示页面: http://localhost:5000/rule_search_demo.html"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "========================================"
echo ""

# 启动服务器
python3 web_app.py
