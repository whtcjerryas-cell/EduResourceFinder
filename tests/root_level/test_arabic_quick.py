#!/usr/bin/env python3
"""
快速阿拉伯语理解测试
对比3个核心模型的关键用例
"""

import os
import sys
import json
import time
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

# 初始化客户端
client = OpenAI(
    api_key=os.getenv("INTERNAL_API_KEY"),
    base_url=os.getenv("INTERNAL_API_BASE_URL", "https://hk-intra-paas.transsion.com/tranai-proxy/v1")
)

# 关键测试用例
critical_tests = [
    {
        "title": "الرياضيات الصف الثاني متوسط",
        "question": "这个标题中的年级是什么？是小学二年级还是初中二年级？",
        "correct_answer": "初中二年级",
        "common_mistake": "很多模型误认为是小学二年级"
    },
    {
        "title": "شرح رياضيات الصف الثاني عشر",
        "question": "这个标题中的年级是什么？是二年级还是十二年级？",
        "correct_answer": "十二年级 (Grade 12)",
        "common_mistake": "很多模型误认为是二年级"
    },
    {
        "title": "رياضيات للصف الثاني ابتدائي",
        "question": "这个标题中的年级是什么？",
        "correct_answer": "小学二年级 (Grade 2)",
        "common_mistake": "很多模型误认为不匹配"
    }
]

# 核心模型列表（快速测试）
core_models = [
    "gpt-5.2",              # OpenAI 旗舰
    "gemini-2.5-flash",      # Gemini 快速
    "gemini-2.5-pro",        # Gemini 高质量
    "claude-3-7-sonnet@20250219",  # Claude 最新
    "qwen3-max"             # 阿里通义
]

print("=" * 100)
print("🚀 快速阿拉伯语理解测试")
print("=" * 100)

results = []

for model in core_models:
    print(f"\n{'=' * 100}")
    print(f"🤖 模型: {model}")
    print(f"{'=' * 100}")

    model_correct = 0

    for i, test in enumerate(critical_tests, 1):
        prompt = f"""你是一个多语言教育专家。请分析以下阿拉伯语标题：

标题: {test['title']}

问题: {test['question']}

请直接回答年级，并简要说明理由。"""

        try:
            start = time.time()
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是教育内容分析专家，精通阿拉伯语。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=200,
                timeout=30
            )
            elapsed = time.time() - start

            answer = response.choices[0].message.content

            # 简单判断是否正确
            correct_keywords = test['correct_answer'].replace("(", "").replace(")", "").split()
            is_correct = any(kw in answer for kw in correct_keywords)

            status = "✅" if is_correct else "❌"
            print(f"\n  [{i}] {test['title'][:60]}")
            print(f"  问题: {test['question']}")
            print(f"  正确答案: {test['correct_answer']}")
            print(f"  模型回答: {answer[:100]}...")
            print(f"  {status} {'✓ 正确' if is_correct else '✗ 错误'} | 耗时: {elapsed:.2f}s")

            if is_correct:
                model_correct += 1

            results.append({
                "model": model,
                "test": test['title'][:50],
                "correct": is_correct,
                "time": elapsed,
                "answer": answer[:200]
            })

        except Exception as e:
            print(f"\n  [{i}] {test['title'][:60]}")
            print(f"  ❌ 错误: {str(e)[:80]}")

    accuracy = model_correct / len(critical_tests)
    print(f"\n  📊 {model} 准确率: {accuracy:.1%} ({model_correct}/{len(critical_tests)})")

# 生成总结
print("\n\n" + "=" * 100)
print("📊 总结")
print("=" * 100)

print(f"\n{'模型':<35} {'准确率':<10} {'平均耗时':<10}")
print("-" * 100)

model_stats = {}
for r in results:
    if r['model'] not in model_stats:
        model_stats[r['model']] = {'correct': 0, 'total': 0, 'time': 0}
    model_stats[r['model']]['total'] += 1
    model_stats[r['model']]['time'] += r['time']
    if r['correct']:
        model_stats[r['model']]['correct'] += 1

for model, stats in model_stats.items():
    accuracy = stats['correct'] / stats['total']
    avg_time = stats['time'] / stats['total']
    print(f"{model:<35} {accuracy:>8.1%} {avg_time:>8.2f}s")

print("\n" + "=" * 100)
print("💡 结论")

best_model = max(model_stats.items(), key=lambda x: x[1]['correct'] / x[1]['total'])
best_accuracy = best_model[1]['correct'] / best_model[1]['total']

if best_accuracy >= 0.8:
    print(f"✅ 找到优秀模型: {best_model[0]} (准确率 {best_accuracy:.1%})")
    print("   建议: 优先使用此模型，可能不需要知识库辅助")
elif best_accuracy >= 0.6:
    print(f"⚠️  中等表现: {best_model[0]} (准确率 {best_accuracy:.1%})")
    print("   建议: 此模型 + 知识库辅助 = 最佳方案")
else:
    print(f"❌ 表现不佳: 最佳模型准确率仅 {best_accuracy:.1%}")
    print("   建议: 知识库方案是必要的，当前模型都不够可靠")

print("\n" + "=" * 100)
