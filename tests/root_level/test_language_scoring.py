#!/usr/bin/env python3
"""测试语言匹配评分功能"""

import sys
sys.path.insert(0, '/Users/shmiwanghao8/Desktop/education/Indonesia')

from core.result_scorer import IntelligentResultScorer

# 创建评分器
scorer = IntelligentResultScorer()

print("=" * 80)
print("语言检测和匹配评分测试")
print("=" * 80)

# 测试数据：混合语言的搜索结果
test_results = [
    {
        "title": "دروس الفيزياء للصف الأول - فيديو كورس",  # 阿拉伯语
        "url": "https://www.youtube.com/playlist?list=arabic_physics",
        "snippet": "شرح كامل لمادة الفيزياء للصف الأول الإعدادي باللغة العربية. تغطي جميع الموضوعات."
    },
    {
        "title": "Grade 1 Physics - Complete Video Course",  # 英语
        "url": "https://www.youtube.com/playlist?list=english_physics",
        "snippet": "Complete physics course for Grade 1 students covering all topics in English."
    },
    {
        "title": "فيزياء الصف الأول - باللغة العربية",  # 阿拉伯语标题
        "url": "https://www.youtube.com/watch?v=arabic_video",
        "snippet": "Physics lessons in Arabic for first grade students."  # 英语摘要
    },
]

# 目标语言：阿拉伯语（伊拉克）
target_language = "ar"

print(f"\n目标语言: 阿拉伯语 (ar) - 伊拉克")
print("\n" + "=" * 80)
print(f"{'序号':<5} {'标题':<50} {'检测到的语言':<15} {'语言匹配得分':<10}")
print("=" * 80)

for i, result in enumerate(test_results, 1):
    title = result['title']
    snippet = result['snippet']

    # 检测标题和摘要的语言
    title_lang = scorer._detect_language(title)
    snippet_lang = scorer._detect_language(snippet)

    # 计算语言匹配得分
    lang_score = scorer._score_language_matching(title, snippet, target_language)

    # 显示标题（截断）
    title_display = title[:47] + "..." if len(title) > 50 else title

    print(f"{i:<5} {title_display:<50} {title_lang}/{snippet_lang:<15} {lang_score:<10.2f}")

print("\n" + "=" * 80)
print("\n分析:")
print("1. 阿拉伯语标题+摘要应获得最高分 (1.5分)")
print("2. 英语标题+摘要应获得较低分 (0.5分，作为通用语言的降级匹配)")
print("3. 阿拉伯语标题+英语摘要应获得中等分 (1.2分，标题匹配)")
print("\n预期结果: 阿拉伯语资源应排在前面，英语资源排在后面")
print("=" * 80)

# 完整评分测试（包含所有评分维度）
print("\n完整评分测试 (包含所有评分维度):")
print("=" * 80)

metadata = {
    'country': 'IQ',
    'grade': 'Grade 1',
    'subject': 'Physics',
    'language_code': 'ar'
}

query = "physics grade 1"

scored_results = scorer.score_results(test_results, query, metadata)

print(f"\n{'序号':<5} {'总分':<10} {'语言分':<10} {'标题':<60}")
print("-" * 80)

for i, result in enumerate(scored_results, 1):
    score = result['score']
    title = result['title'][:57] + "..." if len(result['title']) > 60 else result['title']

    # 重新计算语言分用于显示
    lang_score = scorer._score_language_matching(
        result['title'].lower(),
        result['snippet'].lower(),
        'ar'
    )

    print(f"{i:<5} {score:<10.2f} {lang_score:<10.2f} {title:<60}")

print("\n✅ 测试完成！")
print("预期: 阿拉伯语资源应该排名更高")
