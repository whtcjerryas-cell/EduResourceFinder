#!/usr/bin/env python3
"""
现有 API 测试工具（独立测试，不修改现有代码）
"""

import requests
import json
import sys
from typing import Dict, List

class APITester:
    """API 测试器"""

    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.results = []

    def test_all_apis(self):
        """测试所有配置相关 API"""
        print("[🧪 测试] 开始 API 测试...")

        # 测试 1: 获取国家列表
        self._test_get_countries()

        # 测试 2: 获取国家配置
        self._test_get_country_config()

        # 测试 3: 获取教育层级
        self._test_get_education_levels()

        # 测试 4: 获取学科列表
        self._test_get_subjects()

        # 生成测试报告
        self._generate_report()

        # 返回是否全部通过
        return all("✅" in r["status"] for r in self.results)

    def _test_get_countries(self):
        """测试 GET /api/countries"""
        test_name = "GET /api/countries"
        print(f"  [*] {test_name}")

        try:
            response = requests.get(f"{self.base_url}/api/countries", timeout=10)
            data = response.json()

            if response.status_code == 200 and data.get("success"):
                country_count = len(data.get("countries", []))
                self.results.append({
                    "test": test_name,
                    "status": "✅ 通过",
                    "details": f"返回 {country_count} 个国家"
                })
            else:
                self.results.append({
                    "test": test_name,
                    "status": "❌ 失败",
                    "details": f"状态码: {response.status_code}, 响应: {data}"
                })
        except requests.exceptions.ConnectionError:
            self.results.append({
                "test": test_name,
                "status": "❌ 异常",
                "details": "无法连接到服务器，请确保 web_app.py 正在运行"
            })
        except Exception as e:
            self.results.append({
                "test": test_name,
                "status": "❌ 异常",
                "details": str(e)
            })

    def _test_get_country_config(self):
        """测试 GET /api/config/<country_code>"""
        test_name = "GET /api/config/ID"
        print(f"  [*] {test_name}")

        try:
            response = requests.get(f"{self.base_url}/api/config/ID", timeout=10)
            data = response.json()

            if response.status_code == 200 and data.get("success"):
                self.results.append({
                    "test": test_name,
                    "status": "✅ 通过",
                    "details": "成功获取印尼配置"
                })
            else:
                self.results.append({
                    "test": test_name,
                    "status": "❌ 失败",
                    "details": f"状态码: {response.status_code}"
                })
        except requests.exceptions.ConnectionError:
            self.results.append({
                "test": test_name,
                "status": "❌ 异常",
                "details": "无法连接到服务器"
            })
        except Exception as e:
            self.results.append({
                "test": test_name,
                "status": "❌ 异常",
                "details": str(e)
            })

    def _test_get_education_levels(self):
        """测试 GET /api/config/education_levels"""
        test_name = "GET /api/config/education_levels?country=ID"
        print(f"  [*] {test_name}")

        try:
            response = requests.get(
                f"{self.base_url}/api/config/education_levels",
                params={"country": "ID"},
                timeout=10
            )
            data = response.json()

            if response.status_code == 200 and data.get("success"):
                grade_count = len(data.get("grades", []))
                self.results.append({
                    "test": test_name,
                    "status": "✅ 通过",
                    "details": f"返回 {grade_count} 个年级"
                })
            else:
                self.results.append({
                    "test": test_name,
                    "status": "❌ 失败",
                    "details": f"状态码: {response.status_code}"
                })
        except requests.exceptions.ConnectionError:
            self.results.append({
                "test": test_name,
                "status": "❌ 异常",
                "details": "无法连接到服务器"
            })
        except Exception as e:
            self.results.append({
                "test": test_name,
                "status": "❌ 异常",
                "details": str(e)
            })

    def _test_get_subjects(self):
        """测试 GET /api/config/subjects"""
        test_name = "GET /api/config/subjects?country=ID"
        print(f"  [*] {test_name}")

        try:
            response = requests.get(
                f"{self.base_url}/api/config/subjects",
                params={"country": "ID"},
                timeout=10
            )
            data = response.json()

            if response.status_code == 200 and data.get("success"):
                subject_count = len(data.get("subjects", []))
                self.results.append({
                    "test": test_name,
                    "status": "✅ 通过",
                    "details": f"返回 {subject_count} 个学科"
                })
            else:
                self.results.append({
                    "test": test_name,
                    "status": "❌ 失败",
                    "details": f"状态码: {response.status_code}"
                })
        except requests.exceptions.ConnectionError:
            self.results.append({
                "test": test_name,
                "status": "❌ 异常",
                "details": "无法连接到服务器"
            })
        except Exception as e:
            self.results.append({
                "test": test_name,
                "status": "❌ 异常",
                "details": str(e)
            })

    def _generate_report(self):
        """生成测试报告"""
        print("\n[📊 测试报告]")

        total = len(self.results)
        passed = sum(1 for r in self.results if "✅" in r["status"])
        failed = sum(1 for r in self.results if "❌" in r["status"])

        print(f"  总测试数: {total}")
        print(f"  ✅ 通过: {passed}")
        print(f"  ❌ 失败: {failed}")

        for result in self.results:
            print(f"\n  {result['test']}: {result['status']}")
            print(f"     {result['details']}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Indonesia API 测试工具")
    parser.add_argument(
        "--base-url",
        default="http://localhost:5000",
        help="API 基础 URL"
    )

    args = parser.parse_args()

    # 运行测试
    tester = APITester(args.base_url)
    all_passed = tester.test_all_apis()

    # 返回退出码
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
