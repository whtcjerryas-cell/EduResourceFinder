#!/usr/bin/env python3
"""
测试代理修复

验证 AI Builders API 在禁用代理后可以正常访问
"""

import os
import sys

def test_ai_builders_connection():
    """测试 AI Builders API 连接"""
    print("="*80)
    print("测试 AI Builders API 代理修复")
    print("="*80)

    # 检查环境变量
    api_token = os.getenv("AI_BUILDER_TOKEN")
    if not api_token:
        print("❌ 错误: 未设置 AI_BUILDER_TOKEN 环境变量")
        return False

    print(f"✅ AI_BUILDER_TOKEN: {'*' * 20}{api_token[-4:]}")

    try:
        from llm_client import AIBuildersAPIClient

        # 创建客户端
        client = AIBuildersAPIClient(api_token)
        print(f"✅ AIBuildersAPIClient 初始化成功")
        print(f"   Base URL: {client.base_url}")

        # 测试简单的 LLM 调用
        print("\n测试 call_llm() 方法...")
        response = client.call_llm(
            prompt="测试连接",
            system_prompt="你是一个测试助手",
            max_tokens=100,
            model="deepseek"
        )

        print(f"✅ call_llm() 调用成功")
        print(f"   响应长度: {len(response)} 字符")
        print(f"   响应内容: {response[:100]}...")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        print(f"错误堆栈:\n{traceback.format_exc()}")
        return False

def test_unified_client():
    """测试统一LLM客户端"""
    print("\n" + "="*80)
    print("测试统一LLM客户端")
    print("="*80)

    try:
        from llm_client import UnifiedLLMClient

        # 创建客户端
        client = UnifiedLLMClient()
        print(f"✅ UnifiedLLMClient 初始化成功")

        # 测试 LLM 调用
        print("\n测试 call_llm() 方法...")
        response = client.call_llm(
            prompt="测试连接",
            system_prompt="你是一个测试助手",
            max_tokens=100
        )

        print(f"✅ call_llm() 调用成功")
        print(f"   响应长度: {len(response)} 字符")
        print(f"   响应内容: {response[:100]}...")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        print(f"错误堆栈:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("\n" + "🔧"*40)
    print("代理修复验证测试")
    print("🔧"*40 + "\n")

    # 测试1: AI Builders API
    success1 = test_ai_builders_connection()

    # 测试2: 统一客户端
    success2 = test_unified_client()

    # 总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    print(f"AIBuildersAPIClient: {'✅ 通过' if success1 else '❌ 失败'}")
    print(f"UnifiedLLMClient:    {'✅ 通过' if success2 else '❌ 失败'}")

    if success1 and success2:
        print("\n✅ 所有测试通过！代理修复成功！")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败，请检查错误信息")
        sys.exit(1)
