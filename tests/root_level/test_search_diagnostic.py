#!/usr/bin/env python3
"""
搜索诊断测试 - 查看为什么搜索无法工作
"""

import sys
import asyncio
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def main():
    print("\n" + "=" * 70)
    print("🔍 搜索功能诊断测试")
    print("=" * 70 + "\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        # 收集所有控制台消息
        console_messages = []
        def handle_console(msg):
            text = msg.text
            console_messages.append({
                'type': msg.type,
                'text': text
            })
            print(f"  [{msg.type.upper()}] {text[:200]}")

        page.on('console', handle_console)

        # 收集JavaScript错误
        js_errors = []
        page.on('pageerror', lambda error: js_errors.append(str(error)))

        # 收集网络请求
        network_requests = []
        def handle_request(request):
            if '/api/' in request.url:
                print(f"  [REQUEST] {request.method} {request.url}")
                network_requests.append({
                    'method': request.method,
                    'url': request.url,
                    'timestamp': asyncio.get_event_loop().time()
                })

        page.on('request', handle_request)

        try:
            print("📋 加载页面...")
            await page.goto('http://localhost:5001', wait_until='networkidle')

            print("\n⏳ 等待页面初始化完成...")
            await asyncio.sleep(3)

            print("\n📋 选择搜索条件...")
            # 选择国家
            await page.evaluate('''() => {
                document.getElementById('country').value = 'ID';
                document.getElementById('country').dispatchEvent(new Event('change', { bubbles: true }));
            }''')
            print("  ✅ 已选国家: Indonesia")

            await asyncio.sleep(1)

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

            await asyncio.sleep(0.5)

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

            await asyncio.sleep(0.5)

            # 检查搜索按钮状态
            search_btn = page.locator('#searchBtn')
            is_enabled = await search_btn.is_enabled()
            is_visible = await search_btn.is_visible()
            print(f"\n📋 搜索按钮状态:")
            print(f"  可见: {is_visible}")
            print(f"  可用: {is_enabled}")

            # 截图 - 点击前
            await page.screenshot(path=str(project_root / "test_screenshots_fixed" / "diagnostic_before_search.png"))

            print(f"\n📋 准备点击搜索按钮...")
            print(f"  将在 2 秒后执行...")
            await asyncio.sleep(2)

            print(f"\n📋 点击搜索按钮...")
            await search_btn.click()
            print(f"  ✅ 按钮已点击")

            # 等待并观察
            print(f"\n⏳ 等待 10 秒观察反应...")
            for i in range(10):
                await asyncio.sleep(1)
                print(f"  等待中... {i+1}/10秒")

                # 检查是否有结果卡片出现
                results_card = page.locator('.results-card')
                if await results_card.count() > 0:
                    is_visible = await results_card.is_visible()
                    if is_visible:
                        print(f"  ✅ 搜索结果已出现！")
                        break

            # 最终截图
            await page.screenshot(path=str(project_root / "test_screenshots_fixed" / "diagnostic_after_search.png"))

            print(f"\n📋 诊断结果:")
            print(f"  控制台消息数: {len(console_messages)}")
            print(f"  JavaScript错误数: {len(js_errors)}")
            print(f"  API请求数: {len(network_requests)}")

            if js_errors:
                print(f"\n❌ JavaScript错误:")
                for error in js_errors:
                    print(f"  - {error[:200]}")

            if network_requests:
                print(f"\n📋 API请求列表:")
                for req in network_requests:
                    print(f"  - {req['method']} {req['url']}")

            # 检查页面状态
            results_card = page.locator('.results-card')
            if await results_card.count() > 0 and await results_card.is_visible():
                print(f"\n✅ 搜索结果显示成功")
            else:
                print(f"\n❌ 搜索结果未显示")

                # 检查是否有错误消息
                error_div = page.locator('.error')
                if await error_div.count() > 0:
                    error_text = await error_div.first.text_content()
                    print(f"  错误消息: {error_text}")

            print(f"\n📸 截图已保存")
            print(f"  浏览器将在 5 秒后关闭...")
            await asyncio.sleep(5)

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
