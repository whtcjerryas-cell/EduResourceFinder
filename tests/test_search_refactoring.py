#!/usr/bin/env python3
"""
测试 search() 方法重构后的功能

验证策略模式实现是否正常工作
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_strategy_import():
    """测试 1: 验证策略类可以正常导入"""
    print("\n" + "="*80)
    print("测试 1: 验证策略类导入")
    print("="*80)

    try:
        from core.search_strategies import (
            SearchStrategy,
            SearchContext,
            ChineseGoogleStrategy,
            ChineseMetasoStrategy,
            ChineseBaiduStrategy,
            EnglishGoogleStrategy,
            EnglishMetasoStrategy,
            DefaultGoogleStrategy,
            DefaultTavilyStrategy,
            FallbackTavilyStrategy,
            SearchOrchestrator
        )
        print("✅ 所有策略类导入成功")
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_search_context():
    """测试 2: 验证 SearchContext 功能"""
    print("\n" + "="*80)
    print("测试 2: 验证 SearchContext 功能")
    print("="*80)

    try:
        from core.search_strategies import SearchContext

        # 创建搜索上下文
        context = SearchContext(
            google_remaining=10000,
            metaso_remaining=5000,
            tavily_remaining=1000,
            baidu_remaining=100
        )

        # 验证额度检查
        assert context.is_available('google') == True
        assert context.is_available('metaso') == True
        assert context.is_available('tavily') == True
        assert context.is_available('baidu') == True

        print(f"✅ SearchContext 功能正常")
        print(f"   - Google 剩余: {context.google_remaining:,}")
        print(f"   - Metaso 剩余: {context.metaso_remaining:,}")
        print(f"   - Tavily 剩余: {context.tavily_remaining:,}")
        print(f"   - Baidu 剩余: {context.baidu_remaining:,}")
        return True
    except Exception as e:
        print(f"❌ SearchContext 测试失败: {e}")
        return False


def test_chinese_strategy():
    """测试 3: 验证中文策略"""
    print("\n" + "="*80)
    print("测试 3: 验证中文策略")
    print("="*80)

    try:
        from core.search_strategies import ChineseGoogleStrategy, SearchContext

        strategy = ChineseGoogleStrategy()
        context = SearchContext(
            google_remaining=10000,
            metaso_remaining=5000,
            tavily_remaining=1000,
            baidu_remaining=100
        )

        # 测试中文查询
        assert strategy.can_handle("测试中文", context) == True
        print(f"✅ 中文策略识别成功: {strategy.name}")
        print(f"   - 优先级: {strategy.priority}")

        # 测试英文查询（不应处理）
        assert strategy.can_handle("test english", context) == False
        print(f"✅ 英文查询正确拒绝")

        return True
    except Exception as e:
        print(f"❌ 中文策略测试失败: {e}")
        return False


def test_english_strategy():
    """测试 4: 验证英文策略"""
    print("\n" + "="*80)
    print("测试 4: 验证英文策略")
    print("="*80)

    try:
        from core.search_strategies import EnglishGoogleStrategy, SearchContext

        strategy = EnglishGoogleStrategy()
        context = SearchContext(
            google_remaining=10000,
            metaso_remaining=5000,
            tavily_remaining=1000,
            baidu_remaining=100
        )

        # 测试英文查询
        assert strategy.can_handle("test english query", context) == True
        print(f"✅ 英文策略识别成功: {strategy.name}")
        print(f"   - 优先级: {strategy.priority}")

        # 测试中文查询（不应处理）
        assert strategy.can_handle("测试中文", context) == False
        print(f"✅ 中文查询正确拒绝")

        return True
    except Exception as e:
        print(f"❌ 英文策略测试失败: {e}")
        return False


def test_orchestrator_initialization():
    """测试 5: 验证 SearchOrchestrator 初始化"""
    print("\n" + "="*80)
    print("测试 5: 验证 SearchOrchestrator 初始化")
    print("="*80)

    try:
        from core.search_strategies import SearchOrchestrator

        orchestrator = SearchOrchestrator()

        # 验证策略已加载并按优先级排序
        assert len(orchestrator.strategies) > 0
        print(f"✅ SearchOrchestrator 初始化成功")
        print(f"   - 已加载策略数量: {len(orchestrator.strategies)}")

        # 验证优先级排序
        priorities = [s.priority for s in orchestrator.strategies]
        assert priorities == sorted(priorities)
        print(f"✅ 策略已按优先级排序")
        print(f"   - 优先级范围: {min(priorities)} - {max(priorities)}")

        # 打印所有策略
        print(f"\n   已加载的策略:")
        for i, strategy in enumerate(orchestrator.strategies, 1):
            print(f"   {i}. {strategy.name} (优先级: {strategy.priority})")

        return True
    except Exception as e:
        print(f"❌ SearchOrchestrator 初始化测试失败: {e}")
        return False


def test_llm_client_integration():
    """测试 6: 验证 UnifiedLLMClient 集成"""
    print("\n" + "="*80)
    print("测试 6: 验证 UnifiedLLMClient 集成")
    print("="*80)

    try:
        # 注意：这个测试需要有效的 API 配置
        # 如果 API 不可用，仅验证结构
        from llm_client import UnifiedLLMClient

        try:
            # 创建客户端实例（不调用 API）
            client = UnifiedLLMClient()
        except ValueError as e:
            # 如果因为缺少环境变量而失败，这是正常的
            if "环境变量" in str(e) or "API客户端" in str(e):
                print(f"ℹ️  UnifiedLLMClient 需要环境变量（这是正常的）")
                print(f"   - 跳过实例化测试")
            else:
                raise

        # 验证 SearchOrchestrator 已集成到类中
        import inspect
        search_source = inspect.getsource(UnifiedLLMClient.search)

        # 验证 search() 方法存在
        assert 'search_orchestrator' in search_source
        print(f"✅ UnifiedLLMClient.search() 使用策略模式")

        # 验证使用了 SearchOrchestrator
        assert 'SearchContext' in search_source
        print(f"✅ UnifiedLLMClient.search() 使用 SearchContext")

        return True
    except Exception as e:
        print(f"❌ UnifiedLLMClient 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_code_complexity_reduction():
    """测试 7: 验证代码复杂度降低"""
    print("\n" + "="*80)
    print("测试 7: 验证代码复杂度降低")
    print("="*80)

    try:
        from llm_client import UnifiedLLMClient
        import inspect

        # 获取 search() 方法源代码
        search_source = inspect.getsource(UnifiedLLMClient.search)

        # 计算代码行数
        lines = [line for line in search_source.split('\n') if line.strip() and not line.strip().startswith('#')]

        print(f"✅ search() 方法代码统计:")
        print(f"   - 总行数（含注释和空行）: {len(search_source.split(chr(10)))}")
        print(f"   - 有效代码行数: {len(lines)}")

        # 验证代码行数显著减少（从 104 行）
        assert len(lines) < 40, "代码行数应该少于 40 行"
        print(f"✅ 代码行数符合预期 (< 40 行，从原来的 104 行减少 {(104-len(lines))/104*100:.1f}%)")

        # 验证使用了 SearchOrchestrator
        assert 'search_orchestrator' in search_source
        print(f"✅ 确认使用策略模式 (search_orchestrator)")

        # 验证移除了复杂的 if-else 逻辑
        complexity_indicators = ['if is_chinese:', 'elif is_english:', 'else:', 'if google_remaining']
        complexity_count = sum(1 for indicator in complexity_indicators if indicator in search_source)

        assert complexity_count < 2, "应该移除了大部分复杂的嵌套逻辑"
        print(f"✅ 已移除复杂的嵌套逻辑")

        return True
    except Exception as e:
        print(f"❌ 代码复杂度测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("Search() 方法重构验证测试")
    print("="*80)
    print(f"\n重构目标:")
    print(f"  - 圈复杂度: >15 → <5")
    print(f"  - 代码行数: 104行 → ~20行")
    print(f"  - 可维护性: 显著提升")

    # 运行所有测试
    tests = [
        ("策略类导入", test_strategy_import),
        ("SearchContext 功能", test_search_context),
        ("中文策略", test_chinese_strategy),
        ("英文策略", test_english_strategy),
        ("SearchOrchestrator 初始化", test_orchestrator_initialization),
        ("UnifiedLLMClient 集成", test_llm_client_integration),
        ("代码复杂度降低", test_code_complexity_reduction),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试 '{name}' 执行失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 打印测试总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 所有测试通过！重构成功完成。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，需要修复。")
        return 1


if __name__ == "__main__":
    exit(main())
