#!/usr/bin/env python3
"""
测试视频搜索评分系统
"""

import requests
import json

print("=" * 80)
print("🧪 测试：视频搜索评分系统")
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

print("=" * 80)
print("📊 评分分析（前10个结果）")
print("=" * 80)
print()

# 按分数排序
sorted_results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)

# 统计分数分布
score_ranges = {
    '9.0-10.0': 0,
    '8.0-8.9': 0,
    '7.0-7.9': 0,
    '6.0-6.9': 0,
    '低于6.0': 0
}

for r in results:
    score = r.get('score', 0)
    if score >= 9.0:
        score_ranges['9.0-10.0'] += 1
    elif score >= 8.0:
        score_ranges['8.0-8.9'] += 1
    elif score >= 7.0:
        score_ranges['7.0-7.9'] += 1
    elif score >= 6.0:
        score_ranges['6.0-6.9'] += 1
    else:
        score_ranges['低于6.0'] += 1

print("📈 分数分布:")
for range_name, count in score_ranges.items():
    if count > 0:
        bar = "█" * count
        print(f"  {range_name}: {count}个 {bar}")
print()

# 显示前10名
print("🏆 前10名结果（按分数排序）:")
print()
for i, r in enumerate(sorted_results[:10], 1):
    score = r.get('score', 0)
    title = r.get('title', '未知标题')[:60]
    url = r.get('url', '')
    is_playlist = 'playlist' in url.lower() or 'list=' in url.lower()

    playlist_indicator = "🎁 " if is_playlist else "📹 "
    print(f"{i:2d}. {playlist_indicator} {score:.1f}/10 - {title}")

print()
print("=" * 80)
print("✅ 验证结果")
print("=" * 80)
print()

# 验证1: 分数是否有区分度
scores = [r.get('score', 0) for r in results]
min_score = min(scores)
max_score = max(scores)
score_range = max_score - min_score

if score_range > 2.0:
    print(f"✅ 分数有良好的区分度: {min_score:.1f} - {max_score:.1f} (跨度: {score_range:.1f}分)")
elif score_range > 1.0:
    print(f"⚠️  分数区分度一般: {min_score:.1f} - {max_score:.1f} (跨度: {score_range:.1f}分)")
else:
    print(f"❌ 分数缺乏区分度: {min_score:.1f} - {max_score:.1f} (跨度: {score_range:.1f}分)")

# 验证2: 是否按分数降序排列
is_sorted = all(sorted_results[i].get('score', 0) >= sorted_results[i+1].get('score', 0)
                for i in range(len(sorted_results)-1))

if is_sorted:
    print("✅ 结果按分数降序正确排列")
else:
    print("❌ 结果未按分数降序排列")

# 验证3: 播放列表是否优先
first_playlist_idx = next((i for i, r in enumerate(sorted_results)
                          if 'playlist' in r.get('url', '').lower() or 'list=' in r.get('url', '').lower()), None)
first_non_playlist_idx = next((i for i, r in enumerate(sorted_results)
                               if not ('playlist' in r.get('url', '').lower() or 'list=' in r.get('url', '').lower())), None)

if first_playlist_idx is not None and first_non_playlist_idx is not None:
    if first_playlist_idx < first_non_playlist_idx:
        print(f"✅ 播放列表优先展示（第1个播放列表在第{first_playlist_idx + 1}位，第1个单个视频在第{first_non_playlist_idx + 1}位）")
    else:
        print(f"⚠️  播放列表未优先展示（第1个播放列表在第{first_playlist_idx + 1}位，第1个单个视频在第{first_non_playlist_idx + 1}位）")
elif first_playlist_idx is not None:
    print("✅ 所有结果都是播放列表")
else:
    print("ℹ️  没有检测到播放列表")

print()
print("=" * 80)
