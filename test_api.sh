#!/bin/bash
# API测试脚本

BASE_URL="http://localhost:5005"
API_KEY="dev-key-12345"

echo "=========================================="
echo "🧪 Indonesia教育搜索API测试"
echo "=========================================="
echo ""

# 测试1：健康检查（无需认证）
echo "1️⃣  测试系统健康检查..."
curl -s "$BASE_URL/api/admin/system_health" | python3 -m json.tool
echo ""
echo ""

# 测试2：搜索API（需要认证）
echo "2️⃣  测试搜索API（Indonesia - 一年级数学）..."
curl -s -X POST "$BASE_URL/api/search" \
  -H 'Content-Type: application/json' \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "country": "Indonesia",
    "grade": "一年级",
    "subject": "数学",
    "language": "zh",
    "max_results": 3
  }' | python3 -m json.tool | head -50
echo ""
echo ""

# 测试3：缓存统计（需要认证）
echo "3️⃣  测试缓存统计API..."
curl -s "$BASE_URL/api/cache/stats" \
  -H "X-API-Key: $API_KEY" | python3 -m json.tool
echo ""
echo ""

echo "=========================================="
echo "✅ 测试完成"
echo "=========================================="
