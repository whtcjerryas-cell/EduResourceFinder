#!/usr/bin/env python3
"""
MCP工具单元测试和集成测试

测试印尼语年级/学科识别的准确性
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from mcp_tools import (
    extract_grade_from_title,
    extract_subject_from_title,
    validate_grade_match,
    validate_url_quality,
    read_country_config
)


async def test_indonesian_grade_extraction():
    """测试印尼语年级提取"""
    print("\n" + "="*60)
    print("测试1: 印尼语年级提取")
    print("="*60)

    test_cases = [
        # (标题, 期望年级, 期望年级ID)
        ("Matematika Kelas 1 SD", "一年级", "1"),
        ("matematika Kelas 6 vol 1 LENGKAP", "六年级", "6"),
        ("Kelas 10 Fisika", "十年级", "10"),
        ("Video Pembelajaran Kelas 12", "十二年级", "12"),
        ("SD Kelas 3 - Bahasa Indonesia", "三年级", "3"),
    ]

    passed = 0
    failed = 0

    for title, expected_grade, expected_id in test_cases:
        result = await extract_grade_from_title(title, "ID")

        if result["success"]:
            data = result["data"]
            actual_grade = data["grade_name"]
            actual_id = data["grade_id"]

            if actual_grade == expected_grade and actual_id == expected_id:
                print(f"✅ PASS: {title[:50]}")
                print(f"   期望: {expected_grade} (ID: {expected_id})")
                print(f"   实际: {actual_grade} (ID: {actual_id})")
                passed += 1
            else:
                print(f"❌ FAIL: {title[:50]}")
                print(f"   期望: {expected_grade} (ID: {expected_id})")
                print(f"   实际: {actual_grade} (ID: {actual_id})")
                failed += 1
        else:
            print(f"❌ FAIL: {title[:50]}")
            print(f"   工具无法识别年级")
            failed += 1
        print()

    print(f"年级提取测试结果: {passed} 通过, {failed} 失败")
    return passed, failed


async def test_indonesian_subject_extraction():
    """测试印尼语学科提取"""
    print("\n" + "="*60)
    print("测试2: 印尼语学科提取")
    print("="*60)

    test_cases = [
        # (标题, 期望学科, 期望学科ID)
        ("Matematika Kelas 1", "数学", "math"),
        ("Fisika untuk Kelas 10", "物理", "physics"),
        ("Bahasa Indonesia SD", "印尼语", "indonesian"),
        ("Kimia SMA Kelas 11", "化学", "chemistry"),
        ("Biologi Kelas 7", "生物", "biology"),
    ]

    passed = 0
    failed = 0

    for title, expected_subject, expected_id in test_cases:
        result = await extract_subject_from_title(title, "ID")

        if result["success"]:
            data = result["data"]
            actual_subject = data["subject_name"]
            actual_id = data["subject_id"]

            if actual_subject == expected_subject and actual_id == expected_id:
                print(f"✅ PASS: {title[:50]}")
                print(f"   期望: {expected_subject} (ID: {expected_id})")
                print(f"   实际: {actual_subject} (ID: {actual_id})")
                passed += 1
            else:
                print(f"❌ FAIL: {title[:50]}")
                print(f"   期望: {expected_subject} (ID: {expected_id})")
                print(f"   实际: {actual_subject} (ID: {actual_id})")
                failed += 1
        else:
            print(f"❌ FAIL: {title[:50]}")
            print(f"   工具无法识别学科")
            failed += 1
        print()

    print(f"学科提取测试结果: {passed} 通过, {failed} 失败")
    return passed, failed


async def test_grade_match_validation():
    """测试年级匹配验证"""
    print("\n" + "="*60)
    print("测试3: 年级匹配验证")
    print("="*60)

    test_cases = [
        # (目标年级, 识别年级, 期望匹配)
        ("Kelas 1", "Kelas 1", True),
        ("Kelas 1", "Kelas 6", False),
        ("Kelas 10", "Kelas 10", True),
        ("Kelas 12", "Kelas 1", False),
        ("一年级", "Kelas 1", True),  # 中文名称匹配
        ("六年级", "Kelas 6", True),  # 中文名称匹配
    ]

    passed = 0
    failed = 0

    for target_grade, identified_grade, expected_match in test_cases:
        result = await validate_grade_match(target_grade, identified_grade, "ID")

        if result["success"]:
            data = result["data"]
            actual_match = data["match"]

            if actual_match == expected_match:
                status = "✅ PASS"
                passed += 1
            else:
                status = "❌ FAIL"
                failed += 1

            print(f"{status}: {target_grade} vs {identified_grade}")
            print(f"   期望匹配: {expected_match}")
            print(f"   实际匹配: {actual_match}")
            if not actual_match:
                print(f"   原因: {data['reason']}")
        else:
            print(f"❌ FAIL: {target_grade} vs {identified_grade}")
            print(f"   验证失败: {result.get('error', '未知错误')}")
            failed += 1
        print()

    print(f"年级匹配测试结果: {passed} 通过, {failed} 失败")
    return passed, failed


async def test_url_quality_validation():
    """测试URL质量验证"""
    print("\n" + "="*60)
    print("测试4: URL质量验证")
    print("="*60)

    test_cases = [
        # (URL, 标题, 期望质量, 期望过滤)
        ("https://www.youtube.com/watch?v=xxx", "Math Tutorial", "high", False),
        ("https://www.youtube.com/playlist?list=xxx", "Math Course", "high", False),
        ("https://www.facebook.com/groups/xxx/posts/yyy", "Video", "low", True),
        ("https://www.instagram.com/p/xxx", "Math", "low", True),
        ("https://www.twitch.tv/videos/xxx", "Gaming Stream", "low", True),
        ("https://drive.google.com/file/d/xxx", "Notes", "high", False),
    ]

    passed = 0
    failed = 0

    for url, title, expected_quality, expected_filter in test_cases:
        result = await validate_url_quality(url, title)

        if result["success"]:
            data = result["data"]
            actual_quality = data["quality"]
            actual_filter = data.get("filter", False)

            if actual_quality == expected_quality and actual_filter == expected_filter:
                print(f"✅ PASS: {url[:50]}")
                print(f"   期望: 质量={expected_quality}, 过滤={expected_filter}")
                print(f"   实际: 质量={actual_quality}, 过滤={actual_filter}")
                passed += 1
            else:
                print(f"❌ FAIL: {url[:50]}")
                print(f"   期望: 质量={expected_quality}, 过滤={expected_filter}")
                print(f"   实际: 质量={actual_quality}, 过滤={actual_filter}")
                failed += 1
        else:
            print(f"❌ FAIL: {url[:50]}")
            print(f"   验证失败")
            failed += 1
        print()

    print(f"URL质量测试结果: {passed} 通过, {failed} 失败")
    return passed, failed


async def test_excel_data_validation():
    """使用Excel数据进行验证"""
    print("\n" + "="*60)
    print("测试5: Excel数据验证（批量搜索结果）")
    print("="*60)

    try:
        import pandas as pd

        excel_file = project_root / "outputs/批量搜索_2026-01-13.xlsx"

        if not excel_file.exists():
            print(f"⚠️ Excel文件不存在: {excel_file}")
            return 0, 0

        # 读取Excel
        df = pd.read_excel(excel_file)

        print(f"读取到 {len(df)} 条搜索结果")

        # 统计错误
        errors = []
        success_count = 0

        for idx, row in df.iterrows():
            title = row.get('标题', '')
            target_grade = row.get('年级', '')
            url = row.get('链接', '')
            original_score = row.get('质量分数', 0)

            if not title or not target_grade:
                continue

            # 提取年级
            grade_result = await extract_grade_from_title(str(title), "ID")

            if grade_result["success"]:
                identified_grade_info = grade_result["data"]
                identified_grade = identified_grade_info["local_name"]

                # 验证匹配
                validation = await validate_grade_match(target_grade, identified_grade, "ID")

                if validation["success"]:
                    match_info = validation["data"]

                    if not match_info["match"]:
                        # 年级不匹配
                        errors.append({
                            'idx': idx,
                            'title': str(title)[:60],
                            'target': target_grade,
                            'identified': identified_grade,
                            'target_name': match_info['target_grade_name'],
                            'identified_name': match_info['identified_grade_name'],
                            'original_score': original_score,
                            'reason': match_info['reason']
                        })
                    else:
                        success_count += 1

            # 检查URL质量
            if url:
                url_result = await validate_url_quality(str(url), str(title))
                if url_result["success"]:
                    url_info = url_result["data"]
                    if url_info.get("filter"):
                        # 应该过滤
                        if original_score > 5.0:
                            errors.append({
                                'idx': idx,
                                'title': str(title)[:60],
                                'url': str(url)[:60],
                                'type': 'url_filter',
                                'original_score': original_score,
                                'reason': f"应该过滤（{url_info['reason']}）"
                            })

        # 输出错误统计
        print(f"\n✅ 正确匹配: {success_count} 条")
        print(f"❌ 发现问题: {len(errors)} 条\n")

        if errors:
            print("前10个问题:")
            for i, error in enumerate(errors[:10], 1):
                if error.get('type') == 'url_filter':
                    print(f"{i}. [URL过滤] {error['title']}")
                    print(f"   原始分数: {error['original_score']}")
                    print(f"   问题: {error['reason']}")
                else:
                    print(f"{i}. [年级不匹配] {error['title']}")
                    print(f"   目标: {error['target']} ({error['target_name']})")
                    print(f"   识别: {error['identified']} ({error['identified_name']})")
                    print(f"   原始分数: {error['original_score']}")
                    print(f"   原因: {error['reason']}")
                print()

        # 计算准确率
        total = success_count + len(errors)
        accuracy = success_count / total * 100 if total > 0 else 0

        print(f"\n准确率: {accuracy:.1f}% ({success_count}/{total})")

        return success_count, len(errors)

    except ImportError:
        print("⚠️ 未安装pandas，跳过Excel数据测试")
        return 0, 0
    except Exception as e:
        print(f"❌ Excel数据测试失败: {str(e)}")
        return 0, 0


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("MCP工具测试套件")
    print("="*60)

    total_passed = 0
    total_failed = 0

    # 测试1: 年级提取
    passed, failed = await test_indonesian_grade_extraction()
    total_passed += passed
    total_failed += failed

    # 测试2: 学科提取
    passed, failed = await test_indonesian_subject_extraction()
    total_passed += passed
    total_failed += failed

    # 测试3: 年级匹配验证
    passed, failed = await test_grade_match_validation()
    total_passed += passed
    total_failed += failed

    # 测试4: URL质量验证
    passed, failed = await test_url_quality_validation()
    total_passed += passed
    total_failed += failed

    # 测试5: Excel数据验证
    passed, failed = await test_excel_data_validation()
    total_passed += passed
    total_failed += failed

    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"总通过: {total_passed}")
    print(f"总失败: {total_failed}")

    if total_failed == 0:
        print("✅ 所有测试通过！")
    else:
        accuracy = total_passed / (total_passed + total_failed) * 100
        print(f"准确率: {accuracy:.1f}%")

        if accuracy >= 95:
            print("✅ 达到目标准确率（≥95%）")
        elif accuracy >= 90:
            print("⚠️ 接近目标准确率（≥90%）")
        else:
            print("❌ 未达到目标准确率")


if __name__ == "__main__":
    asyncio.run(main())
