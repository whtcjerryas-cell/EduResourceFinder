#!/usr/bin/env python3
"""
测试公司内部API支持的模型，找出适合快速评估的模型
测试内容：
1. 列出所有可用模型
2. 测试每个模型的响应速度
3. 推荐适合搜索评估的快速模型
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from llm_client import InternalAPIClient, AIBuildersAPIClient, UnifiedLLMClient

# 测试提示词（搜索推荐理由生成场景）
TEST_PROMPT = """请为以下搜索结果生成简洁的推荐理由（20-50字）：

标题: 二年级数学加减法教学视频
描述: 这个视频适合印尼二年级学生学习数学

请返回一个JSON数组格式：
["推荐理由"]
"""

# 简化测试提示词（更短，用于快速测试）
QUICK_TEST_PROMPT = """生成一个JSON数组，包含一条20字的推荐理由：
["适合印尼二年级学生学习基础加减法"]"""


def test_internal_api_models():
    """测试公司内部API支持的模型"""
    print("=" * 80)
    print("🏢 测试公司内部API模型")
    print("=" * 80)
    print()

    # 可能的模型列表（根据OpenAI兼容接口）
    # 重点测试可能较快的模型
    models_to_test = [
        "gpt-4o-mini",      # 轻量版GPT-4o（通常最快）
        "gpt-4o",           # 当前默认
        "gpt-3.5-turbo",    # GPT-3.5 Turbo（经典快速模型）
    ]

    results = []

    for model in models_to_test:
        print(f"\n🧪 测试模型: {model}")
        print("-" * 60)

        try:
            client = InternalAPIClient()

            start_time = time.time()

            response = client.call_llm(
                prompt=QUICK_TEST_PROMPT,
                max_tokens=100,
                temperature=0.3,
                model=model
            )

            elapsed_time = time.time() - start_time

            print(f"✅ 成功！响应时间: {elapsed_time:.2f} 秒")
            print(f"📝 响应内容: {response[:100]}...")

            results.append({
                "model": model,
                "success": True,
                "time": elapsed_time,
                "response_length": len(response)
            })

        except Exception as e:
            print(f"❌ 失败: {str(e)[:100]}")
            results.append({
                "model": model,
                "success": False,
                "error": str(e)[:100]
            })

    # 结果汇总
    print("\n" + "=" * 80)
    print("📊 公司内部API模型测试结果")
    print("=" * 80)
    print()

    successful = [r for r in results if r['success']]
    if successful:
        print("✅ 成功的模型:")
        successful_sorted = sorted(successful, key=lambda x: x['time'])
        for i, r in enumerate(successful_sorted, 1):
            speed_icon = "🚀" if r['time'] < 5 else "⚡" if r['time'] < 10 else "🐢"
            print(f"  {i}. [{speed_icon}] {r['model']:40s} - {r['time']:6.2f}秒")

    failed = [r for r in results if not r['success']]
    if failed:
        print("\n❌ 失败的模型:")
        for r in failed:
            print(f"  - {r['model']}: {r['error']}")

    return results


def test_ai_builders_models():
    """测试AI Builders API支持的模型"""
    print("\n" + "=" * 80)
    print("🔧 测试AI Builders API模型")
    print("=" * 80)
    print()

    # AI Builders支持的模型 - 重点测试快速模型
    models_to_test = [
        "deepseek",         # 当前默认
        "gemini-2.0-flash-exp", # Gemini Flash 2.0（如果可用）
        "gemini-1.5-flash", # Gemini 1.5 Flash
        "grok-4-fast",      # Grok快速版
    ]

    results = []

    for model in models_to_test:
        print(f"\n🧪 测试模型: {model}")
        print("-" * 60)

        try:
            client = AIBuildersAPIClient()

            start_time = time.time()

            response = client.call_llm(
                prompt=QUICK_TEST_PROMPT,
                max_tokens=100,
                temperature=0.3,
                model=model
            )

            elapsed_time = time.time() - start_time

            print(f"✅ 成功！响应时间: {elapsed_time:.2f} 秒")
            print(f"📝 响应内容: {response[:100]}...")

            results.append({
                "model": model,
                "success": True,
                "time": elapsed_time,
                "response_length": len(response)
            })

        except Exception as e:
            print(f"❌ 失败: {str(e)[:100]}")
            results.append({
                "model": model,
                "success": False,
                "error": str(e)[:100]
            })

    # 结果汇总
    print("\n" + "=" * 80)
    print("📊 AI Builders API模型测试结果")
    print("=" * 80)
    print()

    successful = [r for r in results if r['success']]
    if successful:
        print("✅ 成功的模型:")
        successful_sorted = sorted(successful, key=lambda x: x['time'])
        for i, r in enumerate(successful_sorted, 1):
            speed_icon = "🚀" if r['time'] < 5 else "⚡" if r['time'] < 10 else "🐢"
            print(f"  {i}. [{speed_icon}] {r['model']:40s} - {r['time']:6.2f}秒")

    failed = [r for r in results if not r['success']]
    if failed:
        print("\n❌ 失败的模型:")
        for r in failed:
            print(f"  - {r['model']}: {r['error']}")

    return results


def generate_recommendations():
    """生成推荐建议"""
    print("\n" + "=" * 80)
    print("💡 推荐建议")
    print("=" * 80)
    print()

    recommendations = [
        {
            "场景": "搜索推荐理由生成（需要快速）",
            "推荐模型": [
                "1. gemini-2.0-flash 或 gemini-1.5-flash - Gemini Flash系列专门为快速推理优化",
                "2. deepseek - 性价比高，速度较快",
                "3. gpt-4o-mini - 如果公司内部API支持，这是最快速的选择",
                "4. grok-4-fast - 代码中已有使用，应该是快速版本"
            ],
            "理由": "搜索时需要快速生成推荐理由，应该优先使用响应时间<10秒的模型"
        },
        {
            "场景": "视频深度评估（可以慢一些）",
            "推荐模型": [
                "1. gpt-4o - 视觉理解能力强",
                "2. gemini-2.5-pro - 多模态能力好",
                "3. deepseek - 备用方案"
            ],
            "理由": "深度评估对质量要求更高，可以使用更慢但更准确的模型"
        },
        {
            "场景": "搜索策略生成",
            "推荐模型": [
                "1. deepseek - 当前使用，成本效益好",
                "2. gemini-2.5-pro - 备用方案"
            ],
            "理由": "策略生成不需要视觉能力，使用文本模型即可"
        }
    ]

    for rec in recommendations:
        print(f"📌 {rec['场景']}")
        print(f"推荐模型:")
        for model in rec['推荐模型']:
            print(f"  {model}")
        print(f"理由: {rec['理由']}")
        print()


if __name__ == "__main__":
    print()
    print("🔍 开始测试可用模型...")
    print()

    # 测试公司内部API
    internal_results = test_internal_api_models()

    # 测试AI Builders API
    ai_builders_results = test_ai_builders_models()

    # 生成推荐
    generate_recommendations()

    print("=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)
    print()
    print("📝 总结:")
    print("  1. 查看上述测试结果，找到响应最快的模型")
    print("  2. 根据不同场景选择合适的模型")
    print("  3. 建议在配置文件中配置快速模型用于搜索评估")
    print()
