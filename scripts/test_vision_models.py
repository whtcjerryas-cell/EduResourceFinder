#!/usr/bin/env python3
"""
测试 AI Builders API 中的模型是否支持视觉输入
测试模型：Gemini 2.5 Pro, Grok-4-Fast, GPT-5
"""

import os
import json
import base64
import requests
from typing import Dict, Any, Optional
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

# 支持从 .env 文件读取环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    def load_dotenv():
        env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip().strip('"').strip("'")
    load_dotenv()


def create_test_image() -> bytes:
    """
    创建一个简单的测试图片（包含文字和图形）
    用于测试视觉模型是否能识别图片内容
    """
    # 创建一个400x300的白色背景图片
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    
    # 绘制一些图形
    # 矩形
    draw.rectangle([50, 50, 150, 100], fill='blue', outline='black', width=2)
    
    # 圆形
    draw.ellipse([200, 50, 300, 150], fill='red', outline='black', width=2)
    
    # 文字
    try:
        # 尝试使用系统字体
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except:
        font = ImageFont.load_default()
    
    draw.text((50, 150), "Test Image", fill='black', font=font)
    draw.text((50, 200), "Blue Rectangle", fill='blue', font=font)
    draw.text((200, 200), "Red Circle", fill='red', font=font)
    draw.text((50, 250), "AI Vision Test", fill='green', font=font)
    
    # 转换为bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes.getvalue()


def image_to_base64(image_bytes: bytes) -> str:
    """将图片bytes转换为base64字符串"""
    return base64.b64encode(image_bytes).decode('utf-8')


def test_model_vision(
    model_name: str,
    api_token: str,
    test_image_bytes: bytes,
    test_method: str = "array_format"
) -> Dict[str, Any]:
    """
    测试指定模型是否支持视觉输入
    
    Args:
        model_name: 模型名称
        api_token: API令牌
        test_image_bytes: 测试图片的bytes
        test_method: 测试方法 ("array_format", "base64_string", "url")
    
    Returns:
        测试结果字典
    """
    base_url = "https://space.ai-builders.com/backend"
    endpoint = f"{base_url}/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # 准备测试图片的base64编码
    image_base64 = image_to_base64(test_image_bytes)
    
    # 构建不同的请求格式
    if test_method == "array_format":
        # 方法1: OpenAI格式的多模态数组
        user_content = [
            {
                "type": "text",
                "text": "请详细描述这张图片的内容，包括颜色、形状、文字等所有细节。"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image_base64}"
                }
            }
        ]
    elif test_method == "base64_string":
        # 方法2: 直接在文本中包含base64（完整编码）
        user_content = f"""请分析以下图片（base64编码）：
data:image/png;base64,{image_base64}

请详细描述这张图片的内容，包括：
1. 图片中有哪些颜色？
2. 有哪些形状（矩形、圆形等）？
3. 图片中有哪些文字？
4. 整体布局如何？

请尽可能详细地描述。"""
    elif test_method == "url":
        # 方法3: 使用图片URL（需要先上传图片）
        user_content = "请分析这张图片：https://example.com/test.png"
    else:
        user_content = "请描述一张测试图片的内容。"
    
    # 构建消息
    messages = [
        {
            "role": "system",
            "content": "你是一个视觉分析专家，擅长详细描述图片内容。"
        },
        {
            "role": "user",
            "content": user_content
        }
    ]
    
    # GPT-5有特殊要求：temperature必须为1.0，且使用max_completion_tokens
    if model_name == "gpt-5":
        payload = {
            "model": model_name,
            "messages": messages,
            "max_completion_tokens": 1000,  # GPT-5使用max_completion_tokens
            "temperature": 1.0,  # GPT-5必须为1.0
            # GPT-5不支持tool_choice和tools参数
        }
    else:
        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.3,
            "tool_choice": "none",
            "tools": None
        }
    
    print(f"\n{'='*80}")
    print(f"🧪 测试模型: {model_name}")
    print(f"📋 测试方法: {test_method}")
    print(f"{'='*80}")
    print(f"📤 请求Payload:")
    print(f"   Model: {model_name}")
    print(f"   Messages数量: {len(messages)}")
    print(f"   User Content类型: {type(user_content).__name__}")
    if isinstance(user_content, list):
        print(f"   User Content项目数: {len(user_content)}")
        for i, item in enumerate(user_content):
            print(f"     项目{i+1}: type={item.get('type', 'N/A')}")
    else:
        print(f"   User Content长度: {len(str(user_content))} 字符")
    
    result = {
        "model": model_name,
        "test_method": test_method,
        "success": False,
        "supports_vision": False,
        "response_text": "",
        "error": None,
        "token_usage": {},
        "http_status": None,
        "raw_response": None
    }
    
    try:
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        from llm_client import get_proxy_config
        
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            params={"debug": "true"},
            timeout=60,
            proxies=get_proxy_config()
        )
        
        result["http_status"] = response.status_code
        
        print(f"\n📥 HTTP响应状态: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            result["raw_response"] = response_data
            
            # 提取响应内容
            if "choices" in response_data and len(response_data["choices"]) > 0:
                choice = response_data["choices"][0]
                message = choice.get("message", {})
                content = message.get("content", "")
                
                result["response_text"] = content
                result["success"] = True
                
                # 判断是否支持视觉（通过响应内容判断）
                # 如果模型能描述图片的具体内容（颜色、形状、文字），说明支持视觉
                vision_keywords = ["蓝色", "红色", "矩形", "圆形", "Test Image", "blue", "red", 
                                 "rectangle", "circle", "文字", "text", "图片", "image"]
                content_lower = content.lower()
                matched_keywords = [kw for kw in vision_keywords if kw.lower() in content_lower]
                
                if len(matched_keywords) >= 3:
                    result["supports_vision"] = True
                    print(f"✅ 模型响应成功，检测到视觉关键词: {matched_keywords[:5]}")
                else:
                    result["supports_vision"] = False
                    print(f"⚠️  模型响应成功，但未检测到足够的视觉关键词")
                
                # 提取token使用情况
                if "usage" in response_data:
                    result["token_usage"] = response_data["usage"]
                    usage = response_data["usage"]
                    print(f"\n📊 Token使用情况:")
                    print(f"   输入Token: {usage.get('prompt_tokens', 'N/A')}")
                    print(f"   输出Token: {usage.get('completion_tokens', 'N/A')}")
                    print(f"   总计Token: {usage.get('total_tokens', 'N/A')}")
                
                print(f"\n📝 模型响应内容:")
                print(f"{'-'*80}")
                print(content[:500])
                if len(content) > 500:
                    print(f"... (共{len(content)}字符)")
                print(f"{'-'*80}")
                
            else:
                result["error"] = "响应中缺少choices字段"
                print(f"❌ 响应格式异常: 缺少choices字段")
                print(f"响应内容: {json.dumps(response_data, indent=2, ensure_ascii=False)[:500]}")
        
        elif response.status_code == 422:
            # 验证错误，可能是格式不支持
            error_data = response.json()
            result["error"] = f"验证错误: {error_data}"
            print(f"❌ HTTP 422: 验证错误")
            print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)[:500]}")
            result["supports_vision"] = False
        
        else:
            error_text = response.text[:500] if hasattr(response, 'text') else 'N/A'
            result["error"] = f"HTTP {response.status_code}: {error_text}"
            print(f"❌ HTTP {response.status_code}: {error_text}")
            result["supports_vision"] = False
    
    except requests.exceptions.RequestException as e:
        result["error"] = str(e)
        print(f"❌ 请求异常: {str(e)}")
        result["supports_vision"] = False
    
    except Exception as e:
        result["error"] = str(e)
        print(f"❌ 未知错误: {str(e)}")
        import traceback
        traceback.print_exc()
        result["supports_vision"] = False
    
    return result


def evaluate_model_results(results: list) -> Dict[str, Any]:
    """
    对测试结果进行全方位评价
    
    Args:
        results: 测试结果列表
    
    Returns:
        评价结果字典
    """
    evaluation = {
        "summary": {},
        "detailed_comparison": [],
        "recommendations": []
    }
    
    for result in results:
        model_name = result["model"]
        model_eval = {
            "model": model_name,
            "supports_vision": result.get("supports_vision", False),
            "success": result.get("success", False),
            "response_quality": "unknown",
            "token_efficiency": "unknown",
            "error_type": result.get("error"),
            "response_length": len(result.get("response_text", "")),
            "token_usage": result.get("token_usage", {})
        }
        
        # 评价响应质量
        response_text = result.get("response_text", "")
        if response_text:
            # 检查响应是否详细
            if len(response_text) > 200:
                model_eval["response_quality"] = "detailed"
            elif len(response_text) > 50:
                model_eval["response_quality"] = "moderate"
            else:
                model_eval["response_quality"] = "brief"
            
            # 检查是否包含视觉描述
            vision_indicators = ["颜色", "形状", "文字", "图片", "矩形", "圆形", 
                               "color", "shape", "text", "image", "rectangle", "circle"]
            vision_count = sum(1 for indicator in vision_indicators if indicator.lower() in response_text.lower())
            model_eval["vision_indicators_count"] = vision_count
        
        # 评价Token效率
        token_usage = result.get("token_usage", {})
        if token_usage:
            total_tokens = token_usage.get("total_tokens", 0)
            if total_tokens > 0:
                if total_tokens < 500:
                    model_eval["token_efficiency"] = "excellent"
                elif total_tokens < 1000:
                    model_eval["token_efficiency"] = "good"
                else:
                    model_eval["token_efficiency"] = "moderate"
        
        evaluation["detailed_comparison"].append(model_eval)
    
    # 生成总结
    vision_support_count = sum(1 for r in results if r.get("supports_vision", False))
    success_count = sum(1 for r in results if r.get("success", False))
    
    evaluation["summary"] = {
        "total_models_tested": len(results),
        "models_supporting_vision": vision_support_count,
        "successful_requests": success_count,
        "best_model_for_vision": None,
        "most_cost_effective": None
    }
    
    # 找出最佳模型
    vision_models = [r for r in results if r.get("supports_vision", False)]
    if vision_models:
        # 按token使用量排序
        vision_models_sorted = sorted(
            vision_models,
            key=lambda x: x.get("token_usage", {}).get("total_tokens", float('inf'))
        )
        evaluation["summary"]["best_model_for_vision"] = vision_models_sorted[0]["model"]
    
    # 找出最经济的模型
    all_successful = [r for r in results if r.get("success", False)]
    if all_successful:
        cost_sorted = sorted(
            all_successful,
            key=lambda x: x.get("token_usage", {}).get("total_tokens", float('inf'))
        )
        evaluation["summary"]["most_cost_effective"] = cost_sorted[0]["model"]
    
    # 生成建议
    if vision_support_count == 0:
        evaluation["recommendations"].append(
            "⚠️  所有测试的模型都不支持视觉输入，建议使用外部Vision API（如Google Cloud Vision API）"
        )
    elif vision_support_count == len(results):
        evaluation["recommendations"].append(
            "✅ 所有模型都支持视觉输入，可以选择成本最低的模型"
        )
    else:
        vision_model_names = [r["model"] for r in results if r.get("supports_vision", False)]
        evaluation["recommendations"].append(
            f"✅ 以下模型支持视觉输入: {', '.join(vision_model_names)}"
        )
    
    return evaluation


def main():
    """主函数"""
    print("="*80)
    print("🧪 AI Builders 视觉模型支持测试")
    print("="*80)
    
    # 获取API Token
    api_token = os.getenv("AI_BUILDER_TOKEN")
    if not api_token:
        print("❌ 错误: 未找到 AI_BUILDER_TOKEN 环境变量")
        print("💡 提示: 请在 .env 文件中设置 AI_BUILDER_TOKEN")
        return
    
    # 创建测试图片
    print("\n📸 创建测试图片...")
    test_image_bytes = create_test_image()
    print(f"✅ 测试图片已创建，大小: {len(test_image_bytes)} bytes")
    
    # 保存测试图片（用于参考）
    test_image_path = Path(__file__).parent / "test_vision_image.png"
    with open(test_image_path, 'wb') as f:
        f.write(test_image_bytes)
    print(f"💾 测试图片已保存到: {test_image_path}")
    
    # 要测试的模型列表
    models_to_test = [
        "gemini-2.5-pro",
        "grok-4-fast",
        "gpt-5"
    ]
    
    # 测试方法（优先使用数组格式，这是OpenAI标准格式）
    test_methods = ["array_format"]  # 先测试数组格式
    
    all_results = []
    
    # 对每个模型进行测试
    for model_name in models_to_test:
        for test_method in test_methods:
            print(f"\n{'#'*80}")
            print(f"测试: {model_name} ({test_method})")
            print(f"{'#'*80}")
            
            result = test_model_vision(
                model_name=model_name,
                api_token=api_token,
                test_image_bytes=test_image_bytes,
                test_method=test_method
            )
            
            all_results.append(result)
            
            # 如果数组格式失败，尝试其他格式
            if not result.get("success") and test_method == "array_format":
                print(f"\n⚠️  数组格式失败，尝试base64字符串格式...")
                result2 = test_model_vision(
                    model_name=model_name,
                    api_token=api_token,
                    test_image_bytes=test_image_bytes,
                    test_method="base64_string"
                )
                all_results.append(result2)
    
    # 评价结果
    print("\n" + "="*80)
    print("📊 测试结果评价")
    print("="*80)
    
    evaluation = evaluate_model_results(all_results)
    
    # 打印总结
    print("\n📋 测试总结:")
    print(f"   测试模型数量: {evaluation['summary']['total_models_tested']}")
    print(f"   支持视觉的模型数: {evaluation['summary']['models_supporting_vision']}")
    print(f"   成功请求数: {evaluation['summary']['successful_requests']}")
    if evaluation['summary']['best_model_for_vision']:
        print(f"   最佳视觉模型: {evaluation['summary']['best_model_for_vision']}")
    if evaluation['summary']['most_cost_effective']:
        print(f"   最经济模型: {evaluation['summary']['most_cost_effective']}")
    
    # 打印详细比较
    print("\n📊 详细比较:")
    for model_eval in evaluation["detailed_comparison"]:
        print(f"\n   {model_eval['model']}:")
        print(f"      支持视觉: {'✅ 是' if model_eval['supports_vision'] else '❌ 否'}")
        print(f"      请求成功: {'✅ 是' if model_eval['success'] else '❌ 否'}")
        print(f"      响应质量: {model_eval['response_quality']}")
        print(f"      Token效率: {model_eval['token_efficiency']}")
        if model_eval.get('token_usage'):
            usage = model_eval['token_usage']
            print(f"      Token使用: {usage.get('prompt_tokens', 'N/A')} 输入 + {usage.get('completion_tokens', 'N/A')} 输出 = {usage.get('total_tokens', 'N/A')} 总计")
        if model_eval.get('error_type'):
            print(f"      错误: {model_eval['error_type'][:100]}")
    
    # 打印建议
    print("\n💡 建议:")
    for rec in evaluation["recommendations"]:
        print(f"   {rec}")
    
    # 保存结果到JSON文件
    output_file = Path(__file__).parent / "vision_test_results.json"
    output_data = {
        "test_image_path": str(test_image_path),
        "test_image_size_bytes": len(test_image_bytes),
        "results": all_results,
        "evaluation": evaluation
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 完整结果已保存到: {output_file}")
    print("="*80)
    
    return all_results, evaluation


if __name__ == "__main__":
    try:
        results, evaluation = main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        import traceback
        print(f"\n\n❌ 测试失败: {str(e)}")
        traceback.print_exc()

