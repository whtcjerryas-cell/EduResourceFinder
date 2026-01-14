#!/usr/bin/env python3
"""
前端自动化测试 - 像人一样操作系统
测试所有按钮、链接、表单和交互功能
"""

import sys
import asyncio
import time
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright, Page


class FrontendAutomationTester:
    """
    前端自动化测试器
    模拟真实用户操作，测试所有交互功能
    """

    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.results = []
        self.screenshots_dir = project_root / "test_screenshots"
        self.screenshots_dir.mkdir(exist_ok=True)
        print(f"✅ 前端自动化测试器初始化完成")
        print(f"📸 截图保存目录: {self.screenshots_dir}")

    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 70)
        print("🚀 开始前端自动化测试")
        print("=" * 70 + "\n")

        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = await context.new_page()

            try:
                # 测试1: 加载主页
                await self.test_load_homepage(page)

                # 测试2: 测试国家选择
                await self.test_country_selection(page)

                # 测试3: 测试年级选择
                await self.test_grade_selection(page)

                # 测试4: 测试学科选择
                await self.test_subject_selection(page)

                # 测试5: 测试搜索按钮
                await self.test_search_button(page)

                # 测试6: 测试历史记录按钮
                await self.test_history_button(page)

                # 测试7: 测试Debug日志按钮
                await self.test_debug_logs_button(page)

                # 测试8: 测试添加国家按钮
                await self.test_add_country_button(page)

                # 测试9: 测试知识点概览按钮
                await self.test_knowledge_points_button(page)

                # 测试10: 测试刷新配置按钮
                await self.test_refresh_config_button(page)

                # 测试11: 测试搜索结果卡片
                await self.test_search_results_card(page)

                # 测试12: 测试结果项交互
                await self.test_result_item_interaction(page)

                # 生成测试报告
                self.generate_report()

            finally:
                await browser.close()

    async def test_load_homepage(self, page: Page):
        """测试1: 加载主页"""
        print("\n📋 测试1: 加载主页")
        print("-" * 70)

        try:
            start_time = time.time()
            await page.goto(self.base_url, wait_until='networkidle')
            load_time = time.time() - start_time

            # 检查页面标题
            title = await page.title()
            print(f"  ✅ 页面标题: {title}")

            # 检查页面是否可见
            await page.screenshot(path=str(self.screenshots_dir / "01_homepage.png"))
            print(f"  ✅ 页面加载时间: {load_time:.2f}s")

            # 检查关键元素
            header = await page.query_selector('.header')
            if header:
                print(f"  ✅ 页面头部可见")

            self.record_result("加载主页", True, f"加载时间: {load_time:.2f}s")

        except Exception as e:
            print(f"  ❌ 失败: {str(e)}")
            self.record_result("加载主页", False, str(e))

    async def test_country_selection(self, page: Page):
        """测试2: 国家选择"""
        print("\n📋 测试2: 国家选择下拉框")
        print("-" * 70)

        try:
            # 找到国家选择器
            country_select = page.locator('#country')
            await country_select.wait_for(state='visible', timeout=5000)
            print(f"  ✅ 国家选择器可见")

            # 截图
            await page.screenshot(path=str(self.screenshots_dir / "02_country_select.png"))

            # 点击选择器
            await country_select.click()
            await asyncio.sleep(0.5)

            # 检查选项
            options = await country_select.locator('option').all()
            print(f"  ✅ 国家选项数量: {len(options)}")

            # 选择第一个国家
            await country_select.select_option(index=0)
            selected_value = await country_select.input_value()
            print(f"  ✅ 已选择: {selected_value}")

            self.record_result("国家选择", True, f"{len(options)}个选项")

        except Exception as e:
            print(f"  ❌ 失败: {str(e)}")
            self.record_result("国家选择", False, str(e))

    async def test_grade_selection(self, page: Page):
        """测试3: 年级选择"""
        print("\n📋 测试3: 年级选择下拉框")
        print("-" * 70)

        try:
            grade_select = page.locator('#grade')
            await grade_select.wait_for(state='visible', timeout=5000)
            print(f"  ✅ 年级选择器可见")

            # 选择印尼后应该有印尼的年级
            await grade_select.click()
            await asyncio.sleep(0.5)

            options = await grade_select.locator('option').all()
            print(f"  ✅ 年级选项数量: {len(options)}")

            # 选择第一个年级
            await grade_select.select_option(index=1)
            selected = await grade_select.input_value()
            print(f"  ✅ 已选择: {selected}")

            await page.screenshot(path=str(self.screenshots_dir / "03_grade_select.png"))
            self.record_result("年级选择", True, f"{len(options)}个选项")

        except Exception as e:
            print(f"  ❌ 失败: {str(e)}")
            self.record_result("年级选择", False, str(e))

    async def test_subject_selection(self, page: Page):
        """测试4: 学科选择"""
        print("\n📋 测试4: 学科选择下拉框")
        print("-" * 70)

        try:
            subject_select = page.locator('#subject')
            await subject_select.wait_for(state='visible', timeout=5000)
            print(f"  ✅ 学科选择器可见")

            await subject_select.click()
            await asyncio.sleep(0.5)

            options = await subject_select.locator('option').all()
            print(f"  ✅ 学科选项数量: {len(options)}")

            # 选择数学
            await subject_select.select_option('Matematika')
            selected = await subject_select.input_value()
            print(f"  ✅ 已选择: {selected}")

            await page.screenshot(path=str(self.screenshots_dir / "04_subject_select.png"))
            self.record_result("学科选择", True, f"{len(options)}个选项")

        except Exception as e:
            print(f"  ❌ 失败: {str(e)}")
            self.record_result("学科选择", False, str(e))

    async def test_search_button(self, page: Page):
        """测试5: 搜索按钮"""
        print("\n📋 测试5: 搜索按钮")
        print("-" * 70)

        try:
            # 确保已选择搜索条件
            await page.select_option('#country', 'Indonesia')
            await page.select_option('#grade', 'Kelas 10')
            await page.select_option('#subject', 'Matematika')

            # 找到搜索按钮
            search_button = page.locator('button:has-text("开始搜索")')
            await search_button.wait_for(state='visible', timeout=5000)
            print(f"  ✅ 搜索按钮可见")

            await page.screenshot(path=str(self.screenshots_dir / "05_before_search.png"))

            # 点击搜索按钮
            print(f"  🔘 点击搜索按钮...")
            start_time = time.time()
            await search_button.click()

            # 等待搜索完成
            await page.wait_for_selector('.results-card', state='visible', timeout=60000)
            search_time = time.time() - start_time

            print(f"  ✅ 搜索完成，耗时: {search_time:.2f}s")

            await page.screenshot(path=str(self.screenshots_dir / "06_after_search.png"))
            self.record_result("搜索按钮", True, f"搜索时间: {search_time:.2f}s")

        except Exception as e:
            print(f"  ❌ 失败: {str(e)}")
            await page.screenshot(path=str(self.screenshots_dir / "05_search_failed.png"))
            self.record_result("搜索按钮", False, str(e))

    async def test_search_results_card(self, page: Page):
        """测试11: 搜索结果卡片"""
        print("\n📋 测试6: 搜索结果卡片")
        print("-" * 70)

        try:
            # 等待结果卡片出现
            results_card = page.locator('.results-card')
            await results_card.wait_for(state='visible', timeout=10000)
            print(f"  ✅ 结果卡片可见")

            # 检查结果数量
            result_items = page.locator('.result-item')
            count = await result_items.count()
            print(f"  ✅ 结果数量: {count}")

            # 检查结果卡片标题
            card_title = await results_card.locator('h2').text_content()
            print(f"  ✅ 卡片标题: {card_title.strip()}")

            await page.screenshot(path=str(self.screenshots_dir / "07_results_card.png"))
            self.record_result("搜索结果卡片", True, f"{count}个结果")

        except Exception as e:
            print(f"  ❌ 失败: {str(e)}")
            self.record_result("搜索结果卡片", False, str(e))

    async def test_result_item_interaction(self, page: Page):
        """测试12: 结果项交互"""
        print("\n📋 测试7: 结果项交互")
        print("-" * 70)

        try:
            # 找到第一个结果项
            first_result = page.locator('.result-item').first
            await first_result.wait_for(state='visible', timeout=5000)
            print(f"  ✅ 第一个结果项可见")

            # 检查选择框
            checkbox = first_result.locator('input[type="checkbox"]')
            if await checkbox.count() > 0:
                await checkbox.check()
                print(f"  ✅ 选择框已勾选")

            # 检查URL链接
            url_link = first_result.locator('a[href*="http"]')
            if await url_link.count() > 0:
                url = await url_link.get_attribute('href')
                print(f"  ✅ URL链接: {url[:60]}...")

            # 检查查看视频按钮
            view_button = first_result.locator('button:has-text("查看")')
            if await view_button.count() > 0:
                print(f"  ✅ 查看按钮可见")

            await page.screenshot(path=str(self.screenshots_dir / "08_result_interaction.png"))
            self.record_result("结果项交互", True, "所有交互元素正常")

        except Exception as e:
            print(f"  ❌ 失败: {str(e)}")
            self.record_result("结果项交互", False, str(e))

    async def test_history_button(self, page: Page):
        """测试6: 历史记录按钮"""
        print("\n📋 测试8: 历史记录按钮")
        print("-" * 70)

        try:
            history_button = page.locator('button:has-text("📜 历史记录")')
            await history_button.wait_for(state='visible', timeout=5000)
            print(f"  ✅ 历史记录按钮可见")

            # 点击按钮
            await history_button.click()
            await asyncio.sleep(1)

            # 检查是否有响应（可能是弹窗或跳转）
            await page.screenshot(path=str(self.screenshots_dir / "09_history_button.png"))
            print(f"  ✅ 历史记录按钮已点击")

            self.record_result("历史记录按钮", True, "按钮可点击")

        except Exception as e:
            print(f"  ❌ 失败: {str(e)}")
            self.record_result("历史记录按钮", False, str(e))

    async def test_debug_logs_button(self, page: Page):
        """测试7: Debug日志按钮"""
        print("\n📋 测试9: Debug日志按钮")
        print("-" * 70)

        try:
            debug_button = page.locator('button:has-text("🐛 Debug日志")')
            await debug_button.wait_for(state='visible', timeout=5000)
            print(f"  ✅ Debug日志按钮可见")

            # 点击按钮
            await debug_button.click()
            await asyncio.sleep(1)

            await page.screenshot(path=str(self.screenshots_dir / "10_debug_button.png"))
            print(f"  ✅ Debug日志按钮已点击")

            self.record_result("Debug日志按钮", True, "按钮可点击")

        except Exception as e:
            print(f"  ❌ 失败: {str(e)}")
            self.record_result("Debug日志按钮", False, str(e))

    async def test_add_country_button(self, page: Page):
        """测试8: 添加国家按钮"""
        print("\n📋 测试10: 添加国家按钮")
        print("-" * 70)

        try:
            add_country_button = page.locator('button:has-text("🌍 添加国家")')
            await add_country_button.wait_for(state='visible', timeout=5000)
            print(f"  ✅ 添加国家按钮可见")

            # 点击按钮
            await add_country_button.click()
            await asyncio.sleep(1)

            await page.screenshot(path=str(self.screenshots_dir / "11_add_country.png"))
            print(f"  ✅ 添加国家按钮已点击")

            self.record_result("添加国家按钮", True, "按钮可点击")

        except Exception as e:
            print(f"  ❌ 失败: {str(e)}")
            self.record_result("添加国家按钮", False, str(e))

    async def test_knowledge_points_button(self, page: Page):
        """测试9: 知识点概览按钮"""
        print("\n📋 测试11: 知识点概览按钮")
        print("-" * 70)

        try:
            kp_button = page.locator('a:has-text("📚 知识点概览")')
            await kp_button.wait_for(state='visible', timeout=5000)
            print(f"  ✅ 知识点概览按钮可见")

            # 点击按钮
            async with page.expect_navigation():
                await kp_button.click()

            # 等待新页面加载
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(1)

            current_url = page.url
            print(f"  ✅ 已跳转到: {current_url}")

            await page.screenshot(path=str(self.screenshots_dir / "12_knowledge_points.png"))

            # 返回主页
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle')

            self.record_result("知识点概览按钮", True, "页面跳转成功")

        except Exception as e:
            print(f"  ❌ 失败: {str(e)}")
            self.record_result("知识点概览按钮", False, str(e))

    async def test_refresh_config_button(self, page: Page):
        """测试10: 刷新配置按钮"""
        print("\n📋 测试12: 刷新配置按钮")
        print("-" * 70)

        try:
            refresh_button = page.locator('button:has-text("🔄 刷新配置")')
            await refresh_button.wait_for(state='visible', timeout=5000)
            print(f"  ✅ 刷新配置按钮可见")

            # 点击按钮
            await refresh_button.click()
            await asyncio.sleep(1)

            await page.screenshot(path=str(self.screenshots_dir / "13_refresh_config.png"))
            print(f"  ✅ 刷新配置按钮已点击")

            self.record_result("刷新配置按钮", True, "按钮可点击")

        except Exception as e:
            print(f"  ❌ 失败: {str(e)}")
            self.record_result("刷新配置按钮", False, str(e))

    def record_result(self, test_name: str, success: bool, message: str):
        """记录测试结果"""
        self.results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 70)
        print("📊 测试报告")
        print("=" * 70)

        total = len(self.results)
        passed = sum(1 for r in self.results if r['success'])
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"\n总测试数: {total}")
        print(f"通过: {passed} ✅")
        print(f"失败: {failed} ❌")
        print(f"通过率: {pass_rate:.1f}%")

        print(f"\n详细结果:")
        print("-" * 70)
        for result in self.results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} | {result['test']:<30} | {result['message']}")

        print("\n" + "=" * 70)

        # 保存JSON报告
        report_file = project_root / "test_results" / f"frontend_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": pass_rate,
                "results": self.results
            }, f, ensure_ascii=False, indent=2)

        print(f"📄 详细报告已保存: {report_file}")
        print(f"📸 截图已保存: {self.screenshots_dir}")
        print("=" * 70 + "\n")


async def main():
    """主函数"""
    tester = FrontendAutomationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
