#!/usr/bin/env python3
"""
全面测试脚本 - 测试所有页面和功能
"""

import sys
import requests
from datetime import datetime


def test_page(url, name, description=""):
    """测试单个页面"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"✅ {name}")
            if description:
                print(f"   {description}")
            return True
        else:
            print(f"❌ {name} - HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {name} - {str(e)[:60]}")
        return False


def test_api(url, name, check_json=True):
    """测试单个API"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"❌ API: {name} - HTTP {response.status_code}")
            return False

        if check_json:
            try:
                data = response.json()
                if data.get("success"):
                    print(f"✅ API: {name}")
                    return True
                else:
                    print(f"⚠️  API: {name} - success=false")
                    return False
            except:
                print(f"⚠️  API: {name} - 非JSON响应")
                return False
        else:
            print(f"✅ API: {name}")
            return True

    except Exception as e:
        print(f"❌ API: {name} - {str(e)[:60]}")
        return False


def main():
    """主测试函数"""
    print("="*70)
    print("🚀 K12教育资源搜索系统 - 全面功能测试")
    print("="*70)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"服务器: http://localhost:5001")
    print("="*70)

    # 检查服务器
    try:
        response = requests.get("http://localhost:5001", timeout=5)
    except Exception:
        print("\n❌ 错误: 服务器未运行或无法访问")
        print("   请先启动服务器: python3 web_app.py\n")
        return 1

    passed = 0
    failed = 0

    # ========== 测试1: 核心页面 ==========
    print("\n📝 测试1: 核心页面")
    print("-"*70)

    core_pages = [
        ("http://localhost:5001/", "主页", "搜索功能和优化的侧边栏"),
        ("http://localhost:5001/search_history", "搜索历史", "独立的历史记录页面"),
        ("http://localhost:5001/knowledge_points", "知识点概览", "知识点管理系统"),
        ("http://localhost:5001/evaluation_reports", "评估报告", "视频评估报告"),
    ]

    for url, name, desc in core_pages:
        if test_page(url, name, desc):
            passed += 1
        else:
            failed += 1

    # ========== 测试2: Stage 1 数据可视化页面 ==========
    print("\n📊 测试2: 数据可视化页面 (Stage 1)")
    print("-"*70)

    viz_pages = [
        ("http://localhost:5001/global_map", "全球资源地图", "交互式世界地图"),
        ("http://localhost:5001/stats_dashboard", "实时统计仪表板", "系统统计数据"),
        ("http://localhost:5001/compare", "国家资源对比", "多国对比分析"),
    ]

    for url, name, desc in viz_pages:
        if test_page(url, name, desc):
            passed += 1
        else:
            failed += 1

    # ========== 测试3: Stage 2 自动化页面 ==========
    print("\n🤖 测试3: 智能自动化页面 (Stage 2)")
    print("-"*70)

    auto_pages = [
        ("http://localhost:5001/batch_discovery", "批量国家发现", "批量接入新国家"),
        ("http://localhost:5001/health_status", "系统健康检查", "自动化测试套件"),
        ("http://localhost:5001/report_center", "报告中心", "自动报告生成"),
    ]

    for url, name, desc in auto_pages:
        if test_page(url, name, desc):
            passed += 1
        else:
            failed += 1

    # ========== 测试4: 核心API ==========
    print("\n🔌 测试4: 核心API端点")
    print("-"*70)

    core_apis = [
        ("http://localhost:5001/api/countries", "获取国家列表"),
        ("http://localhost:5001/api/history", "获取搜索历史"),
    ]

    for url, name in core_apis:
        if test_api(url, name):
            passed += 1
        else:
            failed += 1

    # ========== 测试5: 配置API ==========
    print("\n⚙️  测试5: 配置相关API")
    print("-"*70)

    # 先获取国家列表，然后测试配置API
    try:
        countries_response = requests.get("http://localhost:5001/api/countries", timeout=10)
        if countries_response.status_code == 200:
            countries_data = countries_response.json()
            if countries_data.get("success") and countries_data.get("countries"):
                first_country = countries_data["countries"][0]["country_code"]

                config_url = f"http://localhost:5001/api/config/{first_country}"
                if test_api(config_url, f"获取{first_country}配置"):
                    passed += 1
                else:
                    failed += 1
            else:
                print("⚠️  无法获取国家列表，跳过配置测试")
                failed += 1
        else:
            print("⚠️  无法获取国家列表，跳过配置测试")
            failed += 1
    except Exception as e:
        print(f"⚠️  配置测试跳过: {str(e)[:60]}")
        failed += 1

    # ========== 测试6: 性能监控API ==========
    print("\n📈 测试6: 性能监控API")
    print("-"*70)

    perf_apis = [
        ("http://localhost:5001/api/performance_stats", "性能统计"),
        ("http://localhost:5001/api/cache_stats", "缓存统计"),
        ("http://localhost:5001/api/system_metrics", "系统指标"),
    ]

    for url, name in perf_apis:
        if test_api(url, name):
            passed += 1
        else:
            failed += 1

    # ========== 测试总结 ==========
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)

    total = passed + failed
    pass_rate = (passed / total * 100) if total > 0 else 0

    print(f"\n📊 测试统计:")
    print(f"   总测试数: {total}")
    print(f"   ✅ 通过: {passed}")
    print(f"   ❌ 失败: {failed}")
    print(f"   通过率: {pass_rate:.1f}%")

    print(f"\n🎯 测试覆盖:")
    print(f"   ✓ 核心页面: 4个")
    print(f"   ✓ 数据可视化: 3个 (Stage 1)")
    print(f"   ✓ 智能自动化: 3个 (Stage 2)")
    print(f"   ✓ 核心API: 2个")
    print(f"   ✓ 性能监控: 3个")

    # 评估结果
    print("\n" + "="*70)
    if failed == 0:
        print("🎉 恭喜！所有测试通过！")
        print("\n✨ 系统状态: 完全正常")
        print("✨ 所有页面可访问")
        print("✨ 所有API响应正常")
        print("="*70)
        return 0
    elif pass_rate >= 80:
        print("⚠️  大部分测试通过，但有少量问题")
        print(f"   建议检查失败的 {failed} 个测试项")
        print("="*70)
        return 1
    else:
        print("❌ 测试失败较多，请检查系统配置")
        print("="*70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
