#!/usr/bin/env python3
"""
直接测试 URL 验证逻辑，查看详细的调试输出
"""
import asyncio
import sys
import os

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(__file__))

async def test_url_validation():
    """测试URL验证逻辑"""
    from mcp_tools.validation_tools import validate_url_quality
    import logging

    # 启用详细日志
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 80)
    print("URL验证测试 - Iteration 3 Debug")
    print("=" * 80)

    test_cases = [
        {
            "name": "YouTube视频 - 应该信任",
            "url": "https://www.youtube.com/watch?v=abc123",
            "title": "Matematika Kelas 1 SD"
        },
        {
            "name": "YouTube播放列表 - 应该信任并加分",
            "url": "https://www.youtube.com/playlist?list=xyz789",
            "title": "Kelas 1 Matematika Complete"
        },
        {
            "name": "youtu.be短链接 - 应该信任",
            "url": "https://youtu.be/def456",
            "title": "Mathematics Grade 1"
        },
        {
            "name": "Facebook - 应该过滤",
            "url": "https://www.facebook.com/watch/?v=xxx",
            "title": "Math Video"
        },
        {
            "name": "Instagram - 应该过滤",
            "url": "https://www.instagram.com/p/abc/",
            "title": "Math Tutorial"
        },
        {
            "name": "未知域名 - 应该返回medium",
            "url": "https://www.example-site.com/video",
            "title": "Mathematics Lesson"
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"测试 {i}/{len(test_cases)}: {test_case['name']}")
        print(f"{'=' * 80}")
        print(f"URL: {test_case['url']}")
        print(f"标题: {test_case['title']}")
        print(f"\n调用 validate_url_quality()...")
        print("-" * 80)

        result = await validate_url_quality(test_case['url'], test_case['title'])

        print(f"\n结果:")
        print(f"  success: {result.get('success')}")
        print(f"  text: {result.get('text')}")

        if result.get('data'):
            data = result['data']
            print(f"  data:")
            print(f"    quality: {data.get('quality')}")
            print(f"    reason: {data.get('reason')}")
            print(f"    filter: {data.get('filter')}")
            print(f"    score_adjustment: {data.get('score_adjustment')}")
            print(f"    domain: {data.get('domain')}")
            print(f"    matched_rule: {data.get('matched_rule')}")

        # 验证预期结果
        expected = test_case['name'].split(' - ')[1].strip() if ' - ' in test_case['name'] else None
        if expected and '应该' in expected:
            if '信任' in expected:
                assert data.get('quality') == 'high', f"❌ 失败: 应该是高质量"
                assert data.get('filter') == False, f"❌ 失败: 不应该被过滤"
                print(f"  ✅ 验证通过: YouTube正确识别为可信平台")
            elif '过滤' in expected:
                assert data.get('quality') == 'low', f"❌ 失败: 应该是低质量"
                assert data.get('filter') == True, f"❌ 失败: 应该被过滤"
                print(f"  ✅ 验证通过: 社交媒体正确识别并过滤")
            elif 'medium' in expected:
                assert data.get('quality') == 'medium', f"❌ 失败: 应该是中等质量"
                assert data.get('filter') == False, f"❌ 失败: 不应该被过滤"
                print(f"  ✅ 验证通过: 未知域名正确识别为中等质量")

    print(f"\n{'=' * 80}")
    print("所有测试完成！")
    print(f"{'=' * 80}")

if __name__ == '__main__':
    asyncio.run(test_url_validation())
