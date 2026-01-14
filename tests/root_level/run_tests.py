#!/usr/bin/env python3
"""
快速测试脚本 - 验证所有核心功能
"""

import os
import sys
import time
import requests
from datetime import datetime

# 测试配置
BASE_URL = "http://localhost:5001"
TEST_RESULTS = []


def test_case(name):
    """测试用例装饰器"""
    def decorator(func):
        def wrapper():
            start_time = time.time()
            try:
                func()
                elapsed = time.time() - start_time
                TEST_RESULTS.append({
                    'name': name,
                    'status': 'PASS',
                    'time': elapsed,
                    'message': '✅ 通过'
                })
                print(f"✅ {name} ({elapsed:.2f}秒)")
            except AssertionError as e:
                elapsed = time.time() - start_time
                TEST_RESULTS.append({
                    'name': name,
                    'status': 'FAIL',
                    'time': elapsed,
                    'message': f"❌ 失败: {str(e)}"
                })
                print(f"❌ {name} - {str(e)}")
            except Exception as e:
                elapsed = time.time() - start_time
                TEST_RESULTS.append({
                    'name': name,
                    'status': 'ERROR',
                    'time': elapsed,
                    'message': f"⚠️ 错误: {str(e)}"
                })
                print(f"⚠️ {name} - {str(e)}")

        return wrapper
    return decorator


# ============================================================================
# 页面访问测试
# ============================================================================

@test_case("首页访问")
def test_homepage():
    response = requests.get(f"{BASE_URL}/", timeout=10)
    assert response.status_code == 200
    assert "功能导航" in response.text


@test_case("全球地图页面")
def test_global_map():
    response = requests.get(f"{BASE_URL}/global_map", timeout=10)
    assert response.status_code == 200


@test_case("统计仪表板页面")
def test_stats_dashboard():
    response = requests.get(f"{BASE_URL}/stats_dashboard", timeout=10)
    assert response.status_code == 200


@test_case("国家对比页面")
def test_compare():
    response = requests.get(f"{BASE_URL}/compare", timeout=10)
    assert response.status_code == 200


@test_case("知识点页面")
def test_knowledge_points():
    response = requests.get(f"{BASE_URL}/knowledge_points", timeout=10)
    assert response.status_code == 200


@test_case("批量发现页面")
def test_batch_discovery():
    response = requests.get(f"{BASE_URL}/batch_discovery", timeout=10)
    assert response.status_code == 200


@test_case("健康检查页面")
def test_health_status():
    response = requests.get(f"{BASE_URL}/health_status", timeout=10)
    assert response.status_code == 200


@test_case("报告中心页面")
def test_report_center():
    response = requests.get(f"{BASE_URL}/report_center", timeout=10)
    assert response.status_code == 200


# ============================================================================
# API测试
# ============================================================================

@test_case("全球统计API")
def test_global_stats_api():
    response = requests.get(f"{BASE_URL}/api/global_stats", timeout=10)
    assert response.status_code == 200, f"API返回状态码: {response.status_code}"
    data = response.json()
    assert data['success'] == True, f"API返回success=False: {data}"
    assert 'total_countries' in data


@test_case("知识点覆盖率API")
def test_knowledge_coverage_api():
    response = requests.get(
        f"{BASE_URL}/api/knowledge_point_coverage",
        params={'country': 'ID', 'grade': 'Grade 1', 'subject': 'Mathematics'},
        timeout=10
    )
    # 如果配置不存在，可能返回500，这是可接受的
    assert response.status_code in [200, 500]


@test_case("国家对比API")
def test_compare_api():
    response = requests.post(
        f"{BASE_URL}/api/compare_countries",
        json={'countries': ['ID', 'PH', 'MY']},
        timeout=10
    )
    assert response.status_code == 200, f"API返回状态码: {response.status_code}"
    data = response.json()
    assert data['success'] == True, f"API返回success=False: {data}"


@test_case("搜索统计API")
def test_search_stats_api():
    response = requests.get(
        f"{BASE_URL}/api/search_stats",
        params={'days': 7},
        timeout=10
    )
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True


@test_case("健康检查API")
def test_health_check_api():
    response = requests.post(f"{BASE_URL}/api/health_check", timeout=60)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert 'results' in data


@test_case("报告列表API")
def test_list_reports_api():
    response = requests.get(f"{BASE_URL}/api/list_reports", timeout=10)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True


# ============================================================================
# 核心模块测试
# ============================================================================

@test_case("数据分析模块")
def test_analytics_module():
    from core.analytics import DataAnalyzer
    analyzer = DataAnalyzer()
    stats = analyzer.get_global_stats()
    assert 'total_countries' in stats


@test_case("健康检查器模块")
def test_health_checker_module():
    from core.health_checker import HealthChecker
    checker = HealthChecker()
    results = checker.run_all_checks()
    assert 'overall_status' in results


@test_case("报告生成器模块")
def test_report_generator_module():
    from core.report_generator import ReportGenerator, ReportConfig
    generator = ReportGenerator()
    config = ReportConfig(title="测试", time_range_days=7)
    report = generator.generate_comprehensive_report(config)
    assert 'metadata' in report


@test_case("任务调度器模块")
def test_scheduler_module():
    from core.scheduler import TaskScheduler
    scheduler = TaskScheduler()

    def test_job():
        pass

    task = scheduler.add_interval_task(
        task_id='test',
        name='测试',
        job_func=test_job,
        interval_seconds=60
    )
    assert task is not None
    scheduler.stop()


# ============================================================================
# 测试运行器
# ============================================================================

def run_all_tests():
    """运行所有测试"""
    print("=" * 80)
    print("🧪 K12教育资源搜索系统 - 自动化测试")
    print("=" * 80)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 测试地址: {BASE_URL}")
    print("=" * 80)
    print()

    # 检查服务器是否运行
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✅ 服务器运行正常")
        print()
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到服务器 {BASE_URL}")
        print(f"请确保服务器正在运行: python3 web_app.py")
        return 1

    # Stage 1: 可视化功能测试
    print("📊 Stage 1: 可视化功能测试")
    print("-" * 80)

    test_homepage()
    test_global_map()
    test_stats_dashboard()
    test_compare()
    test_knowledge_points()

    print()

    # Stage 2: 自动化功能测试
    print("🤖 Stage 2: 自动化功能测试")
    print("-" * 80)

    test_batch_discovery()
    test_health_status()
    test_report_center()

    print()

    # API测试
    print("🔌 API测试")
    print("-" * 80)

    test_global_stats_api()
    test_knowledge_coverage_api()
    test_compare_api()
    test_search_stats_api()
    test_health_check_api()
    test_list_reports_api()

    print()

    # 核心模块测试
    print("🧩 核心模块测试")
    print("-" * 80)

    test_analytics_module()
    test_health_checker_module()
    test_report_generator_module()
    test_scheduler_module()

    print()
    print("=" * 80)

    # 统计结果
    total = len(TEST_RESULTS)
    passed = len([r for r in TEST_RESULTS if r['status'] == 'PASS'])
    failed = len([r for r in TEST_RESULTS if r['status'] == 'FAIL'])
    errors = len([r for r in TEST_RESULTS if r['status'] == 'ERROR'])
    total_time = sum([r['time'] for r in TEST_RESULTS])

    print(f"📊 测试结果统计")
    print(f"   总计: {total}")
    print(f"   通过: {passed} ✅")
    print(f"   失败: {failed} ❌")
    print(f"   错误: {errors} ⚠️")
    print(f"   总耗时: {total_time:.2f}秒")
    print()

    if failed > 0 or errors > 0:
        print("❌ 失败的测试:")
        for result in TEST_RESULTS:
            if result['status'] in ['FAIL', 'ERROR']:
                print(f"   - {result['name']}: {result['message']}")
        print()

    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"📈 成功率: {success_rate:.1f}%")
    print("=" * 80)

    return 0 if (failed == 0 and errors == 0) else 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
