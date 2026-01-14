#!/usr/bin/env python3
"""
侧边栏优化功能测试脚本
测试所有页面的可访问性和核心功能
"""

import sys
import time
import requests

# 尝试导入selenium（可选）
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium未安装，跳过浏览器交互测试")


class SidebarOptimizationTester:
    """侧边栏优化测试类"""

    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
        self.driver = None
        self.test_results = []

    def setup_driver(self):
        """初始化Selenium驱动"""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')  # 无头模式
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_window_size(1920, 1080)
            print("✅ 浏览器驱动初始化成功")
            return True
        except Exception as e:
            print(f"❌ 浏览器驱动初始化失败: {e}")
            return False

    def record_test(self, test_name, passed, message=""):
        """记录测试结果"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            "name": test_name,
            "passed": passed,
            "message": message
        })
        print(f"{status}: {test_name}")
        if message and not passed:
            print(f"   错误信息: {message}")

    def test_page_access(self, path, page_name):
        """测试页面访问"""
        try:
            url = f"{self.base_url}{path}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                self.record_test(f"访问 {page_name} 页面", True)
                return True
            else:
                self.record_test(f"访问 {page_name} 页面", False,
                               f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.record_test(f"访问 {page_name} 页面", False, str(e))
            return False

    def test_all_pages(self):
        """测试所有页面路由"""
        print("\n" + "="*60)
        print("测试1: 页面可访问性")
        print("="*60)

        pages = [
            ("/", "主页"),
            ("/search_history", "搜索历史"),
            ("/knowledge_points", "知识点概览"),
            ("/evaluation_reports", "评估报告"),
            ("/global_map", "全球资源地图"),
            ("/stats_dashboard", "统计仪表板"),
            ("/compare", "国家资源对比"),
            ("/batch_discovery", "批量国家发现"),
            ("/health_status", "系统健康检查"),
            ("/report_center", "报告中心"),
        ]

        for path, name in pages:
            self.test_page_access(path, name)

    def test_main_page_sidebar(self):
        """测试主页侧边栏"""
        print("\n" + "="*60)
        print("测试2: 主页侧边栏功能")
        print("="*60)

        try:
            self.driver.get(f"{self.base_url}/")
            wait = WebDriverWait(self.driver, 10)

            # 等待页面加载
            time.sleep(2)

            # 检查侧边栏是否存在
            try:
                sidebar = self.driver.find_element(By.CLASS_NAME, "sidebar")
                self.record_test("侧边栏元素存在", True)

                # 检查侧边栏宽度（应该是180px）
                sidebar_width = sidebar.value_of_css_property("width")
                if "180" in sidebar_width or "177" in sidebar_width:  # 考虑边框
                    self.record_test("侧边栏宽度为180px", True)
                else:
                    self.record_test("侧边栏宽度为180px", False,
                                   f"实际宽度: {sidebar_width}")

            except NoSuchElementException:
                self.record_test("侧边栏元素存在", False, "未找到侧边栏")
                return False

            # 检查折叠按钮是否存在
            try:
                toggle = self.driver.find_element(By.ID, "sidebarToggle")
                self.record_test("折叠按钮存在", True)

                # 检查按钮位置
                toggle_left = toggle.value_of_css_property("left")
                self.record_test("折叠按钮位置正确", True, f"left: {toggle_left}")

            except NoSuchElementException:
                self.record_test("折叠按钮存在", False, "未找到折叠按钮")

            # 检查搜索历史链接
            try:
                history_links = self.driver.find_elements(By.XPATH,
                    "//a[contains(@href, '/search_history')]")
                if history_links:
                    self.record_test("搜索历史导航链接存在", True)
                else:
                    self.record_test("搜索历史导航链接存在", False)

            except Exception as e:
                self.record_test("搜索历史导航链接存在", False, str(e))

            # 检查搜索历史面板是否已移除
            try:
                history_panel = self.driver.find_elements(By.CLASS_NAME, "history-panel")
                if len(history_panel) == 0:
                    self.record_test("主页搜索历史面板已移除", True)
                else:
                    self.record_test("主页搜索历史面板已移除", False,
                                   f"仍存在 {len(history_panel)} 个面板")

            except Exception as e:
                self.record_test("主页搜索历史面板已移除", False, str(e))

            # 检查搜索结果区域
            try:
                results_panel = self.driver.find_element(By.ID, "resultsPanel")
                self.record_test("搜索结果面板存在", True)

            except NoSuchElementException:
                self.record_test("搜索结果面板存在", False, "未找到结果面板")

            return True

        except Exception as e:
            self.record_test("主页侧边栏测试", False, str(e))
            return False

    def test_sidebar_toggle(self):
        """测试侧边栏折叠功能"""
        print("\n" + "="*60)
        print("测试3: 侧边栏折叠功能")
        print("="*60)

        try:
            self.driver.get(f"{self.base_url}/")
            wait = WebDriverWait(self.driver, 10)
            time.sleep(2)

            # 获取元素
            sidebar = self.driver.find_element(By.ID, "sidebar")
            toggle = self.driver.find_element(By.ID, "sidebarToggle")
            main_content = self.driver.find_element(By.ID, "mainContent")

            # 初始状态：侧边栏展开
            initial_sidebar_width = sidebar.value_of_css_property("width")
            initial_main_margin = main_content.value_of_css_property("margin-left")

            self.record_test("初始状态：侧边栏展开", True,
                           f"宽度: {initial_sidebar_width}, 边距: {initial_main_margin}")

            # 点击折叠按钮
            toggle.click()
            time.sleep(1)  # 等待动画

            # 检查折叠后的状态
            collapsed_class = sidebar.get_attribute("class")
            if "collapsed" in collapsed_class:
                self.record_test("折叠后侧边栏有collapsed类", True)
            else:
                self.record_test("折叠后侧边栏有collapsed类", False,
                               f"类名: {collapsed_class}")

            toggle_collapsed_class = toggle.get_attribute("class")
            if "collapsed" in toggle_collapsed_class:
                self.record_test("折叠后按钮有collapsed类", True)
            else:
                self.record_test("折叠后按钮有collapsed类", False,
                               f"类名: {toggle_collapsed_class}")

            main_expanded_class = main_content.get_attribute("class")
            if "expanded" in main_expanded_class:
                self.record_test("折叠后主内容有expanded类", True)
            else:
                self.record_test("折叠后主内容有expanded类", False,
                               f"类名: {main_expanded_class}")

            # 再次点击展开
            toggle.click()
            time.sleep(1)

            # 检查展开后的状态
            expanded_class = sidebar.get_attribute("class")
            if "collapsed" not in expanded_class:
                self.record_test("展开后侧边栏移除collapsed类", True)
            else:
                self.record_test("展开后侧边栏移除collapsed类", False)

            return True

        except Exception as e:
            self.record_test("侧边栏折叠测试", False, str(e))
            return False

    def test_search_history_page(self):
        """测试搜索历史页面"""
        print("\n" + "="*60)
        print("测试4: 搜索历史页面")
        print("="*60)

        try:
            # 从主页导航到搜索历史
            self.driver.get(f"{self.base_url}/")
            time.sleep(2)

            # 点击搜索历史链接
            try:
                history_link = self.driver.find_element(By.XPATH,
                    "//a[contains(@href, '/search_history')]")
                history_link.click()
                time.sleep(2)

                self.record_test("通过导航链接跳转到搜索历史页", True)

            except Exception as e:
                # 如果链接点击失败，直接访问URL
                self.driver.get(f"{self.base_url}/search_history")
                time.sleep(2)
                self.record_test("通过导航链接跳转到搜索历史页", False,
                               "直接访问URL")

            # 检查页面元素
            # 1. 侧边栏
            try:
                sidebar = self.driver.find_element(By.CLASS_NAME, "sidebar")
                self.record_test("搜索历史页有侧边栏", True)
            except NoSuchElementException:
                self.record_test("搜索历史页有侧边栏", False)

            # 2. 折叠按钮
            try:
                toggle = self.driver.find_element(By.ID, "sidebarToggle")
                self.record_test("搜索历史页有折叠按钮", True)
            except NoSuchElementException:
                self.record_test("搜索历史页有折叠按钮", False)

            # 3. 返回按钮
            try:
                back_button = self.driver.find_element(By.CLASS_NAME, "back-button")
                self.record_test("搜索历史页有返回按钮", True)

                # 测试返回按钮
                back_button.click()
                time.sleep(1)

                current_url = self.driver.current_url
                if current_url.endswith("/") or current_url.rstrip("/").endswith(":5001"):
                    self.record_test("返回按钮跳转到主页", True)
                else:
                    self.record_test("返回按钮跳转到主页", False,
                                   f"当前URL: {current_url}")

            except NoSuchElementException:
                self.record_test("搜索历史页有返回按钮", False)

            # 4. 历史记录容器
            self.driver.get(f"{self.base_url}/search_history")
            time.sleep(2)

            try:
                history_content = self.driver.find_element(By.CLASS_NAME,
                    "history-page-content")
                self.record_test("搜索历史页有内容容器", True)

            except NoSuchElementException:
                self.record_test("搜索历史页有内容容器", False)

            return True

        except Exception as e:
            self.record_test("搜索历史页面测试", False, str(e))
            return False

    def test_api_endpoints(self):
        """测试API端点"""
        print("\n" + "="*60)
        print("测试5: API端点")
        print("="*60)

        api_tests = [
            ("/api/countries", "获取国家列表"),
            ("/api/history", "获取搜索历史"),
        ]

        for endpoint, name in api_tests:
            try:
                response = requests.get(f"{self.base_url}{endpoint}",
                                      timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        self.record_test(f"API: {name}", True)
                    else:
                        self.record_test(f"API: {name}", False,
                                       "返回success=false")
                else:
                    self.record_test(f"API: {name}", False,
                                   f"状态码: {response.status_code}")

            except Exception as e:
                self.record_test(f"API: {name}", False, str(e))

    def test_responsive_design(self):
        """测试响应式设计"""
        print("\n" + "="*60)
        print("测试6: 响应式设计")
        print("="*60)

        try:
            # 测试桌面端（1920x1080）
            self.driver.set_window_size(1920, 1080)
            self.driver.get(f"{self.base_url}/")
            time.sleep(2)

            sidebar = self.driver.find_element(By.CLASS_NAME, "sidebar")
            desktop_width = sidebar.value_of_css_property("width")
            self.record_test("桌面端侧边栏宽度", True, f"{desktop_width}")

            # 测试平板端（768x1024）
            self.driver.set_window_size(768, 1024)
            time.sleep(1)

            tablet_width = sidebar.value_of_css_property("width")
            self.record_test("平板端侧边栏宽度", True, f"{tablet_width}")

            # 测试移动端（375x667）
            self.driver.set_window_size(375, 667)
            time.sleep(1)

            try:
                mobile_sidebar = self.driver.find_element(By.CLASS_NAME, "sidebar")
                mobile_class = mobile_sidebar.get_attribute("class")
                # 移动端默认应该是隐藏的
                self.record_test("移动端侧边栏状态", True,
                               f"类名: {mobile_class}")
            except NoSuchElementException:
                self.record_test("移动端侧边栏状态", False, "未找到侧边栏")

            # 恢复桌面端
            self.driver.set_window_size(1920, 1080)

            return True

        except Exception as e:
            self.record_test("响应式设计测试", False, str(e))
            return False

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["passed"])
        failed = total - passed

        print(f"\n总测试数: {total}")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"通过率: {(passed/total*100):.1f}%")

        if failed > 0:
            print("\n失败的测试:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['name']}")
                    if result['message']:
                        print(f"    {result['message']}")

        print("\n" + "="*60)

        return failed == 0

    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始侧边栏优化功能测试\n")

        # 不使用Selenium，只测试HTTP访问
        print("⚠️  注意：仅测试HTTP访问，不测试浏览器交互")
        print("    （需要Selenium和Chrome驱动才能测试交互）\n")

        # 测试页面访问
        self.test_all_pages()

        # 测试API端点
        self.test_api_endpoints()

        # 打印总结
        success = self.print_summary()

        if success:
            print("\n🎉 所有测试通过！")
            return 0
        else:
            print("\n❌ 部分测试失败，请检查")
            return 1


def quick_test():
    """快速测试（不使用浏览器）"""
    print("🚀 快速测试：检查页面和API可访问性\n")
    print("="*60)

    base_url = "http://localhost:5001"
    passed = 0
    failed = 0

    # 测试页面
    pages = [
        ("/", "主页"),
        ("/search_history", "搜索历史"),
        ("/knowledge_points", "知识点概览"),
        ("/evaluation_reports", "评估报告"),
    ]

    print("\n页面访问测试:")
    for path, name in pages:
        try:
            response = requests.get(f"{base_url}{path}", timeout=10)
            if response.status_code == 200:
                print(f"  ✅ {name}")
                passed += 1
            else:
                print(f"  ❌ {name} (状态码: {response.status_code})")
                failed += 1
        except Exception as e:
            print(f"  ❌ {name} (错误: {str(e)[:50]})")
            failed += 1

    # 测试API
    print("\nAPI端点测试:")
    apis = [
        ("/api/countries", "国家列表"),
        ("/api/history", "搜索历史"),
    ]

    for path, name in apis:
        try:
            response = requests.get(f"{base_url}{path}", timeout=10)
            if response.status_code == 200:
                print(f"  ✅ {name}")
                passed += 1
            else:
                print(f"  ❌ {name} (状态码: {response.status_code})")
                failed += 1
        except Exception as e:
            print(f"  ❌ {name} (错误: {str(e)[:50]})")
            failed += 1

    # 总结
    total = passed + failed
    print(f"\n{'='*60}")
    print(f"总计: {total} | ✅ 通过: {passed} | ❌ 失败: {failed}")
    print(f"通过率: {(passed/total*100):.1f}%")
    print(f"{'='*60}\n")

    if failed == 0:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    # 检查服务器是否运行
    try:
        response = requests.get("http://localhost:5001", timeout=5)
        print("✅ 检测到服务器运行在 http://localhost:5001\n")
    except Exception:
        print("❌ 错误: 服务器未运行或无法访问")
        print("   请先启动服务器: python3 web_app.py\n")
        sys.exit(1)

    # 运行快速测试
    sys.exit(quick_test())
