"""
Playwright test to verify reported bugs before fixing.

Bugs to verify:
1. Homepage "添加国家" (Add Country) and "刷新国家" (Refresh Country) buttons don't work
2. Search history page shows "加载失败 Unexpected token '<', " error
"""
import asyncio
from playwright.async_api import async_playwright


async def test_bug_1_country_buttons():
    """Test that country buttons don't respond to clicks"""
    print("\n=== Testing Bug 1: Country Buttons Don't Work ===")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Navigate to homepage
        await page.goto("http://localhost:5001")
        await page.wait_for_load_state('networkidle')

        # Find the buttons
        add_btn = page.locator('#addCountryBtn')
        refresh_btn = page.locator('#refreshCountryBtn')

        # Check if buttons exist
        add_count = await add_btn.count()
        refresh_count = await refresh_btn.count()

        print(f"✓ Found '添加国家' button: {add_count > 0}")
        print(f"✓ Found '刷新国家' button: {refresh_count > 0}")

        if add_count > 0:
            # Click the add button and see what happens
            await add_btn.click()
            await page.wait_for_timeout(1000)

            # Check if any modal or dialog appeared
            modals = page.locator('.modal, .dialog, [role="dialog"]')
            modal_count = await modals.count()
            print(f"✓ After clicking '添加国家': {modal_count} modals appeared")

            if modal_count == 0:
                print("✗ BUG CONFIRMED: No modal appeared - button doesn't work!")

        if refresh_count > 0:
            # Click the refresh button
            country_select = page.locator('#country')
            initial_options = await country_select.locator('option').count()

            await refresh_btn.click()
            await page.wait_for_timeout(2000)

            # Check if country list changed
            final_options = await country_select.locator('option').count()
            print(f"✓ Country options before refresh: {initial_options}")
            print(f"✓ Country options after refresh: {final_options}")

            if initial_options == final_options:
                print("✗ BUG CONFIRMED: No change detected - button doesn't work!")

        await browser.close()
        print("\n✅ Bug 1 Test Complete\n")


async def test_bug_2_search_history_error():
    """Test that search history page shows JSON parsing error"""
    print("\n=== Testing Bug 2: Search History Loading Error ===")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Navigate to search history page
        await page.goto("http://localhost:5001/search_history")
        await page.wait_for_load_state('networkidle')

        # Wait for page to load
        await page.wait_for_timeout(2000)

        # Check for error message
        error_elements = page.locator('.empty-state, .error-message')
        error_count = await error_elements.count()

        print(f"✓ Error elements on page: {error_count}")

        if error_count > 0:
            error_text = await error_elements.inner_text()
            print(f"✓ Error message found: {error_text[:200]}")

            if "Unexpected token" in error_text or "加载失败" in error_text:
                print("✗ BUG CONFIRMED: JSON parsing error detected!")
        else:
            # Check console errors
            console_messages = []
            page.on('console', lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))

            # Try to manually trigger the API call
            await page.goto("http://localhost:5001/search_history")
            await page.wait_for_timeout(2000)

            # Check for console errors
            error_msgs = [msg for msg in console_messages if 'error' in msg.lower()]
            if error_msgs:
                print(f"✓ Console errors found: {error_msgs[:3]}")
                print("✗ BUG CONFIRMED: API request failed!")

        # Also test the API endpoint directly
        print("\n--- Testing API endpoint directly ---")
        try:
            response = await page.request.get("http://localhost:5001/api/search_history")
            status = response.status
            content_type = response.headers.get('content-type', '')

            print(f"✓ API Response Status: {status}")
            print(f"✓ Content-Type: {content_type}")

            if status != 200:
                print(f"✗ BUG CONFIRMED: API returned status {status}")
            elif 'html' in content_type:
                print("✗ BUG CONFIRMED: API returned HTML instead of JSON!")
            else:
                text = await response.text()
                if text.startswith('<'):
                    print("✗ BUG CONFIRMED: Response starts with HTML tag!")
                else:
                    print(f"✓ Response preview: {text[:200]}")

        except Exception as e:
            print(f"✗ API request failed: {e}")

        await browser.close()
        print("\n✅ Bug 2 Test Complete\n")


async def main():
    """Run all bug verification tests"""
    print("\n" + "="*60)
    print("PLAYWRIGHT BUG VERIFICATION TESTS")
    print("="*60)

    await test_bug_1_country_buttons()
    await test_bug_2_search_history_error()

    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
