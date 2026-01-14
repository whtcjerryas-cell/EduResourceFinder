#!/usr/bin/env python3
"""
测试标题清理和评分功能
"""

import requests
import json

print("=" * 80)
print("🧪 测试：标题清理和评分")
print("=" * 80)
print()

# 搜索请求
search_data = {
    "country": "Indonesia",
    "countryCode": "ID",
    "grade": "Grade 2",
    "semester": "Semester 1",
    "subject": "Mathematics",
    "query": "matematika kelas 2",
    "resourceType": "video"
}

print("🔍 正在搜索...")
response = requests.post(
    "http://localhost:5001/api/search",
    json=search_data,
    timeout=60,
    headers={"Content-Type": "application/json"}
)

if response.status_code != 200:
    print(f"❌ 搜索失败: {response.status_code}")
    exit(1)

result = response.json()

if not result.get('success'):
    print(f"❌ 搜索失败: {result.get('message')}")
    exit(1)

results = result.get('results', [])

print(f"✅ 搜索成功！找到 {len(results)} 个结果")
print()

print("=" * 80)
print("📋 标题清理验证（前10个）")
print("=" * 80)
print()

# 统计包含"YouTube"的标题
youtube_count_before = 0
youtube_count_after = 0

for i, r in enumerate(results[:10], 1):
    title = r.get('title', '')
    url = r.get('url', '')
    score = r.get('score', 0)
    resource_type = r.get('resource_type', '')
    recommendation = r.get('recommendation_reason', '')

    # 检查原始标题中是否包含YouTube
    original_has_youtube = 'youtube' in title.lower()
    # 检查URL是否包含youtube
    url_has_youtube = 'youtube' in url.lower()

    if original_has_youtube:
        youtube_count_before += 1
    if url_has_youtube and not original_has_youtube:
        youtube_count_after += 1

    type_icon = "🎁" if resource_type == "播放列表" else "📹" if resource_type == "视频" else "📄"

    print(f"{i:2d}. {type_icon} {score:4.1f}/10  {resource_type}")
    print(f"    标题: {title[:70]}")
    if len(title) > 70:
        print(f"         {title[70:]}")
    print(f"    推荐: {recommendation[:60]}..." if len(recommendation) > 60 else f"    推荐: {recommendation}")
    print()

print("=" * 80)
print("📊 统计结果")
print("=" * 80)
print()

# 统计资源类型分布
type_counts = {}
for r in results:
    rt = r.get('resource_type', '未知')
    type_counts[rt] = type_counts.get(rt, 0) + 1

print("资源类型分布:")
for rtype, count in type_counts.items():
    icon = "🎁" if rtype == "播放列表" else "📹" if rtype == "视频" else "📄"
    print(f"  {icon} {rtype}: {count}个")
print()

# 统计分数分布
scores = [r.get('score', 0) for r in results]
avg_score = sum(scores) / len(scores) if scores else 0
min_score = min(scores) if scores else 0
max_score = max(scores) if scores else 0

print(f"分数统计:")
print(f"  平均分: {avg_score:.2f}")
print(f"  最高分: {max_score:.2f}")
print(f"  最低分: {min_score:.2f}")
print(f"  跨度: {max_score - min_score:.2f}")
print()

# 统计推荐理由分布
has_recommendation = sum(1 for r in results if r.get('recommendation_reason'))
print(f"推荐理由统计:")
print(f"  有推荐理由: {has_recommendation}个 ({has_recommendation/len(results)*100:.1f}%)")
print(f"  无推荐理由: {len(results) - has_recommendation}个")

print()
print("=" * 80)
