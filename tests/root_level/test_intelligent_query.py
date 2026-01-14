#!/usr/bin/env python3
"""
测试智能查询生成器

测试用例：
1. 伊拉克 - 验证阿拉伯语输出
2. 印尼 - 验证印尼语输出
3. 中国 - 验证中文输出（向后兼容）
4. 多种输入格式 - 验证灵活性
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.intelligent_query_generator import IntelligentQueryGenerator
from config_manager import ConfigManager
from search_engine_v2 import AIBuildersClient


def test_iraq_math():
    """测试1: 伊拉克数学搜索"""
    print("\n" + "="*80)
    print("测试1: 伊拉克 - 三年级 - 数学")
    print("="*80)

    llm_client = AIBuildersClient()
    config_manager = ConfigManager()
    generator = IntelligentQueryGenerator(llm_client, config_manager)

    query = generator.generate_query(
        country="伊拉克",
        grade="三年级",
        subject="数学"
    )

    print(f"\n生成的搜索词: {query}")
    print(f"搜索词长度: {len(query)} 字符")

    # 验证是否包含阿拉伯语
    has_arabic = any('\u0600' <= c <= '\u06FF' for c in query)
    print(f"包含阿拉伯语: {has_arabic}")

    if has_arabic:
        print("✅ 测试通过：生成了阿拉伯语搜索词")
    else:
        print("❌ 测试失败：未生成阿拉伯语搜索词")

    return has_arabic


def test_indonesia_science():
    """测试2: 印尼自然科学搜索"""
    print("\n" + "="*80)
    print("测试2: 印尼 - 七年级 - 自然科学")
    print("="*80)

    llm_client = AIBuildersClient()
    config_manager = ConfigManager()
    generator = IntelligentQueryGenerator(llm_client, config_manager)

    query = generator.generate_query(
        country="印尼",
        grade="七年级",
        subject="自然科学"
    )

    print(f"\n生成的搜索词: {query}")
    print(f"搜索词长度: {len(query)} 字符")

    # 验证是否包含印尼语特征
    has_indonesian = any(keyword in query.lower() for keyword in ['kelas', 'ipa', 'playlist', 'lengkap'])
    print(f"包含印尼语特征: {has_indonesian}")

    if has_indonesian:
        print("✅ 测试通过：生成了印尼语搜索词")
    else:
        print("❌ 测试失败：未生成印尼语搜索词")

    return has_indonesian


def test_china_math():
    """测试3: 中国数学搜索（向后兼容）"""
    print("\n" + "="*80)
    print("测试3: 中国 - 五年级 - 数学")
    print("="*80)

    llm_client = AIBuildersClient()
    config_manager = ConfigManager()
    generator = IntelligentQueryGenerator(llm_client, config_manager)

    query = generator.generate_query(
        country="中国",
        grade="五年级",
        subject="数学"
    )

    print(f"\n生成的搜索词: {query}")
    print(f"搜索词长度: {len(query)} 字符")

    # 验证是否包含中文
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in query)
    print(f"包含中文: {has_chinese}")

    if has_chinese:
        print("✅ 测试通过：生成了中文搜索词（向后兼容）")
    else:
        print("❌ 测试失败：未生成中文搜索词")

    return has_chinese


def test_multiple_input_formats():
    """测试4: 多种输入格式"""
    print("\n" + "="*80)
    print("测试4: 多种输入格式 - 伊拉克三年级数学")
    print("="*80)

    llm_client = AIBuildersClient()
    config_manager = ConfigManager()
    generator = IntelligentQueryGenerator(llm_client, config_manager)

    test_cases = [
        {
            "name": "中文输入",
            "input": ("伊拉克", "三年级", "数学")
        },
        {
            "name": "国家代码输入",
            "input": ("IQ", "Grade 3", "Math")
        },
        {
            "name": "英文国家名输入",
            "input": ("Iraq", "Third Grade", "Mathematics")
        }
    ]

    results = []

    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        print(f"  输入: {test_case['input']}")

        query = generator.generate_query(
            country=test_case['input'][0],
            grade=test_case['input'][1],
            subject=test_case['input'][2]
        )

        print(f"  输出: {query}")

        # 检查是否包含阿拉伯语
        has_arabic = any('\u0600' <= c <= '\u06FF' for c in query)
        results.append(has_arabic)

        if has_arabic:
            print(f"  ✅ 包含阿拉伯语")
        else:
            print(f"  ❌ 未包含阿拉伯语")

    all_passed = all(results)
    if all_passed:
        print("\n✅ 测试通过：所有输入格式都生成了阿拉伯语搜索词")
    else:
        print("\n⚠️ 部分测试失败：某些输入格式未生成阿拉伯语搜索词")

    return all_passed


def main():
    """运行所有测试"""
    print("\n" + "🧪"*40)
    print("智能查询生成器测试套件")
    print("🧪"*40)

    results = []

    try:
        results.append(("伊拉克数学", test_iraq_math()))
    except Exception as e:
        print(f"\n❌ 测试1异常: {str(e)}")
        results.append(("伊拉克数学", False))

    try:
        results.append(("印尼科学", test_indonesia_science()))
    except Exception as e:
        print(f"\n❌ 测试2异常: {str(e)}")
        results.append(("印尼科学", False))

    try:
        results.append(("中国数学", test_china_math()))
    except Exception as e:
        print(f"\n❌ 测试3异常: {str(e)}")
        results.append(("中国数学", False))

    try:
        results.append(("多种输入格式", test_multiple_input_formats()))
    except Exception as e:
        print(f"\n❌ 测试4异常: {str(e)}")
        results.append(("多种输入格式", False))

    # 汇总结果
    print("\n" + "="*80)
    print("测试结果汇总")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
