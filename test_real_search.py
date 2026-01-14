#!/usr/bin/env python3
"""
真实搜索测试脚本

测试规则搜索引擎与真实search_engine_v2的集成
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.rule_based_search import RuleBasedSearchEngine, ConfigError


def test_indonesia_real_search():
    """测试印尼真实搜索"""
    print("=" * 70)
    print("🔍 测试：印尼一年级数学真实搜索")
    print("=" * 70)

    try:
        # 初始化搜索引擎
        print("\n📦 初始化搜索引擎...")
        engine = RuleBasedSearchEngine()

        # 执行搜索
        print("\n🔎 执行搜索...")
        print("   国家: ID (印度尼西亚)")
        print("   年级: 1 (SD Kelas 1)")
        print("   学科: math (Matematika)")

        result = engine.search(
            country='ID',
            grade='1',
            subject='math',
            max_results=10
        )

        # 显示结果
        print("\n" + "=" * 70)
        print("📊 搜索结果")
        print("=" * 70)

        # 本地化信息
        info = result['localized_info']
        print(f"\n📍 本地化信息:")
        print(f"   国家代码: {info['country']}")
        print(f"   年级: {info['grade']}")
        print(f"   学科: {info['subject']}")
        print(f"   课程标准: {info['curriculum']}")
        print(f"   状态: {'✅ 支持' if info['supported'] else '❌ 不支持'}")

        # 搜索元数据
        meta = result['search_metadata']
        print(f"\n📈 搜索统计:")
        print(f"   使用查询数: {len(meta['queries_used'])}")
        print(f"   总结果数: {meta['total_found']}")
        print(f"   返回结果数: {len(result['results'])}")
        print(f"   最高分: {meta['top_score']:.1f}")
        print(f"   搜索方法: {meta['search_method']}")

        # 使用的查询
        print(f"\n🎯 使用的查询:")
        for i, query in enumerate(meta['queries_used'], 1):
            print(f"   {i}. {query}")

        # 显示结果
        print(f"\n📋 搜索结果 (按质量评分排序):")
        print("-" * 70)

        if not result['results']:
            print("   ⚠️  没有找到结果")
        else:
            for i, item in enumerate(result['results'], 1):
                print(f"\n   {i}. [{item['score']:.1f}分] {item.get('title', 'N/A')}")
                print(f"      URL: {item.get('url', 'N/A')}")
                if item.get('snippet'):
                    snippet = item['snippet'][:100] + "..." if len(item['snippet']) > 100 else item['snippet']
                    print(f"      摘要: {snippet}")
                print(f"      评分原因: {item.get('score_reason', 'N/A')}")

        # 验证结果质量
        print("\n" + "=" * 70)
        print("✅ 质量检查")
        print("=" * 70)

        quality_checks = [
            ("找到结果", len(result['results']) > 0),
            ("高分结果 (>7.0)", any(r['score'] > 7.0 for r in result['results'])),
            ("使用本地化查询", len(meta['queries_used']) > 0),
            ("包含可信域名", any('ruangguru.com' in r.get('url', '') or 'youtube.com' in r.get('url', '')
                                  for r in result['results'])),
        ]

        all_pass = True
        for check_name, passed in quality_checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")
            if not passed:
                all_pass = False

        if all_pass:
            print("\n🎉 所有质量检查通过！")
        else:
            print("\n⚠️  部分质量检查未通过")

        return result

    except ConfigError as e:
        print(f"\n❌ 配置错误: {e}")
        return None
    except Exception as e:
        print(f"\n❌ 搜索失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_different_countries():
    """测试不同国家的搜索"""
    print("\n" + "=" * 70)
    print("🌍 测试：多国搜索支持")
    print("=" * 70)

    test_cases = [
        ('ID', '1', 'math', '印度尼西亚'),
        ('SA', '1', 'math', '沙特阿拉伯 (DEFAULT配置)'),
        ('US', '1', 'math', '美国 (DEFAULT配置)'),
    ]

    results = []

    for country, grade, subject, description in test_cases:
        print(f"\n📍 测试: {description}")
        print(f"   参数: {country}, {grade}, {subject}")

        try:
            engine = RuleBasedSearchEngine()
            result = engine.search(country, grade, subject, max_results=5)

            if result['localized_info']['supported']:
                print(f"   ✅ 支持 - 找到 {len(result['results'])} 个结果")
                print(f"   🎯 本地化: {result['localized_info']['grade']} - {result['localized_info']['subject']}")
                if result['results']:
                    print(f"   ⭐ 最高分: {result['results'][0]['score']:.1f}")
                results.append((description, True, len(result['results'])))
            else:
                print(f"   ❌ 不支持 - {result['localized_info'].get('error', 'Unknown error')}")
                results.append((description, False, 0))

        except Exception as e:
            print(f"   ❌ 错误: {e}")
            results.append((description, False, 0))

    # 总结
    print("\n" + "=" * 70)
    print("📊 多国测试总结")
    print("=" * 70)

    for description, success, count in results:
        status = "✅" if success else "❌"
        print(f"   {status} {description}: {count} 个结果")


def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 70)
    print("🛡️  测试：错误处理")
    print("=" * 70)

    test_cases = [
        ("不存在的配置文件", "nonexistent.yaml", None),
        ("不支持的年级", "config/country_search_config.yaml", ('ID', '99', 'math')),
        ("不支持的学科", "config/country_search_config.yaml", ('ID', '1', 'physics')),
    ]

    for test_name, config, search_params in test_cases:
        print(f"\n🧪 测试: {test_name}")

        try:
            if search_params is None:
                # 测试配置加载错误
                engine = RuleBasedSearchEngine(config_path=config)
                print(f"   ❌ 应该抛出错误但没有")
            else:
                # 测试搜索错误
                engine = RuleBasedSearchEngine(config_path=config)
                country, grade, subject = search_params
                result = engine.search(country, grade, subject)

                if not result['localized_info']['supported']:
                    print(f"   ✅ 正确返回不支持状态")
                    print(f"   错误信息: {result['localized_info'].get('error', 'N/A')}")
                else:
                    print(f"   ⚠️  意外: 返回了支持状态")

        except ConfigError as e:
            print(f"   ✅ 正确捕获ConfigError: {e}")
        except Exception as e:
            print(f"   ⚠️  未预期的错误: {e}")


def test_configuration_validation():
    """测试配置验证"""
    print("\n" + "=" * 70)
    print("📋 测试：配置验证")
    print("=" * 70)

    try:
        engine = RuleBasedSearchEngine()

        # 检查配置结构
        print("\n🔍 检查配置文件结构:")

        if 'ID' in engine.config:
            print("   ✅ 印尼配置存在")
            id_config = engine.config['ID']
            if 'grade_1' in id_config:
                print("   ✅ grade_1 配置存在")
                if 'math' in id_config['grade_1']:
                    print("   ✅ math 配置存在")
                    math_config = id_config['grade_1']['math']

                    required_fields = ['localized_terms', 'queries', 'trusted_domains']
                    for field in required_fields:
                        if field in math_config:
                            print(f"   ✅ {field} 字段存在")
                        else:
                            print(f"   ❌ {field} 字段缺失")
                else:
                    print("   ❌ math 配置缺失")
            else:
                print("   ❌ grade_1 配置缺失")
        else:
            print("   ❌ 印尼配置缺失")

        if 'DEFAULT' in engine.config:
            print("   ✅ DEFAULT 配置存在")
        else:
            print("   ⚠️  DEFAULT 配置缺失（推荐添加）")

        print("\n🎯 印尼配置详情:")
        if 'ID' in engine.config and 'grade_1' in engine.config['ID']:
            math_config = engine.config['ID']['grade_1']['math']
            print(f"   本地化年级: {math_config['localized_terms']['grade']}")
            print(f"   本地化学科: {math_config['localized_terms']['subject']}")
            print(f"   课程标准: {math_config['localized_terms']['curriculum']}")
            print(f"   查询数量: {len(math_config['queries'])}")
            print(f"   可信域名数量: {len(math_config['trusted_domains'])}")

            print("\n   可信域名及评分:")
            for domain, score in sorted(math_config['trusted_domains'].items(), key=lambda x: -x[1]):
                print(f"      • {domain}: {score}")

    except Exception as e:
        print(f"❌ 配置验证失败: {e}")


def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("🧪 规则搜索引擎 - 真实集成测试")
    print("=" * 70)

    # 测试1：印尼真实搜索
    result = test_indonesia_real_search()

    # 测试2：多国支持
    test_different_countries()

    # 测试3：错误处理
    test_error_handling()

    # 测试4：配置验证
    test_configuration_validation()

    print("\n" + "=" * 70)
    print("✅ 所有测试完成")
    print("=" * 70)
    print("\n💡 提示:")
    print("   - 如果搜索结果不理想，可以修改 config/country_search_config.yaml")
    print("   - 调整可信域名评分和查询模板")
    print("   - 重新运行此脚本验证效果")
    print()


if __name__ == "__main__":
    main()
