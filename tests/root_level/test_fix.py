#!/usr/bin/env python3
"""
快速测试脚本 - 验证API密钥修复
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_countries_api():
    """测试国家列表API（无需API密钥）"""
    print("🔍 测试 /api/countries 端点（无需API密钥）...")
    try:
        response = requests.get(f"{BASE_URL}/api/countries", timeout=5)
        print(f"   状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                countries = data.get('countries', [])
                print(f"   ✅ 成功！获取到 {len(countries)} 个国家")
                if countries:
                    print(f"   示例国家: {countries[0].get('name', 'N/A')}")
                return True
            else:
                print(f"   ❌ 失败: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"   ⚠️  无法连接到服务器（服务器可能未启动）")
        print(f"   请先运行: python3 web_app.py")
        return None
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False

def test_search_api_with_key():
    """测试搜索API（应该仍然需要API密钥）"""
    print("\n🔍 测试 /api/search 端点（无需API密钥，前端可访问）...")
    try:
        data = {
            "country": "Indonesia",
            "grade": "Grade 10",
            "subject": "Mathematics"
        }
        response = requests.post(
            f"{BASE_URL}/api/search",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   状态码: {response.status_code}")

        if response.status_code == 200:
            print("   ✅ 成功！前端可以访问搜索API")
            return True
        elif response.status_code == 401:
            print("   ❌ 失败：仍然需要API密钥（前端无法使用）")
            return False
        else:
            print(f"   ℹ️  其他状态码: {response.status_code}")
            return True

    except requests.exceptions.ConnectionError:
        print(f"   ⚠️  无法连接到服务器")
        return None
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False

def main():
    print("="*60)
    print("🚀 API密钥修复验证测试")
    print("="*60)
    print()

    # 测试国家列表API
    result1 = test_countries_api()

    # 测试搜索API
    result2 = test_search_api_with_key()

    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)

    if result1 is True:
        print("✅ /api/countries 端点修复成功")
    elif result1 is False:
        print("❌ /api/countries 端点仍有问题")
    else:
        print("⚠️  服务器未运行，无法测试")

    if result2 is True:
        print("✅ /api/search 端点前端可访问")
    elif result2 is False:
        print("❌ /api/search 端点仍需API密钥")
    else:
        print("⚠️  无法测试")

    print("\n" + "="*60)
    if result1 is True and result2 is True:
        print("🎉 所有测试通过！修复成功！")
        print("💡 现在前端应该可以正常加载国家列表和执行搜索")
        return 0
    elif result1 is False or result2 is False:
        print("⚠️  部分测试失败，需要进一步调试")
        return 1
    else:
        print("ℹ️  请先启动服务器: python3 web_app.py")
        print("   然后在另一个终端运行此测试脚本")
        return 2

if __name__ == "__main__":
    import sys
    sys.exit(main())
