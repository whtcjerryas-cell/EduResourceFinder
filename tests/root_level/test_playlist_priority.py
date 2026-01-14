#!/usr/bin/env python3
"""
测试YouTube播放列表优先展示功能
"""

import requests
import json

print("=" * 80)
print("🧪 测试：YouTube播放列表优先展示")
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

print(f"📤 搜索请求:")
print(f"  国家: {search_data['country']}")
print(f"  年级: {search_data['grade']}")
print(f"  学科: {search_data['subject']}")
print(f"  查询: {search_data['query']}")
print(f"  资源类型: {search_data['resourceType']}")
print()

print("🔍 正在发送搜索请求...")

response = requests.post(
    "http://localhost:5001/api/search",
    json=search_data,
    timeout=60,
    headers={"Content-Type": "application/json"}
)

print(f"⏱️  响应时间: {response.elapsed.total_seconds():.2f} 秒")
print()

if response.status_code != 200:
    print(f"❌ 搜索失败，状态码: {response.status_code}")
    print(f"响应内容: {response.text[:200]}")
    exit(1)

result = response.json()

if not result.get('success'):
    print(f"❌ 搜索失败: {result.get('message', '未知错误')}")
    exit(1)

results = result.get('results', [])

print(f"✅ 搜索成功！找到 {len(results)} 个结果")
print()

# 统计播放列表和单个视频
playlists = []
videos = []

for i, result in enumerate(results[:10], 1):
    url = result.get('url', '')
    is_playlist = any([
        'playlist' in url.lower(),
        'list=' in url.lower(),
        '/videos' in url.lower()
    ])

    title = result.get('title', '未知标题')[:60]

    if is_playlist:
        playlists.append((i, title, url))
    else:
        videos.append((i, title, url))

print("=" * 80)
print("📊 搜索结果分析（前10个）")
print("=" * 80)
print()

if playlists:
    print(f"🎁 播放列表 ({len(playlists)} 个):")
    for idx, title, url in playlists[:5]:
        print(f"  {idx}. {title}")
        print(f"     URL: {url[:70]}...")
    if len(playlists) > 5:
        print(f"  ... 还有 {len(playlists) - 5} 个播放列表")
    print()

if videos:
    print(f"🎬 单个视频 ({len(videos)} 个):")
    for idx, title, url in videos[:5]:
        print(f"  {idx}. {title}")
        print(f"     URL: {url[:70]}...")
    if len(videos) > 5:
        print(f"  ... 还有 {len(videos) - 5} 个视频")
    print()

print("=" * 80)
print("✅ 验证结果")
print("=" * 80)
print()

if playlists and videos:
    first_is_playlist = playlists[0][0] < videos[0][0]
    if first_is_playlist:
        print("✅ 播放列表优先展示正确！")
        print(f"   第1个播放列表在第 {playlists[0][0]} 位")
        print(f"   第1个单个视频在第 {videos[0][0]} 位")
    else:
        print("⚠️  播放列表没有优先展示")
        print(f"   第1个播放列表在第 {playlists[0][0]} 位")
        print(f"   第1个单个视频在第 {videos[0][0]} 位")
elif playlists:
    print("✅ 所有结果都是播放列表")
elif videos:
    print("ℹ️  所有结果都是单个视频（没有检测到播放列表）")
else:
    print("⚠️  没有找到结果")

print()
print("=" * 80)
