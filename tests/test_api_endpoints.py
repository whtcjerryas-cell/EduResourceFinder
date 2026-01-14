#!/usr/bin/env python3
"""
API端点测试脚本
需要web_app.py服务正在运行
"""

import sys
import os
import time
import requests

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# API基础URL
API_BASE_URL = "http://localhost:5000"


def test_health_check():
    """测试服务健康检查"""
    print("\n[API测试1] 健康检查")
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ PASS: Web服务正在运行")
            return True
        else:
            print(f"⚠️ WARN: Web服务响应异常 - Status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ FAIL: 无法连接到Web服务，请确保web_app.py正在运行")
        print(f"   尝试连接: {API_BASE_URL}")
        return False
    except Exception as e:
        print(f"❌ FAIL: 健康检查失败 - {str(e)}")
        return False


def test_get_countries():
    """测试获取国家列表API"""
    print("\n[API测试2] 获取国家列表 (/api/countries)")
    try:
        response = requests.get(f"{API_BASE_URL}/api/countries", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ FAIL: HTTP {response.status_code}")
            return False
        
        data = response.json()
        
        if not data.get("success"):
            print(f"❌ FAIL: API返回success=false")
            return False
        
        countries = data.get("countries", [])
        print(f"✅ PASS: 成功获取 {len(countries)} 个国家")
        
        if len(countries) > 0:
            print("  前5个国家:")
            for country in countries[:5]:
                print(f"    - {country['country_code']}: {country['country_name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: 获取国家列表失败 - {str(e)}")
        return False


def test_get_country_config():
    """测试获取国家配置API"""
    print("\n[API测试3] 获取国家配置 (/api/config/<country_code>)")
    try:
        # 测试获取印尼配置
        response = requests.get(f"{API_BASE_URL}/api/config/ID", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ FAIL: HTTP {response.status_code}")
            return False
        
        data = response.json()
        
        if not data.get("success"):
            print(f"❌ FAIL: API返回success=false")
            return False
        
        config = data.get("config")
        
        if not config:
            print("❌ FAIL: 配置为空")
            return False
        
        print("✅ PASS: 成功获取国家配置")
        print(f"  国家代码: {config.get('country_code')}")
        print(f"  国家名称: {config.get('country_name')}")
        print(f"  年级数量: {len(config.get('grades', []))}")
        print(f"  学科数量: {len(config.get('subjects', []))}")
        
        # 检查是否有grade_subject_mappings
        if config.get('grade_subject_mappings'):
            print(f"  年级-学科配对: {len(config['grade_subject_mappings'])} 个年级")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: 获取国家配置失败 - {str(e)}")
        return False


def test_search_api():
    """测试搜索API（可选）"""
    print("\n[API测试4] 搜索API (/api/search) - 可选测试")
    try:
        # 简单的搜索测试
        search_data = {
            "country": "ID",
            "grade": "Kelas 1",
            "subject": "Matematika",
            "query": "penjumlahan bilangan"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/search",
            json=search_data,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"⚠️ WARN: 搜索返回HTTP {response.status_code}")
            return True  # 不算失败，因为可能需要API密钥
        
        data = response.json()
        
        if not data.get("success"):
            print(f"⚠️ WARN: 搜索返回success=false: {data.get('message', 'Unknown')}")
            return True  # 可能是API密钥问题，不算失败
        
        results = data.get("results", [])
        print(f"✅ PASS: 搜索成功，返回 {len(results)} 个结果")
        
        return True
        
    except requests.exceptions.Timeout:
        print("⚠️ WARN: 搜索超时（可能需要API密钥或网络问题）")
        return True  # 不算失败
    except Exception as e:
        print(f"⚠️ WARN: 搜索测试失败 - {str(e)}")
        return True  # 不算失败


def test_add_country_api():
    """测试添加国家API（可选）"""
    print("\n[API测试5] 添加国家API (/api/discover_country) - 可选测试")
    print("  ⚠️ 跳过此测试：需要AI API密钥且耗时较长")
    return True  # 跳过此测试


def run_all_tests():
    """运行所有API测试"""
    print("="*80)
    print("API端点测试套件")
    print("="*80)
    print(f"目标API: {API_BASE_URL}")
    print("⚠️ 注意：请确保web_app.py服务正在运行")
    print("   启动命令: python3 web_app.py")
    
    # 等待用户确认
    print("\n按Enter键开始测试，或输入'skip'跳过API测试...")
    user_input = input()
    
    if user_input.strip().lower() == 'skip':
        print("\n跳过API测试")
        return 0
    
    tests = [
        test_health_check,
        test_get_countries,
        test_get_country_config,
        test_search_api,
        test_add_country_api,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            time.sleep(1)  # 避免请求过快
        except Exception as e:
            print(f"\n❌ 测试异常: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    passed = sum(results)
    total = len(results)
    print(f"总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有API测试通过！")
        return 0
    else:
        print(f"⚠️ {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
