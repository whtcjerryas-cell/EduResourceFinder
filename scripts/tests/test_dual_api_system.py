#!/usr/bin/env python3
"""
测试双API系统
验证公司内部API和AI Builders API的fallback机制
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 支持从 .env 文件读取环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    def load_dotenv():
        env_file = project_root / '.env'
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip().strip('"').strip("'")
    load_dotenv()

from llm_client import UnifiedLLMClient, InternalAPIClient, AIBuildersAPIClient


def test_unified_client():
    """测试统一LLM客户端"""
    print("=" * 80)
    print("测试统一LLM客户端")
    print("=" * 80)
    
    try:
        # 初始化统一客户端
        client = UnifiedLLMClient()
        print("\n[✅] 统一LLM客户端初始化成功")
        
        # 测试简单调用
        print("\n[🔄] 测试简单LLM调用...")
        prompt = "请用一句话介绍Python编程语言"
        system_prompt = "你是一个专业的编程教育助手。"
        
        response = client.call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=100,
            temperature=0.3,
            model="deepseek"
        )
        
        print(f"\n[✅] LLM调用成功")
        print(f"[📥] 响应: {response}")
        
        return True
    
    except Exception as e:
        print(f"\n[❌] 测试失败: {str(e)}")
        import traceback
        print(f"[❌] 异常堆栈:\n{traceback.format_exc()}")
        return False


def test_internal_api():
    """测试公司内部API（如果可用）"""
    print("\n" + "=" * 80)
    print("测试公司内部API")
    print("=" * 80)
    
    internal_api_key = os.getenv("INTERNAL_API_KEY")
    if not internal_api_key:
        print("[⚠️] 未设置 INTERNAL_API_KEY 环境变量，跳过公司内部API测试")
        return False
    
    try:
        client = InternalAPIClient(api_key=internal_api_key)
        print("\n[✅] 公司内部API客户端初始化成功")
        
        # 测试简单调用
        print("\n[🔄] 测试公司内部API调用...")
        prompt = "请用一句话介绍Python编程语言"
        system_prompt = "你是一个专业的编程教育助手。"
        
        response = client.call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=100,
            temperature=0.3
        )
        
        print(f"\n[✅] 公司内部API调用成功")
        print(f"[📥] 响应: {response}")
        
        return True
    
    except Exception as e:
        print(f"\n[⚠️] 公司内部API测试失败（可能不在内网环境）: {str(e)}")
        return False


def test_ai_builders_api():
    """测试AI Builders API"""
    print("\n" + "=" * 80)
    print("测试AI Builders API")
    print("=" * 80)
    
    ai_builder_token = os.getenv("AI_BUILDER_TOKEN")
    if not ai_builder_token:
        print("[⚠️] 未设置 AI_BUILDER_TOKEN 环境变量，跳过AI Builders API测试")
        return False
    
    try:
        client = AIBuildersAPIClient(api_token=ai_builder_token)
        print("\n[✅] AI Builders API客户端初始化成功")
        
        # 测试简单调用
        print("\n[🔄] 测试AI Builders API调用...")
        prompt = "请用一句话介绍Python编程语言"
        system_prompt = "你是一个专业的编程教育助手。"
        
        response = client.call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=100,
            temperature=0.3,
            model="deepseek"
        )
        
        print(f"\n[✅] AI Builders API调用成功")
        print(f"[📥] 响应: {response}")
        
        return True
    
    except Exception as e:
        print(f"\n[❌] AI Builders API测试失败: {str(e)}")
        import traceback
        print(f"[❌] 异常堆栈:\n{traceback.format_exc()}")
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("双API系统测试")
    print("=" * 80)
    
    # 检查环境变量
    print("\n[📋] 环境变量检查:")
    internal_api_key = os.getenv("INTERNAL_API_KEY")
    ai_builder_token = os.getenv("AI_BUILDER_TOKEN")
    
    print(f"  INTERNAL_API_KEY: {'✅ 已设置' if internal_api_key else '❌ 未设置'}")
    print(f"  AI_BUILDER_TOKEN: {'✅ 已设置' if ai_builder_token else '❌ 未设置'}")
    
    if not internal_api_key and not ai_builder_token:
        print("\n[❌] 错误: 至少需要设置一个API密钥")
        print("   - INTERNAL_API_KEY: 公司内部API密钥（可选，优先使用）")
        print("   - AI_BUILDER_TOKEN: AI Builders API令牌（必需，备用）")
        return
    
    # 运行测试
    results = {
        "统一客户端": test_unified_client(),
        "公司内部API": test_internal_api(),
        "AI Builders API": test_ai_builders_api()
    }
    
    # 输出测试结果摘要
    print("\n" + "=" * 80)
    print("测试结果摘要")
    print("=" * 80)
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    # 总结
    print("\n" + "=" * 80)
    print("总结")
    print("=" * 80)
    if results["统一客户端"]:
        print("[✅] 统一LLM客户端工作正常")
        if results["公司内部API"]:
            print("[✅] 公司内部API可用，将优先使用")
        else:
            print("[⚠️] 公司内部API不可用（可能不在内网环境），将使用AI Builders API")
        
        if results["AI Builders API"]:
            print("[✅] AI Builders API可用，作为备用API")
        else:
            print("[⚠️] AI Builders API不可用，请检查配置")
    else:
        print("[❌] 统一LLM客户端测试失败，请检查配置和网络连接")


if __name__ == "__main__":
    main()





