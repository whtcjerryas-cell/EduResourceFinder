#!/usr/bin/env python3
"""
简单测试Google Custom Search API（使用测试URL验证代码逻辑）
"""

import requests
import json

def test_google_api_direct():
    """直接测试Google API（使用测试URL）"""
    print("=" * 80)
    print("测试Google Custom Search API（直接调用）")
    print("=" * 80)
    
    # 使用用户提供的测试URL
    test_url = "https://customsearch.googleapis.com/customsearch/v1?key=AIzaSyDVCPBOmCi_rMfSEyFRsBfvjOwrHWrhCyo&q=Zootopia2&cx=56e7e6dc917ed481e"
    
    print(f"\n[🔍] 测试URL: {test_url}")
    print(f"[📤] 发送请求...")
    
    try:
        response = requests.get(test_url, timeout=30)
        print(f"[📥] HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[✅] API调用成功！")
            
            # 解析结果
            if "items" in data:
                items = data["items"]
                print(f"\n[📊] 找到 {len(items)} 个结果:")
                
                for i, item in enumerate(items[:5], 1):
                    print(f"\n  [{i}] {item.get('title', 'N/A')}")
                    print(f"      URL: {item.get('link', 'N/A')}")
                    print(f"      Snippet: {item.get('snippet', 'N/A')[:100]}...")
                
                # 显示搜索信息
                if "searchInformation" in data:
                    search_info = data["searchInformation"]
                    print(f"\n[📈] 搜索统计:")
                    print(f"      总结果数: {search_info.get('totalResults', 'N/A')}")
                    print(f"      搜索时间: {search_info.get('searchTime', 'N/A')} 秒")
                
                return True
            else:
                print(f"[⚠️] 响应中没有 'items' 字段")
                print(f"[📥] 完整响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return False
        else:
            print(f"[❌] API调用失败")
            print(f"[📥] 响应内容: {response.text[:500]}")
            return False
    
    except Exception as e:
        print(f"[❌] 请求异常: {str(e)}")
        import traceback
        print(f"[🔍] 异常详情:\n{traceback.format_exc()[:500]}")
        return False


def test_search_hunter_integration():
    """测试SearchHunter集成"""
    print("\n" + "=" * 80)
    print("测试SearchHunter集成")
    print("=" * 80)
    
    import os
    import sys
    from pathlib import Path
    
    # 添加项目根目录到路径
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    from search_strategist import SearchHunter
    
    # 设置环境变量（使用测试API密钥）
    os.environ["GOOGLE_API_KEY"] = "AIzaSyDVCPBOmCi_rMfSEyFRsBfvjOwrHWrhCyo"
    os.environ["GOOGLE_CX"] = "56e7e6dc917ed481e"
    
    try:
        hunter = SearchHunter(search_engine="google")
        print("[✅] SearchHunter初始化成功")
        
        # 测试搜索
        print("\n[🔍] 测试搜索: 'Zootopia2'")
        results = hunter.search("Zootopia2", max_results=5)
        
        if results:
            print(f"[✅] 搜索成功，找到 {len(results)} 个结果:")
            for i, result in enumerate(results, 1):
                print(f"\n  [{i}] {result.title}")
                print(f"      URL: {result.url}")
                print(f"      Snippet: {result.snippet[:100]}...")
            return True
        else:
            print("[⚠️] 搜索返回空结果")
            return False
    
    except Exception as e:
        print(f"[❌] 测试失败: {str(e)}")
        import traceback
        print(f"[🔍] 异常详情:\n{traceback.format_exc()[:500]}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Google Custom Search API 集成测试")
    print("=" * 80)
    
    # 测试1: 直接API调用
    test1_result = test_google_api_direct()
    
    # 测试2: SearchHunter集成
    test2_result = test_search_hunter_integration()
    
    # 总结
    print("\n" + "=" * 80)
    print("测试结果总结")
    print("=" * 80)
    print(f"  直接API调用: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"  SearchHunter集成: {'✅ 通过' if test2_result else '❌ 失败'}")
    
    if test1_result and test2_result:
        print("\n[✅] 所有测试通过！Google搜索集成成功！")
    else:
        print("\n[⚠️] 部分测试失败，请检查配置和网络连接")





