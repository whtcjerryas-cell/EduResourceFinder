#!/usr/bin/env python3
"""
综合功能测试脚本 - 验证所有核心功能
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:5004"

def test_homepage():
    """测试首页"""
    print("\n" + "="*60)
    print("测试1: 首页访问")
    print("="*60)

    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            print("✅ 首页访问成功")
            print(f"   状态码: {response.status_code}")
            return True
        else:
            print(f"❌ 首页访问失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 首页访问异常: {str(e)}")
        return False


def test_config_api():
    """测试配置管理API"""
    print("\n" + "="*60)
    print("测试2: 配置管理API")
    print("="*60)

    try:
        # 测试获取所有国家
        response = requests.get(f"{BASE_URL}/api/countries", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if len(data.get('countries', [])) > 0:
                print("✅ 获取国家列表成功")
                print(f"   国家数量: {len(data['countries'])}")
                print(f"   示例国家: {data['countries'][0]['country_name']}")
                return data['countries'][0]['country_code']
            else:
                print("❌ 获取国家列表失败")
                return None
        else:
            print(f"❌ API请求失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 配置API测试异常: {str(e)}")
        return None


def test_search_api(country_code):
    """测试搜索API"""
    print("\n" + "="*60)
    print("测试3: 搜索功能")
    print("="*60)

    search_data = {
        "country": country_code or "ID",
        "grade": "Kelas 1",
        "subject": "Matematika",
        "semester": "",
        "language": "",
        "resourceType": "all"
    }

    try:
        print(f"   搜索参数: {search_data}")
        print("   正在搜索...")
        response = requests.post(
            f"{BASE_URL}/api/search",
            json=search_data,
            timeout=180  # 3分钟超时
        )

        if response.status_code == 200:
            data = response.json()
            print("✅ 搜索请求成功")

            if data.get('success'):
                results = data.get('results', [])
                print(f"   结果数量: {len(results)}")
                print(f"   查询: {data.get('query', '')}")

                if len(results) > 0:
                    print(f"\n   第一个结果:")
                    print(f"   - 标题: {results[0].get('title', 'N/A')[:50]}...")
                    print(f"   - URL: {results[0].get('url', 'N/A')[:60]}...")
                    print(f"   - 资源类型: {results[0].get('resource_type', 'N/A')}")
                    print(f"   - 质量分数: {results[0].get('score', 0)}")
                    return results
                else:
                    print("⚠️  未找到结果")
                    return []
            else:
                print(f"❌ 搜索失败: {data.get('message', '未知错误')}")
                return None
        else:
            print(f"❌ 搜索请求失败，状态码: {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        print("❌ 搜索请求超时（3分钟）")
        return None
    except Exception as e:
        print(f"❌ 搜索测试异常: {str(e)}")
        return None


def test_grade_subjects(country_code):
    """测试获取年级和学科"""
    print("\n" + "="*60)
    print("测试4: 获取年级和学科")
    print("="*60)

    try:
        response = requests.get(
            f"{BASE_URL}/api/config/{country_code}",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                config = data.get('config', {})
                grades = config.get('education_levels', [])
                subjects = config.get('subjects', [])

                print("✅ 获取年级和学科成功")
                print(f"   年级数量: {len(grades)}")
                print(f"   学科数量: {len(subjects)}")

                if len(grades) > 0:
                    print(f"   示例年级: {grades[0]}")
                if len(subjects) > 0:
                    print(f"   示例学科: {subjects[0]}")

                return True
            else:
                print(f"❌ 获取失败: {data.get('message', '未知错误')}")
                return False
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        return False


def test_knowledge_points(country_code):
    """测试获取知识点"""
    print("\n" + "="*60)
    print("测试5: 获取知识点")
    print("="*60)

    try:
        # 使用印度尼西亚作为测试国家（数据更完整）
        test_country = "ID"  # Indonesia

        # 先获取年级和学科
        gs_response = requests.get(
            f"{BASE_URL}/api/config/{test_country}",
            timeout=10
        )

        if gs_response.status_code != 200:
            print("❌ 无法获取年级和学科")
            return False

        gs_data = gs_response.json()
        config = gs_data.get('config', {})
        grades = config.get('education_levels', [])
        subjects = config.get('subjects', [])

        if len(grades) == 0 or len(subjects) == 0:
            print("⚠️  该国家没有年级或学科数据，跳过知识点测试")
            return True  # 不是失败，只是跳过

        # 获取第一个年级和学科
        grade = grades[0] if isinstance(grades[0], str) else grades[0].get('local_name', grades[0].get('zh_name', ''))
        subject = subjects[0] if isinstance(subjects[0], str) else subjects[0].get('local_name', subjects[0].get('zh_name', ''))

        # 获取知识点
        response = requests.get(
            f"{BASE_URL}/api/knowledge_points",
            params={
                "country": test_country,
                "grade": grade,
                "subject": subject
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                knowledge_points = data.get('knowledge_points', [])
                print("✅ 获取知识点成功")
                print(f"   国家: {test_country}")
                print(f"   年级: {grade}")
                print(f"   学科: {subject}")
                print(f"   知识点数量: {len(knowledge_points)}")

                if len(knowledge_points) > 0:
                    kp = knowledge_points[0]
                    kp_name = kp.get('name', 'N/A')
                    print(f"   示例知识点: {kp_name}")

                return True
            else:
                print(f"❌ 获取失败: {data.get('message', '未知错误')}")
                return False
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("🧪 Indonesia 项目综合功能测试")
    print("="*60)
    print(f"测试服务器: {BASE_URL}")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # 测试1: 首页
    results.append(("首页访问", test_homepage()))

    # 测试2: 配置API
    country_code = test_config_api()
    results.append(("配置管理API", country_code is not None))

    if country_code:
        # 测试3: 年级和学科
        results.append(("年级和学科", test_grade_subjects(country_code)))

        # 测试4: 知识点
        results.append(("知识点", test_knowledge_points(country_code)))

        # 测试5: 搜索功能（最关键）
        search_results = test_search_api(country_code)
        results.append(("搜索功能", search_results is not None and len(search_results) >= 0))

    # 打印测试总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:15} : {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print("\n" + "-"*60)
    print(f"总计: {len(results)}个测试")
    print(f"通过: {passed}个")
    print(f"失败: {failed}个")
    print(f"成功率: {passed/len(results)*100:.1f}%")
    print("="*60)

    if failed == 0:
        print("\n🎉 所有测试通过！项目运行正常！")
        return 0
    else:
        print(f"\n⚠️  有{failed}个测试失败，需要修复")
        return 1


if __name__ == '__main__':
    sys.exit(main())
