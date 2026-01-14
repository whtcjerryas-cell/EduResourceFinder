#!/usr/bin/env python3
"""测试当前模型的阿拉伯语理解能力"""

import sys
import os
sys.path.insert(0, '.')

# 检查配置
from core.config_loader import get_config
from llm_client import get_llm_client

config = get_config()
models = config.get_llm_models()

print("=" * 100)
print("🔧 当前LLM配置")
print("=" * 100)
print(f"默认模型: {models.get('internal_api', 'N/A')}")
print(f"快速推理模型: {models.get('fast_inference', 'N/A')}")
print(f"视觉模型: {models.get('vision', 'N/A')}")
print("=" * 100)

# 获取LLM客户端
client = get_llm_client()

# 关键测试用例
test_cases = [
    {
        "title": "الرياضيات الصف الثاني متوسط",
        "question": "这里的'الصف الثاني'是二年级还是十二年级？'متوسط'是什么意思？",
        "expected": "初中二年级 (متوسط = 初中)"
    },
    {
        "title": "شرح رياضيات الصف الثاني عشر",
        "question": "这里的'الصف الثاني عشر'是二年级还是十二年级？",
        "expected": "十二年级 (عشر = 十)"
    },
    {
        "title": "رياضيات للصف الثاني ابتدائي",
        "question": "这里的'الصف الثاني ابتدائي'是什么年级？",
        "expected": "小学二年级 (ابتدائي = 小学)"
    }
]

print("\n🧪 测试阿拉伯语理解能力")
print("=" * 100)

correct_count = 0

for i, test in enumerate(test_cases, 1):
    print(f"\n测试 {i}/{len(test_cases)}")
    print(f"标题: {test['title']}")
    print(f"问题: {test['question']}")
    print(f"正确答案: {test['expected']}")
    print("-" * 100)

    prompt = f"""你是一个精通阿拉伯语的教育专家。请分析以下标题：

标题: {test['title']}

{test['question']}

请直接回答，并说明理由。"""

    try:
        response = client.call_llm(
            prompt=prompt,
            max_tokens=200,
            temperature=0.0
        )

        print(f"模型回答: {response}")

        # 简单判断
        is_correct = any(kw in response for kw in test['expected'].split()[:3])
        if is_correct:
            print("✅ 正确")
            correct_count += 1
        else:
            print("❌ 错误")

    except Exception as e:
        print(f"❌ 调用失败: {str(e)[:100]}")

print("\n" + "=" * 100)
print(f"📊 总结: {correct_count}/{len(test_cases)} 正确 ({correct_count/len(test_cases):.1%})")
print("=" * 100)

if correct_count / len(test_cases) >= 0.8:
    print("✅ 模型对阿拉伯语理解能力良好，知识库可能不是必需的")
elif correct_count / len(test_cases) >= 0.5:
    print("⚠️  模型对阿拉伯语理解能力中等，知识库可作为辅助")
else:
    print("❌ 模型对阿拉伯语理解能力不足，知识库方案是必要的")
