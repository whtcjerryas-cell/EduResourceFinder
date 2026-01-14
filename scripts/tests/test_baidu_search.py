#!/usr/bin/env python3
"""
测试百度搜索API集成
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

def test_baidu_search_client():
    """测试百度搜索客户端"""
    print("=" * 80)
    print("测试百度搜索客户端")
    print("=" * 80)
    
    baidu_api_key = os.getenv("BAIDU_API_KEY")
    baidu_secret_key = os.getenv("BAIDU_SECRET_KEY")
    
    print(f"\n[📋] 环境变量检查:")
    print(f"  BAIDU_API_KEY: {'✅ 已设置' if baidu_api_key else '❌ 未设置'}")
    print(f"  BAIDU_SECRET_KEY: {'✅ 已设置' if baidu_secret_key else '❌ 未设置'}")
    
    if not baidu_api_key or not baidu_secret_key:
        print("\n[❌] 错误: 请设置 BAIDU_API_KEY 和 BAIDU_SECRET_KEY 环境变量")
        print("   在 .env 文件中添加:")
        print("   BAIDU_API_KEY=your_api_key")
        print("   BAIDU_SECRET_KEY=your_secret_key")
        return False
    
    try:
        from baidu_search_client import BaiduSearchClient
        
        client = BaiduSearchClient()
        print("\n[✅] 百度搜索客户端初始化成功")
        
        # 测试百度搜索
        print("\n[🔍] 测试百度搜索API...")
        results = client.search_baidu("Python编程语言", max_results=5)
        
        if results:
            print(f"\n[✅] 百度搜索成功，找到 {len(results)} 个结果:")
            for i, result in enumerate(results, 1):
                print(f"\n  [{i}] {result['title']}")
                print(f"      URL: {result['url']}")
                print(f"      Snippet: {result['snippet'][:100]}...")
            return True
        else:
            print("\n[⚠️] 百度搜索返回空结果")
            return False
    
    except Exception as e:
        print(f"\n[❌] 测试失败: {str(e)}")
        import traceback
        print(f"[🔍] 异常详情:\n{traceback.format_exc()[:500]}")
        return False


def test_search_hunter():
    """测试SearchHunter集成"""
    print("\n" + "=" * 80)
    print("测试SearchHunter集成")
    print("=" * 80)
    
    baidu_api_key = os.getenv("BAIDU_API_KEY")
    baidu_secret_key = os.getenv("BAIDU_SECRET_KEY")
    
    if not baidu_api_key or not baidu_secret_key:
        print("  [⚠️] 百度搜索未配置，跳过测试")
        return False
    
    try:
        from search_strategist import SearchHunter
        
        hunter = SearchHunter(search_engine="baidu")
        print("  [✅] SearchHunter初始化成功（使用百度搜索）")
        
        results = hunter.search("playlist matematika kelas 1", max_results=5)
        
        if results:
            print(f"  [✅] 搜索成功，找到 {len(results)} 个结果:")
            for i, result in enumerate(results, 1):
                print(f"\n    [{i}] {result.title}")
                print(f"        URL: {result.url}")
                print(f"        Snippet: {result.snippet[:100]}...")
            return True
        else:
            print("  [⚠️] 搜索返回空结果")
            return False
    
    except Exception as e:
        print(f"  [❌] 测试失败: {str(e)}")
        import traceback
        print(f"  [🔍] 异常详情:\n{traceback.format_exc()[:500]}")
        return False


def test_api_types():
    """测试不同的API类型"""
    print("\n" + "=" * 80)
    print("测试不同的API类型")
    print("=" * 80)
    
    baidu_api_key = os.getenv("BAIDU_API_KEY")
    baidu_secret_key = os.getenv("BAIDU_SECRET_KEY")
    
    if not baidu_api_key or not baidu_secret_key:
        print("  [⚠️] 百度搜索未配置，跳过测试")
        return False
    
    api_types = ["baidu", "smart", "high_performance"]
    
    for api_type in api_types:
        print(f"\n  [🔍] 测试API类型: {api_type}")
        os.environ["BAIDU_SEARCH_API_TYPE"] = api_type
        
        try:
            from baidu_search_client import BaiduSearchAPIClient
            
            client = BaiduSearchAPIClient()
            results = client.search("Python编程", max_results=3)
            
            if results:
                print(f"    [✅] {api_type} API调用成功，返回 {len(results)} 个结果")
            else:
                print(f"    [⚠️] {api_type} API返回空结果")
        
        except Exception as e:
            print(f"    [❌] {api_type} API测试失败: {str(e)}")
    
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("百度搜索API集成测试")
    print("=" * 80)
    
    # 测试1: 百度搜索客户端
    test1_result = test_baidu_search_client()
    
    # 测试2: SearchHunter集成
    test2_result = test_search_hunter()
    
    # 测试3: 不同API类型
    test3_result = test_api_types()
    
    # 总结
    print("\n" + "=" * 80)
    print("测试结果总结")
    print("=" * 80)
    print(f"  百度搜索客户端: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"  SearchHunter集成: {'✅ 通过' if test2_result else '❌ 失败'}")
    print(f"  API类型测试: {'✅ 通过' if test3_result else '❌ 失败'}")
    
    if test1_result and test2_result:
        print("\n[✅] 百度搜索集成成功！")
    else:
        print("\n[⚠️] 部分测试失败，请检查配置和API密钥")


if __name__ == "__main__":
    main()





