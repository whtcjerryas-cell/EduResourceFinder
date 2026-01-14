#!/usr/bin/env python3
"""
测试公司大模型API连接
"""

import os
import sys
import json
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from llm_client import InternalAPIClient, AIBuildersAPIClient
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_internal_api():
    """测试公司内部API"""
    print("=" * 60)
    print("🔧 测试公司内部API")
    print("=" * 60)

    api_key = os.getenv('INTERNAL_API_KEY')
    api_base = os.getenv('INTERNAL_API_BASE_URL', 'https://hk-intra-paas.transsion.com/tranai-proxy/v1')

    if not api_key:
        print("❌ 未找到 INTERNAL_API_KEY")
        return False

    print(f"✅ API Key: {api_key[:20]}...")
    print(f"✅ Base URL: {api_base}")

    try:
        # 测试gpt-4o模型
        print("\n📝 测试模型: gpt-4o")
        print("-" * 60)

        client = InternalAPIClient(api_key=api_key, base_url=api_base, model_type='internal_api')

        start_time = time.time()
        response = client.call_llm(
            prompt="请用一句话介绍印度尼西亚的首都。",
            system_prompt="你是一个友好的助手。"
        )
        elapsed_time = time.time() - start_time

        print(f"✅ 响应时间: {elapsed_time:.2f}秒")
        print(f"✅ 响应内容: {response[:100]}...")
        print(f"✅ gpt-4o 模型工作正常！")

        return True

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        print(f"❌ 错误类型: {type(e).__name__}")
        return False


def test_gemini_flash():
    """测试gemini-2.5-flash模型（快速推理）"""
    print("\n" + "=" * 60)
    print("⚡ 测试 Gemini 2.5 Flash（快速推理模型）")
    print("=" * 60)

    try:
        client = InternalAPIClient(model_type='fast_inference')

        start_time = time.time()
        response = client.call_llm(
            prompt="2 + 2 = ?",
            system_prompt="你是一个数学助手。"
        )
        elapsed_time = time.time() - start_time

        print(f"✅ 响应时间: {elapsed_time:.2f}秒")
        print(f"✅ 响应内容: {response}")
        print(f"✅ Gemini 2.5 Flash 模型工作正常！")

        return True

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        print(f"❌ 错误类型: {type(e).__name__}")
        return False


def test_vision_api():
    """测试视觉API"""
    print("\n" + "=" * 60)
    print("👁️  测试视觉API（Gemini 2.5 Flash）")
    print("=" * 60)

    try:
        from core.vision_client import VisionClient

        client = VisionClient()

        # 创建一个测试图片（1x1像素的红色图片）
        test_image_path = "/tmp/test_image.png"

        # 使用PIL创建一个简单的测试图片
        try:
            from PIL import Image
            img = Image.new('RGB', (100, 100), color='red')
            img.save(test_image_path)
            print(f"✅ 创建测试图片: {test_image_path}")
        except ImportError:
            print("⚠️  PIL未安装，跳过视觉测试")
            return True

        start_time = time.time()
        result = client.analyze_single_image(
            image_path=test_image_path,
            prompt="这张图片是什么颜色？"
        )
        elapsed_time = time.time() - start_time

        if result['success']:
            print(f"✅ 响应时间: {elapsed_time:.2f}秒")
            print(f"✅ 识别结果: {result['response']}")
            print(f"✅ 视觉API工作正常！")
            return True
        else:
            print(f"❌ 视觉API返回错误: {result['error']}")
            return False

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        print(f"❌ 错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_builders_backup():
    """测试AI Builders备用API"""
    print("\n" + "=" * 60)
    print("🔄 测试 AI Builders 备用API")
    print("=" * 60)

    token = os.getenv('AI_BUILDER_TOKEN')
    if not token:
        print("❌ 未找到 AI_BUILDER_TOKEN")
        return False

    print(f"✅ Token: {token[:20]}...")

    try:
        client = AIBuildersAPIClient(api_token=token)

        start_time = time.time()
        response = client.call_llm(
            prompt="1 + 1 = ?",
            system_prompt="你是一个数学助手。"
        )
        elapsed_time = time.time() - start_time

        print(f"✅ 响应时间: {elapsed_time:.2f}秒")
        print(f"✅ 响应内容: {response}")
        print(f"✅ AI Builders API 工作正常！")

        return True

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        print(f"❌ 错误类型: {type(e).__name__}")
        return False


def main():
    """主测试函数"""
    print("\n" + "🚀" * 30)
    print("公司大模型API连接测试")
    print("=" * 60)

    results = {
        "公司内部API (gpt-4o)": False,
        "Gemini 2.5 Flash (快速推理)": False,
        "视觉API": False,
        "AI Builders 备用API": False
    }

    # 测试1: 公司内部API - gpt-4o
    results["公司内部API (gpt-4o)"] = test_internal_api()

    # 测试2: Gemini 2.5 Flash
    results["Gemini 2.5 Flash (快速推理)"] = test_gemini_flash()

    # 测试3: 视觉API
    results["视觉API"] = test_vision_api()

    # 测试4: AI Builders备用API
    results["AI Builders 备用API"] = test_ai_builders_backup()

    # 打印总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)

    for test_name, result in results.items():
        status = "✅ 正常" if result else "❌ 失败"
        print(f"{test_name}: {status}")

    success_count = sum(results.values())
    total_count = len(results)

    print(f"\n总计: {success_count}/{total_count} 个测试通过")

    if success_count == total_count:
        print("\n🎉 所有API都工作正常！")
        return 0
    else:
        print("\n⚠️  部分API测试失败，请检查网络连接和API密钥")
        return 1


if __name__ == "__main__":
    sys.exit(main())
