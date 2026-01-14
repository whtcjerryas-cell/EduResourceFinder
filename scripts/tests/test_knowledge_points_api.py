#!/usr/bin/env python3
"""
测试知识点API
"""
import requests
import json

def test_knowledge_points_api():
    """测试知识点API"""
    base_url = "http://localhost:5000"
    
    # 测试参数
    params = {
        'country': 'ID',
        'grade': 'Kelas 1',
        'subject': 'Matematika'
    }
    
    print("="*80)
    print("🧪 测试知识点API")
    print("="*80)
    print(f"URL: {base_url}/api/knowledge_points")
    print(f"参数: {params}")
    print("="*80)
    
    try:
        response = requests.get(f"{base_url}/api/knowledge_points", params=params, timeout=10)
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\n✅ API调用成功!")
                print(f"成功: {data.get('success', False)}")
                print(f"知识点数量: {data.get('total', 0)}")
                print(f"文件: {data.get('file', 'N/A')}")
                
                if data.get('knowledge_points'):
                    print(f"\n前3个知识点:")
                    for i, point in enumerate(data['knowledge_points'][:3], 1):
                        print(f"  {i}. {point.get('topic_title_cn', 'N/A')}")
                        print(f"     章节: {point.get('chapter_title', 'N/A')}")
                        print(f"     ID: {point.get('id', 'N/A')}")
            except json.JSONDecodeError as e:
                print(f"\n❌ JSON解析失败: {e}")
                print(f"响应内容（前500字符）:")
                print(response.text[:500])
        else:
            print(f"\n❌ API调用失败!")
            print(f"响应内容（前500字符）:")
            print(response.text[:500])
            
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到服务器!")
        print("请确保Web服务器正在运行:")
        print("  python3 web_app.py")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_knowledge_points_api()





