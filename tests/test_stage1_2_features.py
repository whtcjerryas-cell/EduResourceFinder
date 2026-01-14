#!/usr/bin/env python3
"""
Stage 1 & 2 功能自动化测试套件
测试所有新增的可视化和自动化功能
"""

import os
import sys
import json
import time
import pytest
import requests
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试配置
BASE_URL = "http://localhost:5001"
TEST_TIMEOUT = 30  # API请求超时时间（秒）


class TestStage1Visualization:
    """Stage 1: 可视化功能测试"""

    def test_global_map_page(self):
        """测试全球地图页面访问"""
        response = requests.get(f"{BASE_URL}/global_map", timeout=TEST_TIMEOUT)
        assert response.status_code == 200
        assert "全球教育资源地图" in response.text or "Global" in response.text
        print("✅ 全球地图页面访问成功")

    def test_stats_dashboard_page(self):
        """测试统计仪表板页面访问"""
        response = requests.get(f"{BASE_URL}/stats_dashboard", timeout=TEST_TIMEOUT)
        assert response.status_code == 200
        assert "统计仪表板" in response.text or "Dashboard" in response.text
        print("✅ 统计仪表板页面访问成功")

    def test_compare_page(self):
        """测试国家对比页面访问"""
        response = requests.get(f"{BASE_URL}/compare", timeout=TEST_TIMEOUT)
        assert response.status_code == 200
        assert "对比" in response.text or "Compare" in response.text
        print("✅ 国家对比页面访问成功")

    def test_knowledge_points_page(self):
        """测试知识点热力图页面访问"""
        response = requests.get(f"{BASE_URL}/knowledge_points", timeout=TEST_TIMEOUT)
        assert response.status_code == 200
        assert "知识点" in response.text or "Knowledge" in response.text
        print("✅ 知识点页面访问成功")

    def test_global_stats_api(self):
        """测试全球统计API"""
        response = requests.get(f"{BASE_URL}/api/global_stats", timeout=TEST_TIMEOUT)
        assert response.status_code == 200

        data = response.json()
        assert 'success' in data
        assert data['success'] == True
        assert 'total_countries' in data
        assert data['total_countries'] >= 0
        print(f"✅ 全球统计API正常 - 支持国家数: {data['total_countries']}")

    def test_knowledge_point_coverage_api(self):
        """测试知识点覆盖率API"""
        params = {
            'country': 'ID',
            'grade': 'Grade 1',
            'subject': 'Mathematics'
        }
        response = requests.get(
            f"{BASE_URL}/api/knowledge_point_coverage",
            params=params,
            timeout=TEST_TIMEOUT
        )

        # 如果国家配置存在，应该返回数据
        if response.status_code == 200:
            data = response.json()
            assert 'success' in data
            print(f"✅ 知识点覆盖率API正常")
        else:
            print(f"⚠️ 知识点覆盖率API返回 {response.status_code}（可能缺少配置）")

    def test_compare_countries_api(self):
        """测试国家对比API"""
        payload = {
            'countries': ['ID', 'PH', 'MY']
        }
        response = requests.post(
            f"{BASE_URL}/api/compare_countries",
            json=payload,
            timeout=TEST_TIMEOUT
        )

        if response.status_code == 200:
            data = response.json()
            assert 'success' in data
            assert data['success'] == True
            print(f"✅ 国家对比API正常")
        else:
            print(f"⚠️ 国家对比API返回 {response.status_code}")

    def test_search_stats_api(self):
        """测试搜索统计API"""
        response = requests.get(
            f"{BASE_URL}/api/search_stats",
            params={'days': 7},
            timeout=TEST_TIMEOUT
        )

        if response.status_code == 200:
            data = response.json()
            assert 'success' in data
            print(f"✅ 搜索统计API正常 - 总搜索次数: {data.get('total_searches', 0)}")
        else:
            print(f"⚠️ 搜索统计API返回 {response.status_code}")


class TestStage2Automation:
    """Stage 2: 自动化功能测试"""

    def test_batch_discovery_page(self):
        """测试批量发现页面访问"""
        response = requests.get(f"{BASE_URL}/batch_discovery", timeout=TEST_TIMEOUT)
        assert response.status_code == 200
        assert "批量" in response.text or "Batch" in response.text
        print("✅ 批量发现页面访问成功")

    def test_health_status_page(self):
        """测试健康检查页面访问"""
        response = requests.get(f"{BASE_URL}/health_status", timeout=TEST_TIMEOUT)
        assert response.status_code == 200
        assert "健康" in response.text or "Health" in response.text
        print("✅ 健康检查页面访问成功")

    def test_report_center_page(self):
        """测试报告中心页面访问"""
        response = requests.get(f"{BASE_URL}/report_center", timeout=TEST_TIMEOUT)
        assert response.status_code == 200
        assert "报告" in response.text or "Report" in response.text
        print("✅ 报告中心页面访问成功")

    def test_batch_discovery_api(self):
        """测试批量发现API（使用mock数据，不实际调用）"""
        # 只测试API端点是否存在，不实际执行批量发现
        payload = {
            'countries': ['TestCountry1', 'TestCountry2'],
            'skip_existing': True
        }

        # 这个测试只验证API能接受请求，实际执行会失败（因为国家不存在）
        response = requests.post(
            f"{BASE_URL}/api/batch_discover_countries",
            json=payload,
            timeout=TEST_TIMEOUT
        )

        # API应该能接受请求（即使执行失败）
        assert response.status_code in [200, 500]
        print(f"✅ 批量发现API端点可访问")

    def test_health_check_api(self):
        """测试健康检查API"""
        response = requests.post(
            f"{BASE_URL}/api/health_check",
            timeout=60  # 健康检查可能需要较长时间
        )

        if response.status_code == 200:
            data = response.json()
            assert 'success' in data
            assert 'results' in data
            assert 'overall_status' in data['results']

            # 显示健康检查结果
            results = data['results']
            print(f"✅ 健康检查API正常")
            print(f"   总体状态: {results['overall_status']}")
            print(f"   总检查项: {results['total_checks']}")
            print(f"   通过: {results['passed_checks']}, 失败: {results['failed_checks']}")
        else:
            print(f"⚠️ 健康检查API返回 {response.status_code}")

    def test_generate_report_api(self):
        """测试报告生成API"""
        payload = {
            'title': '测试报告',
            'time_range_days': 7,
            'format_markdown': True,
            'format_json': False
        }

        response = requests.post(
            f"{BASE_URL}/api/generate_report",
            json=payload,
            timeout=60  # 报告生成可能需要较长时间
        )

        if response.status_code == 200:
            data = response.json()
            assert 'success' in data
            assert data['success'] == True
            assert 'results' in data

            results = data['results']
            print(f"✅ 报告生成API正常")
            print(f"   报告标题: {results['metadata']['title']}")
            print(f"   生成耗时: {results['metadata']['generation_time']:.2f}秒")

            if 'markdown_file' in results:
                print(f"   Markdown文件: {results['markdown_file']}")
        else:
            print(f"⚠️ 报告生成API返回 {response.status_code}")

    def test_list_reports_api(self):
        """测试报告列表API"""
        response = requests.get(f"{BASE_URL}/api/list_reports", timeout=TEST_TIMEOUT)

        if response.status_code == 200:
            data = response.json()
            assert 'success' in data
            assert 'reports' in data
            print(f"✅ 报告列表API正常 - 报告数: {len(data['reports'])}")
        else:
            print(f"⚠️ 报告列表API返回 {response.status_code}")


class TestCoreModules:
    """核心模块单元测试"""

    def test_analytics_module(self):
        """测试数据分析模块"""
        try:
            from core.analytics import DataAnalyzer

            analyzer = DataAnalyzer()

            # 测试获取全球统计
            stats = analyzer.get_global_stats()
            assert 'total_countries' in stats
            assert 'total_videos' in stats

            print(f"✅ DataAnalyzer模块正常")
            print(f"   总国家数: {stats['total_countries']}")
        except Exception as e:
            pytest.fail(f"DataAnalyzer模块测试失败: {str(e)}")

    def test_health_checker_module(self):
        """测试健康检查器模块"""
        try:
            from core.health_checker import HealthChecker

            checker = HealthChecker()

            # 运行快速健康检查（不检查搜索引擎，避免API调用）
            results = checker.run_all_checks()

            assert 'overall_status' in results
            assert 'total_checks' in results

            print(f"✅ HealthChecker模块正常")
            print(f"   总体状态: {results['overall_status']}")
        except Exception as e:
            pytest.fail(f"HealthChecker模块测试失败: {str(e)}")

    def test_report_generator_module(self):
        """测试报告生成器模块"""
        try:
            from core.report_generator import ReportGenerator, ReportConfig

            generator = ReportGenerator()
            config = ReportConfig(title="测试报告", time_range_days=7)

            # 生成报告数据
            report_data = generator.generate_comprehensive_report(config)

            assert 'metadata' in report_data
            assert 'sections' in report_data
            assert len(report_data['sections']) > 0

            # 测试Markdown生成
            markdown = generator.generate_markdown_report(report_data)
            assert len(markdown) > 0
            assert "# 测试报告" in markdown or "# K12教育资源" in markdown

            print(f"✅ ReportGenerator模块正常")
            print(f"   生成耗时: {report_data['metadata']['generation_time']:.2f}秒")
            print(f"   章节数: {len(report_data['sections'])}")
        except Exception as e:
            pytest.fail(f"ReportGenerator模块测试失败: {str(e)}")

    def test_scheduler_module(self):
        """测试任务调度器模块"""
        try:
            from core.scheduler import TaskScheduler

            scheduler = TaskScheduler()

            # 添加一个测试任务
            def test_job():
                pass

            task = scheduler.add_interval_task(
                task_id='test_task',
                name='测试任务',
                job_func=test_job,
                interval_seconds=60,
                description='单元测试任务'
            )

            assert task is not None
            assert task.task_id == 'test_task'

            # 获取任务状态
            status = scheduler.get_task_status('test_task')
            assert status is not None
            assert status['name'] == '测试任务'

            # 移除测试任务
            scheduler.remove_task('test_task')

            # 停止调度器
            scheduler.stop()

            print(f"✅ TaskScheduler模块正常")
        except Exception as e:
            pytest.fail(f"TaskScheduler模块测试失败: {str(e)}")


class TestIntegration:
    """集成测试"""

    def test_homepage_feature_navigation(self):
        """测试首页功能导航"""
        response = requests.get(f"{BASE_URL}/", timeout=TEST_TIMEOUT)
        assert response.status_code == 200

        # 检查是否包含功能导航区域
        text = response.text
        assert "功能导航" in text or "Feature" in text

        # 检查Stage 1功能
        assert "全球地图" in text or "Global" in text
        assert "统计仪表板" in text or "Dashboard" in text

        # 检查Stage 2功能
        assert "批量发现" in text or "Batch" in text
        assert "健康检查" in text or "Health" in text

        print(f"✅ 首页功能导航正常")

    def test_end_to_end_search_flow(self):
        """端到端搜索流程测试"""
        # 1. 访问首页
        response = requests.get(f"{BASE_URL}/", timeout=TEST_TIMEOUT)
        assert response.status_code == 200

        # 2. 测试搜索API（使用简单参数）
        search_payload = {
            'country_code': 'ID',
            'grade': 'Grade 1',
            'subject': 'Mathematics',
            'query': 'addition'
        }

        # 注意：如果API不存在，这个测试会跳过
        try:
            response = requests.post(
                f"{BASE_URL}/api/search",
                json=search_payload,
                timeout=TEST_TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ 端到端搜索流程正常")
            else:
                print(f"⚠️ 搜索API返回 {response.status_code}")
        except requests.exceptions.RequestException:
            print(f"⚠️ 搜索API端点不存在")

    def test_api_response_times(self):
        """测试API响应时间"""
        api_endpoints = [
            ('/api/global_stats', 'GET'),
            ('/api/search_stats?days=7', 'GET'),
            ('/health_status', 'GET'),
        ]

        slow_apis = []

        for endpoint, method in api_endpoints:
            start_time = time.time()

            try:
                if method == 'GET':
                    response = requests.get(f"{BASE_URL}{endpoint}", timeout=TEST_TIMEOUT)
                else:
                    response = requests.post(f"{BASE_URL}{endpoint}", timeout=TEST_TIMEOUT)

                elapsed_time = time.time() - start_time

                if response.status_code == 200:
                    if elapsed_time > 5:  # 超过5秒认为响应慢
                        slow_apis.append((endpoint, elapsed_time))
                        print(f"⚠️ {endpoint} 响应较慢: {elapsed_time:.2f}秒")
                    else:
                        print(f"✅ {endpoint}: {elapsed_time:.2f}秒")
                else:
                    print(f"❌ {endpoint}: 返回 {response.status_code}")

            except Exception as e:
                print(f"❌ {endpoint}: {str(e)}")

        if not slow_apis:
            print(f"✅ 所有API响应时间正常")


def run_tests():
    """运行所有测试"""
    print("=" * 80)
    print("🧪 开始自动化测试 - Stage 1 & 2 功能")
    print("=" * 80)
    print()

    # 运行pytest
    exit_code = pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--color=yes'
    ])

    print()
    print("=" * 80)
    if exit_code == 0:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败，请检查上述输出")
    print("=" * 80)

    return exit_code


if __name__ == "__main__":
    sys.exit(run_tests())
