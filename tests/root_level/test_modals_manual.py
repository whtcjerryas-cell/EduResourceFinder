#!/usr/bin/env python3
"""
Manual test for modals - checks if the fixes work
"""
from playwright.sync_api import sync_playwright
import time

BASE_URL = "http://localhost:5001"

def test_debug_modal():
    """Test Debug modal open and close"""
    print("\n" + "="*80)
    print("测试 Debug 模态框")
    print("="*80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1400, 'height': 900})
        page = context.new_page()

        # Clear cache
        context.clear_cookies()

        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        # Find and click Debug button
        debug_btn = page.locator('button:has-text("Debug日志")').first
        debug_btn.wait_for(state="visible", timeout=5000)
        print("✅ Debug按钮可见")

        debug_btn.click()
        print("🖱️ 点击Debug按钮")

        # Wait for modal
        modal = page.locator('#debugModal')
        modal.wait_for(state="visible", timeout=5000)
        print("✅ Debug模态框已打开")

        # Check computed style
        display_value = page.evaluate('''() => {
            const modal = document.getElementById('debugModal');
            return window.getComputedStyle(modal).display;
        }''')
        print(f"📊 Display值: {display_value}")

        # Find close button
        close_btn = page.locator('#closeDebugModal')
        close_btn.wait_for(state="visible", timeout=5000)
        print("✅ 关闭按钮可见")

        # Take screenshot
        page.screenshot(path="test_screenshots/manual_debug_open.png")

        # Click close
        close_btn.click()
        print("🖱️ 点击关闭按钮")

        # Wait a bit
        time.sleep(1)

        # Check if hidden
        is_visible = modal.is_visible()
        print(f"🔍 模态框可见: {is_visible}")

        # Check computed style again
        display_value_after = page.evaluate('''() => {
            const modal = document.getElementById('debugModal');
            return window.getComputedStyle(modal).display;
        }''')
        print(f"📊 关闭后Display值: {display_value_after}")

        page.screenshot(path="test_screenshots/manual_debug_close.png")

        browser.close()

        if display_value_after == 'none':
            print("✅ Debug模态框关闭成功")
            return True
        else:
            print("❌ Debug模态框关闭失败")
            return False

def test_add_country_modal():
    """Test Add Country modal"""
    print("\n" + "="*80)
    print("测试添加国家模态框")
    print("="*80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1400, 'height': 900})
        page = context.new_page()

        # Clear cache
        context.clear_cookies()

        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        # Find and click Add Country button
        add_btn = page.locator('#addCountryBtn')
        add_btn.wait_for(state="visible", timeout=5000)
        print("✅ 添加国家按钮可见")

        add_btn.click()
        print("🖱️ 点击添加国家按钮")

        # Wait a moment
        time.sleep(1)

        # Check if modal is visible
        modal = page.locator('#addCountryModal')
        is_visible = modal.is_visible()
        print(f"🔍 模态框可见: {is_visible}")

        # Check computed style
        display_value = page.evaluate('''() => {
            const modal = document.getElementById('addCountryModal');
            if (!modal) return 'ELEMENT_NOT_FOUND';
            return window.getComputedStyle(modal).display;
        }''')
        print(f"📊 Display值: {display_value}")

        # Check inline style
        inline_style = page.evaluate('''() => {
            const modal = document.getElementById('addCountryModal');
            if (!modal) return 'ELEMENT_NOT_FOUND';
            return modal.style.display;
        }''')
        print(f"📊 Inline style: {inline_style}")

        page.screenshot(path="test_screenshots/manual_add_country.png")

        browser.close()

        if display_value == 'block':
            print("✅ 添加国家模态框显示成功")
            return True
        else:
            print("❌ 添加国家模态框显示失败")
            return False

if __name__ == "__main__":
    print("🧪 手动测试模态框修复")
    print("="*80)

    result1 = test_debug_modal()
    result2 = test_add_country_modal()

    print("\n" + "="*80)
    print("📊 测试结果")
    print("="*80)
    print(f"Debug模态框: {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"添加国家模态框: {'✅ PASS' if result2 else '❌ FAIL'}")

    if result1 and result2:
        print("\n✅ 所有测试通过！")
        exit(0)
    else:
        print("\n❌ 部分测试失败")
        exit(1)
