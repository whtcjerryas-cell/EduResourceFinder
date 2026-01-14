#!/usr/bin/env python3
"""
测试评分系统优化效果
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.result_scorer import IntelligentResultScorer


def test_scoring():
    """测试优化后的评分系统"""
    print("=" * 80)
    print("测试评分系统优化效果")
    print("=" * 80)

    scorer = IntelligentResultScorer()

    # 测试用例（基于真实案例）
    test_cases = [
        {
            'name': '案例7：年级完全匹配，学科完全匹配',
            'input': {
                'title': 'التربية الفنية - الصف الثامن - الفصل الاول',
                'url': 'https://www.youtube.com/playlist?list=PL6-a16Kc5naJKtt6eAmM5-r53-zGBNxkl',
                'snippet': '艺术教育 - 八年级 - 第一学期播放列表',
            },
            'metadata': {
                'grade': '八年级',
                'subject': '艺术',
                'language_code': 'ar',
            },
            'expected': {
                'min_score': 8.0,
                'reason_should_contain': ['八年级', '艺术'],
                'reason_should_not_contain': ['一年级', '拼读', '伊斯兰'],
            }
        },
        {
            'name': '案例8：年级完全匹配，学科完全匹配',
            'input': {
                'title': 'التربية الفنية - الصف السابع - الفصل الاول',
                'url': 'https://www.youtube.com/playlist?list=PL6-a16Kc5naJKtt6eAmM5-r53-zGBNxkl',
                'snippet': '艺术教育 - 七年级 - 第一学期',
            },
            'metadata': {
                'grade': '七年级',
                'subject': '艺术',
                'language_code': 'ar',
            },
            'expected': {
                'min_score': 8.0,
                'reason_should_contain': ['七年级', '艺术'],
                'reason_should_not_contain': ['一年级', '伊斯兰'],
            }
        },
        {
            'name': '年级不匹配：目标一年级，标题八年级',
            'input': {
                'title': 'التربية الفنية - الصف الثامن',
                'url': 'https://test.com',
                'snippet': '艺术教育 - 八年级',
            },
            'metadata': {
                'grade': '一年级',
                'subject': '艺术',
                'language_code': 'ar',
            },
            'expected': {
                'max_score': 5.0,  # 应该低分
                'reason_should_contain': ['不匹配', '不符'],  # 接受两种表达方式
            }
        },
        {
            'name': '学科不匹配：目标数学，标题艺术',
            'input': {
                'title': 'التربية الفنية - الصف الأول',
                'url': 'https://test.com',
                'snippet': '艺术教育 - 一年级',
            },
            'metadata': {
                'grade': '一年级',
                'subject': '数学',
                'language_code': 'ar',
            },
            'expected': {
                'max_score': 5.0,  # 应该低分
                'reason_should_contain': ['不匹配', '不符'],  # 接受两种表达方式
            }
        },
    ]

    print(f"\n共 {len(test_cases)} 个测试用例\n")

    passed = 0
    failed = 0

    for test in test_cases:
        print(f"\n{'=' * 80}")
        print(f"【{test['name']}】")
        print(f"{'=' * 80}")

        result = test['input'].copy()
        metadata = test['metadata']
        query = f"{metadata['grade']} {metadata['subject']}"

        print(f"标题: {test['input']['title']}")
        print(f"目标: {metadata['grade']} {metadata['subject']}")
        print(f"查询: {query}")

        try:
            # 评分（使用score_results方法，返回dict列表）
            scored_list = scorer.score_results([result], query, metadata)
            if not scored_list:
                print(f"\n❌ 评分失败：返回空列表")
                failed += 1
                continue

            scored = scored_list[0]  # 获取第一个（也是唯一一个）结果
            score = scored.get('score', 0)
            reason = scored.get('recommendation_reason', 'N/A')

            print(f"\n✅ 评分结果:")
            print(f"  分数: {score}")
            print(f"  理由: {reason}")

            # 验证结果
            expected = test['expected']
            test_passed = True
            errors = []

            # 检查最低分数
            if 'min_score' in expected:
                if score < expected['min_score']:
                    test_passed = False
                    errors.append(f"分数过低：{score} < {expected['min_score']}")

            # 检查最高分数
            if 'max_score' in expected:
                if score > expected['max_score']:
                    test_passed = False
                    errors.append(f"分数过高：{score} > {expected['max_score']}")

            # 检查推荐理由必须包含的关键词（OR逻辑：至少包含一个即可）
            if 'reason_should_contain' in expected:
                keywords = expected['reason_should_contain']
                # 支持列表套列表：[["不匹配", "不符"], "艺术"] 表示要么包含"不匹配"或"不符"，且必须包含"艺术"
                if isinstance(keywords[0], list) if keywords else False:
                    # 列表套列表：每个子列表的OR条件
                    for keyword_group in keywords:
                        if not any(kw in reason for kw in keyword_group):
                            test_passed = False
                            errors.append(f"推荐理由应包含以下任一关键词: {' 或 '.join(keyword_group)}")
                else:
                    # 简单列表：至少包含一个关键词
                    if not any(kw in reason for kw in keywords):
                        test_passed = False
                        errors.append(f"推荐理由应包含以下任一关键词: {' 或 '.join(keywords)}")

            # 检查推荐理由不应包含的关键词
            if 'reason_should_not_contain' in expected:
                for keyword in expected['reason_should_not_contain']:
                    if keyword in reason:
                        test_passed = False
                        errors.append(f"推荐理由不应包含'{keyword}'")

            if test_passed:
                print(f"\n✅ 测试通过")
                passed += 1
            else:
                print(f"\n❌ 测试失败:")
                for error in errors:
                    print(f"  - {error}")
                failed += 1

        except Exception as e:
            print(f"\n❌ 测试出错: {str(e)}")
            failed += 1
            import traceback
            traceback.print_exc()

    # 总结
    print(f"\n{'=' * 80}")
    print("测试总结")
    print(f"{'=' * 80}")
    print(f"总计: {len(test_cases)} 个测试")
    print(f"通过: {passed} 个 ✅")
    print(f"失败: {failed} 个 ❌")
    print(f"通过率: {passed/len(test_cases)*100:.1f}%")
    print(f"{'=' * 80}\n")

    return failed == 0


if __name__ == "__main__":
    success = test_scoring()
    sys.exit(0 if success else 1)
