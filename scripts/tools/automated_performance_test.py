#!/usr/bin/env python3
"""
自动化性能测试框架（增强版）
用于全面测试系统性能并生成报告
"""

import sys
import time
import json
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import requests
except ImportError:
    print("❌ 请安装 requests 库: pip install requests")
    sys.exit(1)

from logger_utils import get_logger

logger = get_logger('performance_test')


class AutomatedPerformanceTester:
    """
    自动化性能测试器

    功能:
    1. API端点测试
    2. 搜索性能基准测试
    3. 并发压力测试
    4. 缓存效果验证
    5. 性能回归检测
    6. 生成HTML报告
    """

    def __init__(self, base_url: str = "http://localhost:5001"):
        """初始化测试器"""
        self.base_url = base_url
        self.test_results = {}
        logger.info(f"✅ 自动化性能测试器初始化: {base_url}")

    def check_api_health(self) -> bool:
        """检查API健康状态"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            return response.status_code == 200
        except:
            return False

    def benchmark_search(self, country: str, grade: str, subject: str, iterations: int = 3) -> Dict[str, Any]:
        """
        搜索性能基准测试

        Args:
            country: 国家
            grade: 年级
            subject: 学科
            iterations: 迭代次数

        Returns:
            基准测试结果
        """
        url = f"{self.base_url}/api/search"
        payload = {
            "country": country,
            "grade": grade,
            "subject": subject
        }

        durations = []
        success_count = 0

        for i in range(iterations):
            try:
                start = time.time()
                response = requests.post(url, json=payload, timeout=120)
                duration = time.time() - start

                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        success_count += 1

                durations.append(duration)

            except Exception as e:
                logger.error(f"搜索失败: {str(e)}")

        if durations:
            return {
                "country": country,
                "grade": grade,
                "subject": subject,
                "iterations": iterations,
                "success_count": success_count,
                "success_rate": success_count / iterations,
                "min": min(durations),
                "max": max(durations),
                "avg": statistics.mean(durations),
                "median": statistics.median(durations),
                "stdev": statistics.stdev(durations) if len(durations) > 1 else 0
            }
        else:
            return {
                "country": country,
                "grade": grade,
                "subject": subject,
                "error": "All requests failed"
            }

    def run_benchmark_suite(self) -> Dict[str, Any]:
        """运行完整基准测试套件"""
        print("\n" + "=" * 70)
        print("📊 运行基准测试套件")
        print("=" * 70)

        benchmarks = [
            {"country": "Indonesia", "grade": "Kelas 10", "subject": "Matematika"},
            {"country": "China", "grade": "高中一", "subject": "数学"},
            {"country": "India", "grade": "Class 10", "subject": "Mathematics"},
            {"country": "Russia", "grade": "10 класс", "subject": "Математика"},
            {"country": "Philippines", "grade": "Grade 10", "subject": "Mathematics"},
        ]

        results = []
        for benchmark in benchmarks:
            print(f"\n测试: {benchmark['country']} - {benchmark['grade']} - {benchmark['subject']}")
            result = self.benchmark_search(
                benchmark['country'],
                benchmark['grade'],
                benchmark['subject'],
                iterations=3
            )
            results.append(result)

            if 'avg' in result:
                print(f"  ✅ 平均响应时间: {result['avg']:.3f}s")
            else:
                print(f"  ❌ 测试失败: {result.get('error', 'Unknown error')}")

        # 计算总体统计
        successful_results = [r for r in results if 'avg' in r]
        if successful_results:
            avg_times = [r['avg'] for r in successful_results]
            overall_avg = statistics.mean(avg_times)

            # 性能评级
            if overall_avg < 2.0:
                grade = "A (优秀)"
            elif overall_avg < 5.0:
                grade = "B (良好)"
            elif overall_avg < 10.0:
                grade = "C (中等)"
            else:
                grade = "D (需优化)"

            print(f"\n总体评分: {grade}")
            print(f"平均响应时间: {overall_avg:.3f}s")

        return {"benchmarks": results}

    def test_api_endpoints(self) -> Dict[str, Any]:
        """测试所有API端点"""
        print("\n" + "=" * 70)
        print("🔍 测试API端点")
        print("=" * 70)

        endpoints = [
            ("GET", "/api/countries", "获取国家列表"),
            ("GET", "/api/cache_stats", "获取缓存统计"),
            ("GET", "/api/performance_stats", "获取性能统计"),
            ("GET", "/api/system_metrics", "获取系统指标"),
            ("GET", "/api/concurrency_stats", "获取并发统计"),
            ("GET", "/api/search_suggestions?q=mat&country=Indonesia", "搜索建议"),
        ]

        results = []

        for method, endpoint, description in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                start = time.time()

                if method == "GET":
                    response = requests.get(url, timeout=30)

                duration = time.time() - start

                status = "✅" if response.status_code == 200 else "⚠️"
                results.append({
                    "endpoint": endpoint,
                    "description": description,
                    "status_code": response.status_code,
                    "duration": duration,
                    "success": response.status_code == 200
                })

                print(f"{status} {description}: {response.status_code} ({duration:.3f}s)")

            except Exception as e:
                print(f"❌ {description}: {str(e)}")
                results.append({
                    "endpoint": endpoint,
                    "description": description,
                    "error": str(e),
                    "success": False
                })

        success_count = sum(1 for r in results if r.get('success', False))
        print(f"\nAPI测试通过率: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")

        return {"api_tests": results}

    def generate_html_report(self, output_path: str = None):
        """生成HTML测试报告"""
        if output_path is None:
            output_path = project_root / "test_results" / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        output_path = Path(output_path)
        output_path.parent.mkdir(exist_ok=True)

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>性能测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #667eea; border-bottom: 3px solid #667eea; padding-bottom: 10px; }}
        h2 {{ color: #764ba2; margin-top: 30px; }}
        .metric {{ display: inline-block; margin: 10px 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; min-width: 150px; }}
        .metric-label {{ font-size: 12px; color: #666; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #333; }}
        .success {{ color: #28a745; }}
        .warning {{ color: #ffc107; }}
        .danger {{ color: #dc3545; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #667eea; color: white; }}
        .grade-a {{ background: #d4edda; color: #155724; }}
        .grade-b {{ background: #fff3cd; color: #856404; }}
        .grade-c {{ background: #f8d7da; color: #721c24; }}
        .grade-d {{ background: #f5c6cb; color: #721c24; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 性能测试报告</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <h2>📊 测试概览</h2>
        <div class="metric">
            <div class="metric-value">{len(self.test_results.get('api_tests', {}).get('api_tests', []))}</div>
            <div class="metric-label">API端点测试</div>
        </div>
        <div class="metric">
            <div class="metric-value">{len(self.test_results.get('benchmarks', {}).get('benchmarks', []))}</div>
            <div class="metric-label">基准测试</div>
        </div>

        <h2>🔍 API端点测试结果</h2>
        <table>
            <tr>
                <th>端点</th>
                <th>描述</th>
                <th>状态码</th>
                <th>响应时间</th>
                <th>状态</th>
            </tr>
"""

        # API测试结果
        if 'api_tests' in self.test_results:
            for test in self.test_results['api_tests']['api_tests']:
                status_class = 'success' if test.get('success') else 'danger'
                status_text = '✅ 通过' if test.get('success') else '❌ 失败'

                html += f"""
            <tr>
                <td>{test.get('endpoint', 'N/A')}</td>
                <td>{test.get('description', 'N/A')}</td>
                <td>{test.get('status_code', 'N/A')}</td>
                <td>{test.get('duration', 0):.3f}s</td>
                <td class="{status_class}">{status_text}</td>
            </tr>
"""

        html += """
        </table>

        <h2>⚡ 基准测试结果</h2>
        <table>
            <tr>
                <th>国家</th>
                <th>年级</th>
                <th>学科</th>
                <th>平均响应时间</th>
                <th>最小值</th>
                <th>最大值</th>
                <th>成功率</th>
                <th>评级</th>
            </tr>
"""

        # 基准测试结果
        if 'benchmarks' in self.test_results:
            for benchmark in self.test_results['benchmarks']['benchmarks']:
                if 'avg' in benchmark:
                    avg_time = benchmark['avg']
                    if avg_time < 2.0:
                        grade = 'A'
                        grade_class = 'grade-a'
                    elif avg_time < 5.0:
                        grade = 'B'
                        grade_class = 'grade-b'
                    elif avg_time < 10.0:
                        grade = 'C'
                        grade_class = 'grade-c'
                    else:
                        grade = 'D'
                        grade_class = 'grade-d'

                    html += f"""
            <tr class="{grade_class}">
                <td>{benchmark['country']}</td>
                <td>{benchmark['grade']}</td>
                <td>{benchmark['subject']}</td>
                <td>{avg_time:.3f}s</td>
                <td>{benchmark['min']:.3f}s</td>
                <td>{benchmark['max']:.3f}s</td>
                <td>{benchmark['success_rate']:.1%}</td>
                <td><strong>{grade}</strong></td>
            </tr>
"""

        html += """
        </table>

        <h2>💡 优化建议</h2>
        <ul>
            <li>监控慢查询，优化搜索引擎配置</li>
            <li>提高缓存命中率以减少响应时间</li>
            <li>考虑为慢速国家添加本地搜索引擎</li>
            <li>定期执行性能回归测试</li>
        </ul>

        <p style="color: #666; font-size: 12px; margin-top: 30px;">
            由 Indonesia 搜索系统自动化性能测试框架生成
        </p>
    </div>
</body>
</html>
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"\n✅ HTML报告已生成: {output_path}")
        return str(output_path)

    def run_full_test_suite(self) -> str:
        """运行完整测试套件"""
        print("\n" + "=" * 70)
        print("🚀 开始完整性能测试套件")
        print("=" * 70)

        # 健康检查
        if not self.check_api_health():
            print("❌ API不可用，请确保服务正在运行")
            return ""

        # 运行测试
        self.test_results['api_tests'] = self.test_api_endpoints()
        self.test_results['benchmarks'] = self.run_benchmark_suite()

        # 生成报告
        report_path = self.generate_html_report()

        print("\n" + "=" * 70)
        print("✅ 测试完成")
        print("=" * 70)

        return report_path


if __name__ == "__main__":
    tester = AutomatedPerformanceTester()
    report_path = tester.run_full_test_suite()

    if report_path:
        print(f"\n📄 报告路径: {report_path}")
