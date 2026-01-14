#!/usr/bin/env python3
"""
AI深度评估功能专项测试

测试范围：
1. 简化版AI评估（基于URL）
2. 高级版AI评估（视频下载）- 如已实现
3. YouTube播放列表检测
4. 非YouTube资源限制
"""

import requests
import json
import sys
import time
from datetime import datetime

# 配置
BASE_URL = "http://localhost:5001"

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print(text)
    print(f"{'='*60}{Colors.RESET}\n")


def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")


def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")


def print_info(text):
    print(f"{Colors.YELLOW}ℹ️  {text}{Colors.RESET}")


def test_simple_ai_evaluation():
    """测试简化版AI评估（基于URL，不下载视频）"""
    print_header("测试1: 简化版AI评估（基于URL）")

    # 测试URL（YouTube单个视频）
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    evaluation_request = {
        "video_url": test_url,
        "title": "Test Video for AI Evaluation",
        "snippet": "This is a test video for AI evaluation functionality",
        "search_params": {
            "country": "ID",
            "grade": "1",
            "subject": "Matematika"
        }
    }

    print_info(f"测试URL: {test_url}")
    print_info("发送AI评估请求...")

    try:
        # 注意：这个端点可能还不存在，需要根据实际实现调整
        response = requests.post(
            f"{BASE_URL}/api/analyze_video",
            json=evaluation_request,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print_success("AI评估请求成功")

                evaluation = data.get("evaluation", {})
                if evaluation:
                    overall_score = evaluation.get("overall_score", 0)
                    print_success(f"评估完成，总分: {overall_score}/10")

                    # 打印各项评分
                    scores = {
                        "内容相关性": evaluation.get("content_relevance"),
                        "教学质量": evaluation.get("teaching_quality"),
                        "内容准确性": evaluation.get("accuracy"),
                        "适合程度": evaluation.get("appropriateness"),
                        "视频质量": evaluation.get("video_quality"),
                        "互动性": evaluation.get("interactivity"),
                        "教育价值": evaluation.get("educational_value"),
                    }

                    print("\n各项评分:")
                    for name, score in scores.items():
                        if score is not None:
                            print(f"  {name}: {score}/10")

                    # 打印优缺点
                    strengths = evaluation.get("strengths", [])
                    weaknesses = evaluation.get("weaknesses", [])

                    if strengths:
                        print(f"\n{Colors.GREEN}优点:{Colors.RESET}")
                        for s in strengths:
                            print(f"  - {s}")

                    if weaknesses:
                        print(f"\n{Colors.YELLOW}不足:{Colors.RESET}")
                        for w in weaknesses:
                            print(f"  - {w}")

                    return True
                else:
                    print_error("评估结果为空")
                    return False
            else:
                print_error(f"AI评估失败: {data.get('message')}")
                return False
        else:
            print_error(f"HTTP错误: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print_error(f"请求异常: {str(e)}")
        print_info("注意: /api/analyze_video 端点可能还未实现")
        return False
    except Exception as e:
        print_error(f"未知异常: {str(e)}")
        return False


def test_youtube_playlist_detection():
    """测试YouTube播放列表URL检测"""
    print_header("测试2: YouTube播放列表URL检测")

    # 测试URL
    test_cases = [
        {
            "url": "https://www.youtube.com/playlist?list=PLBGjTP24UKQ9Q4c18PFkG_sf3uf5Q3aom",
            "is_playlist": True,
            "description": "标准播放列表URL"
        },
        {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLBGjTP24UKQ9Q4c18PFkG_sf3uf5Q3aom",
            "is_playlist": True,
            "description": "带list参数的视频URL"
        },
        {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "is_playlist": False,
            "description": "普通单个视频URL"
        },
        {
            "url": "https://youtu.be/dQw4w9WgXcQ",
            "is_playlist": False,
            "description": "短链接单个视频"
        }
    ]

    all_correct = True

    for i, test_case in enumerate(test_cases, 1):
        url = test_case["url"]
        expected = test_case["is_playlist"]
        desc = test_case["description"]

        # 简单的播放列表检测逻辑
        is_playlist = (
            "playlist" in url.lower() or
            ("list=" in url and "youtube.com" in url.lower())
        )

        print(f"\n测试用例 {i}: {desc}")
        print(f"  URL: {url[:60]}...")
        print(f"  预期: {'播放列表' if expected else '单个视频'}")
        print(f"  实际: {'播放列表' if is_playlist else '单个视频'}")

        if is_playlist == expected:
            print_success(f"测试用例 {i} 通过")
        else:
            print_error(f"测试用例 {i} 失败 - 检测结果不符合预期")
            all_correct = False

    return all_correct


def test_youtube_vs_non_youtube():
    """测试YouTube vs 非YouTube资源"""
    print_header("测试3: YouTube vs 非YouTube资源检测")

    test_cases = [
        {
            "url": "https://www.youtube.com/watch?v=test",
            "is_youtube": True,
            "description": "YouTube视频"
        },
        {
            "url": "https://youtu.be/test",
            "is_youtube": True,
            "description": "YouTube短链接"
        },
        {
            "url": "https://vimeo.com/123456789",
            "is_youtube": False,
            "description": "Vimeo视频"
        },
        {
            "url": "https://ruangguru.com/video/test",
            "is_youtube": False,
            "description": "Ruangguru视频"
        },
        {
            "url": "https://example.com/resource.pdf",
            "is_youtube": False,
            "description": "PDF文档"
        }
    ]

    all_correct = True

    for i, test_case in enumerate(test_cases, 1):
        url = test_case["url"]
        expected = test_case["is_youtube"]
        desc = test_case["description"]

        # YouTube检测逻辑
        is_youtube = bool(
            "youtube.com" in url.lower() or
            "youtu.be" in url.lower()
        )

        print(f"\n测试用例 {i}: {desc}")
        print(f"  URL: {url}")
        print(f"  预期: {'YouTube' if expected else '非YouTube'}")
        print(f"  实际: {'YouTube' if is_youtube else '非YouTube'}")

        if is_youtube == expected:
            print_success(f"测试用例 {i} 通过")
        else:
            print_error(f"测试用例 {i} 失败")
            all_correct = False

    return all_correct


def test_ai_evaluation_endpoint_availability():
    """测试AI评估端点是否可用"""
    print_header("测试4: AI评估端点可用性检查")

    endpoints = [
        "/api/analyze_video",          # 简化版评估
        "/api/analyze_video_advanced", # 高级版评估（可能未实现）
    ]

    available_endpoints = []

    for endpoint in endpoints:
        print_info(f"检查端点: {endpoint}")

        try:
            # 发送一个简单的请求来测试端点是否存在
            response = requests.post(
                f"{BASE_URL}{endpoint}",
                json={"test": "test"},
                timeout=5
            )

            if response.status_code != 404:
                available_endpoints.append(endpoint)
                print_success(f"端点 {endpoint} 可用（状态码: {response.status_code}）")
            else:
                print_info(f"端点 {endpoint} 不存在（404）")

        except requests.exceptions.RequestException as e:
            print_info(f"端点 {endpoint} 请求失败: {str(e)[:50]}...")

    if available_endpoints:
        print_success(f"\n可用的AI评估端点: {', '.join(available_endpoints)}")
        return True
    else:
        print_error("\n没有找到可用的AI评估端点")
        print_info("提示: AI评估端点可能还未实现")
        return False


def test_frontend_ui_elements():
    """测试前端UI元素（通过HTML检查）"""
    print_header("测试5: 前端UI元素检查")

    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print_error("无法加载前端页面")
            return False

        html = response.text

        # 检查关键UI元素
        checks = [
            ("AI深度评估按钮", "AI 深度评估", True),
            ("YouTube检测代码", "youtube", True),
            ("播放列表检测", "playlist", True),
            ("AI评估Modal", "analyzeModal", True),
            ("资源类型标签", "resource_type", True),
        ]

        all_present = True

        for name, keyword, expected in checks:
            is_present = keyword in html
            status = "存在" if is_present else "缺失"

            if is_present == expected:
                print_success(f"{name}: {status}")
            else:
                print_error(f"{name}: {status}（不符合预期）")
                all_present = False

        return all_present

    except Exception as e:
        print_error(f"检查失败: {str(e)}")
        return False


def print_summary(results):
    """打印测试总结"""
    print_header("测试总结")

    total = len(results)
    passed = sum(1 for r in results if r)
    failed = total - failed

    print(f"总测试数: {total}")
    print(f"{Colors.GREEN}通过: {passed}{Colors.RESET}")
    print(f"{Colors.RED}失败: {failed}{Colors.RESET}")

    if failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 所有测试通过！{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠️ 部分测试未通过{Colors.RESET}\n")
        return 1


def main():
    """主测试流程"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("="*60)
    print("AI深度评估功能 - 专项测试")
    print("="*60)
    print(f"{Colors.RESET}\n")

    print(f"测试目标: {BASE_URL}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # 执行所有测试
    results.append(test_youtube_playlist_detection())
    results.append(test_youtube_vs_non_youtube())
    results.append(test_ai_evaluation_endpoint_availability())
    results.append(test_frontend_ui_elements())

    # 简化版AI评估测试（可能失败，因为端点可能还未实现）
    print_info("\n注意: 以下测试需要API端点支持，可能会失败")
    results.append(test_simple_ai_evaluation())

    # 打印总结
    exit_code = print_summary(results)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
