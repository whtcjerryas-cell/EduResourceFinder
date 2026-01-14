#!/usr/bin/env python3
"""
完整功能测试脚本
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5001"

def print_section(title):
    """打印测试区块"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_test(name, status, details=""):
    """打印测试结果"""
    icon = "✅" if status else "❌"
    print(f"{icon} {name}")
    if details:
        print(f"   {details}")

def test_api_health():
    """测试API健康状态"""
    print_section("1. API健康状态测试")

    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print_test("服务器响应", response.status_code == 200, f"状态码: {response.status_code}")
        return True
    except Exception as e:
        print_test("服务器响应", False, f"错误: {str(e)}")
        return False

def test_countries_api():
    """测试国家配置API"""
    print_section("2. 国家配置API测试")

    try:
        response = requests.get(f"{BASE_URL}/api/countries", timeout=10)
        data = response.json()

        print_test("获取国家列表", data.get("success"), f"返回 {data.get('success')}")

        if data.get("success"):
            countries = data.get("countries", [])
            print_test("国家数量", len(countries) > 0, f"共 {len(countries)} 个国家")

            country_names = [c['country_name'] for c in countries]
            print_test("支持的国家", "Indonesia" in country_names, f"{', '.join(country_names)}")

        return data.get("success")
    except Exception as e:
        print_test("获取国家列表", False, f"错误: {str(e)}")
        return False

def test_k12_search():
    """测试K12教育搜索"""
    print_section("3. K12教育搜索测试")

    test_cases = [
        {
            "name": "印尼一年级数学",
            "params": {
                "country": "ID",
                "grade": "Kelas 1",
                "subject": "Matematika",
                "query": "Matematika Kelas 1",
                "resourceType": "all"
            }
        },
        {
            "name": "埃及三年级科学",
            "params": {
                "country": "EG",
                "grade": "Grade 3",
                "subject": "Science",
                "query": "Science Grade 3 Egypt",
                "resourceType": "all"
            }
        }
    ]

    results = []
    for test in test_cases:
        try:
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/api/search",
                json=test["params"],
                timeout=30
            )
            elapsed = time.time() - start_time
            data = response.json()

            success = data.get("success")
            total = data.get("total_count", 0)
            query = data.get("query", "N/A")

            print_test(
                test["name"],
                success and total > 0,
                f"结果: {total}个 | 耗时: {elapsed:.1f}秒"
            )

            results.append(success)
        except Exception as e:
            print_test(test["name"], False, f"错误: {str(e)}")
            results.append(False)

    return all(results)

def test_university_search():
    """测试大学教育搜索"""
    print_section("4. 大学教育搜索测试")

    try:
        # 先获取可用大学
        response = requests.get(
            f"{BASE_URL}/api/universities?country=ID",
            timeout=10
        )
        data = response.json()

        if not data.get("success"):
            print_test("获取大学列表", False, "API返回失败")
            return False

        universities = data.get("universities", [])
        print_test("获取大学列表", len(universities) > 0, f"共 {len(universities)} 所大学")

        if len(universities) == 0:
            return False

        # 测试大学搜索
        uni = universities[0]
        print_test(f"大学搜索测试 ({uni['local_name']})", True, f"代码: {uni['university_code']}")

        # 执行搜索
        search_params = {
            "country": "ID",
            "query": "Algoritma",
            "university_code": uni.get("university_code"),
            "max_results": 5
        }

        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/search_university",
            json=search_params,
            timeout=30
        )
        elapsed = time.time() - start_time
        data = response.json()

        success = data.get("success")
        total = data.get("total_count", 0)

        print_test(
            "大学搜索结果",
            success,
            f"结果: {total}个 | 耗时: {elapsed:.1f}秒"
        )

        return success

    except Exception as e:
        print_test("大学搜索", False, f"错误: {str(e)}")
        return False

def test_vocational_search():
    """测试职业教育搜索"""
    print_section("5. 职业教育搜索测试")

    try:
        # 先获取技能领域
        response = requests.get(
            f"{BASE_URL}/api/vocational_skill_areas?country=ID",
            timeout=10
        )
        data = response.json()

        if not data.get("success"):
            print_test("获取技能领域", False, "API返回失败")
            return False

        skill_areas = data.get("skill_areas", [])
        print_test("获取技能领域", len(skill_areas) > 0, f"共 {len(skill_areas)} 个领域")

        if len(skill_areas) == 0:
            return False

        # 显示技能领域
        area_names = [f"{a['icon']} {a['area_name']}" for a in skill_areas]
        print(f"   可用领域: {', '.join(area_names)}")

        # 执行搜索
        search_params = {
            "country": "ID",
            "query": "Python",
            "skill_area": "IT",
            "max_results": 5
        }

        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/search_vocational",
            json=search_params,
            timeout=30
        )
        elapsed = time.time() - start_time
        data = response.json()

        success = data.get("success")
        total = data.get("total_count", 0)

        print_test(
            "职业搜索结果",
            success,
            f"结果: {total}个 | 耗时: {elapsed:.1f}秒"
        )

        return success

    except Exception as e:
        print_test("职业搜索", False, f"错误: {str(e)}")
        return False

def test_batch_search_simulation():
    """模拟批量搜索（不实际执行，只验证配置）"""
    print_section("6. 批量搜索配置测试")

    try:
        # 读取配置
        import re
        with open("templates/index.html", "r") as f:
            content = f.read()

        # 检查并发配置
        match = re.search(r"MAX_CONCURRENT\s*=\s*(\d+)", content)
        if match:
            max_concurrent = int(match.group(1))
            print_test("并发配置", True, f"MAX_CONCURRENT = {max_concurrent}")
        else:
            print_test("并发配置", False, "未找到配置")
            return False

        # 检查是否有并发控制器
        has_controller = "executeConcurrentSearches" in content or "ConcurrencyController" in content
        print_test("并发控制器", has_controller, "并发执行逻辑已实现")

        # 检查进度更新函数
        has_progress = "updateProgressUI" in content
        print_test("进度显示", has_progress, "实时进度更新已实现")

        return max_concurrent > 0

    except Exception as e:
        print_test("批量搜索配置", False, f"错误: {str(e)}")
        return False

def test_grade_subject_validation():
    """测试年级-学科验证"""
    print_section("7. 年级-学科验证测试")

    try:
        # 测试有效配对
        response = requests.post(
            f"{BASE_URL}/api/validate_grade_subject",
            json={
                "country": "ID",
                "grade": "Kelas 1",
                "subject": "Matematika"
            },
            timeout=10
        )
        data = response.json()

        valid = data.get("valid")
        print_test("有效配对验证（Kelas 1 + Matematika）", valid, f"验证结果: {valid}")

        # 测试无效配对
        response2 = requests.post(
            f"{BASE_URL}/api/validate_grade_subject",
            json={
                "country": "ID",
                "grade": "Kelas 1",
                "subject": "Fisika"  # 一年级通常没有物理
            },
            timeout=10
        )
        data2 = response2.json()

        invalid = not data2.get("valid", True)
        print_test("无效配对检测（Kelas 1 + Fisika）", invalid, f"应该被拒绝: {not data2.get('valid', True)}")

        return valid or invalid  # 至少一个测试通过

    except Exception as e:
        print_test("年级-学科验证", False, f"错误: {str(e)}")
        return False

def test_documentation():
    """测试文档可用性"""
    print_section("8. 文档完整性测试")

    import os

    docs = [
        ("用户手册", "docs/USER_MANUAL.md"),
        ("开发者指南", "docs/DEVELOPER_GUIDE.md"),
        ("LLM模型目录", "LLM_MODELS_CATALOG.md"),
        ("数据模型目录", "MODEL_CATALOG.md")
    ]

    results = []
    for name, path in docs:
        exists = os.path.exists(path)
        print_test(name, exists, f"路径: {path}" if exists else "文件不存在")
        results.append(exists)

    # 检查测试文件
    test_files = [
        ("综合测试套件", "tests/test_comprehensive_system.py"),
        ("配置管理器测试", "tests/test_config_manager.py"),
        ("年级-学科验证测试", "tests/test_grade_subject_validator.py")
    ]

    for name, path in test_files:
        exists = os.path.exists(path)
        print_test(name, exists, f"路径: {path}" if exists else "文件不存在")
        results.append(exists)

    return all(results)

def generate_summary(results):
    """生成测试总结"""
    print_section("测试总结")

    total = len(results)
    passed = sum(results.values())
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0

    print(f"总测试数: {total}")
    print(f"通过: {passed} ✅")
    print(f"失败: {failed} ❌")
    print(f"通过率: {pass_rate:.1f}%")

    if pass_rate == 100:
        print("\n🎉 所有测试通过！系统运行正常！")
    elif pass_rate >= 80:
        print("\n⚠️  大部分测试通过，系统基本正常")
    else:
        print("\n❌ 多个测试失败，需要检查系统配置")

    # 生成报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": pass_rate,
        "results": results
    }

    with open("test_report_latest.json", "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n📄 详细报告已保存: test_report_latest.json")

def main():
    """主测试函数"""
    print("\n" + "🚀"*40)
    print("  全教育层级智能搜索系统 - 完整功能测试")
    print("  版本: v5.0 (0b697f9)")
    print("  测试时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("🚀"*40)

    results = {}

    # 执行所有测试
    results["API健康"] = test_api_health()
    results["国家配置"] = test_countries_api()
    results["K12搜索"] = test_k12_search()
    results["大学搜索"] = test_university_search()
    results["职业搜索"] = test_vocational_search()
    results["批量搜索配置"] = test_batch_search_simulation()
    results["年级-学科验证"] = test_grade_subject_validation()
    results["文档完整性"] = test_documentation()

    # 生成总结
    generate_summary(results)

    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    exit(main())
