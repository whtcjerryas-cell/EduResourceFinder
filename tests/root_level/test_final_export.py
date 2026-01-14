#!/usr/bin/env python3
"""完整测试导出功能"""

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

print("🔍 搜索中（无缓存）...")
response = requests.post(
    "http://localhost:5001/api/search",
    json=search_data,
    timeout=60,
    headers={"Content-Type": "application/json"}
)

result = response.json()
results = result.get('results', [])

print(f"\n✅ 找到 {len(results)} 个结果\n")

# 详细检查每个结果
print("=" * 100)
print(f"{'序号':<5} {'质量分数':<10} {'资源类型':<10} {'URL':<70}")
print("=" * 100)

for i, r in enumerate(results, 1):
    url = r.get('url', '')
    score = r.get('score', 0)
    rtype = r.get('resource_type', '')
    
    # 检查URL类型
    is_playlist = 'list=' in url
    is_channel = any(x in url for x in ['/@', '/channel/', '/playlists'])
    is_excluded = any(x in url for x in ['facebook.com', 'imdb.com'])
    
    marker = ""
    if is_playlist:
        marker = "✅ PLAYLIST"
    elif is_channel:
        marker = "❌ CHANNEL"
    elif is_excluded:
        marker = "❌ EXCLUDED"
    
    print(f"{i:<5} {score:<10.2f} {rtype:<10} {url[:70]}")
    if marker:
        print(f"      {marker}")

print("\n" + "=" * 100)
print("统计")
print("=" * 100)

# URL类型统计
playlist_count = sum(1 for r in results if 'list=' in r.get('url', ''))
channel_count = sum(1 for r in results if any(x in r.get('url', '') for x in ['/@', '/channel/', '/playlists']))
excluded_count = sum(1 for r in results if any(x in r.get('url', '') for x in ['facebook.com', 'imdb.com', 'soundcloud.com']))

print(f"✅ 具体播放列表(list=): {playlist_count}个")
print(f"❌ 频道页面: {channel_count}个（应该为0）")
print(f"❌ 无效域名: {excluded_count}个（应该为0）")

# 分数统计
scores = [r.get('score', 0) for r in results]
if scores:
    print(f"\n质量分数:")
    print(f"  范围: {min(scores):.2f} - {max(scores):.2f}")
    print(f"  平均: {sum(scores)/len(scores):.2f}")
    print(f"  为0的数量: {sum(1 for s in scores if s == 0)}（应该为0）")

print("\n" + "=" * 100)
