#!/usr/bin/env python3
"""
测试视频搜索评分系统 - 查看API原始顺序
"""

import requests
import json

print("=" * 80)
print("🧪 测试：视频搜索评分系统（API原始顺序）")
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

print(f"📤 搜索请求: {search_data['query']}")
print()

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
print("📊 API返回的原始顺序（前10个）")
print("=" * 80)
print()

# 不重新排序，直接显示API返回的顺序
for i, r in enumerate(results[:10], 1):
    score = r.get('score', 0)
    title = r.get('title', '未知标题')[:55]
    url = r.get('url', '')
    is_playlist = 'playlist' in url.lower() or 'list=' in url.lower()

    playlist_indicator = "🎁 " if is_playlist else "📹 "
    print(f"{i:2d}. {playlist_indicator} {score:4.1f}/10  {title}")

print()
print("=" * 80)
print("✅ 验证")
print("=" * 80)
print()

# 验证播放列表优先
first_playlist_idx = next((i for i, r in enumerate(results)
                          if 'playlist' in r.get('url', '').lower() or 'list=' in r.get('url', '').lower()), None)
first_video_idx = next((i for i, r in enumerate(results)
                       if not ('playlist' in r.get('url', '').lower() or 'list=' in r.get('url', '').lower())), None)

if first_playlist_idx is not None and first_video_idx is not None:
    if first_playlist_idx < first_video_idx:
        print(f"✅ 播放列表优先（第1个播放列表: #{first_playlist_idx + 1}, 第1个视频: #{first_video_idx + 1}）")
    else:
        print(f"❌ 播放列表未优先（第1个播放列表: #{first_playlist_idx + 1}, 第1个视频: #{first_video_idx + 1}）")

# 验证分数降序
scores = [r.get('score', 0) for r in results]
is_descending = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
if is_descending:
    print("✅ 结果按分数降序排列")
else:
    print("⚠️  结果未严格按分数降序（可能因为播放列表优先）")

print()
print("=" * 80)
