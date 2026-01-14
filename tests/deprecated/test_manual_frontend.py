#!/usr/bin/env python3
"""
手动前端测试 - 检查JavaScript错误和控制台日志
"""

import sys
import asyncio
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def main():
    print("\n" + "=" * 70)
    print("🔍 手动前端测试 - 检查JavaScript执行情况")
    print("=" * 70 + "\n")

    async with async_playwright() as p:
        # 启动浏览器（非无头模式以便观察）
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        # 收集控制台消息
        console_messages = []
        page.on('console', lambda msg: console_messages.append({
            'type': msg.type,
            'text': msg.text
        }))

        # 收集JavaScript错误
        js_errors = []
        page.on('pageerror', lambda error: js_errors.append(str(error)))

        try:
            print("📋 正在访问页面...")
            await page.goto('http://localhost:5001', wait_until='networkidle')

            print("\n⏳ 等待5秒，观察页面变化...")
            await asyncio.sleep(5)

            # 检查国家选择框
            print("\n📋 检查国家选择框...")
            country_select = page.locator('#country')
            await country_select.wait_for(state='visible', timeout=5000)

            # 获取所有选项
            options = await country_select.locator('option').all()
            print(f"  选项数量: {len(options)}")

            for i, option in enumerate(options[:5]):  # 只显示前5个
                text = await option.text_content()
                value = await option.get_attribute('value')
                print(f"  选项{i+1}: value='{value}', text='{text}'")

            if len(options) > 5:
                print(f"  ... 还有 {len(options) - 5} 个选项")

            # 截图
            screenshot_path = project_root / "test_screenshots_v2" / "manual_test.png"
            screenshot_path.parent.mkdir(exist_ok=True)
            await page.screenshot(path=str(screenshot_path))
            print(f"\n📸 截图已保存: {screenshot_path}")

            # 打印控制台消息
            print("\n📋 浏览器控制台消息:")
            print("-" * 70)
            if console_messages:
                for msg in console_messages[-20:]:  # 只显示最后20条
                    icon = {
                        'error': '❌',
                        'warning': '⚠️ ',
                        'info': 'ℹ️ ',
                        'log': '📝'
                    }.get(msg['type'], '•')
                    print(f"  {icon} {msg['type']}: {msg['text'][:100]}")
            else:
                print("  (无控制台消息)")

            # 打印JavaScript错误
            if js_errors:
                print("\n❌ JavaScript错误:")
                print("-" * 70)
                for error in js_errors:
                    print(f"  {error}")
            else:
                print("\n✅ 无JavaScript错误")

            # 检查是否加载成功
            print("\n📋 诊断结果:")
            print("-" * 70)
            if len(options) > 1:
                print(f"  ✅ 国家列表加载成功！共有 {len(options)} 个选项")
            elif options and await options[0].text_content() == '加载中...':
                print(f"  ❌ 国家列表未加载 - 仍显示'加载中...'")
                print(f"  💡 可能原因: JavaScript未执行或API调用失败")
            elif options and '加载失败' in await options[0].text_content():
                print(f"  ❌ 国家列表加载失败")
                error_text = await options[0].text_content()
                print(f"  💡 错误信息: {error_text}")
            else:
                print(f"  ⚠️  未知状态")

            # 检查API响应
            print("\n📋 测试API直接调用:")
            print("-" * 70)
            try:
                response = await page.request.get('http://localhost:5001/api/countries')
                status = response.status
                data = await response.json()
                print(f"  ✅ API响应状态: {status}")
                print(f"  ✅ 返回国家数量: {len(data.get('countries', []))}")
            except Exception as e:
                print(f"  ❌ API调用失败: {e}")

            print("\n" + "=" * 70)
            print("测试完成！浏览器将在10秒后关闭...")
            print("=" * 70)

            # 保持浏览器打开10秒以便观察
            await asyncio.sleep(10)

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
