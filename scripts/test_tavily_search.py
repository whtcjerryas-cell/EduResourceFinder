#!/usr/bin/env python3
"""
测试 Tavily 搜索接口
用于验证 AI Builders 后端的 Tavily 搜索功能是否正常工作
"""

import os
import json
import sys
from typing import Optional

# 支持从 .env 文件读取环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 如果没有 python-dotenv，手动读取 .env 文件
    def load_dotenv():
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip().strip('"').strip("'")
    load_dotenv()

import requests


def test_tavily_search(query: str, max_results: int = 10):
    """
    测试 Tavily 搜索接口
    
    Args:
        query: 搜索查询词
        max_results: 最大返回结果数
    """
    # 获取 API Token
    api_token = os.getenv("AI_BUILDER_TOKEN")
    if not api_token:
        print("❌ 错误: 请设置 AI_BUILDER_TOKEN 环境变量")
        print("   可以在 .env 文件中设置，或使用 export AI_BUILDER_TOKEN=your_token")
        return None
    
    # API 端点
    base_url = "https://space.ai-builders.com/backend"
    endpoint = f"{base_url}/v1/search/"
    
    # 请求头
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # 请求体（根据 OpenAPI 规范）
    payload = {
        "keywords": [query],  # Tavily API 接受关键词数组
        "max_results": min(max_results, 20)  # 限制在 1-20 之间
    }
    
    print("="*80)
    print("🧪 Tavily 搜索接口测试")
    print("="*80)
    print(f"\n📝 搜索查询: \"{query}\"")
    print(f"📊 最大结果数: {max_results}")
    print(f"🔗 API 端点: {endpoint}")
    print(f"\n📤 请求体:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print("\n" + "-"*80)
    
    try:
        # 发送请求（禁用代理）
        print("⏳ 正在发送请求...")
        proxies = {
            "http": None,
            "https": None
        }
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=30,
            proxies=proxies
        )
        
        print(f"📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n✅ 搜索成功！")
            print("\n" + "="*80)
            print("📋 原始 JSON 响应:")
            print("="*80)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 解析结果
            print("\n" + "="*80)
            print("📊 解析后的搜索结果:")
            print("="*80)
            
            if isinstance(result, dict) and "queries" in result:
                queries = result.get("queries", [])
                errors = result.get("errors", [])
                combined_answer = result.get("combined_answer")
                
                if errors:
                    print(f"\n⚠️  错误信息: {errors}")
                
                if combined_answer:
                    print(f"\n💡 综合答案: {combined_answer}")
                
                if queries:
                    for query_result in queries:
                        keyword = query_result.get("keyword", "")
                        tavily_response = query_result.get("response", {})
                        
                        print(f"\n🔍 关键词: {keyword}")
                        print(f"📦 Tavily 响应结构: {list(tavily_response.keys())}")
                        
                        # 提取结果
                        tavily_results = tavily_response.get("results", [])
                        print(f"📈 找到 {len(tavily_results)} 个结果\n")
                        
                        for i, item in enumerate(tavily_results[:max_results], 1):
                            print(f"结果 {i}:")
                            print(f"  标题: {item.get('title', 'N/A')}")
                            print(f"  URL: {item.get('url', 'N/A')}")
                            print(f"  评分: {item.get('score', 'N/A')}")
                            content = item.get('content', item.get('snippet', ''))
                            if content:
                                preview = content[:150] + "..." if len(content) > 150 else content
                                print(f"  内容预览: {preview}")
                            print()
                else:
                    print("⚠️  未找到搜索结果")
            else:
                print("⚠️  响应格式不符合预期")
                print(f"响应键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            
            return result
        else:
            print(f"\n❌ 搜索失败！")
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 请求异常: {str(e)}")
        return None
    except Exception as e:
        print(f"\n❌ 未知错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    # 默认测试查询
    test_query = "Playlist Matematika Kelas 7 Bilangan Bulat"
    
    # 如果提供了命令行参数，使用命令行参数作为查询
    if len(sys.argv) > 1:
        test_query = " ".join(sys.argv[1:])
    
    print(f"\n🎯 测试查询: {test_query}\n")
    
    # 执行测试
    result = test_tavily_search(test_query, max_results=10)
    
    if result:
        print("\n" + "="*80)
        print("✅ 测试完成！")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ 测试失败！")
        print("="*80)
        sys.exit(1)


if __name__ == "__main__":
    main()

