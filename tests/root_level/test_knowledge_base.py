#!/usr/bin/env python3
"""
测试知识库系统
验证知识库加载、检索和集成功能
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.knowledge_base_manager import KnowledgeBaseManager, get_knowledge_base_manager
from core.result_scorer import IntelligentResultScorer
import json

def test_knowledge_base_manager():
    """测试知识库管理器"""
    print("=" * 70)
    print("测试1: 知识库管理器")
    print("=" * 70)

    # 创建伊拉克知识库管理器
    kb_manager = get_knowledge_base_manager("IQ")

    print(f"\n✅ 知识库加载成功")
    print(f"   国家: {kb_manager.knowledge['metadata']['country_name']}")
    print(f"   总搜索次数: {kb_manager.knowledge['metadata']['total_searches']}")
    print(f"   平均质量分: {kb_manager.knowledge['metadata']['avg_quality_score']}")

    # 测试获取年级表达
    print(f"\n📚 测试: 获取 Grade 2 的所有表达")
    grade_variants = kb_manager.get_grade_variants("2")
    print(f"   找到 {len(grade_variants)} 个表达:")
    for variant in grade_variants:
        print(f"   - {variant}")

    # 验证关键表达
    assert "الصف الثاني" in grade_variants, "❌ 缺少阿拉伯语表达"
    assert "G2" in grade_variants, "❌ 缺少G2表达"
    print(f"\n✅ 年级表达检索正确")

    # 测试获取学科表达
    print(f"\n📚 测试: 获取 Mathematics 的所有表达")
    subject_variants = kb_manager.get_subject_variants("Mathematics")
    print(f"   找到 {len(subject_variants)} 个表达:")
    for variant in subject_variants:
        print(f"   - {variant}")

    assert "الرياضيات" in subject_variants, "❌ 缺少阿拉伯语数学表达"
    print(f"\n✅ 学科表达检索正确")

    # 测试生成评估prompt
    print(f"\n📝 测试: 生成增强的评估prompt")
    base_prompt = "你是教育资源评分专家。"
    enhanced_prompt = kb_manager.generate_evaluation_prompt(base_prompt)

    print(f"   基础prompt长度: {len(base_prompt)}")
    print(f"   增强后prompt长度: {len(enhanced_prompt)}")
    print(f"   增加了 {len(enhanced_prompt) - len(base_prompt)} 字符")

    # 验证关键内容
    assert "الصف الثاني" in enhanced_prompt, "❌ prompt中缺少阿拉伯语年级"
    assert "G2" in enhanced_prompt, "❌ prompt中缺少G2"
    assert "不是8年级" in enhanced_prompt or "Grade 2" in enhanced_prompt, "❌ prompt中缺少G2说明"
    print(f"\n✅ Prompt增强成功")

    # 导出摘要
    print(f"\n📊 知识库摘要:")
    print(kb_manager.export_summary())

    return True

def test_result_scorer_integration():
    """测试评分器与知识库的集成"""
    print("\n" + "=" * 70)
    print("测试2: 评分器集成")
    print("=" * 70)

    # 创建带知识库的评分器
    scorer = IntelligentResultScorer(country_code="IQ")

    print(f"\n✅ 评分器初始化成功（带知识库）")
    print(f"   知识库管理器: {'已加载' if scorer.kb_manager else '未加载'}")

    # 测试从知识库获取年级表达
    print(f"\n📚 测试: 从评分器获取年级表达")
    grade_variants = scorer.get_grade_variants_from_kb("2")
    print(f"   找到 {len(grade_variants)} 个表达")
    for variant in grade_variants:
        print(f"   - {variant}")

    assert len(grade_variants) > 0, "❌ 未找到年级表达"
    print(f"\n✅ 评分器可以正确从知识库获取年级表达")

    # 测试评分验证
    print(f"\n🔍 测试: 验证LLM评分")

    # 案例1: 标题包含"الصف الثاني"但LLM评为低分
    test_title_1 = "رياضيات للصف الثاني ابتدائي"
    test_score_1 = 4.5
    test_reasoning_1 = "年级不符，标题中未提及具体年级"

    is_valid, msg = scorer.validate_score_with_kb(
        test_title_1, test_score_1, test_reasoning_1, "2"
    )

    print(f"\n   案例1: {test_title_1}")
    print(f"   LLM评分: {test_score_1}, 理由: {test_reasoning_1}")
    print(f"   验证结果: {'❌ 未通过' if not is_valid else '✅ 通过'}")
    print(f"   消息: {msg}")

    assert not is_valid, "❌ 应该检测到LLM评分错误"
    print(f"\n✅ 成功检测到LLM评分错误")

    # 案例2: 标题包含"G2"但LLM说是8年级
    test_title_2 = "G2 فيديو كرتون الرياضيات"
    test_score_2 = 5.5
    test_reasoning_2 = "年级不符，标题显示为八年级"

    is_valid, msg = scorer.validate_score_with_kb(
        test_title_2, test_score_2, test_reasoning_2, "2"
    )

    print(f"\n   案例2: {test_title_2}")
    print(f"   LLM评分: {test_score_2}, 理由: {test_reasoning_2}")
    print(f"   验证结果: {'❌ 未通过' if not is_valid else '✅ 通过'}")
    print(f"   消息: {msg}")

    assert not is_valid, "❌ 应该检测到G2误解"
    print(f"\n✅ 成功检测到G2误解")

    # 案例3: 正确的评分
    test_title_3 = "جميع دروس منهاج الرياضيات الصف الثاني"
    test_score_3 = 9.5
    test_reasoning_3 = "年级和学科完全匹配"

    is_valid, msg = scorer.validate_score_with_kb(
        test_title_3, test_score_3, test_reasoning_3, "2"
    )

    print(f"\n   案例3: {test_title_3}")
    print(f"   LLM评分: {test_score_3}, 理由: {test_reasoning_3}")
    print(f"   验证结果: {'✅ 通过' if is_valid else '❌ 未通过'}")
    print(f"   消息: {msg}")

    assert is_valid, "❌ 正确评分应该通过验证"
    print(f"\n✅ 正确评分通过验证")

    return True

def test_discovery_recording():
    """测试发现和记录功能"""
    print("\n" + "=" * 70)
    print("测试3: 发现和记录")
    print("=" * 70)

    kb_manager = get_knowledge_base_manager("IQ")

    # 测试记录LLM错误
    print(f"\n📝 测试: 记录LLM错误")

    initial_mistakes = len(kb_manager.knowledge["llm_insights"]["accuracy_issues"])

    kb_manager.record_llm_mistake(
        mistake_type="test_mistake",
        example="测试错误",
        correction="测试修正",
        severity="low"
    )

    new_mistakes = len(kb_manager.knowledge["llm_insights"]["accuracy_issues"])

    assert new_mistakes == initial_mistakes + 1, "❌ 错误记录失败"
    print(f"   记录前: {initial_mistakes} 个错误")
    print(f"   记录后: {new_mistakes} 个错误")
    print(f"   ✅ LLM错误记录成功")

    # 测试添加新发现的表达
    print(f"\n🔍 测试: 添加新发现的年级表达")

    kb_manager.add_discovered_variant(
        grade="Grade 4",
        variant="الصف الرابع",
        language="arabic",
        confidence=0.95,
        source="ai"
    )

    grade_4_variants = kb_manager.get_grade_variants("4")
    assert "الصف الرابع" in grade_4_variants, "❌ 新表达添加失败"
    print(f"   新表达: الصف الرابع (Grade 4)")
    print(f"   ✅ 新表达添加成功")

    # 测试记录搜索结果
    print(f"\n📊 测试: 记录搜索结果")

    test_results = [
        {"url": "https://youtube.com/playlist?list=test1"},
        {"url": "https://youtube.com/playlist?list=test2"},
        {"url": "https://t.me/test"}
    ]

    test_quality_report = {
        "overall_quality_score": 75.0
    }

    initial_searches = kb_manager.knowledge["metadata"]["total_searches"]

    kb_manager.record_search_results(
        query="الرياضيات الصف الثاني playlist",
        results=test_results,
        quality_report=test_quality_report
    )

    new_searches = kb_manager.knowledge["metadata"]["total_searches"]
    assert new_searches == initial_searches + 1, "❌ 搜索记录失败"
    print(f"   记录前: {initial_searches} 次搜索")
    print(f"   记录后: {new_searches} 次搜索")
    print(f"   ✅ 搜索结果记录成功")

    # 保存知识库
    print(f"\n💾 测试: 保存知识库")
    kb_manager.save()
    print(f"   ✅ 知识库保存成功")

    return True

def main():
    """主测试函数"""
    print("\n" + "🚀" * 35)
    print("知识库系统测试")
    print("🚀" * 35 + "\n")

    try:
        # 测试1: 知识库管理器
        test_knowledge_base_manager()

        # 测试2: 评分器集成
        test_result_scorer_integration()

        # 测试3: 发现和记录
        test_discovery_recording()

        print("\n" + "=" * 70)
        print("✅ 所有测试通过！")
        print("=" * 70)

        print("\n📋 总结:")
        print("1. ✅ 知识库管理器可以正确加载和检索知识")
        print("2. ✅ 评分器成功集成知识库")
        print("3. ✅ LLM评分验证功能正常")
        print("4. ✅ 发现和记录功能正常")
        print("5. ✅ 知识库持久化正常")

        print("\n🎯 下一步:")
        print("- 在search_engine_v2.py中集成知识库")
        print("- 实现自动学习和优化循环")
        print("- 测试完整的搜索→评分→学习流程")

        return 0

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
