#!/usr/bin/env python3
"""
系统功能测试脚本
检查所有主要端点和功能是否正常工作
"""

import sys
import json
import requests
from typing import Dict, List

BASE_URL = "http://localhost:5000"

def test_health_check():
    """测试健康检查端点"""
    print("🔍 测试 /health 端点...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ /health 端点正常")
            return True
        else:
            print(f"❌ /health 返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ /health 测试失败: {e}")
        return False

def test_api_version():
    """测试版本信息端点"""
    print("\n🔍 测试 /api/version 端点...")
    try:
        response = requests.get(f"{BASE_URL}/api/version", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ /api/version 端点正常 - 版本: {data.get('data', {}).get('version', 'N/A')}")
            return True
        else:
            print(f"❌ /api/version 返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ /api/version 测试失败: {e}")
        return False

def test_api_stats():
    """测试统计信息端点"""
    print("\n🔍 测试 /api/stats 端点...")
    try:
        response = requests.get(f"{BASE_URL}/api/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ /api/stats 端点正常")
            return True
        else:
            print(f"❌ /api/stats 返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ /api/stats 测试失败: {e}")
        return False

def test_api_metrics():
    """测试监控指标端点"""
    print("\n🔍 测试 /api/metrics 端点...")
    try:
        response = requests.get(f"{BASE_URL}/api/metrics", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ /api/metrics 端点正常")
            return True
        else:
            print(f"❌ /api/metrics 返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ /api/metrics 测试失败: {e}")
        return False

def test_api_docs():
    """测试API文档端点"""
    print("\n🔍 测试 /api/docs 端点...")
    try:
        response = requests.get(f"{BASE_URL}/api/docs", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ /api/docs 端点正常")
            return True
        else:
            print(f"❌ /api/docs 返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ /api/docs 测试失败: {e}")
        return False

def test_api_countries():
    """测试国家列表端点"""
    print("\n🔍 测试 /api/countries 端点...")
    try:
        response = requests.get(f"{BASE_URL}/api/countries", timeout=5)
        if response.status_code == 200:
            data = response.json()
            countries = data.get('data', [])
            print(f"✅ /api/countries 端点正常 - 找到 {len(countries)} 个国家")
            return True
        else:
            print(f"❌ /api/countries 返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ /api/countries 测试失败: {e}")
        return False

def test_index_page():
    """测试首页"""
    print("\n🔍 测试 / 首页...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ / 首页正常")
            return True
        else:
            print(f"❌ / 返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ / 测试失败: {e}")
        return False

def test_static_files():
    """测试静态文件"""
    print("\n🔍 测试静态文件访问...")
    try:
        response = requests.get(f"{BASE_URL}/static/css/sidebar_styles.css", timeout=5)
        if response.status_code == 200:
            print("✅ 静态文件可访问")
            return True
        else:
            print(f"❌ 静态文件返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 静态文件测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("="*60)
    print("🚀 K12教育视频搜索系统 - 功能测试")
    print("="*60)

    tests = [
        ("健康检查", test_health_check),
        ("版本信息", test_api_version),
        ("统计信息", test_api_stats),
        ("监控指标", test_api_metrics),
        ("API文档", test_api_docs),
        ("国家列表", test_api_countries),
        ("首页", test_index_page),
        ("静态文件", test_static_files),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} 测试异常: {e}")
            results.append((name, False))

    # 输出测试总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    print(f"\n总计: {passed}/{total} 测试通过 ({passed*100//total}%)")

    if passed == total:
        print("\n🎉 所有测试通过！系统运行正常！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，需要修复")
        return 1

if __name__ == "__main__":
    sys.exit(main())
