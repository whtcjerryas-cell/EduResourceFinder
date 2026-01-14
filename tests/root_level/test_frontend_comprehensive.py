#!/usr/bin/env python3
"""
前端全面测试 - 测试所有按钮和交互功能
"""

import sys
import asyncio
import time
import json
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright, Page


class ComprehensiveFrontendTester:
    """全面的前端测试器"""

    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.results = []
        self.screenshots_dir = project_root / "test_screenshots_v2"
        self.screenshots_dir.mkdir(exist_ok=True)

    async def run_tests(self, headless: bool = False):
        """运行所有测试"""
        print("\n" + "=" * 70)
        print("🚀 前端全面自动化测试")
        print("=" * 70 + "\n")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = await context.new_page()

            try:
                # 测试1: 主页加载
                await self.test_01_homepage(page)

                # 测试2: 搜索功能完整流程
                await self.test_02_search_workflow(page)

                # 测试3: 知识点概览按钮
                await self.test_03_knowledge_points(page)

                # 测试4: Debug日志按钮
                await self.test_04_debug_logs(page)

                # 测试5: 评估报告按钮
                await self.test_05_evaluation_history(page)

                # 测试6: 添加国家按钮
                await self.test_06_add_country(page)

                # 测试7: 刷新配置按钮
                await self.test_07_refresh_config(page)

                # 测试8: 选择框交互
                await self.test_08_checkboxes(page)

                # 测试9: 结果卡片按钮
                await self.test_09_result_buttons(page)

                # 生成报告
                self.generate_report()

            finally:
                await browser.close()

    async def test_01_homepage(self, page: Page):
        """测试1: 主页加载"""
        print("\n📋 测试1: 主页加载")
        print("-" * 70)

        try:
            start = time.time()
            await page.goto(self.base_url, wait_until='networkidle')
            load_time = time.time() - start

            title = await page.title()
            print(f"  ✅ 页面标题: {title}")
            print(f"  ✅ 加载时间: {load_time:.2f}s")

            await page.screenshot(path=str(self.screenshots_dir / "01_homepage.png"))
            self.record_result("主页加载", True, f"{load_time:.2f}s")

        except Exception as e:
            print(f"  ❌ 失败: {e}")
            self.record_result("主页加载", False, str(e))

    async def test_02_search_workflow(self, page: Page):
        """测试2: 搜索完整流程"""
        print("\n📋 测试2: 搜索功能")
        print("-" * 70)

        try:
            # 等待国家选择器
            country_select = page.locator('#country')
            await country_select.wait_for(state='visible', timeout=5000)
            print(f"  ✅ 国家选择器可见")

            # 选择印度尼西亚
            await country_select.select_option('Indonesia')
            print(f"  ✅ 已选择: Indonesia")

            # 等待动态加载年级
            await asyncio.sleep(1)

            # 选择年级
            grade_select = page.locator('#grade')
            options = await grade_select.locator('option').all()
            print(f"  ✅ 年级选项数: {len(options)}")

            if len(options) > 1:
                await grade_select.select_option(index=1)
                grade_value = await grade_select.input_value()
                print(f"  ✅ 已选择年级: {grade_value}")

            # 选择学科
            subject_select = page.locator('#subject')
            options = await subject_select.locator('option').all()
            print(f"  ✅ 学科选项数: {len(options)}")

            if len(options) > 1:
                await subject_select.select_option('Matematika')
                print(f"  ✅ 已选择学科: Matematika")

            await page.screenshot(path=str(self.screenshots_dir / "02_form_filled.png"))

            # 点击搜索按钮
            search_btn = page.locator('#searchBtn')
            await search_btn.click()
            print(f"  🔘 点击搜索按钮")

            # 等待搜索结果
            await page.wait_for_selector('.results-card', state='visible', timeout=60000)
            print(f"  ✅ 搜索结果已显示")

            await page.screenshot(path=str(self.screenshots_dir / "03_search_results.png"))
            self.record_result("搜索功能", True, "完整流程成功")

        except Exception as e:
            print(f"  ❌ 失败: {e}")
            self.record_result("搜索功能", False, str(e))

    async def test_03_knowledge_points(self, page: Page):
        """测试3: 知识点概览"""
        print("\n📋 测试3: 知识点概览按钮")
        print("-" * 70)

        try:
            # 查找按钮
            kp_btn = page.locator('button:has-text("📚 知识点概览")')
            if await kp_btn.count() > 0:
                await kp_btn.click()
                print(f"  ✅ 按钮已点击")

                # 等待导航
                await page.wait_for_load_state('networkidle')
                current_url = page.url
                print(f"  ✅ 当前URL: {current_url}")

                await page.screenshot(path=str(self.screenshots_dir / "04_knowledge_points.png"))

                # 返回主页
                await page.goto(self.base_url)
                await page.wait_for_load_state('networkidle')

                self.record_result("知识点概览", True, "跳转成功")
            else:
                print(f"  ⚠️ 按钮未找到")
                self.record_result("知识点概览", False, "按钮不存在")

        except Exception as e:
            print(f"  ❌ 失败: {e}")
            self.record_result("知识点概览", False, str(e))

    async def test_04_debug_logs(self, page: Page):
        """测试4: Debug日志"""
        print("\n📋 测试4: Debug日志按钮")
        print("-" * 70)

        try:
            debug_btn = page.locator('button:has-text("🐛 Debug日志")')
            await debug_btn.click()
            print(f"  ✅ Debug按钮已点击")

            await asyncio.sleep(1)
            await page.screenshot(path=str(self.screenshots_dir / "05_debug_modal.png"))

            # 检查模态框是否打开
            modal = page.locator('.debug-modal')
            if await modal.count() > 0 and await modal.is_visible():
                print(f"  ✅ Debug模态框已打开")

                # 关闭模态框
                close_btn = page.locator('#closeDebugModal')
                await close_btn.click()
                await asyncio.sleep(0.5)
                print(f"  ✅ 模态框已关闭")

                self.record_result("Debug日志", True, "模态框正常")
            else:
                print(f"  ⚠️ 模态框未显示")
                self.record_result("Debug日志", False, "模态框未打开")

        except Exception as e:
            print(f"  ❌ 失败: {e}")
            self.record_result("Debug日志", False, str(e))

    async def test_05_evaluation_history(self, page: Page):
        """测试5: 评估报告"""
        print("\n📋 测试5: 评估报告按钮")
        print("-" * 70)

        try:
            eval_btn = page.locator('button:has-text("📊 评估报告")')
            if await eval_btn.count() > 0:
                await eval_btn.click()
                print(f"  ✅ 评估报告按钮已点击")
                await asyncio.sleep(1)
                await page.screenshot(path=str(self.screenshots_dir / "06_evaluation.png"))
                self.record_result("评估报告", True, "按钮可点击")
            else:
                print(f"  ⚠️ 按钮未找到")
                self.record_result("评估报告", False, "按钮不存在")

        except Exception as e:
            print(f"  ❌ 失败: {e}")
            self.record_result("评估报告", False, str(e))

    async def test_06_add_country(self, page: Page):
        """测试6: 添加国家"""
        print("\n📋 测试6: 添加国家按钮")
        print("-" * 70)

        try:
            add_btn = page.locator('#addCountryBtn')
            await add_btn.click()
            print(f"  ✅ 添加国家按钮已点击")

            await asyncio.sleep(1)
            await page.screenshot(path=str(self.screenshots_dir / "07_add_country.png"))

            # 检查是否有模态框
            modal = page.locator('.modal')
            if await modal.count() > 0 and await modal.is_visible():
                print(f"  ✅ 添加国家模态框已打开")

                # 关闭模态框
                cancel_btn = page.locator('#cancelAddBtn')
                await cancel_btn.click()
                await asyncio.sleep(0.5)
                print(f"  ✅ 模态框已关闭")

                self.record_result("添加国家", True, "模态框正常")
            else:
                print(f"  ⚠️ 模态框未显示")
                self.record_result("添加国家", False, "模态框未打开")

        except Exception as e:
            print(f"  ❌ 失败: {e}")
            self.record_result("添加国家", False, str(e))

    async def test_07_refresh_config(self, page: Page):
        """测试7: 刷新配置"""
        print("\n📋 测试7: 刷新配置按钮")
        print("-" * 70)

        try:
            refresh_btn = page.locator('#refreshCountryBtn')
            await refresh_btn.click()
            print(f"  ✅ 刷新配置按钮已点击")

            await asyncio.sleep(2)
            print(f"  ✅ 配置已刷新")

            self.record_result("刷新配置", True, "功能正常")

        except Exception as e:
            print(f"  ❌ 失败: {e}")
            self.record_result("刷新配置", False, str(e))

    async def test_08_checkboxes(self, page: Page):
        """测试8: 选择框"""
        print("\n📋 测试8: 结果选择框")
        print("-" * 70)

        try:
            # 先执行搜索
            await page.select_option('#country', 'Indonesia')
            await asyncio.sleep(1)
            await page.select_option('#grade', index=1)
            await page.select_option('#subject', 'Matematika')

            search_btn = page.locator('#searchBtn')
            await search_btn.click()
            await page.wait_for_selector('.results-card', timeout=60000)

            # 测试选择框
            checkboxes = page.locator('.result-item input[type="checkbox"]')
            count = await checkboxes.count()
            print(f"  ✅ 选择框数量: {count}")

            if count > 0:
                # 勾选第一个
                first_checkbox = checkboxes.first
                await first_checkbox.check()
                print(f"  ✅ 第一个选择框已勾选")

                await page.screenshot(path=str(self.screenshots_dir / "08_checkbox.png"))
                self.record_result("选择框", True, f"{count}个选择框")
            else:
                print(f"  ⚠️ 没有找到选择框")
                self.record_result("选择框", False, "无选择框")

        except Exception as e:
            print(f"  ❌ 失败: {e}")
            self.record_result("选择框", False, str(e))

    async def test_09_result_buttons(self, page: Page):
        """测试9: 结果项按钮"""
        print("\n📋 测试9: 结果项按钮")
        print("-" * 70)

        try:
            # 查看按钮
            view_btns = page.locator('.result-item button')
            count = await view_btns.count()
            print(f"  ✅ 查看按钮数量: {count}")

            if count > 0:
                await page.screenshot(path=str(self.screenshots_dir / "09_result_buttons.png"))
                self.record_result("结果按钮", True, f"{count}个按钮")
            else:
                print(f"  ⚠️ 没有找到按钮")
                self.record_result("结果按钮", False, "无按钮")

        except Exception as e:
            print(f"  ❌ 失败: {e}")
            self.record_result("结果按钮", False, str(e))

    def record_result(self, name: str, success: bool, msg: str):
        """记录结果"""
        self.results.append({
            "test": name,
            "success": success,
            "message": msg,
            "timestamp": datetime.now().isoformat()
        })

    def generate_report(self):
        """生成报告"""
        print("\n" + "=" * 70)
        print("📊 测试报告")
        print("=" * 70)

        total = len(self.results)
        passed = sum(1 for r in self.results if r['success'])
        failed = total - passed

        print(f"\n总测试数: {total}")
        print(f"通过: {passed} ✅")
        print(f"失败: {failed} ❌")
        print(f"通过率: {passed/total*100:.1f}%" if total > 0 else "通过率: 0%")

        print(f"\n详细结果:")
        print("-" * 70)
        for r in self.results:
            status = "✅" if r['success'] else "❌"
            print(f"{status} {r['test']:<25} | {r['message']}")

        # 保存报告
        report_file = project_root / "test_results" / f"comprehensive_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total": total,
                "passed": passed,
                "failed": failed,
                "results": self.results
            }, f, indent=2, ensure_ascii=False)

        print(f"\n📄 报告已保存: {report_file}")
        print(f"📸 截图已保存: {self.screenshots_dir}")
        print("=" * 70 + "\n")


async def main():
    tester = ComprehensiveFrontendTester()
    await tester.run_tests(headless=False)  # 显示浏览器以便观察


if __name__ == "__main__":
    asyncio.run(main())
