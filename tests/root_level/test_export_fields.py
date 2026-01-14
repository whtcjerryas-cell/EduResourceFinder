#!/usr/bin/env python3
"""测试导出字段"""

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

print(f"\n✅ 找到 {len(results)} 个结果")
print("\n前3个结果的字段:")
for i, r in enumerate(results[:3], 1):
    print(f"\n{i}. {r.get('title', '')[:60]}")
    print(f"   score: {r.get('score', 'N/A')}")
    print(f"   recommendation_reason: {r.get('recommendation_reason', 'N/A')[:60]}")
    print(f"   resource_type: {r.get('resource_type', 'N/A')}")
    print(f"   URL: {r.get('url', '')[:80]}")
