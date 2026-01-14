#!/usr/bin/env python3
"""
测试网页评估工具
演示如何免费、无限制地评估教育资源
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from webpage_evaluator import ResourceEvaluator, evaluate_resource


def test_basic_evaluation():
    """测试基础评估功能（不依赖 LLM）"""
    print("\n" + "=" * 80)
    print("测试 1: 基础评估（规则引擎）")
    print("=" * 80)

    # 创建评估器（不使用 LLM）
    evaluator = ResourceEvaluator(use_internal_api=False)

    # 测试 YouTube 视频
    url = "https://www.youtube.com/watch?v=epHRx091W7M"

    criteria = {
        "url": url,
        "country": "伊拉克",
        "grade": "高中一年级",
        "subject": "伊斯兰教育"
    }

    result = evaluator.evaluate_youtube_resource(
        url=url,
        criteria=criteria
    )

    print(f"\n✅ 测试完成")
    print(f"最终评分: {result['final_score']}/10")
    print(f"推荐意见: {result['recommendation']}")


def test_with_llm():
    """测试使用 LLM 的深度评估"""
    print("\n" + "=" * 80)
    print("测试 2: LLM 深度评估")
    print("=" * 80)

    # 创建评估器（使用 LLM）
    try:
        evaluator = ResourceEvaluator(use_internal_api=True)

        url = "https://www.youtube.com/watch?v=epHRx091W7M"

        criteria = {
            "url": url,
            "country": "伊拉克",
            "grade": "高中一年级",
            "subject": "伊斯兰教育"
        }

        result = evaluator.evaluate_youtube_resource(
            url=url,
            criteria=criteria
        )

        print(f"\n✅ 测试完成")
        print(f"最终评分: {result['final_score']}/10")
        print(f"推荐意见: {result['recommendation']}")

    except Exception as e:
        print(f"\n⚠️ LLM 测试失败（这是正常的，如果没有配置 API）: {e}")


def test_batch_evaluation():
    """测试批量评估多个资源"""
    print("\n" + "=" * 80)
    print("测试 3: 批量评估")
    print("=" * 80)

    evaluator = ResourceEvaluator(use_internal_api=False)

    # 测试多个资源
    test_cases = [
        {
            "url": "https://www.youtube.com/watch?v=epHRx091W7M",
            "country": "伊拉克",
            "grade": "高中一年级",
            "subject": "伊斯兰教育"
        },
        {
            "url": "https://www.youtube.com/playlist?list=PLLbwDrE8zWWVLe3BCccgJLrArsNS-gWXG",
            "country": "伊拉克",
            "grade": "高中一年级",
            "subject": "伊斯兰教育"
        }
    ]

    results = []
    for i, criteria in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] 评估: {criteria['url']}")

        result = evaluator.evaluate_youtube_resource(
            url=criteria["url"],
            criteria=criteria
        )

        results.append(result)

    # 输出汇总
    print("\n" + "=" * 80)
    print("批量评估汇总")
    print("=" * 80)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['url']}")
        print(f"   评分: {result['final_score']}/10")
        print(f"   推荐: {result['recommendation']}")


def test_convenience_function():
    """测试便捷函数"""
    print("\n" + "=" * 80)
    print("测试 4: 便捷函数")
    print("=" * 80)

    result = evaluate_resource(
        url="https://www.youtube.com/watch?v=epHRx091W7M",
        country="伊拉克",
        grade="高中一年级",
        subject="伊斯兰教育"
    )

    print(f"\n✅ 测试完成")
    print(f"最终评分: {result['final_score']}/10")


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("🚀 网页评估工具 - 完整测试套件")
    print("=" * 80)

    print("\n本测试展示如何免费、无限制地评估教育资源")
    print("不需要 GLM 或其他付费平台")

    # 运行测试
    try:
        test_basic_evaluation()
        test_with_llm()
        test_batch_evaluation()
        test_convenience_function()

        print("\n" + "=" * 80)
        print("🎉 所有测试完成！")
        print("=" * 80)

        print("\n💡 使用提示:")
        print("1. 基础评估（规则引擎）完全免费，无限制使用")
        print("2. LLM 评估需要配置 API，但可以使用内部免费 API")
        print("3. 所有评估结果都会保存在 evaluation_reports/ 目录")

    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
