#!/usr/bin/env python3
"""
测试 VisionClient（小豆包平台视觉API）
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.vision_client import VisionClient

def main():
    """主函数"""
    print("="*80)
    print("🧪 测试 VisionClient（小豆包平台视觉API）")
    print("="*80)
    
    # 检查 API Key
    api_key = os.getenv("XIAODOUBAO_API_KEY") or os.getenv("LINKAPI_API_KEY")
    if not api_key:
        print("❌ 错误: 未找到 XIAODOUBAO_API_KEY 或 LINKAPI_API_KEY 环境变量")
        print("💡 提示: 请在 .env 文件中设置 API Key")
        return
    
    print(f"✅ API Key 已配置（长度: {len(api_key)} 字符）")
    
    # 初始化客户端
    try:
        client = VisionClient(api_key=api_key)
        print(f"✅ VisionClient 初始化成功")
        print(f"   Base URL: {client.base_url}")
    except Exception as e:
        print(f"❌ VisionClient 初始化失败: {str(e)}")
        return
    
    # 查找测试图片
    test_image_path = project_root / "scripts" / "test_vision_image.png"
    if not test_image_path.exists():
        print(f"\n⚠️  测试图片不存在: {test_image_path}")
        print("💡 提示: 请先运行 scripts/test_vision_models.py 生成测试图片")
        return
    
    print(f"\n📸 找到测试图片: {test_image_path}")
    print(f"   文件大小: {test_image_path.stat().st_size / 1024:.2f} KB")
    
    # 测试单张图片分析
    print(f"\n{'='*80}")
    print("📤 发送视觉分析请求...")
    print(f"{'='*80}")
    
    try:
        result = client.analyze_single_image(
            image_path=str(test_image_path),
            prompt="请详细描述这张图片的内容，包括：\n1. 图片中有哪些颜色？\n2. 有哪些形状（矩形、圆形等）？\n3. 图片中有哪些文字？\n4. 整体布局如何？\n\n请尽可能详细地描述。",
            system_prompt="你是一个视觉分析专家，擅长详细描述图片内容。",
            model="gpt-4o",
            max_tokens=1000,
            temperature=0.3
        )
        
        if result["success"]:
            print(f"\n✅ 视觉分析成功！")
            print(f"\n📝 响应内容:")
            print(f"{'-'*80}")
            print(result["response"])
            print(f"{'-'*80}")
            
            if result.get("usage"):
                usage = result["usage"]
                print(f"\n📊 Token 使用情况:")
                print(f"   输入Token: {usage.get('prompt_tokens', 'N/A')}")
                print(f"   输出Token: {usage.get('completion_tokens', 'N/A')}")
                print(f"   总计Token: {usage.get('total_tokens', 'N/A')}")
        else:
            print(f"\n❌ 视觉分析失败:")
            print(f"   错误: {result.get('error', '未知错误')}")
    
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*80}")
    print("✅ 测试完成")
    print(f"{'='*80}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        import traceback
        print(f"\n\n❌ 测试失败: {str(e)}")
        traceback.print_exc()





