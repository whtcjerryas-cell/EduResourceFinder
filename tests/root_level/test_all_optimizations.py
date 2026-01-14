#!/usr/bin/env python3
"""测试所有优化功能"""

import sys
sys.path.insert(0, '/Users/shmiwanghao8/Desktop/education/Indonesia')

from core.result_scorer import IntelligentResultScorer

print("=" * 80)
print("测试所有优化功能")
print("=" * 80)

scorer = IntelligentResultScorer()

# 测试数据：不同丰富度的播放列表
test_results = [
    {
        "title": "完整物理课程 - 20个视频 - 10小时",
        "url": "https://www.youtube.com/playlist?list=physics_full_20",
        "snippet": "完整的物理课程，包含20个视频，总时长10小时",
        "playlist_info": {
            "video_count": 20,
            "total_duration_minutes": 600
        }
    },
    {
        "title": "物理基础课程 - 5个视频 - 1小时",
        "url": "https://www.youtube.com/playlist?list=physics_basic_5",
        "snippet": "物理基础课程，5个视频，总时长1小时",
        "playlist_info": {
            "video_count": 5,
            "total_duration_minutes": 60
        }
    },
    {
        "title": "物理简介 - 2个视频 - 30分钟",
        "url": "https://www.youtube.com/playlist?list=physics_intro_2",
        "snippet": "物理简介，2个视频，总时长30分钟",
        "playlist_info": {
            "video_count": 2,
            "total_duration_minutes": 30
        }
    },
]

metadata = {
    'country': 'IQ',
    'grade': 'Grade 1',
    'subject': 'Physics',
    'language_code': 'ar'
}

query = "physics grade 1"

print("\n1. 测试播放列表丰富度评分:")
print("=" * 80)

for result in test_results:
    playlist_info = result['playlist_info']
    richness_score = scorer._score_playlist_richness(playlist_info)

    print(f"\n标题: {result['title']}")
    print(f"  视频数量: {playlist_info['video_count']}")
    print(f"  总时长: {playlist_info['total_duration_minutes']}分钟")
    print(f"  丰富度得分: {richness_score:.2f}/1.5")

print("\n" + "=" * 80)
print("\n2. 测试完整评分（包含所有维度）:")
print("=" * 80)

scored_results = scorer.score_results(test_results, query, metadata)

print(f"\n{'排名':<6} {'总分':<10} {'丰富度分':<10} {'标题':<60}")
print("-" * 80)

for i, result in enumerate(scored_results, 1):
    score = result['score']
    title = result['title'][:57] + "..." if len(result['title']) > 60 else result['title']

    # 重新计算丰富度分用于显示
    playlist_info = result.get('playlist_info', {})
    richness_score = scorer._score_playlist_richness(playlist_info) if playlist_info else 0

    print(f"{i:<6} {score:<10.2f} {richness_score:<10.2f} {title:<60}")

print("\n" + "=" * 80)
print("\n✅ 预期结果:")
print("  - 20个视频、10小时的播放列表应该得分最高")
print("  - 2个视频、30分钟的播放列表应该得分最低")
print("  - 播放列表丰富度评分影响总分排名")
print("=" * 80)
