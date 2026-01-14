#!/usr/bin/env python3
"""
Rule-based Search Engine - Usage Demo

演示如何使用基于规则的教育搜索引擎
"""

from core.rule_based_search import RuleBasedSearchEngine, ConfigError


def demo_indonesia_search():
    """演示印尼搜索"""
    print("=" * 60)
    print("演示：印尼一年级数学搜索")
    print("=" * 60)

    try:
        # 初始化搜索引擎
        engine = RuleBasedSearchEngine()

        # 模拟搜索结果（避免真实API调用）
        class MockSearchEngine:
            def search(self, query, country):
                print(f"\n🔍 查询: {query}")
                results = [
                    {
                        'url': 'https://ruangguru.com/matematika-kelas-1',
                        'title': 'Matematika SD Kelas 1 - Ruangguru',
                        'snippet': 'Belajar Matematika SD Kelas 1 dengan Kurikulum Merdeka'
                    },
                    {
                        'url': 'https://youtube.com/watch?v=example1',
                        'title': 'Kurikulum Merdeka - Matematika Kelas 1',
                        'snippet': 'Video pembelajaran matematika kelas 1 SD'
                    },
                    {
                        'url': 'https://zenius.net/matematika-sd-1',
                        'title': 'Matematika SD Kelas 1 - Zenius',
                        'snippet': 'Pembelajaran matematika SD kelas 1 lengkap'
                    },
                    {
                        'url': 'https://kemdikbud.go.id/matematika-kelas-1',
                        'title': 'Matematika Kelas 1 - Kemdikbud',
                        'snippet': 'Materi resmi Kurikulum Merdeka'
                    }
                ]
                print(f"   找到 {len(results)} 个结果")
                return results

        engine.search_engine = MockSearchEngine()

        # 执行搜索
        result = engine.search(
            country='ID',
            grade='1',
            subject='math',
            max_results=10
        )

        # 显示结果
        print("\n" + "=" * 60)
        print("搜索结果")
        print("=" * 60)

        print(f"\n📍 本地化信息:")
        print(f"   国家: {result['localized_info']['country']}")
        print(f"   年级: {result['localized_info']['grade']}")
        print(f"   学科: {result['localized_info']['subject']}")
        print(f"   课程: {result['localized_info']['curriculum']}")
        print(f"   支持: {'✅' if result['localized_info']['supported'] else '❌'}")

        print(f"\n📊 搜索元数据:")
        print(f"   查询数: {len(result['search_metadata']['queries_used'])}")
        print(f"   总结果: {result['search_metadata']['total_found']}")
        print(f"   最高分: {result['search_metadata']['top_score']:.1f}")
        print(f"   方法: {result['search_metadata']['search_method']}")

        print(f"\n🎯 使用的查询:")
        for i, q in enumerate(result['search_metadata']['queries_used'], 1):
            print(f"   {i}. {q}")

        print(f"\n📋 排序后的结果:")
        for i, r in enumerate(result['results'], 1):
            print(f"\n   {i}. [{r['score']:.1f}分] {r['title']}")
            print(f"      URL: {r['url']}")
            print(f"      评分: {r['score_reason']}")

    except ConfigError as e:
        print(f"❌ 配置错误: {e}")
    except Exception as e:
        print(f"❌ 搜索失败: {e}")


def demo_unsupported_country():
    """演示不支持的国家（使用DEFAULT配置）"""
    print("\n" + "=" * 60)
    print("演示：不支持的国家（沙特阿拉伯）- 使用DEFAULT配置")
    print("=" * 60)

    try:
        engine = RuleBasedSearchEngine()

        class MockSearchEngine:
            def search(self, query, country):
                print(f"\n🔍 查询: {query}")
                return [
                    {
                        'url': 'https://youtube.com/math1',
                        'title': 'Grade 1 Mathematics',
                        'snippet': 'Mathematics for grade 1'
                    }
                ]

        engine.search_engine = MockSearchEngine()

        result = engine.search(
            country='SA',  # 沙特阿拉伯（未配置）
            grade='1',
            subject='math'
        )

        print(f"\n📍 本地化信息:")
        print(f"   国家: {result['localized_info']['country']}")
        print(f"   年级: {result['localized_info']['grade']}")
        print(f"   学科: {result['localized_info']['subject']}")
        print(f"   支持: {'✅' if result['localized_info']['supported'] else '❌'}")

        print(f"\n⚠️  注意: 沙特阿拉伯未配置，使用DEFAULT配置")

    except Exception as e:
        print(f"❌ 错误: {e}")


def demo_error_handling():
    """演示错误处理"""
    print("\n" + "=" * 60)
    print("演示：错误处理")
    print("=" * 60)

    # 测试1：配置文件不存在
    print("\n1. 测试配置文件不存在:")
    try:
        engine = RuleBasedSearchEngine(config_path="nonexistent.yaml")
    except ConfigError as e:
        print(f"   ✅ 正确捕获错误: {e}")

    # 测试2：无效的年级/学科组合
    print("\n2. 测试无效的年级/学科组合:")
    try:
        engine = RuleBasedSearchEngine()

        class MockSearchEngine:
            def search(self, query, country):
                return []

        engine.search_engine = MockSearchEngine()
        result = engine.search('ID', '99', 'physics')  # 不存在

        print(f"   ✅ 返回空结果: supported={result['localized_info']['supported']}")
        print(f"   错误信息: {result['localized_info'].get('error', 'N/A')}")
    except Exception as e:
        print(f"   ❌ 未预期的异常: {e}")


if __name__ == "__main__":
    print("\n🌟 基于规则的教育搜索引擎 - 演示\n")

    # 演示1：印尼搜索
    demo_indonesia_search()

    # 演示2：不支持的国家
    demo_unsupported_country()

    # 演示3：错误处理
    demo_error_handling()

    print("\n" + "=" * 60)
    print("演示完成")
    print("=" * 60)
    print("\n📖 使用说明:")
    print("   1. 在 config/country_search_config.yaml 添加新国家配置")
    print("   2. 调用 engine.search(country, grade, subject) 即可")
    print("   3. 10分钟添加一个新国家的配置")
    print()
