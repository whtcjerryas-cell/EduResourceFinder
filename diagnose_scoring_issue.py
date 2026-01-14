#!/usr/bin/env python3
"""
诊断评分系统问题

检查：
1. 搜索关键词是否正确
2. MCP工具评分逻辑
3. LLM评分逻辑
4. 后处理验证逻辑
5. 结果匹配逻辑
"""

import sys
import json
from typing import Dict, Any

def diagnose_search_query():
    """诊断搜索查询生成"""
    print("=" * 80)
    print("诊断1: 搜索查询生成")
    print("=" * 80)

    # 模拟搜索参数
    params = {
        'country': 'ID',
        'grade': 'Kelas 1 / 一年级',
        'subject': 'Matematika / 数学',
        'language_code': 'id'
    }

    print(f"搜索参数: {json.dumps(params, indent=2, ensure_ascii=False)}")

    # 检查配置
    from config_manager import ConfigManager
    config = ConfigManager()

    # 读取本地化关键词
    local_keywords = config.get_localized_keywords('id')
    print(f"\n印尼语本地化关键词:")
    print(f"  playlist: {local_keywords.get('playlist', 'N/A')}")

    # 生成搜索查询
    base_query = f"{params['subject'].split('/')[0].strip()} {params['grade'].split('/')[0].strip()}"
    playlist_query = f"{base_query} playlist lengkap"

    print(f"\n生成的搜索查询:")
    print(f"  基础: {base_query}")
    print(f"  完整: {playlist_query}")

    return playlist_query


def diagnose_mcp_scoring():
    """诊断MCP工具评分"""
    print("\n" + "=" * 80)
    print("诊断2: MCP工具评分逻辑")
    print("=" * 80)

    from mcp_tools.validation_tools import validate_url_quality
    import asyncio

    # 测试案例
    test_cases = [
        {
            'title': 'Rivian News, Latest Software Updates, Rivian Rumors and Tips',
            'url': 'https://www.rivianwave.com/',
            'expected_score': 0.0,
            'expected_reason': 'blacklist或无关内容'
        },
        {
            'title': 'matematika Kelas 6 vol 1 LENGKAP',
            'url': 'https://www.youtube.com/playlist?list=PLDCfM59fEA8',
            'expected_score': 2.5,
            'expected_reason': '年级不符（六年级 vs 一年级）'
        },
        {
            'title': 'Matematika Kelas 1 SD Bab 1',
            'url': 'https://www.youtube.com/watch?v=test',
            'expected_score': 10.0,
            'expected_reason': '年级和学科完全匹配'
        }
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n测试案例 {i}: {case['title'][:60]}")
        print(f"  URL: {case['url']}")
        print(f"  预期: score={case['expected_score']}, {case['expected_reason']}")

        # 测试URL验证
        async def test_url():
            return await validate_url_quality(case['url'], case['title'])

        import threading
        result_container = [None]

        def run_test():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result_container[0] = loop.run_until_complete(test_url())
                finally:
                    loop.close()
            except Exception as e:
                result_container[0] = {'error': str(e)}

        thread = threading.Thread(target=run_test)
        thread.start()
        thread.join(timeout=5)

        url_result = result_container[0]
        if url_result and 'data' in url_result:
            quality = url_result['data'].get('quality', 'unknown')
            filter_flag = url_result['data'].get('filter', False)
            print(f"  URL验证: quality={quality}, filter={filter_flag}")


def diagnose_result_matching():
    """诊断结果匹配逻辑"""
    print("\n" + "=" * 80)
    print("诊断3: 结果匹配逻辑")
    print("=" * 80)

    import traceback
    traceback.print_stack()

    # 检查score_results函数
    from search_engine_v2 import SearchEngineV2
    import inspect

    print("\n检查SearchEngineV2.search()方法:")
    print("-" * 80)

    # 获取search方法源码
    source = inspect.getsource(SearchEngineV2.search)
    lines = source.split('\n')

    # 查找评分相关的代码
    for i, line in enumerate(lines[:100], 1):
        if 'score' in line.lower() or 'sort' in line.lower():
            print(f"  Line {i}: {line}")


def main():
    print("🔍 评分系统诊断工具")
    print("=" * 80)

    try:
        # 诊断1: 搜索查询
        query = diagnose_search_query()

        # 诊断2: MCP工具评分
        diagnose_mcp_scoring()

        # 诊断3: 结果匹配
        diagnose_result_matching()

        print("\n" + "=" * 80)
        print("诊断完成")
        print("=" * 80)
        print("\n下一步:")
        print("1. 检查上述输出，找出问题")
        print("2. 修复评分系统逻辑")
        print("3. 使用Playwright测试验证")

    except Exception as e:
        print(f"\n❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
