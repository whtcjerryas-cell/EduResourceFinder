#!/usr/bin/env python3
from core.result_scorer import IntelligentResultScorer

scorer = IntelligentResultScorer()

print("=" * 80)
print("测试优化后的年级识别")
print("=" * 80)

test_cases = [
    {
        'title': 'التربية البدنية بنات - الصف الثاني عشر - الفصل الثاني',
        'expected_grade': '十二年级',
    },
    {
        'title': 'التربية البدنية بنات - الصف الثاني - الفصل الثاني',
        'expected_grade': '二年级',
    },
    {
        'title': 'التربية البدنية بنات - الصف الثامن - الفصل الاول',
        'expected_grade': '八年级',
    },
]

for i, test in enumerate(test_cases, 1):
    print(f"\n测试 {i}:")
    print(f"标题: {test['title']}")

    # 测试年级识别
    extracted = scorer._extract_grade_from_title_rule(test['title'], 'ar')
    expected = test['expected_grade']

    print(f"期望年级: {expected}")
    print(f"提取年级: {extracted}")

    if extracted == expected:
        print("✅ 通过")
    else:
        print(f"❌ 失败：期望{expected}，实际{extracted}")

print("\n" + "=" * 80)
