#!/usr/bin/env python3
"""测试导出修复"""

import requests
import json

search_data = {
    "country": "Egypt",
    "countryCode": "EG",
    "grade": "Grade 1",
    "semester": "Semester 1",
    "subject": "Physics",
    "query": "physics grade 1",
    "resourceType": "video"
}

print("🔍 搜索中...")
response = requests.post(
    "http://localhost:5001/api/search",
    json=search_data,
    timeout=60,
    headers={"Content-Type": "application/json"}
)

result = response.json()
results = result.get('results', [])

print(f"\n✅ 找到 {len(results)} 个结果\n")

print("=" * 80)
print("检查结果字段（前5个）")
print("=" * 80)

for i, r in enumerate(results[:5], 1):
    title = r.get('title', '')[:50]
    url = r.get('url', '')[:70]
    score = r.get('score', 0)
    reason = r.get('recommendation_reason', '')[:50]
    rtype = r.get('resource_type', '')
    
    print(f"\n{i}. {title}")
    print(f"   URL: {url}")
    print(f"   质量分数: {score}")
    print(f"   资源类型: {rtype}")
    print(f"   推荐理由: {reason}...")

print("\n" + "=" * 80)
print("统计信息")
print("=" * 80)

# 统计质量分数
scores = [r.get('score', 0) for r in results]
print(f"质量分数范围: {min(scores):.2f} - {max(scores):.2f}")
print(f"平均质量分数: {sum(scores)/len(scores):.2f}")

# 统计资源类型
types = {}
for r in results:
    t = r.get('resource_type', '未知')
    types[t] = types.get(t, 0) + 1

print(f"\n资源类型分布:")
for t, count in types.items():
    print(f"  {t}: {count}个")

# 检查是否有无效URL
excluded_patterns = ['/playlists', '/channel/', '/c/', '/user/', 
                     'facebook.com', 'imdb.com', 'soundcloud.com']
excluded_count = 0
for r in results:
    url = r.get('url', '').lower()
    if any(pattern in url for pattern in excluded_patterns):
        excluded_count += 1

print(f"\n无效URL数量（应该为0）: {excluded_count}")
print("=" * 80)
