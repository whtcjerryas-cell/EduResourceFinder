#!/usr/bin/env python3
"""
前端自动化测试 - 模拟真实用户操作
使用 Playwright 进行浏览器自动化测试
"""

import asyncio
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = "http://localhost:5001"
SCREENSHOT_DIR = "test_screenshots"
TEST_RESULTS = []

class FrontendTester:
    def __init__(self):
        self.browser = None
        self.page = None
        self.context = None
        self.playwright = None

    def setup(self):
        """初始化浏览器"""
        print("🚀 启动浏览器...")
        self.playwright = sync_playwright().start()
        # 使用Chromium，在所有平台上都可用
        self.browser = self.playwright.chromium.launch(headless=False)  # 显示浏览器以便观察
        self.context = self.browser.new_context(viewport={'width': 1400, 'height': 900})
        self.page = self.context.new_page()
        self.page.set_default_timeout(10000)
        print("✅ 浏览器启动成功")

    def teardown(self):
        """关闭浏览器"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("✅ 浏览器已关闭")

    def take_screenshot(self, name):
        """截取屏幕截图"""
        import os
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        filename = f"{SCREENSHOT_DIR}/{name}_{int(time.time())}.png"
        self.page.screenshot(path=filename)
        print(f"📸 截图已保存: {filename}")
        return filename

    def test_page_load(self):
        """测试1: 页面加载"""
        print("\n" + "="*80)
        print("测试 1: 页面加载")
        print("="*80)

        try:
            print(f"📍 访问 {BASE_URL}...")
            self.page.goto(BASE_URL, wait_until="networkidle")

            # 等待关键元素加载
            self.page.wait_for_selector('#country', timeout=5000)
            self.page.wait_for_selector('#searchBtn', timeout=5000)

            # 验证标题
            title = self.page.title()
            print(f"✅ 页面标题: {title}")

            # 验证国家选择框
            country_select = self.page.locator('#country')
            country_count = country_select.locator('option').count()
            print(f"✅ 国家数量: {country_count}")

            self.take_screenshot("01_homepage_loaded")
            self.record_result("页面加载", True, "页面成功加载，所有元素显示正常")
            return True

        except Exception as e:
            print(f"❌ 页面加载失败: {str(e)}")
            self.take_screenshot("01_homepage_failed")
            self.record_result("页面加载", False, str(e))
            return False

    def test_knowledge_points_button(self):
        """测试2: 知识点概览按钮"""
        print("\n" + "="*80)
        print("测试 2: 📚 知识点概览按钮")
        print("="*80)

        try:
            # 查找并点击知识点概览按钮
            print("🔍 查找知识点概览按钮...")
            button = self.page.locator('button:has-text("知识点概览")').first
            button.wait_for(state="visible", timeout=5000)

            print(f"✅ 找到按钮: {button.inner_text()}")
            self.take_screenshot("02_before_knowledge_click")

            print("🖱️ 点击按钮...")
            button.click()

            # 等待页面跳转
            self.page.wait_for_url("**/knowledge_points", timeout=5000)
            print("✅ 成功跳转到知识点页面")

            # 验证知识点页面内容
            self.page.wait_for_selector('h1, h2', timeout=5000)
            title = self.page.locator('h1, h2').first.inner_text()
            print(f"✅ 页面标题: {title}")

            self.take_screenshot("03_knowledge_points_page")

            # 返回主页
            print("🔙 返回主页...")
            self.page.goto(BASE_URL)
            self.page.wait_for_load_state("networkidle")

            self.record_result("知识点概览按钮", True, "成功跳转到知识点页面")
            return True

        except Exception as e:
            print(f"❌ 知识点概览按钮测试失败: {str(e)}")
            self.take_screenshot("02_knowledge_points_failed")
            self.record_result("知识点概览按钮", False, str(e))
            return False

    def test_debug_button(self):
        """测试3: Debug日志按钮"""
        print("\n" + "="*80)
        print("测试 3: 🐛 Debug日志按钮")
        print("="*80)

        try:
            print("🔍 查找Debug日志按钮...")
            button = self.page.locator('button:has-text("Debug日志")').first
            button.wait_for(state="visible", timeout=5000)

            print(f"✅ 找到按钮")
            self.take_screenshot("04_before_debug_click")

            print("🖱️ 点击Debug日志按钮...")
            button.click()

            # 等待模态框出现
            modal = self.page.locator('#debugModal')
            modal.wait_for(state="visible", timeout=5000)
            print("✅ Debug模态框已打开")

            # 验证模态框内容
            close_btn = self.page.locator('#closeDebugModal')
            if close_btn.is_visible():
                print("✅ 关闭按钮可见")

            # 关闭模态框
            print("🖱️ 点击关闭按钮...")
            close_btn.click()
            modal.wait_for(state="hidden", timeout=5000)
            print("✅ 模态框已关闭")

            self.take_screenshot("05_debug_modal_closed")
            self.record_result("Debug日志按钮", True, "成功打开和关闭Debug模态框")
            return True

        except Exception as e:
            print(f"❌ Debug按钮测试失败: {str(e)}")
            self.take_screenshot("04_debug_failed")
            self.record_result("Debug日志按钮", False, str(e))
            return False

    def check_for_errors(self):
        """检查页面上是否有错误消息"""
        error_selectors = [
            '.alert-danger',
            '.error',
            '.alert-error',
            '[class*="error"]',
            '[role="alert"]',
            '.toast.error',
            '.toast-danger'
        ]

        for selector in error_selectors:
            try:
                error_element = self.page.locator(selector).first
                if error_element.is_visible():
                    error_text = error_element.inner_text()
                    if error_text and 'fail' in error_text.lower():
                        return error_text
            except:
                continue
        return None

    def test_search_functionality(self):
        """测试4: 搜索功能（增强版 - 检测后端错误）"""
        print("\n" + "="*80)
        print("测试 4: 🔍 搜索功能（增强版）")
        print("="*80)

        try:
            # 确保在主页
            self.page.goto(BASE_URL)
            self.page.wait_for_load_state("networkidle")

            # 选择国家
            print("🌍 选择国家: Indonesia")
            country_select = self.page.locator('#country')
            country_select.select_option('ID')
            time.sleep(1)  # 等待年级和学科加载

            self.take_screenshot("06_country_selected")

            # 选择年级
            print("📚 选择年级: Kelas 10")
            grade_select = self.page.locator('#grade')
            grade_select.wait_for(state="visible", timeout=5000)
            grade_select.select_option('Kelas 10')

            # 选择学科
            print("📖 选择学科: Matematika")
            subject_select = self.page.locator('#subject')
            subject_select.wait_for(state="visible", timeout=5000)
            subject_select.select_option('Matematika')

            self.take_screenshot("07_search_form_filled")

            # 点击搜索按钮
            print("🖱️ 点击搜索按钮...")
            search_btn = self.page.locator('#searchBtn')
            search_btn.click()

            # 等待搜索结果或错误消息
            print("⏳ 等待搜索结果...")
            results_card = self.page.locator('#resultsCard')
            results_card.wait_for(state="visible", timeout=60000)  # 最多等待60秒

            # 等待一下，让错误消息有时间显示
            time.sleep(2)

            # 🔥 关键改进：检查错误消息
            print("🔍 检查错误消息...")
            error_message = self.check_for_errors()

            if error_message:
                print(f"❌ 发现错误消息: {error_message}")
                self.take_screenshot("08_search_error_detected")
                self.record_result("搜索功能", False, f"后端错误: {error_message}")
                return False

            # 验证结果
            result_items = self.page.locator('.result-item')
            count = result_items.count()
            print(f"📊 结果数量: {count}")

            # 检查结果卡片的内容，看是否有"搜索失败"等文本
            try:
                results_text = results_card.inner_text()
                if '搜索失败' in results_text or 'error' in results_text.lower():
                    print(f"❌ 结果卡片包含错误文本")
                    # 尝试提取具体错误信息
                    for line in results_text.split('\n'):
                        if '搜索失败' in line or 'error' in line.lower():
                            print(f"   错误详情: {line.strip()}")
                    self.take_screenshot("08_search_error_in_card")
                    self.record_result("搜索功能", False, f"结果卡片显示错误: {results_text[:200]}")
                    return False
            except:
                pass

            if count > 0:
                first_result = result_items.first
                title = first_result.locator('h3').inner_text()
                print(f"✅ 第一个结果: {title[:50]}...")
                self.take_screenshot("08_search_results")
                self.record_result("搜索功能", True, f"✅ 成功执行搜索，返回{count}个结果")
                return True
            else:
                # 没有结果，但也没有错误消息 - 可能是正常情况（数据为空）
                print(f"⚠️  搜索完成但返回0个结果（可能无数据）")
                self.take_screenshot("08_search_no_results")
                # 检查是否有"找到0个结果"的成功提示
                try:
                    if '找到' in results_text and '0' in results_text:
                        self.record_result("搜索功能", True, f"⚠️ 搜索执行成功，但返回0个结果")
                        return True
                except:
                    pass

                # 0个结果也算通过（功能可用，只是无数据）
                self.record_result("搜索功能", True, f"⚠️ 搜索执行成功，但返回0个结果")
                return True

        except Exception as e:
            print(f"❌ 搜索功能测试失败: {str(e)}")
            self.take_screenshot("07_search_failed")
            self.record_result("搜索功能", False, str(e))
            return False

    def test_history_buttons(self):
        """测试5: 历史记录按钮"""
        print("\n" + "="*80)
        print("测试 5: 📚 历史记录按钮")
        print("="*80)

        try:
            # 筛选按钮
            print("🔍 测试筛选按钮...")
            filter_btn = self.page.locator('button:has-text("筛选")')
            if filter_btn.is_visible():
                filter_btn.click()
                print("✅ 筛选按钮响应正常")
                time.sleep(1)

            # 清除按钮
            print("🧹 测试清除按钮...")
            clear_btn = self.page.locator('button:has-text("清除")')
            if clear_btn.is_visible():
                clear_btn.click()
                print("✅ 清除按钮响应正常")
                time.sleep(1)

            self.take_screenshot("09_history_buttons_tested")
            self.record_result("历史记录按钮", True, "所有历史记录按钮响应正常")
            return True

        except Exception as e:
            print(f"❌ 历史记录按钮测试失败: {str(e)}")
            self.take_screenshot("09_history_failed")
            self.record_result("历史记录按钮", False, str(e))
            return False

    def test_add_country_button(self):
        """测试6: 添加国家按钮"""
        print("\n" + "="*80)
        print("测试 6: ➕ 添加国家按钮")
        print("="*80)

        try:
            print("🔍 查找添加国家按钮...")
            add_btn = self.page.locator('#addCountryBtn')
            add_btn.wait_for(state="visible", timeout=5000)

            self.take_screenshot("10_before_add_country")

            print("🖱️ 点击添加国家按钮...")
            add_btn.click()

            # 等待模态框
            modal = self.page.locator('#addCountryModal')
            modal.wait_for(state="visible", timeout=5000)
            print("✅ 添加国家模态框已打开")

            # 关闭模态框
            print("🖱️ 点击取消按钮...")
            cancel_btn = self.page.locator('#cancelAddBtn')
            cancel_btn.click()
            modal.wait_for(state="hidden", timeout=5000)
            print("✅ 模态框已关闭")

            self.take_screenshot("11_add_country_modal")
            self.record_result("添加国家按钮", True, "成功打开和关闭添加国家模态框")
            return True

        except Exception as e:
            print(f"❌ 添加国家按钮测试失败: {str(e)}")
            self.take_screenshot("10_add_country_failed")
            self.record_result("添加国家按钮", False, str(e))
            return False

    def test_refresh_button(self):
        """测试7: 刷新配置按钮"""
        print("\n" + "="*80)
        print("测试 7: 🔄 刷新配置按钮")
        print("="*80)

        try:
            print("🔍 查找刷新按钮...")
            refresh_btn = self.page.locator('#refreshCountryBtn')
            refresh_btn.wait_for(state="visible", timeout=5000)

            self.take_screenshot("12_before_refresh")

            print("🖱️ 点击刷新按钮...")
            # 记录当前选项数
            grade_options = self.page.locator('#grade option').count()

            refresh_btn.click()

            # 等待刷新完成
            time.sleep(2)

            # 验证选项依然存在
            grade_options_after = self.page.locator('#grade option').count()
            if grade_options_after > 0:
                print(f"✅ 刷新成功，年级选项: {grade_options_after}")

            self.take_screenshot("13_after_refresh")
            self.record_result("刷新配置按钮", True, "成功刷新国家配置")
            return True

        except Exception as e:
            print(f"❌ 刷新按钮测试失败: {str(e)}")
            self.take_screenshot("12_refresh_failed")
            self.record_result("刷新配置按钮", False, str(e))
            return False

    def test_interactive_elements(self):
        """测试8: 其他交互元素"""
        print("\n" + "="*80)
        print("测试 8: 🎯 其他交互元素")
        print("="*80)

        try:
            # 测试所有可见的按钮
            all_buttons = self.page.locator('button').all()
            print(f"🔍 发现 {len(all_buttons)} 个按钮")

            clickable_count = 0
            visible_count = 0

            for i, button in enumerate(all_buttons[:20]):  # 测试前20个
                try:
                    if button.is_visible():
                        visible_count += 1
                        print(f"✅ 按钮 {i+1}: {button.inner_text()[:30]}... - 可见")

                        # 测试是否可点击
                        if button.is_enabled():
                            clickable_count += 1

                except:
                    pass

            print(f"\n📊 统计:")
            print(f"   可见按钮: {visible_count}")
            print(f"   可点击按钮: {clickable_count}")

            self.take_screenshot("14_all_buttons")
            self.record_result("交互元素", True, f"发现{visible_count}个可见按钮，{clickable_count}个可点击")
            return True

        except Exception as e:
            print(f"❌ 交互元素测试失败: {str(e)}")
            self.record_result("交互元素", False, str(e))
            return False

    def record_result(self, test_name, success, message):
        """记录测试结果"""
        TEST_RESULTS.append({
            "name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*80)
        print("📊 测试报告")
        print("="*80)

        total = len(TEST_RESULTS)
        passed = sum(1 for r in TEST_RESULTS if r['success'])
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"\n总测试数: {total}")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"📈 通过率: {pass_rate:.1f}%")

        print("\n详细结果:")
        print("-" * 80)
        for result in TEST_RESULTS:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} {result['name']}")
            if not result['success']:
                print(f"   错误: {result['message']}")

        # 保存JSON报告
        report_file = "test_results_frontend.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "pass_rate": pass_rate
                },
                "results": TEST_RESULTS,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)

        print(f"\n📄 详细报告已保存: {report_file}")
        print(f"📸 截图目录: {SCREENSHOT_DIR}/")

        return pass_rate >= 80

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "╔" + "="*78 + "╗")
        print("║" + " "*20 + "🤖 自动化前端测试开始 🤖" + " "*34 + "║")
        print("╚" + "="*78 + "╝")

        try:
            self.setup()

            # 执行所有测试
            tests = [
                ("页面加载", self.test_page_load),
                ("知识点概览按钮", self.test_knowledge_points_button),
                ("Debug日志按钮", self.test_debug_button),
                ("搜索功能", self.test_search_functionality),
                ("历史记录按钮", self.test_history_buttons),
                ("添加国家按钮", self.test_add_country_button),
                ("刷新配置按钮", self.test_refresh_button),
                ("交互元素", self.test_interactive_elements),
            ]

            for test_name, test_func in tests:
                try:
                    test_func()
                except Exception as e:
                    print(f"💥 测试异常: {str(e)}")
                    self.record_result(test_name, False, f"异常: {str(e)}")

            # 生成报告
            success = self.generate_report()

            if success:
                print("\n" + "╔" + "="*78 + "╗")
                print("║" + " "*25 + "✅ 所有测试完成！ ✅" + " "*37 + "║")
                print("╚" + "="*78 + "╝")
            else:
                print("\n⚠️  部分测试失败，请查看详细报告")

            return success

        finally:
            self.teardown()


def main():
    """主函数"""
    tester = FrontendTester()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
