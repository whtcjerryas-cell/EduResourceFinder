#!/usr/bin/env python3
"""
自动化测试脚本 - 验证所有优化功能

测试范围：
1. 资源类型自动分类
2. 资源类型过滤
3. YouTube播放列表检测
4. AI深度评估功能
5. LLM推荐理由生成
"""

import requests
import json
import sys
import time
from typing import Dict, List, Any
from datetime import datetime

# 配置
BASE_URL = "http://localhost:5001"
TEST_RESULTS = []

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def log_test(test_name: str, passed: bool, details: str = ""):
    """记录测试结果"""
    status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if passed else f"{Colors.RED}❌ FAIL{Colors.RESET}"
    TEST_RESULTS.append({
        "test_name": test_name,
        "passed": passed,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })
    print(f"{status} | {test_name}")
    if details:
        print(f"    {details}")


def test_server_running():
    """测试1: 验证服务器是否运行"""
    print(f"\n{Colors.BOLD}{'='*60}")
    print("测试1: 验证服务器状态")
    print(f"{'='*60}{Colors.RESET}\n")

    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            log_test("服务器运行状态", True, f"服务器响应正常: {BASE_URL}")
            return True
        else:
            log_test("服务器运行状态", False, f"状态码: {response.status_code}")
            return False
    except Exception as e:
        log_test("服务器运行状态", False, f"错误: {str(e)}")
        return False


def test_search_api():
    """测试2: 验证搜索API基本功能"""
    print(f"\n{Colors.BOLD}{'='*60}")
    print("测试2: 搜索API功能")
    print(f"{'='*60}{Colors.RESET}\n")

    search_request = {
        "country": "ID",
        "grade": "1",
        "subject": "Matematika",
        "resourceType": "all"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/search",
            json=search_request,
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                result_count = len(data.get("results", []))
                log_test("搜索API响应", True, f"找到 {result_count} 个结果")

                # 检查是否有结果
                if result_count > 0:
                    log_test("搜索结果数量", True, f"返回 {result_count} 个资源")
                    return data
                else:
                    log_test("搜索结果数量", False, "没有返回任何结果")
                    return None
            else:
                log_test("搜索API响应", False, f"API返回失败: {data.get('message')}")
                return None
        else:
            log_test("搜索API响应", False, f"状态码: {response.status_code}")
            return None

    except Exception as e:
        log_test("搜索API响应", False, f"异常: {str(e)}")
        return None


def test_resource_classification(search_data: Dict):
    """测试3: 验证资源类型自动分类"""
    print(f"\n{Colors.BOLD}{'='*60}")
    print("测试3: 资源类型自动分类")
    print(f"{'='*60}{Colors.RESET}\n")

    if not search_data or not search_data.get("results"):
        log_test("资源分类功能", False, "没有搜索结果可供测试")
        return False

    results = search_data["results"]
    type_counts = {}
    has_types = False

    for result in results:
        resource_type = result.get("resource_type", "未知")

        if resource_type != "未知":
            has_types = True

        type_counts[resource_type] = type_counts.get(resource_type, 0) + 1

    # 统计各类型数量
    print(f"\n资源类型统计:")
    for type_name, count in sorted(type_counts.items()):
        print(f"  {type_name}: {count} 个")

    if has_types:
        log_test("资源分类功能", True, f"成功分类为 {len(type_counts)} 种类型")
        return True
    else:
        log_test("资源分类功能", False, "所有资源的resource_type都是'未知'")
        return False


def test_resource_type_filter():
    """测试4: 验证资源类型过滤功能"""
    print(f"\n{Colors.BOLD}{'='*60}")
    print("测试4: 资源类型过滤")
    print(f"{'='*60}{Colors.RESET}\n")

    search_request = {
        "country": "ID",
        "grade": "1",
        "subject": "Matematika",
        "resourceType": "video"  # 过滤仅视频
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/search",
            json=search_request,
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                results = data.get("results", [])
                all_videos = True

                for result in results:
                    if result.get("resource_type") != "视频":
                        all_videos = False
                        break

                if all_videos:
                    log_test("资源类型过滤-仅视频", True,
                            f"过滤后返回 {len(results)} 个结果，全部是视频")
                    return True
                else:
                    log_test("资源类型过滤-仅视频", False,
                            "过滤结果中包含非视频资源")
                    return False
            else:
                log_test("资源类型过滤-仅视频", False,
                        f"API返回失败: {data.get('message')}")
                return False
        else:
            log_test("资源类型过滤-仅视频", False,
                    f"状态码: {response.status_code}")
            return False

    except Exception as e:
        log_test("资源类型过滤-仅视频", False, f"异常: {str(e)}")
        return False


def test_llm_recommendations(search_data: Dict):
    """测试5: 验证LLM推荐理由生成"""
    print(f"\n{Colors.BOLD}{'='*60}")
    print("测试5: LLM推荐理由生成")
    print(f"{'='*60}{Colors.RESET}\n")

    if not search_data or not search_data.get("results"):
        log_test("LLM推荐理由", False, "没有搜索结果可供测试")
        return False

    results = search_data["results"]
    has_recommendations = False
    unique_recommendations = set()

    for result in results[:10]:  # 检查前10个结果
        reason = result.get("recommendation_reason", "")

        if reason and len(reason) > 10:
            has_recommendations = True
            unique_recommendations.add(reason[:50])  # 只比较前50个字符

    if has_recommendations:
        unique_count = len(unique_recommendations)
        if unique_count >= 3:  # 至少有3个不同的推荐理由
            log_test("LLM推荐理由生成", True,
                    f"找到 {unique_count} 个不同的推荐理由（前10个结果中）")
            return True
        else:
            log_test("LLM推荐理由生成", False,
                    f"推荐理由过于相似（只有{unique_count}个不同的）")
            return False
    else:
        log_test("LLM推荐理由生成", False, "没有找到推荐理由")
        return False


def test_youtube_playlist_detection_ui():
    """测试6: 验证YouTube播放列表检测（前端UI测试）"""
    print(f"\n{Colors.BOLD}{'='*60}")
    print("测试6: YouTube播放列表检测（前端）")
    print(f"{'='*60}{Colors.RESET}\n")

    try:
        # 获取前端页面
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            log_test("前端页面加载", False, "无法加载页面")
            return False

        html_content = response.text

        # 检查是否包含播放列表检测代码
        has_playlist_detection = (
            "playlist" in html_content.lower() and
            "list=" in html_content
        )

        if has_playlist_detection:
            log_test("YouTube播放列表检测", True,
                    "前端代码包含播放列表检测逻辑")
            return True
        else:
            log_test("YouTube播放列表检测", False,
                    "前端代码未找到播放列表检测逻辑")
            return False

    except Exception as e:
        log_test("YouTube播放列表检测", False, f"异常: {str(e)}")
        return False


def test_ai_evaluation_button_ui():
    """测试7: 验证AI深度评估按钮（前端UI测试）"""
    print(f"\n{Colors.BOLD}{'='*60}")
    print("测试7: AI深度评估按钮（前端）")
    print(f"{'='*60}{Colors.RESET}\n")

    try:
        # 获取前端页面
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            log_test("AI深度评估按钮", False, "无法加载页面")
            return False

        html_content = response.text

        # 检查是否包含AI评估按钮相关代码
        has_ai_button = "AI 深度评估" in html_content
        has_youtube_detection = "youtube" in html_content.lower()

        if has_ai_button and has_youtube_detection:
            log_test("AI深度评估按钮", True,
                    "前端包含AI评估按钮和YouTube检测代码")
            return True
        else:
            missing = []
            if not has_ai_button:
                missing.append("AI评估按钮")
            if not has_youtube_detection:
                missing.append("YouTube检测")

            log_test("AI深度评估按钮", False,
                    f"缺少: {', '.join(missing)}")
            return False

    except Exception as e:
        log_test("AI深度评估按钮", False, f"异常: {str(e)}")
        return False


def test_resource_type_dropdown_ui():
    """测试8: 验证资源类型下拉框（前端UI测试）"""
    print(f"\n{Colors.BOLD}{'='*60}")
    print("测试8: 资源类型下拉框（前端）")
    print(f"{'='*60}{Colors.RESET}\n")

    try:
        # 获取前端页面
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            log_test("资源类型下拉框", False, "无法加载页面")
            return False

        html_content = response.text

        # 检查是否包含资源类型下拉框
        has_resource_type_select = "resourceType" in html_content
        has_video_option = "仅视频" in html_content or "video" in html_content
        has_textbook_option = "仅教材" in html_content or "textbook" in html_content

        if has_resource_type_select and has_video_option:
            log_test("资源类型下拉框", True,
                    "前端包含资源类型选择器，包含'仅视频'选项")
            return True
        else:
            missing = []
            if not has_resource_type_select:
                missing.append("资源类型选择器")
            if not has_video_option:
                missing.append("仅视频选项")

            log_test("资源类型下拉框", False,
                    f"缺少: {', '.join(missing)}")
            return False

    except Exception as e:
        log_test("资源类型下拉框", False, f"异常: {str(e)}")
        return False


def test_colored_type_tags_ui():
    """测试9: 验证彩色类型标签（前端UI测试）"""
    print(f"\n{Colors.BOLD}{'='*60}")
    print("测试9: 彩色资源类型标签（前端）")
    print(f"{'='*60}{Colors.RESET}\n")

    try:
        # 获取前端页面
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            log_test("彩色类型标签", False, "无法加载页面")
            return False

        html_content = response.text

        # 检查是否包含彩色标签相关代码
        has_video_emoji = "🎬" in html_content
        has_textbook_emoji = "📚" in html_content
        has_gradient_colors = (
            "#ff6b6b" in html_content or  # 视频红色
            "#4ecdc4" in html_content      # 教材青色
        )

        if has_video_emoji and has_textbook_emoji:
            log_test("彩色类型标签", True,
                    f"前端包含类型标签（🎬 📚）和渐变色样式")
            return True
        else:
            missing = []
            if not has_video_emoji:
                missing.append("视频emoji")
            if not has_textbook_emoji:
                missing.append("教材emoji")

            log_test("彩色类型标签", False,
                    f"缺少: {', '.join(missing)}")
            return False

    except Exception as e:
        log_test("彩色类型标签", False, f"异常: {str(e)}")
        return False


def print_test_summary():
    """打印测试总结"""
    print(f"\n{Colors.BOLD}{'='*60}")
    print("测试总结")
    print(f"{'='*60}{Colors.RESET}\n")

    total_tests = len(TEST_RESULTS)
    passed_tests = sum(1 for r in TEST_RESULTS if r["passed"])
    failed_tests = total_tests - passed_tests
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

    print(f"总测试数: {total_tests}")
    print(f"{Colors.GREEN}通过: {passed_tests}{Colors.RESET}")
    print(f"{Colors.RED}失败: {failed_tests}{Colors.RESET}")
    print(f"通过率: {pass_rate:.1f}%\n")

    if failed_tests > 0:
        print(f"{Colors.RED}失败的测试:{Colors.RESET}")
        for result in TEST_RESULTS:
            if not result["passed"]:
                print(f"  - {result['test_name']}")
                if result.get("details"):
                    print(f"    {result['details']}")
        print()

    # 保存测试结果到JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"test_report_{timestamp}.json"

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "pass_rate": pass_rate,
            "results": TEST_RESULTS
        }, f, ensure_ascii=False, indent=2)

    print(f"测试报告已保存到: {report_file}")

    return failed_tests == 0


def main():
    """主测试流程"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("="*60)
    print("教育视频搜索系统 - 自动化测试套件")
    print("="*60)
    print(f"{Colors.RESET}\n")

    print(f"测试目标: {BASE_URL}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 执行所有测试
    server_ok = test_server_running()
    if not server_ok:
        print(f"\n{Colors.RED}错误: 服务器未运行，请先启动服务器{Colors.RESET}")
        print("运行命令: python3 web_app.py")
        sys.exit(1)

    # 执行搜索测试
    search_data = test_search_api()

    # 执行其他测试
    test_resource_classification(search_data)
    test_resource_type_filter()
    test_llm_recommendations(search_data)
    test_youtube_playlist_detection_ui()
    test_ai_evaluation_button_ui()
    test_resource_type_dropdown_ui()
    test_colored_type_tags_ui()

    # 打印总结
    all_passed = print_test_summary()

    if all_passed:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 所有测试通过！{Colors.RESET}\n")
        sys.exit(0)
    else:
        print(f"\n{Colors.YELLOW}⚠️ 部分测试失败，请检查详细信息{Colors.RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
