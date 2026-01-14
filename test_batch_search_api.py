#!/usr/bin/env python3
"""
直接测试批量搜索API（绕过认证）

测试evaluation_method字段修复和URL过滤功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_batch_search_direct():
    """直接调用批量搜索函数，测试所有修复"""
    from search_engine_v2 import SearchEngineV2
    from logger_utils import get_logger
    from urllib.parse import urlparse
    import json

    logger = get_logger('batch_search_test')

    print("=" * 80)
    print("批量搜索API测试 - 验证所有修复")
    print("=" * 80)

    # 测试参数
    search_params = {
        'country': 'Indonesia',
        'grade': 'Kelas 1 / 一年级',
        'subject': 'Matematika / 数学',
        'resource_types': ['video', 'playlist'],
        'max_results': 10
    }

    print(f"\n搜索参数:")
    for key, value in search_params.items():
        print(f"  {key}: {value}")
    print()

    # 执行批量搜索
    print("执行批量搜索...")
    print("-" * 80)

    engine = SearchEngineV2()
    results = engine.search(
        country=search_params['country'],
        grade=search_params['grade'],
        subject=search_params['subject'],
        resource_types=search_params['resource_types'],
        max_results=search_params['max_results']
    )

    if not results:
        print("❌ 搜索失败：无结果返回")
        return False

    print(f"\n✅ 搜索完成，共获得 {len(results)} 个结果\n")

    # 分析结果
    print("=" * 80)
    print("结果分析")
    print("=" * 80)

    # 统计数据
    stats = {
        'total': len(results),
        'with_evaluation_method': 0,
        'mcp_tools': 0,
        'llm': 0,
        'rule_based': 0,
        'unknown': 0,
        'high_score': 0,  # >= 8.0
        'low_score': 0,   # <= 3.0
        'youtube': 0,
        'facebook': 0,
        'instagram': 0,
        'kelas_1_high': 0,  # Kelas 1 高分
        'kelas_6_low': 0,   # Kelas 6 低分
    }

    # 详细分析每个结果
    for i, result in enumerate(results[:10], 1):  # 只显示前10个
        title = result.get('title', 'N/A')[:60]
        score = result.get('score', 0)
        method = result.get('evaluation_method', 'N/A')
        reason = result.get('recommendation_reason', 'N/A')[:70]
        url = result.get('url', 'N/A')

        # 提取域名
        domain = 'N/A'
        if url and url != 'N/A':
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                if domain.startswith('www.'):
                    domain = domain[4:]
            except:
                domain = 'INVALID'

        # 统计
        if method != 'N/A':
            stats['with_evaluation_method'] += 1

        if method == 'MCP Tools':
            stats['mcp_tools'] += 1
        elif method == 'LLM':
            stats['llm'] += 1
        elif method == 'Rule-based':
            stats['rule_based'] += 1
        else:
            stats['unknown'] += 1

        if score >= 8.0:
            stats['high_score'] += 1
        elif score <= 3.0:
            stats['low_score'] += 1

        if 'youtube' in domain or 'youtu.be' in domain:
            stats['youtube'] += 1
        elif 'facebook' in domain:
            stats['facebook'] += 1
        elif 'instagram' in domain:
            stats['instagram'] += 1

        # 年级匹配检查
        title_lower = title.lower()
        if 'kelas 1' in title_lower or 'grade 1' in title_lower:
            if score >= 8.0:
                stats['kelas_1_high'] += 1
        elif 'kelas 6' in title_lower or 'grade 6' in title_lower:
            if score <= 3.0:
                stats['kelas_6_low'] += 1

        # 显示结果
        print(f"\n{i}. [{method}] {title}")
        print(f"   score: {score}/10")
        print(f"   URL: {url[:80]}...")
        print(f"   domain: {domain}")
        print(f"   理由: {reason}")

    # 打印统计
    print(f"\n{'=' * 80}")
    print("统计汇总")
    print(f"{'=' * 80}")
    print(f"总结果数: {stats['total']}")
    print(f"有evaluation_method字段: {stats['with_evaluation_method']} ({stats['with_evaluation_method']/stats['total']*100:.1f}%)")
    print()
    print(f"评估方法分布:")
    print(f"  MCP Tools: {stats['mcp_tools']} ({stats['mcp_tools']/stats['total']*100:.1f}%)")
    print(f"  LLM: {stats['llm']} ({stats['llm']/stats['total']*100:.1f}%)")
    print(f"  Rule-based: {stats['rule_based']} ({stats['rule_based']/stats['total']*100:.1f}%)")
    print(f"  Unknown: {stats['unknown']} ({stats['unknown']/stats['total']*100:.1f}%)")
    print()
    print(f"分数分布:")
    print(f"  高分(≥8.0): {stats['high_score']} ({stats['high_score']/stats['total']*100:.1f}%)")
    print(f"  低分(≤3.0): {stats['low_score']} ({stats['low_score']/stats['total']*100:.1f}%)")
    print()
    print(f"URL域名分布:")
    print(f"  YouTube: {stats['youtube']}")
    print(f"  Facebook: {stats['facebook']}")
    print(f"  Instagram: {stats['instagram']}")
    print()
    print(f"年级匹配准确性:")
    print(f"  Kelas 1 高分率: {stats['kelas_1_high']} 个 (预期: 100%)")
    print(f"  Kelas 6 低分率: {stats['kelas_6_low']} 个 (预期: 100%)")

    # 验证结果
    print(f"\n{'=' * 80}")
    print("验证结果")
    print(f"{'=' * 80}")

    checks = [
        {
            'name': 'evaluation_method字段存在',
            'passed': stats['with_evaluation_method'] == stats['total'],
            'expected': stats['total'],
            'actual': stats['with_evaluation_method']
        },
        {
            'name': 'MCP Tools使用率>0%',
            'passed': stats['mcp_tools'] > 0,
            'expected': '> 0',
            'actual': stats['mcp_tools']
        },
        {
            'name': 'Facebook被过滤（低分）',
            'passed': all(r.get('score', 10) <= 3.0 for r in results if 'facebook' in r.get('url', '')),
            'expected': '所有Facebook结果<=3.0分',
            'actual': f"{stats['facebook']}个结果"
        },
        {
            'name': 'Instagram被过滤（低分）',
            'passed': all(r.get('score', 10) <= 3.0 for r in results if 'instagram' in r.get('url', '')),
            'expected': '所有Instagram结果<=3.0分',
            'actual': f"{stats['instagram']}个结果"
        }
    ]

    all_passed = True
    for check in checks:
        status = "✅" if check['passed'] else "❌"
        print(f"{status} {check['name']}")
        print(f"   预期: {check['expected']}")
        print(f"   实际: {check['actual']}")
        if not check['passed']:
            all_passed = False

    print(f"\n{'=' * 80}")
    if all_passed:
        print("🎉 所有验证通过！")
    else:
        print("⚠️ 部分验证失败，需要进一步调查")
    print(f"{'=' * 80}")

    return all_passed

if __name__ == '__main__':
    success = test_batch_search_direct()
    sys.exit(0 if success else 1)
