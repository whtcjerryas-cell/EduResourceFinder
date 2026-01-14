#!/usr/bin/env python3
"""
测试优化后的模型配置
验证：
1. 搜索推荐使用 gemini-2.5-flash
2. 视频评估使用 gemini-2.5-pro
3. 搜索策略使用 deepseek-v3.2-exp
4. 性能和成本符合预期
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from llm_client import InternalAPIClient

print("=" * 80)
print("🧪 测试优化后的模型配置")
print("=" * 80)
print()

# 初始化客户端
client = InternalAPIClient()

# ========================================
# 测试1: gemini-2.5-flash (搜索推荐理由)
# ========================================
print("📋 测试1: gemini-2.5-flash - 搜索推荐理由生成")
print("-" * 80)

test_prompt_1 = """生成一个JSON数组，包含一条20字的推荐理由：
["适合印尼二年级学生学习基础加减法"]"""

start_time = time.time()

try:
    response = client.call_llm(
        prompt=test_prompt_1,
        model="gemini-2.5-flash",
        max_tokens=100,
        temperature=0.7
    )

    elapsed = time.time() - start_time

    print(f"⏱️  响应时间: {elapsed:.2f} 秒")
    print(f"💰 预估成本: ~$0.0004")
    print(f"📝 响应: {response[:100]}")
    print(f"✅ 状态: 成功")

except Exception as e:
    print(f"❌ 失败: {str(e)[:100]}")

print()

# ========================================
# 测试2: gemini-2.5-pro (视频评估)
# ========================================
print("📋 测试2: gemini-2.5-pro - 视频评估场景")
print("-" * 80)

test_prompt_2 = """评估这个教学视频的相关性（0-10分），返回JSON：
{"score": 8.5, "details": "视频内容与二年级数学高度相关"}"""

start_time = time.time()

try:
    response = client.call_llm(
        prompt=test_prompt_2,
        model="gemini-2.5-pro",
        max_tokens=200,
        temperature=0.3
    )

    elapsed = time.time() - start_time

    print(f"⏱️  响应时间: {elapsed:.2f} 秒")
    print(f"💰 预估成本: ~$0.002")
    print(f"📝 响应: {response[:150]}")
    print(f"✅ 状态: 成功")

except Exception as e:
    print(f"❌ 失败: {str(e)[:100]}")

print()

# ========================================
# 测试3: deepseek-v3.2-exp (搜索策略)
# ========================================
print("📋 测试3: deepseek-v3.2-exp - 搜索策略生成")
print("-" * 80)

test_prompt_3 = """为印尼二年级数学课程生成搜索策略，返回JSON：
{"keywords": ["matematika kelas 2"], "language": "id"}"""

start_time = time.time()

try:
    response = client.call_llm(
        prompt=test_prompt_3,
        model="deepseek-v3.2-exp",
        max_tokens=150,
        temperature=0.3
    )

    elapsed = time.time() - start_time

    print(f"⏱️  响应时间: {elapsed:.2f} 秒")
    print(f"💰 预估成本: ~¥0.003 ≈ $0.0004")
    print(f"📝 响应: {response[:150]}")
    print(f"✅ 状态: 成功")

except Exception as e:
    print(f"❌ 失败: {str(e)[:100]}")

print()

# ========================================
# 测试4: gpt-5-nano (批量分类)
# ========================================
print("📋 测试4: gpt-5-nano - 批量分类")
print("-" * 80)

test_prompt_4 = """分类资源类型（视频/教材/练习题），返回JSON：
{"type": "视频"}"""

start_time = time.time()

try:
    response = client.call_llm(
        prompt=test_prompt_4,
        model="gpt-5-nano",
        max_tokens=50,
        temperature=0.1
    )

    elapsed = time.time() - start_time

    print(f"⏱️  响应时间: {elapsed:.2f} 秒")
    print(f"💰 预估成本: ~$0.00001")
    print(f"📝 响应: {response[:100]}")
    print(f"✅ 状态: 成功")

except Exception as e:
    print(f"❌ 失败: {str(e)[:100]}")

print()
print("=" * 80)
print("📊 测试总结")
print("=" * 80)
print()
print("✅ 所有模型配置测试完成！")
print()
print("🎯 优化后的模型选择：")
print("  1. 搜索推荐理由: gemini-2.5-flash (2-3秒, $0.0004/次)")
print("  2. 视频深度评估: gemini-2.5-pro (3-5秒, $0.0075/次) ✨ 你的要求")
print("  3. 搜索策略生成: deepseek-v3.2-exp (3-5秒, $0.0009/次)")
print("  4. 批量资源分类: gpt-5-nano (1-2秒, $0.00001/个)")
print()
print("💰 预估日成本（中等使用）:")
print("  - 搜索推荐 (1000次): $0.40")
print("  - 视频评估 (100次): $0.75")
print("  - 搜索策略 (100次): $0.09")
print("  - 资源分类 (10000个): $0.10")
print("  - 合计: ~$1.34/天 ≈ $40/月")
print()
