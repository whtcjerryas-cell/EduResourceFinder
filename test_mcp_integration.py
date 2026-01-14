#!/usr/bin/env python3
"""
MCP工具集成测试脚本

验证实际搜索结果的质量评分
"""

import requests
import json
import sys

def test_indonesian_search():
    """测试印尼语搜索 - Grade 1 Mathematics"""

    print("=" * 60)
    print("测试1: 印尼语搜索 - 一年级数学")
    print("=" * 60)

    # API endpoint
    url = "http://localhost:5001/api/search"

    # Search parameters
    payload = {
        "query": "Kelas 1 Matematika",
        "country": "Indonesia",
        "grade": "Kelas 1",
        "subject": "Matematika",
        "search_type": "batch",
        "num_results": 10
    }

    print(f"\n发送请求到: {url}")
    print(f"搜索参数: {json.dumps(payload, indent=2, ensure_ascii=False)}")

    try:
        # Send request
        response = requests.post(url, json=payload, timeout=120)

        # Check response
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])

            print(f"\n✅ 请求成功！获取到 {len(results)} 条结果\n")

            # Analyze results
            grade_mismatches = []
            social_media_filtered = []
            high_quality_matches = []

            for idx, result in enumerate(results, 1):
                title = result.get('title', '')
                score = result.get('score', 0)
                reason = result.get('recommendation_reason', '')
                url = result.get('url', '')

                print(f"结果 {idx}:")
                print(f"  标题: {title[:60]}...")
                print(f"  分数: {score}")
                print(f"  理由: {reason[:80]}...")
                print(f"  URL: {url[:60]}...")
                print()

                # Check for grade mismatches
                if 'Kelas 6' in title or 'Kelas 10' in title or 'Kelas 12' in title:
                    if score > 5.0:
                        grade_mismatches.append({
                            'idx': idx,
                            'title': title,
                            'score': score,
                            'reason': reason
                        })
                    elif score <= 3.0:
                        high_quality_matches.append({
                            'idx': idx,
                            'title': title,
                            'score': score,
                            'reason': reason
                        })

                # Check for social media
                if any(domain in url for domain in ['facebook.com', 'instagram.com', 'twitch.tv']):
                    if score > 0.0:
                        social_media_filtered.append({
                            'idx': idx,
                            'title': title,
                            'url': url,
                            'score': score
                        })

            # Print analysis
            print("=" * 60)
            print("测试结果分析")
            print("=" * 60)

            if grade_mismatches:
                print(f"\n❌ 发现 {len(grade_mismatches)} 个年级不匹配但高分的问题:")
                for item in grade_mismatches:
                    print(f"  结果 #{item['idx']}: {item['title'][:50]}")
                    print(f"    分数: {item['score']} (应该 ≤ 3.0)")
                    print(f"    理由: {item['reason'][:60]}")
            else:
                print("\n✅ 未发现年级不匹配的问题")

            if social_media_filtered:
                print(f"\n❌ 发现 {len(social_media_filtered)} 个社交媒体未过滤:")
                for item in social_media_filtered:
                    print(f"  结果 #{item['idx']}: {item['title'][:50]}")
                    print(f"    URL: {item['url'][:50]}")
                    print(f"    分数: {item['score']} (应该是 0.0)")
            else:
                print("\n✅ 社交媒体过滤正常")

            if high_quality_matches:
                print(f"\n✅ 发现 {len(high_quality_matches)} 个正确识别的年级不匹配:")
                for item in high_quality_matches:
                    print(f"  结果 #{item['idx']}: {item['title'][:50]}")
                    print(f"    分数: {item['score']} ✅")
                    print(f"    理由: {item['reason'][:60]}")

            # Overall assessment
            print("\n" + "=" * 60)
            if not grade_mismatches and not social_media_filtered:
                print("✅ 测试通过！所有评分都符合预期")
                return True
            else:
                print("❌ 测试失败！存在评分问题")
                return False

        else:
            print(f"\n❌ 请求失败: HTTP {response.status_code}")
            print(f"响应: {response.text[:500]}")
            return False

    except requests.exceptions.Timeout:
        print("\n⏰ 请求超时（120秒）")
        return False
    except Exception as e:
        print(f"\n❌ 请求异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_indonesian_search()
    sys.exit(0 if success else 1)
