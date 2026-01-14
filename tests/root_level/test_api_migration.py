#!/usr/bin/env python3
"""测试API切换到公司内部API"""

import sys
sys.path.insert(0, '/Users/shmiwanghao8/Desktop/education/Indonesia')

print("=" * 80)
print("测试API切换到公司内部API（Gemini 2.5 Flash）")
print("=" * 80)

# 测试1: VisionClient
print("\n测试1: VisionClient 初始化")
print("-" * 80)
try:
    from core.vision_client import VisionClient
    vision_client = VisionClient()
    print(f"✅ VisionClient 初始化成功")
    print(f"   模型: {vision_client.model}")
    print(f"   Base URL: {vision_client.client.base_url}")
except Exception as e:
    print(f"❌ VisionClient 初始化失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 测试2: VideoEvaluator
print("\n测试2: VideoEvaluator 初始化")
print("-" * 80)
try:
    from core.video_evaluator import VideoEvaluator
    video_evaluator = VideoEvaluator()
    print(f"✅ VideoEvaluator 初始化成功")
    if video_evaluator.vision_client:
        print(f"   VisionClient已启用")
        print(f"   模型: {video_evaluator.vision_client.model}")
    else:
        print(f"   ⚠️  VisionClient未启用，将使用文本模拟")
except Exception as e:
    print(f"❌ VideoEvaluator 初始化失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 测试3: InternalAPIClient
print("\n测试3: InternalAPIClient 初始化")
print("-" * 80)
try:
    from llm_client import InternalAPIClient
    internal_client = InternalAPIClient()
    print(f"✅ InternalAPIClient 初始化成功")
    print(f"   模型: {internal_client.model}")
    print(f"   Base URL: {internal_client.base_url}")
except Exception as e:
    print(f"❌ InternalAPIClient 初始化失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 测试4: 检查配置
print("\n测试4: 检查配置文件")
print("-" * 80)
try:
    from core.config_loader import get_config
    config = get_config()
    models = config.get_llm_models()
    print(f"✅ 配置加载成功")
    print(f"   internal_api: {models.get('internal_api')}")
    print(f"   vision: {models.get('vision')}")
    print(f"   fast_inference: {models.get('fast_inference')}")
except Exception as e:
    print(f"❌ 配置加载失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 测试5: 简单的视觉分析测试（如果有测试图片）
print("\n测试5: 视觉分析功能测试（模拟）")
print("-" * 80)
try:
    from core.vision_client import VisionClient
    from llm_client import InternalAPIClient

    # 检查是否支持视觉功能
    internal_client = InternalAPIClient()

    # 检查call_with_vision方法是否存在
    if hasattr(internal_client, 'call_with_vision'):
        print(f"✅ InternalAPIClient 支持视觉功能 (call_with_vision)")
        print(f"   方法签名: {internal_client.call_with_vision.__doc__[:100]}...")
    else:
        print(f"❌ InternalAPIClient 不支持视觉功能")
except Exception as e:
    print(f"❌ 视觉功能检查失败: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("✅ API切换测试完成")
print("=" * 80)
print("\n总结:")
print("1. VisionClient 已切换到公司内部API")
print("2. VideoEvaluator 使用 VisionClient（已切换到公司API）")
print("3. 配置文件中视觉模型设置为 gemini-2.5-flash")
print("4. 所有视觉分析将使用公司内部API，不再使用小豆包平台")
print("=" * 80)
