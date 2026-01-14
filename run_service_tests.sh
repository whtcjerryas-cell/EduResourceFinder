#!/bin/bash
# 服务类单元测试执行脚本

set -e  # 遇到错误立即退出

echo "========================================"
echo "服务类单元测试执行脚本"
echo "========================================"
echo ""

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
echo "检查测试依赖..."
python -m pytest --version > /dev/null 2>&1 || {
    echo "❌ pytest 未安装"
    exit 1
}
echo "✅ pytest 已安装"
echo ""

# 运行测试
echo "========================================"
echo "运行服务类单元测试"
echo "========================================"
echo ""

python -m pytest tests/services/ \
    -v \
    --strict-markers \
    --tb=short \
    --cov=services.knowledge_overview_service \
    --cov=services.batch_video_service \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-fail-under=60

# 检查测试结果
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "✅ 所有测试通过！"
    echo "========================================"
    echo ""
    echo "覆盖率报告已生成:"
    echo "  - HTML: htmlcov/index.html"
    echo "  - 终端: 见上方输出"
    echo ""
    echo "查看 HTML 报告:"
    echo "  open htmlcov/index.html"
else
    echo ""
    echo "========================================"
    echo "❌ 测试失败"
    echo "========================================"
    exit 1
fi
