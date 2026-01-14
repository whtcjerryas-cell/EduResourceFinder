#!/usr/bin/env python3
"""
Debug test - check event listeners and console
"""
from playwright.sync_api import sync_playwright
import time

BASE_URL = "http://localhost:5001"

def test_debug_listeners():
    """Test if event listeners are attached"""
    print("\n" + "="*80)
    print("调试事件监听器")
    print("="*80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(viewport={'width': 1400, 'height': 900})
        page = context.new_page()

        # Listen to console messages
        console_messages = []
        def on_console(msg):
            console_messages.append(msg.text)
            print(f"🖥️  Console: {msg.text}")

        page.on("console", on_console)

        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(2)  # Wait for all JS to load

        # Check if functions exist
        has_toggle = page.evaluate('''() => {
            return typeof window.toggleDebugModal === 'function';
        }''')
        print(f"🔍 toggleDebugModal 存在: {has_toggle}")

        has_close = page.evaluate('''() => {
            return typeof closeDebugModal === 'function';
        }''')
        print(f"🔍 closeDebugModal 存在: {has_close}")

        # Check if close button has event listener
        has_close_listener = page.evaluate('''() => {
            const btn = document.getElementById('closeDebugModal');
            if (!btn) return 'BUTTON_NOT_FOUND';
            // Try to check if it has onclick
            return 'onclick' in btn || btn.onclick !== null;
        }''')
        print(f"🔍 关闭按钮有onclick: {has_close_listener}")

        # Try to manually call closeDebugModal
        print("\n🖱️ 手动调用 closeDebugModal()...")
        result = page.evaluate('''() => {
            const modal = document.getElementById('debugModal');
            if (typeof closeDebugModal === 'function') {
                closeDebugModal();
                return window.getComputedStyle(modal).display;
            } else {
                return 'closeDebugModal_NOT_FUNCTION';
            }
        }''')
        print(f"📊 调用后Display值: {result}")

        # Try direct inline click
        print("\n🖱️ 尝试内联点击...")
        page.evaluate('''() => {
            const btn = document.getElementById('closeDebugModal');
            if (btn) {
                btn.click();
            }
        }''')
        time.sleep(1)

        display_after_click = page.evaluate('''() => {
            const modal = document.getElementById('debugModal');
            return window.getComputedStyle(modal).display;
        }''')
        print(f"📊 点击后Display值: {display_after_click}")

        # Check console messages
        print(f"\n📋 Console消息 ({len(console_messages)} 条):")
        for msg in console_messages[-10:]:  # Last 10 messages
            print(f"   {msg}")

        time.sleep(2)
        browser.close()

if __name__ == "__main__":
    test_debug_listeners()
