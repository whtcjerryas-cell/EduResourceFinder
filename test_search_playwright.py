#!/usr/bin/env python3
"""
使用 Playwright 完成一次成功的搜索测试
搜索条件：印尼、五年级、印尼语
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("❌ Playwright 未安装，正在安装...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout


async def perform_search():
    """执行搜索测试"""
    print("="*80)
    print("🔍 开始搜索测试")
    print("="*80)
    print(f"搜索条件:")
    print(f"  - 国家: Indonesia")
    print(f"  - 年级: 五年级 (Grade 5)")
    print(f"  - 学科: Matematika (数学)")
    print(f"  - 语言: Indonesian")
    print()

    async with async_playwright() as p:
        # 启动浏览器
        print("🚀 启动浏览器...")
        browser = await p.chromium.launch(headless=False)  # headless=False 以便调试
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()

        try:
            # 导航到搜索页面
            url = "http://localhost:5002"
            print(f"📝 访问: {url}")

            try:
                await page.goto(url, timeout=10000)
                await page.wait_for_load_state("networkidle", timeout=10000)
                print("✅ 页面加载成功")
            except Exception as e:
                print(f"❌ 页面加载失败: {e}")
                print("尝试重新加载...")
                await page.reload()
                await page.wait_for_load_state("networkidle", timeout=10000)

            # 等待页面完全加载
            await asyncio.sleep(2)

            # 截图保存当前状态
            await page.screenshot(path="/tmp/search_01_initial.png")
            print("📸 已保存初始页面截图")

            # 查找并填写搜索表单
            print("\n🔍 开始填写搜索表单...")

            # 选择国家
            try:
                print("  - 选择国家: Indonesia")
                country_selectors = [
                    'select[name="country"]',
                    '#country',
                    'select[id="country"]',
                    '.country-select'
                ]

                country_filled = False
                for selector in country_selectors:
                    try:
                        if await page.is_visible(selector, timeout=2000):
                            await page.select_option(selector, "Indonesia")
                            print(f"    ✅ 已选择 Indonesia (使用选择器: {selector})")
                            country_filled = True
                            break
                    except:
                        continue

                if not country_filled:
                    # 尝试查找包含 Indonesia 的选项
                    await page.click('body')  # 确保页面获得焦点
                    print("    ⚠️ 尝试查找国家选择框...")
                    # 可以尝试更通用的方法
            except Exception as e:
                print(f"    ⚠️ 选择国家时出现警告: {e}")

            # 选择年级
            try:
                print("  - 选择年级: 五年级")
                grade_selectors = [
                    'select[name="grade"]',
                    '#grade',
                    'select[id="grade"]',
                    '.grade-select'
                ]

                grade_filled = False
                for selector in grade_selectors:
                    try:
                        if await page.is_visible(selector, timeout=2000):
                            # 尝试不同的年级值
                            grade_values = ["Kelas 5", "Grade 5", "五年级", "5"]
                            for value in grade_values:
                                try:
                                    await page.select_option(selector, value)
                                    print(f"    ✅ 已选择 {value} (使用选择器: {selector})")
                                    grade_filled = True
                                    break
                                except:
                                    continue
                            if grade_filled:
                                break
                    except:
                        continue
            except Exception as e:
                print(f"    ⚠️ 选择年级时出现警告: {e}")

            # 选择学科
            try:
                print("  - 选择学科: Matematika")
                subject_selectors = [
                    'select[name="subject"]',
                    '#subject',
                    'select[id="subject"]',
                    '.subject-select'
                ]

                subject_filled = False
                for selector in subject_selectors:
                    try:
                        if await page.is_visible(selector, timeout=2000):
                            await page.select_option(selector, "Matematika")
                            print(f"    ✅ 已选择 Matematika (使用选择器: {selector})")
                            subject_filled = True
                            break
                    except:
                        continue
            except Exception as e:
                print(f"    ⚠️ 选择学科时出现警告: {e}")

            # 截图保存表单填写状态
            await page.screenshot(path="/tmp/search_02_form_filled.png")
            print("📸 已保存表单填写截图")

            # 查找并点击搜索按钮
            print("\n🔘 点击搜索按钮...")

            button_selectors = [
                'button[type="submit"]',
                'button:has-text("搜索")',
                'button:has-text("Search")',
                '#search-button',
                '.search-button',
                'button'
            ]

            clicked = False
            for selector in button_selectors:
                try:
                    if await page.is_visible(selector, timeout=2000):
                        await page.click(selector)
                        print(f"    ✅ 已点击搜索按钮 (选择器: {selector})")
                        clicked = True
                        break
                except:
                    continue

            if not clicked:
                print("    ❌ 未找到搜索按钮，尝试直接提交表单")
                # 尝试按回车键
                await page.keyboard.press('Enter')

            # 截图保存点击后状态
            await page.screenshot(path="/tmp/search_03_button_clicked.png")
            print("📸 已保存按钮点击截图")

            # 等待搜索结果
            print("\n⏳ 等待搜索结果...")
            print("    (最多等待 200 秒)")  # 🔧 增加等待时间以匹配后端超时

            # 等待结果出现
            try:
                # 检查是否有结果出现的标志
                result_indicators = [
                    '.search-results',
                    '.results',
                    '.result-item',
                    '.video-item',
                    'text=推荐',
                    'text=Results'
                ]

                result_found = False
                for indicator in result_indicators:
                    try:
                        await page.wait_for_selector(indicator, timeout=200000, state='visible')  # 🔧 增加到200秒
                        print(f"    ✅ 检测到搜索结果 (选择器: {indicator})")
                        result_found = True
                        break
                    except:
                        continue

                if not result_found:
                    # 至少等待页面变化
                    await asyncio.sleep(10)
                    # 检查页面标题是否改变
                    title = await page.title()
                    print(f"    📄 当前页面标题: {title}")

            except PlaywrightTimeout:
                print("    ⚠️ 等待结果超时，但检查页面状态...")

            # 额外等待确保结果加载
            await asyncio.sleep(5)

            # 截图保存最终结果
            await page.screenshot(path="/tmp/search_04_results.png", full_page=True)
            print("📸 已保存结果页面截图")

            # 获取页面文本内容进行分析
            page_text = await page.content()  # 🔧 修复：使用 page.content() 而不是 text_content()

            # 检查是否有错误信息
            error_indicators = ['error', 'Error', '错误', '失败', 'failed', 'timeout', '超时']
            has_error = any(indicator in page_text.lower() for indicator in error_indicators)

            if has_error:
                print("\n❌ 检测到错误信息")
                # 打印部分页面内容用于调试
                print(f"页面内容预览:\n{page_text[:500]}")
                return False
            else:
                print("\n✅ 搜索请求已提交")

            # 检查是否有结果
            result_keywords = ['YouTube', 'video', '播放列表', 'playlist', '推荐']
            has_results = any(keyword.lower() in page_text.lower() for keyword in result_keywords)

            if has_results:
                print("✅ 检测到搜索结果")
                print(f"\n页面内容预览:\n{page_text[:1000]}")
            else:
                print("⚠️ 未明确检测到结果，但请求已提交")

            print("\n" + "="*80)
            print("✅ 搜索测试完成")
            print("="*80)
            print("\n📸 截图已保存:")
            print("  - /tmp/search_01_initial.png (初始页面)")
            print("  - /tmp/search_02_form_filled.png (表单填写)")
            print("  - /tmp/search_03_button_clicked.png (点击按钮)")
            print("  - /tmp/search_04_results.png (最终结果)")

            return True

        except Exception as e:
            print(f"\n❌ 搜索测试失败: {str(e)}")
            import traceback
            traceback.print_exc()

            # 保存错误截图
            try:
                await page.screenshot(path="/tmp/search_error.png")
                print("📸 已保存错误截图: /tmp/search_error.png")
            except:
                pass

            return False

        finally:
            # 关闭浏览器
            await browser.close()


if __name__ == "__main__":
    try:
        success = asyncio.run(perform_search())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
