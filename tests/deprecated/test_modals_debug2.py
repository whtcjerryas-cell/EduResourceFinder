#!/usr/bin/env python3
"""
Debug test - check Add Country modal
"""
from playwright.sync_api import sync_playwright
import time

BASE_URL = "http://localhost:5001"

def test_add_country_debug():
    """Test Add Country modal in detail"""
    print("\n" + "="*80)
    print("调试添加国家模态框")
    print("="*80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(viewport={'width': 1400, 'height': 900})
        page = context.new_page()

        # Listen to console messages
        console_messages = []
        def on_console(msg):
            console_messages.append(msg.text)
            if 'DEBUG' in msg.text or 'ERROR' in msg.text or '模态框' in msg.text:
                print(f"🖥️  Console: {msg.text}")

        page.on("console", on_console)

        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(2)  # Wait for all JS to load

        # Check if bindButtonEvents exists
        has_bind = page.evaluate('''() => {
            return typeof bindButtonEvents === 'function';
        }''')
        print(f"🔍 bindButtonEvents 存在: {has_bind}")

        # Check if button exists
        has_btn = page.evaluate('''() => {
            const btn = document.getElementById('addCountryBtn');
            return btn !== null;
        }''')
        print(f"🔍 addCountryBtn 存在: {has_btn}")

        # Check if modal exists
        has_modal = page.evaluate('''() => {
            const modal = document.getElementById('addCountryModal');
            return modal !== null;
        }''')
        print(f"🔍 addCountryModal 存在: {has_modal}")

        # Check initial display
        initial_display = page.evaluate('''() => {
            const modal = document.getElementById('addCountryModal');
            return window.getComputedStyle(modal).display;
        }''')
        print(f"📊 初始Display值: {initial_display}")

        # Try to call bindButtonEvents manually
        print("\n🖱️ 手动调用 bindButtonEvents()...")
        page.evaluate('''() => {
            if (typeof bindButtonEvents === 'function') {
                bindButtonEvents();
            }
        }''')
        time.sleep(1)

        # Now try clicking the button
        print("\n🖱️ 点击添加国家按钮...")
        page.evaluate('''() => {
            const btn = document.getElementById('addCountryBtn');
            if (btn) {
                btn.click();
            }
        }''')
        time.sleep(2)  # Wait longer

        # Check display after click
        display_after = page.evaluate('''() => {
            const modal = document.getElementById('addCountryModal');
            return window.getComputedStyle(modal).display;
        }''')
        print(f"📊 点击后Display值: {display_after}")

        # Check inline style
        inline_style = page.evaluate('''() => {
            const modal = document.getElementById('addCountryModal');
            return modal.style.display;
        }''')
        print(f"📊 Inline style: {inline_style}")

        page.screenshot(path="test_screenshots/debug_add_country.png")

        time.sleep(2)
        browser.close()

if __name__ == "__main__":
    test_add_country_debug()
