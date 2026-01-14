#!/usr/bin/env python3
"""
MCP工具直接测试脚本（跳过API层）

直接测试评分系统的MCP工具集成
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.result_scorer import IntelligentResultScorer


def test_mcp_tools_direct():
    """直接测试MCP工具集成"""

    print("=" * 60)
    print("测试: MCP工具直接集成测试")
    print("=" * 60)

    # 初始化评分器（印尼）
    scorer = IntelligentResultScorer(country_code='ID')

    # 测试案例
    test_cases = [
        {
            'name': '案例1: 年级不匹配 (Kelas 6 vs Kelas 1)',
            'result': {
                'title': 'matematika Kelas 6 vol 1 LENGKAP',
                'url': 'https://www.youtube.com/playlist?list=example',
                'snippet': 'Complete mathematics curriculum for Grade 6'
            },
            'metadata': {
                'country': 'Indonesia',
                'grade': 'Kelas 1',
                'subject': 'Matematika',
                'language_code': 'id'
            },
            'expected_score': 3.0,  # 应该低分
            'expected_keywords': ['不符', '不匹配', 'Kelas 6']
        },
        {
            'name': '案例2: 社交媒体 (Instagram)',
            'result': {
                'title': 'Math Tips from Instagram',
                'url': 'https://www.instagram.com/p/123456',
                'snippet': 'Quick math tips'
            },
            'metadata': {
                'country': 'Indonesia',
                'grade': 'Kelas 1',
                'subject': 'Matematika',
                'language_code': 'id'
            },
            'expected_score': 0.0,  # 应该过滤
            'expected_keywords': ['不推荐', '过滤', 'instagram']
        },
        {
            'name': '案例3: 完美匹配 (Kelas 1)',
            'result': {
                'title': 'Matematika Kelas 1 SD - Bilangan 1-10',
                'url': 'https://www.youtube.com/watch?v=example',
                'snippet': 'Pembelajaran matematika kelas 1 bilangan'
            },
            'metadata': {
                'country': 'Indonesia',
                'grade': 'Kelas 1',
                'subject': 'Matematika',
                'language_code': 'id'
            },
            'expected_score': 9.0,  # 应该高分
            'expected_keywords': ['匹配', '正确', 'Kelas 1']
        },
        {
            'name': '案例4: 两位数年级 (Kelas 10)',
            'result': {
                'title': 'Fisika Kelas 10 SMA',
                'url': 'https://www.youtube.com/playlist?list=example',
                'snippet': 'Physics for Grade 10'
            },
            'metadata': {
                'country': 'Indonesia',
                'grade': 'Kelas 1',
                'subject': 'Matematika',
                'language_code': 'id'
            },
            'expected_score': 3.0,  # 应该低分（年级不符）
            'expected_keywords': ['不符', 'Kelas 10']
        }
    ]

    passed = 0
    failed = 0

    for idx, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 60}")
        print(f"{test_case['name']}")
        print('=' * 60)

        result = test_case['result']
        metadata = test_case['metadata']
        expected_score = test_case['expected_score']
        expected_keywords = test_case['expected_keywords']

        print(f"标题: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"目标年级: {metadata['grade']}")
        print(f"期望分数: ≤ {expected_score}")

        try:
            # 调用评分系统 - 使用score_results方法获取完整信息
            scored_results = scorer.score_results(
                results=[result],
                query=f"{metadata['grade']} {metadata['subject']}",
                metadata=metadata
            )

            # 取第一个结果
            score_info = scored_results[0] if scored_results else {}
            actual_score = score_info.get('score', 0)
            actual_reason = score_info.get('recommendation_reason', '')

            print(f"\n实际分数: {actual_score}")
            print(f"推荐理由: {actual_reason[:100]}...")

            # 验证分数
            score_ok = True
            if expected_score == 0.0:
                # 应该是0分
                score_ok = actual_score == 0.0
            elif expected_score <= 3.0:
                # 应该是低分
                score_ok = actual_score <= 3.0
            elif expected_score >= 9.0:
                # 应该是高分
                score_ok = actual_score >= 8.0

            # 验证关键词
            keywords_found = any(kw.lower() in actual_reason.lower() for kw in expected_keywords)

            if score_ok and keywords_found:
                print(f"✅ 通过")
                passed += 1
            else:
                print(f"❌ 失败")
                if not score_ok:
                    print(f"   原因: 分数不符合预期")
                    print(f"   期望: ≤ {expected_score}, 实际: {actual_score}")
                if not keywords_found:
                    print(f"   原因: 推荐理由缺少关键词")
                    print(f"   期望关键词: {expected_keywords}")
                failed += 1

        except Exception as e:
            print(f"❌ 异常: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"通过: {passed}/{len(test_cases)}")
    print(f"失败: {failed}/{len(test_cases)}")

    if failed == 0:
        print("\n✅ 所有测试通过！")
        return True
    else:
        print(f"\n⚠️ {failed} 个测试失败")
        return False


if __name__ == "__main__":
    success = test_mcp_tools_direct()
    sys.exit(0 if success else 1)
