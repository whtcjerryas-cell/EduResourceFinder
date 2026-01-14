#!/usr/bin/env python3
"""
Full console capture test
"""
from playwright.sync_api import sync_playwright
import time

BASE_URL = "http://localhost:5001"

def test_full_console():
    """Capture all console messages including errors"""
    print("\n" + "="*80)
    print("完整控制台捕获测试")
    print("="*80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1400, 'height': 900})
        page = context.new_page()

        # Capture ALL console messages
        all_messages = []
        def on_console(msg):
            all_messages.append({
                'type': msg.type,
                'text': msg.text,
                'args': [str(arg) for arg in msg.args]
            })
            print(f"🖥️  [{msg.type}] {msg.text}")

        page.on("console", on_console)

        # Also capture page errors
        page_errors = []
        def on_error(error):
            page_errors.append(str(error))
            print(f"❌ PAGE ERROR: {error}")

        page.on("pageerror", on_error)

        print("\n📜 正在加载页面...")
        page.goto(BASE_URL, wait_until="networkidle")

        # Wait for all JS to execute
        time.sleep(3)

        print(f"\n📊 总共捕获 {len(all_messages)} 条console消息")
        print(f"❌ 页面错误: {len(page_errors)} 个")

        # Check for errors
        error_messages = [msg for msg in all_messages if msg['type'] in ['error']]
        if error_messages:
            print(f"\n❌ 发现 {len(error_messages)} 条错误消息:")
            for msg in error_messages[-10:]:  # Last 10 errors
                print(f"   {msg['text']}")

        # Check if bindButtonEvents exists
        has_bind = page.evaluate('''() => {
            return typeof window.bindButtonEvents === 'function';
        }''')
        print(f"\n🔍 bindButtonEvents 存在: {has_bind}")

        # Try to find the debug message
        has_debug_msg = any('bindButtonEvents 已暴露' in msg['text'] for msg in all_messages)
        print(f"🔍 找到暴露消息: {has_debug_msg}")

        # Check for syntax errors
        syntax_errors = [msg for msg in all_messages if 'SyntaxError' in msg['text'] or 'Unexpected' in msg['text']]
        if syntax_errors:
            print(f"\n❌ 发现语法错误:")
            for msg in syntax_errors:
                print(f"   {msg['text']}")

        time.sleep(2)
        browser.close()

if __name__ == "__main__":
    test_full_console()
