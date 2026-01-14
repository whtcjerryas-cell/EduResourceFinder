#!/usr/bin/env python3
"""
测试 API 端点是否正常工作
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_countries_api():
    """测试 /api/countries 端点"""
    print("="*80)
    print("测试 /api/countries")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/api/countries")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {str(e)}")
        return False

def test_config_api(country_code="ID"):
    """测试 /api/config/<country_code> 端点"""
    print("\n" + "="*80)
    print(f"测试 /api/config/{country_code}")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/api/config/{country_code}")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 开始测试 API 端点...\n")
    
    # 测试国家列表 API
    result1 = test_countries_api()
    
    # 测试配置 API
    result2 = test_config_api("ID")
    
    print("\n" + "="*80)
    if result1 and result2:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败，请检查后端日志")
    print("="*80)

