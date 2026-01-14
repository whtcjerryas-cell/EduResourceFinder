#!/usr/bin/env python3
"""直接测试不同模型的阿拉伯语理解能力"""

from openai import OpenAI
import os
import time

# API配置
API_KEY = "sk_4c34c16af4f8bb4bc102f3d1afd6439127c4d95a2912af34efcbda0"
BASE_URL = "https://hk-intra-paas.transsion.com/tranai-proxy/v1"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# 测试用例
test_cases = [
    {
        "title": "الرياضيات الصف الثاني متوسط",
        "question": "这里的年级是什么？是小学二年级还是初中二年级？",
        "correct": "初中二年级",
        "keyword": "初中"
    },
    {
        "title": "شرح رياضيات الصف الثاني عشر",
        "question": "这里的年级是什么？是二年级(Grade 2)还是十二年级(Grade 12)？",
        "correct": "十二年级",
        "keyword": "十二"
    },
    {
        "title": "رياضيات للصف الثاني ابتدائي",
        "question": "这里的年级是什么？",
        "correct": "小学二年级",
        "keyword": "小学"
    }
]

# 要测试的模型
models = [
    "gpt-5.2",
    "gemini-2.5-flash",
    "gemini-2.5-pro"
]

print("=" * 120)
print("🧪 阿拉伯语理解能力测试")
print("=" * 120)

results = {}

for model in models:
    print(f"\n{'=' * 120}")
    print(f"🤖 测试模型: {model}")
    print(f"{'=' * 120}")

    model_correct = 0
    results[model] = []

    for i, test in enumerate(test_cases, 1):
        prompt = f"""你是一个精通阿拉伯语的教育专家。请分析以下标题：

标题: {test['title']}

{test['question']}

请直接回答，并简要说明理由（不超过50字）。"""

        try:
            start = time.time()
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是教育内容分析专家，精通阿拉伯语。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=150,
                timeout=30
            )
            elapsed = time.time() - start

            answer = response.choices[0].message.content

            # 判断是否包含关键词
            is_correct = test['keyword'] in answer

            status = "✅" if is_correct else "❌"
            print(f"\n  [{i}] {test['title']}")
            print(f"  问题: {test['question']}")
            print(f"  正确答案: {test['correct']}")
            print(f"  模型回答: {answer[:80]}...")
            print(f"  {status} {'✓ 正确' if is_correct else '✗ 错误'} | 耗时: {elapsed:.2f}s")

            if is_correct:
                model_correct += 1

            results[model].append({
                "test": test['title'][:40],
                "correct": is_correct,
                "answer": answer[:100],
                "time": elapsed
            })

        except Exception as e:
            print(f"\n  [{i}] {test['title']}")
            print(f"  ❌ 错误: {str(e)[:80]}")
            results[model].append({
                "test": test['title'][:40],
                "correct": False,
                "error": str(e)[:100]
            })

    accuracy = model_correct / len(test_cases) if len(test_cases) > 0 else 0
    print(f"\n  📊 {model} 准确率: {accuracy:.1%} ({model_correct}/{len(test_cases)})")

# 总结
print("\n\n" + "=" * 120)
print("📊 测试总结")
print("=" * 120)

print(f"\n{'模型':<25} {'准确率':<10} {'正确数':<10} {'平均耗时':<10}")
print("-" * 120)

best_model = None
best_accuracy = 0

for model, tests in results.items():
    correct = sum(1 for t in tests if t.get('correct', False))
    total = len(tests)
    accuracy = correct / total if total > 0 else 0
    avg_time = sum(t.get('time', 0) for t in tests) / total

    print(f"{model:<25} {accuracy:>8.1%} {correct:>3}/{total:<6} {avg_time:>8.2f}s")

    if accuracy > best_accuracy:
        best_accuracy = accuracy
        best_model = model

print("\n" + "=" * 120)
print("💡 结论")

if best_accuracy >= 0.8:
    print(f"✅ 找到优秀模型: {best_model} (准确率 {best_accuracy:.1%})")
    print("   建议: 该模型对阿拉伯语理解能力良好，可能不需要知识库")
    print("   但要注意: 这只是3个简单测试用例，实际场景可能更复杂")
elif best_accuracy >= 0.5:
    print(f"⚠️  中等表现: {best_model} (准确率 {best_accuracy:.1%})")
    print("   建议: 该模型 + 知识库辅助 = 最佳方案")
else:
    print(f"❌ 表现不佳: 最佳模型准确率仅 {best_accuracy:.1%}")
    print("   建议: 知识库方案是必要的，当前模型对阿拉伯语理解能力不足")

print("\n" + "=" * 120)
