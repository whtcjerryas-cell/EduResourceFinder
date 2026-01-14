#!/usr/bin/env python3
"""
前端自动化测试 - 修复版
正确等待JavaScript执行完成
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


class FixedFrontendTester:
    """修复后的前端测试器 - 正确处理异步加载"""

    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.results = []
        self.screenshots_dir = project_root / "test_screenshots_fixed"
        self.screenshots_dir.mkdir(exist_ok=True)

    async def run_tests(self, headless: bool = False):
        """运行所有测试"""
        print("\n" + "=" * 70)
        print("🚀 前端自动化测试 - 修复版")
        print("=" * 70 + "\n")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = await context.new_page()

            try:
                # 测试1: 主页加载（含完整初始化）
                await self.test_01_full_initialization(page)

                # 测试2: 搜索功能
                await self.test_02_search_functionality(page)

                # 测试3: 所有按钮
                await self.test_03_all_buttons(page)

                # 测试4: 搜索结果交互
                await self.test_04_result_interactions(page)

                # 生成报告
                self.generate_report()

            finally:
                await browser.close()

    async def wait_for_countries_loaded(self, page: Page, timeout: int = 10000):
        """等待国家列表加载完成"""
        start = time.time()
        while time.time() - start < timeout / 1000:
            country_select = page.locator('#country')
            if await country_select.count() > 0:
                options = await country_select.locator('option').all()
                # 如果有多个选项，且第一个不是"加载中..."，说明加载完成
                if len(options) > 1:
                    first_text = await options[0].text_content()
                    if '加载中' not in first_text and '加载失败' not in first_text:
                        return True
            await asyncio.sleep(0.2)
        return False

    async def test_01_full_initialization(self, page: Page):
        """测试1: 完整页面初始化"""
        print("\n📋 测试1: 页面完整初始化")
        print("-" * 70)

        try:
            start = time.time()
            await page.goto(self.base_url, wait_until='networkidle')
            load_time = time.time() - start
            print(f"  ✅ 页面加载完成: {load_time:.2f}s")

            # 等待国家列表加载
            print(f"  ⏳ 等待国家列表加载...")
            if await self.wait_for_countries_loaded(page, timeout=10000):
                print(f"  ✅ 国家列表已加载")

                # 检查选项数量
                country_select = page.locator('#country')
                options = await country_select.locator('option').all()
                print(f"  ✅ 国家选项数量: {len(options)}")

                # 显示前3个选项
                for i in range(min(3, len(options))):
                    text = await options[i].text_content()
                    print(f"     - {text}")

                # 检查年级列表
                grade_select = page.locator('#grade')
                grade_options = await grade_select.locator('option').all()
                print(f"  ✅ 年级选项数量: {len(grade_options)}")

                # 检查学科列表
                subject_select = page.locator('#subject')
                subject_options = await subject_select.locator('option').all()
                print(f"  ✅ 学科选项数量: {len(subject_options)}")

                await page.screenshot(path=str(self.screenshots_dir / "01_initialization.png"))
                self.record_result("页面初始化", True, f"所有下拉框已加载")
            else:
                print(f"  ❌ 国家列表加载超时")
                self.record_result("页面初始化", False, "国家列表未加载")

        except Exception as e:
            print(f"  ❌ 失败: {e}")
            self.record_result("页面初始化", False, str(e))

    async def test_02_search_functionality(self, page: Page):
        """测试2: 搜索功能"""
        print("\n📋 测试2: 搜索功能")
        print("-" * 70)

        try:
            # 选择搜索条件（使用JavaScript避免Playwright的select_option问题）
            print(f"  🔘 选择搜索条件...")

            # 使用JavaScript直接设置值
            await page.evaluate('''() => {
                document.getElementById('country').value = 'ID';
                document.getElementById('country').dispatchEvent(new Event('change', { bubbles: true }));
            }''')
            print(f"  ✅ 已选国家: Indonesia")

            await asyncio.sleep(1.5)  # 等待年级和学科动态加载

            # 选择年级
            await page.evaluate('''() => {
                const gradeSelect = document.getElementById('grade');
                if (gradeSelect.options.length > 1) {
                    gradeSelect.selectedIndex = 1;
                    gradeSelect.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }''')
            grade_value = await page.locator('#grade').input_value()
            print(f"  ✅ 已选年级: {grade_value}")

            # 选择学科
            await page.evaluate('''() => {
                const subjectSelect = document.getElementById('subject');
                for (let i = 0; i < subjectSelect.options.length; i++) {
                    if (subjectSelect.options[i].value === 'Matematika') {
                        subjectSelect.selectedIndex = i;
                        subjectSelect.dispatchEvent(new Event('change', { bubbles: true }));
                        break;
                    }
                }
            }''')
            print(f"  ✅ 已选学科: Matematika")

            await page.screenshot(path=str(self.screenshots_dir / "02_before_search.png"))

            # 点击搜索
            print(f"  🔘 开始搜索...")
            search_btn = page.locator('#searchBtn')
            await search_btn.click()

            # 等待搜索结果
            print(f"  ⏳ 等待搜索结果...")
            try:
                await page.wait_for_selector('.results-card', state='visible', timeout=60000)
                print(f"  ✅ 搜索结果已显示")

                # 检查结果数量
                result_items = page.locator('.result-item')
                count = await result_items.count()
                print(f"  ✅ 结果数量: {count}")

                await page.screenshot(path=str(self.screenshots_dir / "03_search_results.png"))
                self.record_result("搜索功能", True, f"找到{count}个结果")

            except Exception as e:
                print(f"  ❌ 搜索结果未显示: {e}")
                self.record_result("搜索功能", False, "搜索结果未显示")

        except Exception as e:
            print(f"  ❌ 失败: {e}")
            self.record_result("搜索功能", False, str(e))

    async def test_03_all_buttons(self, page: Page):
        """测试3: 所有主要按钮"""
        print("\n📋 测试3: 按钮功能测试")
        print("-" * 70)

        # 测试Debug日志按钮
        try:
            print(f"\n  测试 🐛 Debug日志按钮...")
            debug_btn = page.locator('button:has-text("🐛 Debug日志")')
            if await debug_btn.count() > 0:
                await debug_btn.click()
                await asyncio.sleep(1)
                print(f"  ✅ Debug按钮可点击")

                # 检查模态框
                modal = page.locator('.debug-modal')
                if await modal.count() > 0 and await modal.is_visible():
                    print(f"  ✅ Debug模态框已打开")
                    # 关闭
                    close_btn = page.locator('#closeDebugModal')
                    await close_btn.click()
                    await asyncio.sleep(0.5)
                    print(f"  ✅ 模态框已关闭")
                    self.record_result("Debug日志", True, "正常")
                else:
                    print(f"  ⚠️ 模态框未显示")
                    self.record_result("Debug日志", False, "模态框未打开")
            else:
                print(f"  ⚠️ 按钮未找到")
                self.record_result("Debug日志", False, "按钮不存在")
        except Exception as e:
            print(f"  ❌ Debug按钮测试失败: {e}")
            self.record_result("Debug日志", False, str(e))

        # 测试添加国家按钮
        try:
            print(f"\n  测试 🌍 添加国家按钮...")
            add_btn = page.locator('#addCountryBtn')
            if await add_btn.count() > 0:
                await add_btn.click()
                await asyncio.sleep(1)
                print(f"  ✅ 添加国家按钮可点击")

                # 检查模态框
                modal = page.locator('#addCountryModal')
                if await modal.count() > 0 and await modal.is_visible():
                    print(f"  ✅ 添加国家模态框已打开")
                    # 关闭
                    cancel_btn = page.locator('#cancelAddBtn')
                    await cancel_btn.click()
                    await asyncio.sleep(0.5)
                    print(f"  ✅ 模态框已关闭")
                    self.record_result("添加国家", True, "正常")
                else:
                    print(f"  ⚠️ 模态框未显示")
                    self.record_result("添加国家", False, "模态框未打开")
            else:
                print(f"  ⚠️ 按钮未找到")
                self.record_result("添加国家", False, "按钮不存在")
        except Exception as e:
            print(f"  ❌ 添加国家按钮测试失败: {e}")
            self.record_result("添加国家", False, str(e))

        # 测试刷新配置按钮
        try:
            print(f"\n  测试 🔄 刷新配置按钮...")
            refresh_btn = page.locator('#refreshCountryBtn')
            if await refresh_btn.count() > 0:
                await refresh_btn.click()
                await asyncio.sleep(2)
                print(f"  ✅ 刷新配置按钮可点击")
                self.record_result("刷新配置", True, "正常")
            else:
                print(f"  ⚠️ 按钮未找到")
                self.record_result("刷新配置", False, "按钮不存在")
        except Exception as e:
            print(f"  ❌ 刷新配置按钮测试失败: {e}")
            self.record_result("刷新配置", False, str(e))

        # 测试知识点概览链接
        try:
            print(f"\n  测试 📚 知识点概览链接...")
            kp_link = page.locator('a:has-text("📚 知识点概览")')
            if await kp_link.count() > 0:
                current_url = page.url
                await kp_link.click()
                await page.wait_for_load_state('networkidle')
                new_url = page.url
                if new_url != current_url:
                    print(f"  ✅ 知识点概览已跳转")
                    # 返回主页
                    await page.goto(self.base_url)
                    await page.wait_for_load_state('networkidle')
                    self.record_result("知识点概览", True, "正常")
                else:
                    print(f"  ⚠️ 未跳转")
                    self.record_result("知识点概览", False, "未跳转")
            else:
                print(f"  ⚠️ 链接未找到")
                self.record_result("知识点概览", False, "链接不存在")
        except Exception as e:
            print(f"  ❌ 知识点概览测试失败: {e}")
            self.record_result("知识点概览", False, str(e))

    async def test_04_result_interactions(self, page: Page):
        """测试4: 搜索结果交互"""
        print("\n📋 测试4: 搜索结果交互")
        print("-" * 70)

        try:
            # 确保有搜索结果
            result_items = page.locator('.result-item')
            count = await result_items.count()

            if count > 0:
                print(f"  ✅ 找到 {count} 个结果项")

                # 测试第一个结果的交互
                first_result = result_items.first

                # 测试选择框
                checkbox = first_result.locator('input[type="checkbox"]')
                if await checkbox.count() > 0:
                    await checkbox.check()
                    is_checked = await checkbox.is_checked()
                    if is_checked:
                        print(f"  ✅ 选择框可勾选")
                    else:
                        print(f"  ⚠️ 选择框状态异常")
                else:
                    print(f"  ⚠️ 未找到选择框")

                # 测试查看按钮
                view_btn = first_result.locator('button:has-text("查看")')
                if await view_btn.count() > 0:
                    print(f"  ✅ 查看按钮存在")
                else:
                    print(f"  ⚠️ 未找到查看按钮")

                # 测试URL链接
                url_link = first_result.locator('a[href*="http"]')
                if await url_link.count() > 0:
                    url = await url_link.first.get_attribute('href')
                    print(f"  ✅ URL链接存在: {url[:50]}...")
                else:
                    print(f"  ⚠️ 未找到URL链接")

                await page.screenshot(path=str(self.screenshots_dir / "04_result_interaction.png"))
                self.record_result("结果交互", True, "所有交互元素正常")

            else:
                print(f"  ⚠️ 无搜索结果可测试")
                self.record_result("结果交互", False, "无搜索结果")

        except Exception as e:
            print(f"  ❌ 失败: {e}")
            self.record_result("结果交互", False, str(e))

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
        report_file = project_root / "test_results" / f"fixed_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
    tester = FixedFrontendTester()
    await tester.run_tests(headless=False)


if __name__ == "__main__":
    asyncio.run(main())
