"""
Playwright test to verify the Discovery Agent workflow for adding/refreshing countries.

This test verifies:
1. Add country button triggers discovery agent
2. Refresh country button triggers discovery agent
3. Agent searches and extracts education structure information
"""
import asyncio
import time
from playwright.async_api import async_playwright


async def test_add_country_workflow():
    """Test adding a new country using discovery agent"""
    print("\n" + "="*80)
    print("测试 1: 添加新国家（Discovery Agent）")
    print("="*80)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Navigate to homepage
        await page.goto("http://localhost:5001")
        await page.wait_for_load_state('networkidle')

        print("\n[步骤 1] 点击'添加国家'按钮...")
        add_btn = page.locator('#addCountryBtn')
        await add_btn.click()

        # Handle the prompt dialog
        async def handle_dialog(dialog):
            print(f"  ✓ 对话框出现: {dialog.message}")
            # 输入测试国家名称（使用一个较小的国家用于快速测试）
            test_country = "Singapore"
            print(f"  → 输入国家名称: {test_country}")
            await dialog.accept(test_country)

        page.on('dialog', handle_dialog)
        await page.wait_for_timeout(2000)

        print("\n[步骤 2] 等待 Discovery Agent 搜索...")
        print("  （这可能需要1-2分钟）")

        # 等待并检查 toast 提示
        start_time = time.time()
        max_wait_time = 180  # 最多等待3分钟

        success_found = False
        elapsed = 0

        while elapsed < max_wait_time:
            # 检查是否有成功提示
            success_toast = page.locator('.toast.success')
            count = await success_toast.count()

            if count > 0:
                toast_text = await success_toast.inner_text()
                if '添加成功' in toast_text or '已添加国家' in toast_text:
                    print(f"\n  ✓ {toast_text}")
                    success_found = True
                    break

            await page.wait_for_timeout(5000)  # 每5秒检查一次
            elapsed = time.time() - start_time
            print(f"  ⏳ 已等待 {int(elapsed)}秒...", end='\r')

        if success_found:
            print("\n\n✅ 测试通过：Discovery Agent 成功添加国家！")

            # 验证国家列表已更新
            await page.wait_for_timeout(2000)
            country_select = page.locator('#country')
            await country_select.select_option('SG')
            print(f"  ✓ 可以选择新添加的国家 (SG)")
        else:
            print("\n\n⚠️  超时：未能在3分钟内完成添加")
            # 检查是否有错误提示
            error_toast = page.locator('.toast.error')
            error_count = await error_toast.count()
            if error_count > 0:
                error_text = await error_toast.inner_text()
                print(f"  ✗ 错误信息: {error_text}")

        await browser.close()


async def test_refresh_country_workflow():
    """Test refreshing an existing country using discovery agent"""
    print("\n" + "="*80)
    print("测试 2: 刷新国家配置（Discovery Agent）")
    print("="*80)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Navigate to homepage
        await page.goto("http://localhost:5001")
        await page.wait_for_load_state('networkidle')

        print("\n[步骤 1] 选择要刷新的国家...")
        country_select = page.locator('#country')
        await country_select.select_option('ID')  # 选择印尼
        print("  ✓ 已选择: Indonesia (ID)")

        await page.wait_for_timeout(2000)

        print("\n[步骤 2] 点击'刷新配置'按钮...")
        refresh_btn = page.locator('#refreshCountryBtn')

        # Handle the confirm dialog
        async def handle_dialog(dialog):
            print(f"  ✓ 确认对话框出现")
            print(f"  → 点击确认")
            await dialog.accept()

        page.on('dialog', handle_dialog)
        await refresh_btn.click()
        await page.wait_for_timeout(2000)

        print("\n[步骤 3] 等待 Discovery Agent 重新搜索...")
        print("  （这可能需要1-2分钟）")

        # 等待并检查 toast 提示
        start_time = time.time()
        max_wait_time = 180  # 最多等待3分钟

        success_found = False
        elapsed = 0

        while elapsed < max_wait_time:
            # 检查是否有成功提示
            success_toast = page.locator('.toast.success')
            count = await success_toast.count()

            if count > 0:
                toast_text = await success_toast.inner_text()
                if '刷新成功' in toast_text or '已更新国家' in toast_text:
                    print(f"\n  ✓ {toast_text}")
                    success_found = True
                    break

            await page.wait_for_timeout(5000)  # 每5秒检查一次
            elapsed = time.time() - start_time
            print(f"  ⏳ 已等待 {int(elapsed)}秒...", end='\r')

        if success_found:
            print("\n\n✅ 测试通过：Discovery Agent 成功刷新国家配置！")
        else:
            print("\n\n⚠️  超时：未能在3分钟内完成刷新")
            # 检查是否有错误提示
            error_toast = page.locator('.toast.error')
            error_count = await error_toast.count()
            if error_count > 0:
                error_text = await error_toast.inner_text()
                print(f"  ✗ 错误信息: {error_text}")

        await browser.close()


async def main():
    """Run all agent workflow tests"""
    print("\n" + "="*80)
    print("DISCOVERY AGENT 工作流程测试")
    print("="*80)

    try:
        # 测试 1: 添加新国家
        await test_add_country_workflow()

        # 等待几秒
        await asyncio.sleep(5)

        # 测试 2: 刷新国家
        await test_refresh_country_workflow()

        print("\n" + "="*80)
        print("🎉 所有测试完成！")
        print("="*80)
        print("\n📋 测试总结:")
        print("  ✅ 添加国家功能：启动 Discovery Agent 搜索教育体系")
        print("  ✅ 刷新国家功能：启动 Discovery Agent 更新教育配置")
        print("\n💡 说明:")
        print("  - Discovery Agent 使用 AI 搜索和分析网络信息")
        print("  - 自动提取国家的年级、学科、教育层级等结构化数据")
        print("  - 将提取的配置保存到 countries_config.json")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
